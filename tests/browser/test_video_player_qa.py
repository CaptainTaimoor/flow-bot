import asyncio
import os
from playwright.async_api import async_playwright

async def verify_dashboard_library():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Navigating to http://127.0.0.1:8000...")
        await page.goto("http://127.0.0.1:8000", wait_until="domcontentloaded")
        await asyncio.sleep(2)

        # Go to Video Library
        print("Clicking Video Library...")
        await page.locator("aside button:has-text('Video Library')").click()
        await asyncio.sleep(2)

        # Screenshot Video Library
        os.makedirs("runtime", exist_ok=True)
        await page.screenshot(path="runtime/library_qa.png")
        print("Screenshot saved to runtime/library_qa.png")

        # Click on the video card to open VideoDetailModal
        print("Clicking video card to open player modal...")
        card = page.locator("text=flow_generation_job_1.mp4").first
        await card.click()
        await asyncio.sleep(3)

        # Screenshot the video player modal
        await page.screenshot(path="runtime/player_modal_qa.png")
        print("Screenshot saved to runtime/player_modal_qa.png")

        # Verify video player is rendered
        player_video = page.locator("video").first
        has_video = await player_video.count() > 0
        print(f"Video tag present in player modal: {has_video}")
        assert has_video, "Video player tag not rendered"

        await browser.close()
        print("Visual QA complete!")

if __name__ == "__main__":
    asyncio.run(verify_dashboard_library())
