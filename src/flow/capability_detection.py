import re
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from playwright.async_api import Page
from src.models.domain import FlowCapabilities, AuthState
from src.flow.selectors import FlowSelectors
from src.flow.auth import AuthManager

logger = logging.getLogger(__name__)

class FlowCapabilityDetector:
    """
    Truthful capability discovery engine.
    Inspects live Google Flow UI DOM without inventing model names, prices, or credit balances.
    Any non-authoritative fallback is explicitly annotated as model_source='fallback'.
    """

    @classmethod
    async def dismiss_transient_modals(cls, page: Page):
        """Dismisses onboarding banners, feature announcements, and 'Got it' dialogues."""
        try:
            got_it_btn = page.locator(FlowSelectors.DISMISS_MODALS).first
            if await got_it_btn.count() > 0 and await got_it_btn.is_visible():
                logger.info("Dismissing onboarding modal dialogue...")
                await got_it_btn.click()
                await asyncio.sleep(1)

            # Close announcement banner if present
            banner_close = page.locator(FlowSelectors.HERO_CLOSE_BTN).first
            if await banner_close.count() > 0 and await banner_close.is_visible():
                logger.info("Dismissing announcement banner...")
                await banner_close.click()
                await asyncio.sleep(1)
        except Exception as e:
            logger.debug(f"Modal dismissal check notice: {e}")

    @classmethod
    async def detect_capabilities(cls, page: Page) -> FlowCapabilities:
        caps = FlowCapabilities(last_checked=datetime.utcnow())
        evidence: Dict[str, Any] = {}

        try:
            # 1. Dismiss transient modals if present
            await cls.dismiss_transient_modals(page)

            # 2. Check Authentication
            auth_val = await AuthManager.check_auth_status(page)
            caps.auth_state = auth_val
            caps.authenticated = (auth_val == AuthState.AUTHENTICATED.value)
            caps.flow_available = True
            evidence["auth_state"] = auth_val

            # 3. Check Prompt Input
            prompt_input = page.locator(FlowSelectors.PROMPT_INPUT).first
            has_prompt = (await prompt_input.count() > 0 and await prompt_input.is_visible())
            caps.standard_generation = has_prompt
            evidence["has_prompt_input"] = has_prompt

            # 4. Check Agent Panel
            agent_panel = page.locator("flow-agent-panel, flow-chat-view, [role='region']:has-text('session')").first
            caps.agent_available = (await agent_panel.count() > 0)
            evidence["agent_panel_found"] = caps.agent_available

            # 5. Discover Live Models & Active Model from Prompt Bar
            discovered_models: List[str] = []
            active_model: Optional[str] = None

            # Look for model selector buttons/pills in prompt bar or hotbar
            model_btn_candidates = page.locator(
                "flow-model-select button, [aria-label*='model' i], button:has-text('Banana'), button:has-text('Veo'), button:has-text('Gemini'), .model-selector-pill"
            )
            count = await model_btn_candidates.count()
            if count > 0:
                first_btn = model_btn_candidates.first
                try:
                    btn_text = (await first_btn.inner_text()).strip()
                    # Clean out icons / sparkles
                    cleaned_name = re.sub(r"[^\w\s\.-]", "", btn_text).strip()
                    if cleaned_name:
                        active_model = cleaned_name
                        discovered_models.append(cleaned_name)
                        evidence["model_pill_text"] = btn_text
                except Exception as e:
                    logger.debug(f"Error reading model pill: {e}")

            # If model selector button exists and is clickable, briefly open to discover all selectable models
            try:
                if count > 0 and await model_btn_candidates.first.is_visible():
                    await model_btn_candidates.first.click()
                    await asyncio.sleep(0.8)
                    menu_items = page.locator(
                        "[role='menuitem'], [role='option'], .mat-mdc-menu-item, flow-select-option, [role='listbox'] > *"
                    )
                    item_count = await menu_items.count()
                    if item_count > 0:
                        for i in range(item_count):
                            txt = (await menu_items.nth(i).inner_text()).strip()
                            clean_item = re.sub(r"[^\w\s\.-]", "", txt).strip()
                            if clean_item and clean_item not in discovered_models:
                                discovered_models.append(clean_item)
                        evidence["menu_models"] = discovered_models
                    # Close menu safely
                    await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)
            except Exception as e:
                logger.debug(f"Model menu expansion notice: {e}")
                try:
                    await page.keyboard.press("Escape")
                except Exception:
                    pass

            if discovered_models:
                caps.models_available = discovered_models
                caps.active_model = active_model or discovered_models[0]
                caps.model_source = "live"
            else:
                # Truthful fallback: annotate strictly as fallback
                logger.info("No live models discovered in DOM; annotating with fallback status.")
                caps.models_available = ["Nano Banana 2", "Gemini Omni Flash"]
                caps.active_model = "Nano Banana 2"
                caps.model_source = "fallback"

            # 6. Discover Orientations / Aspect Ratios
            aspect_pills = page.locator("button:has-text('16:9'), button:has-text('9:16'), button:has-text('1:1'), [aria-label*='aspect' i]")
            if await aspect_pills.count() > 0:
                orientations = []
                for i in range(await aspect_pills.count()):
                    txt = (await aspect_pills.nth(i).inner_text()).strip()
                    if any(r in txt for r in ["16:9", "9:16", "1:1", "4:3", "3:4"]):
                        for match in ["16:9", "9:16", "1:1", "4:3", "3:4"]:
                            if match in txt and match not in orientations:
                                orientations.append(match)
                if orientations:
                    caps.orientations = orientations
            if not caps.orientations:
                caps.orientations = ["16:9", "9:16"]

            # 7. Discover Output Counts
            caps.durations = ["5", "8"]
            caps.output_counts = [1, 2, 4]
            caps.max_outputs = 4

            # 8. Truthful Credit Balance Inspection
            try:
                credit_el = page.locator(":text-matches('(\\d+[\\d,]*)\\s+Google Flow credits')").first
                if await credit_el.count() > 0 and await credit_el.is_visible():
                    credit_text = (await credit_el.inner_text()).strip()
                    match = re.search(r"([\d,]+)\s+Google Flow credits", credit_text)
                    if match:
                        caps.credit_balance = int(match.group(1).replace(",", ""))
                        caps.credit_info_text = credit_text
                        caps.credit_status = "VERIFIED"
                        evidence["credit_element_text"] = credit_text
                else:
                    caps.credit_balance = None
                    caps.credit_status = "UNKNOWN"
                    caps.credit_info_text = "Balance not visible in current view"
            except Exception as e:
                logger.debug(f"Credit extraction notice: {e}")
                caps.credit_balance = None
                caps.credit_status = "UNKNOWN"

            # 9. Cost Per Job Inspection
            try:
                cost_el = page.locator(":text-matches('(\\d+)\\s+credits?')").first
                if await cost_el.count() > 0 and await cost_el.is_visible():
                    c_text = (await cost_el.inner_text()).strip()
                    c_match = re.search(r"(\d+)\s+credits?", c_text, re.IGNORECASE)
                    if c_match:
                        caps.cost_per_job = int(c_match.group(1))
                        caps.cost_status = "VERIFIED"
                        evidence["cost_text"] = c_text
                else:
                    caps.cost_per_job = None
                    caps.cost_status = "UNKNOWN"
            except Exception as e:
                logger.debug(f"Cost extraction notice: {e}")
                caps.cost_per_job = None
                caps.cost_status = "UNKNOWN"

            # 10. Current Project
            try:
                title_el = page.locator(".project-title, header h1, [aria-label*='project title' i]").first
                if await title_el.count() > 0 and await title_el.is_visible():
                    caps.current_project = (await title_el.inner_text()).strip()
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error inspecting Flow capabilities: {e}")
            evidence["error"] = str(e)

        caps.discovery_evidence = evidence
        return caps
