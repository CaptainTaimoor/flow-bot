import asyncio
from playwright.async_api import async_playwright
from src.config.settings import settings
from src.flow.selectors import FlowSelectors

async def check_menu():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=settings.BROWSER_PROFILE_DIR,
            headless=False,
            no_viewport=True,
        )
        page = context.pages[0] if context.pages else await context.new_page()
        await page.goto("https://flow.google.com/", wait_until="networkidle", timeout=45000)
        await asyncio.sleep(2)

        # Enter project
        recent_card = page.locator("a[href*='/project/'], div[data-project-id], [class*='project-card']").first
        if await recent_card.count() > 0 and await recent_card.is_visible():
            await recent_card.click()
            await asyncio.sleep(3)

        # Open settings trigger
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

        # Model button
        model_btn = overlay.locator(FlowSelectors.SELECT_MODEL_FAMILY_BTN).first
        await model_btn.click()
        await asyncio.sleep(1)

        menu_items = page.locator("[role='menuitem'], .mat-mdc-menu-item")
        count = await menu_items.count()
        print(f"Total model menu items: {count}")
        for i in range(count):
            txt = (await menu_items.nth(i).inner_text()).strip()
            print(f"Item #{i}: {repr(txt)}")

        await page.keyboard.press("Escape")
        await context.close()

if __name__ == "__main__":
    asyncio.run(check_menu())
