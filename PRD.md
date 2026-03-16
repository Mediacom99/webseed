# webseed — Frontend PRD

## Overview
Internal dashboard for operating the webseed pipeline — a system that finds Italian local businesses without websites on Google Maps, generates professional HTML sites with Claude AI, deploys them to Vercel, and creates Gmail outreach drafts. Built for a single operator/team who needs to monitor pipeline progress in real-time, manage discovered businesses, and tune prompts/config. React SPA with WebSocket-driven live updates.

## Tech Stack
- **Framework:** React 19 + Vite (SPA, TypeScript strict)
- **Components:** shadcn/ui (Radix + Tailwind CSS)
- **Pipeline viz:** React Flow (xyflow) + Framer Motion
- **Icons:** Lucide
- **Routing:** react-router-dom
- **API client:** Orval (auto-generated from openapi.json) → TanStack Query hooks + Zod schemas
- **Server state:** TanStack Query
- **Client state:** Zustand (WebSocket, active jobs)
- **Forms:** react-hook-form + Zod
- **Testing:** Vitest + Testing Library (unit), Playwright (E2E)

## References
- Architecture: `docs/FRONTEND_ARCHITECTURE.md`
- API: `openapi.json`
- Project context: `CLAUDE.md`

---

## Epic 1: Project Foundation

### Story 1.1: Project scaffold + API client + health check
**As a** developer, **I want to** have a fully configured frontend project with auto-generated API types, **so that** all subsequent stories can build on a working foundation.

**Depends on:** none

**API endpoints:**
- `GET /api/businesses/stats` — used to verify API connectivity on health check page

**Files to create/modify:**
- `frontend/package.json` — dependencies (react, vite, tailwind, shadcn, orval, tanstack-query, zustand, react-router-dom, react-hook-form, zod, framer-motion, @xyflow/react, lucide-react)
- `frontend/tsconfig.json` — strict mode TypeScript config
- `frontend/vite.config.ts` — Vite config with `/api` and `/ws` proxy to localhost:8000
- `frontend/tailwind.config.ts` — Tailwind config with shadcn/ui preset
- `frontend/orval.config.ts` — reads `../openapi.json`, outputs to `src/api/`
- `frontend/components.json` — shadcn/ui config
- `frontend/index.html` — entry HTML
- `frontend/src/main.tsx` — React entry point
- `frontend/src/App.tsx` — QueryClientProvider + RouterProvider shell
- `frontend/src/api/client.ts` — custom fetch instance (reads API key from localStorage, attaches `X-API-Key` header)
- `frontend/src/api/` — Orval-generated endpoints, schemas, types
- `frontend/src/lib/utils.ts` — `cn()` helper
- `frontend/src/pages/HealthCheckPage.tsx` — temporary page that calls `GET /api/businesses/stats` and displays result or error
- `frontend/src/components/ui/button.tsx` — shadcn Button (first UI component to confirm shadcn works)
- `frontend/src/components/ui/card.tsx` — shadcn Card
- `frontend/src/components/ui/sonner.tsx` — shadcn Sonner (toast notifications)

**Acceptance criteria:**
- [x] `npm install` completes without errors
- [x] `npm run generate-api` produces typed hooks in `src/api/endpoints/`
- [x] `npm run dev` starts Vite dev server on localhost:5173
- [x] `npm run type-check` passes with no errors
- [x] Health check page at `/` calls `GET /api/businesses/stats` and renders the JSON response
- [x] API proxy works: request goes through Vite to backend on :8000

**Testing:**
- [x] `npm run type-check` passes
- [x] `npm run build` succeeds
- [x] Health check page renders and shows API response or connection error
- [x] Vitest config works: `npm run test` runs (even with 0 tests)

**Commit:** `feat(scaffold): initialize frontend with Vite, shadcn, Orval API client`

**Status:** - [x] Done

---

## HARD STOP — Checkpoint: Project foundation
**Verify before continuing:**
- [x] `cd frontend && npm run dev` starts without errors
- [x] Open http://localhost:5173 — health check page loads
- [x] Page shows stats from backend (backend must be running on :8000)
- [x] `npm run type-check` and `npm run build` both pass

---

## Epic 2: Authentication & App Shell

