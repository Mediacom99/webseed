# webseed

Automated CLI pipeline that finds Italian local businesses without websites on Google Maps, generates professional HTML sites with Claude AI, tests them locally, deploys to Vercel, creates personalized email drafts in Gmail for outreach, and tracks everything in a local TinyDB database.

> **Claude's role**: General-purpose helper for all things webseed — implementing features, fixing bugs, improving prompts, designing architecture, testing, product strategy, and anything else that evolves around webseed as a product and codebase.

## Tech Stack

- **Python ≥3.11** — `src/` layout package, venv at `.venv/`, managed via `pyproject.toml` (`.python-version` pins 3.14 for dev)
- **Google Maps Places API** (legacy) — business discovery via `googlemaps` library
- **Claude Code CLI** — site generation, visual testing, HTML fixes, and email generation (via `claude --print` subprocess)
- **Vercel CLI** — deployment (`npm i -g vercel`)
- **Playwright MCP** — visual testing via Claude Code CLI (browser navigation, screenshots, DOM inspection)
- **Playwright** (Python) — above-the-fold email screenshots only
- **TinyDB** — local JSON-based state management (`webseed.json`)
- **Gmail API** — OAuth-based draft creation with label management

## Project Structure

```
webseed/                          (project root)
├── pyproject.toml                (project metadata, dependencies, CLI entry point)
├── .python-version               (3.14 — dev version)
├── .env / .env.example
├── CLAUDE.md
└── src/
    └── webseed/                  (Python package)
        ├── __init__.py
        ├── __main__.py           (python -m webseed entry)
        ├── claude_cli.py          (Claude Code CLI subprocess helper)
        ├── pipeline.py           (CLI entry point, orchestrates all steps)
        ├── store.py              (TinyDB data store)
        ├── maps.py               (Google Places search, photo download)
        ├── generator.py          (Claude Code CLI HTML generation)
        ├── deployer.py           (Vercel deploy under shared 'webseed' project)
        ├── tester.py             (Visual testing via Claude CLI + email screenshots)
        ├── emailer.py            (Gmail draft creation + Claude email gen)
        └── prompts/
            ├── site_gen.txt      (Italian site generation user prompt)
            ├── site_gen_system.txt (site generation system prompt)
            ├── code_review.txt   (HTML code review QA checklist)
            ├── visual_test.txt   (QA checklist for Playwright visual testing)
            ├── fix_html.txt      (HTML fix prompt)
            └── email_gen.txt     (Italian email generation prompt)
```

## Pipeline Flow

```
Search (Maps) → Generate (Claude) → Test (Code Review + optional Playwright) → Deploy (Vercel) → Email (Claude+Gmail Draft)
```

Each step is independent and resumable. State is tracked per-business in TinyDB with status progression:
`searched` → `generated` → `tested` → `deployed` → `email_queued`

Error statuses: `error_generate`, `error_test`, `error_deploy`, `error_email`. Special: `opted_out` (blacklisted). `emailed` is a valid reset target but not currently set by the pipeline.

## Module Map

| File | Role |
|------|------|
| `src/webseed/pipeline.py` | CLI entry point with subcommands (`search`, `generate`, `test`, `deploy`, `email`, `run` + management). Orchestrates all pipeline steps |
| `src/webseed/claude_cli.py` | `run_claude_cli()` subprocess helper + `extract_json_result()` JSON parser. Shared by generator, tester, and emailer |
| `src/webseed/store.py` | TinyDB data store — open/upsert/query businesses, status updates, blacklist management |
| `src/webseed/maps.py` | Searches Google Places for businesses without websites, downloads photos. Returns `BusinessData` dataclasses |
| `src/webseed/generator.py` | Builds prompt from template + business data, calls Claude Code CLI, writes single-file `index.html` with inline CSS/JS |
| `src/webseed/deployer.py` | Deploy to Vercel under a single `webseed` project. Each business gets a unique public deployment URL |
| `src/webseed/tester.py` | Visual testing via Claude Code CLI + Playwright MCP, HTML fixes, and email screenshot capture (Python Playwright) |
| `src/webseed/emailer.py` | Gmail API auth, Claude Code CLI email generation, MIME draft creation with inline screenshot |
| `src/webseed/prompts/site_gen.txt` | Italian-language user prompt template for site generation |
| `src/webseed/prompts/site_gen_system.txt` | System prompt for site generation |
| `src/webseed/prompts/code_review.txt` | HTML code review QA checklist (text-only, no browser) |
| `src/webseed/prompts/visual_test.txt` | QA checklist prompt for Playwright visual testing |
| `src/webseed/prompts/fix_html.txt` | HTML fix prompt template |
| `src/webseed/prompts/email_gen.txt` | Italian-language prompt template for email generation (outputs JSON) |

