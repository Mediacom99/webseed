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