### Story 2.1: Auth store + Login page
**As a** user, **I want to** enter my API key on a login page, **so that** I can authenticate and access the dashboard.

**Depends on:** Story 1.1

**API endpoints:**
- `GET /api/businesses/stats` — validates the API key works (returns 200 or 401/403)

**Files to create/modify:**
- `frontend/src/stores/auth.ts` — Zustand store: `apiKey`, `setApiKey()`, `clearApiKey()`, reads/writes localStorage
- `frontend/src/api/client.ts` — update custom fetch to read API key from auth store
- `frontend/src/pages/LoginPage.tsx` — API key input form, submit validates by calling stats endpoint, on success stores key + redirects to `/`
- `frontend/src/components/ui/input.tsx` — shadcn Input
- `frontend/src/components/ui/label.tsx` — shadcn Label

**Acceptance criteria:**
- [x] Login page renders at `/login` with API key input and submit button
- [x] Entering a valid key and submitting redirects to `/`
- [x] Entering an invalid key shows an error message (toast or inline)
- [x] API key persists in localStorage across page refreshes
- [x] Auth store `clearApiKey()` removes key from localStorage

**Testing:**
- [x] Auth store unit test: set/get/clear key from localStorage
- [x] Login page renders without errors
- [x] Invalid key shows error state
- [x] Valid key triggers redirect

**Commit:** `feat(auth): add login page with API key validation`

**Status:** - [x] Done

---

### Story 2.2: App layout with sidebar + route protection
**As a** user, **I want to** see a sidebar navigation and be redirected to login if unauthenticated, **so that** I can navigate between pages securely.

**Depends on:** Story 2.1

**API endpoints:** none (client-side routing only)

**Files to create/modify:**
- `frontend/src/components/layout/AuthGuard.tsx` — checks auth store for API key, redirects to `/login` if missing, renders `<Outlet>` if present
- `frontend/src/components/layout/Sidebar.tsx` — collapsible sidebar with nav items (Dashboard, Pipeline, Businesses, Settings), Lucide icons, active state
- `frontend/src/components/layout/AppLayout.tsx` — Sidebar + main content `<Outlet>`
- `frontend/src/App.tsx` — update with full route config: `/login` (public), `/` group under AuthGuard → AppLayout with Dashboard, Pipeline, Businesses, Business Detail, Settings
- `frontend/src/pages/DashboardPage.tsx` — placeholder page with title
- `frontend/src/pages/PipelinePage.tsx` — placeholder page with title
- `frontend/src/pages/BusinessesPage.tsx` — placeholder page with title
- `frontend/src/pages/BusinessDetailPage.tsx` — placeholder page with title
- `frontend/src/pages/SettingsPage.tsx` — placeholder page with title
- `frontend/src/components/ui/separator.tsx` — shadcn Separator
- `frontend/src/components/ui/tooltip.tsx` — shadcn Tooltip

**Acceptance criteria:**
- [x] Visiting `/` without API key redirects to `/login`
- [x] After login, sidebar shows 4 nav items with correct icons
- [x] Clicking nav items navigates to correct routes; active item is highlighted
- [x] Sidebar collapses to icon-only mode via toggle button
- [x] All placeholder pages render their titles at correct routes

**Testing:**
- [x] AuthGuard redirects unauthenticated users to `/login`
- [x] AuthGuard renders children when API key is present
- [x] Sidebar renders all nav items
- [x] Route navigation works between all pages

**Commit:** `feat(layout): add sidebar navigation, AuthGuard, and route protection`

**Status:** - [x] Done

---

## HARD STOP — Checkpoint: Auth & navigation
**Verify before continuing:**
- [x] Login flow works: enter API key → lands on dashboard
- [x] Sidebar navigation between all pages works
- [x] Refreshing page preserves login state
- [x] Visiting any protected route while logged out redirects to `/login`

---

## Epic 3: WebSocket & Dashboard

### Story 3.1: WebSocket store + connection lifecycle
**As a** developer, **I want to** have a persistent WebSocket connection managed in Zustand, **so that** all pages can receive real-time pipeline events.

**Depends on:** Story 2.2

**API endpoints:**
- `WS /ws?api_key=...` — real-time event stream

