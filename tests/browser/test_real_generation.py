import pytest
import asyncio
import os
from src.browser.service import browser_service
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager, AuthState
from src.config.settings import settings
from src.models.domain import JobCreate, CorrelationConfidence
from src.media.service import media_service

# Controlled single real generation test. Consumes credits on Google Flow.
# Usage: pytest tests/browser/test_real_generation.py -s -v

@pytest.mark.asyncio
async def test_real_generation_single():
    async with browser_service.lease_page() as page:
        adapter = GoogleFlowAdapter(page)
        
        print("\n[Test] 1. Opening Google Flow...")
        await adapter.open_flow()
        
        print("[Test] 2. Checking Authentication Status...")
        status = await AuthManager.check_auth_status(page)
        print(f"[Test] Current Auth Status: {status}")
        if status != AuthState.AUTHENTICATED:
            print("[Test] Not authenticated. Manual login required.")
            pytest.skip("Not authenticated")
            
        print("[Test] 3. Discovering Live Flow Capabilities...")
        caps = await adapter.detect_capabilities()
        print(f"[Test] Discovered Models: {caps.models_available} (source={caps.model_source})")
        print(f"[Test] Credit Status: {caps.credit_status} (Balance: {caps.credit_balance})")

        print("[Test] 4. Taking Baseline Asset Snapshot...")
        baseline = await adapter.prepare_for_submission()
        print(f"[Test] Baseline snapshot contains {len(baseline)} tokens.")

        test_prompt = "A cinematic landscape of a peaceful mountain lake at sunrise, realistic lighting, gentle camera movement."
        job = JobCreate(
            prompt=test_prompt,
            model=caps.active_model,
            orientation="16:9",
            duration="5",
            output_count=1,
        )

        print("[Test] 5. Selecting Parameters in Prompt Bar...")
        effective_cfg = await adapter.select_parameters(job)
        print(f"[Test] Effective Configuration: {effective_cfg}")

        print("[Test] 6. Submitting Prompt to Google Flow...")
        submitted, proof = await adapter.submit_prompt(job)
        assert submitted is True, f"Failed to submit prompt: {proof}"
        print(f"[Test] Prompt submitted successfully. Proof: {proof}")

        print("[Test] 7. Locating Generated Tile with Layered Correlation...")
        tile, confidence, evidence = await adapter.locate_generated_tile(test_prompt, timeout_seconds=60)
        assert tile is not None, f"Failed to locate generated tile. Evidence: {evidence}"
        assert confidence in (CorrelationConfidence.HIGH, CorrelationConfidence.MEDIUM), f"Correlation confidence inadequate: {confidence}"
        print(f"[Test] Tile located with {confidence.value} confidence. Top Candidates: {evidence.get('candidates_evaluated', [])[:2]}")

        def on_progress(pct, msg):
            print(f"       -> [Progress] {msg}")

        print("[Test] 8. Monitoring Generation Completion on Canvas...")
        completed = await adapter.wait_for_completion(tile, progress_callback=on_progress)
        assert completed is True, "Generation timed out on Google Flow canvas."
        print("[Test] Generation completed on canvas.")

        print("[Test] 9. Downloading Video Asset...")
        path = await adapter.download_asset(job_id=1, generation_id=1, target_tile=tile)
        assert path is not None, "Failed to download generated asset."
        assert os.path.exists(path), f"Downloaded file does not exist at {path}"
        file_size = os.path.getsize(path)
        assert file_size > 1000, f"Downloaded file suspiciously small: {file_size} bytes"
        print(f"[Test] Video downloaded successfully: {path} ({file_size} bytes)")

        print("[Test] 10. Validating Media with Deep FFprobe Inspection...")
        is_valid, meta = await media_service.validate_video(path)
        assert is_valid is True, f"FFprobe validation failed: {meta.get('error')}"
        print(
            f"[Test] FFprobe Validation PASSED: {meta['width']}x{meta['height']}, "
            f"codec={meta['video_codec']}, duration={meta['duration']}s, fps={meta['fps']}"
        )

        print("[Test] 11. Generating Thumbnail via FFmpeg...")
        dest_thumb = media_service.get_destination_thumbnail_path(job_id=1, generation_id=1)
        thumb_path = await media_service.generate_thumbnail(path, dest_thumb, duration=meta.get("duration"))
        assert thumb_path is not None, "Failed to generate thumbnail via FFmpeg"
        assert os.path.exists(thumb_path), "Thumbnail file does not exist"
        print(f"[Test] Thumbnail generated successfully: {thumb_path}")

        print("\n[Test] REAL FLOW GENERATION E2E TEST COMPLETED SUCCESSFULLY!")
