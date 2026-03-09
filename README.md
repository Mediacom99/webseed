# webseed

**Automated lead-gen pipeline for local businesses without websites.**

webseed finds Italian local businesses on Google Maps that don't have a website, generates a professional HTML site for each one using Claude AI, deploys it to Vercel, and creates a personalized email draft in Gmail — ready for you to review and send.

```
Search (Maps) → Generate (Claude) → Test (QA) → Deploy (Vercel) → Email (Gmail Draft)
```

Every step is independent and resumable. Stop anywhere, pick up later. State is tracked per-business in a local database.

---

## How It Works

1. **Search** — Queries Google Maps for businesses of a given type (e.g. "ristorante") in a given location. Filters out businesses that already have a website. Downloads photos.

2. **Generate** — Sends business data (name, address, photos, reviews) to Claude AI, which generates a complete single-file HTML site with inline CSS/JS. Professional, responsive, Italian-language.

3. **Test** — Runs an automated code review via Claude against a QA checklist. Optionally runs a visual test with Playwright (screenshots, DOM inspection, console errors). If issues are found, Claude fixes the HTML and retests — up to 3 cycles.

4. **Deploy** — Deploys to Vercel (single `webseed` project, unique URL per business). Takes an above-the-fold screenshot for the outreach email.

5. **Email** — Claude generates a personalized Italian email for each business. Creates a Gmail draft with the screenshot embedded, labeled `webseed-queue` for easy batch review.

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated
- [Vercel CLI](https://vercel.com/docs/cli) installed and logged in (`npm i -g vercel`)
- [Google Maps API key](https://console.cloud.google.com/) with Places API (legacy) enabled

### Install

```bash
git clone https://github.com/Mediacom99/webseed.git
cd webseed
python -m venv .venv && source .venv/bin/activate
pip install -e .
playwright install chromium  # for visual testing & email screenshots
```

### Configure

```bash
cp .env.example .env
```

Edit `.env` with your API key:

```env
GOOGLE_MAPS_API_KEY=your_key_here
CONTACT_EMAIL=you@example.com
```

### Run

```bash
# Find 5 restaurants in Milan without a website
webseed search --location "Milano, Italy" --query "ristorante" --limit 5

# Generate sites (place_id or name required)
webseed generate PLACE_ID "nome attività"

# Test with code review + auto-fix
webseed test PLACE_ID

# Deploy to Vercel
webseed deploy PLACE_ID

# Create Gmail drafts
webseed email PLACE_ID
```

Or run the full pipeline for specific businesses:

```bash
webseed run "ristorante da mario" --model opus

# Full pipeline with best quality settings (opus models, verbose)
webseed run "ristorante da mario" --hard
```

---

## CLI Reference

### Pipeline Commands

| Command | Description |
|---------|-------------|
| `webseed search` | Find businesses on Google Maps |
| `webseed generate <id>...` | Generate HTML sites via Claude AI |
| `webseed test <id>...` | Code review + optional Playwright visual test |
| `webseed deploy <id>...` | Deploy to Vercel |
| `webseed email <id>...` | Generate emails and create Gmail drafts |
| `webseed run <id>...` | Full pipeline for specific businesses |

### Management Commands

| Command | Description |
|---------|-------------|
| `webseed status` | Show all businesses and their status |
| `webseed show <id>` | Full detail for one business |
| `webseed stats` | Summary counts per status |
| `webseed reset <id> --to <status>` | Reset a business to re-process it |
| `webseed blacklist-add <id>...` | Block businesses from processing |
| `webseed blacklist-remove <id>` | Unblock a business |
| `webseed blacklist-list` | Show all blocked businesses |
| `webseed db-delete <id>...` | Remove from DB (keeps files) |
| `webseed hard-delete <id>...` | Remove DB + files + Vercel deployment |
| `webseed export-csv` | Export database to CSV |

Most commands accept place IDs or partial business names (case-insensitive).

### Key Flags

| Flag | Applies to | Description |
|------|-----------|-------------|
| `--location` | search | City/area to search (required) |
| `--query` | search | Business type, e.g. "ristorante" (required) |
| `--limit` | search | Max businesses to find (default: 10) |
| `--model` | generate, email | Claude model to use |
| `--test-model` | test, run | Model for testing (default: sonnet) |
| `--playwright` | test | Enable visual testing with Playwright |
| `--max-fix-iterations` | test, run | Max fix-retest cycles (default: 3) |
| `--no-email` | run | Skip the email step |
| `--hard` | run | Deep run: opus models, 3 fix iterations, verbose |
| `--db` | all | Database file path (default: webseed.json) |
| `--results-dir` | all | Output directory (default: results/) |
| `-v` | all | Verbose/debug logging |

---

## Architecture

```
src/webseed/
├── pipeline.py        # CLI entry point, orchestrates all steps
├── maps.py            # Google Places search, photo download
├── generator.py       # Claude AI site generation
├── tester.py          # Code review, visual testing, auto-fix loop
├── deployer.py        # Vercel deployment
├── emailer.py         # Gmail draft creation via Claude + Gmail API
├── store.py           # TinyDB state management
├── claude_cli.py      # Claude Code CLI subprocess helper
└── prompts/           # All prompt templates (Italian)
    ├── site_gen.txt
    ├── site_gen_system.txt
    ├── code_review.txt
    ├── visual_test.txt
    ├── fix_html.txt
    └── email_gen.txt
```

### State Machine

Each business progresses through statuses:

```
searched → generated → tested → deployed → email_queued
```

Error states (`error_generate`, `error_deploy`, etc.) can be reset with `webseed reset`. Blacklisted businesses get `opted_out` status.

### Key Design Decisions

- **Claude Code CLI** is used for all AI operations (not the API directly) — handles its own auth, supports tool use and Playwright MCP
- **Single-file HTML** — each site is one `index.html` with inline CSS/JS for zero-config Vercel deploys. All sites deploy under a single `webseed` project, each with a unique public URL
- **TinyDB** — simple local JSON database, no server needed
- **Prompt templates** are externalized in `src/webseed/prompts/` — easy to iterate on without touching Python code
- **Synonym expansion** — searching "ristorante" also tries "trattoria", "osteria", "pizzeria" automatically

---

## Gmail Setup

The email step requires Gmail API OAuth credentials:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the **Gmail API**
3. Configure **OAuth consent screen** (External)
4. Create **Credentials** → OAuth client ID → Desktop app
5. Download the JSON and save as `credentials.json` in the project root
6. First run of `webseed email` opens a browser for OAuth consent → saves `token.json`

---

## Costs

| Step | Cost per business |
|------|-------------------|
| Generate | ~$0.07 |
| Test (code review) | ~$0.05 |
| Fix (per iteration) | ~$0.03-0.05 |
| Email | ~$0.03 |
| **Worst case (3 fix cycles)** | **~$0.40-0.70** |
| **Happy path (no fixes)** | **~$0.15** |

All costs are from Claude Code CLI usage. Google Maps API and Vercel have their own free tiers.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_MAPS_API_KEY` | Yes | Google Cloud, Places API (legacy) enabled |
| `CONTACT_EMAIL` | For email step | Shown in email footer for data requests |
| `GMAIL_CREDENTIALS_FILE` | For email step | Path to OAuth credentials JSON |
| `SENDER_NAME` | No | Sender name in emails |
| `CLAUDE_CLI_PATH` | No | Path to Claude CLI binary (auto-detected) |
| `VERCEL_CLI_PATH` | No | Path to Vercel CLI binary (auto-detected) |

---

## License

[MIT](LICENSE)
