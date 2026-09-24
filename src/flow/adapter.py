from playwright.async_api import Page, TimeoutError
from src.models.domain import JobCreate
from src.config.settings import settings
import logging
import asyncio
import os

logger = logging.getLogger(__name__)

class GoogleFlowAdapter:
    def __init__(self, page: Page):
        self.page = page

    async def open_flow(self):
        """Navigate to Flow URL and open a project."""
        logger.info(f"Navigating to {settings.FLOW_URL}")
        await self.page.goto(settings.FLOW_URL, wait_until="networkidle")
        
        # Click the new project button if we are on the project selection screen
        try:
            await asyncio.sleep(3) # allow buttons to render
            new_proj_btn = self.page.locator("button:has-text('New project')").first
            if await new_proj_btn.count() > 0:
                logger.info("Found 'New project' button. Clicking...")
                await new_proj_btn.click()
                await asyncio.sleep(8) # Wait for project workspace to load
            else:
                logger.info("No 'New project' button found. Attempting to proceed...")
        except Exception as e:
            logger.debug(f"Did not click 'New project', might already be in workspace: {e}")

    async def submit_prompt(self, job: JobCreate) -> bool:
        """Enters the prompt and clicks generate."""
        prompt_input = self.page.locator(".ProseMirror").first
        
        try:
            await prompt_input.wait_for(state="visible", timeout=15000)
        except TimeoutError:
            logger.error("Could not find prompt box (.ProseMirror). Taking debug screenshot...")
            os.makedirs(settings.DIAGNOSTICS_DIR, exist_ok=True)
            await self.page.screenshot(path=os.path.join(settings.DIAGNOSTICS_DIR, "debug_prosemirror.png"))
            return False

        logger.info(f"Filling prompt: {job.prompt[:30]}...")
        await prompt_input.click()
        await self.page.keyboard.type(job.prompt, delay=10)

        await asyncio.sleep(1)

        generate_btn = self.page.locator("button[aria-label='Start generation']").first
        try:
            if await generate_btn.count() == 0:
                logger.error("Could not find 'Start generation' button. Taking screenshot...")
                await self.page.screenshot(path=os.path.join(settings.DIAGNOSTICS_DIR, "debug_btn.png"))
                return False
                
            await generate_btn.wait_for(state="visible", timeout=5000)
            await generate_btn.click()
            logger.info("Generate button clicked.")
            return True
        except TimeoutError:
            logger.error("Generate button did not become visible/clickable.")
            await self.page.screenshot(path=os.path.join(settings.DIAGNOSTICS_DIR, "debug_btn_timeout.png"))
            return False
            
    async def wait_for_generation(self) -> bool:
        """Waits for the generation to complete."""
        logger.info(f"Waiting for generation to complete (timeout {settings.GENERATION_TIMEOUT}s)...")
        try:
            success_indicator = self.page.locator("video, button:has-text('Download')").first
            await success_indicator.wait_for(state="visible", timeout=settings.GENERATION_TIMEOUT * 1000)
            return True
        except TimeoutError:
            logger.error("Generation timed out.")
            return False

    async def download_asset(self, job_id: int) -> str | None:
        """Finds the generated asset and downloads it."""
        try:
            download_btn = self.page.locator("button:has-text('Download'), button[aria-label*='Download']").first
            
            if await download_btn.count() > 0:
                async with self.page.expect_download() as download_info:
                    await download_btn.click()
                download = await download_info.value
                
                os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
                file_path = os.path.join(settings.OUTPUT_DIR, f"generation_{job_id}.mp4")
                await download.save_as(file_path)
                logger.info(f"Downloaded asset to {file_path}")
                return file_path
            else:
                logger.error("Could not find download button for asset.")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading asset: {e}")
            return None
