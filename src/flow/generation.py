import re
import logging
import asyncio
from datetime import datetime
from typing import Callable, Optional, Dict, Any, Tuple
from playwright.async_api import Page, Locator
from src.flow.selectors import FlowSelectors
from src.models.domain import JobCreate, normalize_aspect_ratio

logger = logging.getLogger(__name__)

class FlowGenerationExecutor:
    def __init__(self, page: Page):
        self.page = page

    async def select_parameters(self, job: JobCreate) -> Dict[str, Any]:
        """
        Interacts with Flow UI controls to select requested model, orientation, and output count.
        Returns the effective configuration verified from the live UI.
        """
        effective = {
            "effective_model": None,
            "effective_orientation": normalize_aspect_ratio(job.orientation) or "16:9",
            "effective_duration": job.duration or "5",
            "effective_output_count": job.output_count or 1,
        }

        # 1. Model Selection
        model_pill = self.page.locator(FlowSelectors.MODEL_SELECTOR_PILL).first
        if await model_pill.count() > 0 and await model_pill.is_visible():
            current_pill_text = (await model_pill.inner_text()).strip()
            clean_current = re.sub(r"[^\w\s\.-]", "", current_pill_text).strip()
            effective["effective_model"] = clean_current

            # If user requested a specific model and it differs from current
            if job.model and job.model.lower() not in clean_current.lower():
                logger.info(f"Requested model '{job.model}' differs from current '{clean_current}'. Selecting...")
                try:
                    await model_pill.click()
                    await asyncio.sleep(1)
                    options = self.page.locator(FlowSelectors.MODEL_MENU_OPTIONS)
                    opt_count = await options.count()
                    matched = False
                    for i in range(opt_count):
                        opt = options.nth(i)
                        txt = (await opt.inner_text()).strip().lower()
                        if job.model.lower() in txt:
                            logger.info(f"Found matching model option: {txt}. Clicking...")
                            await opt.click()
                            await asyncio.sleep(1)
                            matched = True
                            break

                    if not matched:
                        logger.warning(f"Requested model '{job.model}' not found in Flow options menu. Retaining '{clean_current}'.")
                        await self.page.keyboard.press("Escape")
                    else:
                        # Re-read pill to confirm
                        new_pill_text = (await model_pill.inner_text()).strip()
                        clean_new = re.sub(r"[^\w\s\.-]", "", new_pill_text).strip()
                        effective["effective_model"] = clean_new
                except Exception as e:
                    logger.warning(f"Error during model selection: {e}")
                    try:
                        await self.page.keyboard.press("Escape")
                    except Exception:
                        pass

        # 2. Aspect Ratio / Orientation Selection
        if job.orientation:
            norm_orient = normalize_aspect_ratio(job.orientation)
            orient_btn = self.page.locator(f"button:has-text('{norm_orient}')").first
            if await orient_btn.count() > 0 and await orient_btn.is_visible():
                try:
                    await orient_btn.click()
                    effective["effective_orientation"] = norm_orient
                    logger.info(f"Selected orientation '{norm_orient}'.")
                except Exception as e:
                    logger.debug(f"Orientation selection notice: {e}")

        # 3. Output Count Selection
        if job.output_count and job.output_count > 1:
            count_btn = self.page.locator(f"button:has-text('x{job.output_count}')").first
            if await count_btn.count() > 0 and await count_btn.is_visible():
                try:
                    await count_btn.click()
                    effective["effective_output_count"] = job.output_count
                    logger.info(f"Selected output count x{job.output_count}.")
                except Exception as e:
                    logger.debug(f"Output count selection notice: {e}")

        return effective

    async def submit_prompt_and_confirm(
        self, prompt: str, auto_confirm: bool = True
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Fills prompt, triggers generation, handles confirmation modals,
        and returns (confirmed: bool, proof: Dict[str, Any]).
        """
        proof: Dict[str, Any] = {
            "submitted_at": datetime.utcnow().isoformat(),
            "prompt_length": len(prompt),
        }

        prompt_input = self.page.locator(FlowSelectors.PROMPT_INPUT).first
        await prompt_input.wait_for(state="visible", timeout=20000)

        logger.info(f"Entering prompt: '{prompt[:45]}...'")
        await prompt_input.click()
        
        # Select all and delete previous content if any
        await self.page.keyboard.press("Control+A")
        await self.page.keyboard.press("Backspace")
        await asyncio.sleep(0.3)

        # Type prompt
        await self.page.keyboard.type(prompt, delay=10)
        await asyncio.sleep(1)

        generate_btn = self.page.locator(FlowSelectors.GENERATE_BTN).first
        await generate_btn.wait_for(state="visible", timeout=10000)

        # Check if generate button is disabled
        is_disabled = await generate_btn.is_disabled()
        if is_disabled:
            logger.error("Generate button is disabled.")
            proof["error"] = "Generate button disabled"
            return False, proof

        await generate_btn.click()
        logger.info("Generate button clicked.")
        proof["generate_clicked"] = True

        # Check for credit confirmation or approval dialogue
        if auto_confirm:
            logger.info("Monitoring for credit approval prompt...")
            for _ in range(8):
                await asyncio.sleep(1.2)
                approve_btn = self.page.locator(
                    f"{FlowSelectors.ALWAYS_APPROVE_BTN}, {FlowSelectors.APPROVE_BTN}"
                ).first
                if await approve_btn.count() > 0 and await approve_btn.is_visible():
                    logger.info("Found credit confirmation dialogue. Auto-approving...")
                    btn_text = (await approve_btn.inner_text()).strip()
                    await approve_btn.click()
                    proof["auto_approved"] = True
                    proof["approval_button_text"] = btn_text
                    await asyncio.sleep(2)
                    return True, proof

        # Verify generation actually initiated (active indicator or input clearing)
        active_ind = self.page.locator(FlowSelectors.GENERATION_ACTIVE_INDICATOR).first
        if await active_ind.count() > 0 and await active_ind.is_visible():
            proof["active_indicator_verified"] = True
            return True, proof

        # If no explicit indicator, assume submission sent
        proof["active_indicator_verified"] = False
        return True, proof

    async def wait_for_tile_completion(
        self,
        tile: Locator,
        timeout_seconds: int = 600,
        progress_callback: Optional[Callable[[Optional[int], str], None]] = None,
    ) -> bool:
        """
        Monitors an individual video tile on canvas until it reaches 100% or renders media.
        Detects failure banners or error states.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"Waiting for tile completion (timeout: {timeout_seconds}s)...")

        # Initial wait for Flow canvas to initialize render
        await asyncio.sleep(5)

        last_percent = -1

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            # Check for error badge/text on tile
            error_el = tile.locator(":text-matches('error|failed|policy|retry', 'i')").first
            if await error_el.count() > 0 and await error_el.is_visible():
                err_text = (await error_el.inner_text()).strip()
                logger.error(f"Tile indicated generation error: {err_text}")
                raise Exception(f"Flow generation failed on canvas: {err_text}")

            # 1. Play icon visible on tile -> definitively complete and playable!
            play_circle = tile.locator(FlowSelectors.PLAY_CIRCLE_ICON).first
            if await play_circle.count() > 0 and await play_circle.is_visible():
                logger.info("Play circle icon visible on tile - rendering complete!")
                if progress_callback:
                    progress_callback(100, "Rendering complete")
                return True

            # 2. Video element present inside tile -> definitively complete!
            video = tile.locator("video").first
            if await video.count() > 0 and await video.is_visible():
                logger.info("Video element visible in tile - rendering complete!")
                if progress_callback:
                    progress_callback(100, "Rendering complete")
                return True

            # 3. Check progress bar
            pb = tile.locator(FlowSelectors.TILE_PROGRESS_BAR).first
            if await pb.count() > 0 and await pb.is_visible():
                style = await pb.get_attribute("style") or ""
                match = re.search(r"--progress-percent:\s*(\d+)%", style)
                if match:
                    percent = int(match.group(1))
                    if 0 < percent < 100:
                        if percent != last_percent:
                            last_percent = percent
                            if progress_callback:
                                progress_callback(percent, f"Generating ({percent}%)")
                    elif percent >= 100:
                        logger.info("Tile progress bar reached 100%!")
                        if progress_callback:
                            progress_callback(100, "Rendering complete")
                        return True
                    elif percent == 0:
                        # Flow resets progress bar to 0% after completion - check if thumbnail is loaded
                        thumb = tile.locator(FlowSelectors.TILE_THUMBNAIL).first
                        if await thumb.count() > 0 and await thumb.is_visible():
                            src = await thumb.get_attribute("src") or ""
                            if src and ("asb" in src or "blob" in src or "http" in src):
                                logger.info("Thumbnail loaded and progress complete - rendering finished!")
                                if progress_callback:
                                    progress_callback(100, "Rendering complete")
                                return True

            # 4. Check if thumbnail image is rendered and hotbar buttons exist
            thumb = tile.locator(FlowSelectors.TILE_THUMBNAIL).first
            if await thumb.count() > 0 and await thumb.is_visible():
                src = await thumb.get_attribute("src") or ""
                if src and ("asb" in src or "blob" in src or "http" in src):
                    # Check if hotbar options are available
                    more_btn = tile.locator(FlowSelectors.TILE_MORE_OPTIONS).first
                    if await more_btn.count() > 0:
                        logger.info("Rendered media thumbnail and hotbar detected - rendering complete!")
                        if progress_callback:
                            progress_callback(100, "Rendering complete")
                        return True

            await asyncio.sleep(3)

        logger.warning(f"Tile generation wait timed out after {timeout_seconds}s.")
        return False
