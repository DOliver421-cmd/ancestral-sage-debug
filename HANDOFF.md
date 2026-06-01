# WAI Institute — Agent Handoff Document
**Date:** June 1 2026
**Repo:** DOliver421-cmd/ancestral-sage-debug
**Deploy:** Railway — two services (frontend nginx + backend uvicorn)
**Domains:** wai-institute.org (main) · morehelp.center (M.O.R.E. subdomain)
**Last merged PR:** #34 (PR #35 open, not merged)

---

## HONEST SESSION ASSESSMENT

The last session spent the majority of its time on cosmetic changes — replacing `window.confirm` / `window.prompt` with inline modals. These changes do not fix anything broken for a real user or visitor. They improve polish on admin-only screens that users never see. A significant number of PRs (#33, #34, #35 partial) were consumed by this.

One real functional bug was introduced and not caught until an end-of-session audit:
- **Creators.jsx line 58** reads `c.displayName || c.name` but the backend returns `display_name` (snake_case). Every real creator profile fetched from the DB renders with a **blank name** on the public `/creators` page. This is user-visible and was caused by this session's PR #34 rewrite of Creators.jsx.

---

## PERMANENT MANDATES (must survive every session)

1. **Never call Anthropic/LLMs directly** — always use `call_llm()` from `backend/ai/llm_gateway.py`
2. **API keys encrypted at rest** via Fernet (`PROVIDER_KEY_ENCRYPTION_SECRET`). `encrypted_key` field **NEVER** returned in any API response.
3. **Cash refunds require ALL 5 conditions**: `is_extreme_violation`, `user_not_at_fault`, `is_legal`, `no_harm_to_wai`, `supervisor_approved`
4. **Sequential commits** — one unit of work per PR, wait for merge before starting next
5. **No accumulation** — never let more than one PR sit open without user merge approval
6. **Never remove any site control/feature** without explicit instruction to remove that specific feature
7. **No cosmetic mocks** — every metric, control, and display must be real and functional

---

## ARCHITECTURE

- **Frontend**: React 18 SPA, React Router v6, Tailwind CSS, Vite/CRA + Craco, served by nginx
- **Backend**: FastAPI + Motor (async MongoDB), ~12,400 lines in `backend/server.py`
- **Auth**: JWT Bearer token (`lce_token` in localStorage), roles: `student < instructor < admin < executive_admin`
- **Payments**: Stripe checkout + webhooks + subscriptions
- **AI**: `call_llm()` gateway in `backend/ai/llm_gateway.py` — all LLM calls go through here
- **Static tools**: `frontend/public/tools/` — standalone HTML pages using `hub_client.js` shared state

**API routing**: `api_router = APIRouter(prefix="/api")` — frontend axios baseURL is `${BACKEND_URL}/api`. So `api.post("/foo")` hits `/api/foo`.

---

## WHAT ACTUALLY WORKS (end-to-end verified, field names traced)

| Feature | Status | Notes |
|---------|--------|-------|
| Plans → Stripe checkout | ✅ Works | `product_key` matches; backend returns `url`; all 5 plan keys valid |
| Creator course publishing (CRUD) | ✅ Works | POST/GET/PATCH/DELETE all wired; field names match |
| Creator earnings dashboard | ✅ Works | All response fields match what frontend reads |
| Creator profile self-edit | ✅ Works | `PUT /creator/profile` with `display_name` (snake_case) |
| Landing page live course cards | ✅ Works | Reads `price_cents`/`enrollment_count` — matches backend |
| Tool-page AI via WAI backend | ✅ Works | `callWAI()` in hub_client.js → `/api/ai/tool-chat` → `call_llm()` |
| GhostProducer TTS | ✅ Works | Calls `/ai/sage/tts`, blob response, plays via Web Audio API |
| FlagModal → /more/flag | ✅ Works | Field names match; auth attached |
| Stripe webhook → creator_enrollments | ✅ Works | Branches on `product_key=="creator_course"`, upserts with `paid:True` |
| SiteControlPanel data | ✅ Works | All keys from `/admin/control-panel` match what frontend destructures |
| Creator profile is_owner flag | ✅ Works | JWT vs `user_id` comparison; Edit button shows correctly |

---

## KNOWN BUGS — MUST FIX BEFORE ANYTHING ELSE

### 🔴 BUG 1 — Creators.jsx: real creator names are blank (introduced PR #34)
**File**: `frontend/src/pages/Creators.jsx` line 58
**Problem**: `c.displayName || c.name` — backend returns `display_name` (snake_case). Real DB profiles render with blank name.
**Fix**: Change to `c.display_name || c.displayName || c.name`
**Impact**: Every real creator on the public `/creators` directory is nameless.

### 🔴 BUG 2 — CreatorProfile.jsx: Nova Highborn still hardcoded with no real DB profile
**File**: `frontend/src/pages/CreatorProfile.jsx` lines 197–239
**Problem**: Nova Highborn (`slug: "nova-highborn"`) is fully hardcoded in the frontend registry. If a user navigates to `/creator/nova-highborn`, it renders from this hardcoded data — but there is no real DB profile and no backend endpoint for this creator. If the hardcoded registry is ever cleaned, the page 404s. This is a ticking bomb.
**Fix**: Either create a real DB profile for Nova Highborn (`/creator/profile` PUT), or remove the hardcoded entry and accept the 404.

### 🟡 BUG 3 — /ai/tool-chat calls invisible to AI spend dashboard
**File**: `backend/server.py` ~line 3867
**Problem**: `ai_usage_log` insert for tool-chat writes only `{user_id, endpoint, skill, created_at}`. Missing `cost_usd`, `provider`, `model`. The SiteControlPanel AI spend widget sums `cost_usd` by provider — tool-chat calls never appear. You are flying blind on this cost center.
**Fix**: After `gw = await _call_llm(...)`, read `gw.get("cost_usd", 0)` and `gw.get("provider", "")` and write them to the log.

### 🟡 BUG 4 — ModuleView has video/diagram placeholder divs in production
**File**: `frontend/src/pages/ModuleView.jsx` lines ~72–79
**Problem**: `data-testid="video-placeholder"` and `data-testid="diagram-placeholder"` divs are rendered. Learners see empty boxes where video content should be.
**Fix**: Audit whether the backend serves `video_url` and `diagram_url` fields on modules; wire or hide appropriately.

---

## REMAINING WINDOW.CONFIRM DIALOGS (cosmetic — low priority, do last)

These are all on admin-only pages. Real users never see them. Do NOT work on these until all functional bugs above are fixed.

| File | Dialog | Priority |
|------|--------|---------|
| `AdminDashboard.jsx` | Delete user, resolve incident, force logout, `window.prompt` for reset link | Admin only |
| `ExecutiveDirectorDashboard.jsx` | Resolve refund, deactivate/delete user, lock platform, disable feature toggle | Exec only |
| `MoreHelpCenter.jsx` | Delete user, revoke env key, reset token counter | Admin only |
| `SeshatsHub.jsx` | Failover, emergency broadcast, reset counter | Exec only |
| `PlatformPrices.jsx` | Delete price key | Admin only |
| `Settings.jsx` | Log out all other devices | User-facing but non-destructive |

PR #35 (ExecSystem, RevenueDivision, ProviderGateway modals) is open and unmerged. If merged, it addresses 3 more admin dialogs but still leaves 6 files untouched.

---

## REAL VISITOR/USER VALUE — WHAT TO BUILD NEXT

These are ordered by actual user/visitor impact. Do these before any more cosmetic work.

### Priority 1 — Fix the blank name bug (15 min)
`Creators.jsx` line 58: `c.display_name || c.displayName || c.name`
This is the only user-visible regression from the entire session.

### Priority 2 — Nova Highborn resolution (30 min)
Decide: create a real DB profile via `PUT /creator/profile` (requires a real user account), or remove the hardcoded entry. Currently a maintenance trap.

### Priority 3 — AI spend logging for tool-chat (20 min)
Add `cost_usd`, `provider`, `model` to the `ai_usage_log` insert in the tool-chat endpoint. Without this, the platform owner has no visibility into what AI tools are costing.

### Priority 4 — ModuleView content delivery (unknown)
Audit whether paid courses actually deliver video/diagram content to enrolled students. If the content fields are empty in DB, learners are paying for nothing.

### Priority 5 — End-to-end student flow test
A new student should be able to: register → buy a plan → enroll in a creator course → access module content → pass a quiz → receive a certificate. Trace this entire flow in code and find where it breaks.

---

## FILE MAP (key files by role)

| File | Role |
|------|------|
| `backend/server.py` | Entire backend — ~12,400 lines |
| `backend/ai/llm_gateway.py` | **Only** way to call any LLM |
| `frontend/src/App.js` | All routes |
| `frontend/src/lib/api.js` | Axios instance — auto-attaches JWT |
| `frontend/src/lib/auth.js` | `useAuth()` hook, `current_user` dependency |
| `frontend/public/tools/hub_client.js` | Shared state for all standalone tool HTML pages |
| `frontend/public/tools/*.html` | Standalone tool pages (djedi-oracle, electrical-courses, media-strategist, publisher-prime, creators-sanctuary, litigation-weapon) |

---

## ENVIRONMENT

- `MONGO_URL` — MongoDB Atlas connection string
- `JWT_SECRET` — JWT signing key
- `STRIPE_SECRET_KEY` — Stripe API key
- `STRIPE_WEBHOOK_SECRET` — Stripe webhook signing secret
- `PROVIDER_KEY_ENCRYPTION_SECRET` — Fernet key for encrypting stored API keys
- `EXEC_EMAIL` / `EXEC_PASSWORD` — executive admin seed account
- `PORT` — injected by Railway (default 8080)

---

## OPEN PR

**PR #35** — Replace `window.confirm` on destructive admin actions with modals (ExecSystem, RevenueDivision, ProviderGateway)
Branch: `claude/gracious-gauss-xbJ8e`
Status: Open, not merged. Cosmetic value only — no functional fix.
