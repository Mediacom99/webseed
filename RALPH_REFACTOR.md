# webseed Clean Architecture Refactoring

You are refactoring the webseed Python project from a CLI tool with TinyDB to a REST API with PostgreSQL. This is a large, phased refactoring. On each iteration, READ THE CODEBASE FIRST to understand what has already been done, then continue from where you left off.

## How to work

1. **First**: Run `git log --oneline -20` and check which files exist under `src/webseed/` to understand current state
2. **Then**: Determine which phase you're in (see phases below)
3. **Do**: Complete the current phase's tasks
4. **Verify**: Run the phase's checks (pyright, file existence, server start)
5. **Commit**: Commit your work immediately after completing each task or subtask. Use concise but descriptive messages like `"refactor: add models.py with BusinessData, PipelineStatus, BusinessRecord"` or `"refactor: implement PostgresStore with all PersistencePort methods"`. Commit FREQUENTLY — after every meaningful unit of work, not just at the end of a phase. This is critical because your git history is how you track progress across iterations.
6. **Continue**: Move to the next phase

IMPORTANT:
- Activate the venv before running any python/pyright commands: `source .venv/bin/activate`
- Run `pyright src/` after every phase. Fix ALL errors before moving on.
- Do NOT create or connect to a PostgreSQL database. The DB adapter code must be correct but untested against a real DB.
- Prompts use `.format()` with `{{double braces}}` for literal curly braces in templates. NEVER switch to `.replace()`.
- PRs from feature branches must target `develop`, never `main`.
- Keep all existing business logic intact (scoring, prompt building, output parsing, grid tiling, etc.). This is a STRUCTURAL refactor, not a logic rewrite.
- Use UUID v4 for all database primary keys.
- Use absolute imports: `from webseed.models import BusinessData`

## Current state (before refactoring)

The project is at `src/webseed/` with these files:
- `pipeline.py` (~1350 lines) — CLI entry + all subcommands + orchestration
- `store.py` — TinyDB persistence
- `maps.py` — Google Places API + `BusinessData` dataclass + lead scoring + `safe_name()`
- `generator.py` — Claude CLI HTML generation
- `tester.py` — Claude CLI code review + visual test + fix + screenshot
- `deployer.py` — Vercel CLI deployment
- `emailer.py` — Claude CLI email gen + Gmail drafts
- `claude_cli.py` — Claude subprocess wrapper
- `utils.py` — `atomic_write()` helper
- `prompts/` — 9 `.txt` prompt template files
- `__init__.py`, `__main__.py`

## Architecture decisions

These are final. Do not deviate.

1. **Three layers**: Core (business logic), Persistence (PostgreSQL), Interface (REST API + WebSocket)
2. **Core** = pipeline orchestration + domain models + all actual work. External services (Google Maps, Claude CLI, Vercel CLI, Gmail, Playwright) are CONCRETE in the core — no abstract ports for them.
3. **Persistence port** = abstract Protocol. Implementation: PostgreSQL via SQLAlchemy (sync) + Alembic migrations. TinyDB dropped entirely.
4. **File storage port** = abstract Protocol. Implementation: local filesystem. Later: S3.
5. **Interface** = FastAPI REST API + WebSocket. CLI dropped entirely.
6. **Prompts in DB** — stored in a `settings` table (key prefix `prompt.*`), editable via API. Seeded from current `.txt` files in initial migration.
7. **Config in DB** — business-tunable config in same `settings` table (key prefix `config.*`). Secrets (API keys) stay as env vars.
8. **Auth** = simple API key via `X-API-Key` header (env var `WEBSEED_API_KEY`).
9. **Progress/events** = callback `Callable[[PipelineEvent], None]` injected into core. REST layer forwards to WebSocket. Includes cost tracking per step.
10. **Background execution** = FastAPI BackgroundTasks. On crash, startup cleanup resets stale `running_*` statuses.
11. **Core stays sync** — no async in business logic. BackgroundTasks runs sync functions in thread pool.
12. **UUID v4** primary keys on all tables. `place_id` remains as unique business identifier from Google.
13. **Blacklist** consolidated into DB only — `blacklist.txt` dropped. Blacklist = `status = 'opted_out'`.
14. **No frontend** — backend only. Include a minimal WebSocket test page at `GET /` for debugging.

## Target directory structure

