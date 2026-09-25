import asyncio
from playwright.async_api import async_playwright
from src.config.settings import settings
from src.flow.selectors import FlowSelectors

async def inspect_veo():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=settings.BROWSER_PROFILE_DIR,
            headless=False,
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://flow.google.com/", wait_until="networkidle", timeout=45000)
        await asyncio.sleep(2)

        recent_card = page.locator("a[href*='/project/'], div[data-project-id], [class*='project-card']").first
        if await recent_card.count() > 0 and await recent_card.is_visible():
            await recent_card.click()
            await asyncio.sleep(3)

        trigger = page.locator(FlowSelectors.SETTINGS_TRIGGER_BTN).first
        await trigger.wait_for(state="visible", timeout=10000)
        await trigger.click()
        await asyncio.sleep(1)

        overlay = page.locator(".cdk-overlay-pane:has(mat-button-toggle)").first
        await overlay.wait_for(state="visible", timeout=5000)

        # Video tab
        video_tab = overlay.locator("mat-button-toggle:has-text('Video')").first
        if await video_tab.count() > 0:
            await video_tab.click()
            await asyncio.sleep(0.5)

        # Click model button
        model_btn = page.locator(FlowSelectors.SELECT_MODEL_FAMILY_BTN).first
        await model_btn.click()
        await asyncio.sleep(0.8)

        # Click Veo 3.1 - Lite
        veo_item = page.locator("[role='menuitem']:has-text('Veo 3.1 - Lite'), .mat-mdc-menu-item:has-text('Veo 3.1 - Lite')").first
        await veo_item.click()
        await asyncio.sleep(1)

        # Now print all text inside the overlay or on the page!
        info = await page.evaluate("""() => {
            const overlays = Array.from(document.querySelectorAll('.cdk-overlay-pane'));
            return overlays.map(o => o.innerText);
        }""")
        print("=== OVERLAY CONTENT FOR VEO 3.1 - LITE ===")
        for idx, text in enumerate(info):
            print(f"--- Overlay {idx} ---")
            print(text)

        await page.screenshot(path="data/veo_settings_inspect.png")
        print("Saved screenshot to data/veo_settings_inspect.png")

        await page.keyboard.press("Escape")
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_veo())
