"""Visual testing via Claude Code CLI + Playwright MCP, and email screenshots."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

log = logging.getLogger(__name__)

from playwright.sync_api import sync_playwright

from webseed.claude_cli import extract_json_result, get_timeout, run_claude_cli
from webseed.ports import FileStoragePort

# ---------------------------------------------------------------------------
# Code review (Claude Code CLI, text-only — no browser needed)
# ---------------------------------------------------------------------------

def code_review(
    file_storage: FileStoragePort,
    name_slug: str,
    business_name: str,
    category: str,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
) -> dict[str, Any]:
    """Run a code review on the local index.html via Claude Code CLI.

    Returns ``{"ok": bool, "issues": list, "summary": str, "error": str}``.
    """
    html = file_storage.read_file(f"{name_slug}/index.html")

    prompt = prompt_template.format(
        name=business_name,
        category=category,
        html=html,
    )

    try:
        raw = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_TEST", 120))
        result = extract_json_result(raw)
        return {
            "ok": result.get("pass", False),
            "issues": result.get("issues", []),
            "summary": result.get("summary", ""),
            "error": "",
        }
    except (ValueError, json.JSONDecodeError) as e:
        return {"ok": False, "issues": [], "summary": "", "error": str(e)}
    except Exception as e:
        return {"ok": False, "issues": [], "summary": "", "error": str(e)}


# ---------------------------------------------------------------------------
# Visual test (Claude Code CLI + Playwright MCP)
# ---------------------------------------------------------------------------

def visual_test(
    url: str,
    business_name: str,
    category: str,
    file_storage: FileStoragePort,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
) -> dict[str, Any]:
    """Run a Claude Code CLI visual test on a deployed preview URL.

    Claude navigates the site via Playwright MCP, takes screenshots,
    inspects the DOM, and evaluates against a QA checklist.

    Returns ``{"ok": bool, "issues": list, "summary": str, "error": str}``.
    """
    # Ensure screenshots dir exists
    file_storage.screenshots_dir()

    prompt = prompt_template.format(
        url=url,
        name=business_name,
        category=category,
    )

    try:
        raw = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_TEST", 180), use_tools=True)
        result = extract_json_result(raw)
        return {
            "ok": result.get("pass", False),
            "issues": result.get("issues", []),
            "summary": result.get("summary", ""),
            "error": "",
        }
    except (ValueError, json.JSONDecodeError) as e:
        return {"ok": False, "issues": [], "summary": "", "error": str(e)}
    except Exception as e:
        return {"ok": False, "issues": [], "summary": "", "error": str(e)}


# ---------------------------------------------------------------------------
# Fix HTML (Claude Code CLI, text-only — no browser needed)
# ---------------------------------------------------------------------------

def _strip_code_fences(html: str) -> str:
    """Remove markdown code fences if Claude includes them."""
    html = re.sub(r"^```html?\n?", "", html.strip())
    html = re.sub(r"\n?```$", "", html.strip())
    return html


def fix_html(
    file_storage: FileStoragePort,
    name_slug: str,
    issues: list[dict[str, Any]],
    business_name: str,
    category: str,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
) -> None:
    """Fix index.html based on QA issues using Claude Code CLI. Modifies in place."""
    current_html = file_storage.read_file(f"{name_slug}/index.html")

    issues_text = "\n".join(
        f"- [{i['severity']}] {i['description']}" for i in issues
    )

    prompt = prompt_template.format(
        name=business_name,
        category=category,
        issues=issues_text,
        html=current_html,
    )

    raw = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_TEST", 120))
    fixed_html = _strip_code_fences(raw)

    file_storage.write_file(f"{name_slug}/index.html", fixed_html)


# ---------------------------------------------------------------------------
# Email screenshot (Python Playwright — mechanical task, no AI needed)
# ---------------------------------------------------------------------------

def capture_email_screenshot(url: str, safe_name: str, file_storage: FileStoragePort) -> str:
    """Capture a 1280x600 above-the-fold screenshot for email embedding.

    Returns the screenshot path, or "" if capture fails.
    """
    try:
        screenshots_dir = file_storage.screenshots_dir()
        screenshot_path = os.path.join(screenshots_dir, f"{safe_name}_email.png")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 600})
            try:
                page.goto(url, timeout=30000, wait_until="domcontentloaded")
                page.screenshot(
                    path=screenshot_path,
                    clip={"x": 0, "y": 0, "width": 1280, "height": 600},
                )
            finally:
                browser.close()

        return screenshot_path
    except Exception as e:
        log.warning("Screenshot email fallito: %s", e)
        return ""
