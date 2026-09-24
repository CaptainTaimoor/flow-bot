import os
import re
import logging
import asyncio
from typing import Set, Optional, Dict, Any, List
from playwright.async_api import Page, Locator
from src.flow.selectors import FlowSelectors

logger = logging.getLogger(__name__)

class FlowAssetTracker:
    def __init__(self, page: Page):
        self.page = page

    async def snapshot_existing_assets(self) -> Set[str]:
        """
        Takes a snapshot of all existing video tiles in the project workspace
        before submitting a new generation prompt.
        """
        identifiers: Set[str] = set()
        try:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            for t in tiles:
                # Capture thumbnail source, ID or title
                img = t.locator("img").first
                if await img.count() > 0:
                    src = await img.get_attribute("src") or ""
                    if src:
                        identifiers.add(src)
                title = t.locator(".footer-title, [class*='title']").first
                if await title.count() > 0:
                    txt = (await title.inner_text()).strip()
                    if txt:
                        identifiers.add(f"title:{txt}")
        except Exception as e:
            logger.warning(f"Error taking asset baseline snapshot: {e}")

        logger.info(f"Asset baseline recorded with {len(identifiers)} existing items.")
        return identifiers

    async def find_new_asset_tile(self, baseline: Set[str], prompt: str) -> Optional[Locator]:
        """
        Locates the new asset tile created specifically by this generation job.
        Uses multi-signal correlation:
        1. Compares against baseline snapshot.
        2. Checks prompt keywords in tile footer.
        3. Identifies active progress bar on the newly added tile.
        """
        try:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            new_candidates: List[Locator] = []

            for t in tiles:
                img = t.locator("img").first
                src = (await img.get_attribute("src") or "") if await img.count() > 0 else ""
                title_loc = t.locator(".footer-title, [class*='title']").first
                txt = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else ""

                is_in_baseline = (src in baseline) or (f"title:{txt}" in baseline)
                if not is_in_baseline:
                    new_candidates.append(t)

            if len(new_candidates) == 1:
                logger.info("Found exactly 1 new video tile matching current generation!")
                return new_candidates[0]
            elif len(new_candidates) > 1:
                logger.info(f"Found {len(new_candidates)} new tiles, correlating by prompt...")
                prompt_words = set(re.findall(r"\w+", prompt.lower()))
                best_match = new_candidates[0]
                best_score = -1

                for cand in new_candidates:
                    title_loc = cand.locator(".footer-title, [class*='title']").first
                    if await title_loc.count() > 0:
                        cand_title = (await title_loc.inner_text()).lower()
                        score = sum(1 for w in prompt_words if w in cand_title)
                        if score > best_score:
                            best_score = score
                            best_match = cand

                return best_match
            elif len(tiles) > 0:
                # If no strictly new candidate, correlate against all existing tiles
                logger.info(f"Correlating across all {len(tiles)} tiles on canvas by prompt keywords...")
                prompt_words = set(re.findall(r"\w+", prompt.lower()))
                best_match = tiles[0]
                best_score = -1

                for t in tiles:
                    title_loc = t.locator(".footer-title, [class*='title']").first
                    if await title_loc.count() > 0:
                        cand_title = (await title_loc.inner_text()).lower()
                        score = sum(1 for w in prompt_words if w in cand_title)
                        if score > best_score:
                            best_score = score
                            best_match = t

                return best_match
        except Exception as e:
            logger.error(f"Error during asset correlation: {e}")

        return None

    async def download_tile_asset(self, tile: Locator, destination_path: str) -> Optional[str]:
        """
        Downloads the asset specifically from the identified tile.
        Tries hotbar menu download first, viewer modal download, then direct button fallback.
        """
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Strategy A: Hover tile and click 'More options' -> Download
            logger.info("Hovering over target tile to reveal hotbar...")
            await tile.hover()
            await asyncio.sleep(1)

            more_btn = tile.locator("button[aria-label*='More' i], button[aria-label*='options' i]").first
            if await more_btn.count() > 0:
                logger.info("Opening tile options menu...")
                await more_btn.click()
                await asyncio.sleep(1.5)

                menu_dl = self.page.locator(
                    "[role='menuitem']:has-text('Download'), button:has-text('Download'), [data-tooltip*='Download' i]"
                ).first
                if await menu_dl.count() > 0 and await menu_dl.is_visible():
                    logger.info("Clicking Download in tile menu...")
                    async with self.page.expect_download(timeout=25000) as dl_info:
                        await menu_dl.click()
                    download = await dl_info.value
                    await download.save_as(destination_path)
                    logger.info(f"Successfully downloaded asset to {destination_path}")
                    return destination_path

            # Strategy B: Click tile directly to open viewer and look for download
            logger.info("Opening viewer modal for target tile...")
            await tile.click()
            await asyncio.sleep(2)

            viewer_dl = self.page.locator(
                "button[aria-label*='Download' i], button:has-text('Download'), [data-tooltip*='Download' i]"
            ).first
            if await viewer_dl.count() > 0 and await viewer_dl.is_visible():
                logger.info("Found download button in viewer modal!")
                async with self.page.expect_download(timeout=25000) as dl_info:
                    await viewer_dl.click()
                download = await dl_info.value
                await download.save_as(destination_path)
                logger.info(f"Viewer download saved to {destination_path}")

                # Close viewer if close button present
                close_btn = self.page.locator("button[aria-label*='Close' i]").first
                if await close_btn.count() > 0 and await close_btn.is_visible():
                    await close_btn.click()

                return destination_path

            # Strategy C: Check direct download button anywhere on canvas/page
            dl_btn = self.page.locator("button:has-text('Download'), button[aria-label*='Download' i]").first
            if await dl_btn.count() > 0 and await dl_btn.is_visible():
                logger.info("Found direct download button on page!")
                async with self.page.expect_download(timeout=25000) as dl_info:
                    await dl_btn.click()
                download = await dl_info.value
                await download.save_as(destination_path)
                logger.info(f"Direct download saved to {destination_path}")
                return destination_path

            # Strategy D: Direct stream download from video tag src
            video_el = self.page.locator("video").first
            if await video_el.count() > 0:
                v_src = await video_el.get_attribute("src") or ""
                if v_src and v_src.startswith("http"):
                    logger.info("Fetching video stream via authenticated Playwright context...")
                    resp = await self.page.request.get(v_src)
                    if resp.status == 200:
                        content = await resp.body()
                        with open(destination_path, "wb") as f:
                            f.write(content)
                        logger.info(f"Direct stream download saved ({len(content)} bytes) to {destination_path}")
                        return destination_path

        except Exception as e:
            logger.error(f"Failed to download asset from tile: {e}")

        return None
