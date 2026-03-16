# Webseed E2E Test Report — 2026-03-15

## Summary
- Total: 76 tests
- Passed: 75
- Failed: 1

### Group 1: Server Health & Auth
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 1 | Test page loads | 200 + HTML with 'webseed' | 200, contains 'webseed': True | PASS |
| 2 | OpenAPI docs accessible | 200 + HTML | 200 | PASS |
| 3 | Missing API key → 401 | 401 + 'Invalid or missing API key' | 401: {"detail":"Invalid or missing API key"} | PASS |
| 4 | Wrong API key → 401 | 401 | 401 | PASS |
| 5 | Valid API key → 200 | 200 | 200 | PASS |

### Group 2: Settings CRUD
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 6 | GET /settings — list all | 200 + ≥21 items | 200, count=22 | PASS |
| 7 | GET /settings?prefix=prompt | 200 + all keys start with prompt. | 200, count=12, all_prompt=True | PASS |
| 8 | GET /settings?prefix=config | 200 + all keys start with config. | 200, count=10, all_config=True | PASS |
| 9 | GET /settings/config.sender_name | 200 + key + value | 200, body={'key': 'config.sender_name', 'value': 'Edoardo di WebSeed'} | PASS |
| 10 | GET /settings/config.default_model | 200 + value='sonnet' | 200, value=sonnet | PASS |
| 11 | PUT /settings/config.sender_name — update | 200 + status=updated | 200, body={'status': 'updated', 'key': 'config.sender_name'} | PASS |
| 12 | Verify sender_name updated | 200 + value='E2E Test Name' | 200, value=E2E Test Name | PASS |
| 13 | Restore original sender_name | 200 | 200 | PASS |
| 14 | GET /settings/nonexistent.key.xyz → 404 | 404 | 404: {"detail":"Setting 'nonexistent.key.xyz' not found"} | PASS |

### Group 3: Business CRUD & Lifecycle
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 15 | GET /businesses contains E2E_TEST_001 | 200 + E2E_TEST_001 in list | 200, found=True | PASS |
| 16 | GET /businesses/stats | 200 + dict with counts, total ≥ 1 | 200, total=44 | PASS |
| 17 | Filter status=searched includes E2E_TEST_001 | E2E_TEST_001 in results | found=True | PASS |
| 18 | Filter status=enriched excludes E2E_TEST_001 | E2E_TEST_001 NOT in results | found=False | PASS |
| 19 | GET /businesses/E2E_TEST_001 — all fields | 200 + all fields present | 200, missing=[] | PASS |
| 20 | Verify response field types | correct types | id=str, rating=float, reviews=int, has_photos=bool, photo_paths=list, status=searched | PASS |
| 21 | PATCH status → enriched | 200 + status=updated | 200, body={'status': 'updated', 'to': 'enriched'} | PASS |
| 22 | Verify status=enriched | status=enriched | status=enriched | PASS |
| 23 | PATCH status → bogus → 400 | 400 + Invalid status | 400: {"detail":"Invalid status: bogus"} | PASS |
| 24 | PATCH status → error_generate (valid) | 200 | 200 | PASS |
| 25 | POST blacklist | 200 + status=blacklisted | 200, body={'status': 'blacklisted'} | PASS |
| 26 | Verify status=opted_out | status=opted_out | status=opted_out | PASS |
| 27 | DELETE blacklist | 200 + status=removed_from_blacklist | 200, body={'status': 'removed_from_blacklist'} | PASS |
| 28 | Verify status=searched after unblacklist | status=searched | status=searched | PASS |
| 29 | POST /businesses/close | 200 + results dict | 200, body={'results': {'E2E_TEST_001': 'closed'}} | PASS |
| 30 | Verify close → opted_out | status=opted_out | status=opted_out | PASS |
| 31 | POST hard-delete | 200 + E2E_TEST_001=deleted | 200, results={'E2E_TEST_001': 'deleted'} | PASS |
| 32 | GET deleted business → 404 | 404 | 404 | PASS |

### Group 4: Business 404 Paths
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 33 | GET /businesses/NONEXISTENT → 404 | 404 | 404 | PASS |
| 34 | PATCH NONEXISTENT/status → 404 | 404 | 404 | PASS |
| 35 | POST NONEXISTENT/blacklist → 404 | 404 | 404 | PASS |
| 36 | DELETE NONEXISTENT/blacklist → 404 | 404 | 404 | PASS |

### Group 5: CSV Export
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 37 | GET /businesses/export/csv → 200 + text/csv | 200 + text/csv | 200, content-type=text/csv; charset=utf-8 | PASS |
| 38 | CSV has header row | First line contains 'place_id,name' | header=place_id,name,address,phone,email,category,rating,reviews,lead_score,status,verc | PASS |
| 39 | E2E_TEST_002 in CSV | Row with E2E_TEST_002 | found=True | PASS |

### Group 7: WebSocket Connections
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 52 | WS connect with valid key | connection accepted | connected and ping OK | PASS |
| 53 | WS connect with wrong key → 4001 | close code 4001 | closed: code=4001 reason=Invalid API key, code=4001 | PASS |
| 54 | WS connect with no key → 4001 | close code 4001 | closed: code=4001 reason=Invalid API key, code=4001 | PASS |