```
src/webseed/
  __init__.py
  __main__.py               # uvicorn entrypoint
  models.py                 # BusinessData, PipelineStatus, BusinessRecord, PipelineEvent
  ports.py                  # PersistencePort, FileStoragePort, EventCallback type
  maps.py                   # Google Places search, enrich, scoring, safe_name
  generator.py              # Claude CLI HTML generation
  tester.py                 # Claude CLI code review, visual test, fix, screenshot
  deployer.py               # Vercel CLI deployment
  emailer.py                # Claude CLI email gen + Gmail drafts
  claude_cli.py             # Claude subprocess wrapper
  services.py               # Pipeline orchestration (all run_* functions)
  db/
    __init__.py
    tables.py               # SQLAlchemy ORM models (BusinessRow, SettingRow, EventLogRow)
    store.py                # PostgresStore implements PersistencePort
  storage.py                # FileStoragePort Protocol + LocalFileStorage
  api/
    __init__.py
    app.py                  # FastAPI factory, lifespan, startup cleanup
    auth.py                 # API key dependency
    ws.py                   # WebSocket manager + sync-to-async bridge
    deps.py                 # FastAPI dependencies (get_store, get_storage)
    routers/
      __init__.py
      pipeline.py           # POST /pipeline/* endpoints
      businesses.py         # Business CRUD + management
      settings.py           # Prompts + config CRUD (unified)
```

Plus at project root:
```
alembic.ini
docker-compose.yml          # Postgres for local dev
migrations/
  env.py
  script.py.mako
  versions/
    0001_initial.py         # Schema + seed prompts/config
```

## Port interfaces

### PersistencePort (Protocol)

```python
from typing import Any, Protocol
from webseed.models import BusinessData, BusinessRecord, PipelineStatus

class PersistencePort(Protocol):
    # Business CRUD
    def upsert_business(self, biz: BusinessData, run_id: str) -> str: ...  # "inserted" | "updated"
    def find_by_place_id(self, place_id: str) -> BusinessRecord | None: ...
    def find_by_name(self, query: str) -> list[BusinessRecord]: ...
    def resolve_identifier(self, identifier: str) -> list[BusinessRecord]: ...
    def update_status(self, place_id: str, status: PipelineStatus, extra: dict[str, Any] | None = None) -> bool: ...
    def delete_business(self, place_id: str) -> bool: ...
    def all_place_ids(self) -> set[str]: ...
    def get_all_businesses(self, status: str | None = None) -> list[BusinessRecord]: ...
    # Blacklist
    def get_blacklisted_place_ids(self) -> set[str]: ...
    # Settings (prompts + config)
    def get_setting(self, key: str) -> str | None: ...
    def upsert_setting(self, key: str, value: str, description: str = "") -> None: ...
    def list_settings(self, prefix: str | None = None) -> list[dict[str, Any]]: ...
    def delete_setting(self, key: str) -> bool: ...
    # Crash recovery
    def reset_stale_running(self) -> int: ...
    # Event logging
    def log_event(self, job_id: str, place_id: str, event_type: str, step: str, message: str, data: dict[str, Any]) -> None: ...
```

### FileStoragePort (Protocol)

```python
class FileStoragePort(Protocol):
    def site_dir(self, name_slug: str) -> str: ...
    def photo_dir(self, name_slug: str) -> str: ...
    def screenshots_dir(self) -> str: ...
    def write_file(self, relative_path: str, content: str | bytes) -> str: ...  # returns abs path
    def read_file(self, relative_path: str) -> str: ...
    def exists(self, relative_path: str) -> bool: ...
    def list_files(self, relative_path: str, pattern: str = "*") -> list[str]: ...
    def delete_dir(self, relative_path: str) -> None: ...
```

### EventCallback

```python
from collections.abc import Callable
from webseed.models import PipelineEvent

EventCallback = Callable[[PipelineEvent], None]
```

## Database schema

Three tables, all with UUID v4 PKs:

