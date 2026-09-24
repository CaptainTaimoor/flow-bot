import pytest
import asyncio
import os
from src.browser.manager import BrowserManager
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager, AuthState
from src.config.settings import settings
from src.models.domain import JobCreate

# Note: Run this carefully, as it consumes credits.
# Usage: pytest tests/browser/test_real_generation.py -s

@pytest.mark.asyncio
async def test_real_generation_single():
    # Force test configuration
    settings.HEADLESS = False
    
    manager = BrowserManager()
    await manager.start()
    
    try:
        page = await manager.get_page()
        adapter = GoogleFlowAdapter(page)
        
        print("\n[Test] Opening Flow...")
        await adapter.open_flow()
        
        status = await AuthManager.check_auth_status(page)
        if status != AuthState.AUTHENTICATED:
            print("[Test] Not authenticated. Please run the CLI `auth` command first.")
            pytest.skip("Not authenticated")
            
        print("[Test] Taking baseline asset snapshot...")
        await adapter.prepare_for_submission()

        print("[Test] Submitting prompt...")
        test_prompt = "A cinematic landscape shot of a peaceful mountain lake at sunrise, realistic lighting, slow camera movement."
        job = JobCreate(prompt=test_prompt)
        
        success = await adapter.submit_prompt(job)
        assert success, "Failed to submit prompt"
        
        print("[Test] Locating generated tile...")
        tile = await adapter.locate_generated_tile(test_prompt, timeout_seconds=60)
        
        print("[Test] Waiting for generation completion...")
        gen_success = await adapter.wait_for_completion(tile)
        assert gen_success, "Generation timed out"
        
        print("[Test] Downloading asset...")
        path = await adapter.download_asset(job_id=999, generation_id=1, target_tile=tile)
        assert path is not None, "Failed to download asset"
        assert os.path.exists(path), "Downloaded file does not exist"
        assert os.path.getsize(path) > 1000, "Downloaded file is empty or corrupted"
        
        print(f"\n[Test] SUCCESS: Video asset validated and downloaded to {path}")
    finally:
        await manager.stop()