**Files to create/modify:**
- `frontend/src/stores/websocket.ts` — Zustand store: `connect(apiKey)`, `disconnect()`, `events[]` (capped buffer), `activeJobs` map, `isConnected` flag, exponential backoff reconnect
- `frontend/src/hooks/useWebSocketEvents.ts` — subscribe to filtered events (by job_id, event_type, step)
- `frontend/src/types/index.ts` — `PipelineEvent` interface, `PipelineStep` type, `EventType` type
- `frontend/src/components/layout/AuthGuard.tsx` — connect WebSocket on mount (when API key present), disconnect on unmount/logout

**Acceptance criteria:**
- [x] WebSocket connects automatically after login
- [x] Store parses incoming JSON into typed `PipelineEvent` objects
- [x] `isConnected` flag reflects actual connection state
- [x] Reconnects with exponential backoff on disconnect (up to 30s max)
- [x] `disconnect()` cleanly closes the connection
- [x] Events buffer is capped at 200 entries (oldest dropped)

**Testing:**
- [x] WebSocket store unit test: event parsing, buffer cap, activeJobs tracking
- [x] useWebSocketEvents hook filters events by job_id correctly
- [x] Reconnect logic backs off correctly
- [x] Disconnect clears state

**Commit:** `feat(websocket): add Zustand WebSocket store with reconnect and event filtering`

**Status:** - [x] Done

---

### Story 3.2: Dashboard page with stats and activity
**As a** user, **I want to** see pipeline statistics and recent activity on the dashboard, **so that** I can quickly assess the state of my businesses and decide what to run next.

**Depends on:** Story 3.1

**API endpoints:**
- `GET /api/businesses/stats` — returns `{searched: N, enriched: N, ...}` status counts

**Files to create/modify:**
- `frontend/src/components/dashboard/StatsCards.tsx` — grid of cards showing count per pipeline status, colored badges
- `frontend/src/components/dashboard/RecentActivity.tsx` — scrollable list of recent WebSocket events from store
- `frontend/src/components/dashboard/ActiveJobs.tsx` — summary of currently running jobs (derived from WS events with `step_start` without matching `job_complete`)
- `frontend/src/pages/DashboardPage.tsx` — compose StatsCards + ActiveJobs + RecentActivity
- `frontend/src/components/ui/badge.tsx` — shadcn Badge
- `frontend/src/components/ui/scroll-area.tsx` — shadcn ScrollArea

**Acceptance criteria:**
- [x] Stats cards display counts for each pipeline status from API
- [x] Stats auto-refresh on short interval (30s stale time)
- [x] Recent activity shows last 50 WebSocket events with timestamp and message
- [x] Active jobs section shows running jobs or "No active jobs" when idle
- [x] Stats cards refetch when a `step_done` WebSocket event arrives

**Testing:**
- [x] StatsCards renders all status counts from mock API data
- [x] RecentActivity renders event list from mock WS store
- [x] Dashboard page composes all three sections without errors
- [x] Empty state shows when no events exist

**Commit:** `feat(dashboard): add stats cards, recent activity, and active jobs`

**Status:** - [x] Done

---

## Epic 4: Pipeline Runner

### Story 4.1: React Flow pipeline visualization
**As a** user, **I want to** see the 6-step pipeline as an interactive flow graph, **so that** I can visually track which step is running, done, or errored.

**Depends on:** Story 3.1

**API endpoints:** none (driven by WebSocket events)

**Files to create/modify:**
- `frontend/src/components/pipeline/PipelineNode.tsx` — custom React Flow node: icon, label, status indicator (idle/queued/running/done/error) with Framer Motion transitions
- `frontend/src/components/pipeline/PipelineEdge.tsx` — custom animated edge (dashed when idle, animated flow when active)
- `frontend/src/components/pipeline/PipelineFlow.tsx` — React Flow canvas with 6 nodes (Search → Enrich → Generate → Test → Deploy → Email), horizontal layout, connected with custom edges
- `frontend/src/hooks/usePipelineStatus.ts` — derives per-step status from WebSocket events for a given job_id
- `frontend/src/pages/PipelinePage.tsx` — renders PipelineFlow (full width) + placeholder sections below

