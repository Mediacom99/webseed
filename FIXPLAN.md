# FIXPLAN — webseed Codebase Audit

> Batches 1, 2, 6 completed (32 fixes). Remaining: REST API refactor.

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

## Progress

| Batch | Total | Done | Remaining |
|-------|-------|------|-----------|
| 1 — Critical | 6 | 6 | 0 |
| 2 — High | 9 | 9 | 0 |
| 3 — REST API | 14 | 0 | 14 |
| 6 — Verified Bugs | 17 | 17 | 0 |
| **Total** | **46** | **32** | **14** |
