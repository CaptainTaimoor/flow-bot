import pytest
from src.browser.manager import BrowserManager

@pytest.mark.asyncio
async def test_browser_startup_safe():
    manager = BrowserManager()
    await manager.start()
    
    page = await manager.get_page()
    assert page is not None
    
    # Just navigate to Google to ensure Playwright is working
    await page.goto("https://www.google.com")
    title = await page.title()
    assert "Google" in title
    
    await manager.stop()
