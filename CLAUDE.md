# webseed

REST API backend that finds Italian local businesses without websites on Google Maps, generates professional HTML sites with Claude AI, tests them locally, deploys to Vercel, creates personalized email drafts in Gmail for outreach, and tracks everything in PostgreSQL. Real-time progress via WebSocket.

> **Claude's role**: General-purpose helper for all things webseed — implementing features, fixing bugs, improving prompts, designing architecture, testing, product strategy, and anything else that evolves around webseed as a product and codebase.

## Tech Stack

- **Python ≥3.11** — `src/` layout package, venv at `.venv/`, managed via `pyproject.toml` (`.python-version` pins 3.14 for dev)
- **FastAPI** — REST API + WebSocket for real-time events
- **PostgreSQL** — business data, settings (prompts + config), event log. Via SQLAlchemy 2.0 (sync) + Alembic migrations
- **Google Maps Places API** (new v1) — business discovery + enrichment via `google-maps-places` SDK
- **Claude Code CLI** — site generation, visual testing, HTML fixes, and email generation (via `claude --print` subprocess)
- **Vercel CLI** — deployment (`npm i -g vercel`)
- **Playwright MCP** — visual testing via Claude Code CLI (browser navigation, screenshots, DOM inspection)
- **Playwright** (Python) — above-the-fold email screenshots only
- **Gmail API** — OAuth-based draft creation with label management

### Frontend (planned — all in `frontend/`, not yet implemented)
- **React 19 + Vite** — SPA, TypeScript strict mode
- **shadcn/ui** (Radix + Tailwind CSS) — copy-paste components, full ownership
- **Orval** — auto-generates TanStack Query hooks + Zod schemas from `openapi.json`
- **TanStack Query** — server state (caching, refetch, mutations)
- **Zustand** — client state (WebSocket connection, auth, active jobs)
- **React Flow (xyflow) + Framer Motion** — pipeline visualization with animated nodes/edges
- **react-hook-form + Zod** — forms with validation
- **Vitest + Testing Library** — unit tests
- **Playwright** — E2E tests

## Architecture

Three-layer clean architecture:

1. **Core** (business logic): `services.py` orchestrates pipeline steps. External services (Maps, Claude CLI, Vercel CLI, Gmail, Playwright) are concrete — no abstract ports for them.
2. **Persistence**: `PersistencePort` protocol → `PostgresStore` implementation. `FileStoragePort` protocol → `LocalFileStorage` implementation.
3. **Interface**: FastAPI REST API + WebSocket. Background tasks run sync service functions in thread pool.

Key decisions:
- **Core stays sync** — no async in business logic
- **Prompts in DB** — stored in `settings` table (key prefix `prompt.*`), editable via API
- **Config in DB** — business-tunable config in `settings` table (key prefix `config.*`). Secrets stay as env vars
- **Auth** = API key via `X-API-Key` header (env var `WEBSEED_API_KEY`)
- **Blacklist** consolidated into DB only (`status = 'opted_out'`)
- **UUID v4** primary keys on all tables. `place_id` remains as unique business identifier from Google

## Project Structure

```
webseed/                          (project root)
├── pyproject.toml                (project metadata, dependencies)
├── .python-version               (3.14 — dev version)
├── .env / .env.example
├── CLAUDE.md
├── alembic.ini                   (Alembic config)
├── docker-compose.yml            (Postgres 16 for local dev)
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py       (schema + seed prompts/config)
└── src/
    └── webseed/                  (Python package)
        ├── __init__.py
        ├── __main__.py           (uvicorn entrypoint)
        ├── models.py             (BusinessData, PipelineStatus, BusinessRecord, PipelineEvent)
        ├── ports.py              (PersistencePort, FileStoragePort, EventCallback)
        ├── services.py           (pipeline orchestration — all run_* functions)
        ├── storage.py            (LocalFileStorage + atomic_write)
        ├── maps.py               (Google Places search, enrich, scoring, safe_name)
        ├── generator.py          (Claude CLI HTML generation)
        ├── tester.py             (Claude CLI code review, visual test, fix, screenshot)
        ├── deployer.py           (Vercel CLI deployment)
        ├── emailer.py            (Claude CLI email gen + Gmail drafts)
        ├── claude_cli.py         (Claude subprocess wrapper)
        ├── db/
        │   ├── __init__.py
        │   ├── tables.py         (SQLAlchemy ORM models)
        │   └── store.py          (PostgresStore implements PersistencePort)
        └── api/
            ├── __init__.py
            ├── app.py            (FastAPI factory, lifespan, test page)
            ├── auth.py           (API key dependency)
            ├── ws.py             (WebSocket manager + sync-to-async bridge)
            ├── deps.py           (FastAPI dependencies)
            └── routers/
                ├── __init__.py
                ├── pipeline.py   (POST /pipeline/* endpoints)
                ├── businesses.py (Business CRUD + management)
                └── settings.py   (Prompts + config CRUD)
```

