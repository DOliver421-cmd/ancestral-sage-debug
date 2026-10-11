# TIER BASELINE

**Date:** 2026-10-11
**Status:** LIVE BASELINE — generated from the code, not from memory
**Sources of truth:** `backend/security/feature_control.py` (`FEATURE_MIN_TIER`, `FEATURE_API_PATHS`) · `frontend/src/lib/tiers.js` (`TIER_FOR_FEATURE`) · `frontend/src/App.js` (route gates) · `frontend/src/lib/originalTools.js` (per-tool gates)
**Owner decisions incorporated:** 2026-10-11 (Creator Studio is a paid member feature; module content is Plus; the Soup requires registration with per-file tiers; no anonymous file downloads)

This document is the moving-forward baseline: it states what each tier is and what it can reach, and it is regenerated whenever a tier decision changes. If the code and this file disagree, **the code wins and this file is regenerated in the same commit.**

---

## 1. THE TIERS

| Tier | Rank | Price | What it is |
|---|---|---|---|
| `free` | 0 | $0 | An anonymous or signed-in account with no subscription. |
| `member` | 1 | **$9/mo** | The paid entry tier. The "$0 doorway" Academy stays free; everything that costs the platform resources starts here. |
| `plus` | 2 | **$15/mo** | The full platform: the complete Creator Studio, published content, the Resource Hub. |
| `pro` | 3 | — | Business tools (artist management), the video studio. |
| `patron` | 4 | — | Mass posting. |
| `executive` | 5 | — | Owner/executive surfaces. Never a purchase tier. |

Roles are a separate axis (`public` → `student` → `trial_pass` → `instructor` → `support_staff` → `oversight` → `admin` → `executive_admin`); see `BUSINESS_ACCESS_POLICY.md`. A tier gate never overrides a role gate.

**Anonymous visitors (not signed in) reach: the marketing pages, the course *catalogue listing*, `/api/health`, and nothing else.** Module content, progress, labs, credentials, the Resource Hub, all file downloads, and the entire Soup are behind an account.

## 2. WHAT EACH TIER REACHES

### Free (signed-in) — $0
| Surface | Gate |
|---|---|
| Profile, dashboard, navigation | login |
| Academy (courses, projects, portfolio, compliance, records) | login — **the "$0 doorway" is free and stays free** |
| Curriculum catalogue listing (`/api/modules`, `/curriculum`) | `curriculum: free` |
| The Soup: Confusion Engine, SEE Through Black | `soup: free` (registration required — the Soup has no anonymous entry) |
| Studio | **none** — the Creator Studio is a paid $9 feature |

### Member — $9/mo
| Surface | Gate |
|---|---|
| AI chat | `ai_chat` (see §4 drift) |
| Posts, Lounge, Projects | `posts` / `lounge` / `projects`: member |
| **Creator Studio: Beat sequencer + Keys** | `studio: member` |
| **The Soup manual, pantheon, games, training, the 60 tactics, the calendar** | `soup_manual: member` |
| Module content, progress, labs, credentials | **`courses: plus` — this tier does NOT reach them** |

### Plus — $15/mo
| Surface | Gate |
|---|---|
| Module **content**, progress, labs, credentials | `courses: plus` |
| **Creator Studio: Song Arrangement + Publish** (the full studio) | `studio_full: plus` |
| Track sequencing, Band, Publisher, Earnings, Payouts | `tracks` / `band` / `publisher` / `earnings` / `payouts`: plus |
| **The Soup production suite** — Broadcast/patronage hub, Sovereign Distribution Cockpit, Publisher Empire, Media Strategist, Autonomous Partner, Suno masterclass, Prompt Architect workshop | `soup_full: plus` |
| Resource Hub (templates, guides, workflows) | `resource_hub: plus` |

### Pro / Patron / Executive
`artist_mgmt: pro`, `mass_post: patron`, `sovereign: executive` (the Sovereign puzzle engine and chat remain executive-only — see OPEN ITEMS).

## 3. THE SOUP — per-file gate (owner decision 2026-10-11)