```sql
CREATE TABLE businesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    place_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT DEFAULT '',
    phone VARCHAR(50),
    email VARCHAR(255) DEFAULT '',
    rating REAL DEFAULT 0,
    reviews INTEGER DEFAULT 0,
    category VARCHAR(100) DEFAULT '',
    maps_url TEXT DEFAULT '',
    has_photos BOOLEAN DEFAULT FALSE,
    photo_paths JSONB DEFAULT '[]',
    photo_refs JSONB DEFAULT '[]',
    fallback_unsplash_url TEXT DEFAULT '',
    lead_score INTEGER DEFAULT 0,
    price_level VARCHAR(50),
    business_status VARCHAR(50) DEFAULT 'OPERATIONAL',
    primary_type VARCHAR(100),
    types JSONB,
    has_opening_hours BOOLEAN DEFAULT FALSE,
    opening_hours_summary TEXT,
    accepts_credit_cards BOOLEAN,
    editorial_summary TEXT,
    review_texts JSONB,
    status VARCHAR(32) NOT NULL DEFAULT 'searched',
    error_detail TEXT DEFAULT '',
    vercel_url TEXT DEFAULT '',
    site_screenshot_path TEXT DEFAULT '',
    email_sent_at VARCHAR(50) DEFAULT '',
    test_iterations INTEGER DEFAULT 0,
    test_issues JSONB DEFAULT '[]',
    run_id VARCHAR(64) DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_businesses_status ON businesses(status);
CREATE INDEX idx_businesses_place_id ON businesses(place_id);

CREATE TABLE settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT DEFAULT '',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id VARCHAR(36) NOT NULL,
    place_id VARCHAR(100),
    event_type VARCHAR(32) NOT NULL,
    step VARCHAR(32),
    message TEXT DEFAULT '',
    data JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_event_log_job_id ON event_log(job_id);
CREATE INDEX idx_event_log_timestamp ON event_log(timestamp);
```

### Seed data for settings table

Prompts (read content from `src/webseed/prompts/*.txt` files BEFORE deleting them):
- `prompt.site_gen` — from `site_gen.txt`
- `prompt.site_gen_system` — from `site_gen_system.txt`
- `prompt.site_gen_photos` — from `site_gen_photos.txt`
- `prompt.site_gen_no_photos` — from `site_gen_no_photos.txt`
- `prompt.code_review` — from `code_review.txt`
- `prompt.code_review_system` — hardcoded Italian string currently in `tester.py:code_review()`
- `prompt.visual_test` — from `visual_test.txt`
- `prompt.visual_test_system` — hardcoded Italian string currently in `tester.py:visual_test()`
- `prompt.fix_html` — from `fix_html.txt`
- `prompt.fix_html_system` — hardcoded Italian string currently in `tester.py:fix_html()`
- `prompt.email_gen` — from `email_gen.txt`
- `prompt.email_gen_system` — from `email_gen_system.txt`

Config:
- `config.contact_email` — default `""`
- `config.sender_name` — default `"Edoardo di WebSeed"`
- `config.default_model` — default `"sonnet"`
- `config.test_model` — default `"sonnet"`
- `config.max_fix_iterations` — default `"3"`
- `config.gmail_label_name` — default `"webseed-queue"`
- `config.max_photos` — default `"3"`
- `config.timeout_generate` — default `"120"`
- `config.timeout_test` — default `"120"`
- `config.timeout_email` — default `"180"`

## REST API endpoints

All require `X-API-Key` header except `GET /` (test page) and `WS /ws`.

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

### Test page
- `GET /` — minimal HTML page with WebSocket connection for testing

## WebSocket event format

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

## Module mapping (current -> new)

- `pipeline.py` -> **SPLIT**: orchestration logic -> `services.py`, CLI -> deleted, `_doc_to_business_data` -> `db/store.py`, `_load_prompt` -> deleted (replaced by `store.get_setting()`)
- `store.py` -> **REWRITTEN**: `db/store.py` as `PostgresStore` class. Same method semantics, new implementation.
- `maps.py` -> **MOVED** to top level. `BusinessData` extracted to `models.py`. `print()` -> `on_event()`. `results_dir` -> `FileStoragePort`. `safe_name()` stays here.
- `generator.py` -> **MOVED**. `output_dir` -> `FileStoragePort`. Prompts passed as strings from `services.py`.
- `tester.py` -> **MOVED**. `site_dir` -> `FileStoragePort`. 3 hardcoded system prompts extracted to DB seeds.
- `deployer.py` -> **MOVED**. `site_dir` from `FileStoragePort.site_dir()`.
- `emailer.py` -> **MOVED**. `contact_email` and `sender_name` passed from `services.py` (which reads from DB config).
- `claude_cli.py` -> **MOVED** unchanged, optional `on_event` param added.
- `utils.py` -> **DELETED**. `atomic_write()` moves to `storage.py` as private function.
- `prompts/*.txt` -> **READ** content into migration seed, then directory deleted.
- `__main__.py` -> **REWRITTEN** as uvicorn entrypoint.

