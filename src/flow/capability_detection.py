import re
import logging
import asyncio
from playwright.async_api import Page
from src.models.domain import FlowCapabilities
from src.flow.selectors import FlowSelectors
from src.flow.auth import AuthManager, AuthState

logger = logging.getLogger(__name__)

class FlowCapabilityDetector:
    @staticmethod
    async def detect_capabilities(page: Page) -> FlowCapabilities:
        caps = FlowCapabilities()
        try:
            # Check auth
            auth_state = await AuthManager.check_auth_status(page)
            caps.authenticated = (auth_state == AuthState.AUTHENTICATED)
            caps.flow_available = True

            # Check prompt input
            prompt_input = page.locator(FlowSelectors.PROMPT_INPUT).first
            caps.standard_generation = (await prompt_input.count() > 0)

            # Check agent panel
            agent_panel = page.locator("flow-agent-panel, flow-chat-view, [role='region']:has-text('session')").first
            caps.agent_available = (await agent_panel.count() > 0)

            # Inspect credit info if visible
            try:
                credit_text = await page.locator(":text-matches('(\\d+[\\d,]*)\\s+Google Flow credits')").first.inner_text()
                match = re.search(r"([\d,]+)\s+Google Flow credits", credit_text)
                if match:
                    caps.credit_balance = int(match.group(1).replace(",", ""))
                    caps.credit_info_text = credit_text.strip()
            except Exception:
                pass

            # Inspect project title
            try:
                title_el = page.locator(".project-title, header h1, [aria-label*='project title' i]").first
                if await title_el.count() > 0:
                    caps.current_project = (await title_el.inner_text()).strip()
            except Exception:
                pass

        except Exception as e:
            logger.warning(f"Error inspecting Flow capabilities: {e}")

        return caps
