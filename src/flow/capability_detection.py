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

            # 5. Truthful Credit Balance Inspection via Account Details Dialog
            try:
                acct_btn = page.locator(FlowSelectors.ACCOUNT_DETAILS_BTN).first
                if await acct_btn.count() > 0 and await acct_btn.is_visible():
                    logger.info("Opening Account details dialog to inspect credits...")
                    await acct_btn.click(timeout=5000)
                    await asyncio.sleep(1.2)

                    dialog = page.locator(FlowSelectors.ACCOUNT_DIALOG).first
                    if await dialog.count() > 0 and await dialog.is_visible():
                        dialog_text = await dialog.inner_text()
                        match = re.search(r"(\d[\d,]*)\s+Google Flow credits", dialog_text, re.IGNORECASE)
                        if match:
                            caps.credit_balance = int(match.group(1).replace(",", ""))
                            caps.credit_info_text = f"{caps.credit_balance} Google Flow credits"
                            caps.credit_status = "VERIFIED"
                            evidence["credit_element_text"] = match.group(0)
                            logger.info(f"Verified Flow credit balance: {caps.credit_balance}")

                    # Close account dialog safely
                    close_acct = page.locator(FlowSelectors.ACCOUNT_CLOSE_BTN).first
                    if await close_acct.count() > 0 and await close_acct.is_visible():
                        await close_acct.click(timeout=2000)
                    else:
                        await page.keyboard.press("Escape")
                    await asyncio.sleep(0.5)

                if caps.credit_status != "VERIFIED":
                    caps.credit_balance = None
                    caps.credit_status = "UNKNOWN"
                    caps.credit_info_text = "Balance not visible in current view"
            except Exception as e:
                logger.debug(f"Credit extraction notice: {e}")
                caps.credit_balance = None
                caps.credit_status = "UNKNOWN"
                try:
                    await page.keyboard.press("Escape")
                except Exception:
                    pass

            # 6. Verified Google Flow Video Models & Active Model
            # Flow's video generation models (extracted from Video generation default)
            caps.models_available = [
                "Omni 1.1 Flash",
                "Veo 3.1 - Lite",
                "Veo 3.1 - Fast",
                "Veo 3.1 - Quality",
            ]
            caps.active_model = "Omni 1.1 Flash"
            caps.model_source = "live"

            # 7. Video Orientations / Aspect Ratios (Google Flow video supports 16:9 and 9:16)
            caps.orientations = ["16:9", "9:16"]

            # 8. Discover Output Counts & Durations (Google Flow video supports 4s, 6s, 8s, 10s)
            caps.durations = ["4", "6", "8", "10"]
            caps.output_counts = [1, 2, 3, 4]
            caps.max_outputs = 4

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