Registered in `frontend/src/lib/originalTools.js`, enforced in `frontend/src/pages/LegacyTool.jsx` at `/classic/:slug` **before the iframe exists**, and surfaced as a badge in `ClassicTools.jsx`.

| File | Tier |
|---|---|
| Confusion Engine, SEE Through Black | `soup` — free for any signed-in member |
| Founder's Manual, Pantheon, Games, Training, 60 Tactics, Calendar, Index | `soup_manual` — $9 member |
| Broadcast/Patronage, Distribution Cockpit, Publisher, Media Strategist, Autonomous Partner, Suno, Prompt Architect | `soup_full` — $15 plus |

**The Soup files are byte-for-byte untouched.** They ship from `frontend/public/mini-more-help-center/` (verbatim copies — the repo-root originals are not served by the build, which is why the Soup was unreachable). The Confusion Engine's game design is intentional and must not be condensed.

## 4. OPEN ITEMS (drift and undecided)

1. **`ai_chat` drift — code disagrees with itself.** `frontend/src/lib/tiers.js` says `member`; `backend/security/feature_control.py` says `free`. The backend is what enforces an API call, so an anonymous caller can reach the AI chat endpoint today while the UI implies Member. **This needs one decision** (the owner stated "very limited AI" for anonymous, paid above that — the exact boundary is not yet encoded).
2. **Backend map has no Soup keys** — deliberate: the Soup has no `/api` surface, and `test_tier_map_mirrors_frontend_contract` requires every backend key to map one. Its contract lives in the frontend map where its gate is.
3. **The Sovereign puzzle engine and `/api/sovereign/chat` are still `executive`** in the backend while the owner's model places paid game surfaces in the paid tiers. Awaiting the tier decision.
4. **`/api/*` unknown paths return 200 HTML** (the SPA catch-all). Owner-approved decision #3 to enforce JSON 404/405 — not yet implemented.
5. **The Soup's partner chat has no backend.** `partner-chat.html` calls `/api/partner`, `/api/config`, `/api/memory`, `/api/upload`, `/api/report` — served today by an orphaned `Mini More Help Center/server.js` that the platform never runs. Porting those five routes is the remaining step for that file to be real.
6. **`Suno 202 workshop series2.html` references `rule_90211.mp3`, which exists nowhere in the repo.** A pre-existing broken reference in the original file; the file was not modified.

## 5. PLAN PHASE STATUS (docs/WORKING_PLAN.md)

| Phase | Task | State |
|---|---|---|
| **0** | R1 Legal Engine account sync | **Merged & live** — 201/200 verified |
| **0** | R2 Enrollment atomicity | **Merged** — 8→0 races |
| **0** | R3 Artifact atomicity | **Merged** — 6→0 races |
| **0** | R4 NAM seed on real DBs | **Merged & live** — health check reports 31 skipped/0 failed |
| **0** | R5 In-product guides | **Merged** — verbatim guides + idempotent upsert |
| **0** | R6 Creator Studio at Plus | **Implemented** — `studio: member`, `studio_full: plus`, owner's tier model |
| **0** | R7 Resource Hub tier | **Implemented** — `resource_hub: plus`, handler truth is Member for read |
| **0** | R8 JSON 404/405 for `/api/*` | **NOT IMPLEMENTED** — owner-approved, open item 4 |
| **0** | R9 PipelineManager import | **Merged** — dead import removed, honest 503 |
| **0** | R10 Loud seed failures | **Merged & live** |
| **0** | G0 Structural hygiene | **Merged** — Anthropic removed, indexes, api_keys split, nav, Refresh |
| **0** | G1 Real revocation | **Merged** — call-time key resolution + eviction |
| **1** | Simulation Lab fixes | **Merged** — engine staleness, lesson ordering, analytics envelope |
| **1** | API key gateway (G2–G7) | **Not started** — design in `docs/API_KEY_GATEWAY_PLAN.md` |
| **2–3** | Depth + monetisation (R11–R17) | **Not started** |
| **New** | The Soup (registration + per-file tiers) | **Implemented** — this PR |