**Acceptance criteria:**
- [x] 6 pipeline nodes render in horizontal flow: Search → Enrich → Generate → Test → Deploy → Email
- [x] Each node shows its name and a status icon (idle state by default)
- [x] Nodes update status based on WebSocket events (step_start → running, step_done → done, step_error → error)
- [x] Edges animate when the source node is in "running" state
- [x] usePipelineStatus hook correctly aggregates events per step

**Testing:**
- [x] PipelineFlow renders 6 nodes and 5 edges
- [x] PipelineNode displays correct status colors for each state
- [x] usePipelineStatus unit test: derives correct step statuses from event sequence
- [x] Flow is non-interactive (no drag/zoom needed but allowed)

**Commit:** `feat(pipeline): add React Flow visualization with animated step nodes`

**Status:** - [x] Done

---

### Story 4.2: Search form + job submission
**As a** user, **I want to** fill out a search form and trigger a Maps search, **so that** I can discover new businesses to process.

**Depends on:** Story 4.1

**API endpoints:**
- `POST /api/pipeline/search` — `{location, query, types?, limit?, min_score?, grid_size?}` → `{job_id}`

**Files to create/modify:**
- `frontend/src/components/pipeline/SearchForm.tsx` — react-hook-form: location (required text), query (required text), types (optional comma-separated text), limit (number, default 10), min_score (number slider 0-60, default 0), grid_size (number, default 3). Submit calls `POST /api/pipeline/search`
- `frontend/src/pages/PipelinePage.tsx` — add SearchForm in a collapsible panel/dialog above the flow
- `frontend/src/components/ui/slider.tsx` — shadcn Slider
- `frontend/src/components/ui/dialog.tsx` — shadcn Dialog
- `frontend/src/components/ui/form.tsx` — shadcn Form
- `frontend/src/components/ui/select.tsx` — shadcn Select

**Acceptance criteria:**
- [x] Search form renders with all fields and correct defaults
- [x] Submitting with valid data calls `POST /api/pipeline/search` and returns a job_id
- [x] Job_id is set as the active job — pipeline flow starts showing WS events for it
- [x] Validation prevents submission without location and query
- [x] Toast notification shows on successful submission with job_id
- [x] Toast shows error message on API failure

**Testing:**
- [x] Search form renders all fields with defaults
- [x] Form validation rejects empty location/query
- [x] Successful submission calls API and shows success toast
- [x] API error displays error toast

**Commit:** `feat(pipeline): add search form with Maps discovery job submission`

**Status:** - [x] Done

---

### Story 4.3: Live activity feed + business progress table
**As a** user, **I want to** see a live scrolling event log and per-business progress table during a job, **so that** I can monitor exactly what's happening in real-time.

**Depends on:** Story 4.2

**API endpoints:**
- `GET /api/businesses` — fetches businesses to populate progress table after search completes

**Files to create/modify:**
- `frontend/src/components/pipeline/LiveActivityFeed.tsx` — scrollable list of WS events for current job_id, auto-scrolls to bottom, shows timestamp + step + message, color-coded by event_type
- `frontend/src/components/pipeline/BusinessProgressTable.tsx` — table showing businesses in current job, columns: name, place_id (truncated), current step, status badge. Updates via WS events
- `frontend/src/components/businesses/StatusBadge.tsx` — reusable colored badge component mapping pipeline status to color
- `frontend/src/pages/PipelinePage.tsx` — compose: PipelineFlow (top) → BusinessProgressTable (middle) → LiveActivityFeed (bottom)
- `frontend/src/components/ui/table.tsx` — shadcn Table

**Acceptance criteria:**
- [x] Activity feed shows all WS events for the active job, newest at bottom
- [x] Feed auto-scrolls to latest event as new ones arrive
- [x] Business progress table lists businesses discovered by search, updates status per WS events
- [x] StatusBadge shows correct color for each status (searched=blue, enriched=purple, generated=green, etc.)
- [x] Events are color-coded: step_done=green, step_error=red, progress=gray

**Testing:**
- [x] LiveActivityFeed renders events from mock store
- [x] BusinessProgressTable renders rows and updates on new events
- [x] StatusBadge renders correct variant for each status
- [x] Empty states show when no events/businesses

