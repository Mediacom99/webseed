# webseed

Automated CLI pipeline that finds Italian local businesses without websites on Google Maps, generates professional HTML sites with Claude AI, deploys them to Vercel, and exports data to CSV for sales outreach.

## Tech Stack

- **Python 3.9+** — all source files are in the project root, venv at `.venv/`
- **Google Maps Places API** (legacy) — business discovery via `googlemaps` library
- **Anthropic Claude API** (claude-opus-4-5) — HTML site generation
- **Vercel CLI** — deployment (`npm i -g vercel`), optional with `--no-deploy`
- **Playwright** — optional headless browser smoke tests

## Pipeline Flow

```
Search (Maps) → Generate (Claude) → Deploy (Vercel, optional) → Test (Playwright, optional) → Export (CSV)
```

## Module Map

| File | Role |
|------|------|
| `pipeline.py` | CLI entry point and orchestrator. Parses args, loads env, coordinates all modules, writes CSV |
| `maps.py` | Searches Google Places for businesses without websites, downloads photos. Paginates and tries synonym queries to maximize results. Returns list of `BusinessData` dataclasses |
| `generator.py` | Builds prompt from template + business data, calls Claude, writes single-file `index.html` with inline CSS/JS. Supports both standard API keys and OAuth tokens (`sk-ant-oat`) |
| `deployer.py` | Wraps `vercel --prod` CLI, extracts deployed URL from stdout |
| `tester.py` | Playwright smoke test — loads page, checks title/body, captures screenshot |
| `prompts/site_gen.txt` | Italian-language prompt template for Claude with `{placeholders}` for business data |

## Environment Variables

Defined in `.env` (copy from `.env.example`):

- `GOOGLE_MAPS_API_KEY` — Google Cloud, **legacy Places API** enabled
- `ANTHROPIC_API_KEY` — Anthropic Console (`sk-ant-api...`) or Claude MAX subscription token (`sk-ant-oat...` via `claude setup-token`)
- `VERCEL_TOKEN` — Vercel account tokens (not required with `--no-deploy`)

## Auth Notes

- Standard API keys (`sk-ant-api...`) use the `anthropic` Python SDK directly
- OAuth tokens (`sk-ant-oat...` from `claude setup-token` / MAX subscription) require raw HTTP with `Authorization: Bearer` header and `anthropic-beta: oauth-2025-04-20` header — the Python SDK does not support OAuth tokens natively

## Running

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in API keys
python pipeline.py --location "Milano, Italy" --query "ristorante" --limit 5 --no-deploy
```

Optional smoke test: `playwright install chromium`, then add `--test` flag.

### CLI Flags

- `--location` (required) — city/area to search
- `--query` (required) — business type (e.g. "ristorante", "parrucchiere")
- `--limit` — max businesses to process (default: 10)
- `--output` — CSV output path (default: `results.csv`)
- `--results-dir` — output directory (default: `results/`)
- `--no-deploy` — generate sites locally without deploying to Vercel
- `--test` — run Playwright smoke test after deploy

## Search Behavior

- Maps search paginates through all available results (up to 60 per Google's limit)
- When the primary query doesn't find enough businesses without websites, synonym queries are tried automatically (e.g. "ristorante" also searches "trattoria", "osteria", "pizzeria", "tavola calda")
- Synonym map defined in `QUERY_VARIANTS` dict in `maps.py`
- Duplicate places are deduplicated by `place_id`

## Output

- `results.csv` — one row per business (name, address, phone, rating, reviews, category, Vercel URL or file:// path, Maps URL, timestamp)
- `results/<business_name>/` — `index.html`, `vercel.json`, `img/` with downloaded photos

## Code Conventions

- Language: Python, snake_case functions, UPPERCASE constants
- UI text and prompt template are in Italian
- Modules are imported lazily inside `main()` in pipeline.py
- `BusinessData` dataclass (defined in maps.py) is the shared data model across modules
- Photo download falls back to Unsplash when Maps photos are unavailable
- Generated HTML strips markdown code fences that Claude may add
- Error handling: try/except per business in the pipeline loop, failures are logged but don't stop the batch
- Legacy Places API field names: use `photo` not `photos`, `type` not `types`

## Testing

No unit test suite. Testing is done via the `--test` flag which runs Playwright smoke tests against deployed sites (30s timeout, networkidle wait, full-page screenshots saved to `results/screenshots/`).

## Cost

~$0.07 per site generated via Claude.
