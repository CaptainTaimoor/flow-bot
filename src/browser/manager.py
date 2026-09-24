import os
import logging
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, BrowserContext, Playwright, Page
from src.config.settings import settings

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None

    async def start(self):
        """Starts Playwright with the user's persistent profile."""
        if self.context:
            return

        logger.info("Starting browser manager...")
        self.playwright = await async_playwright().start()

        settings.ensure_directories()
        profile_dir = settings.BROWSER_PROFILE_DIR
        logger.info(f"Using persistent profile at {profile_dir} (headless={settings.HEADLESS})")

        # Standard browser automation without evasion flags per Part 51
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=settings.HEADLESS,
            no_viewport=True,
        )

    async def get_page(self) -> Page:
        """Returns the active page or creates a new one."""
        if not self.context:
            await self.start()

        pages = self.context.pages
        if pages:
            return pages[0]
        return await self.context.new_page()

    async def restart(self):
        """Safely restarts the browser context."""
        logger.info("Restarting browser context...")
        await self.stop()
        await self.start()

    def get_status(self) -> Dict[str, Any]:
        """Returns current browser health and connection status."""
        is_running = self.context is not None
        page_count = len(self.context.pages) if self.context else 0
        return {
            "running": is_running,
            "headless": settings.HEADLESS,
            "page_count": page_count,
            "profile_dir": settings.BROWSER_PROFILE_DIR,
        }

    async def stop(self):
        """Stops the browser and playwright instance."""
        logger.info("Stopping browser manager...")
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.debug(f"Context close note: {e}")
            self.context = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.debug(f"Playwright stop note: {e}")
            self.playwright = None
