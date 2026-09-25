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
        # If already in workspace with prompt input visible or /project/ URL
        if "/project/" in self.page.url:
            prompt_input = self.page.locator(FlowSelectors.PROMPT_INPUT).first
            if await prompt_input.count() > 0 and await prompt_input.is_visible():
                logger.info("Already inside project workspace.")
                return True

        # Dismiss hero banner or modal on gallery if present
        close_btn = self.page.locator(FlowSelectors.HERO_CLOSE_BTN).first
        if await close_btn.count() > 0 and await close_btn.is_visible():
            logger.info("Dismissing gallery announcement banner...")
            try:
                await close_btn.click()
                await asyncio.sleep(1)
            except Exception:
                pass

        # Check if on project landing/gallery
        new_proj_btn = self.page.locator(FlowSelectors.NEW_PROJECT_BTN).first
        has_new_btn = (await new_proj_btn.count() > 0 and await new_proj_btn.is_visible())

        if settings.FLOW_PROJECT_MODE == "CREATE_PROJECT_PER_JOB" and has_new_btn:
            logger.info("Clicking 'New project'...")
            await new_proj_btn.click()
        else:
            # Try to click most recent project card (a[href*='/project/'] or flow-project-card)
            recent_card = self.page.locator("a[href*='/project/'], flow-project-card").first
            if await recent_card.count() > 0 and await recent_card.is_visible():
                logger.info("Opening most recent project card...")
                await recent_card.click()
            elif has_new_btn:
                logger.info("No recent project card found, clicking 'New project'...")
                await new_proj_btn.click()
            else:
                # Fallback to 'Start Creating' button if banner is still active
                start_btn = self.page.locator(FlowSelectors.HERO_START_CREATING).first
                if await start_btn.count() > 0 and await start_btn.is_visible():
                    logger.info("Clicking 'Start Creating' on hero banner...")
                    await start_btn.click()

        # Wait for workspace to load (URL containing /project/ or prompt input visible)
        try:
            prompt_input = self.page.locator(FlowSelectors.PROMPT_INPUT).first
            await prompt_input.wait_for(state="visible", timeout=20000)
            logger.info("Successfully entered project workspace.")
            return True
        except Exception as e:
            logger.warning(f"Waiting for prompt input after project open timed out: {e}")
            return "/project/" in self.page.url

    async def get_current_project_id(self) -> Optional[str]:
        """Extracts the project ID from the active URL if present."""
        url = self.page.url
        if "/project/" in url:
            parts = url.split("/project/")
            if len(parts) > 1:
                return parts[1].split("?")[0].split("/")[0]
        return None
