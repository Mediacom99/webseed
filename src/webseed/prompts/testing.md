# webseed — Testing & Bug Fixing Guide

Follow this guide top-to-bottom. Each section builds on the previous one. Use TDD: write the failing test first, then fix the bug.

---

## 1. Test Infrastructure Setup

### 1.1 Add test dependencies to `pyproject.toml`

Add after the `dependencies` list:

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-mock>=3.12",
    "responses>=0.24",
    "pytest-cov>=4.1",
]
```

Install: `pip install -e ".[test]"`

### 1.2 Create test directory and shared fixtures

Create `tests/conftest.py`:

```python
"""Shared fixtures for webseed tests."""

import os
import pytest
from tinydb import TinyDB
from webseed.maps import BusinessData


@pytest.fixture
def tmp_db(tmp_path):
    """Isolated TinyDB instance in a temp directory."""
    db_path = str(tmp_path / "test.json")
    db = TinyDB(db_path, indent=2)
    yield db
    db.close()


@pytest.fixture
def sample_business():
    """Realistic BusinessData instance with Italian data."""
    return BusinessData(
        name="Ristorante Da Mario",
        place_id="ChIJ_test_place_id_123",
        address="Via Roma 42, 20121 Milano MI, Italia",
        phone="+39 02 1234567",
        rating=4.5,
        reviews=127,
        category="restaurant",
        maps_url="https://maps.google.com/?cid=123456789",
        has_photos=True,
        photo_paths=["img/photo1.jpg", "img/photo2.jpg"],
        fallback_unsplash_url="https://source.unsplash.com/1200x600/?italian-restaurant",
    )


@pytest.fixture
def sample_business_no_photos():
    """BusinessData with no photos (Unsplash fallback)."""
    return BusinessData(
        name="Barbiere Luigi",
        place_id="ChIJ_test_barber_456",
        address="Corso Vittorio Emanuele 15, 20122 Milano MI, Italia",
        phone=None,
        rating=3.8,
        reviews=23,
        category="hair_care",
        maps_url="https://maps.google.com/?cid=987654321",
        has_photos=False,
        photo_paths=[],
        fallback_unsplash_url="https://source.unsplash.com/1200x600/?hair-salon",
    )