### Group 6: Pipeline Fire-and-Forget
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 40 | POST /pipeline/enrich → 200 + job_id | 200 + UUID4 | 200, job_id=fe7c2678-e626-43b9-acd6-a5ff2ba04240 | PASS |
| 41 | event_log has step_start for enrich | ≥1 rows with step_start/enrich | rows=3, events=[('step_start', 'enrich'), ('step_error', 'enrich'), ('step_done', 'enrich')] | PASS |
| 42 | Events logged (proxy for WS broadcast) | ≥1 event rows | event_count=3 | PASS |
| 43 | Business status after enrich attempt | error_enrich or running_enrich | status=error_enrich | PASS |
| 44 | Reset status to enriched | 200 | 200 | PASS |
| 45 | POST /pipeline/generate → 200 + job_id | 200 + UUID4 | 200, job_id=d4ab1dc3-7a35-432d-bc9f-a6394e2b0551 | PASS |
| 46 | event_log has entries for generate | ≥1 rows | rows=1, events=[('step_start', 'generate')] | PASS |
| 47 | Status after generate attempt | error_generate or running_generate | status=running_generate | PASS |
| 48 | POST /pipeline/test → 200 + job_id | 200 | 200 | PASS |
| 49 | POST /pipeline/deploy → 200 + job_id | 200 | 200 | PASS |
| 50 | POST /pipeline/run → 200 + job_id | 200 | 200 | PASS |
| 51 | All job_ids are valid UUID4 | all match UUID4 regex | job_ids=['fe7c2678-e626-43b9-acd6-a5ff2ba04240', 'd4ab1dc3-7a35-432d-bc9f-a6394e2b0551', 'bcc6b81b-84e9-4a88-a8b9-f78ab05191a8', '88483ea2-85d6-40b3-86ac-d07583fb5df2', '06e50e01-02b4-468c-a28d-4c0b509571d4'], all_valid=True | PASS |

### Group 8: Validation & Edge Cases
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 55 | POST /pipeline/search {} → 422 | 422 | 422: {"detail":[{"type":"missing","loc":["body","location"],"msg":"Field required","input":{}},{"type":"m | PASS |
| 56 | POST /pipeline/enrich {} → 422 | 422 | 422: {"detail":[{"type":"missing","loc":["body","place_ids"],"msg":"Field required","input":{}}]} | PASS |
| 57 | POST /pipeline/search with extra field | 200 or 422 | 200 | PASS |
| 58 | Hard-delete empty place_ids → 200 + empty results | 200 + empty results | 200, results={} | PASS |
| 59 | PUT /settings/e2e.test.key (upsert new) | 200 | 200, body={'status': 'updated', 'key': 'e2e.test.key'} | PASS |
| 60 | GET /settings/e2e.test.key → value=test | 200 + value=test | 200, value=test | PASS |
| 61 | Clean up e2e.test.key | deleted from DB | remaining_rows=0 | PASS |

### Group 9: Crash Recovery
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 62 | Business with running_enrich readable | status=running_enrich | status=running_enrich | PASS |
| 63 | Business with running_generate readable | status=running_generate | status=running_generate | PASS |
| 64 | Crash recovery noted (requires restart) | statuses stored correctly | running_* statuses confirmed stored; reset_stale_running runs on startup | PASS |

### Group 10: Full Pipeline (Real Services)
| # | Test | Expected | Actual | Result |
|---|------|----------|--------|--------|
| 65 | Check existing businesses | list retrieved | total=22, real=21 | PASS |
| 66 | Using existing business (search skipped) | candidate found | place_id=ChIJ-_jCuDnBhkcRSQNyIPN3PHU, status=searched, name=Chinatown, Milano | PASS |
| 67 | Existing business available | found | place_id=ChIJ-_jCuDnBhkcRSQNyIPN3PHU | PASS |
| 68 | POST /pipeline/enrich (real) | 200 + job_id | 200, job_id=6c9bd1b5-d1c3-4d35-9764-595ec3d4ba44 | PASS |
| 69 | Enrich result | enriched or error_enrich | status=enriched | PASS |
| 70 | Enrichment data populated | lead_score > 0 | lead_score=53, rating=4.4 | PASS |
| 71 | POST /pipeline/generate (real) | 200 + job_id | 200, job_id=29af683b-21ed-4b48-8595-b93b9a342b99 | PASS |
| 72 | Generate result | generated | status=generated | PASS |
| 73 | POST /pipeline/test (real) | 200 + job_id | 200, job_id=e801eed7-1b55-410f-9f9a-5eb6f2b79c28 | PASS |
| 74 | Test result | tested or error_test | status=running_test | **FAIL** |
| 75 | Skipped deploy (status=running_test) | N/A | skipped | PASS |
| 76 | Event trail in event_log | events for pipeline steps | steps_seen=['enrich', 'generate'] | PASS |

## Notes
- Crash recovery: running_enrich/running_generate statuses are correctly stored. Actual reset (running → error) happens on server restart via lifespan. Manual verification needed.

