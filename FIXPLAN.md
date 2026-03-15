# FIXPLAN — webseed Codebase Audit

> Generated 2026-03-15 from full codebase audit. 45 issues across 5 severity tiers + REST API readiness blockers.

---

## Batch 1 — Critical (Security & Data Loss)

- [x] **#1** `emailer.py:51` — OAuth token file world-readable. Add `os.chmod(token_file, 0o600)` after write.
- [x] **#2** `emailer.py:51-52` — Non-atomic token write. Replace `open()` with `atomic_write()` + binary mode support.
- [x] **#3** `deployer.py:83-89` — Zombie deployments on timeout. Catch `subprocess.TimeoutExpired`, call `.kill()` on child, record `error_deploy` status.
- [x] **#4** `tester.py:33-37, 135-140` — `str.format(html=html)` crashes on CSS braces. Verify template double-escapes `{{`/`}}` or switch to `str.replace("{html}", html)`.
- [x] **#5** `store.py:180-191` — Non-atomic blacklist rewrite. Use `atomic_write()` in `remove_from_blacklist()`.
- [x] **#6** `__main__.py:1-3` — `main()` runs on import. Add `if __name__ == "__main__":` guard.

---

## Batch 2 — High Priority (Error Handling & Brittleness)

- [x] **#7** `pipeline.py:26`, `emailer.py:29` — Env vars read before `load_dotenv()`. Move `GMAIL_LABEL_NAME` and `SENDER_NAME` reads inside their respective functions.
- [x] **#8** `pipeline.py:44` — `_doc_to_business_data()` hardcodes `"results"` instead of using `results_dir` param. Thread `results_dir` through or make it a function parameter.
- [x] **#9** `pipeline.py:805-807` — Outer `except` in `cmd_run` doesn't update status. Add `store.update_status(db, place_id, "error_run", str(e))`.
- [x] **#10** `maps.py:581, 730` — Unsplash `source.unsplash.com` is dead (410 Gone since 2024). Remove fallback or replace with working alternative.
- [x] **#11** `generator.py:32-42`, `emailer.py:88` — Template injection via `str.format()`. Business names/addresses containing `{` crash with `KeyError`. Switch to `string.Template` or pre-escape braces in data.
- [x] **#12** `emailer.py:49` — Browser OAuth crashes in headless. Add interactive environment check with clear error message for non-interactive contexts.
- [x] **#13** `emailer.py:127` — Malformed `From` header (display name only, no email). Use `"Name <email>"` format.
- [x] **#14** `claude_cli.py:88-94` — No explicit `encoding="utf-8"` on `subprocess.run(text=True)`. Add `encoding="utf-8"`.
- [x] **#15** `claude_cli.py:103-104` — Bare `json.loads()` with no error context. Wrap in try/except, include `result.stdout[:500]` in error message.

---

## Batch 3 — REST API Readiness Refactor

### 3A — Decouple business logic from CLI

- [ ] **#3A.1** Extract core logic from each `cmd_*` function into service functions with typed parameters (not `argparse.Namespace`).
- [ ] **#3A.2** Service functions return structured result dicts/dataclasses instead of printing to stdout.
- [ ] **#3A.3** Thin CLI adapter layer that calls service functions and handles display.

### 3B — Fix state management

- [ ] **#3B.1** `maps.py:146-192` — Remove global `_client` singleton. Instantiate `PlacesClient` per-call or accept it as a parameter.
- [ ] **#3B.2** Evaluate replacing TinyDB with SQLite for thread-safe concurrent access.
- [ ] **#3B.3** `store.py` — Add proper DB lifecycle management (context manager, connection pooling).

### 3C — Fix path handling

- [ ] **#3C.1** Resolve all path arguments to absolute with `os.path.abspath()` at point of use.
- [ ] **#3C.2** `pipeline.py:44` — Remove hardcoded `"results"` in `_doc_to_business_data()` (overlaps with #8).
- [ ] **#3C.3** `pipeline.py:899+` — Derive `blacklist.txt` path from `--db` location instead of CWD.
- [ ] **#3C.4** `emailer.py:38-39` — Resolve `credentials.json` / `token.json` paths with `os.path.abspath()`.

### 3D — Fix concurrency & resource management

- [ ] **#3D.1** All subprocess calls — catch `TimeoutExpired`, call `.kill()`, prevent zombie accumulation (generalizes #3).
- [ ] **#3D.2** `emailer.py:57-73` — Make `ensure_label()` idempotent (handle duplicate creation race).
- [ ] **#3D.3** `emailer.py:49` — Support service account / pre-provisioned tokens for headless auth (extends #12).

### 3E — Unify return contracts

- [ ] **#3E.1** Define a `Result[T]` type or consistent `{"ok": bool, "data": ..., "error": ...}` pattern across all modules.
- [ ] **#3E.2** Distinguish "AI found issues" from "tooling broke" in tester return values.

