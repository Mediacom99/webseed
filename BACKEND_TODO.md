# Backend TODO — Changes needed to support frontend redesign

## JobResponse enhancement
- Current: `POST /pipeline/*` returns `{"job_id": "uuid"}`
- Needed: Return additional context so frontend can display meaningful job labels
- Suggestion: `{"job_id": "uuid", "label": "Search: ristoranti, Milano", "step": "search", "target_count": 5}`
- The backend should construct the label from the request parameters (e.g. search query+location, or step name + business count)
- Frontend should NOT guess/construct labels from request params it sent

## Business detail endpoint — expose all fields
- Current: `_record_to_dict` strips enrichment and pipeline metadata fields
- Needed: At minimum for `GET /businesses/{place_id}`, return ALL fields:
  - `opening_hours_summary`, `has_opening_hours`
  - `accepts_credit_cards`
  - `editorial_summary`
  - `review_texts` (list of review excerpts)
  - `types` (list of Google Place types)
  - `test_iterations`, `test_issues`
  - `site_screenshot_path` (needed for deployed site thumbnail)
  - `email_sent_at`
- Could either: add a `_record_to_full_dict` for detail endpoint, or add all fields to `_record_to_dict` (list endpoint can handle the extra data)
- Consider: list endpoint might want a lighter response (no review_texts, no test_issues) for performance. Detail endpoint should be complete.

## Typed Pydantic response models for all endpoints
- Current: Most endpoints return `dict[str, Any]` — OpenAPI spec shows `additionalProperties: true`
- Problem: Orval generates untyped interfaces (`Record<string, unknown>`), frontend has to cast everything
- Needed: Proper Pydantic `BaseModel` response classes:
  - `BusinessSummary` (for list endpoint — lighter fields)
  - `BusinessDetail` (for detail endpoint — all fields)
  - `StatsResponse`
  - `SettingItem` (for settings list)
- This gives us typed OpenAPI schemas → Orval generates real TypeScript interfaces → frontend catches missing fields at compile time
- PRIORITY: High — this unblocks the entire frontend from `as never` / `as Record<string, unknown>` casts

## [FUTURE] Aggregate stats endpoint
- Current: `GET /businesses/stats` returns only counts by status `{searched: 5, enriched: 3, ...}`
- Future: Add computed aggregate metrics:
  - Average lead score (across all non-opted-out businesses)
  - Average rating
  - Businesses processed today / this week (based on `updated_at`)
  - Emails sent this week (count of `emailed` status with recent `email_sent_at`)
- Could extend existing `/businesses/stats` or create a new `/businesses/analytics` endpoint
- PRIORITY: Low — nice-to-have for dashboard, not blocking

## Stats count mismatch with businesses list
- Dashboard stats show `50 total` (from `GET /businesses/stats`), but `GET /businesses` only returns 25 rows
- The stats endpoint counts all DB rows, but the list endpoint may be deduplicating or filtering differently
- Frontend shows "All (50)" in the status filter chips but only renders 25 table rows — confusing UX
- Investigate: either stats is over-counting or list is under-returning. Align both endpoints.
- PRIORITY: Medium — causes user confusion on the Businesses page

## GET /events endpoint for event history
- Current: Events are logged to `event_log` table but there's no REST endpoint to query them
- Needed: `GET /events?limit=200` (most recent first) so frontend can hydrate the log console on page refresh
- Optional filters: `?job_id=`, `?place_id=`, `?since=<timestamp>`
- The `event_log` table already has indexes on `job_id` and `timestamp`
- Frontend currently uses `sessionStorage` as a stopgap — this endpoint would be the proper solution
- PRIORITY: Medium — sessionStorage works for same-tab refresh but events are lost on new tabs

## Include business name in WebSocket events
- Current: `PipelineEvent` carries `place_id` but not business `name`
- Needed: Add `place_name` (or `business_name`) field to WebSocket events so the frontend log console can show human-readable tab labels instead of job ID hashes
- The name is already available in the `BusinessRecord` / `BusinessRow` at each pipeline step
- PRIORITY: Medium — frontend currently has to do separate lookups to resolve place_id → name

## Price level raw enum in API response
- Business detail returns raw Google enum like `PRICE_LEVEL_MODERATE` for price_level field
- Frontend displays it verbatim — should either be mapped on the backend to a human-friendly value, or documented so frontend can map it
- PRIORITY: Low — cosmetic issue
