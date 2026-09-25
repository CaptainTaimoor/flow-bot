import os
import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, BrowserContext, Playwright, Page
from src.config.settings import settings
from src.config.runtime_config import runtime_config

logger = logging.getLogger(__name__)

class BrowserService:
    """
    Singleton application-level browser service.
    Coordinates browser lifecycle and provides cooperative page leasing
    across API endpoints, background job runners, and diagnostic tasks
    to eliminate persistent Chromium profile lock contention.
    """
    _instance: Optional["BrowserService"] = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BrowserService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()
        self._initialized = True

    async def start(self) -> BrowserContext:
        """Starts Playwright with persistent context if not already active."""
        async with self._lock:
            if self.context:
                return self.context

            logger.info("Initializing shared application BrowserService...")
            if not self.playwright:
                self.playwright = await async_playwright().start()

            settings.ensure_directories()
            profile_dir = settings.BROWSER_PROFILE_DIR
            headless = runtime_config.get("HEADLESS", settings.HEADLESS)
            logger.info(f"Launching persistent Chromium context at {profile_dir} (headless={headless})")

            self.context = await self._launch_context(profile_dir, headless)
            return self.context

    async def _launch_context(self, profile_dir: str, headless: bool) -> BrowserContext:
        ctx = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            no_viewport=True,
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        await ctx.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """)
        return ctx

    async def get_page(self) -> Page:
        """Returns the primary page or creates one within the shared context."""
        if not self.context:
            await self.start()

        pages = self.context.pages
        if pages:
            return pages[0]
        return await self.context.new_page()

    @asynccontextmanager
    async def lease_page(self) -> AsyncGenerator[Page, None]:
        """
        Leases the active page with an exclusive lock so that background jobs
        and on-demand inspection never collide.
        """
        async with self._lock:
            if not self.context:
                logger.info("Starting browser for leased page access...")
                if not self.playwright:
                    self.playwright = await async_playwright().start()
                settings.ensure_directories()
                profile_dir = settings.BROWSER_PROFILE_DIR
                headless = runtime_config.get("HEADLESS", settings.HEADLESS)
                self.context = await self._launch_context(profile_dir, headless)
            pages = self.context.pages
            page = pages[0] if pages else await self.context.new_page()
            try:
                yield page
            finally:
                pass

    async def restart(self):
        """Safely restarts the browser context."""
        async with self._lock:
            logger.info("Restarting shared browser context...")
            await self._stop_internal()
            if not self.playwright:
                self.playwright = await async_playwright().start()
            settings.ensure_directories()
            profile_dir = settings.BROWSER_PROFILE_DIR
            headless = runtime_config.get("HEADLESS", settings.HEADLESS)
            self.context = await self._launch_context(profile_dir, headless)

    def get_status(self) -> Dict[str, Any]:
        """Returns current browser health and connection status."""
        is_running = self.context is not None
        page_count = len(self.context.pages) if self.context else 0
        headless = runtime_config.get("HEADLESS", settings.HEADLESS)
        return {
            "running": is_running,
            "headless": headless,
            "page_count": page_count,
            "profile_dir": settings.BROWSER_PROFILE_DIR,
        }

    async def stop(self):
        """Stops the browser and playwright instance gracefully."""
        async with self._lock:
            await self._stop_internal()

    async def _stop_internal(self):
        logger.info("Stopping shared browser service...")
        if self.context:
            try:
                await self.context.close()
            except Exception as e:
                logger.debug(f"Context close notice: {e}")
            self.context = None

        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception as e:
                logger.debug(f"Playwright stop notice: {e}")
            self.playwright = None

browser_service = BrowserService()
