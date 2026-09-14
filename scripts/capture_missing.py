import os
import shutil
import time
from playwright.sync_api import sync_playwright

def capture_missing():
    output_dir = os.path.abspath("screenshots")
    typo_dir = os.path.abspath("scheenshots")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(typo_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()

        # 4. Copilot Drawer
        print("Capturing 04_copilot_assistant.png...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        page.evaluate("() => localStorage.setItem('nexusfleet_tutorial_closed', 'true')")
        page.reload(wait_until="networkidle")
        time.sleep(2)
        try:
            copilot_btn = page.locator("button:has-text('NexusFleet AI')").first
            copilot_btn.click()
            time.sleep(1)
            chat_input = page.locator("input[type='text']").last
            if chat_input.is_visible():
                chat_input.fill("Status da frota e métricas")
                chat_input.press("Enter")
                time.sleep(2.5)
            page.screenshot(path=os.path.join(output_dir, "04_copilot_assistant.png"))
            print("04_copilot_assistant.png captured!")
        except Exception as e:
            print(f"Error capturing copilot: {e}")

        # 5. Layout Studio Tab
        print("Capturing 05_layout_studio.png...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(1.5)
        try:
            studio_btn = page.locator("button:has-text('Studio')").first
            studio_btn.click()
            time.sleep(2)
            page.screenshot(path=os.path.join(output_dir, "05_layout_studio.png"))
            print("05_layout_studio.png captured!")
        except Exception as e:
            print(f"Error capturing layout studio: {e}")

        # 6. Analytics Dashboard Tab
        print("Capturing 06_analytics_bi.png...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(1.5)
        try:
            analytics_btn = page.locator("button:has-text('Analytics')").first
            analytics_btn.click()
            time.sleep(2.5)
            page.screenshot(path=os.path.join(output_dir, "06_analytics_bi.png"))
            print("06_analytics_bi.png captured!")
        except Exception as e:
            print(f"Error capturing analytics: {e}")

        browser.close()

    print("Copying all assets to scheenshots directory...")
    for filename in os.listdir(output_dir):
        src = os.path.join(output_dir, filename)
        dst = os.path.join(typo_dir, filename)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copied {filename} to {typo_dir}")

    print("Done!")

if __name__ == "__main__":
    capture_missing()