## CLI Usage

### Installation

```bash
pip install -e .     # editable install from project root
```

### Pipeline Subcommands

```bash
# 1. Search — find businesses on Maps, save to DB
webseed search --location "Milano, Italy" --query "ristorante" --limit 5

# 2. Generate — create HTML sites via Claude Code CLI (place_ids required)
webseed generate PLACE_ID "nome"       # by place_id or name
webseed generate PLACE_ID --model opus # use a specific model

# 3. Test — code review + fix loop (local, no deploy needed) (place_ids required)
webseed test PLACE_ID "nome"           # by place_id or name
webseed test PLACE_ID --playwright     # also run Playwright visual test
webseed test PLACE_ID --max-fix-iterations 1    # limit fix-retest cycles (default: 3)
webseed test PLACE_ID --test-model sonnet       # model for testing (default: sonnet)

# 4. Deploy — deploy to Vercel + email screenshot (place_ids required)
webseed deploy PLACE_ID "nome"         # by place_id or name

# 5. Email — generate personalized emails, create Gmail drafts (place_ids required)
webseed email PLACE_ID "nome"          # by place_id or name
webseed email PLACE_ID --model opus    # use a specific model

# 6. Run — full pipeline (generate → test → deploy → email) for specific businesses
webseed run PLACE_ID [PLACE_ID...]     # required: one or more identifiers
webseed run "nome" --no-email          # skip email step
webseed run PLACE_ID --model opus --test-model sonnet --max-fix-iterations 1
```

Alternative invocation: `python -m webseed <subcommand>`

### Management Subcommands

```bash
webseed status                              # Table of all businesses + statuses
webseed status --filter deployed             # Filter by status prefix
webseed show PLACE_ID                        # Full detail for one business
webseed stats                                # Summary counts per status
webseed blacklist-add PLACE_ID [PLACE_ID...] # Add to blacklist
webseed blacklist-remove PLACE_ID            # Remove from blacklist
webseed blacklist-list                       # Show all blacklisted
webseed reset PLACE_ID --to searched         # Reset status to re-process
webseed db-delete PLACE_ID [PLACE_ID...]     # Remove from DB only (keeps files + Vercel)
webseed db-delete --all --skip PLACE_ID      # Remove all except specified
webseed hard-delete PLACE_ID [PLACE_ID...]   # Delete DB + files + Vercel deployment
webseed hard-delete --blacklist PLACE_ID     # Same but keep entry as blacklisted
webseed hard-delete -y PLACE_ID              # Skip confirmation
webseed export-csv --output results.csv      # Export DB to CSV
```

### Global Flags

- `--db` — TinyDB file path (default: `webseed.json`)
- `--results-dir` — output directory (default: `results/`)
- `-v` / `--verbose` — enable DEBUG logging

## Environment Variables

Defined in `.env` (copy from `.env.example`):

- `GOOGLE_MAPS_API_KEY` — Google Cloud, **legacy Places API** enabled
- `CLAUDE_CLI_PATH` — (optional) path to Claude Code CLI binary; auto-detected if on PATH
- `VERCEL_CLI_PATH` — (optional) path to Vercel CLI binary; auto-detected if on PATH
- `GMAIL_CREDENTIALS_FILE` — path to Gmail OAuth credentials JSON (default: `credentials.json`)
- `CONTACT_EMAIL` — **required for `email` step** — email address shown in email footer for data requests
- `SENDER_NAME` — (optional) sender display name in emails (default: `Edoardo di WebSeed`)

## Auth Notes

- **Claude Code CLI**: Used for all AI steps (site generation, visual testing, HTML fixes, email generation). Handles its own auth — no API key needed
- **Gmail API**: OAuth2 desktop app flow. First run of `email` step opens browser for consent → saves `token.json`. Scopes: `gmail.compose`, `gmail.labels`, `gmail.modify`
- **Gmail setup**: GCP Console → Enable Gmail API → OAuth consent screen → Credentials → Desktop app → Download `credentials.json`

## State Management

