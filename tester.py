"""Playwright smoke test — verify deployed site loads correctly."""

import os

from playwright.sync_api import sync_playwright


def smoke_test(url: str, safe_name: str, screenshots_dir: str) -> dict:
    """Load the URL in headless Chromium, take a screenshot, return status."""
    os.makedirs(screenshots_dir, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 720})

        try:
            page.goto(url, timeout=30000, wait_until="networkidle")
            title = page.title()
            has_content = page.locator("body").inner_text() != ""
            screenshot_path = os.path.join(screenshots_dir, f"{safe_name}.png")
            page.screenshot(path=screenshot_path, full_page=True)

            return {
                "ok": True,
                "title": title,
                "has_content": has_content,
                "screenshot": screenshot_path,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            browser.close()
