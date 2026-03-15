# FIXPLAN — webseed Codebase Audit

> Generated 2026-03-15 from full codebase audit. Batches 1 & 2 completed (15 fixes). Remaining: REST API refactor + 17 verified bugs.

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

## Batch 6 — Verified Bugs from Batches 4 & 5

> 17 real bugs triaged from Batches 4 (16 candidates → 9 real) and 5 (13 candidates → 8 real). False positives: #16, #26, #30, #31, #35, #36, #38, #39, #40, #44. Duplicates of Batch 3: #18 (= #3C.3), #21 (= #3B.1).

### Critical

- [x] **#23** `maps.py:568-569` — `safe_name()` allows `..` path traversal. Strip leading dots, validate result stays within base dir.

### High

- [x] **#17** `pipeline.py:1159` — CSV export uses first-doc fields only. Union all keys across documents.
- [x] **#22** `maps.py:338-343` — Photo download: no content-type check, full response buffered in memory. Add content-type validation, use `iter_content()`.
- [x] **#24** `maps.py:541-565` — `only_media` with no existing photo refs → partial enrichment saved as "enriched". Guard against incomplete state.
- [x] **#32** `maps.py` (all API calls) — No retry logic on transient errors (429, 503, `DeadlineExceeded`). Add `google-api-core` retry parameters.

### Medium

- [x] **#19** `store.py:53-79` — `upsert_business` doesn't clear `error_detail` on successful update. Add `"error_detail": ""` to update dict.
- [x] **#20** `store.py:118-126` — `update_status` is silent no-op for unknown `place_id`. Return bool or raise.
- [x] **#27** `emailer.py:118-129` — No email address validation on `to_email`. Validate format before creating draft.
- [x] **#29** `tester.py:170` — `networkidle` causes 30s hangs. Switch to `domcontentloaded` + explicit short wait.
- [x] **#33** `pipeline.py:400, 785` — `assert` used for control flow. Replace with `if not x: raise ValueError(...)`.
- [x] **#43** `deployer.py:76` — `VERCEL_PROJECT_NAME` env var documented but never read. Wire it up or remove from docs.

### Low

- [x] **#25** `deployer.py:77-79` — Non-atomic `vercel.json` write. Use `atomic_write()`.
- [x] **#28** `emailer.py:160-166` — Label application non-atomic. Log warning if label step fails; consider retry.
- [x] **#34** `pipeline.py:76-80` — `_load_prompt` gives raw `FileNotFoundError`. Catch and re-raise with computed path.
- [x] **#37** `maps.py:344` — Photo download failures fully silent. Add `log.debug()` on exception.
- [x] **#41** `tester.py:63-67` — `safe_name` parameter accepted but never used. Remove or implement.
- [x] **#42** `tester.py:180` — `print()` instead of `logging`. Add `log = logging.getLogger(__name__)`.
- [x] **#45** `pyproject.toml:17` — `google-maps-places>=0.1.0` extremely loose pin. Add upper bound or lock file.

---

## Progress

| Batch | Total | Done | Remaining |
|-------|-------|------|-----------|
| 1 — Critical | 6 | 6 | 0 |
| 2 — High | 9 | 9 | 0 |
| 3 — REST API | 14 | 0 | 14 |
| 6 — Verified Bugs | 17 | 17 | 0 |
| **Total** | **46** | **32** | **14** |

> Batches 4 & 5 triaged: 10 false positives dismissed, 2 duplicates folded into Batch 3, 17 real bugs promoted to Batch 6.
> Cross-batch overlaps: #8/#3C.2, #18/#3C.3, #21/#3B.1, #3/#3D.1, #12/#3D.3 — fix once, check off both.