- **TinyDB** (`webseed.json`): local JSON database, one document per business with all fields + status
- **Blacklist**: dual — `blacklist.txt` (local file, one place_id per line) + DB entries with `opted_out` status
- **Deduplication**: cross-run by `place_id`. Existing businesses get info updated (rating, reviews) but skip regeneration
- **Error tracking**: status like `error_deploy` + `error_detail` field with message

## Test Flow

1. `code_review()` — Claude Code CLI analyzes `index.html` source code against QA checklist (text-only, no browser)
2. (optional) `visual_test()` — Claude Code CLI + Playwright MCP navigates local file, takes screenshots, inspects DOM. Enabled with `--playwright`
3. Fix loop (if test fails) — `fix_html()` sends issues + current HTML to Claude Code CLI, rewrites `index.html`, retests. Max iterations configurable via `--max-fix-iterations` (default 3)

## Deploy Flow

1. `deploy()` — all sites deploy under a single `webseed` Vercel project (no `--prod`). Each deployment gets a unique permanent public URL
2. `capture_email_screenshot()` — 1280x600 above-the-fold screenshot for email via Python Playwright (non-fatal on failure)
3. The public deployment URL is saved in the DB and used in outreach emails

## Email Flow

1. Claude generates personalized Italian email (subject + body_html) per business
2. Email includes: greeting, compliment on reviews, site link, pricing (€299 + €9/mo), CTA, minimal legal footer
3. Gmail draft created with inline above-the-fold screenshot, labeled `webseed-queue`
4. User reviews drafts in Gmail and sends manually

## Search Behavior

- Maps search paginates through all available results (up to 60 per Google's limit)
- Synonym queries tried automatically (e.g. "ristorante" also searches "trattoria", "osteria", "pizzeria")
- Synonym map defined in `QUERY_VARIANTS` dict in `maps.py`
- Duplicate places deduplicated by `place_id` within run + across runs via DB

## Output

- `webseed.json` — TinyDB database with all business data and pipeline state
- `results/<business_name>/` — `index.html`, `vercel.json`, `img/` with downloaded photos
- `results/screenshots/` — smoke test screenshots + email preview screenshots

## Code Conventions

- Language: Python, snake_case functions, UPPERCASE constants
- Package uses absolute imports (`from webseed import maps`, `from webseed.maps import safe_name`)
- UI text and prompt templates are in Italian
- `BusinessData` dataclass (defined in `src/webseed/maps.py`) is the shared data model across modules
- `safe_name()` (public, in `src/webseed/maps.py`) is the shared slug function — used by generator.py, pipeline.py, and maps.py
- Photo download falls back to Unsplash when Maps photos are unavailable; `fallback_unsplash_url`, `photo_paths`, and `has_photos` are stored in DB
- All prompts are externalized in `src/webseed/prompts/` as `.txt` files — no hardcoded prompt text in Python code
- Prompts are loaded via `_load_prompt()` in pipeline.py and passed as parameters to modules
- Generated HTML strips markdown code fences that Claude may add
- Error handling: try/except per business in each step, failures logged but don't stop the batch
- Legacy Places API field names: use `photo` not `photos`, `type` not `types`
- **Identifier resolution**: most commands accept place_ids or partial business names (case-insensitive substring match via `store.resolve_identifier()`). Ambiguous matches prompt the user to be more specific

## Testing

The `test` step runs locally on generated HTML (no deployment needed):

1. **Code review** (default) — Claude Code CLI analyzes HTML source against QA checklist. Text-only, no browser.
2. **Playwright visual test** (with `--playwright`) — Claude Code CLI + Playwright MCP opens local file, takes screenshots, inspects DOM, checks console errors.

Both report issues as structured JSON with severity levels (critical/major/minor). If issues are found, Claude Code CLI fixes the HTML and retests (up to `--max-fix-iterations` cycles, default 3).

Email screenshots (1280x600 above-the-fold) are captured during `deploy` step via Python Playwright.

## Cost

- Generation: ~$0.07 per site (via Claude Code CLI)
- Visual test: ~$0.05-0.10 per test call (Sonnet via Claude Code CLI)
- Fix: ~$0.03-0.05 per fix call
- Worst case per business (with 3 test-fix cycles): ~$0.40-0.70
- With `--no-test`: ~$0.07 per site (generation only)
- Email: ~$0.03 per email (via Claude Code CLI)
