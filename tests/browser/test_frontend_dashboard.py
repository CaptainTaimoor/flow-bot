import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_frontend_navigation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        print("\nNavigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded")

        title = await page.title()
        print(f"Page title: {title}")
        assert "Flow" in title or "Google" in title

        # Verify Header Branding
        brand_locator = page.locator("text=FLOW STUDIO")
        await brand_locator.wait_for(state="visible", timeout=5000)
        print("Header branding verified.")

        # Click navigation items and verify heading appearance
        tabs = [
            ("Create Video", "Create Video"),
            ("Active Jobs", "Active Generations"),
            ("Queue", "Generation Queue"),
            ("Video Library", "Video Library"),
            ("History", "Generation History"),
            ("Diagnostics", "System Diagnostics"),
            ("Settings", "System & Engine Settings"),
            ("Overview", "AI Video Generation Command Center"),
        ]

        for tab_label, expected_heading in tabs:
            btn = page.locator(f"aside button:has-text('{tab_label}')")
            await btn.click()
            heading_locator = page.locator(f"text={expected_heading}").first
            await heading_locator.wait_for(state="visible", timeout=6000)
            print(f"Tab '{tab_label}' rendered '{expected_heading}' successfully.")

        # Take screenshot of Overview
        await page.screenshot(path="runtime/dashboard_qa.png")
        print("Screenshot saved to runtime/dashboard_qa.png")

        await browser.close()

        # Verify no fatal JS crashes
        fatal_errors = [e for e in console_errors if "uncaught" in e.lower()]
        assert len(fatal_errors) == 0, f"Fatal JS errors found: {fatal_errors}"
