import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from src.database.db import get_db_context
from src.database.repository import Repository
from src.database.models import JobDB
from src.models.domain import JobStatus, GenerationState, JobCreate
from src.browser.manager import BrowserManager
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager, AuthState
from src.media.service import media_service
from src.api.events import event_broadcaster
from src.config.settings import settings

logger = logging.getLogger(__name__)

class JobRunner:
    def __init__(self):
        self.browser_manager = BrowserManager()
        self.running = False
        self._current_job_id: Optional[int] = None

    async def start_loop(self):
        self.running = True
        logger.info("Starting V2 JobRunner loop...")

        while self.running:
            try:
                with get_db_context() as db:
                    repo = Repository(db)
                    job = repo.get_next_queued_job()

                    if job:
                        self._current_job_id = job.id
                        logger.info(f"Picked up job #{job.id}: '{job.prompt[:40]}...'")
                        repo.update_job_status(job.id, JobStatus.RUNNING)
                        gen = repo.create_generation(job.id, GenerationState.QUEUED)
                        gen_id = gen.id

                        event_broadcaster.publish("job.started", {"job_id": job.id, "prompt": job.prompt})

                        # Process job outside database context lock
                        job_data = JobCreate(
                            prompt=job.prompt,
                            model=job.model,
                            orientation=job.orientation,
                            duration=job.duration,
                            output_count=job.output_count,
                            project=job.project,
                            generation_mode=job.generation_mode,
                        )

                if job:
                    try:
                        await self._process_job(job.id, gen_id, job_data)
                    except Exception as e:
                        logger.error(f"Job #{job.id} failed: {e}", exc_info=True)
                        with get_db_context() as db:
                            r = Repository(db)
                            r.update_generation_state(gen_id, GenerationState.FAILED, error_message=str(e))
                            r.update_job_status(job.id, JobStatus.FAILED, error_message=str(e))
                        event_broadcaster.publish("job.failed", {"job_id": job.id, "error": str(e)})
                    finally:
                        self._current_job_id = None

                await asyncio.sleep(3)
            except Exception as loop_err:
                logger.error(f"Error in JobRunner loop: {loop_err}")
                await asyncio.sleep(5)

    async def _process_job(self, job_id: int, gen_id: int, job_data: JobCreate):
        def update_state(state: GenerationState, details: Optional[dict] = None):
            with get_db_context() as db:
                r = Repository(db)
                r.update_generation_state(gen_id, state)
            payload = {"job_id": job_id, "generation_id": gen_id, "state": state.value}
            if details:
                payload.update(details)
            event_broadcaster.publish("generation.state_changed", payload)

        # 1. Opening Browser
        update_state(GenerationState.OPENING_BROWSER)
        page = await self.browser_manager.get_page()
        adapter = GoogleFlowAdapter(page)

        # 2. Opening Flow
        update_state(GenerationState.OPENING_FLOW)
        await adapter.open_flow()

        # 3. Checking Authentication
        update_state(GenerationState.CHECKING_AUTH)
        auth_status = await AuthManager.check_auth_status(page)
        if auth_status != AuthState.AUTHENTICATED:
            logger.warning("Authentication required. Pausing for user login...")
            update_state(GenerationState.AUTH_REQUIRED)
            event_broadcaster.publish("auth.required", {"job_id": job_id})
            auth_ok = await AuthManager.wait_for_manual_auth(page, timeout=300000)
            if not auth_ok:
                raise Exception("Manual authentication timed out.")

        # 4. Checking Capabilities
        update_state(GenerationState.CHECKING_CAPABILITIES)
        caps = await adapter.detect_capabilities()

        # 5. Preparing & Baselining
        update_state(GenerationState.PREPARING)
        await adapter.prepare_for_submission()

        # 6. Submitting Prompt
        update_state(GenerationState.SUBMITTING)
        submitted = await adapter.submit_prompt(job_data)
        if not submitted:
            raise Exception("Failed to submit prompt to Google Flow.")

        # 7. Generation Started & Locating Asset Tile
        update_state(GenerationState.GENERATION_STARTED)
        await asyncio.sleep(4)

        update_state(GenerationState.LOCATING_ASSET)
        tile = await adapter.locate_generated_tile(job_data.prompt, timeout_seconds=40)

        # 8. Generating & Progress Monitoring
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

        # 9. Downloading Asset
        update_state(GenerationState.DOWNLOADING)
        video_path = await adapter.download_asset(job_id, gen_id, target_tile=tile)
        if not video_path or not os.path.exists(video_path):
            raise Exception("Failed to download generated video asset.")

        # 10. Validating Asset
        update_state(GenerationState.VALIDATING)
        is_valid, meta = await media_service.validate_video(video_path)
        if not is_valid:
            raise Exception(f"Video validation failed: {meta.get('error')}")

        # 11. Thumbnail Generation
        update_state(GenerationState.THUMBNAIL_GENERATING)
        dest_thumb = media_service.get_destination_thumbnail_path(job_id, gen_id)
        thumb_path = await media_service.generate_thumbnail(video_path, dest_thumb)

        # 12. Persisting Asset & Success
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
                file_size=meta.get("file_size", 0),
                duration=meta.get("duration"),
                width=meta.get("width"),
                height=meta.get("height"),
            )
            r.update_generation_state(gen_id, GenerationState.SUCCESS)
            r.update_job_status(job_id, JobStatus.SUCCESS)

        event_broadcaster.publish("job.completed", {
            "job_id": job_id,
            "asset_id": asset.id,
            "filename": filename,
        })
        logger.info(f"Job #{job_id} successfully completed. Asset ID: {asset.id}")

    async def stop(self):
        self.running = False
        await self.browser_manager.stop()

job_runner = JobRunner()
