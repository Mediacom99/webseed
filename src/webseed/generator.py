"""Claude Code CLI site generator — produces single-file HTML for a business."""

import os
import re

from webseed.claude_cli import run_claude_cli


def _build_prompt(biz, prompt_template: str) -> str:
    """Fill the prompt template with business data."""
    if biz.has_photos:
        images_block = "\n".join(f"- {p}" for p in biz.photo_paths)
        image_instructions = (
            "Usa le foto di Google Maps (path relativi indicati sopra). "
            "Hero background: prima foto. Galleria: mostra tutte le foto disponibili in una grid."
        )
        gallery_instruction = f"{len(biz.photo_paths)} foto Maps disponibili"
    else:
        images_block = (
            f"Nessuna foto Maps disponibile. Fallback Unsplash: {biz.fallback_unsplash_url}"
        )
        image_instructions = (
            f"Non ci sono foto Maps. Usa questo URL Unsplash come hero background: "
            f"{biz.fallback_unsplash_url} "
            f"Per la galleria, usa 3 varianti dello stesso URL Unsplash con dimensioni diverse "
            f"(aggiungendo /?{biz.category}-2, /?{biz.category}-3)."
        )
        gallery_instruction = "usa URL Unsplash"

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
    biz,
    output_dir: str,
    prompt_template: str,
    system_prompt: str,
    model: str = "sonnet",
) -> str:
    """Generate index.html for the business. Returns the site directory path."""
    from webseed.maps import safe_name

    safe = safe_name(biz.name)
    site_dir = os.path.join(output_dir, safe)
    os.makedirs(site_dir, exist_ok=True)

    prompt = _build_prompt(biz, prompt_template)

    raw_text = run_claude_cli(prompt, system_prompt, model=model, timeout=120)

    html = _strip_code_fences(raw_text)

    html_path = os.path.join(site_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    vercel_json_path = os.path.join(site_dir, "vercel.json")
    with open(vercel_json_path, "w") as f:
        f.write('{"version": 2}\n')

    return site_dir
