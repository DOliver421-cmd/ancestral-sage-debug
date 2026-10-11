# TIER BASELINE

**Date:** 2026-10-11
**Status:** LIVE BASELINE — generated from the code, not from memory
**Sources of truth:** `backend/security/feature_control.py` (`FEATURE_MIN_TIER`, `FEATURE_API_PATHS`) · `frontend/src/lib/tiers.js` (`TIER_FOR_FEATURE`) · `frontend/src/App.js` (route gates) · `frontend/src/lib/originalTools.js` (per-tool gates)
**Owner decisions incorporated:** 2026-10-11 (Creator Studio is a paid member feature; module content is Plus; the Soup requires registration with per-file tiers; no anonymous file downloads; AI chat is Member+ or BYOK; the daily puzzle is free; the Soup's bytes are gated server-side with a scoped session cookie; unknown `/api/*` paths answer JSON 404)

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

**Every gate in this file is editable from the exec console, for real.** `POST /api/exec/control/authz-matrix` writes `db.authz_matrix`; `security/feature_control.load_feature_tier_requirements()` and `load_soup_tier_requirements()` read it back on every request, so an edit changes what the next request encounters — no redeploy, no code change. The console UI (`frontend/src/pages/ExecBusinessOffice.jsx` / `ExecControlPanel.jsx`) reads that same endpoint and writes it back with an audit reason. The `AUTHZ_FEATURES` list in `routers/exec_control.py` is the editable surface, and a test (`test_every_enforced_feature_is_exec_editable`) fails if any enforced gate is missing from it — a gate nobody can edit is a lock nobody holds the key to. Roles and per-user tiers are edited through `/api/exec/control/user/role` and `/api/exec/control/user/tier`; both write the user document, bump `token_version` (revoking old JWTs), delete sessions, and are audit-logged.

**Anonymous visitors (not signed in) reach: the marketing pages, the course *catalogue listing*, `/api/health`, and nothing else.** Module content, progress, labs, credentials, the Resource Hub, all file downloads, and the entire Soup are behind an account.

## 2. WHAT EACH TIER REACHES

### Free (signed-in) — $0
| Surface | Gate |
|---|---|
| Profile, dashboard, navigation | login |
| Academy (courses, projects, portfolio, compliance, records) | login — **the "$0 doorway" is free and stays free** |
| Curriculum catalogue listing (`/api/modules`, `/curriculum`) | `curriculum: free` |
| The Soup: Confusion Engine, SEE Through Black | `soup: free` (registration required — the Soup has no anonymous entry) |
| The daily puzzle / partnership points (on the free StudentDashboard) | `puzzles: free` — public to view; points require login |
| AI chat | **NOT free** — `ai_chat: member` (§4, resolved 2026-10-11). The keyword knowledge-base Helper (`/api/ai/helper`) stays free for every signed-in account |
| Studio | **none** — the Creator Studio is a paid $9 feature |

### Member — $9/mo
| Surface | Gate |
|---|---|
| AI chat | `ai_chat: member` — or an active BYOK key (the same contract `/ai/chat` applies in `routers/ai.py:_ai_chat_access`; staff roles bypass) |
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
`artist_mgmt: pro`, `mass_post: patron`, `sovereign: executive` (the Sovereign chat + pipeline; also role-gated `executive_admin`). The daily **puzzle** was split out of this feature on 2026-10-11 and is `free` — it ships on the free StudentDashboard.

## 3. THE SOUP — per-file gate (owner decision 2026-10-11, server-side enforcement added same day)

Registered in `frontend/src/lib/originalTools.js`, mirrored in `backend/security/feature_control.py` (`SOUP_FILE_FEATURES` / `SOUP_MIN_TIER`), enforced **server-side on the bytes** by `backend/security/soup_gate.py` on the `/mini-more-help-center/` prefix, and mirrored a third time in the React launcher (`frontend/src/pages/LegacyTool.jsx` at `/classic/:slug`, plus the badge in `ClassicTools.jsx`).

| File | Feature | Tier |
|---|---|---|
| Confusion Engine, SEE Through Black | `soup` | any signed-in account |
| Founder's Manual, Pantheon, Games, Training, 60 Tactics, Calendar, Index | `soup_manual` | $9 member |
| Broadcast/Patronage, Distribution Cockpit, Publisher, Media Strategist, Autonomous Partner, Suno, Prompt Architect | `soup_full` | $15 plus |
| `hub_client.js`, `rule_90211.mp3` (assets the `soup_full` pages load) | `soup_full` | $15 plus |

**Enforcement is real, not decorative.** A raw file URL now answers 401 (anonymous), 403 (wrong tier), or 404 (file not in the map) — verified live: anonymous `401 JSON`, free account `403 JSON` on `soup-broadcast.html`, cookie session `200` with the real 37,687-byte file for `soup-confusion.html`. Unknown files under the prefix are a 404 that never confirms what exists.

**Authentication.** The app has no cookie auth, and the Soup's pages cannot send an `Authorization` header: an iframe's document navigation cannot carry it, and `soup-partner.html`'s own `fetch()` calls send none (the files are read-only content and must not be edited to add one). Login/register therefore also issue the **same JWT in an httpOnly, SameSite=Lax `lce_session` cookie** (`security/session_cookie.py`), accepted **only** by the Soup byte gate and the five partner routes — the header remains the one auth mechanism for the rest of `/api`.

**Owner/executive are never locked out.** `admin` and `executive_admin` bypass every Soup tier and every feature tier (`TIER_EXEMPT_ROLES`), exactly as they bypass `/api` gates.

**The Soup files are byte-for-byte untouched.** They ship from `frontend/public/mini-more-help-center/` (verbatim copies — the repo-root originals are not served by the build, which is why the Soup was unreachable). The Confusion Engine's game design is intentional and must not be condensed.

## 4. RESOLVED 2026-10-11 (was OPEN ITEMS)

All five items that were open on the morning of 2026-10-11 were decided and shipped the same day. The outcomes, and where each rule now lives:

1. **`ai_chat` tier — RESOLVED: `member`.** The three locations now agree (`feature_control.feature_control` `FEATURE_MIN_TIER["ai_chat"] = "member"`, `frontend/src/lib/tiers.js`, and the `/ai/chat` handler's own guard). Two carve-outs keep the enforceable contract honest: an **active BYOK key** satisfies the member requirement, and the **keyword knowledge-base Helper** (`/api/ai/helper`, zero LLM cost, documented to serve anonymous and authenticated visitors) stays free for every signed-in account. Anonymous callers never reach the LLM surfaces anyway — those handlers require a session.
2. **Soup keys in the backend map — RESOLVED: they now exist.** `SOUP_FILE_FEATURES` / `SOUP_MIN_TIER` in `security/feature_control.py`, enforced by `security/soup_gate.py`. They live beside `FEATURE_MIN_TIER`, not inside it, because the mirror test requires every `FEATURE_MIN_TIER` key to own an `/api` prefix — the Soup's contract is the prefix gate, not an API surface.
3. **Sovereign/puzzles split — RESOLVED.** `puzzles` is its own **free** feature (`/api/puzzles/*`): the card ships on the free StudentDashboard and the handler contract is "public to view; points require login". `sovereign` (`/api/sovereign/*` chat + pipeline) stays `executive` and is additionally role-gated `executive_admin`. Before the split, every signed-in free account got a 403 on puzzles and the dashboard card silently rendered nothing.
4. **`/api/*` unknown paths — RESOLVED: JSON 404.** A `/api/{full_path:path}` catch registered after every real route answers `404 {"detail":"Not Found"}` for any verb. Verified live: `GET` and `POST` on an unknown `/api` path both return `application/json`, and the SPA catch-all no longer serves HTML to an API probe. Real routes keep FastAPI's native JSON 405 for a wrong verb on a path that exists.
5. **The Soup's partner API — RESOLVED: ported.** `backend/routers/soup_partner.py` serves `/api/partner`, `/api/config`, `/api/memory`, `/api/upload`, `/api/report`. Access is the member AI contract (staff, or member+, or active BYOK); answers come from the platform `llm_gateway`; memory/uploads/config persist per-user in MongoDB; **no raw provider key is ever stored** (the orphaned Express spec wrote one to disk) and **nothing is written to the filesystem**.

## 5. STILL OPEN

1. **`Suno 202 workshop series2.html` references `rule_90211.mp3`, which exists nowhere in the repo.** A pre-existing broken reference in the original file; the file was not modified. The gate map includes the asset so that the day the owner supplies it, it is protected automatically. **Supplying the file is the owner's to do — no agent may synthesize it.**
2. **Cold-start test flakiness.** Two full-suite runs after this work passed clean (717 passed, 4 skipped). One earlier run in the same session failed 44 tests purely from state pollution (manual probe traffic tripping the login rate limiter mid-suite). Re-run before trusting a red suite.

## 6. PLAN PHASE STATUS (docs/WORKING_PLAN.md)

| Phase | Task | State |
|---|---|---|
| **0** | R1 Legal Engine account sync | **Merged & live** — 201/200 verified |
| **0** | R2 Enrollment atomicity | **Merged** — 8→0 races |
| **0** | R3 Artifact atomicity | **Merged** — 6→0 races |
| **0** | R4 NAM seed on real DBs | **Merged & live** — health check reports 31 skipped/0 failed |
| **0** | R5 In-product guides | **Merged** — verbatim guides + idempotent upsert |
| **0** | R6 Creator Studio at Plus | **Implemented** — `studio: member`, `studio_full: plus`, owner's tier model |
| **0** | R7 Resource Hub tier | **Implemented** — `resource_hub: plus`, handler truth is Member for read |
| **0** | R8 JSON 404/405 for `/api/*` | **MERGED & live-verified** — unknown `/api/*` answers 404 JSON for every verb |
| **0** | R9 PipelineManager import | **Merged** — dead import removed, honest 503 |
| **0** | R10 Loud seed failures | **Merged & live** |
| **0** | G0 Structural hygiene | **Merged** — Anthropic removed, indexes, api_keys split, nav, Refresh |
| **0** | G1 Real revocation | **Merged** — call-time key resolution + eviction |
| **1** | Simulation Lab fixes | **Merged** — engine staleness, lesson ordering, analytics envelope |
| **1** | API key gateway (G2–G7) | **Not started** — design in `docs/API_KEY_GATEWAY_PLAN.md` |
| **2–3** | Depth + monetisation (R11–R17) | **Not started** |
| **New** | The Soup (registration + per-file tiers) | **MERGED & live-verified** — per-file tiers enforced server-side on the bytes (401/403/404 verified live); the partner API ported; the daily puzzle split to `free`; `ai_chat` set to `member` with BYOK + KB-helper carve-outs |
