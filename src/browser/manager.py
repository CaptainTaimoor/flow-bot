import os
from playwright.async_api import async_playwright, BrowserContext, Playwright
from src.config.settings import settings
import logging

logger = logging.getLogger(__name__)

class BrowserManager:
    def __init__(self):
        self.playwright: Playwright | None = None
        self.context: BrowserContext | None = None

    async def start(self):
        logger.info("Starting browser manager...")
        self.playwright = await async_playwright().start()
        
        # Ensure profile dir exists
        os.makedirs(settings.BROWSER_PROFILE_DIR, exist_ok=True)
        
        logger.info(f"Using persistent profile at {settings.BROWSER_PROFILE_DIR}")
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=settings.BROWSER_PROFILE_DIR,
            headless=settings.HEADLESS,
            args=["--disable-blink-features=AutomationControlled"], # Basic stealth
            no_viewport=True # Allow window to be resized by OS
        )
        
    async def get_page(self):
        if not self.context:
            await self.start()
        
        pages = self.context.pages
        if pages:
            return pages[0]
        return await self.context.new_page()
        
    async def stop(self):
        logger.info("Stopping browser manager...")
        if self.context:
            await self.context.close()
        if self.playwright:
            await self.playwright.stop()
