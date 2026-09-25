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
        Configures model, aspect ratio, duration, and output count using Flow's Video generation popup.
        Ensures Agent mode is toggled off and side panels are closed so generation spawns on the canvas.
        Returns the effective configuration verified from the live UI.
        """
        norm_orient = normalize_aspect_ratio(job.orientation) or "16:9"
        if norm_orient not in ["16:9", "9:16"]:
            norm_orient = "16:9"

        target_model = job.model or "Omni 1.1 Flash"
        target_count = job.output_count or 1
        target_dur = str(job.duration or "8").rstrip("s")
        if target_dur not in ["4", "6", "8", "10"]:
            target_dur = "8"

        effective = {
            "effective_model": target_model,
            "effective_orientation": norm_orient,
            "effective_duration": target_dur,
            "effective_output_count": target_count,
            "estimated_credits": None,
        }

        try:
            # 1. Close any open side panel or chat session
            close_btn = self.page.locator(FlowSelectors.PANEL_CLOSE_BTN).first
            if await close_btn.count() > 0 and await close_btn.is_visible():
                logger.info("Closing open side panel...")
                await close_btn.click()
                await asyncio.sleep(0.8)

            # 2. Ensure Agent mode is toggled OFF (direct media generation mode)
            agent_chip = self.page.locator(FlowSelectors.AGENT_MODE_CHIP).first
            if await agent_chip.count() > 0 and await agent_chip.is_visible():
                is_pressed = await agent_chip.get_attribute("aria-pressed")
                if is_pressed == "true":
                    logger.info("Toggling off Agent mode for direct canvas generation...")
                    await agent_chip.click()
                    await asyncio.sleep(0.8)

            # 3. Open prompt settings popup
            trigger = self.page.locator(FlowSelectors.SETTINGS_TRIGGER_BTN).first
            await trigger.wait_for(state="visible", timeout=10000)
            logger.info("Opening prompt settings popup...")

            overlay = self.page.locator(".cdk-overlay-pane:has(mat-button-toggle)").first
            for attempt in range(3):
                if await overlay.count() > 0 and await overlay.is_visible():
                    break
                await trigger.click()
                try:
                    await overlay.wait_for(state="visible", timeout=3500)
                    break
                except Exception:
                    logger.debug(f"Retrying settings trigger click (attempt {attempt+1})...")
                    await asyncio.sleep(0.5)

            await overlay.wait_for(state="visible", timeout=5000)

            # 4. Activate 'Video' tab inside overlay
            video_tab = overlay.locator("mat-button-toggle:has-text('Video')").first
            if await video_tab.count() > 0 and await video_tab.is_visible():
                logger.info("Selecting 'Video' tab in settings popup...")
                await video_tab.click()
                await asyncio.sleep(0.5)

            # 5. Select Video Aspect Ratio (16:9 or 9:16) inside overlay
            ratio_btn = overlay.locator(f"mat-button-toggle:has-text('{norm_orient}')").first
            if await ratio_btn.count() > 0 and await ratio_btn.is_visible():
                logger.info(f"Selecting aspect ratio: {norm_orient}")
                await ratio_btn.click()
                effective["effective_orientation"] = norm_orient
                await asyncio.sleep(0.3)

            # 6. Select Video Model from 'Select model family' dropdown inside overlay
            model_btn = overlay.locator(FlowSelectors.SELECT_MODEL_FAMILY_BTN).first
            if await model_btn.count() > 0 and await model_btn.is_visible():
                cur_model = (await model_btn.inner_text()).strip()
                clean_cur = cur_model.split("\n")[0].strip()
                if target_model.lower() not in clean_cur.lower():
                    logger.info(f"Switching video model from '{clean_cur}' to '{target_model}'...")
                    await model_btn.click()
                    await asyncio.sleep(0.6)

                    menu_items = self.page.locator("[role='menuitem'], .mat-mdc-menu-item")
                    item_count = await menu_items.count()
                    matched = False
                    for i in range(item_count):
                        item = menu_items.nth(i)
                        txt = (await item.inner_text()).strip()
                        if target_model.lower() in txt.lower():
                            await item.click()
                            clean_chosen = txt.split("\n")[0].strip()
                            effective["effective_model"] = clean_chosen
                            matched = True
                            logger.info(f"Selected video model: {clean_chosen}")
                            await asyncio.sleep(0.5)
                            break
                    if not matched:
                        logger.warning(f"Video model '{target_model}' not found in dropdown; retaining '{clean_cur}'.")
                        await self.page.keyboard.press("Escape")
                else:
                    effective["effective_model"] = clean_cur

            # 7. Select Duration (4s, 6s, 8s, 10s) inside overlay
            chosen_model = effective.get("effective_model", target_model)
            if "veo" in chosen_model.lower():
                effective["effective_duration"] = "8"
                logger.info(f"Veo model selected ('{chosen_model}'); native 8s clip duration preserved.")
            else:
                dur_btn = overlay.locator(f"mat-button-toggle:has-text('{target_dur}s')").first
                if await dur_btn.count() > 0 and await dur_btn.is_visible():
                    logger.info(f"Selecting video duration: {target_dur}s")
                    await dur_btn.click()
                    effective["effective_duration"] = target_dur
                    await asyncio.sleep(0.3)

            # 8. Select Output Count (x1, x2, x3, x4) inside overlay
            count_btn = overlay.locator(f"mat-button-toggle:has-text('x{target_count}')").first
            if await count_btn.count() > 0 and await count_btn.is_visible():
                logger.info(f"Selecting video output count: x{target_count}")
                await count_btn.click()
                effective["effective_output_count"] = target_count
                await asyncio.sleep(0.3)

            # 9. Extract estimated credit cost notice
            cost_text = await self.page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('*'));
                const el = els.find(e => (e.innerText || '').includes('Generating will use'));
                return el ? el.innerText.trim() : null;
            }""")
            if cost_text:
                match = re.search(r"Generating will use\s+(\d+)\s+credits", cost_text, re.IGNORECASE)
                if match:
                    effective["estimated_credits"] = int(match.group(1))
                    logger.info(f"Estimated credits for configuration: {effective['estimated_credits']}")

            # 10. Close popup cleanly
            await self.page.keyboard.press("Escape")
            await asyncio.sleep(0.8)

        except Exception as e:
            logger.error(f"Error during video parameter selection: {e}")
            try:
                await self.page.keyboard.press("Escape")
            except Exception:
                pass
            raise

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

        # 1. Close any side panel and ensure Agent mode is off
        close_btn = self.page.locator(FlowSelectors.PANEL_CLOSE_BTN).first
        if await close_btn.count() > 0 and await close_btn.is_visible():
            await close_btn.click()
            await asyncio.sleep(0.5)

        agent_chip = self.page.locator(FlowSelectors.AGENT_MODE_CHIP).first
        if await agent_chip.count() > 0 and await agent_chip.is_visible():
            is_pressed = await agent_chip.get_attribute("aria-pressed")
            if is_pressed == "true":
                logger.info("Toggling off Agent mode prior to prompt submission...")
                await agent_chip.click()
                await asyncio.sleep(0.5)

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
        Monitors an individual video tile on canvas until rendering reaches 100% and media controls are ready.
        Detects active percentages (e.g. 9%, 50%) and failure states accurately.
        """
        start_time = asyncio.get_event_loop().time()
        logger.info(f"Waiting for tile completion (timeout: {timeout_seconds}s)...")

        # Initial wait for Flow canvas to initialize render
        await asyncio.sleep(5)

        last_percent = -1

        while asyncio.get_event_loop().time() - start_time < timeout_seconds:
            try:
                # If tile locator detached or not found, re-acquire newest tile from page
                if await tile.count() == 0:
                    current_tiles = await self.page.locator(FlowSelectors.VIDEO_TILE).all()
                    if current_tiles:
                        tile = current_tiles[-1]

                # Check for explicit generation error badge/text on tile
                error_el = tile.locator(":text-matches('error|failed|policy|retry', 'i')").first
                if await error_el.count() > 0 and await error_el.is_visible():
                    err_text = (await error_el.inner_text()).strip()
                    logger.error(f"Tile indicated generation error: {err_text}")
                    raise Exception(f"Flow generation failed on canvas: {err_text}")

                # Check if prompt bar still indicates active generation
                active_ind = self.page.locator(FlowSelectors.GENERATION_ACTIVE_INDICATOR).first
                is_generating_globally = await active_ind.count() > 0 and await active_ind.is_visible()

                # Read tile text for percentage
                tile_text = (await tile.inner_text()).strip() if await tile.count() > 0 else ""
                pct_match = re.search(r"(\d+)%", tile_text)

                # Check progress bar style
                pb = tile.locator(FlowSelectors.TILE_PROGRESS_BAR).first
                pb_percent = None
                if await pb.count() > 0 and await pb.is_visible():
                    style = await pb.get_attribute("style") or ""
                    m = re.search(r"--progress-percent:\s*(\d+)%", style)
                    if m:
                        pb_percent = int(m.group(1))

                current_pct = None
                if pct_match:
                    current_pct = int(pct_match.group(1))
                elif pb_percent is not None:
                    current_pct = pb_percent

                if current_pct is not None and 0 <= current_pct < 100:
                    if current_pct != last_percent:
                        last_percent = current_pct
                        if progress_callback:
                            progress_callback(current_pct, f"Generating ({current_pct}%)")
                    await asyncio.sleep(2)
                    continue

                # Check for thumbnail rendered and hotbar buttons
                thumb = tile.locator(FlowSelectors.TILE_THUMBNAIL).first
                has_thumb = False
                if await thumb.count() > 0:
                    src = await thumb.get_attribute("src") or ""
                    if src and ("asb" in src or "blob" in src or "http" in src):
                        has_thumb = True

                has_play_icon = (
                    await tile.locator("mat-icon:has-text('play_circle')").count() > 0
                    or "play_circle" in tile_text
                )
                more_btn = tile.locator("button[aria-label='More options'], flow-video-hotbar button").first
                has_more_btn = await more_btn.count() > 0

                # Completed conditions:
                # 1) Percentage reached 100%
                # 2) Thumbnail or play_circle is present, active percentage is gone, and global generation indicator is clear
                if current_pct == 100 or ((has_thumb or has_play_icon) and (has_more_btn or not is_generating_globally) and current_pct is None):
                    logger.info("Tile rendering finished: thumbnail loaded and tile controls ready!")
                    if progress_callback:
                        progress_callback(100, "Rendering complete")
                    return True

                # Check for completed video element directly inside tile
                video = tile.locator("video").first
                if await video.count() > 0 and await video.is_visible():
                    logger.info("Video element visible in tile - rendering complete!")
                    if progress_callback:
                        progress_callback(100, "Rendering complete")
                    return True

            except Exception as e_inner:
                if "failed on canvas" in str(e_inner):
                    raise
                logger.debug(f"Transient polling notice in wait_for_tile_completion: {e_inner}")

            await asyncio.sleep(2)

        logger.warning(f"Tile generation wait timed out after {timeout_seconds}s.")
        return False
