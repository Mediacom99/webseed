"""Claude Code CLI site generator — produces single-file HTML for a business."""

import os
import re

from webseed.claude_cli import get_timeout, run_claude_cli
from webseed.maps import BusinessData
from webseed.utils import atomic_write


def _build_prompt(biz: BusinessData, prompt_template: str) -> str:
    """Fill the prompt template with business data."""
    if biz.has_photos:
        images_block = "\n".join(f"- {p}" for p in biz.photo_paths)
        image_instructions = (
            "Usa le foto di Google Maps (path relativi indicati sopra). "
            "Hero background: prima foto. Galleria: mostra tutte le foto disponibili in una grid."
        )
        gallery_instruction = f"{len(biz.photo_paths)} foto Maps disponibili"
    else:
        images_block = "Nessuna foto disponibile."
        image_instructions = (
            "Non ci sono foto. Usa un hero con gradiente o colore solido di sfondo, "
            "con il nome del business in grande. NON usare URL di immagini esterni. "
            "Per la galleria, ometti la sezione oppure usa placeholder con icone SVG inline."
        )
        gallery_instruction = "nessuna foto, usa design senza immagini"

    def _esc(val: str) -> str:
        """Escape braces in user data to prevent str.format() KeyError."""
        return val.replace("{", "{{").replace("}", "}}")

    return prompt_template.format(
        name=_esc(biz.name),
        category=_esc(biz.category.replace("_", " ")),
        address=_esc(biz.address),
        phone=_esc(biz.phone or "Non disponibile"),
        rating=biz.rating,
        reviews=biz.reviews,
        images_block=_esc(images_block),
        image_instructions=_esc(image_instructions),
        gallery_instruction=_esc(gallery_instruction),
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
) -> str:
    """Generate index.html for the business. Returns the site directory path.

    Expects photos to be already downloaded by the ``enrich`` step.
    """
    from webseed.maps import safe_name

    safe = safe_name(biz.name)
    site_dir = os.path.join(output_dir, safe)
    os.makedirs(site_dir, exist_ok=True)

    prompt = _build_prompt(biz, prompt_template)

    raw_text = run_claude_cli(prompt, system_prompt, model=model, timeout=get_timeout("CLAUDE_TIMEOUT_GENERATE", 120))

    html = _strip_code_fences(raw_text)

    html_path = os.path.join(site_dir, "index.html")
    atomic_write(html_path, html)

    vercel_json_path = os.path.join(site_dir, "vercel.json")
    with open(vercel_json_path, "w") as f:
        f.write('{"version": 2}\n')

    return site_dir
