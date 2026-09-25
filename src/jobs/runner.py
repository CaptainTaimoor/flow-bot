import os
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from src.database.db import get_db_context
from src.database.repository import Repository
from src.database.models import JobDB
from src.models.domain import (
    JobStatus,
    GenerationState,
    JobCreate,
    CorrelationConfidence,
    AuthState,
)
from src.browser.service import browser_service
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager
from src.flow.credit_policy import CreditPolicyManager
from src.jobs.queue import JobQueue
from src.media.service import media_service
from src.api.events import event_broadcaster
from src.config.runtime_config import runtime_config

logger = logging.getLogger(__name__)

class JobRunner:
    def __init__(self):
        self.running = False
        self._current_job_id: Optional[int] = None
        self._cancel_requested_jobs: set = set()

    def request_job_cancellation(self, job_id: int):
        self._cancel_requested_jobs.add(job_id)

    async def start_loop(self):
        self.running = True
        logger.info("Starting Production-Grade JobRunner loop...")

        while self.running:
            try:
                job_to_run = None
                gen_id = None
                job_data = None

                with get_db_context() as db:
                    queue = JobQueue(db)
                    job = queue.claim_next_job()
                    if job:
                        self._current_job_id = job.id
                        logger.info(f"Claimed job #{job.id}: '{job.prompt[:40]}...'")
                        gen_id = queue.add_generation(job.id, GenerationState.QUEUED)
                        event_broadcaster.publish("job.started", {"job_id": job.id, "prompt": job.prompt})

                        job_data = JobCreate(
                            prompt=job.prompt,
                            model=job.requested_model or job.model,
                            orientation=job.requested_orientation or job.orientation,
                            duration=job.requested_duration or job.duration,
                            output_count=job.requested_output_count or job.output_count,
                            project=job.project,
                            generation_mode=job.generation_mode,
                            allow_unverified_credits=False,
                        )
                        job_to_run = job

                if job_to_run and gen_id and job_data:
                    try:
                        await self._process_job(job_to_run.id, gen_id, job_data)
                    except Exception as e:
                        logger.error(f"Job #{job_to_run.id} failed: {e}", exc_info=True)
                        with get_db_context() as db:
                            r = Repository(db)
                            r.update_generation_state(gen_id, GenerationState.FAILED, error_message=str(e))
                            r.update_job_status(job_to_run.id, JobStatus.FAILED, error_message=str(e))
                        event_broadcaster.publish("job.failed", {"job_id": job_to_run.id, "error": str(e)})
                    finally:
                        self._current_job_id = None
                        self._cancel_requested_jobs.discard(job_to_run.id)

                await asyncio.sleep(2)
            except Exception as loop_err:
                logger.error(f"Error in JobRunner loop: {loop_err}", exc_info=True)
                await asyncio.sleep(4)

    async def _process_job(self, job_id: int, gen_id: int, job_data: JobCreate):
        def update_state(
            state: GenerationState,
            details: Optional[Dict[str, Any]] = None,
            submission_confirmed: Optional[bool] = None,
            submission_proof: Optional[dict] = None,
            correlation_confidence: Optional[str] = None,
            correlation_evidence: Optional[dict] = None,
            error_message: Optional[str] = None,
        ):
            with get_db_context() as db:
                r = Repository(db)
                r.update_generation_state(
                    gen_id=gen_id,
                    state=state,
                    submission_confirmed=submission_confirmed,
                    submission_proof=submission_proof,
                    correlation_confidence=correlation_confidence,
                    correlation_evidence=correlation_evidence,
                    error_message=error_message,
                )
            payload = {"job_id": job_id, "generation_id": gen_id, "state": state.value}
            if details:
                payload.update(details)
            event_broadcaster.publish("generation.state_changed", payload)

        async with browser_service.lease_page() as page:
            adapter = GoogleFlowAdapter(page)

            # 1. Opening Browser
            update_state(GenerationState.OPENING_BROWSER)

            # 2. Opening Flow
            update_state(GenerationState.OPENING_FLOW)
            await adapter.open_flow()

            # 3. Checking Authentication
            update_state(GenerationState.CHECKING_AUTH)
            auth_val = await AuthManager.check_auth_status(page)
            if auth_val != AuthState.AUTHENTICATED.value:
                logger.warning(f"Authentication required (state={auth_val}). Pausing for login...")
                update_state(GenerationState.AUTH_REQUIRED)
                event_broadcaster.publish("auth.required", {"job_id": job_id})
                auth_ok = await AuthManager.wait_for_manual_auth(page, timeout=300000)
                if not auth_ok:
                    raise Exception("Manual authentication timed out on Google Flow.")

            # 4. Opening Project Workspace
            update_state(GenerationState.OPENING_PROJECT)
            await adapter.project_manager.ensure_project_open()

            # 5. Discovering Capabilities
            update_state(GenerationState.DISCOVERING_CAPABILITIES)
            caps = await adapter.detect_capabilities()

            # 6. Checking Credit Safety Policy
            update_state(GenerationState.CHECKING_CREDIT_POLICY)
            with get_db_context() as db:
                is_safe, safety_reason, verified_cost = CreditPolicyManager.evaluate_submission_safety(
                    job_data, caps, db
                )
                r = Repository(db)
                r.update_job_submission(
                    job_id,
                    confirmed=False,
                    credit_status=caps.credit_status,
                    verified_cost=verified_cost,
                )

            if not is_safe:
                raise Exception(safety_reason)

            # Check if cancellation requested before proceeding
            if job_id in self._cancel_requested_jobs:
                update_state(GenerationState.CANCELLED)
                with get_db_context() as db:
                    Repository(db).update_job_status(job_id, JobStatus.CANCELLED)
                return

            # 7. Retry Reconciliation Check
            reconciled_tile = None
            with get_db_context() as db:
                job_record = Repository(db).get_job(job_id)
                if job_record and job_record.retry_count > 0:
                    update_state(GenerationState.RETRY_RECONCILIATION_REQUIRED)
                    reconciled, matched_tile, evidence = await adapter.reconcile_prior_submission(job_data.prompt)
                    if reconciled and matched_tile:
                        logger.info("Prior generation reconciled. Reusing existing Flow canvas render...")
                        reconciled_tile = matched_tile

            tile = reconciled_tile

            if not tile:
                # 8. Preparing Workspace & Selecting Parameters
                update_state(GenerationState.PREPARING)
                await adapter.prepare_for_submission()
                effective_cfg = await adapter.select_parameters(job_data)

                with get_db_context() as db:
                    Repository(db).update_job_effective_config(
                        job_id=job_id,
                        effective_model=effective_cfg.get("effective_model"),
                        effective_orientation=effective_cfg.get("effective_orientation"),
                        effective_duration=effective_cfg.get("effective_duration"),
                        effective_output_count=effective_cfg.get("effective_output_count"),
                    )

                # 9. Submitting Prompt
                update_state(GenerationState.SUBMITTING)
                submitted, proof = await adapter.submit_prompt(job_data)

                # 10. Submission Confirmation Audit
                if submitted:
                    update_state(GenerationState.SUBMISSION_CONFIRMED, submission_confirmed=True, submission_proof=proof)
                    with get_db_context() as db:
                        Repository(db).update_job_submission(job_id, confirmed=True)
                else:
                    update_state(GenerationState.SUBMISSION_UNKNOWN, submission_confirmed=False, submission_proof=proof)
                    raise Exception(f"Prompt submission was rejected or unconfirmed: {proof.get('error', 'unknown error')}")

                # 11. Generation Started
                update_state(GenerationState.GENERATION_STARTED)
                await asyncio.sleep(3)

                # 12. Waiting for Asset
                update_state(GenerationState.WAITING_FOR_ASSET)

                # 13. Asset Identification with Layered Correlation
                update_state(GenerationState.ASSET_IDENTIFICATION)
                tile, confidence, correlation_evidence = await adapter.locate_generated_tile(job_data.prompt, timeout_seconds=45)

                # 14. Locating Asset
                update_state(
                    GenerationState.LOCATING_ASSET,
                    correlation_confidence=confidence.value,
                    correlation_evidence=correlation_evidence,
                )

                if confidence == CorrelationConfidence.FAILED or not tile:
                    raise Exception(
                        "Deterministic asset correlation failed: Could not locate newly generated tile with sufficient confidence."
                    )

            # Check if cancellation requested while running
            if job_id in self._cancel_requested_jobs:
                cancelled, cancel_reason = await adapter.cancel_active_generation(target_tile=tile)
                if cancelled:
                    update_state(GenerationState.CANCELLED, {"reason": cancel_reason})
                    with get_db_context() as db:
                        Repository(db).update_job_status(job_id, JobStatus.CANCELLED)
                else:
                    update_state(GenerationState.CANCELLATION_UNCONFIRMED, {"reason": cancel_reason})
                return

            # 15. Generating & Progress Monitoring
            update_state(GenerationState.GENERATING)

            def on_progress(percent: Optional[int], message: str):
                event_broadcaster.publish("generation.progress", {
                    "job_id": job_id,
                    "generation_id": gen_id,
                    "percent": percent,
                    "message": message,
                })

            completed = await adapter.wait_for_completion(tile, progress_callback=on_progress)
            if not completed:
                raise Exception("Generation timed out on Google Flow canvas.")

            # 16. Downloading Asset
            update_state(GenerationState.DOWNLOADING)
            video_path = await adapter.download_asset(job_id, gen_id, target_tile=tile)
            if not video_path or not os.path.exists(video_path):
                raise Exception("Failed to download generated video asset from Google Flow.")

            # 17. Validating Asset with Strict FFprobe
            update_state(GenerationState.VALIDATING)
            is_valid, meta = await media_service.validate_video(video_path)
            if not is_valid:
                raise Exception(f"Video media validation failed: {meta.get('error')}")

            # 18. Thumbnail Generating
            update_state(GenerationState.THUMBNAIL_GENERATING)
            dest_thumb = media_service.get_destination_thumbnail_path(job_id, gen_id)
            thumb_path = await media_service.generate_thumbnail(
                video_path, dest_thumb, duration=meta.get("duration")
            )

            # 19. Ready & DB Persistence
            update_state(GenerationState.READY)
            with get_db_context() as db:
                r = Repository(db)
                filename = os.path.basename(video_path)
                asset = r.create_asset(
                    job_id=job_id,
                    generation_id=gen_id,
                    filename=filename,
                    file_path=video_path,
                    thumbnail_path=thumb_path,
                    mime_type="video/mp4",
                    file_size=meta.get("file_size", 0),
                    duration=meta.get("duration"),
                    width=meta.get("width"),
                    height=meta.get("height"),
                    video_codec=meta.get("video_codec"),
                    audio_codec=meta.get("audio_codec"),
                    fps=meta.get("fps"),
                    correlation_confidence=confidence.value if 'confidence' in locals() else CorrelationConfidence.HIGH.value,
                    correlation_evidence=correlation_evidence if 'correlation_evidence' in locals() else None,
                    ffprobe_metadata=meta.get("ffprobe_metadata"),
                )
                r.update_generation_state(gen_id, GenerationState.SUCCESS)
                r.update_job_status(job_id, JobStatus.SUCCESS)

            # 20. Completed Notification
            update_state(GenerationState.COMPLETED)
            event_broadcaster.publish("job.completed", {
                "job_id": job_id,
                "asset_id": asset.id,
                "filename": filename,
            })
            logger.info(f"Job #{job_id} successfully completed. Asset ID: {asset.id}")

    async def stop(self):
        self.running = False
        await browser_service.stop()

job_runner = JobRunner()