---

## BUILD PHASES

### Phase 1: Foundation (models, ports, dependencies)

**Tasks:**
1. Create `src/webseed/models.py` with `PipelineStatus` enum, `BusinessData` dataclass (moved from maps.py), `BusinessRecord` dataclass, `PipelineEvent` dataclass. Use UUID v4 for BusinessRecord.id.
2. Create `src/webseed/ports.py` with `PersistencePort` Protocol, `FileStoragePort` Protocol, `EventCallback` type alias.
3. Update `pyproject.toml`: add `fastapi`, `uvicorn[standard]`, `sqlalchemy>=2.0`, `psycopg2-binary`, `alembic` to dependencies. Remove `tinydb`. Remove CLI entry point (`webseed = "webseed.pipeline:main"`).
4. Create `src/webseed/db/__init__.py` (empty).
5. Create `src/webseed/api/__init__.py` (empty).
6. Create `src/webseed/api/routers/__init__.py` (empty).
7. Run `pip install -e .` to install new deps.

**Check:** `pyright src/webseed/models.py src/webseed/ports.py` passes with zero errors.

### Phase 2: Storage adapter

**Tasks:**
1. Create `src/webseed/storage.py` with `FileStoragePort` Protocol (imported from ports.py) and `LocalFileStorage` class implementing it. Move `atomic_write()` from `utils.py` into this file as `_atomic_write()` (private).
2. `LocalFileStorage.__init__(self, base_dir: str)` stores the absolute base path.
3. Implement all methods: `site_dir`, `photo_dir`, `screenshots_dir`, `write_file` (handles both str and bytes, uses atomic write for str), `read_file`, `exists`, `list_files` (glob pattern), `delete_dir` (shutil.rmtree).

**Check:** `pyright src/webseed/storage.py` passes.

### Phase 3: Database layer

**Tasks:**
1. Create `src/webseed/db/tables.py` with SQLAlchemy 2.0 ORM models: `BusinessRow`, `SettingRow`, `EventLogRow`. Use `Mapped[]` type annotations. UUID v4 PKs. `Base = DeclarativeBase`.
2. Create `src/webseed/db/store.py` with `PostgresStore` class implementing `PersistencePort`. Constructor takes `database_url: str`, creates `Engine` and `sessionmaker`. Each method creates its own session (for thread safety in background tasks).
3. Implement ALL `PersistencePort` methods. Key mappings:
   - `upsert_business()`: INSERT ON CONFLICT UPDATE on `place_id`
   - `find_by_place_id()`: query by `place_id` column (not `id`)
   - `find_by_name()`: case-insensitive ILIKE on `name`
   - `resolve_identifier()`: try exact `place_id` first, fall back to name search
   - `update_status()`: update status + extra fields + `updated_at`
   - `get_blacklisted_place_ids()`: `WHERE status = 'opted_out'`
   - `get_setting()` / `upsert_setting()` / `list_settings()` / `delete_setting()`: CRUD on `settings` table. `list_settings(prefix="prompt")` filters by `key LIKE 'prompt.%'`
   - `reset_stale_running()`: update all `running_*` statuses to corresponding `error_*`
   - `log_event()`: insert into `event_log`
4. Create `alembic.ini` at project root (template, `sqlalchemy.url` reads from env).
5. Create `migrations/env.py` that imports `Base` from `db.tables` and reads `DATABASE_URL` from env.
6. Create `migrations/script.py.mako` (standard Alembic template).
7. Create `migrations/versions/0001_initial.py`: creates all 3 tables + indexes. Seeds the `settings` table with all prompt and config values. **READ the current `.txt` prompt files to get their content for seeding.** Also seed the 3 hardcoded system prompts from `tester.py`.
8. Create `docker-compose.yml` with a Postgres 16 service (port 5432, db `webseed`, user `webseed`, password `webseed`).

**Check:** `pyright src/webseed/db/` passes.

### Phase 4: Core modules

