import re
import logging
import asyncio
from typing import Callable, Optional, Dict, Any
from playwright.async_api import Page, Locator
from src.flow.selectors import FlowSelectors
from src.models.domain import GenerationState
from src.config.settings import settings

logger = logging.getLogger(__name__)

class FlowGenerationExecutor:
    def __init__(self, page: Page):
        self.page = page

    async def submit_prompt_and_confirm(
        self, prompt: str, auto_confirm: bool = True
    ) -> bool:
        """Types prompt, triggers generation, and handles approval prompt if present."""
        prompt_input = self.page.locator(FlowSelectors.PROMPT_INPUT).first
        await prompt_input.wait_for(state="visible", timeout=20000)

        logger.info(f"Filling prompt: '{prompt[:40]}...'")
        await prompt_input.click()
        await self.page.keyboard.type(prompt, delay=12)
        await asyncio.sleep(1)

        generate_btn = self.page.locator(FlowSelectors.GENERATE_BTN).first
        await generate_btn.wait_for(state="visible", timeout=6000)
        await generate_btn.click()
        logger.info("Generation button clicked.")

        # Check for credit confirmation
        if auto_confirm:
            logger.info("Checking for credit confirmation prompt...")
            for _ in range(8):
                await asyncio.sleep(1.5)
                approve_btn = self.page.locator(
                    f"{FlowSelectors.ALWAYS_APPROVE_BTN}, {FlowSelectors.APPROVE_BTN}"
                ).first
                if await approve_btn.count() > 0 and await approve_btn.is_visible():
                    logger.info("Auto-confirming generation prompt...")
                    await approve_btn.click()
                    await asyncio.sleep(2)
                    return True

        return True

    async def wait_for_tile_completion(
        self,
        tile: Locator,
        timeout_seconds: int = 600,
        progress_callback: Optional[Callable[[Optional[int], str], None]] = None,
    ) -> bool:
        """
        Monitors an individual video tile on the canvas until it reaches 100%
        or finishes rendering.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"Waiting for tile completion (timeout: {timeout_seconds}s)...")

        # Initial grace period to allow Google Flow to register generation
        await asyncio.sleep(5)

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            # 1. Check if a video tag is present in tile (definitive proof of ready video)
            video = tile.locator("video").first
            if await video.count() > 0:
                logger.info("Video element detected inside tile - rendering complete!")
                if progress_callback:
                    progress_callback(100, "Rendering complete")
                return True

            # 2. Check if options hotbar button or download button is visible on tile
            more_opt = tile.locator("button[aria-label*='More' i], button[aria-label*='Download' i]").first
            if await more_opt.count() > 0 and await more_opt.is_visible():
                logger.info("Tile action button active - rendering complete!")
                if progress_callback:
                    progress_callback(100, "Rendering complete")
                return True

            # 3. Check progress bar style
            pb = tile.locator(f"{FlowSelectors.TILE_PROGRESS_BAR}, [role='progressbar'], flow-progress-bar").first
            if await pb.count() > 0:
                style = await pb.get_attribute("style") or ""
                match = re.search(r"--progress-percent:\s*(\d+)%", style)
                if match:
                    percent = int(match.group(1))
                    if progress_callback:
                        progress_callback(percent, f"Generating ({percent}%)")
                    if percent >= 100:
                        logger.info("Tile reached 100% completion!")
                        return True
            else:
                # Progress bar is not present / finished: verify thumbnail or media is active
                media = tile.locator("img, canvas").first
                if await media.count() > 0:
                    logger.info("Progress bar absent and media rendered inside tile.")
                    if progress_callback:
                        progress_callback(100, "Rendering complete")
                    return True

            await asyncio.sleep(4)

        logger.warning("Tile generation wait timed out.")
        return False