**Commit:** `feat(pipeline): add live activity feed and business progress table`

**Status:** - [x] Done

---

### Story 4.4: Run pipeline + individual step forms
**As a** user, **I want to** run the full pipeline or individual steps on selected businesses, **so that** I can process businesses through any combination of steps.

**Depends on:** Story 4.3

**API endpoints:**
- `POST /api/pipeline/run` — `{place_ids, model?, test_model?, max_fix_iterations?, no_email?, playwright?}` → `{job_id}`
- `POST /api/pipeline/enrich` — `{place_ids, only_media?}` → `{job_id}`
- `POST /api/pipeline/generate` — `{place_ids, model?}` → `{job_id}`
- `POST /api/pipeline/test` — `{place_ids, playwright?, max_fix_iterations?, model?}` → `{job_id}`
- `POST /api/pipeline/deploy` — `{place_ids}` → `{job_id}`
- `POST /api/pipeline/email` — `{place_ids, model?}` → `{job_id}`

**Files to create/modify:**
- `frontend/src/components/pipeline/RunPipelineForm.tsx` — form with: business multi-select (checkbox list from GET /businesses), model select, test_model select, max_fix_iterations number, no_email toggle, playwright toggle. Submits to `POST /api/pipeline/run`. Also dropdown to pick individual step (enrich/generate/test/deploy/email) with step-specific fields
- `frontend/src/pages/PipelinePage.tsx` — add RunPipelineForm alongside SearchForm (tabbed or side-by-side)
- `frontend/src/components/ui/checkbox.tsx` — shadcn Checkbox
- `frontend/src/components/ui/switch.tsx` — shadcn Switch
- `frontend/src/components/ui/tabs.tsx` — shadcn Tabs

**Acceptance criteria:**
- [x] Run pipeline form lists businesses from API with checkboxes for selection
- [x] Full pipeline run submits selected place_ids + options to `POST /api/pipeline/run`
- [x] Individual step dropdown shows enrich/generate/test/deploy/email with step-specific fields
- [x] Submitting any form returns job_id and sets it as active job
- [x] Form disables submit when no businesses are selected
- [x] Toast confirms job submission or shows error

**Testing:**
- [x] RunPipelineForm renders business list from mock API
- [x] Submit calls correct endpoint based on selected step
- [x] Validation prevents submission with empty place_ids
- [x] All 7 pipeline endpoints are callable from the form

**Commit:** `feat(pipeline): add run pipeline and individual step trigger forms`

**Status:** - [x] Done

---

## HARD STOP — Checkpoint: Pipeline Runner complete
**Verify before continuing:**
- [x] Search form submits and returns job_id
- [x] Pipeline flow nodes update in real-time via WebSocket
- [x] Activity feed streams events for active job
- [x] Business progress table shows per-business status
- [x] Run pipeline form selects businesses and triggers full run
- [x] Individual step triggers work (enrich, generate, test, deploy, email)

---

## Epic 5: Business Management

### Story 5.1: Business list with filtering and sorting
**As a** user, **I want to** see all businesses in a filterable, sortable data table, **so that** I can find and manage businesses by status.

**Depends on:** Story 2.2

**API endpoints:**
- `GET /api/businesses` — list all, filterable by `?status=`
- `GET /api/businesses/stats` — status counts for filter badges

**Files to create/modify:**
- `frontend/src/components/businesses/BusinessTable.tsx` — data table with columns: name, place_id (truncated), status (StatusBadge), city, rating, lead_score. Client-side sorting. Status filter dropdown
- `frontend/src/pages/BusinessesPage.tsx` — compose: status filter bar (using stats counts) + BusinessTable
- `frontend/src/components/ui/dropdown-menu.tsx` — shadcn DropdownMenu

**Acceptance criteria:**
- [x] Table renders all businesses from API with correct columns
- [x] Status filter dropdown filters the list (calls API with `?status=` param)
- [x] Filter bar shows count badges per status from stats endpoint
- [x] Client-side sorting works on name, rating, lead_score columns
- [x] Clicking a business row navigates to `/businesses/:placeId`
- [x] Table refreshes when WS `step_done` events arrive

