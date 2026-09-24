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
        """Navigate to Flow URL and ensure project workspace is open."""
        logger.info(f"Navigating to {settings.FLOW_URL}...")
        # Use domcontentloaded to avoid hanging on persistent websockets
        await self.page.goto(settings.FLOW_URL, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        # Click the 'New project' button if on project gallery/landing
        try:
            new_proj_btn = self.page.locator("button:has-text('New project')").first
            if await new_proj_btn.count() > 0 and await new_proj_btn.is_visible():
                logger.info("Found 'New project' button. Clicking...")
                await new_proj_btn.click()
                await asyncio.sleep(5)
            else:
                logger.info("Checking if already in project workspace...")
        except Exception as e:
            logger.debug(f"Note on opening project: {e}")

    async def submit_prompt(self, job: JobCreate) -> bool:
        """Enters the prompt, clicks Start Generation, and auto-approves credit usage."""
        prompt_input = self.page.locator(".ProseMirror").first
        
        try:
            await prompt_input.wait_for(state="visible", timeout=20000)
        except TimeoutError:
            logger.error("Could not find prompt box (.ProseMirror). Taking debug screenshot...")
            os.makedirs(settings.DIAGNOSTICS_DIR, exist_ok=True)
            await self.page.screenshot(path=os.path.join(settings.DIAGNOSTICS_DIR, "debug_no_prosemirror.png"))
            return False

        logger.info(f"Typing prompt: {job.prompt[:40]}...")
        await prompt_input.click()
        await self.page.keyboard.type(job.prompt, delay=12)
        await asyncio.sleep(1)

        # Click Start generation
        generate_btn = self.page.locator("button[aria-label='Start generation']").first
        try:
            if await generate_btn.count() == 0:
                logger.error("Could not find 'Start generation' button.")
                return False
                
            await generate_btn.wait_for(state="visible", timeout=5000)
            await generate_btn.click()
            logger.info("Generate button clicked.")
        except TimeoutError:
            logger.error("Generate button did not become clickable.")
            return False
            
        # Check and handle credit confirmation ('Always approve' / 'Approve')
        logger.info("Checking for credit confirmation prompt...")
        for _ in range(8):
            await asyncio.sleep(1.5)
            approve_btn = self.page.locator(
                "button:has-text('Always approve'), [role='button']:has-text('Always approve'), "
                "button:has-text('Approve'), [role='button']:has-text('Approve')"
            ).first
            
            if await approve_btn.count() > 0 and await approve_btn.is_visible():
                btn_text = await approve_btn.inner_text()
                logger.info(f"Auto-confirming video generation with: '{btn_text}'")
                await approve_btn.click()
                await asyncio.sleep(2)
                return True
                
        # If no confirmation appeared, it may already be approved or directly started
        logger.info("Prompt submitted and accepted directly without prompt.")
        return True
            
    async def wait_for_generation(self) -> bool:
        """
        Monitors generation progress on Google Flow canvas.
        Detects flow-video-tile, progress bar, or queued status.
        """
        logger.info(f"Monitoring generation progress (timeout: {settings.GENERATION_TIMEOUT}s)...")
        start_time = asyncio.get_event_loop().time()
        
        while asyncio.get_event_loop().time() - start_time < settings.GENERATION_TIMEOUT:
            # Check if video tile appeared on canvas
            tile = self.page.locator("flow-video-tile").first
            if await tile.count() > 0:
                # Check if progress bar exists or has finished
                pb = tile.locator(".progress-bar")
                if await pb.count() > 0:
                    style = await pb.get_attribute("style") or ""
                    # If 100% or done
                    if "100%" in style:
                        logger.info("Video generation reached 100%!")
                        return True
                else:
                    # No progress bar on tile often means rendering is complete
                    logger.info("Video tile present with no active progress bar (ready).")
                    return True
                    
            # Check for direct download button
            dl = self.page.locator("button:has-text('Download'), button[aria-label*='Download' i]").first
            if await dl.count() > 0 and await dl.is_visible():
                logger.info("Direct download button is now visible!")
                return True
                
            # Check for video tag
            videos = await self.page.locator("video").all()
            for v in videos:
                src = await v.get_attribute("src") or ""
                if src and ("blob:" in src or "http" in src):
                    logger.info("Active video stream ready.")
                    return True
                    
            await asyncio.sleep(10)
            
        logger.warning("Generation wait reached configured timeout.")
        return False

    async def download_asset(self, job_id: int) -> str | None:
        """Downloads the generated asset from the tile menu or viewer."""
        try:
            # Method 1: Check direct download button
            dl_btn = self.page.locator("button:has-text('Download'), button[aria-label*='Download' i]").first
            if await dl_btn.count() > 0 and await dl_btn.is_visible():
                logger.info("Using direct download button...")
                return await self._trigger_download(dl_btn, job_id)

            # Method 2: Use flow-video-tile hover hotbar menu
            tile = self.page.locator("flow-video-tile").first
            if await tile.count() > 0:
                logger.info("Hovering over video tile to reveal hotbar...")
                await tile.hover()
                await asyncio.sleep(1)
                
                more_btn = tile.locator("button[aria-label='More options']").first
                if await more_btn.count() > 0:
                    logger.info("Opening tile options menu...")
                    await more_btn.click()
                    await asyncio.sleep(1.5)
                    
                    menu_dl = self.page.locator("[role='menuitem']:has-text('Download'), button:has-text('Download')").first
                    if await menu_dl.count() > 0 and await menu_dl.is_visible():
                        logger.info("Found Download in tile menu! Triggering...")
                        return await self._trigger_download(menu_dl, job_id)
                        
                # Method 3: Click tile directly to open viewer and look for download
                logger.info("Clicking video tile to open viewer...")
                await tile.click()
                await asyncio.sleep(2)
                
                viewer_dl = self.page.locator("button[aria-label*='Download' i], button:has-text('Download')").first
                if await viewer_dl.count() > 0 and await viewer_dl.is_visible():
                    logger.info("Found download button in viewer!")
                    return await self._trigger_download(viewer_dl, job_id)
                    
            logger.error("Could not locate download trigger on tile or viewer.")
            return None
        except Exception as e:
            logger.error(f"Error downloading asset: {e}")
            return None

    async def _trigger_download(self, locator, job_id: int) -> str:
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        file_path = os.path.join(settings.OUTPUT_DIR, f"generation_{job_id}.mp4")
        
        async with self.page.expect_download(timeout=20000) as dl_info:
            await locator.click()
        download = await dl_info.value
        await download.save_as(file_path)
        logger.info(f"Asset successfully saved to {file_path}")
        return file_path
