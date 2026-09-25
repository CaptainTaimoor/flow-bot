import os
import logging
import asyncio
from typing import Optional, Set, Callable, Tuple, Dict, Any
from playwright.async_api import Page, Locator
from src.config.settings import settings
from src.config.runtime_config import runtime_config
from src.models.domain import JobCreate, FlowCapabilities, CorrelationConfidence
from src.flow.selectors import FlowSelectors
from src.flow.capability_detection import FlowCapabilityDetector
from src.flow.projects import FlowProjectManager
from src.flow.assets import FlowAssetTracker
from src.flow.generation import FlowGenerationExecutor
from src.flow.reconciliation import FlowReconciliationManager

logger = logging.getLogger(__name__)

class GoogleFlowAdapter:
    """Consolidated Google Flow automation facade coordinating modular services."""

    def __init__(self, page: Page):
        self.page = page
        self.project_manager = FlowProjectManager(page)
        self.asset_tracker = FlowAssetTracker(page)
        self.generation_executor = FlowGenerationExecutor(page)
        self.reconciliation_manager = FlowReconciliationManager(page)
        self._baseline_assets: Set[str] = set()

    async def open_flow(self):
        """Navigates to Flow, dismisses onboarding overlays, and enters the project workspace."""
        flow_url = runtime_config.get("FLOW_URL", settings.FLOW_URL)
        logger.info(f"Navigating to Flow: {flow_url}...")
        await self.page.goto(flow_url, wait_until="domcontentloaded")
        await asyncio.sleep(3)
        await FlowCapabilityDetector.dismiss_transient_modals(self.page)
        await self.project_manager.ensure_project_open()
        await FlowCapabilityDetector.dismiss_transient_modals(self.page)

    async def detect_capabilities(self) -> FlowCapabilities:
        """Inspects and returns the truthful capabilities of the current Flow UI."""
        return await FlowCapabilityDetector.detect_capabilities(self.page)

    async def reconcile_prior_submission(
        self, prompt: str
    ) -> Tuple[bool, Optional[Locator], Dict[str, Any]]:
        """Checks if generation is already running or completed on canvas."""
        return await self.reconciliation_manager.reconcile_prior_submission(
            prompt, self._baseline_assets
        )

    async def select_parameters(self, job: JobCreate) -> Dict[str, Any]:
        """Configures model, aspect ratio, and output count in the Flow prompt bar."""
        return await self.generation_executor.select_parameters(job)

    async def prepare_for_submission(self) -> Set[str]:
        """Snapshots existing assets prior to prompt submission for correlation."""
        self._baseline_assets = await self.asset_tracker.snapshot_existing_assets()
        return self._baseline_assets

    async def submit_prompt(self, job: JobCreate) -> Tuple[bool, Dict[str, Any]]:
        """Submits the prompt into the workspace and handles confirmation."""
        auto_confirm = runtime_config.get("AUTO_CONFIRM_GENERATION", settings.AUTO_CONFIRM_GENERATION)
        return await self.generation_executor.submit_prompt_and_confirm(
            prompt=job.prompt,
            auto_confirm=auto_confirm,
        )

    async def locate_generated_tile(
        self, prompt: str, timeout_seconds: int = 45
    ) -> Tuple[Optional[Locator], CorrelationConfidence, Dict[str, Any]]:
        """
        Polls for the newly created tile on the canvas matching the current generation.
        Returns (tile, confidence, evidence).
        """
        start_time = asyncio.get_event_loop().time()
        last_evidence = {}
        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            tile, conf, evidence = await self.asset_tracker.find_new_asset_tile(
                self._baseline_assets, prompt
            )
            last_evidence = evidence
            if tile and conf in (CorrelationConfidence.HIGH, CorrelationConfidence.MEDIUM):
                return tile, conf, evidence
            await asyncio.sleep(3)

        # Final check if low confidence is present
        tile, conf, evidence = await self.asset_tracker.find_new_asset_tile(
            self._baseline_assets, prompt
        )
        return tile, conf, evidence or last_evidence

    async def wait_for_completion(
        self,
        tile: Optional[Locator],
        progress_callback: Optional[Callable[[Optional[int], str], None]] = None,
    ) -> bool:
        """Waits for generation to complete on the tile or general workspace."""
        gen_timeout = runtime_config.get("GENERATION_TIMEOUT", settings.GENERATION_TIMEOUT)
        if tile:
            return await self.generation_executor.wait_for_tile_completion(
                tile=tile,
                timeout_seconds=gen_timeout,
                progress_callback=progress_callback,
            )

        # Resilient fallback if specific tile handle wasn't isolated
        logger.info("Monitoring general workspace for completion...")
        start_time = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start_time < gen_timeout:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            if tiles:
                pb = tiles[0].locator(FlowSelectors.TILE_PROGRESS_BAR).first
                if await pb.count() == 0 or not await pb.is_visible():
                    if progress_callback:
                        progress_callback(100, "Rendering complete")
                    return True
            await asyncio.sleep(6)

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

        # Resilient fallback: close any open menus and locate completed valid tile
        logger.info("Target tile download unverified; attempting fallback to latest completed tile...")
        try:
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
        except Exception:
            pass

        tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
        for idx, t in enumerate(tiles):
            try:
                # Skip failed tiles
                failed = t.locator(":text-matches('error|failed', 'i')").first
                if await failed.count() > 0 and await failed.is_visible():
                    continue

                play = t.locator(FlowSelectors.PLAY_CIRCLE_ICON).first
                if await play.count() > 0 and await play.is_visible():
                    logger.info(f"Fallback downloading from completed tile index {idx}...")
                    downloaded = await self.asset_tracker.download_tile_asset(t, dest_path)
                    if downloaded:
                        return downloaded
            except Exception:
                continue

        return None

    async def cancel_active_generation(self, target_tile: Optional[Locator] = None) -> Tuple[bool, str]:
        """Attempts to cancel generation on Google Flow UI."""
        return await self.reconciliation_manager.attempt_cancellation(target_tile)