**Testing:**
- [x] BusinessTable renders rows from mock data
- [x] Status filter updates query params and refetches
- [x] Row click navigates to detail route
- [x] Empty state when no businesses match filter

**Commit:** `feat(businesses): add filterable business data table with status filter`

**Status:** - [x] Done

---

### Story 5.2: Business detail page with status management
**As a** user, **I want to** view full business details and manage its status/blacklist, **so that** I can inspect individual businesses and control their pipeline state.

**Depends on:** Story 5.1

**API endpoints:**
- `GET /api/businesses/{place_id}` — full business detail
- `PATCH /api/businesses/{place_id}/status` — `{to: "status_name"}`
- `POST /api/businesses/{place_id}/blacklist` — add to blacklist
- `DELETE /api/businesses/{place_id}/blacklist` — remove from blacklist
- `DELETE /api/businesses/{place_id}` — soft delete

**Files to create/modify:**
- `frontend/src/components/businesses/BusinessDetail.tsx` — detail card: all business fields (name, address, phone, rating, reviews, lead_score, status, website_url, vercel_url, error_detail, etc.), status badge, action buttons
- `frontend/src/pages/BusinessDetailPage.tsx` — fetch business by placeId route param, render BusinessDetail + action buttons
- `frontend/src/components/ui/alert-dialog.tsx` — shadcn AlertDialog (for destructive confirmations)

**Acceptance criteria:**
- [ ] Detail page loads business data by place_id from route params
- [ ] All business fields render (name, address, phone, rating, lead_score, status, etc.)
- [ ] "Change Status" dropdown allows setting any valid status
- [ ] Blacklist toggle adds/removes `opted_out` status with optimistic update
- [ ] Delete button shows confirmation dialog, then removes business
- [ ] 404 state shows when business not found

**Testing:**
- [ ] BusinessDetail renders all fields from mock data
- [ ] Status change calls PATCH endpoint with correct payload
- [ ] Blacklist toggle calls correct POST/DELETE endpoint
- [ ] Delete confirmation dialog appears before deletion

**Commit:** `feat(businesses): add business detail page with status and blacklist management`

**Status:** - [ ] Not started

---

### Story 5.3: Bulk actions + CSV export
**As a** user, **I want to** select multiple businesses for bulk actions and export data as CSV, **so that** I can manage businesses efficiently at scale.

**Depends on:** Story 5.1

**API endpoints:**
- `POST /api/businesses/hard-delete` — `{place_ids, keep_blacklisted?}`
- `POST /api/businesses/close` — `{place_ids}`
- `GET /api/businesses/export/csv` — CSV file download

**Files to create/modify:**
- `frontend/src/components/businesses/BusinessTable.tsx` — add checkbox column for row selection, bulk action toolbar (hard delete, close, run pipeline on selected)
- `frontend/src/pages/BusinessesPage.tsx` — add CSV export button in header

**Acceptance criteria:**
- [ ] Checkbox column allows selecting individual rows and "select all"
- [ ] Bulk action toolbar appears when rows are selected, showing count
- [ ] "Hard Delete" bulk action shows confirmation, calls `POST /api/businesses/hard-delete`
- [ ] "Close" bulk action calls `POST /api/businesses/close`
- [ ] CSV export button triggers file download via `GET /api/businesses/export/csv`
- [ ] Selection clears after bulk action completes

**Testing:**
- [ ] Checkbox selection/deselection works correctly
- [ ] Bulk delete calls API with selected place_ids
- [ ] CSV export triggers download
- [ ] Confirmation dialog prevents accidental bulk delete

**Commit:** `feat(businesses): add bulk actions and CSV export`

**Status:** - [ ] Not started

---

## Epic 6: Settings

### Story 6.1: Settings page with prompt editor and config table
**As a** user, **I want to** edit prompt templates and config values, **so that** I can tune the pipeline's behavior without touching code.

**Depends on:** Story 2.2

**API endpoints:**
- `GET /api/settings` — list all, filterable by `?prefix=prompt` or `?prefix=config`
- `GET /api/settings/{key}` — single setting
- `PUT /api/settings/{key}` — `{value, description?}`