Move and adapt the domain modules. Do each file one at a time.

**Tasks:**
1. **`maps.py`**: Remove `BusinessData` class definition (import from `models.py`). Remove all `print()` calls — replace with `on_event: EventCallback | None = None` parameter on `search()` and `enrich_business()`. When `on_event` is not None, call it with `PipelineEvent(...)` instead of printing. Replace `results_dir: str` param in `enrich_business()` with `file_storage: FileStoragePort`. Use `file_storage.photo_dir(safe_name(name))` for photo download directory. Keep all scoring, grid, retry logic unchanged.
2. **`claude_cli.py`**: Add optional `on_event: EventCallback | None = None` parameter to `run_claude_cli()`. Emit a `PipelineEvent` with type `"cost"` containing model name and prompt length. Otherwise unchanged.
3. **`generator.py`**: Import `BusinessData` from `models`. Replace `output_dir: str` with `file_storage: FileStoragePort`. Use `file_storage.write_file(f"{safe}/index.html", html)` and `file_storage.write_file(f"{safe}/vercel.json", ...)`. Keep prompt string parameters (services.py passes them in).
4. **`tester.py`**: Replace `site_dir: str` params with `file_storage: FileStoragePort` + `name_slug: str`. Read HTML via `file_storage.read_file(f"{name_slug}/index.html")`. Write fixed HTML via `file_storage.write_file(...)`. Write screenshots via `file_storage.write_file(...)`. Remove the 3 hardcoded system prompt strings — accept them as parameters instead. Keep `capture_email_screenshot()` using Playwright directly but write output via `file_storage`.
5. **`deployer.py`**: Accept `file_storage: FileStoragePort` + `name_slug: str`. Get `site_dir` path via `file_storage.site_dir(name_slug)`. Read/write `vercel.json` via `file_storage`. Otherwise unchanged.
6. **`emailer.py`**: Import `BusinessData` from `models`. Accept `contact_email` and `sender_name` as explicit params (no more `os.getenv` for these). Accept prompt strings as params. Otherwise unchanged.
7. **Delete `utils.py`** (atomic_write already moved to storage.py).

**Check:** `pyright src/webseed/models.py src/webseed/ports.py src/webseed/maps.py src/webseed/generator.py src/webseed/tester.py src/webseed/deployer.py src/webseed/emailer.py src/webseed/claude_cli.py src/webseed/storage.py` all pass.

### Phase 5: Services layer

**Tasks:**
1. Create `src/webseed/services.py`. This is the biggest new file. Extract ALL orchestration logic from `pipeline.py`'s `cmd_*` functions into pure service functions. No printing, no argparse, no CLI concepts.
2. Each service function takes `store: PersistencePort`, `file_storage: FileStoragePort`, `on_event: EventCallback | None = None`, plus step-specific params.
3. Service functions load prompts via `store.get_setting("prompt.site_gen")` etc. Raise `RuntimeError` if a required prompt is missing.
4. Service functions load config via `store.get_setting("config.default_model")` etc., with sensible fallbacks.
5. Implement these functions:
   - `run_search(query, location, limit, types, min_score, grid_size, store, api_key, on_event) -> dict`
   - `run_enrich(place_ids, store, file_storage, api_key, only_media, on_event) -> dict`
   - `run_generate(place_ids, store, file_storage, model, on_event) -> dict`
   - `run_test(place_ids, store, file_storage, playwright, max_fix_iterations, model, on_event) -> dict`
   - `run_deploy(place_ids, store, file_storage, on_event) -> dict`
   - `run_email(place_ids, store, file_storage, model, on_event) -> dict`
   - `run_pipeline(place_ids, store, file_storage, model, test_model, max_fix_iterations, no_email, playwright, on_event) -> dict`
   - Management: `get_business`, `list_businesses`, `get_stats`, `reset_status`, `blacklist_add`, `blacklist_remove`, `hard_delete`, `close_businesses`, `export_csv`
6. The `run_pipeline` function must replicate the status-gated step execution from `cmd_run()` — check current status, run only the steps needed, handle errors per-business, set `running_*` status at step start, set final status at step end.

**Check:** `pyright src/webseed/services.py` passes.

### Phase 6: API layer

