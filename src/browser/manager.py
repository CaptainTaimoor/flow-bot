import logging
from typing import Optional, Dict, Any
from playwright.async_api import BrowserContext, Playwright, Page
from src.browser.service import browser_service

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Facade maintaining backward compatibility while delegating to
    the singleton BrowserService to prevent Chromium profile directory lock contention.
    """
    def __init__(self):
        self._service = browser_service

    @property
    def playwright(self) -> Optional[Playwright]:
        return self._service.playwright

    @property
    def context(self) -> Optional[BrowserContext]:
        return self._service.context

    async def start(self) -> BrowserContext:
        return await self._service.start()

    async def get_page(self) -> Page:
        return await self._service.get_page()

    async def restart(self):
        await self._service.restart()

    def get_status(self) -> Dict[str, Any]:
        return self._service.get_status()

    async def stop(self):
        await self._service.stop()