## Pipeline Flow

```
Search (Maps) → Enrich (Place Details + Photos) → Generate (Claude) → Test (Code Review + optional Playwright) → Deploy (Vercel) → Email (Claude+Gmail Draft)
```

Each step is independent and resumable. State is tracked per-business in PostgreSQL with status progression:
`searched` → `enriched` → `generated` → `tested` → `deployed` → `email_queued` → `emailed`

Running statuses: `running_enrich`, `running_generate`, `running_test`, `running_deploy`, `running_email` (set at step start, reset on crash recovery). Search runs synchronously — no `running_search` status.

Error statuses: `error_enrich`, `error_generate`, `error_test`, `error_deploy`, `error_email`, `error_run`. Special: `opted_out` (blacklisted).

## Module Map

| File | Role |
|------|------|
| `models.py` | `PipelineStatus` enum, `BusinessData` dataclass, `BusinessRecord` dataclass, `PipelineEvent` dataclass |
| `ports.py` | `PersistencePort` and `FileStoragePort` protocols, `EventCallback` type alias |
| `services.py` | All orchestration: `run_search`, `run_enrich`, `run_generate`, `run_test`, `run_deploy`, `run_email`, `run_pipeline` + management functions |
| `storage.py` | `LocalFileStorage` implementing `FileStoragePort`, `atomic_write()` |
| `maps.py` | Stage 1 search, Stage 2 enrichment, photo download, lead scoring, `safe_name()` |
| `generator.py` | Builds prompt from template + business data, calls Claude CLI, writes `index.html` via `FileStoragePort` |
| `tester.py` | Code review, visual test, HTML fix, email screenshot — all via `FileStoragePort` |
| `deployer.py` | Deploy to Vercel via `FileStoragePort`, URL extraction |
| `emailer.py` | Gmail OAuth, Claude CLI email generation, MIME draft creation |
| `claude_cli.py` | `run_claude_cli()` subprocess helper + JSON parser + timeout reader |
| `db/tables.py` | SQLAlchemy ORM: `BusinessRow`, `SettingRow`, `EventLogRow` |
| `db/store.py` | `PostgresStore` implementing `PersistencePort` |
| `api/app.py` | `create_app()` factory, lifespan (crash recovery), WebSocket endpoint |
| `api/auth.py` | `require_api_key` FastAPI dependency |
| `api/ws.py` | `WebSocketManager`, `make_event_callback()` sync-to-async bridge |
| `api/deps.py` | `get_store()`, `get_file_storage()` FastAPI dependencies |
| `api/routers/pipeline.py` | 7 POST endpoints, all BackgroundTasks |
| `api/routers/businesses.py` | Business CRUD + management + CSV export |
| `api/routers/settings.py` | Prompts + config CRUD |

## Running the Server

### Setup

```bash
pip install -e .                    # install dependencies
docker compose up -d                # start Postgres
alembic upgrade head                # run migrations (creates tables + seeds prompts/config)
```

### Start

```bash
python -m webseed                   # starts uvicorn on 0.0.0.0:8000
```

### Tests

```bash
pytest tests/                       # run all tests
pytest tests/test_api.py            # API route tests
pytest tests/test_services.py       # pipeline orchestration tests
pytest tests/test_store.py          # persistence layer tests
```


## REST API Endpoints

All require `X-API-Key` header except `WS /ws`.

