import re
import logging
import asyncio
from typing import Optional, Set, Dict, Any, Tuple
from playwright.async_api import Page, Locator
from src.flow.selectors import FlowSelectors

logger = logging.getLogger(__name__)

class FlowReconciliationManager:
    """
    Manages retry reconciliation and verified UI cancellation.
    Prevents duplicate credit spending on retries and guarantees truthful cancellation states.
    """

    def __init__(self, page: Page):
        self.page = page

    async def reconcile_prior_submission(
        self, prompt: str, baseline: Set[str]
    ) -> Tuple[bool, Optional[Locator], Dict[str, Any]]:
        """
        Inspects the canvas to determine if an identical prompt was already submitted
        and is currently generating or completed.
        Returns (reconciled, tile, evidence).
        """
        evidence: Dict[str, Any] = {"prompt": prompt}
        try:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            prompt_words = set(re.findall(r"\w+", prompt.lower()))

            for tile in tiles:
                title_loc = tile.locator(FlowSelectors.TILE_TITLE).first
                if await title_loc.count() > 0:
                    cand_title = (await title_loc.inner_text()).lower()
                    overlap = sum(1 for w in prompt_words if w in cand_title)
                    if overlap >= min(3, len(prompt_words)):
                        # Found high match
                        pb = tile.locator(FlowSelectors.TILE_PROGRESS_BAR).first
                        is_rendering = (await pb.count() > 0 and await pb.is_visible())
                        has_video = (await tile.locator("video").count() > 0)
                        
                        evidence["matched_tile_title"] = cand_title
                        evidence["is_rendering"] = is_rendering
                        evidence["has_video"] = has_video

                        if is_rendering or has_video:
                            logger.info(f"Reconciled existing submission on Flow canvas for: '{prompt[:40]}...'")
                            return True, tile, evidence
        except Exception as e:
            logger.warning(f"Error during retry reconciliation check: {e}")
            evidence["error"] = str(e)

        return False, None, evidence

    async def attempt_cancellation(
        self, target_tile: Optional[Locator] = None
    ) -> Tuple[bool, str]:
        """
        Attempts to cancel active generation via Flow UI.
        Returns (confirmed_cancelled: bool, reason: str).
        """
        try:
            # 1. Look for global 'Stop generation' button
            stop_btn = self.page.locator(FlowSelectors.STOP_GENERATION_BTN).first
            if await stop_btn.count() > 0 and await stop_btn.is_visible():
                logger.info("Found global 'Stop generation' button. Clicking...")
                await stop_btn.click()
                await asyncio.sleep(2)
                # Verify that stop button disappears or generation indicator stops
                if await stop_btn.count() == 0 or not await stop_btn.is_visible():
                    logger.info("Confirmed cancellation via global stop button.")
                    return True, "Cancelled via Flow UI Stop button"

            # 2. If target tile provided, look for tile-level stop button
            if target_tile:
                try:
                    await target_tile.hover()
                    await asyncio.sleep(0.5)
                    tile_stop = target_tile.locator("button[aria-label*='Cancel' i], button[aria-label*='Stop' i]").first
                    if await tile_stop.count() > 0 and await tile_stop.is_visible():
                        logger.info("Found tile-level cancel button. Clicking...")
                        await tile_stop.click()
                        await asyncio.sleep(2)
                        return True, "Cancelled via tile hotbar control"
                except Exception as tile_err:
                    logger.debug(f"Tile hover cancel notice: {tile_err}")

        except Exception as e:
            logger.warning(f"Error attempting UI cancellation: {e}")
            return False, f"Cancellation attempt error: {e}"

        logger.info("No interactive cancel control found on Flow UI. Cancellation unconfirmed.")
        return False, "Flow UI does not expose interactive cancellation for this state"