@pytest.fixture
def mock_env(monkeypatch):
    """Set required environment variables for tests."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-api-test-key-000")
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "AIza-test-key")
    monkeypatch.setenv("VERCEL_TOKEN", "test-vercel-token")
    monkeypatch.setenv("CONTACT_EMAIL", "test@example.com")
    # Clear optional params to avoid leaking from real env
    monkeypatch.delenv("CLAUDE_TEMPERATURE", raising=False)
    monkeypatch.delenv("CLAUDE_TOP_P", raising=False)
    monkeypatch.delenv("CLAUDE_TOP_K", raising=False)


@pytest.fixture
def sample_db_doc():
    """Dict matching the DB schema produced by store.upsert_business."""
    return {
        "place_id": "ChIJ_test_place_id_123",
        "name": "Ristorante Da Mario",
        "address": "Via Roma 42, 20121 Milano MI, Italia",
        "phone": "+39 02 1234567",
        "email": "",
        "rating": 4.5,
        "reviews": 127,
        "category": "restaurant",
        "maps_url": "https://maps.google.com/?cid=123456789",
        "has_photos": True,
        "photo_paths": ["img/photo1.jpg", "img/photo2.jpg"],
        "fallback_unsplash_url": "https://source.unsplash.com/1200x600/?italian-restaurant",
        "status": "searched",
        "error_detail": "",
        "vercel_preview_url": "",
        "vercel_prod_url": "",
        "site_screenshot_path": "",
        "email_sent_at": "",
        "run_id": "test_run_001",
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }
```

### 1.3 Test file layout

```
tests/
├── conftest.py
├── test_store.py
├── test_maps.py
├── test_config.py
├── test_generator.py
├── test_deployer.py
├── test_tester.py
├── test_emailer.py
└── test_pipeline.py
```

---

## 2. Unit Tests + Bug Fixes per Module

Work through modules in dependency order (leaf modules first).

---

### 2A. `test_store.py` — targets `src/webseed/store.py`

No bugs to fix. Tests establish baseline coverage for the data layer.

```
test_open_db_creates_file        — verify TinyDB file created at specified path
test_upsert_business_insert      — insert new business, verify all fields stored, returns "inserted"
test_upsert_business_update      — insert then upsert same place_id, verify mutable fields updated but status preserved, returns "updated"
test_find_by_place_id_found      — insert, find by place_id, verify match
test_find_by_place_id_not_found  — empty DB, find returns None
test_update_status               — update status, verify new status + updated_at changed
test_update_status_with_extra    — pass extra dict, verify fields merged into document
test_blacklist_roundtrip         — add_to_blacklist → load_blacklist → verify; remove → verify gone
test_get_full_blacklist_merges   — DB opted_out + file blacklist both included in result
```

**Note:** TinyDB is inherently single-process. Document that concurrent `webseed` invocations risk data corruption. Consider adding a file lock (`fcntl.flock`) in `open_db()` if concurrent use becomes a real scenario.

---

### 2B. `test_maps.py` — targets `src/webseed/maps.py`

#### Tests

```
test_safe_name_basic             — "Ristorante Da Mario" → "ristorante_da_mario"
test_safe_name_truncation        — 40-char name truncated to 30 chars
test_safe_name_collision         — two names that collide after truncation (document the risk)
test_safe_name_accented_chars    — "Caffè dell'Arte" preserves accented chars (verify filesystem safety)
test_download_photos_success     — mock requests.get returning 200, verify file written and path returned
test_download_photos_missing_ref — photo dict without "photo_reference" key → currently crashes with KeyError
test_download_photos_network_err — mock requests.get raising RequestException → verify graceful continue
test_fetch_all_pages_pagination  — mock gmaps.places with next_page_token on first call, none on second
test_fetch_all_pages_no_results  — mock gmaps.places returning empty results list
test_search_skips_with_website   — place details include "website" field → skipped
test_search_uses_query_variants  — query "ristorante" also searches "trattoria", "osteria", "pizzeria"
```

#### Bug fix #1: `photo["photo_reference"]` KeyError

**File:** `src/webseed/maps.py:55`

**Before:**
```python
ref = photo["photo_reference"]
```

**After:**
```python
ref = photo.get("photo_reference")
if not ref:
    continue
```

**Why:** Google Places API occasionally returns photo objects without `photo_reference`. The current code crashes with `KeyError`.

#### Bug fix #2: `safe_name()` collision risk

**File:** `src/webseed/maps.py:44`

The 30-char truncation creates collision risk (e.g. two businesses starting with the same 30 characters overwrite each other's `results/` directory). Options:
- Increase limit to 50 chars
- Append a short hash: `name[:30] + "_" + hashlib.md5(name.encode()).hexdigest()[:6]`
- At minimum, document the risk in a comment

Recommended minimal fix — add comment and increase to 50:
```python
def safe_name(name: str) -> str:
    # Used for results/ directory names. Keep in sync with deployer.project_name().
    return name.lower().replace(" ", "_").replace("/", "_")[:50]
```

---

### 2C. `test_config.py` — targets `src/webseed/config.py`

#### Tests

```
test_call_claude_standard_key    — mock anthropic.Anthropic client, verify model/max_tokens/messages, verify text extraction
test_call_claude_oauth_token     — mock httpx.post, verify Bearer auth + anthropic-beta header, verify text extraction
test_call_claude_oauth_empty     — mock httpx.post returning {"content": []} → should raise clear error, not IndexError
test_call_claude_oauth_http_err  — mock httpx.post returning 429/500 → verify httpx.HTTPStatusError raised
test_call_claude_missing_key     — unset ANTHROPIC_API_KEY → verify KeyError
test_call_claude_optional_params — set CLAUDE_TEMPERATURE env var → verify temperature passed to API
```

#### Bug fix #3: OAuth response bounds check

**File:** `src/webseed/config.py:54`

**Before:**
```python
resp.raise_for_status()
return resp.json()["content"][0]["text"]
```

**After:**
```python
resp.raise_for_status()
data = resp.json()
content = data.get("content", [])
if not content or "text" not in content[0]:
    raise ValueError(
        f"Unexpected API response structure: {str(data)[:200]}"
    )
return content[0]["text"]
```

**Why:** If the API returns an unexpected response shape (empty content array, missing text field), this crashes with `IndexError` or `KeyError` — an inscrutable error. The fix gives a clear error message.

---

### 2D. `test_generator.py` — targets `src/webseed/generator.py`

#### Tests

```
test_strip_code_fences_html      — "```html\n<html>...</html>\n```" → stripped
test_strip_code_fences_no_fence  — "<html>...</html>" → unchanged
test_strip_code_fences_backtick  — "```\n...\n```" (no language tag) → stripped
test_strip_code_fences_uppercase — "```HTML\n...\n```" → currently NOT stripped (bug)
test_build_prompt_with_photos    — verify template populated with photo paths and Maps instructions
test_build_prompt_without_photos — verify Unsplash fallback URL used in prompt
test_generate_writes_html        — mock call_claude, verify index.html written to correct directory
test_generate_writes_vercel_json — verify vercel.json created with {"version": 2}
test_generate_strips_fences      — mock call_claude returning fenced HTML, verify fences stripped in output file
```

#### Bug fix #4: Code fence regex case insensitive

**File:** `src/webseed/generator.py:45`

**Before:**
```python
html = re.sub(r"^```html?\n?", "", html.strip())
html = re.sub(r"\n?```$", "", html.strip())
```

**After:**
```python
html = re.sub(r"^```html?\n?", "", html.strip(), flags=re.IGNORECASE)
html = re.sub(r"\n?```$", "", html.strip())
```

**Why:** Claude sometimes outputs `` ```HTML `` (uppercase). The current regex only matches lowercase.

#### Bug fix #5: Minimal HTML validation

**File:** `src/webseed/generator.py:66-70`

**After** the `_strip_code_fences` call on line 66, add validation:

```python
html = _strip_code_fences(raw_text)

# Validate that Claude returned actual HTML
if not html.lstrip().lower().startswith(("<!doctype", "<html")):
    raise ValueError(f"Claude did not return valid HTML. Response starts with: {html[:100]}")
if len(html) < 500:
    raise ValueError(f"Generated HTML suspiciously short ({len(html)} chars). Likely truncated or error response.")
```

**Why:** Without validation, a Claude error message or truncated response gets silently written as `index.html` and deployed.

---

### 2E. `test_deployer.py` — targets `src/webseed/deployer.py`

#### Tests

```
test_project_name_basic          — "Ristorante Da Mario" → "webseed-ristorante-da-mario"
test_project_name_special_chars  — accented/special chars removed by regex
test_project_name_truncation     — long name truncated at 40 chars
test_extract_url_standard        — multi-line output with "https://..." on a line → extracted
test_extract_url_no_https        — output with no https line → falls back to last line
test_extract_url_empty           — empty string → should handle gracefully
test_deploy_preview_success      — mock subprocess returning 0 + URL → verify URL returned
test_deploy_preview_failure      — mock subprocess returning non-zero → verify RuntimeError
test_promote_success             — mock first subprocess (promote) succeeding → URL returned
test_promote_fallback            — mock promote failing, fallback --prod succeeding → URL returned
test_promote_both_fail           — both fail → RuntimeError with stderr
```

#### Bug fix #6: URL extraction validation

**File:** `src/webseed/deployer.py:16-23`

**Before:**
```python
def _extract_url(stdout: str) -> str:
    lines = stdout.strip().split("\n")
    url = next(
        (line.strip() for line in reversed(lines) if line.strip().startswith("https://")),
        lines[-1].strip(),
    )
    return url
```

**After:**
```python
def _extract_url(stdout: str) -> str:
    lines = stdout.strip().split("\n")
    url = next(
        (line.strip() for line in reversed(lines) if line.strip().startswith("https://")),
        None,
    )
    if url is None:
        raise RuntimeError(
            f"Could not extract deployment URL from Vercel output:\n{stdout[:500]}"
        )
    return url
```

**Why:** The fallback to `lines[-1].strip()` can return an error message or garbage string as the "URL", causing silent failures downstream. Better to fail fast with a clear error.

**Note on safe_name vs project_name:** `safe_name()` (maps.py:44) produces underscored slugs truncated at 30 chars for directory names. `project_name()` (deployer.py:9-13) produces hyphenated slugs truncated at 40 chars for Vercel projects. These serve different purposes and the difference is intentional. The collision risk is higher in `safe_name()` due to the shorter limit — addressed in bug fix #2.

---

### 2F. `test_tester.py` — targets `src/webseed/tester.py`

All tests require mocking Playwright. Create a minimal mock structure:

```python
@pytest.fixture
def mock_playwright(mocker):
    """Mock sync_playwright context manager."""
    mock_page = mocker.MagicMock()
    mock_page.title.return_value = "Ristorante Da Mario"
    mock_page.locator.return_value.inner_text.return_value = "Welcome"

    mock_browser = mocker.MagicMock()
    mock_browser.new_page.return_value = mock_page

    mock_pw = mocker.MagicMock()
    mock_pw.__enter__ = mocker.MagicMock(return_value=mock_pw)
    mock_pw.__exit__ = mocker.MagicMock(return_value=False)
    mock_pw.chromium.launch.return_value = mock_browser

    mocker.patch("webseed.tester.sync_playwright", return_value=mock_pw)
    return mock_page, mock_browser
```

#### Tests

```
test_smoke_test_success          — mock page load, verify return dict with ok=True, title, has_content, screenshot path
test_smoke_test_timeout          — mock page.goto raising TimeoutError → verify ok=False with error message
test_capture_screenshot_success  — verify screenshot path returned
test_capture_screenshot_failure  — mock exception → verify returns "" (non-fatal)
```

#### Bug fix #7: Narrow exception catching

**File:** `src/webseed/tester.py:30` and `tester.py:56`

**Before:**
```python
except Exception as e:
```

**After:**
```python
from playwright.sync_api import Error as PlaywrightError

# In capture_email_screenshot (line 30):
except (PlaywrightError, TimeoutError, OSError) as e:

# In smoke_test (line 56):
except (PlaywrightError, TimeoutError) as e:
```

**Why:** Bare `except Exception` catches `KeyboardInterrupt` and `SystemExit`, making it impossible to Ctrl+C out of a hanging test. Narrowing to expected failure modes lets unexpected errors propagate.

---

### 2G. `test_emailer.py` — targets `src/webseed/emailer.py`

#### Tests

```
test_generate_email_valid_json    — mock call_claude returning '{"subject": "...", "body_html": "..."}' → verify dict
test_generate_email_code_fence    — response wrapped in ```json ... ``` → verify extraction works
test_generate_email_missing_subj  — JSON has body_html but no subject → should raise ValueError (bug)
test_generate_email_missing_body  — JSON has subject but no body_html → should raise ValueError (bug)
test_generate_email_extra_keys    — JSON has unexpected extra keys → should still work
test_generate_email_invalid_json  — non-JSON response → verify ValueError raised
test_create_draft_with_screenshot — mock Gmail service, verify MIME structure has inline image with Content-ID
test_create_draft_no_screenshot   — verify email created without image attachment
test_create_draft_no_to_email     — empty to_email → verify draft created without To header
test_ensure_label_existing        — mock labels().list returning matching label → verify no create call
test_ensure_label_new             — mock labels().list without match → verify create called
```

#### Bug fix #8: JSON schema validation

**File:** `src/webseed/emailer.py:91`

**Before:**
```python
try:
    return json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(...) from e
```

**After:**
```python
try:
    data = json.loads(text)
except json.JSONDecodeError as e:
    raise ValueError(
        f"JSON parsing fallito: {e}\nRaw response:\n{raw_text[:500]}"
    ) from e

# Validate required fields
for field in ("subject", "body_html"):
    if field not in data or not isinstance(data[field], str) or not data[field].strip():
        raise ValueError(
            f"Campo obbligatorio mancante o vuoto: '{field}'\nParsed JSON: {data}"
        )
return data
```

**Why:** Without schema validation, a JSON response missing `subject` or `body_html` passes silently here but crashes later in `create_draft()` at `email_data["subject"]` (pipeline.py:283) with an unhelpful `KeyError`.

---

## 3. Integration Tests — `test_pipeline.py`

These test multi-module flows with mocked external services. Use `monkeypatch` and `mocker` to intercept API calls.

#### Tests

```
test_cmd_search_end_to_end
    — Mock googlemaps.Client + requests.get
    — Call cmd_search with argparse namespace
    — Verify businesses inserted into DB with status "searched"
    — Verify blacklisted place_ids skipped

test_cmd_generate_end_to_end
    — Pre-populate tmp_db with "searched" businesses
    — Mock call_claude returning valid HTML
    — Call cmd_generate
    — Verify index.html written to results dir
    — Verify DB status updated to "generated"

test_cmd_deploy_status_progression
    — Pre-populate tmp_db with "generated" businesses
    — Mock subprocess.run (Vercel CLI), sync_playwright
    — Call cmd_deploy
    — Verify status progression: generated → preview_deployed → tested → deployed
    — Verify NOT "tested" twice (bug fix #9)

test_cmd_email_end_to_end
    — Pre-populate tmp_db with "deployed" businesses + vercel_prod_url
    — Mock call_claude returning valid JSON, Gmail service
    — Call cmd_email
    — Verify draft created and status → "email_queued"

test_blacklist_respected_in_generate
    — Pre-populate tmp_db with "searched" business that is also in blacklist
    — Call cmd_generate
    — Verify business skipped (requires bug fix #10)
```

#### Bug fix #9: Duplicate status update to "tested"

**File:** `src/webseed/pipeline.py:207` and `pipeline.py:215-218`

**Before:**
```python
store.update_status(db, place_id, "tested")          # line 207
print("  ✅ Test passed")

# ...screenshot capture...

store.update_status(                                   # line 215-218
    db, place_id, "tested",
    {"site_screenshot_path": email_screenshot},
)
```

**After:**
```python
store.update_status(db, place_id, "tested")            # line 207
print("  ✅ Test passed")

# ...screenshot capture...

# Only update the screenshot path, don't re-set status
if email_screenshot:
    store.update_status(
        db, place_id, "tested",
        {"site_screenshot_path": email_screenshot},
    )
```

**Why:** The double `update_status` call is harmless but wasteful and confusing. More importantly, if the status were changed between lines 207 and 215 (e.g. by a concurrent process), the second call would revert it. The conditional also avoids storing an empty string on screenshot failure.

---

## 4. Status Constants

Replace hard-coded status strings to prevent typos and enable IDE autocomplete.

**File:** `src/webseed/store.py` — add at the top of the file, after imports:

```python
# Status constants — pipeline progression
SEARCHED = "searched"
GENERATED = "generated"
PREVIEW_DEPLOYED = "preview_deployed"
TESTED = "tested"
DEPLOYED = "deployed"
EMAIL_QUEUED = "email_queued"
EMAILED = "emailed"
OPTED_OUT = "opted_out"

# Error statuses
ERROR_GENERATE = "error_generate"
ERROR_DEPLOY = "error_deploy"
ERROR_TEST = "error_test"
ERROR_EMAIL = "error_email"
```

Then replace all string literals in `src/webseed/pipeline.py` and `src/webseed/store.py`:
- `"searched"` → `store.SEARCHED` (or `SEARCHED` within store.py)
- `"generated"` → `store.GENERATED`
- `"preview_deployed"` → `store.PREVIEW_DEPLOYED`
- `"tested"` → `store.TESTED`
- `"deployed"` → `store.DEPLOYED`
- `"email_queued"` → `store.EMAIL_QUEUED`
- `"opted_out"` → `store.OPTED_OUT`
- `"error_generate"` → `store.ERROR_GENERATE`
- `"error_deploy"` → `store.ERROR_DEPLOY`
- `"error_test"` → `store.ERROR_TEST`
- `"error_email"` → `store.ERROR_EMAIL`

---

## 5. Additional Bug Fixes

### Bug fix #10: Blacklist check missing in generate/deploy/email

**File:** `src/webseed/pipeline.py`

Currently, blacklist is only checked in `cmd_search` (line 105). Businesses blacklisted *after* search still get processed by generate, deploy, and email.

**Fix:** Add blacklist check at the start of the loop in `cmd_generate`, `cmd_deploy`, and `cmd_email`:

```python
# In cmd_generate, after line 138 (for i, doc in enumerate(...)):
blacklist = store.get_full_blacklist(db)
# ... then inside the loop:
if doc["place_id"] in blacklist:
    print(f"  Skip (blacklisted): {doc['name']}")
    continue
```

Apply the same pattern in `cmd_deploy` (after line 175) and `cmd_email` (after line 268). Load the blacklist once before the loop, check inside.

### Bug fix #11: CONTACT_EMAIL validation

**File:** `src/webseed/pipeline.py:261`

After `contact_email = env["CONTACT_EMAIL"]`, add:

```python
import re
if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", contact_email):
    print(f"❌ CONTACT_EMAIL non valido: {contact_email}")
    raise SystemExit(1)
```

**Why:** An invalid CONTACT_EMAIL gets embedded in every generated email's footer. Catching it early prevents a batch of broken emails.

---

## 6. Verification

### Run all tests

```bash
pip install -e ".[test]"
pytest tests/ -v --tb=short
```

### Check coverage

```bash
pytest tests/ --cov=webseed --cov-report=term-missing
```

### Expected coverage targets

| Module | Target |
|--------|--------|
| store.py | >90% |
| maps.py | >70% (external API calls mocked) |
| config.py | >80% |
| generator.py | >85% |
| deployer.py | >75% (subprocess mocked) |
| tester.py | >60% (Playwright mocked) |
| emailer.py | >70% (Gmail API mocked) |
| pipeline.py | >50% (integration tests cover main paths) |

### Manual smoke test after bug fixes

```bash
# Verify the full pipeline still works end-to-end
webseed search --location "Milano, Italy" --query "ristorante" --limit 2
webseed generate
webseed deploy
webseed status
```

---

## Summary of Bug Fixes

| # | File:Line | Issue | Severity |
|---|-----------|-------|----------|
| 1 | `maps.py:55` | `photo["photo_reference"]` KeyError | Critical |
| 2 | `maps.py:44` | `safe_name()` 30-char truncation collisions | Moderate |
| 3 | `config.py:54` | OAuth response no bounds check → IndexError | Critical |
| 4 | `generator.py:45` | Code fence regex not case insensitive | Low |
| 5 | `generator.py:66-70` | No HTML validation on Claude output | High |
| 6 | `deployer.py:16-23` | URL extraction falls back to garbage | High |
| 7 | `tester.py:30,56` | Bare `except Exception` catches Ctrl+C | Moderate |
| 8 | `emailer.py:91` | No JSON schema validation for email fields | High |
| 9 | `pipeline.py:207,215` | Duplicate status update to "tested" | Low |
| 10 | `pipeline.py` | Blacklist not checked in generate/deploy/email | Moderate |
| 11 | `pipeline.py:261` | No CONTACT_EMAIL format validation | Low |
