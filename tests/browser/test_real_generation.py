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
        assert "Omni 1.1 Flash" in caps.models_available, f"Omni 1.1 Flash not in discovered models: {caps.models_available}"
        assert "Nano Banana 2" not in caps.models_available, "Image model Nano Banana 2 should not be in video models"
        assert caps.credit_status == "VERIFIED", f"Credit status is not VERIFIED: {caps.credit_status}"
        assert caps.credit_balance is not None and caps.credit_balance > 0, f"Credit balance invalid: {caps.credit_balance}"
        assert caps.orientations == ["16:9", "9:16"], f"Video orientations mismatch: {caps.orientations}"

        initial_credits = caps.credit_balance
        print(f"[Test] Initial Verified Credits: {initial_credits}")

        # =========================================================================
        # TEST VIDEO 1: Landscape 16:9 with lowest video model (Omni 1.1 Flash)
        # =========================================================================
        print("\n--- TEST 1: Generating Landscape (16:9) Video with Omni 1.1 Flash ---")
        print("[Test 1] 4. Taking Baseline Asset Snapshot...")
        baseline = await adapter.prepare_for_submission()
        print(f"[Test 1] Baseline snapshot contains {len(baseline)} tokens.")

        prompt_1 = "A peaceful Zen garden with smooth raked sand patterns and bamboo water fountain, 4k landscape"
        job_1 = JobCreate(
            prompt=prompt_1,
            model="Omni 1.1 Flash",
            orientation="16:9",
            duration="4",
            output_count=1,
        )

        print("[Test 1] 5. Selecting Parameters in Settings Panel (Omni 1.1 Flash, 16:9, x1)...")
        effective_cfg_1 = await adapter.select_parameters(job_1)
        print(f"[Test 1] Effective Configuration: {effective_cfg_1}")
        assert effective_cfg_1["effective_orientation"] == "16:9"

        print("[Test 1] 6. Submitting Prompt to Google Flow...")
        submitted_1, proof_1 = await adapter.submit_prompt(job_1)
        assert submitted_1 is True, f"Failed to submit prompt: {proof_1}"
        print(f"[Test 1] Prompt submitted successfully. Proof: {proof_1}")

        print("[Test 1] 7. Locating Generated Tile with Layered Correlation...")
        tile_1, conf_1, evid_1 = await adapter.locate_generated_tile(prompt_1, timeout_seconds=60)
        assert tile_1 is not None, f"Failed to locate generated tile. Evidence: {evid_1}"
        assert conf_1 in (CorrelationConfidence.HIGH, CorrelationConfidence.MEDIUM), f"Inadequate confidence: {conf_1}"
        print(f"[Test 1] Tile located with {conf_1.value} confidence.")

        def on_progress(pct, msg):
            print(f"       -> [Progress] {msg}")

        print("[Test 1] 8. Monitoring Generation Completion on Canvas...")
        completed_1 = await adapter.wait_for_completion(tile_1, progress_callback=on_progress)
        assert completed_1 is True, "Generation timed out on Google Flow canvas."
        print("[Test 1] Generation completed on canvas.")

        print("[Test 1] 9. Downloading Video Asset...")
        path_1 = await adapter.download_asset(job_id=1, generation_id=1, target_tile=tile_1)
        assert path_1 is not None and os.path.exists(path_1)
        file_size_1 = os.path.getsize(path_1)
        assert file_size_1 > 1000, f"File suspiciously small: {file_size_1} bytes"
        print(f"[Test 1] Video downloaded successfully: {path_1} ({file_size_1} bytes)")

        print("[Test 1] 10. Validating Media with FFprobe...")
        is_valid_1, meta_1 = await media_service.validate_video(path_1)
        assert is_valid_1 is True, f"FFprobe validation failed: {meta_1.get('error')}"
        assert meta_1["width"] >= meta_1["height"], f"Expected landscape 16:9 but got {meta_1['width']}x{meta_1['height']}"
        print(
            f"[Test 1] FFprobe Validation PASSED: {meta_1['width']}x{meta_1['height']}, "
            f"codec={meta_1['video_codec']}, duration={meta_1['duration']}s, fps={meta_1['fps']}"
        )

        print("[Test 1] 11. Generating Thumbnail via FFmpeg...")
        dest_thumb_1 = media_service.get_destination_thumbnail_path(job_id=1, generation_id=1)
        thumb_path_1 = await media_service.generate_thumbnail(path_1, dest_thumb_1, duration=meta_1.get("duration"))
        assert thumb_path_1 is not None and os.path.exists(thumb_path_1)
        print(f"[Test 1] Thumbnail generated successfully: {thumb_path_1}")

        # Check credits after Video 1
        caps_after_1 = await adapter.detect_capabilities()
        print(f"[Test 1] Credits after Video 1: {caps_after_1.credit_balance} (Initial: {initial_credits})")
        await asyncio.sleep(2)

        # =========================================================================
        # TEST VIDEO 2: Portrait 9:16 with lowest video model (Omni 1.1 Flash)
        # =========================================================================
        print("\n--- TEST 2: Generating Portrait (9:16) Video with Omni 1.1 Flash ---")
        baseline_2 = await adapter.prepare_for_submission()

        prompt_2 = "An elegant crystal hourglass with glowing blue sand falling vertically, dark background, 4k portrait"
        job_2 = JobCreate(
            prompt=prompt_2,
            model="Omni 1.1 Flash",
            orientation="9:16",
            duration="4",
            output_count=1,
        )

        print("[Test 2] Selecting Parameters in Settings Panel (Omni 1.1 Flash, 9:16, x1)...")
        effective_cfg_2 = await adapter.select_parameters(job_2)
        print(f"[Test 2] Effective Configuration: {effective_cfg_2}")
        assert effective_cfg_2["effective_orientation"] == "9:16"

        print("[Test 2] Submitting Prompt to Google Flow...")
        submitted_2, proof_2 = await adapter.submit_prompt(job_2)
        assert submitted_2 is True, f"Failed to submit prompt 2: {proof_2}"

        print("[Test 2] Locating Generated Tile...")
        tile_2, conf_2, evid_2 = await adapter.locate_generated_tile(prompt_2, timeout_seconds=60)
        assert tile_2 is not None, f"Failed to locate generated tile 2: {evid_2}"

        print("[Test 2] Monitoring Generation Completion...")
        completed_2 = await adapter.wait_for_completion(tile_2, progress_callback=on_progress)
        assert completed_2 is True, "Generation 2 timed out."

        print("[Test 2] Downloading Portrait Video Asset...")
        path_2 = await adapter.download_asset(job_id=2, generation_id=1, target_tile=tile_2)
        assert path_2 is not None and os.path.exists(path_2)

        print("[Test 2] Validating Media with FFprobe...")
        is_valid_2, meta_2 = await media_service.validate_video(path_2)
        assert is_valid_2 is True, f"FFprobe validation failed on video 2: {meta_2.get('error')}"
        assert meta_2["height"] > meta_2["width"], f"Expected portrait 9:16 (height > width) but got {meta_2['width']}x{meta_2['height']}"
        print(
            f"[Test 2] FFprobe Validation PASSED (Portrait 9:16 verified!): {meta_2['width']}x{meta_2['height']}, "
            f"codec={meta_2['video_codec']}, duration={meta_2['duration']}s, fps={meta_2['fps']}"
        )

        dest_thumb_2 = media_service.get_destination_thumbnail_path(job_id=2, generation_id=1)
        thumb_path_2 = await media_service.generate_thumbnail(path_2, dest_thumb_2, duration=meta_2.get("duration"))
        assert thumb_path_2 is not None and os.path.exists(thumb_path_2)
        print(f"[Test 2] Thumbnail generated successfully: {thumb_path_2}")

        caps_after_2 = await adapter.detect_capabilities()
        print(f"\n[Test] FINAL VERIFIED CREDITS: {caps_after_2.credit_balance} (Started at: {initial_credits})")
        print("[Test] BOTH LANDSCAPE (16:9) AND PORTRAIT (9:16) TESTS PASSED FLAWLESSLY WITH OMNI 1.1 FLASH!")

