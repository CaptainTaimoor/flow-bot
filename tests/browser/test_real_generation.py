import pytest
import asyncio
from src.browser.manager import BrowserManager
from src.flow.adapter import GoogleFlowAdapter
from src.flow.auth import AuthManager, AuthState
from src.config.settings import settings
from src.models.domain import JobCreate
import os

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
        
        print("Opening Flow...")
        await adapter.open_flow()
        
        status = await AuthManager.check_auth_status(page)
        if status != AuthState.AUTHENTICATED:
            print("Not authenticated. Please run the CLI `auth` command first.")
            pytest.skip("Not authenticated")
            
        print("Submitting prompt...")
        test_prompt = "A cinematic landscape shot of a peaceful mountain lake at sunrise, realistic lighting, slow camera movement."
        job = JobCreate(prompt=test_prompt)
        
        success = await adapter.submit_prompt(job)
        assert success, "Failed to submit prompt"
        
        print("Waiting for generation...")
        gen_success = await adapter.wait_for_generation()
        assert gen_success, "Generation timed out"
        
        print("Downloading asset...")
        # Note: We simulate job_id = 999 for test
        path = await adapter.download_asset(999)
        assert path is not None, "Failed to download asset"
        assert os.path.exists(path), "Downloaded file does not exist"
        
        print(f"SUCCESS: Downloaded to {path}")
    finally:
        await manager.stop()