### Pipeline (all return `{"job_id": "uuid"}` immediately, run in background)
- `POST /pipeline/search` — `{location, query, types, limit?, min_score?, grid_size?}`
- `POST /pipeline/enrich` — `{place_ids, only_media?}`
- `POST /pipeline/generate` — `{place_ids, model?}`
- `POST /pipeline/test` — `{place_ids, playwright?, max_fix_iterations?, model?}`
- `POST /pipeline/deploy` — `{place_ids}`
- `POST /pipeline/email` — `{place_ids, model?}`
- `POST /pipeline/run` — `{place_ids, model?, test_model?, max_fix_iterations?, no_email?, playwright?}`

### Businesses
- `GET /businesses` — list, filterable by `?status=`
- `GET /businesses/stats` — `{searched: 5, enriched: 3, ...}`
- `GET /businesses/{place_id}` — single detail
- `PATCH /businesses/{place_id}/status` — `{to: "searched"}`
- `DELETE /businesses/{place_id}` — remove from DB
- `POST /businesses/{place_id}/blacklist` — set opted_out
- `DELETE /businesses/{place_id}/blacklist` — remove from blacklist
- `POST /businesses/hard-delete` — `{place_ids, keep_blacklisted?}`
- `POST /businesses/close` — `{place_ids}`
- `GET /businesses/export/csv` — CSV download

### Settings (prompts + config unified)
- `GET /settings` — list all, filterable by `?prefix=prompt` or `?prefix=config`
- `GET /settings/{key}` — single
- `PUT /settings/{key}` — `{value, description?}`

### WebSocket
- `WS /ws` — real-time event stream, auth via `?api_key=`


## WebSocket Event Format

```json
{
  "event_type": "step_start|step_done|step_error|progress|cost|job_complete",
  "job_id": "uuid",
  "step": "search|enrich|generate|test|deploy|email",
  "place_id": "ChIJ...",
  "message": "Human-readable string",
  "data": {"lead_score": 72, "cost_usd": 0.07},
  "timestamp": "2026-03-15T10:30:00.000Z"
}
```

## Environment Variables

Defined in `.env` (copy from `.env.example`):

- `DATABASE_URL` — PostgreSQL connection string (default: `postgresql://webseed:webseed@localhost:5432/webseed`)
- `RESULTS_DIR` — output directory for generated sites (default: `results`)
- `PORT` — server port (default: `8000`)
- `WEBSEED_API_KEY` — **required** — API key for authenticating REST requests
- `GOOGLE_MAPS_API_KEY` — Google Cloud, **Places API (New)** enabled
- `CLAUDE_CLI_PATH` — (optional) path to Claude Code CLI binary; auto-detected if on PATH
- `VERCEL_CLI_PATH` — (optional) path to Vercel CLI binary; auto-detected if on PATH
- `GMAIL_CREDENTIALS_FILE` — path to Gmail OAuth credentials JSON (default: `credentials.json`)
- `GMAIL_TOKEN_FILE` — (optional) path to OAuth token file (default: `token.json`)
- `CLAUDE_TIMEOUT_GENERATE` — (optional) Claude CLI timeout in seconds for generation (default: `120`)
- `CLAUDE_TIMEOUT_TEST` — (optional) Claude CLI timeout in seconds for testing (default: `120`)
- `CLAUDE_TIMEOUT_EMAIL` — (optional) Claude CLI timeout in seconds for email gen (default: `180`)
- `VERCEL_PROJECT_NAME` — (optional) Vercel project name for deployments (default: `webseed`)

Config values like `contact_email`, `sender_name`, `default_model`, `gmail_label_name` etc. are stored in the DB `settings` table (key prefix `config.*`) and editable via API.

## Auth Notes

- **API**: Simple API key via `X-API-Key` header. Set `WEBSEED_API_KEY` env var.
- **Claude Code CLI**: Used for all AI steps. Handles its own auth — no API key needed
- **Gmail API**: OAuth2 desktop app flow. First run of email step opens browser for consent → saves `token.json`. Scopes: `gmail.compose`, `gmail.labels`, `gmail.modify`
- **Gmail setup**: GCP Console → Enable Gmail API → OAuth consent screen → Credentials → Desktop app → Download `credentials.json`

