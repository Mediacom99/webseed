# Frontend Redesign Specification

Complete UI/UX redesign of the webseed frontend. This document is the implementation spec — it captures every design decision, layout, component, data flow, and interaction pattern agreed upon during the design session.

Source of truth for data contracts: `openapi.json` (generated from FastAPI).
Source of truth for business logic: backend `services.py` state machine.

---

## Table of Contents

1. [Page Map & Navigation](#1-page-map--navigation)
2. [Global Components](#2-global-components)
3. [Page: Login](#3-page-login)
4. [Page: Dashboard](#4-page-dashboard)
5. [Page: Search](#5-page-search)
6. [Page: Businesses](#6-page-businesses)
7. [Page: Business Detail](#7-page-business-detail)
8. [Page: Settings](#8-page-settings)
9. [Status System](#9-status-system)
10. [WebSocket Integration](#10-websocket-integration)
11. [Data Typing Strategy](#11-data-typing-strategy)
12. [Backend Dependencies](#12-backend-dependencies)

---

## 1. Page Map & Navigation

### Routes

| Route | Page | Purpose |
|---|---|---|
| `/login` | Login | API key entry, validates against backend |
| `/` | Dashboard | Birds-eye view: pipeline funnel, active jobs, quick actions |
| `/search` | Search | Discover new businesses, review results, enrich or blacklist |
| `/businesses` | Businesses | Master list with filter, sort, search, bulk actions |
| `/businesses/:placeId` | Business Detail | Full business info, pipeline graph, single-step actions |
| `/settings` | Settings | Prompt templates (markdown) and configuration values |

### What changed from current frontend

- **`/pipeline` route is removed.** Its responsibilities are split:
  - Search functionality → new `/search` page
  - "Run pipeline steps" forms → bulk actions on `/businesses` + single actions on `/businesses/:placeId`
  - Live progress monitoring → global bottom panel (visible on all pages)
- **`/search` is a new page.**
- All other routes remain the same.

### Sidebar Navigation

4 nav items + logout, in this order:

| Icon | Label | Route |
|---|---|---|
| `LayoutDashboard` | Dashboard | `/` |
| `Search` | Search | `/search` |
| `Building2` | Businesses | `/businesses` |
| `Settings` | Settings | `/settings` |
| `LogOut` | Logout | (clears API key, redirects to `/login`) |

Responsive behavior (keep current implementation):
- Desktop: full sidebar with labels, collapsible to icon-only
- Tablet (<=1024px): auto-collapses to icon-only with tooltips
- Mobile (<=768px): hamburger button, overlay drawer

---

## 2. Global Components

### 2.1 Bottom Panel (Event Log)

A resizable panel fixed to the bottom of the viewport. Part of `AppLayout`, not any individual page. All real-time WebSocket event display lives here — individual pages do not render their own activity feeds.

#### Collapsed State (default, ~32px height)

Always visible. Shows a thin bar with:

- **Connection indicator**: green dot = connected, red dot = disconnected
- **Active job summary**: "2 jobs running" or "Idle"
- **Last event message**: single-line auto-updating text, e.g. "Enriched Trattoria Nonna"
- Click anywhere on the bar to expand

#### Expanded State (resizable via drag handle, default ~250px)

- **Tab bar**: filter events by scope
  - `[All]` — all events, no filter
  - `[Job: <short-uuid> ●]` — one tab per active/recent job, showing the first 8 chars of the job ID. Status indicator: `●` running, `✓` complete, `✗` had errors
- **Event log**: scrollable list of events
  - Each row: `timestamp | event_type | step | message`
  - Color-coded by `event_type` (see [Status System](#9-status-system))
  - Auto-scrolls to bottom. Pauses auto-scroll when user scrolls up (like any log viewer). Resumes when user scrolls back to bottom.
- **Clear button**: flushes the event buffer and resets tab selection
- **Drag handle**: top edge of panel, resize vertically (min 120px, max 500px)

#### Contextual Auto-Filtering

The bottom panel auto-selects a tab based on current page context:

| Current page | Auto-selected tab |
|---|---|
| `/search` | The most recent job tab (last job in event history) |
| `/businesses/:placeId` | The most recent job tab that has events matching this `place_id` |
| `/` (Dashboard) | "All" |
| `/businesses` | "All" |
| `/settings` | "All" |

User can always manually switch tabs to override the auto-filter. Manual selection resets when the auto-tab changes (e.g., navigating to a different page).

#### Implementation Notes

- The panel is a flex child of `AppLayout`, not `position: fixed` — the main content area and panel share the screen vertically
- Resize is implemented via custom mouse/touch event handlers (not shadcn `resizable`)
- Event buffer is capped at 200 events (existing behavior in WebSocket store)
- Events and active jobs are persisted to `sessionStorage` (key `webseed-ws-events`) so they survive page navigations
- Job labels use the first 8 characters of the job UUID (e.g., `"a1b2c3d4"`). Backend `JobResponse` does not yet include a human-readable label

---

## 3. Page: Login

No changes from current implementation. Simple form:
- API key input field
- Submit button
- Validates by calling `GET /businesses/stats` with the key
- On success: stores key in `localStorage`, redirects to `/`
- On failure: shows error message

---

## 4. Page: Dashboard

The command center. Answers three questions at a glance: Where are my businesses? What's running? What should I do next?

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Dashboard                                                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Pipeline Funnel                                              │
│  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐ │
│  │  47  │──→│  32  │──→│  24  │──→│  20  │──→│  15  │──→│  12  │ │
│  │search│   │enrich│   │genera│   │ test │   │deploy│   │email │ │
│  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘   └──────┘ │
│                                                               │
│  Errors: 4 (clickable)  ·  Opted Out: 3  ·  Total: 47       │
│                                     [New Search] [View Errors] │
│                                                               │
├───────────────────────┬──────────────────────────────────────┤
│  Active Jobs          │  Stats                                │
│                       │                                       │
│  ● Enrich (3 biz)    │  Total businesses:  47                │
│    running...         │  With sites:        15 (32%)         │
│                       │  Errors:             4 (8.5%)        │
│  ● Generate (2 biz)  │  Blacklisted:        3               │
│    running...         │                                       │
│                       │                                       │
│  (or: "No active      │                                       │
│   jobs" empty state)  │                                       │
└───────────────────────┴──────────────────────────────────────┘
```

### Components

#### Pipeline Funnel

- 6 nodes in a horizontal chain: Search → Enrich → Generate → Test → Deploy → Email
- Each node displays the **count** of businesses at that stable status
- Visual funnel effect: nodes can use decreasing intensity/width to show the narrowing
- **Running indicator**: if businesses are currently in a `running_*` status for a step, that node pulses/animates and shows a secondary label like "+3 running" below the count
- Nodes are **not clickable** (this is informational, not interactive)
- Data source: `GET /businesses/stats`
- Refetches on WebSocket `step_done` events

#### Summary Row

Below the funnel:
- **Errors: N** — clickable, navigates to `/businesses?status=errors`
- **Opted Out: N** — informational
- **Total: N** — total business count

#### Quick Action Buttons

Inline with the summary row (right side, wrapped on small screens):
- **New Search** — navigates to `/search`
- **View Errors** — navigates to `/businesses?status=errors`

#### Active Jobs Panel

Left column below the funnel:
- Reads from `useWebSocketStore` → `activeJobs` map
- Each active job shows: label (from `JobResponse`), current step, business count
- Subtle pulse animation on running jobs
- Empty state: "No active jobs" with muted text
- Clicking a job expands its tab in the bottom panel

#### Stats Panel

Right column below the funnel:
- Total businesses, businesses with sites (deployed+emailed), error count+percentage, blacklisted count
- Derived from `GET /businesses/stats` response
- Refetches on WebSocket `step_done` events

---

## 5. Page: Search

The discovery surface. This is the entry point of the workflow — find new leads, review them, decide which to invest in.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Search                                                       │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  [Location..........] [Query............] [Types ▼ multi]    │
│                                                               │
│  ▸ Advanced Options                                           │
│    Limit: [10]   Min Score: [0]   Grid Size: [3]             │
│                                                               │
│  [Search]                                                     │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Results (23 found)                         [Select All]      │
│                                                               │
│  ☐ │ Name              │ Category   │ ★    │ Reviews │ Addr  │
│  ──┼───────────────────┼────────────┼──────┼─────────┼───────│
│  ☑ │ Trattoria Nonna   │ restaurant │ 4.5  │ 127     │ Via…  │
│  ☑ │ Pizzeria Roma     │ pizza_rest │ 4.2  │ 89      │ Cor…  │
│  ☐ │ Bar Sport         │ bar        │ 3.1  │ 12      │ Pia…  │
│  ...                                                          │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  ░░░░░░░░░ Sticky action bar ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
│  3 selected          [Enrich Selected]  [Blacklist Selected]  │
└──────────────────────────────────────────────────────────────┘
```

### Search Form

A horizontal form bar at the top of the page. Three primary fields inline:

| Field | Type | Required | Notes |
|---|---|---|---|
| Location | Text input | Yes | e.g. "Milano, Italia" |
| Query | Text input | Yes | e.g. "ristorante" |
| Types | Multi-select dropdown | No (defaults to `[]`) | Grouped by category, displays as chips/tags when selected |

**Types Dropdown** — grouped multi-select with these categories:

| Group | Types |
|---|---|
| Food & Drink | restaurant, italian_restaurant, pizza_restaurant, meal_takeaway, meal_delivery, cafe, coffee_shop, bakery, bar, ice_cream_shop, sandwich_shop, seafood_restaurant, steak_house, sushi_restaurant, vegetarian_restaurant, breakfast_restaurant, brunch_restaurant, hamburger_restaurant, indian_restaurant, chinese_restaurant, japanese_restaurant, mexican_restaurant, thai_restaurant, mediterranean_restaurant, middle_eastern_restaurant, ramen_restaurant, fast_food_restaurant |
| Beauty & Wellness | hair_salon, beauty_salon, barber_shop, spa, nail_salon |
| Health | dentist, dental_clinic, doctor, physiotherapist, veterinary_care |
| Automotive | car_repair, car_wash, car_dealer |
| Accommodation | hotel, bed_and_breakfast, lodging, guest_house, motel, hostel |
| Fitness | gym, fitness_center |
| Retail | store, clothing_store, shoe_store, jewelry_store, pet_store, furniture_store, electronics_store, book_store, gift_shop, florist, pharmacy, hardware_store, bicycle_store, sporting_goods_store, convenience_store, liquor_store |
| Services | laundry, locksmith, plumber, electrician, roofing_contractor, moving_company, painter, real_estate_agency, travel_agency, insurance_agency, accounting, lawyer |

Display selected types as removable chips/tags below or inside the select.

**Advanced Options** — collapsible section (collapsed by default):

| Field | Type | Default | Notes |
|---|---|---|---|
| Limit | Number input | 10 | Max results to return |
| Min Score | Number input | 0 | Minimum pre-score (0-60) |
| Grid Size | Number input | 3 | Grid tiling density |

**Search Button**: Triggers `POST /pipeline/search`. On click:
1. Button shows loading/spinner state
2. Results stream in via WebSocket `progress` events during the search step
3. On `step_done`, search is complete — button resets
4. Bottom panel auto-filters to this job's tab

### Results Table

Appears after search completes. Columns:

| Column | Source | Sortable | Notes |
|---|---|---|---|
| Checkbox | — | No | For selection |
| Name | `name` | Yes | Business name |
| Category | `category` | No | Google Places primary type |
| Rating | `rating` | Yes | Star rating (numeric, e.g. "4.5") |
| Reviews | `reviews` | Yes | Review count |
| Address | `address` | No | Truncated with ellipsis |
| Pre-score | `lead_score` | Yes | 0-60 score from search stage |

Data source: `GET /businesses?status=searched` (fetch after search completes).

**Behavior**: The search page is ephemeral. Starting a new search replaces the previous results. Enriched businesses disappear from this view (they move to `enriched` status and appear on the Businesses page).

### Sticky Action Bar

Fixed to the bottom of the results area (above the global bottom panel). Appears when results exist.

| Element | Notes |
|---|---|
| Selection count | "3 selected" or "0 selected" |
| Select All / Deselect All | Toggle button |
| **Enrich Selected** | Primary action. Triggers `POST /pipeline/enrich` with selected `place_ids`. Disabled when 0 selected. |
| **Blacklist Selected** | Secondary/destructive action. Calls `POST /businesses/{place_id}/blacklist` for each selected. Confirmation dialog before executing. |

**After enrichment**: Toast notification "3 businesses enriched — View in Businesses" with a clickable link to `/businesses?status=enriched`.

---

## 6. Page: Businesses

The main working surface. A data table with smart filtering, sorting, searching, and context-aware bulk actions.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Businesses                                              [⋯] │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  [Search by name...                              ]           │
│                                                               │
│  [All (47)] [Enriched (12)] [Generated (8)] [Tested (5)]    │
│  [Deployed (3)] [Emailed (2)] [Errors (4)] [Opted Out (3)]  │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ☐ │ Name           │ Status       │ Error  │ Cat  │ ★   …  │
│  ──┼────────────────┼──────────────┼────────┼──────┼─────── │
│  ☐ │ Trattoria No…  │ 🟢 enriched  │        │ rest │ 4.5 …  │
│  ☐ │ Pizzeria Roma  │ 🟡 running…  │        │ pizz │ 4.2 …  │
│  ☐ │ Salon Bella    │ 🔴 err_gen   │ timeo… │ beau │ 4.8 …  │
│  ...                                                          │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  ░░░░ Sticky bulk action bar (on selection) ░░░░░░░░░░░░░░  │
│  5 selected (all enriched)                                    │
│  [▶ Generate]  ·  [Blacklist] [Delete]                       │
└──────────────────────────────────────────────────────────────┘
```

### Text Search

Client-side filter on business `name`. Simple `input` at the top. Filters the displayed rows in real-time as you type. No debounce needed since it's a local array filter.

### Status Filter Chips

Horizontal row of clickable badges, each showing status label + count:

- **All (N)** — no filter, shows total
- **Enriched (N)** — `status=enriched`
- **Generated (N)** — `status=generated`
- **Tested (N)** — `status=tested`
- **Deployed (N)** — `status=deployed`
- **Emailed (N)** — `status=emailed` + `status=email_queued`
- **Errors (N)** — groups all `error_*` statuses
- **Opted Out (N)** — `status=opted_out` (this is the blacklist view)

Active chip is visually highlighted. Counts come from `GET /businesses/stats`. Only show chips that have count > 0 (except "All" which always shows).

Note: `searched` businesses are intentionally not shown as a chip here. Searched businesses live on the Search page. If the user needs them, they can use the "All" filter.

### Table

| Column | Field | Sortable | Notes |
|---|---|---|---|
| Checkbox | — | No | For bulk selection |
| Name | `name` | Yes | Clickable — navigates to `/businesses/:placeId` |
| Status | `status` | No | Colored badge (see [Status System](#9-status-system)). Animated pulse for `running_*` |
| Error | `error_detail` | No | Shown only when non-empty. Truncated. Column stays narrow for happy-path rows |
| Category | `category` | No | Google Places primary type |
| Rating | `rating` | Yes | Numeric, e.g. "4.5" |
| Lead Score | `lead_score` | Yes | Numeric, 0-100 |
| City | `city` | No | Extracted from address |
| Maps | `maps_url` | No | Small external-link icon, opens Google Maps in new tab |

**Row click**: Navigates to `/businesses/:placeId` (the whole row is clickable except the checkbox column and the Maps link).

Data source: `GET /businesses` (optionally `?status=<filter>`). Refetches on WebSocket `step_done` events.

### Smart Bulk Action Bar

Sticky bar that appears when 1+ rows are selected. Shows selection count and **context-aware action buttons**.

#### Smart Action Logic

The bar analyzes the `status` of all selected businesses and shows the **next logical pipeline step** as the primary action:

| All selected are... | Primary action | API call |
|---|---|---|
| `enriched` | **Generate** | `POST /pipeline/generate` |
| `generated` | **Test** | `POST /pipeline/test` |
| `tested` | **Deploy** | `POST /pipeline/deploy` |
| `deployed` | **Email** | `POST /pipeline/email` |
| `error_enrich` | **Retry Enrich** | `POST /pipeline/enrich` |
| `error_generate` | **Retry Generate** | `POST /pipeline/generate` |
| `error_test` | **Retry Test** | `POST /pipeline/test` |
| `error_deploy` | **Retry Deploy** | `POST /pipeline/deploy` |
| `error_email` | **Retry Email** | `POST /pipeline/email` |
| Mixed statuses | Show all applicable action buttons, no single primary. The backend skips businesses in wrong status. |

Note: The backend's state machine enforces valid transitions. Each `run_*` function checks status and silently skips businesses in wrong state. So even with mixed selections, clicking "Generate" will only generate the `enriched` ones — the rest get `"skipped (status=xxx)"`.

#### Always-available actions (secondary)

- **Blacklist** — calls `POST /businesses/{place_id}/blacklist` for each. Confirmation dialog.
- **Delete** — calls `POST /businesses/hard-delete`. Confirmation dialog.

### Overflow Menu (⋯)

Top-right of the page header. Contains:
- **Export CSV** — triggers `GET /businesses/export/csv` download

---

## 7. Page: Business Detail

Deep dive on a single business. Shows all available data, pipeline status, and per-business actions.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  ← Businesses                                                 │
│                                                               │
│  Trattoria Nonna                           [Blacklist] [🗑]   │
│  🟢 enriched · italian_restaurant · ★ 4.5 (127 reviews)     │
│                                                               │
├── Pipeline ──────────────────────────────────────────────────┤
│                                                               │
│  [Search ✓]→[Enrich ✓]→[Generate]→[Test]→[Deploy]→[Email]   │
│                          ▲ current                            │
│                     [ ▶ Generate ]                            │
│                                                               │
├── Contact ───────────────┬── Scores ─────────────────────────┤
│  Address: Via Roma 1      │  Lead Score: 72/100               │
│  Phone: +39 02 1234       │  Rating: ★ 4.5 (127 reviews)     │
│  Email: info@trattoria.it │  Price Level: $$                  │
│  Maps: ↗ View on Maps     │                                   │
│                           │                                   │
├── Business Info ─────────┴───────────────────────────────────┤
│  Types: italian_restaurant, restaurant, food                  │
│  Business Status: OPERATIONAL                                 │
│  Opening Hours: Mon-Sat 12:00-23:00, Sun closed               │
│  Accepts Credit Cards: Yes                                    │
│  Editorial Summary: "A cozy family-run trattoria known for…" │
│                                                               │
├── Reviews ───────────────────────────────────────────────────┤
│  "Ottima pasta fatta in casa, servizio cordiale..."           │
│  "Best carbonara in the neighborhood, will come back"         │
│  "Ambiente accogliente, prezzi onesti per la zona"            │
│                                                               │
├── Site & Deployment ─────────────────────────────────────────┤
│  Vercel URL: ↗ https://trattoria-nonna.vercel.app            │
│  ┌─────────────────────────────┐                              │
│  │   [site screenshot thumb]   │                              │
│  └─────────────────────────────┘                              │
│  Email sent: 2026-03-16 14:30                                 │
│                                                               │
├── Testing ───────────────────────────────────────────────────┤
│  Iterations: 2                                                │
│  Issues: ▸ (collapsible list of test_issues)                  │
│                                                               │
├── Error ─────────────────────────────────────────────────────┤
│  Failed at: error_generate                                    │
│  Detail: Claude CLI timeout after 120s                        │
│  [Reset to enriched ▼]                                        │
│                                                               │
├── Metadata ──────────────────────────────────────────────────┤
│  Created: 2026-03-15 10:30   Updated: 2026-03-16 08:15       │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Header

- **Back link**: "← Businesses" — navigates to `/businesses`
- **Business name**: large, prominent
- **Status line**: colored status badge + `primary_type` + rating with review count, all inline
- **Action buttons** (top-right):
  - **Blacklist / Unblacklist** toggle (outline variant normally, default variant when opted_out)
  - **Delete** (destructive variant, with confirmation dialog)

### Pipeline Graph

Horizontal chain of 6 nodes: Search → Enrich → Generate → Test → Deploy → Email.

Node states:
- **Completed**: green fill, checkmark icon
- **Current / next**: highlighted border, node label emphasized
- **Running**: animated pulse, spinner icon (for `running_*` statuses)
- **Error**: red fill, X icon
- **Future**: grey/dimmed, no icon

Below the graph: **one primary action button** showing the next logical step.

| Current status | Button label | API call |
|---|---|---|
| `searched` | Enrich | `POST /pipeline/enrich` |
| `enriched` | Generate | `POST /pipeline/generate` |
| `generated` | Test | `POST /pipeline/test` |
| `tested` | Deploy | `POST /pipeline/deploy` |
| `deployed` | Email | `POST /pipeline/email` |
| `email_queued` / `emailed` | *(no button — pipeline complete)* | — |
| `error_*` | Retry [step] | Corresponding pipeline endpoint |
| `running_*` | *(disabled, shows "Running...")* | — |
| `opted_out` | *(no button)* | — |

Action fires with defaults from Settings (model, test_model, etc). One-click, no config popover.

### Info Sections (Cards)

All sections use **progressive disclosure** — sections only render when they have data. A `searched`-only business shows Contact + Pipeline. A fully `deployed` business shows everything.

#### Contact Card
| Field | Source | Notes |
|---|---|---|
| Address | `address` | Full address |
| Phone | `phone` | Clickable `tel:` link |
| Email | `email` | Clickable `mailto:` link |
| Maps | `maps_url` | External link icon, opens in new tab |

#### Scores Card
| Field | Source | Notes |
|---|---|---|
| Lead Score | `lead_score` | Display as "72/100" with a small progress bar |
| Rating | `rating` + `reviews` | Star display + review count |
| Price Level | `price_level` | Dollar signs or "N/A" |

#### Business Info Card (enrichment data)
Only shows when business has been enriched.

| Field | Source |
|---|---|
| Types | `types` — list of Google Place types as badges |
| Business Status | `business_status` |
| Opening Hours | `opening_hours_summary` |
| Accepts Credit Cards | `accepts_credit_cards` — Yes/No/Unknown |
| Editorial Summary | `editorial_summary` — italic quoted text |

#### Reviews Card
Only shows when `review_texts` is non-empty. Displays each review as a quoted block.

#### Site & Deployment Card
Only shows when `vercel_url` is non-empty.

| Field | Source | Notes |
|---|---|---|
| Vercel URL | `vercel_url` | Clickable external link |
| Email Sent | `email_sent_at` | Formatted datetime or "Not sent" |

> **Not yet implemented:** Screenshot thumbnail from `site_screenshot_path`. Requires backend static file serving endpoint.

#### Testing Card
Only shows when `test_iterations > 0`.

| Field | Source | Notes |
|---|---|---|
| Iterations | `test_iterations` | How many test-fix cycles ran |
| Issues | `test_issues` | Collapsible list. Each issue shows severity + description |

#### Error Card
Only shows when `error_detail` is non-empty.

| Field | Source | Notes |
|---|---|---|
| Failed at | `status` | The error status (e.g. "error_generate") |
| Detail | `error_detail` | The error message |
| Reset action | — | Dropdown to select a target status + "Reset" button. Uses `PATCH /businesses/{place_id}/status`. The backend has **no transition guards** on this endpoint — any valid `PipelineStatus` can be set. |

#### Metadata Card
| Field | Source |
|---|---|
| Created | `created_at` |
| Updated | `updated_at` |

### Data Source

`GET /businesses/{place_id}` — must return ALL fields (see [Backend Dependencies](#12-backend-dependencies)).

The pipeline graph status updates in real-time via WebSocket events matching this `place_id`. Refetch full business data on `step_done` or `step_error` events for this business.

---

## 8. Page: Settings

Two tabs: Prompts and Configuration.

### Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Settings                                                     │
├──────────────────────────────────────────────────────────────┤
│  [Prompts]  [Configuration]                                   │
│                                                               │
│  ── Prompts tab ────────────────────────────────────────────  │
│                                                               │
│  ▸ Site Generation (4 prompts)                                │
│  ▾ Code Review (2 prompts)                     [2 unsaved]   │
│    ┌─ prompt.code_review ──────────────────────────────────┐ │
│    │  (markdown-highlighted textarea)                       │ │
│    │  ...prompt template content...                         │ │
│    │                                                [Save]  │ │
│    └────────────────────────────────────────────────────────┘ │
│    ┌─ prompt.code_review_system ───────────────────────────┐ │
│    │  ...system prompt content...              ● unsaved    │ │
│    │                                                [Save]  │ │
│    └────────────────────────────────────────────────────────┘ │
│  ▸ Visual Test (2 prompts)                                    │
│  ▸ Fix HTML (2 prompts)                                       │
│  ▸ Email Generation (2 prompts)                               │
│                                                               │
│  ── Configuration tab ──────────────────────────────────────  │
│                                                               │
│  ┌────────────────────┬─────────────────┬────────┐           │
│  │ Key                │ Value           │        │           │
│  ├────────────────────┼─────────────────┼────────┤           │
│  │ contact_email      │ [ed@webseed.it] │ [Save] │           │
│  │ sender_name        │ [Edoardo      ] │ [Save] │           │
│  │ default_model      │ [sonnet       ] │ [Save] │           │
│  │ test_model         │ [sonnet       ] │ [Save] │           │
│  │ max_fix_iterations │ [3            ] │ [Save] │           │
│  │ gmail_label_name   │ [webseed-queue] │ [Save] │           │
│  │ max_photos         │ [3            ] │ [Save] │           │
│  │ timeout_generate   │ [120          ] │ [Save] │           │
│  │ timeout_test       │ [120          ] │ [Save] │           │
│  │ timeout_email      │ [180          ] │ [Save] │           │
│  └────────────────────┴─────────────────┴────────┘           │
│                                                               │
│  Description shown below each field when focused              │
└──────────────────────────────────────────────────────────────┘
```

### Prompts Tab

**Grouped by pipeline step** (not a flat list):

| Group | Prompts |
|---|---|
| Site Generation | `prompt.site_gen`, `prompt.site_gen_system`, `prompt.site_gen_photos`, `prompt.site_gen_no_photos` |
| Code Review | `prompt.code_review`, `prompt.code_review_system` |
| Visual Test | `prompt.visual_test`, `prompt.visual_test_system` |
| Fix HTML | `prompt.fix_html`, `prompt.fix_html_system` |
| Email Generation | `prompt.email_gen`, `prompt.email_gen_system` |

Each group is a **collapsible section** (using shadcn `Collapsible`). Group header shows name + prompt count + unsaved indicator (e.g. "[2 unsaved]").

Each prompt within a group:
- **Label**: the key name (e.g. `prompt.code_review`)
- **Description**: from the `description` field in the settings API
- **Textarea**: with **markdown syntax highlighting** for editing
- **Unsaved indicator**: dot or badge when content differs from saved value
- **Save button**: per-prompt, calls `PUT /settings/{key}`

Data source: `GET /settings?prefix=prompt`

### Configuration Tab

Simple table with inline editing:
- **Key**: display name (strip `config.` prefix, replace `_` with spaces, title case)
- **Value**: `<Input>` for editing
- **Save button**: per-row, calls `PUT /settings/{key}`
- **Description**: shown below the input when focused (from `description` field)
- **Dirty indicator**: visual cue when value differs from saved

Data source: `GET /settings?prefix=config`

---

## 9. Status System

### Status Colors

Consistent color scheme used across all pages (badges, pipeline nodes, table rows).

| Status Category | Statuses | Color | Badge Variant | Notes |
|---|---|---|---|---|
| Stable (completed) | `searched`, `enriched`, `generated`, `tested`, `deployed`, `email_queued`, `emailed` | Green | `default` (green bg) | Solid badge |
| Running | `running_enrich`, `running_generate`, `running_test`, `running_deploy`, `running_email` | Blue | `default` (blue bg) | **Animated pulse** |
| Error | `error_enrich`, `error_generate`, `error_test`, `error_deploy`, `error_email`, `error_run` | Red | `destructive` | Solid badge |
| Blacklisted | `opted_out` | Grey | `secondary` | Muted |

### Pipeline Node Colors (for funnel and detail page graph)

| State | Fill | Border | Icon |
|---|---|---|---|
| Completed | Green fill | Green border | ✓ checkmark |
| Running | Blue fill, pulsing | Blue border | Spinner |
| Error | Red fill | Red border | ✗ |
| Current (next step) | White/transparent | Highlighted border | None |
| Future | Grey fill (very light) | Grey border (muted) | None |

### WebSocket Event Colors (for bottom panel log)

| Event Type | Color |
|---|---|
| `step_start` | Blue |
| `progress` | Default (inherit) |
| `step_done` | Green |
| `step_error` | Red |
| `cost` | Amber |
| `job_complete` | Green (bold) |

---

## 10. WebSocket Integration

### Connection Lifecycle

Same as current: `AuthGuard` calls `connect(apiKey)` on mount, `disconnect()` on unmount. Exponential backoff reconnect (1s → 30s cap).

### Store Shape

```
{
  isConnected: boolean
  events: PipelineEvent[]          // capped at 200, persisted to sessionStorage
  activeJobs: Map<string, ActiveJob>

  connect(apiKey): void
  disconnect(): void
  clearEvents(): void
}

ActiveJob {
  jobId: string
  startedAt: string
  currentStep?: string
}
```

The WebSocket singleton lives outside the Zustand store (module-level variable) to avoid React Strict Mode double-connection issues. State is persisted to `sessionStorage` (key `webseed-ws-events`) so events and active jobs survive page navigations within the same session.

### Refetch Strategy

Components that display server data should refetch when relevant WebSocket events arrive:

| Component | Trigger | Action |
|---|---|---|
| Dashboard funnel + stats | Any `step_done` event | Refetch `GET /businesses/stats` |
| Businesses table | Any `step_done` event | Refetch `GET /businesses` |
| Business detail | `step_done` or `step_error` with matching `place_id` | Refetch `GET /businesses/{place_id}` |
| Search results | `step_done` for search job | Fetch `GET /businesses?status=searched` |

Use TanStack Query's `queryClient.invalidateQueries()` to trigger refetches, rather than manual `refetch()` calls in each component. This centralizes the invalidation logic.

### Event Filtering (for bottom panel)

All filtering is client-side on the existing event buffer:

- **By job**: `events.filter(e => e.job_id === selectedJobId)`
- **By business**: `events.filter(e => e.place_id === selectedPlaceId)`
- **All**: no filter

---

## 11. Data Typing Strategy

### Current State

Manual TypeScript interfaces are defined in `frontend/src/types/index.ts`. Orval generates hooks and model types from `openapi.json`, but the generated models use `Record<string, unknown>` because the backend lacks typed Pydantic response models.

**Known limitation:** Components bypass both manual types and Orval types, casting API responses through `as Record<string, unknown>` or `as never` to access fields. This is a type-safety gap — runtime errors from missing/renamed fields won't be caught at compile time.

### Goal (not yet achieved)

1. **Backend**: Add Pydantic response models (`BusinessSummary`, `BusinessDetail`, `StatsResponse`, `SettingItem`) to all endpoints. This produces typed OpenAPI schemas.
2. **Frontend**: Regenerate Orval hooks after backend change. Orval produces real TypeScript interfaces.
3. **Frontend**: Remove all `as never`, `as Record<string, unknown>` casts. Use the generated types directly.
4. **Frontend**: All components consume typed data — missing fields are caught at compile time by TypeScript strict mode.

### Key Interfaces (defined in `frontend/src/types/index.ts`)

```typescript
interface BusinessSummary {
  id: string
  place_id: string
  name: string
  address: string
  category: string
  rating: number
  reviews: number
  lead_score: number
  status: string
  error_detail: string
  vercel_url: string
  primary_type: string | null
  created_at: string
  updated_at: string
}

interface BusinessDetail {
  id: string
  place_id: string
  name: string
  address: string
  phone: string | null
  email: string
  rating: number
  reviews: number
  category: string
  maps_url: string
  has_photos: boolean
  photo_paths: string[]
  photo_refs: string[]
  fallback_unsplash_url: string
  lead_score: number
  price_level: string | null
  business_status: string
  primary_type: string | null
  types: string[] | null
  has_opening_hours: boolean
  opening_hours_summary: string | null
  accepts_credit_cards: boolean | null
  editorial_summary: string | null
  review_texts: string[] | null
  status: string
  error_detail: string
  vercel_url: string
  site_screenshot_path: string
  email_sent_at: string
  test_iterations: number
  test_issues: Record<string, unknown>[]
  run_id: string
  created_at: string
  updated_at: string
}

interface StatsResponse {
  [status: string]: number  // e.g. { searched: 5, enriched: 3, total: 47 }
}

interface SettingItem {
  key: string
  value: string
  description: string
  updated_at: string
}

interface JobResponse {
  job_id: string
}

interface PipelineEvent {
  event_type: 'step_start' | 'step_done' | 'step_error' | 'progress' | 'cost' | 'job_complete'
  job_id: string
  step: 'search' | 'enrich' | 'generate' | 'test' | 'deploy' | 'email'
  place_id?: string       // optional — not all events target a specific business
  message: string
  data?: Record<string, unknown>  // optional — only present on some event types
  timestamp: string
}
```

---

## 12. Backend Dependencies

Changes needed in the backend to improve frontend functionality.

### Unresolved

| Change | Why | Priority |
|---|---|---|
| **Typed Pydantic response models** | Orval generates `Record<string, unknown>` without them. Frontend works around this with `as Record<string, unknown>` casts, but loses type safety. | High |
| **JobResponse enhancement** | Bottom panel shows truncated UUIDs as job labels. Adding a human-readable `label` field (e.g., "Search: ristoranti, Milano") and `step` field to the response would improve UX. | Medium |
| **Static file serving for screenshots** | Business detail page could show a site thumbnail from `site_screenshot_path`, but backend doesn't serve static files from `results/` | Low |
| **Aggregate stats endpoint** | Dashboard avg lead score, avg rating, time-based metrics | Low |

### Resolved

| Change | Status |
|---|---|
| Business detail endpoint: expose all fields | Done — all enrichment data, test data, screenshot path, email_sent_at available |
