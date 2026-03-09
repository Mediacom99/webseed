"""Visual testing via Claude Code CLI + Playwright MCP, and email screenshots."""

import json
import os
import re

from playwright.sync_api import sync_playwright

from webseed.claude_cli import extract_json_result, run_claude_cli


# ---------------------------------------------------------------------------
# Code review (Claude Code CLI, text-only — no browser needed)
# ---------------------------------------------------------------------------

def code_review(
    site_dir: str,
    business_name: str,
    category: str,
    prompt_template: str,
    model: str = "sonnet",
) -> dict:
    """Run a code review on the local index.html via Claude Code CLI.

    Returns ``{"ok": bool, "issues": list, "summary": str, "error": str}``.
    """
    html_path = os.path.join(site_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    prompt = prompt_template.format(
        name=business_name,
        category=category,
        html=html,
    )

    system_prompt = (
        "Sei un QA engineer senior. Analizza il codice HTML e riporta eventuali problemi. "
        "NON usare strumenti browser o Playwright. Analizza solo il codice sorgente."
    )

    try:
        raw = run_claude_cli(prompt, system_prompt, model=model, timeout=120)
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
    safe_name: str,
    screenshots_dir: str,
    prompt_template: str,
    model: str = "sonnet",
) -> dict:
    """Run a Claude Code CLI visual test on a deployed preview URL.

    Claude navigates the site via Playwright MCP, takes screenshots,
    inspects the DOM, and evaluates against a QA checklist.

    Returns ``{"ok": bool, "issues": list, "summary": str, "error": str}``.
    """
    os.makedirs(screenshots_dir, exist_ok=True)

    prompt = prompt_template.format(
        url=url,
        name=business_name,
        category=category,
    )

    system_prompt = (
        "Sei un QA engineer senior. Usa gli strumenti Playwright MCP per "
        "testare visivamente il sito web. Segui la procedura indicata nel prompt."
    )

    try:
        raw = run_claude_cli(prompt, system_prompt, model=model, timeout=180, use_tools=True)
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
    site_dir: str,
    issues: list,
    business_name: str,
    category: str,
    prompt_template: str,
    model: str = "sonnet",
) -> None:
    """Fix index.html based on QA issues using Claude Code CLI. Modifies in place."""
    html_path = os.path.join(site_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        current_html = f.read()

    issues_text = "\n".join(
        f"- [{i['severity']}] {i['description']}" for i in issues
    )

    prompt = prompt_template.format(
        name=business_name,
        category=category,
        issues=issues_text,
        html=current_html,
    )

    system_prompt = (
        "Sei un web designer esperto. Correggi il codice HTML secondo le istruzioni. "
        "Rispondi ESCLUSIVAMENTE con il codice HTML corretto."
    )

    raw = run_claude_cli(prompt, system_prompt, model=model, timeout=120)
    fixed_html = _strip_code_fences(raw)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(fixed_html)


# ---------------------------------------------------------------------------
# Email screenshot (Python Playwright — mechanical task, no AI needed)
# ---------------------------------------------------------------------------

def capture_email_screenshot(url: str, safe_name: str, screenshots_dir: str) -> str:
    """Capture a 1280x600 above-the-fold screenshot for email embedding.

    Returns the screenshot path, or "" if capture fails.
    """
    try:
        os.makedirs(screenshots_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshots_dir, f"{safe_name}_email.png")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 600})
            try:
                page.goto(url, timeout=30000, wait_until="networkidle")
                page.screenshot(
                    path=screenshot_path,
                    clip={"x": 0, "y": 0, "width": 1280, "height": 600},
                )
            finally:
                browser.close()

        return screenshot_path
    except Exception as e:
        print(f"  ⚠️ Screenshot email fallito: {e}")
        return ""
