"""Initial schema and seed data.

Revision ID: 0001
Revises: None
Create Date: 2026-03-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── businesses table ──
    op.create_table(
        "businesses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("place_id", sa.String(100), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text(), server_default=""),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), server_default=""),
        sa.Column("rating", sa.Float(), server_default="0"),
        sa.Column("reviews", sa.Integer(), server_default="0"),
        sa.Column("category", sa.String(100), server_default=""),
        sa.Column("maps_url", sa.Text(), server_default=""),
        sa.Column("has_photos", sa.Boolean(), server_default="false"),
        sa.Column("photo_paths", JSONB(), server_default=sa.text("'[]'")),
        sa.Column("photo_refs", JSONB(), server_default=sa.text("'[]'")),
        sa.Column("fallback_unsplash_url", sa.Text(), server_default=""),
        sa.Column("lead_score", sa.Integer(), server_default="0"),
        sa.Column("price_level", sa.String(50), nullable=True),
        sa.Column("business_status", sa.String(50), server_default="OPERATIONAL"),
        sa.Column("primary_type", sa.String(100), nullable=True),
        sa.Column("types", JSONB(), nullable=True),
        sa.Column("has_opening_hours", sa.Boolean(), server_default="false"),
        sa.Column("opening_hours_summary", sa.Text(), nullable=True),
        sa.Column("accepts_credit_cards", sa.Boolean(), nullable=True),
        sa.Column("editorial_summary", sa.Text(), nullable=True),
        sa.Column("review_texts", JSONB(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="searched"),
        sa.Column("error_detail", sa.Text(), server_default=""),
        sa.Column("vercel_url", sa.Text(), server_default=""),
        sa.Column("site_screenshot_path", sa.Text(), server_default=""),
        sa.Column("email_sent_at", sa.String(50), server_default=""),
        sa.Column("test_iterations", sa.Integer(), server_default="0"),
        sa.Column("test_issues", JSONB(), server_default=sa.text("'[]'")),
        sa.Column("run_id", sa.String(64), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_businesses_status", "businesses", ["status"])
    op.create_index("idx_businesses_place_id", "businesses", ["place_id"])

    # ── settings table ──
    op.create_table(
        "settings",
        sa.Column("key", sa.String(100), primary_key=True),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )

    # ── event_log table ──
    op.create_table(
        "event_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", sa.String(36), nullable=False),
        sa.Column("place_id", sa.String(100), nullable=True),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("step", sa.String(32), nullable=True),
        sa.Column("message", sa.Text(), server_default=""),
        sa.Column("data", JSONB(), server_default=sa.text("'{}'")),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
    )
    op.create_index("idx_event_log_job_id", "event_log", ["job_id"])
    op.create_index("idx_event_log_timestamp", "event_log", ["timestamp"])

    # ── Seed settings ──
    settings_table = sa.table(
        "settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Text),
        sa.column("description", sa.Text),
    )

    seeds = _get_seed_data()
    op.bulk_insert(settings_table, seeds)


def downgrade() -> None:
    op.drop_table("event_log")
    op.drop_table("settings")
    op.drop_table("businesses")


def _get_seed_data() -> list[dict[str, str]]:
    """Return all prompt and config seed data."""
    return [
        # ── Prompts ──
        {
            "key": "prompt.site_gen",
            "value": _PROMPT_SITE_GEN,
            "description": "Italian site generation user prompt template",
        },
        {
            "key": "prompt.site_gen_system",
            "value": _PROMPT_SITE_GEN_SYSTEM,
            "description": "System prompt for site generation",
        },
        {
            "key": "prompt.site_gen_photos",
            "value": _PROMPT_SITE_GEN_PHOTOS,
            "description": "Photo config for site generation (key: value format)",
        },
        {
            "key": "prompt.site_gen_no_photos",
            "value": _PROMPT_SITE_GEN_NO_PHOTOS,
            "description": "No-photo config for site generation (key: value format)",
        },
        {
            "key": "prompt.code_review",
            "value": _PROMPT_CODE_REVIEW,
            "description": "HTML code review QA checklist prompt",
        },
        {
            "key": "prompt.code_review_system",
            "value": _PROMPT_CODE_REVIEW_SYSTEM,
            "description": "System prompt for code review (Italian QA engineer)",
        },
        {
            "key": "prompt.visual_test",
            "value": _PROMPT_VISUAL_TEST,
            "description": "QA checklist prompt for Playwright visual testing",
        },
        {
            "key": "prompt.visual_test_system",
            "value": _PROMPT_VISUAL_TEST_SYSTEM,
            "description": "System prompt for visual testing (Italian QA + Playwright)",
        },
        {
            "key": "prompt.fix_html",
            "value": _PROMPT_FIX_HTML,
            "description": "HTML fix prompt template",
        },
        {
            "key": "prompt.fix_html_system",
            "value": _PROMPT_FIX_HTML_SYSTEM,
            "description": "System prompt for HTML fixing (Italian web designer)",
        },
        {
            "key": "prompt.email_gen",
            "value": _PROMPT_EMAIL_GEN,
            "description": "Italian email generation prompt template",
        },
        {
            "key": "prompt.email_gen_system",
            "value": _PROMPT_EMAIL_GEN_SYSTEM,
            "description": "System prompt for email generation (Italian B2B copywriter)",
        },
        # ── Config ──
        {
            "key": "config.contact_email",
            "value": "",
            "description": "Contact email shown in email footer for data requests",
        },
        {
            "key": "config.sender_name",
            "value": "Edoardo di WebSeed",
            "description": "Sender display name in outreach emails",
        },
        {
            "key": "config.default_model",
            "value": "sonnet",
            "description": "Default Claude model for generation and email",
        },
        {
            "key": "config.test_model",
            "value": "sonnet",
            "description": "Default Claude model for testing",
        },
        {
            "key": "config.max_fix_iterations",
            "value": "3",
            "description": "Maximum test-fix cycles before giving up",
        },
        {
            "key": "config.gmail_label_name",
            "value": "webseed-queue",
            "description": "Gmail label for draft emails",
        },
        {
            "key": "config.max_photos",
            "value": "3",
            "description": "Maximum photos to download per business",
        },
        {
            "key": "config.timeout_generate",
            "value": "120",
            "description": "Claude CLI timeout in seconds for site generation",
        },
        {
            "key": "config.timeout_test",
            "value": "120",
            "description": "Claude CLI timeout in seconds for testing",
        },
        {
            "key": "config.timeout_email",
            "value": "180",
            "description": "Claude CLI timeout in seconds for email generation",
        },
    ]


# ═══════════════════════════════════════════════════════════════════
# Prompt content (seeded from src/webseed/prompts/*.txt files)
# ═══════════════════════════════════════════════════════════════════

_PROMPT_SITE_GEN = """\
Sei un web designer esperto. Crea un sito web single-page professionale per questo business locale italiano.

