import os
import logging
import asyncio
from typing import Optional, Set, Callable
from playwright.async_api import Page, Locator
from src.config.settings import settings
from src.models.domain import JobCreate, FlowCapabilities
from src.flow.selectors import FlowSelectors
from src.flow.capability_detection import FlowCapabilityDetector
from src.flow.projects import FlowProjectManager
from src.flow.assets import FlowAssetTracker
from src.flow.generation import FlowGenerationExecutor
from src.flow.auth import AuthManager

logger = logging.getLogger(__name__)

class GoogleFlowAdapter:
    """Consolidated Google Flow automation facade coordinating modular services."""

    def __init__(self, page: Page):
        self.page = page
        self.project_manager = FlowProjectManager(page)
        self.asset_tracker = FlowAssetTracker(page)
        self.generation_executor = FlowGenerationExecutor(page)
        self._baseline_assets: Set[str] = set()

    async def open_flow(self):
        """Navigates to Flow and enters the project workspace."""
        logger.info(f"Navigating to Flow: {settings.FLOW_URL}...")
        await self.page.goto(settings.FLOW_URL, wait_until="domcontentloaded")
        await asyncio.sleep(4)
        await self.project_manager.ensure_project_open()

    async def detect_capabilities(self) -> FlowCapabilities:
        """Inspects and returns the live capabilities of the current Flow UI."""
        return await FlowCapabilityDetector.detect_capabilities(self.page)

    async def prepare_for_submission(self) -> Set[str]:
        """Snapshots existing assets prior to prompt submission for correlation."""
        self._baseline_assets = await self.asset_tracker.snapshot_existing_assets()
        return self._baseline_assets

    async def submit_prompt(self, job: JobCreate) -> bool:
        """Submits the prompt into the workspace and auto-approves credit prompts."""
        return await self.generation_executor.submit_prompt_and_confirm(
            prompt=job.prompt,
            auto_confirm=settings.AUTO_CONFIRM_GENERATION,
        )

    async def locate_generated_tile(self, prompt: str, timeout_seconds: int = 45) -> Optional[Locator]:
        """Polls for the newly created tile on the canvas matching the current generation."""
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            tile = await self.asset_tracker.find_new_asset_tile(self._baseline_assets, prompt)
            if tile:
                return tile
            await asyncio.sleep(4)
        return None

    async def wait_for_completion(
        self,
        tile: Optional[Locator],
        progress_callback: Optional[Callable[[Optional[int], str], None]] = None,
    ) -> bool:
        """Waits for generation to complete on the tile or general workspace."""
        if tile:
            return await self.generation_executor.wait_for_tile_completion(
                tile=tile,
                timeout_seconds=settings.GENERATION_TIMEOUT,
                progress_callback=progress_callback,
            )

        # Fallback if specific tile handle wasn't isolated
        logger.info("Monitoring general workspace for completion...")
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < settings.GENERATION_TIMEOUT:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            if tiles:
                pb = tiles[0].locator(FlowSelectors.TILE_PROGRESS_BAR).first
                if await pb.count() == 0:
                    if progress_callback:
                        progress_callback(100, "Rendering complete")
                    return True
            await asyncio.sleep(8)

        return False

    async def download_asset(
        self, job_id: int, generation_id: int, target_tile: Optional[Locator] = None
    ) -> Optional[str]:
        """Downloads the video asset to the designated media storage path."""
        from src.media.service import media_service
        dest_path = str(media_service.get_destination_video_path(job_id, generation_id))

        if target_tile:
            downloaded = await self.asset_tracker.download_tile_asset(target_tile, dest_path)
            if downloaded:
                return downloaded

        # Fallback to direct download button
        dl_btn = self.page.locator(FlowSelectors.DOWNLOAD_BUTTONS).first
        if await dl_btn.count() > 0 and await dl_btn.is_visible():
            logger.info("Attempting direct download button fallback...")
            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                async with self.page.expect_download(timeout=25000) as dl_info:
                    await dl_btn.click()
                dl = await dl_info.value
                await dl.save_as(dest_path)
                return dest_path
            except Exception as e:
                logger.error(f"Fallback download failed: {e}")

        return None
