"""Claude Code CLI site generator — produces single-file HTML for a business."""

import os
import re

from webseed.claude_cli import get_timeout, run_claude_cli
from webseed.maps import BusinessData
from webseed.utils import atomic_write


def parse_kv(text: str) -> dict[str, str]:
    """Parse a simple ``key: value`` text file into a dict (one pair per line)."""
    result: dict[str, str] = {}
    for line in text.splitlines():
        if ": " in line:
            key, value = line.split(": ", 1)
            result[key.strip()] = value.strip()
    return result


def _build_prompt(
    biz: BusinessData,
    prompt_template: str,
    photos_config: dict[str, str],
    no_photos_config: dict[str, str],
) -> str:
    """Fill the prompt template with business data."""
    if biz.has_photos:
        images_block = "\n".join(f"- {p}" for p in biz.photo_paths)
        image_instructions = photos_config["image_instructions"]
        gallery_instruction = f"{len(biz.photo_paths)} {photos_config['gallery_suffix']}"
    else:
        images_block = no_photos_config["images_block"]
        image_instructions = no_photos_config["image_instructions"]
        gallery_instruction = no_photos_config["gallery_instruction"]

    return prompt_template.format(
        name=biz.name,
        category=biz.category.replace("_", " "),
        address=biz.address,
        phone=biz.phone or "Non disponibile",
        rating=biz.rating,
        reviews=biz.reviews,
        images_block=images_block,
        image_instructions=image_instructions,
        gallery_instruction=gallery_instruction,
    )


def _strip_code_fences(html: str) -> str:
    """Remove markdown code fences if Claude includes them despite instructions."""
    html = re.sub(r"^```html?\n?", "", html.strip())
    html = re.sub(r"\n?```$", "", html.strip())
    return html


def generate(
    biz: BusinessData,
    output_dir: str,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
    photos_config: dict[str, str] | None = None,
    no_photos_config: dict[str, str] | None = None,
) -> str:
    """Generate index.html for the business. Returns the site directory path.

    Expects photos to be already downloaded by the ``enrich`` step.
    """
    from webseed.maps import safe_name

    safe = safe_name(biz.name)
    site_dir = os.path.join(output_dir, safe)
    os.makedirs(site_dir, exist_ok=True)

    prompt = _build_prompt(biz, prompt_template, photos_config or {}, no_photos_config or {})

    raw_text = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_GENERATE", 120))

    html = _strip_code_fences(raw_text)

    html_path = os.path.join(site_dir, "index.html")
    atomic_write(html_path, html)

    vercel_json_path = os.path.join(site_dir, "vercel.json")
    with open(vercel_json_path, "w") as f:
        f.write('{"version": 2}\n')

    return site_dir
