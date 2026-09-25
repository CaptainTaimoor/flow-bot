import asyncio
import json
import re
from playwright.async_api import async_playwright
from src.config.settings import settings
from src.flow.selectors import FlowSelectors

async def inspect_all_veo():
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

        veo_models = ["Veo 3.1 - Lite", "Veo 3.1 - Fast", "Veo 3.1 - Quality"]
        counts = [1, 2, 3, 4]
        results = {}

        for m_name in veo_models:
            results[m_name] = {}
            # Open model dropdown
            model_btn = page.locator(FlowSelectors.SELECT_MODEL_FAMILY_BTN).first
            await model_btn.click()
            await asyncio.sleep(0.8)

            menu_item = page.locator(f"[role='menuitem']:has-text('{m_name}'), .mat-mdc-menu-item:has-text('{m_name}')").first
            await menu_item.click()
            await asyncio.sleep(0.8)

            for c in counts:
                count_btn = page.locator(f".cdk-overlay-pane:has(mat-button-toggle) mat-button-toggle:has-text('x{c}')").first
                if await count_btn.count() > 0 and await count_btn.is_visible():
                    await count_btn.click()
                    await asyncio.sleep(0.4)

                    cost_text = await page.evaluate("""() => {
                        const els = Array.from(document.querySelectorAll('*'));
                        const el = els.find(e => (e.innerText || '').includes('Generating will use'));
                        return el ? el.innerText.trim() : null;
                    }""")
                    if cost_text:
                        match = re.search(r"Generating will use\s+(\d+)\s+credits", cost_text, re.IGNORECASE)
                        if match:
                            results[m_name][f"x{c}"] = int(match.group(1))
                        else:
                            results[m_name][f"x{c}"] = cost_text
                    else:
                        results[m_name][f"x{c}"] = "NOT_FOUND"

        await page.keyboard.press("Escape")
        await context.close()

        print("\n=== VEO MODELS ACCURATE CREDIT COSTS ===", flush=True)
        print(json.dumps(results, indent=2), flush=True)

if __name__ == "__main__":
    asyncio.run(inspect_all_veo())