**Files to create/modify:**
- `frontend/src/components/settings/PromptEditor.tsx` — list of prompt settings, each with key (read-only), expandable textarea for value, description field, save button. Calls `PUT /api/settings/{key}`
- `frontend/src/components/settings/ConfigTable.tsx` — table of config settings: key (read-only), value (inline editable text input), description, save button per row
- `frontend/src/pages/SettingsPage.tsx` — tabbed layout: "Prompts" tab → PromptEditor, "Config" tab → ConfigTable
- `frontend/src/components/ui/textarea.tsx` — shadcn Textarea
- `frontend/src/components/ui/collapsible.tsx` — shadcn Collapsible

**Acceptance criteria:**
- [ ] Prompts tab loads all `prompt.*` settings and displays as expandable editors
- [ ] Config tab loads all `config.*` settings in an editable table
- [ ] Editing a value and clicking save calls `PUT /api/settings/{key}` with new value
- [ ] Success toast confirms save; error toast on failure
- [ ] Unsaved changes are visually indicated (dirty state)
- [ ] Tab switching preserves unsaved edits (client-side)

**Testing:**
- [ ] PromptEditor renders prompt settings from mock data
- [ ] ConfigTable renders config settings and allows inline editing
- [ ] Save calls PUT endpoint with correct key and value
- [ ] Dirty state indicator shows on modified fields

**Commit:** `feat(settings): add prompt editor and config table with tabbed layout`

**Status:** - [ ] Not started

---

## HARD STOP — Checkpoint: All features complete
**Verify before continuing:**
- [ ] Dashboard: stats cards load, recent activity shows WS events
- [ ] Pipeline: search form works, flow updates in real-time, run pipeline form works
- [ ] Businesses: table filters/sorts, detail page loads, bulk actions work, CSV exports
- [ ] Settings: prompts and config are editable and saveable
- [ ] WebSocket: events flow to all pages, reconnect works after disconnect
- [ ] All routes protected by AuthGuard

---

## Epic 7: Polish & QA

### Story 7.1: Loading states + error boundaries
**As a** user, **I want to** see loading indicators and graceful error pages, **so that** the app feels responsive and doesn't crash on failures.

**Depends on:** Stories 3.2, 4.4, 5.3, 6.1

**API endpoints:** none (UI-only)

**Files to create/modify:**
- `frontend/src/components/ui/skeleton.tsx` — shadcn Skeleton
- `frontend/src/components/layout/ErrorBoundary.tsx` — React error boundary with "Something went wrong" message + retry button
- `frontend/src/pages/DashboardPage.tsx` — add skeleton loading for stats cards
- `frontend/src/pages/BusinessesPage.tsx` — add skeleton loading for table
- `frontend/src/pages/BusinessDetailPage.tsx` — add skeleton loading for detail
- `frontend/src/pages/SettingsPage.tsx` — add skeleton loading for settings list
- `frontend/src/pages/PipelinePage.tsx` — add skeleton loading for business list in RunPipelineForm
- `frontend/src/App.tsx` — wrap route tree in ErrorBoundary

**Acceptance criteria:**
- [ ] Every page shows skeleton loaders while data is fetching
- [ ] Error boundary catches rendering errors and shows recovery UI
- [ ] API error states show inline error message with retry button
- [ ] Toast notifications show on mutation errors (422, 500, network)

**Testing:**
- [ ] Skeleton loaders appear during loading state (mock slow API)
- [ ] ErrorBoundary catches thrown errors and renders fallback
- [ ] Retry button re-fetches data
- [ ] API 422 errors display field-level messages on forms

**Commit:** `feat(polish): add loading skeletons and error boundaries`

**Status:** - [ ] Not started

---

### Story 7.2: Empty states + responsive layout + accessibility
**As a** user, **I want to** see helpful empty states and use the app on smaller screens, **so that** the app is usable in all scenarios.

**Depends on:** Story 7.1

**API endpoints:** none (UI-only)