BUSINESS:
- Nome: {name}
- Tipo: {category}
- Indirizzo: {address}
- Telefono: {phone}
- Rating Google: {rating}/5 ({reviews} recensioni)

IMMAGINI DISPONIBILI:
{images_block}

REQUISITI TECNICI:
- Un SINGOLO file HTML completo con tutto inline (CSS nel <style>, JS nel <script>)
- Mobile-first e responsive (viewport meta + media queries)
- Design moderno e professionale adatto al settore

SEZIONI OBBLIGATORIE (in quest'ordine):
1. HERO — immagine/background full-width, nome business in grande, sottotitolo, CTA "Chiamaci ora" (href="tel:{phone}"). Se il telefono è "Non disponibile", NON inserire link tel: e usa "Contattaci" come CTA generico.
2. CHI SIAMO — 2-3 paragrafi caldi e professionali, basati sul tipo di business (non generici)
3. SERVIZI — 3-4 card con icona emoji + titolo + descrizione breve
4. GALLERIA — mostra le immagini disponibili ({gallery_instruction})
5. CONTATTI — iframe Google Maps embed (USA QUESTO FORMATO SENZA API KEY: src="https://maps.google.com/maps?q=INDIRIZZO+ENCODATO&output=embed" — NON usare maps/embed/v1/ e NON inventare API key) + tel cliccabile + indirizzo formattato
6. FOOTER — "© 2025 {name} · Tutti i diritti riservati"

STILE:
- Google Fonts CDN (scegli font adatto: serif per ristoranti, sans per servizi, ecc.)
- Palette colori coerente col settore
- Hover effects e transizioni CSS leggere
- Sticky navbar con il nome del business

ISTRUZIONI IMMAGINI:
{image_instructions}

Rispondi ESCLUSIVAMENTE con il codice HTML. Nessun testo aggiuntivo, nessun markdown."""

_PROMPT_SITE_GEN_SYSTEM = """\
Sei un web designer esperto specializzato in siti per business locali italiani.
Crea siti web single-page in HTML con CSS e JS inline.
Output ESCLUSIVAMENTE codice HTML valido, partendo da <!DOCTYPE html> e finendo con </html>.
NON usare tool, NON scrivere file, NON aggiungere markdown, spiegazioni o testo aggiuntivo.
La tua risposta DEVE contenere SOLO il codice HTML."""

_PROMPT_SITE_GEN_PHOTOS = """\
image_instructions: Usa le foto di Google Maps (path relativi indicati sopra). Hero background: prima foto. Galleria: mostra tutte le foto disponibili in una grid.
gallery_suffix: foto Maps disponibili"""

_PROMPT_SITE_GEN_NO_PHOTOS = """\
images_block: Nessuna foto disponibile.
image_instructions: Non ci sono foto. Usa un hero con gradiente o colore solido di sfondo, con il nome del business in grande. NON usare URL di immagini esterni. Per la galleria, ometti la sezione oppure usa placeholder con icone SVG inline.
gallery_instruction: nessuna foto, usa design senza immagini"""

_PROMPT_CODE_REVIEW = """\
Sei un QA engineer senior. Devi fare code review dell'HTML di un sito web per un business locale italiano.

Business: {name} ({category})

HTML DA ANALIZZARE:
```html
{html}
```

CHECKLIST DI VALUTAZIONE:

- [ ] HTML valido: tag aperti/chiusi correttamente, nessun errore di sintassi
- [ ] Hero section: presente, contiene il nome del business, ha background-image o background-color
- [ ] Navbar: presente con position sticky/fixed, mostra il nome del business
- [ ] Sezione "Chi Siamo": presente, con testo in italiano pertinente al tipo di business (non generico)
- [ ] Sezione "Servizi": presente, con almeno 3 card/elementi
- [ ] Sezione "Galleria": presente, img src puntano a path relativi (img/photo*.jpg) o URL validi
- [ ] Sezione "Contatti": presente, con indirizzo e telefono
- [ ] Google Maps iframe: usa formato https://maps.google.com/maps?q=...&output=embed (NON maps/embed/v1/ con API key)
- [ ] Footer: presente, con copyright
- [ ] Testo: tutto in italiano, nessun lorem ipsum, nessun placeholder, nessun testo in inglese
- [ ] CSS: contrasti di colore adeguati (no testo bianco su sfondo bianco), font-size leggibili
- [ ] Mobile: viewport meta tag presente, media queries per responsive design
- [ ] Link tel: se telefono disponibile, href="tel:..." corretto; se "Non disponibile", nessun link tel:
- [ ] Nessuna API key hardcoded nel codice

LIVELLI DI SEVERITA:
- critical: HTML non valido, sezioni obbligatorie mancanti, pagina non renderizzabile
- major: contrasti illeggibili, immagini con path errati, testo in inglese, API key esposta
- minor: piccoli difetti CSS, spaziature imprecise, best practice mancate

DOPO la valutazione, riporta i risultati in questo formato ESATTO:

---JSON_RESULT---
{{"pass": true, "issues": [], "summary": "Tutti i controlli superati"}}
---JSON_RESULT---

Oppure se ci sono problemi:

---JSON_RESULT---
{{"pass": false, "issues": [{{"severity": "major", "description": "Descrizione del problema"}}], "summary": "Riassunto in una riga"}}
---JSON_RESULT---

IMPORTANTE: Il blocco JSON_RESULT DEVE essere presente nella tua risposta."""

_PROMPT_CODE_REVIEW_SYSTEM = """\
Sei un QA engineer senior. Analizza il codice HTML e riporta eventuali problemi. \
NON usare strumenti browser o Playwright. Analizza solo il codice sorgente."""

_PROMPT_VISUAL_TEST = """\
Sei un QA engineer senior. Devi testare visivamente un sito web per un business locale italiano.

URL: {url}
Business: {name} ({category})

PROCEDURA — usa gli strumenti Playwright MCP in quest'ordine:

1. browser_navigate verso {url}, attendi il caricamento completo
2. browser_console_messages per verificare eventuali errori JavaScript
3. browser_snapshot per ispezionare la struttura DOM e l'accessibilita
4. browser_take_screenshot per catturare la pagina intera

CHECKLIST DI VALUTAZIONE:

- [ ] La pagina si carica senza errori JS nella console
- [ ] Hero section: visibile, contiene il nome del business, ha un'immagine di sfondo o colore
- [ ] Navbar: presente e sticky, mostra il nome del business
- [ ] Sezione "Chi Siamo": presente, con testo in italiano pertinente al tipo di business
- [ ] Sezione "Servizi": presente, con almeno 3 servizi/card
- [ ] Sezione "Galleria": presente, le immagini si caricano correttamente (nessuna immagine rotta)
- [ ] Sezione "Contatti": presente, con indirizzo e/o telefono
- [ ] Footer: presente, con copyright
- [ ] Testo: tutto in italiano, nessun lorem ipsum o placeholder
- [ ] Layout mobile: ridimensiona a 375px (browser_resize width=375 height=812), verifica che non ci sia overflow orizzontale e che il contenuto sia leggibile

LIVELLI DI SEVERITA:
- critical: pagina non carica, pagina bianca, layout completamente rotto
- major: sezioni mancanti, immagini rotte, testo illeggibile, navigazione non funzionante
- minor: piccoli difetti visivi, spaziature imprecise, elementi non critici mancanti

DOPO la valutazione, riporta i risultati in questo formato ESATTO:

---JSON_RESULT---
{{"pass": true, "issues": [], "summary": "Tutti i controlli superati"}}
---JSON_RESULT---

Oppure se ci sono problemi:

---JSON_RESULT---
{{"pass": false, "issues": [{{"severity": "major", "description": "Descrizione del problema"}}], "summary": "Riassunto in una riga"}}
---JSON_RESULT---

IMPORTANTE: Il blocco JSON_RESULT DEVE essere presente nella tua risposta."""

_PROMPT_VISUAL_TEST_SYSTEM = """\
Sei un QA engineer senior. Usa gli strumenti Playwright MCP per \
testare visivamente il sito web. Segui la procedura indicata nel prompt."""

_PROMPT_FIX_HTML = """\
Sei un web designer esperto. Correggi questo sito HTML per un business locale italiano.

BUSINESS: {name} ({category})

PROBLEMI TROVATI DAL QA:
{issues}

HTML ATTUALE:
{html}

ISTRUZIONI:
- Correggi TUTTI i problemi elencati sopra
- Mantieni la struttura e lo stile generale del sito
- Mantieni tutte le sezioni esistenti che funzionano
- Il sito deve rimanere un singolo file HTML con CSS e JS inline
- Il testo deve essere in italiano

Rispondi ESCLUSIVAMENTE con il codice HTML corretto. Nessun testo aggiuntivo, nessun markdown."""

_PROMPT_FIX_HTML_SYSTEM = """\
Sei un web designer esperto. Correggi il codice HTML secondo le istruzioni. \
Rispondi ESCLUSIVAMENTE con il codice HTML corretto."""

_PROMPT_EMAIL_GEN = """\
Sei un copywriter esperto in comunicazione B2B italiana. Scrivi un'email commerciale per proporre un sito web professionale a un business locale che attualmente non ha un sito.

BUSINESS:
- Nome: {name}
- Tipo: {category}
- Indirizzo: {address}
- Telefono: {phone}
- Rating Google: {rating}/5 ({reviews} recensioni)

SITO CREATO: {site_url}

OFFERTA:
- Setup sito web professionale: €299 (una tantum)
- Mantenimento e hosting: €9/mese
- Il sito è già pronto e online (vedi link sopra)

TONO:
- Italiano, dare del Lei ma senza essere rigido o troppo formale
- Professionale ma caloroso e diretto
- Evidenzia il valore: i clienti cercano online, un sito aumenta la visibilità e le prenotazioni
- Menziona il loro rating Google come punto di forza

CONTENUTO EMAIL:
1. Saluto personalizzato col nome del business
2. Complimento genuino basato sulle recensioni/rating
3. Proposta del sito già pronto con link cliccabile
4. Prezzi chiari (€299 + €9/mese)
5. Call to action: rispondere a questa email o chiamare. Se il telefono è "Non disponibile", non menzionare il numero di telefono.
6. Nota: "In fondo a questa email trova un'anteprima del sito che abbiamo preparato per voi."

Il body deve essere HTML semplice (paragrafi, link, bold). NON usare tag <html>/<head>/<body>.

FOOTER (includi letteralmente alla fine del body):
<p style="font-size:11px;color:#999;margin-top:30px;">
Dati raccolti da Google Maps. Per richieste: {contact_email}
</p>

FORMATO OUTPUT — usa esattamente questi marker:

---SUBJECT---
L'oggetto dell'email qui
---SUBJECT---

---BODY_HTML---
<p>Il body HTML dell'email qui...</p>
---BODY_HTML---

Nessun testo aggiuntivo fuori dai marker."""

_PROMPT_EMAIL_GEN_SYSTEM = """\
Sei un copywriter esperto in comunicazione B2B italiana. Rispondi usando ESCLUSIVAMENTE i marker ---SUBJECT--- e ---BODY_HTML--- come indicato nel prompt. NON usare JSON, NON usare markdown, NON aggiungere testo fuori dai marker."""