---

## Batch 4 — Medium (Code Quality & Inconsistencies)

- [ ] **#16** `pipeline.py:368-396, 703-729` — Off-by-one in fix loop. Change `iteration <= max_fix_iterations` to `iteration < max_fix_iterations`.
- [ ] **#17** `pipeline.py:1159` — CSV export uses first-doc fields only. Union all keys across documents.
- [ ] **#18** `pipeline.py:899+` — Hardcoded `blacklist.txt` path ignores `--db` location (see also #3C.3).
- [ ] **#19** `store.py:53-79` — `upsert_business` doesn't clear `error_detail` on successful update. Add `"error_detail": ""` to update dict.
- [ ] **#20** `store.py:118-126` — `update_status` is silent no-op for unknown `place_id`. Return bool or raise.
- [ ] **#21** `maps.py:146-192` — Global `_client` singleton not thread-safe (see also #3B.1).
- [ ] **#22** `maps.py:338-343` — Photo download: no content-type check, full response buffered in memory. Add content-type validation, use `iter_content()`.
- [ ] **#23** `maps.py:568-569` — `safe_name()` allows `..` path traversal. Strip leading dots, validate result stays within base dir.
- [ ] **#24** `maps.py:541-565` — `only_media` with no existing photo refs → partial enrichment saved as "enriched". Guard against incomplete state.
- [ ] **#25** `deployer.py:77-79` — Non-atomic `vercel.json` write. Use `atomic_write()`.
- [ ] **#26** `generator.py:45-49` — Fragile fence stripping. Extract content of first code block instead of stripping edges.
- [ ] **#27** `emailer.py:118-129` — No email address validation on `to_email`. Validate format before creating draft.
- [ ] **#28** `emailer.py:160-166` — Label application non-atomic. Log warning if label step fails; consider retry.
- [ ] **#29** `tester.py:170` — `networkidle` causes 30s hangs. Switch to `domcontentloaded` + explicit short wait.
- [ ] **#30** `claude_cli.py:103` — Wrong type annotation `dict[str, str]`. Change to `dict[str, Any]`.
- [ ] **#31** `claude_cli.py:83` — `--tools ""` fragile against CLI version changes. Test or use `--no-tools` if available.
- [ ] **#32** `maps.py` (all API calls) — No retry logic on transient errors (429, 503, `DeadlineExceeded`). Add `google-api-core` retry parameters.

---

## Batch 5 — Low (Style & Minor)

- [ ] **#33** `pipeline.py:400, 785` — `assert` used for control flow. Replace with `if not x: raise ValueError(...)`.
- [ ] **#34** `pipeline.py:76-80` — `_load_prompt` gives raw `FileNotFoundError`. Catch and re-raise with computed path.
- [ ] **#35** `store.py:29-35` — `find_by_name` is O(n) full scan. Acceptable for CLI, note for future indexing.
- [ ] **#36** `maps.py:354-392` — Float-to-int truncation in scoring. Use `round()` instead of `int()`.
- [ ] **#37** `maps.py:344` — Photo download failures fully silent. Add `log.debug()` on exception.
- [ ] **#38** `maps.py:556-560` — `phone` stored as `""` instead of `None`. Use `None` consistently with `BusinessData`.
- [ ] **#39** `generator.py:63` — Deferred import of `safe_name` inside function. Move to module-level.
- [ ] **#40** `generator.py:71-76` — No validation that Claude output is HTML. Add `"<html" in html` sanity check.
- [ ] **#41** `tester.py:63-67` — `safe_name` parameter accepted but never used. Remove or implement.
- [ ] **#42** `tester.py:180` — `print()` instead of `logging`. Add `log = logging.getLogger(__name__)`.
- [ ] **#43** `deployer.py:76` — `VERCEL_PROJECT_NAME` env var documented but never read. Wire it up or remove from docs.
- [ ] **#44** `utils.py:13-17` — `atomic_write` sets `0o600` perms via `mkstemp`. Preserve original file permissions if file exists.
- [ ] **#45** `pyproject.toml:17` — `google-maps-places>=0.1.0` extremely loose pin. Add upper bound or lock file.

---

## Progress

| Batch | Total | Done | Remaining |
|-------|-------|------|-----------|
| 1 — Critical | 6 | 6 | 0 |
| 2 — High | 9 | 9 | 0 |
| 3 — REST API | 14 | 0 | 14 |
| 4 — Medium | 17 | 0 | 17 |
| 5 — Low | 13 | 0 | 13 |
| **Total** | **59** | **15** | **44** |

> Some issues appear in multiple batches (e.g. #8/#3C.2, #18/#3C.3, #21/#3B.1, #3/#3D.1, #12/#3D.3). Fix once, check off both.
