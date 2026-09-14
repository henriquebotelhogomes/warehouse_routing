import io
import os
import shutil
import time

from PIL import Image
from playwright.sync_api import sync_playwright


def capture_all():
    output_dir = os.path.abspath("screenshots")
    os.makedirs(output_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,  # Crisp high-res capture
        )
        page = context.new_page()

        print("1. Navigating to Digital Twin Simulator...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        page.evaluate("() => localStorage.setItem('nexusfleet_tutorial_closed', 'true')")
        page.reload(wait_until="networkidle")
        time.sleep(3)  # Wait for WebSocket telemetry & AMRs to move

        # 1. Digital Twin Simulator Main Screen
        print("Capturing 01_digital_twin_simulator.png...")
        page.screenshot(path=os.path.join(output_dir, "01_digital_twin_simulator.png"))

        # 2. AMR Detail Modal
        print("Opening AMR Detail Modal...")
        try:
            amr_card = page.locator("div:has-text('AMR-01')").first
            if amr_card.is_visible():
                amr_card.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(output_dir, "02_amr_detail_modal.png"))
                page.keyboard.press("Escape")
                time.sleep(0.5)
        except Exception as e:
            print(f"AMR detail capture error: {e}")

        # 3. Fleet Logs Modal
        print("Opening Fleet Logs Terminal...")
        try:
            logs_btn = page.locator("button:has-text('Logs')").first
            if logs_btn.is_visible():
                logs_btn.click()
                time.sleep(1)
                page.screenshot(path=os.path.join(output_dir, "03_fleet_logs_terminal.png"))
                page.keyboard.press("Escape")
                time.sleep(0.5)
        except Exception as e:
            print(f"Fleet logs capture error: {e}")

        # 4. Copilot Drawer
        print("Opening NexusFleet Copilot Drawer...")
        try:
            copilot_btn = page.locator("button:has-text('NexusFleet AI')").first
            if copilot_btn.is_visible():
                copilot_btn.click()
                time.sleep(1)
                # Send prompt to copilot
                chat_input = page.locator("input[type='text']").last
                if chat_input.is_visible():
                    chat_input.fill("Status da frota e métricas")
                    chat_input.press("Enter")
                    time.sleep(2.5)
                page.screenshot(path=os.path.join(output_dir, "04_copilot_assistant.png"))
                page.keyboard.press("Escape")
                time.sleep(0.5)
        except Exception as e:
            print(f"Copilot capture error: {e}")

        # 5. Layout Studio Tab
        print("Switching to Layout Studio...")
        try:
            studio_btn = page.locator("button:has-text('Studio')").first
            if studio_btn.is_visible():
                studio_btn.click()
                time.sleep(1.5)
                page.screenshot(path=os.path.join(output_dir, "05_layout_studio.png"))
        except Exception as e:
            print(f"Layout Studio capture error: {e}")

        # 6. Analytics Dashboard Tab
        print("Switching to Analytics Dashboard...")
        try:
            analytics_btn = page.locator("button:has-text('Analytics')").first
            if analytics_btn.is_visible():
                analytics_btn.click()
                time.sleep(2)
                page.screenshot(path=os.path.join(output_dir, "06_analytics_bi.png"))
        except Exception as e:
            print(f"Analytics capture error: {e}")

        # 7. Scalar API Docs
        print("Navigating to Scalar API Docs...")
        try:
            page.goto("http://localhost:8080/docs", wait_until="networkidle")
            time.sleep(3)
            page.screenshot(path=os.path.join(output_dir, "07_scalar_api_docs.png"))
        except Exception as e:
            print(f"Scalar docs capture error: {e}")

        # 8. Animated GIF recording from Simulator
        print("Recording animated GIF frames from Simulator...")
        page.goto("http://localhost:8080", wait_until="networkidle")
        time.sleep(2)

        frames = []
        frame_count = 35
        for _ in range(frame_count):
            frame_bytes = page.screenshot(type="jpeg", quality=85)
            img = Image.open(io.BytesIO(frame_bytes))
            img = img.resize((1080, 675), Image.Resampling.LANCZOS)
            img_p = img.convert("P", palette=Image.Palette.ADAPTIVE, colors=128)
            frames.append(img_p)
            time.sleep(0.18)

        if frames:
            gif_path = os.path.join(output_dir, "nexusfleet_demo.gif")
            short_gif_path = os.path.join(output_dir, "demo.gif")
            print(f"Compiling GIF to {gif_path}...")
            frames[0].save(
                gif_path,
                save_all=True,
                append_images=frames[1:],
                duration=180,
                loop=0,
                optimize=True,
            )
            shutil.copy2(gif_path, short_gif_path)
            print("GIF compilation complete!")

        browser.close()

    print("All screenshots and GIFs captured successfully!")


if __name__ == "__main__":
    capture_all()
