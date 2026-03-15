# WebSeed — Complete Product Review

*Review date: 2026-03-10*

## What This Is

WebSeed is a lead-gen pipeline for Italian local businesses without websites. It scrapes Google Maps, generates a free site with AI, deploys it, then cold-emails the business owner with a link and a price tag (€299 + €9/mo). The bet: seeing a real, deployed site for their business is compelling enough to convert.

This is a clever approach. The "show, don't tell" strategy of building the site *before* the pitch is the core differentiator. Let's evaluate where this product stands and where it should go.

---

## 1. WHAT WORKS WELL

### Strong foundations
- **Clean architecture**: ~2,700 LOC, well-separated modules, externalized prompts, status-based resumability. The codebase is lean and readable.
- **Smart search**: Two-stage discovery + enrichment, grid tiling, lead scoring (0-100 on 8 signals), cost safeguards (max 100 detail calls). This is thoughtful engineering.
- **Atomic operations**: Graceful CTRL-C, atomic file writes, per-business error isolation. Production-minded.
- **Type safety**: pyright strict mode with 0 errors. Unusual discipline for a solo project.
- **Cost efficiency**: $0.07-0.70 per business end-to-end. Remarkably cheap unit economics.

### The pitch mechanics
- Site is already live when the email arrives — removes the "imagination gap"
- Single-file HTML with inline everything — zero-config Vercel deploy, no build step
- Email screenshot gives an instant visual hook in the inbox

---

## 2. CRITICAL PROBLEMS

### P0: No email addresses
Google Maps doesn't provide email addresses. This is the single biggest blocker. You can generate perfect sites and emails, but if there's no `To:` field, the pipeline stops. The TODO mentions Hunter.io/Apollo/scraping, but this is not an "enhancement" — it's the missing link that makes the entire automation work end-to-end. Without it, every business requires manual email lookup, which kills the scalability thesis.

**Options:**
- Hunter.io/Apollo API integration (cost per lookup, but automatable)
- Scrape Google Maps listing for social links → find email from Facebook/Instagram pages
- Google Custom Search for `"business name" + "city" + "@" + email`
- Manual `webseed set-email` command as interim (you already suggested this)
- Accept that some manual effort is needed and optimize the workflow around it

### P1: Unsplash fallback is dead
`source.unsplash.com` is deprecated. Businesses without Maps photos get broken image fallbacks. This directly impacts site quality for a meaningful chunk of leads. Needs an alternative (Unsplash API, Pexels API, or just handle the no-photo case gracefully in the HTML template).

### P2: No tracking or analytics
You have zero visibility into what happens after the email is sent:
- Did they open the email?
- Did they click the site link?
- Did they visit the deployed site?
- How long did they spend on it?

Without this, you can't iterate on what works. You're flying blind on conversion. At minimum: add a simple analytics snippet (Plausible/Umami — privacy-friendly, no cookie banner needed) to generated sites, and consider email open tracking via a pixel.