**Files to create/modify:**
- `frontend/src/components/businesses/BusinessTable.tsx` — empty state: "No businesses found" with call-to-action to search
- `frontend/src/components/pipeline/LiveActivityFeed.tsx` — empty state: "No events yet. Start a job to see activity"
- `frontend/src/components/pipeline/BusinessProgressTable.tsx` — empty state: "No businesses in this job"
- `frontend/src/components/dashboard/RecentActivity.tsx` — empty state: "No recent activity"
- `frontend/src/components/settings/PromptEditor.tsx` — empty state: "No prompts configured"
- `frontend/src/components/layout/Sidebar.tsx` — responsive: collapses to icons at md breakpoint, hidden on mobile with hamburger toggle
- All interactive elements — ensure keyboard navigation and aria labels

**Acceptance criteria:**
- [ ] Every list/table shows a meaningful empty state when data is empty
- [ ] Sidebar collapses automatically on screens < 1024px
- [ ] Mobile: sidebar hidden by default, toggle via hamburger menu
- [ ] All buttons and form elements are keyboard-navigable
- [ ] Color contrast meets WCAG AA for all text and badges
- [ ] Focus indicators visible on all interactive elements

**Testing:**
- [ ] Empty state renders when API returns empty arrays
- [ ] Sidebar collapse/expand works at different viewport widths
- [ ] Tab key navigates through all interactive elements
- [ ] Screen reader can announce page content (aria-labels on landmarks)

**Commit:** `feat(polish): add empty states, responsive sidebar, and accessibility`

**Status:** - [ ] Not started

---

## Completion
All stories implemented and tested. All acceptance criteria checked off.

---

## Report

| Metric | Value |
|--------|-------|
| Total epics | 7 |
| Total stories | 13 |
| Total HARD STOPs | 4 |

### Effort per story

| Story | Title | Effort |
|-------|-------|--------|
| 1.1 | Project scaffold + API client + health check | **L** |
| 2.1 | Auth store + Login page | **S** |
| 2.2 | App layout with sidebar + route protection | **M** |
| 3.1 | WebSocket store + connection lifecycle | **M** |
| 3.2 | Dashboard page with stats and activity | **M** |
| 4.1 | React Flow pipeline visualization | **M** |
| 4.2 | Search form + job submission | **M** |
| 4.3 | Live activity feed + business progress table | **M** |
| 4.4 | Run pipeline + individual step forms | **L** |
| 5.1 | Business list with filtering and sorting | **M** |
| 5.2 | Business detail page with status management | **M** |
| 5.3 | Bulk actions + CSV export | **M** |
| 6.1 | Settings page with prompt editor and config table | **M** |
| 7.1 | Loading states + error boundaries | **S** |
| 7.2 | Empty states + responsive layout + accessibility | **M** |

### API endpoint coverage

| Endpoint | Covered by |
|----------|-----------|
| `POST /pipeline/search` | Story 4.2 |
| `POST /pipeline/enrich` | Story 4.4 |
| `POST /pipeline/generate` | Story 4.4 |
| `POST /pipeline/test` | Story 4.4 |
| `POST /pipeline/deploy` | Story 4.4 |
| `POST /pipeline/email` | Story 4.4 |
| `POST /pipeline/run` | Story 4.4 |
| `GET /businesses` | Story 5.1 |
| `GET /businesses/stats` | Stories 1.1, 2.1, 3.2, 5.1 |
| `GET /businesses/export/csv` | Story 5.3 |
| `GET /businesses/{place_id}` | Story 5.2 |
| `DELETE /businesses/{place_id}` | Story 5.2 |
| `PATCH /businesses/{place_id}/status` | Story 5.2 |
| `POST /businesses/{place_id}/blacklist` | Story 5.2 |
| `DELETE /businesses/{place_id}/blacklist` | Story 5.2 |
| `POST /businesses/hard-delete` | Story 5.3 |
| `POST /businesses/close` | Story 5.3 |
| `GET /settings` | Story 6.1 |
| `GET /settings/{key}` | Story 6.1 |
| `PUT /settings/{key}` | Story 6.1 |
| `WS /ws` | Story 3.1 |

All 21 endpoints covered.

### Parallelizable stories
Stories that touch completely different files and could run in parallel (if multiple developers were available):
- **5.1 + 6.1**: Business table and Settings page are independent feature areas
- **5.3 + 6.1**: Bulk actions and Settings are independent
- **7.1 + 7.2**: Polish stories touch different aspects but some shared files — partial parallelism

Default execution is sequential as ordered above.