## Database

PostgreSQL with 3 tables:
- `businesses` — one row per business, all fields + status + metadata. UUID v4 PK, `place_id` unique index.
- `settings` — key-value store for prompts (`prompt.*`) and config (`config.*`). Seeded by initial migration.
- `event_log` — pipeline events for debugging/audit. UUID v4 PK, indexed by `job_id` and `timestamp`.

Crash recovery: on server startup, all `running_*` statuses are reset to corresponding `error_*` statuses.

## State Management

- **PostgreSQL**: business data, pipeline status, prompts, config, event log
- **Blacklist**: DB only — `status = 'opted_out'`
- **Deduplication**: cross-run by `place_id`. Existing businesses get info updated (rating, reviews) but skip regeneration
- **Error tracking**: status like `error_deploy` + `error_detail` field with message

## Code Conventions

### Backend
- Language: Python, snake_case functions, UPPERCASE constants
- Package uses absolute imports (`from webseed.models import BusinessData`)
- UI text and prompt templates are in Italian
- `BusinessData` dataclass (defined in `src/webseed/models.py`) is the shared data model across modules
- `safe_name()` (public, in `src/webseed/maps.py`) is the shared slug function
- Prompts stored in DB `settings` table, loaded via `store.get_setting("prompt.*")`
- Prompts use `.format()` with `{{double braces}}` for literal curly braces in templates. NEVER switch to `.replace()`
- Generated HTML strips markdown code fences that Claude may add
- Error handling: try/except per business in each step, failures logged but don't stop the batch
- **Pyright strict mode** enabled (`pyproject.toml`) — all code must pass strict type checking
- Legacy Places API field names: use `photo` not `photos`, `type` not `types`

### Frontend (planned)
- **All frontend code lives in `frontend/`** — backend (`src/`) and frontend are strictly separated in the monorepo. Never put frontend files outside `frontend/`
- TypeScript strict mode — all code must pass `tsc --noEmit`
- PascalCase files for components (`BusinessTable.tsx`), camelCase for utils/stores/hooks (`websocket.ts`, `useWebSocketEvents.ts`)
- No barrel exports — import directly from file, not via `index.ts` re-exports
- Pages are thin — compose feature components, minimal logic in page files
- Orval-generated files in `frontend/src/api/` — do not edit manually, regenerate with `npm run generate-api`
- `typescript-lsp` and `pyright-lsp` plugins enabled for type checking
- Use Context7 plugin to look up latest library docs (React, shadcn, Orval, TanStack Query, etc.) when needed

## Search Behavior

- **Stage 1 only (cheap)**: `search` discovers candidates via Nearby + Text Search on a grid. No Place Details calls — enrichment is a separate step
- **Pre-scoring**: candidates ranked by `_compute_pre_score()` using Stage 1 fields (rating, review count, business status, category tier). Max 60 points
- **Grid tiling**: grid_size 3 (default) divides the area into 9 cells with ~20% overlap for broader coverage
- Duplicate places deduplicated by `place_id` within run; known place_ids skipped

## Enrich Behavior

- **Place Details** ($0.025/call): fetches phone, photos, reviews, opening hours, editorial summary, price level, payment options
- **Photo download**: downloads up to 3 Google Maps photos to `results/<name>/img/`
- **Lead scoring**: full `_compute_lead_score()` (0-100) on 8 signals
- **Website double-check**: if Place Details reveals a website, business is flagged and skipped

## Output

- PostgreSQL database with all business data and pipeline state
- `results/<business_name>/` — `index.html`, `vercel.json`, `img/` with downloaded photos
- `results/screenshots/` — email preview screenshots

## Cost

- Search: ~$0 (Stage 1 only, included in basic Places API quota)
- Enrich: ~$0.025 per business (Place Details call) + negligible photo download
- Generation: ~$0.07 per site (via Claude Code CLI)
- Visual test: ~$0.05-0.10 per test call (Sonnet via Claude Code CLI)
- Fix: ~$0.03-0.05 per fix call
- Worst case per business (with 3 test-fix cycles): ~$0.43-0.73
- Email: ~$0.03 per email (via Claude Code CLI)