### P3: Legal gray area
Cold-emailing businesses with sites built from their Google Maps data (photos, name, address) without consent sits in a legal gray zone, especially under GDPR/Italian privacy law. The tiny footer disclaimer ("Dati raccolti da Google Maps") is insufficient. You need:
- Clear opt-out mechanism in every email
- Data processing basis (legitimate interest is arguable but needs documentation)
- Site takedown on request (you have `hard-delete` but the email doesn't mention it)
- Consider: the photos are Google's, used on a site you're selling. Licensing?

---

## 3. PRODUCT GAPS

### No follow-up system
The pipeline ends at `email_queued`. There's no:
- Follow-up email after N days of no response
- Reminder with updated site or seasonal content
- Status tracking for responses (interested / not interested / no reply)
- CRM-like pipeline view (lead → contacted → interested → client → churned)

The `emailed` status exists but is never set. The real funnel is: email sent → opened → clicked → responded → converted. You track none of this.

### No client onboarding flow
What happens when someone says "yes"? There's no:
- Payment collection (Stripe link?)
- Custom domain setup workflow
- Content revision process (they'll want changes)
- Handoff from "demo site" to "production site"
- Ongoing maintenance/hosting management

### Sites are static snapshots
Generated sites are frozen at creation time. If a business changes hours, phone, or gets new reviews, the site is stale. There's no update mechanism. For a paid service (€9/mo for "mantenimento"), customers will expect the site to reflect reality.

### No competitive differentiation in the site itself
The generated HTML is decent but generic. Every restaurant gets the same 6-section template. There's no:
- Menu/price list integration
- Booking widget (even a simple `tel:` link is basic)
- Social media feeds
- Seasonal content or specials
- Multi-language support (tourist areas need English)

### Single-market limitation
Everything is hardcoded for Italy: prompts in Italian, € pricing, Italian cultural context. The architecture doesn't support other markets without duplicating all prompts.

---

## 4. TECHNICAL DEBT & IMPROVEMENTS

### No test suite
Zero automated tests. For a pipeline that handles money-adjacent operations (sending emails to real businesses, deploying to production), this is risky. At minimum:
- Unit tests for `store.py` (upsert logic, blacklist merging)
- Unit tests for `maps.py` (lead scoring, grid tiling, dedup)
- Integration test for the generate → test → fix loop
- Snapshot tests for prompt templates

### pipeline.py is too big (1,114 lines)
This file is the CLI parser, orchestrator, prompt loader, identifier resolver, and output formatter all in one. It should be split:
- CLI parsing → `cli.py`
- Orchestration logic → keep in `pipeline.py`
- Output formatting (tables, CSV export) → `formatters.py`

### Claude CLI coupling
The entire AI layer depends on the Claude Code CLI subprocess. This means:
- No programmatic error handling (parse stdout/stderr)
- No streaming or progress indication
- No token usage tracking
- 180s hard timeout with no visibility into what's happening
- If Claude Code CLI changes its output format, everything breaks

Consider migrating to the Claude API directly for generation/testing/email. Keep CLI for Playwright MCP only (where tool use is needed).

### TinyDB scalability
TinyDB is fine for hundreds of businesses. At thousands, it'll slow down (full file read/write on every operation). Not urgent, but worth noting if the product scales.

### Vercel single-project model
All sites under one Vercel project. Vercel free tier has limits (bandwidth, builds). At scale, you'll hit them fast. No monitoring for this currently.

---

## 5. WHERE THE PRODUCT SHOULD GO

### Phase 1: Make the current pipeline actually work end-to-end
- **Fix email addresses** (P0) — even a semi-manual solution unblocks everything
- **Fix Unsplash fallback** (P1) — or handle no-photo gracefully
- **Add basic site analytics** (P2) — know if anyone visits
- **Clean up legal posture** (P3) — opt-out link, better disclaimer
- **Run it on 50 real businesses** and measure: how many emails bounce, how many sites get visited, how many responses

### Phase 2: Close the conversion loop
- Add follow-up email system (day 3, day 7, day 14)
- Add response tracking (manual at first: `webseed mark-responded PLACE_ID`)
- Add payment link (Stripe) in email or follow-up
- Build a simple dashboard: businesses by status, click-through rates, response rates
- Define the onboarding flow: what happens when they say yes

### Phase 3: Improve the product (sites)
- Better templates per category (restaurant ≠ plumber ≠ salon)
- Vue.js/Tailwind migration for better PageSpeed scores
- Dynamic content: pull live reviews, hours from Maps API periodically
- Booking/contact form integration
- PageSpeed Insights as a quality gate

### Phase 4: Scale
- Multi-city automated search campaigns
- A/B test email templates
- Multi-language support (for tourist areas, or to expand beyond Italy)
- Consider: is this a tool you use, or a SaaS others use too?

---

## 6. THE FUNDAMENTAL QUESTION

WebSeed's value proposition is: "I'll build you a website before you even ask for one, and it'll be so good you'll want to pay for it."

The risk is that **businesses without websites often don't want one**. They may be:
- Intentionally offline (cash-only, word-of-mouth, old-school)
- Already using Instagram/Facebook as their web presence
- Not the decision-maker you're emailing
- Suspicious of unsolicited emails with "your site is ready"

The lead scoring helps filter for "likely to want a site" but doesn't solve the demand-side question. Before over-investing in pipeline quality, the most important thing is to **run 50-100 real emails and measure the response rate**. If it's <1%, the problem isn't the code — it's the business model. If it's 3-5%, you have something worth scaling.

---

## Summary

| Area | Status | Priority |
|------|--------|----------|
| Email address acquisition | Blocked | P0 |
| Unsplash fallback broken | Broken | P1 |
| Analytics / tracking | Missing | P2 |
| Legal compliance | Insufficient | P3 |
| Follow-up system | Missing | High |
| Test suite | Missing | Medium |
| Site quality / templates | Basic | Medium |
| Client onboarding flow | Missing | Medium (after first sale) |
| Scalability (TinyDB, Vercel) | Fine for now | Low |
| Multi-market | Not supported | Low (validate Italy first) |