**Tasks:**
1. Create `src/webseed/api/auth.py`: a FastAPI `Security` dependency that reads `X-API-Key` header, compares to `WEBSEED_API_KEY` env var, raises 401 on mismatch. Skip auth for `GET /` and WebSocket (WS uses query param `?api_key=`).
2. Create `src/webseed/api/ws.py`: `WebSocketManager` class with `connect()`, `disconnect()`, `broadcast(event: PipelineEvent)` async methods. Module-level `manager` singleton. `make_event_callback(loop: asyncio.AbstractEventLoop) -> EventCallback` function that bridges sync callback to async broadcast via `asyncio.run_coroutine_threadsafe`. The callback should also call `store.log_event()` to persist events.
3. Create `src/webseed/api/deps.py`: FastAPI dependencies `get_store() -> PersistencePort` and `get_file_storage() -> FileStoragePort` that read from `request.app.state`.
4. Create `src/webseed/api/routers/pipeline.py`: All 7 POST endpoints. Each validates input (Pydantic models), creates a job_id (uuid4), adds a BackgroundTask that calls the corresponding service function with the event callback, and returns `{"job_id": str}` immediately.
5. Create `src/webseed/api/routers/businesses.py`: All business CRUD + management endpoints. These are synchronous (fast DB operations, no background tasks needed).
6. Create `src/webseed/api/routers/settings.py`: GET/PUT for prompts and config. Filterable by prefix.
7. Create `src/webseed/api/app.py`: `create_app(database_url: str, results_dir: str) -> FastAPI` factory. Creates `PostgresStore`, `LocalFileStorage`, attaches to `app.state`. Lifespan hook calls `store.reset_stale_running()` on startup. Includes all routers. Adds WebSocket endpoint at `/ws`. Adds a `GET /` that serves a minimal HTML test page.
8. The minimal test page at `GET /` should be a single HTML page (returned inline, no template file) with:
   - A WebSocket connection to `/ws`
   - Display of incoming events as they arrive (styled cards/log entries)
   - A simple form to trigger pipeline endpoints (POST to `/pipeline/run` etc.)
   - Basic dark theme, clean layout
   - Show connection status (connected/disconnected)
   - Job ID display when a pipeline is triggered
   - Auto-scroll event log
   Make it actually useful for testing — not just a blank page.
9. Update `src/webseed/__main__.py`: import `create_app`, read `DATABASE_URL` and `RESULTS_DIR` from env, call `create_app()`, run `uvicorn.run(app, host="0.0.0.0", port=8000)`.

**Check:** `pyright src/webseed/api/` passes. Running `python -m webseed` starts the server without errors (it will fail to connect to DB but should not crash on import).

### Phase 7: Cleanup and final wiring

**Tasks:**
1. Delete `src/webseed/pipeline.py`
2. Delete `src/webseed/store.py` (old TinyDB store)
3. Delete `src/webseed/utils.py`
4. Delete `src/webseed/prompts/` directory (content already in migration seed)
5. Update `src/webseed/__init__.py` — keep `__version__` only
6. Make sure ALL imports across ALL files are correct and nothing references deleted modules.
7. Run `pyright src/` on the ENTIRE source tree. Fix ALL errors.
8. Verify the server starts: `python -c "from webseed.api.app import create_app; print('OK')"` should print OK.
9. Update `CLAUDE.md` to reflect the new architecture (REST API, PostgreSQL, no CLI, new directory structure, new endpoints, docker-compose setup).
10. Commit all changes.

**Check:** `pyright src/` passes with ZERO errors. `python -c "from webseed.api.app import create_app; print('OK')"` prints OK.

---

## Final completion criteria

ALL of these must be true:

1. All files in the target directory structure exist
2. `pyright src/` passes with zero errors
3. `python -c "from webseed.api.app import create_app; print('OK')"` succeeds
4. `pipeline.py`, `store.py` (old), `utils.py`, and `prompts/` directory are deleted
5. `tinydb` is not in `pyproject.toml` dependencies
6. No file under `src/webseed/` imports from `webseed.pipeline`, `webseed.store` (old), or `webseed.utils`
7. `alembic.ini`, `docker-compose.yml`, and `migrations/versions/0001_initial.py` exist
8. The migration file contains seed data for all 12 prompts and 10 config values
9. `CLAUDE.md` has been updated to reflect the new architecture
10. All work is committed to git

When ALL criteria above are met, output: <promise>REFACTORING COMPLETE</promise>
