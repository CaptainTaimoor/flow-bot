import asyncio
import json
import re
from playwright.async_api import async_playwright
from src.config.settings import settings
from src.flow.selectors import FlowSelectors

async def inspect():
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

        models_to_test = ["Omni 1.1 Flash", "Veo 3.1 - Lite", "Veo 3.1 - Fast", "Veo 3.1 - Quality"]
        durations = ["4", "6", "8", "10"]
        
        matrix = {}

        for m_name in models_to_test:
            matrix[m_name] = {}
            print(f"\n--- Checking Model: {m_name} ---", flush=True)

            # Re-locate model button inside overlay
            model_btn = page.locator(FlowSelectors.SELECT_MODEL_FAMILY_BTN).first
            await model_btn.click()
            await asyncio.sleep(0.8)

            menu_items = page.locator("[role='menuitem'], .mat-mdc-menu-item")
            item_count = await menu_items.count()
            found = False
            for i in range(item_count):
                it = menu_items.nth(i)
                txt = (await it.inner_text()).strip()
                if m_name.lower() in txt.lower():
                    await it.click()
                    found = True
                    print(f"Clicked model option: {repr(txt)}", flush=True)
                    await asyncio.sleep(0.8)
                    break
            
            if not found:
                print(f"Could NOT find menu item for {m_name}!", flush=True)
                await page.keyboard.press("Escape")
                continue

            for d in durations:
                dur_btn = page.locator(f".cdk-overlay-pane:has(mat-button-toggle) mat-button-toggle:has-text('{d}s')").first
                if await dur_btn.count() > 0 and await dur_btn.is_visible():
                    classes = await dur_btn.get_attribute("class") or ""
                    is_disabled = "mat-button-toggle-disabled" in classes or await dur_btn.get_attribute("disabled") is not None
                    if is_disabled:
                        matrix[m_name][f"{d}s"] = "DISABLED"
                        print(f"  Duration {d}s: DISABLED", flush=True)
                        continue

                    await dur_btn.click()
                    await asyncio.sleep(0.5)

                    cost_text = await page.evaluate("""() => {
                        const els = Array.from(document.querySelectorAll('*'));
                        const el = els.find(e => (e.innerText || '').includes('Generating will use'));
                        return el ? el.innerText.trim() : null;
                    }""")
                    if cost_text:
                        match = re.search(r"Generating will use\s+(\d+)\s+credits", cost_text, re.IGNORECASE)
                        if match:
                            credits = int(match.group(1))
                            matrix[m_name][f"{d}s"] = credits
                            print(f"  Duration {d}s: {credits} credits", flush=True)
                        else:
                            matrix[m_name][f"{d}s"] = cost_text
                            print(f"  Duration {d}s: {cost_text}", flush=True)
                    else:
                        matrix[m_name][f"{d}s"] = "NOT_FOUND"
                        print(f"  Duration {d}s: NOT_FOUND", flush=True)

        await page.keyboard.press("Escape")
        await context.close()
        print("\n=== FINAL ACCURATE CREDIT MATRIX ===", flush=True)
        print(json.dumps(matrix, indent=2), flush=True)

if __name__ == "__main__":
    asyncio.run(inspect())
