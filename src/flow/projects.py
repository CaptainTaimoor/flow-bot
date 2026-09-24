import logging
import asyncio
from typing import Optional, List, Dict
from playwright.async_api import Page
from src.flow.selectors import FlowSelectors
from src.config.settings import settings

logger = logging.getLogger(__name__)

class FlowProjectManager:
    def __init__(self, page: Page):
        self.page = page

    async def ensure_project_open(self, project_id_or_name: Optional[str] = None) -> bool:
        """
        Navigates into an open project workspace.
        If a specific project is requested, tries to open it;
        otherwise opens the latest or creates a new project according to FLOW_PROJECT_MODE.
        """
        # If already in workspace with prompt input visible, we are ready
        prompt_input = self.page.locator(FlowSelectors.PROMPT_INPUT).first
        if await prompt_input.count() > 0 and await prompt_input.is_visible():
            logger.info("Already inside project workspace.")
            return True

        # Check if on project landing/gallery
        new_proj_btn = self.page.locator(FlowSelectors.NEW_PROJECT_BTN).first
        if await new_proj_btn.count() > 0 and await new_proj_btn.is_visible():
            if settings.FLOW_PROJECT_MODE == "CREATE_PROJECT_PER_JOB":
                logger.info("Clicking 'New project'...")
                await new_proj_btn.click()
                await asyncio.sleep(5)
                return True
            else:
                # Try to click most recent project card
                recent_card = self.page.locator(FlowSelectors.PROJECT_CARDS).first
                if await recent_card.count() > 0 and await recent_card.is_visible():
                    logger.info("Opening most recent project card...")
                    await recent_card.click()
                    await asyncio.sleep(5)
                    return True
                else:
                    logger.info("No recent project found, creating new project...")
                    await new_proj_btn.click()
                    await asyncio.sleep(5)
                    return True

        return False

    async def get_current_project_id(self) -> Optional[str]:
        """Extracts the project ID from the active URL if present."""
        url = self.page.url
        if "/project/" in url:
            parts = url.split("/project/")
            if len(parts) > 1:
                return parts[1].split("?")[0].split("/")[0]
        return None
