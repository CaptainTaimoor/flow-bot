import os
import re
import logging
import asyncio
from datetime import datetime
from typing import Set, Optional, Dict, Any, List, Tuple
from playwright.async_api import Page, Locator
from src.flow.selectors import FlowSelectors
from src.models.domain import CorrelationConfidence

logger = logging.getLogger(__name__)

class FlowAssetTracker:
    def __init__(self, page: Page):
        self.page = page

    async def snapshot_existing_assets(self) -> Set[str]:
        """
        Takes an exhaustive snapshot of existing video tiles in the project workspace
        before submitting a new generation prompt.
        """
        identifiers: Set[str] = set()
        try:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            for idx, t in enumerate(tiles):
                # 1. Image source
                img = t.locator("img").first
                if await img.count() > 0:
                    src = await img.get_attribute("src") or ""
                    if src:
                        identifiers.add(f"src:{src}")

                # 2. Title text
                title = t.locator(FlowSelectors.TILE_TITLE).first
                if await title.count() > 0:
                    txt = (await title.inner_text()).strip()
                    if txt:
                        identifiers.add(f"title:{txt}")

                # 3. DOM id or attribute
                tile_id = await t.get_attribute("id") or await t.get_attribute("data-id")
                if tile_id:
                    identifiers.add(f"id:{tile_id}")

                # 4. Fallback index key
                identifiers.add(f"idx:{idx}")
        except Exception as e:
            logger.warning(f"Error taking asset baseline snapshot: {e}")

        logger.info(f"Asset baseline recorded with {len(identifiers)} fingerprint tokens.")
        return identifiers

    async def find_new_asset_tile(
        self, baseline: Set[str], prompt: str
    ) -> Tuple[Optional[Locator], CorrelationConfidence, Dict[str, Any]]:
        """
        Deterministic Layered Asset Correlation Engine.
        Evaluates 4 layers of evidence:
        1. Snapshot diff (tiles not in baseline)
        2. Prompt keyword matching
        3. Active rendering indicator (visible progress bar)
        4. DOM order and recency
        Returns (tile: Optional[Locator], confidence: CorrelationConfidence, evidence: Dict[str, Any]).
        """
        evidence: Dict[str, Any] = {
            "baseline_count": len(baseline),
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
            evidence["current_tile_count"] = len(tiles)
            if not tiles:
                return None, CorrelationConfidence.FAILED, evidence

            prompt_words = set(re.findall(r"\w+", prompt.lower()))

            candidate_evaluations: List[Dict[str, Any]] = []

            for idx, t in enumerate(tiles):
                img = t.locator("img").first
                src = (await img.get_attribute("src") or "") if await img.count() > 0 else ""
                title_loc = t.locator(FlowSelectors.TILE_TITLE).first
                txt = (await title_loc.inner_text()).strip() if await title_loc.count() > 0 else ""
                t_id = (await t.get_attribute("id") or "")

                is_in_baseline = (
                    (f"src:{src}" in baseline and src != "") or
                    (f"title:{txt}" in baseline and txt != "") or
                    (f"id:{t_id}" in baseline and t_id != "")
                )

                pb = t.locator(FlowSelectors.TILE_PROGRESS_BAR).first
                is_actively_rendering = False
                if await pb.count() > 0 and await pb.is_visible():
                    pb_style = await pb.get_attribute("style") or ""
                    pb_match = re.search(r"--progress-percent:\s*(\d+)%", pb_style)
                    if pb_match and 0 < int(pb_match.group(1)) < 100:
                        is_actively_rendering = True

                # Keyword match
                txt_words = set(re.findall(r"\w+", txt.lower()))
                word_overlap = len(prompt_words.intersection(txt_words))

                score = 0
                reasons = []

                if not is_in_baseline:
                    score += 40
                    reasons.append("snapshot_diff_new")
                if is_actively_rendering:
                    score += 35
                    reasons.append("active_progress_bar")
                if word_overlap > 0:
                    score += min(25, word_overlap * 10)
                    reasons.append(f"prompt_word_overlap_{word_overlap}")

                candidate_evaluations.append({
                    "tile": t,
                    "index": idx,
                    "score": score,
                    "is_new": not is_in_baseline,
                    "is_rendering": is_actively_rendering,
                    "overlap": word_overlap,
                    "reasons": reasons,
                    "title": txt,
                })

            # Sort candidates by score descending
            candidate_evaluations.sort(key=lambda x: x["score"], reverse=True)
            top = candidate_evaluations[0]
            evidence["candidates_evaluated"] = [
                {k: v for k, v in c.items() if k != "tile"} for c in candidate_evaluations[:5]
            ]

            # High confidence: New tile + actively rendering OR (New tile + prompt overlap)
            if top["score"] >= 65:
                logger.info(f"High confidence asset correlation (score={top['score']}): {top['reasons']}")
                return top["tile"], CorrelationConfidence.HIGH, evidence

            # Medium confidence: New tile or (active rendering + keyword overlap)
            if top["score"] >= 35:
                logger.info(f"Medium confidence asset correlation (score={top['score']}): {top['reasons']}")
                return top["tile"], CorrelationConfidence.MEDIUM, evidence

            # Low confidence: Some keyword overlap on existing tile
            if top["score"] >= 20:
                logger.warning(f"Low confidence asset correlation (score={top['score']}): {top['reasons']}")
                return top["tile"], CorrelationConfidence.LOW, evidence

            logger.warning(f"Asset correlation failed: top score {top['score']} below threshold.")
            return None, CorrelationConfidence.FAILED, evidence

        except Exception as e:
            logger.error(f"Error during deterministic asset correlation: {e}")
            evidence["error"] = str(e)
            return None, CorrelationConfidence.FAILED, evidence

    async def download_tile_asset(self, tile: Locator, destination_path: str) -> Optional[str]:
        """
        Downloads the asset specifically from the identified tile.
        Employs 4 resilient strategies:
        1. Hotbar menu -> Download item
        2. Viewer modal -> Download button
        3. Direct authenticated stream download from video tag src
        4. Global page download button
        """
        try:
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)

            # Strategy 1: Hover tile and click 'More options' -> Download -> Resolution Option (720p / 1080p)
            logger.info("Strategy 1: Hovering over target tile to reveal hotbar...")
            try:
                await tile.scroll_into_view_if_needed()
                await tile.hover()
                await asyncio.sleep(0.8)

                more_btn = tile.locator(FlowSelectors.TILE_MORE_OPTIONS).first
                if not await more_btn.is_visible():
                    await tile.hover()
                    await asyncio.sleep(0.5)

                if await more_btn.count() > 0:
                    logger.info("Opening tile options menu...")
                    await more_btn.click()
                    await asyncio.sleep(0.8)

                    menu_dl = self.page.locator(
                        "[role='menuitem']:has-text('Download'), .mat-mdc-menu-item:has-text('Download')"
                    ).first
                    if await menu_dl.count() > 0 and await menu_dl.is_visible():
                        logger.info("Revealing Download options submenu...")
                        await menu_dl.click()

                        # Explicitly wait for resolution options (720p / 1080p)
                        res_opt = self.page.locator(FlowSelectors.DOWNLOAD_QUALITY_OPTIONS).first
                        try:
                            await res_opt.wait_for(state="visible", timeout=6000)
                            logger.info(f"Selecting resolution option (720p/1080p)...")
                            async with self.page.expect_download(timeout=30000) as dl_info:
                                await res_opt.click()
                            download = await dl_info.value
                            await download.save_as(destination_path)
                            logger.info(f"Downloaded asset via resolution menu to {destination_path}")
                            return destination_path
                        except Exception as e_opt:
                            logger.warning(f"Resolution submenu wait failed: {e_opt}")
            except Exception as e1:
                logger.debug(f"Strategy 1 notice: {e1}")

            # Strategy 2: Click tile directly to open viewer and look for download
            logger.info("Strategy 2: Opening viewer modal for target tile...")
            try:
                await tile.click()
                await asyncio.sleep(2)

                viewer_dl = self.page.locator(FlowSelectors.DOWNLOAD_BUTTONS).first
                if await viewer_dl.count() > 0 and await viewer_dl.is_visible():
                    logger.info("Found download button in viewer modal!")
                    async with self.page.expect_download(timeout=25000) as dl_info:
                        await viewer_dl.click()
                    download = await dl_info.value
                    await download.save_as(destination_path)
                    logger.info(f"Viewer download saved to {destination_path}")

                    # Close viewer modal safely
                    close_btn = self.page.locator("button[aria-label*='Close' i], button:has-text('Close')").first
                    if await close_btn.count() > 0 and await close_btn.is_visible():
                        await close_btn.click()
                    else:
                        await self.page.keyboard.press("Escape")

                    return destination_path
            except Exception as e2:
                logger.debug(f"Strategy 2 notice: {e2}")

            # Strategy 3: Direct stream download from video tag src in viewer modal
            logger.info("Strategy 3: Checking for direct video stream element...")
            try:
                video_el = self.page.locator("video").first
                if await video_el.count() > 0:
                    v_src = await video_el.get_attribute("src") or ""
                    if v_src and v_src.startswith("http"):
                        logger.info("Fetching video stream via authenticated Playwright context...")
                        resp = await self.page.request.get(v_src)
                        if resp.status == 200:
                            content = await resp.body()
                            if len(content) > 1024:
                                with open(destination_path, "wb") as f:
                                    f.write(content)
                                logger.info(f"Direct stream download saved ({len(content)} bytes) to {destination_path}")
                                return destination_path
            except Exception as e3:
                logger.debug(f"Strategy 3 notice: {e3}")

            # Strategy 4: Direct download button fallback anywhere on page
            logger.info("Strategy 4: Checking direct download button fallback...")
            try:
                dl_btn = self.page.locator(FlowSelectors.DOWNLOAD_BUTTONS).first
                if await dl_btn.count() > 0 and await dl_btn.is_visible():
                    async with self.page.expect_download(timeout=25000) as dl_info:
                        await dl_btn.click()
                    download = await dl_info.value
                    await download.save_as(destination_path)
                    logger.info(f"Direct download saved to {destination_path}")
                    return destination_path
            except Exception as e4:
                logger.debug(f"Strategy 4 notice: {e4}")

        except Exception as e:
            logger.error(f"Failed to download asset from tile: {e}")

        return None
