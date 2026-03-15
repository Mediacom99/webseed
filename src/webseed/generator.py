"""Claude Code CLI site generator — produces single-file HTML for a business."""

from __future__ import annotations

import re

from webseed.claude_cli import get_timeout, run_claude_cli
from webseed.maps import safe_name
from webseed.models import BusinessData
from webseed.ports import FileStoragePort


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
    try:
        if biz.has_photos:
            images_block = "\n".join(f"- {p}" for p in biz.photo_paths)
            image_instructions = photos_config["image_instructions"]
            gallery_instruction = f"{len(biz.photo_paths)} {photos_config['gallery_suffix']}"
        else:
            images_block = no_photos_config["images_block"]
            image_instructions = no_photos_config["image_instructions"]
            gallery_instruction = no_photos_config["gallery_instruction"]
    except KeyError as exc:
        config_name = "site_gen_photos" if biz.has_photos else "site_gen_no_photos"
        raise ValueError(
            f"Missing key {exc} in {config_name} — check the prompt has all required key=value pairs"
        ) from exc

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
    file_storage: FileStoragePort,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
    photos_config: dict[str, str] | None = None,
    no_photos_config: dict[str, str] | None = None,
) -> str:
    """Generate index.html for the business. Returns the site directory path.

    Expects photos to be already downloaded by the ``enrich`` step.
    """
    safe = safe_name(biz.name)
    site_dir = file_storage.site_dir(safe)

    prompt = _build_prompt(biz, prompt_template, photos_config or {}, no_photos_config or {})

    raw_text = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_GENERATE", 120))

    html = _strip_code_fences(raw_text)

    file_storage.write_file(f"{safe}/index.html", html)
    file_storage.write_file(f"{safe}/vercel.json", '{"version": 2}\n')

    return site_dir
