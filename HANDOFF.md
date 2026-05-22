# WAI-Institute — Claude Handoff Document
**Date:** 2026-05-21  
**Repo:** https://github.com/DOliver421-cmd/ancestral-sage-debug  
**Live URL:** https://ancestral-sage-debug-production.up.railway.app  
**Custom domain (broken, see below):** www.wai-institute.org  

---

## Who You're Working With

**Delon Oliver / NAM Oshun** — Executive Director, WAI-Institute & M.O.R.E. Help Center.  
Not a developer. Expects results, not explanations.

- "ok continue" = execute without summarizing
- "you broke it" = stop, diagnose, fix, push — no debate
- Screenshots he sends contain the exact error — read them carefully
- Low tolerance for over-engineering

---

## Absolute Rules — Never Break These

1. **NEVER touch** `frontend/src/components/DirectorWidget.jsx` unless explicitly asked
2. **NEVER touch** the greeting endpoint or greeting text unless explicitly asked
3. **NEVER touch** any frontend UI, layout, or styling unless explicitly asked
4. **NEVER use** `asyncio.wait_for` to wrap a Motor (MongoDB async) coroutine — corrupts the connection pool
5. **ALWAYS wrap** any code added to `on_startup()` in try/except — uncaught exceptions here crash all routes (502)
6. **No added complexity** without a direct request

---

## Executive Login Credentials

| Email | Password |
|---|---|
| `delon.oliver@lightningcityelectric.com` | `Executive@LCE2026` |
| `youpickeddoliver@gmail.com` | `NamOshun@WAI2026` |
| `souppoetry@gmail.com` | `NamOshun@WAI2026` |

**If login fails (password mismatch):**
1. Railway dashboard → backend service → Variables → add `EXEC_FORCE_RESET = 1` → Save
2. Wait ~60 sec for redeploy
3. Log in with `NamOshun@WAI2026`
4. **Immediately delete `EXEC_FORCE_RESET` from Railway vars** — leaving it causes reset on every deploy

---

## Stack

- **Frontend:** React/CRACO on Railway nginx — proxies `/api/*` to FastAPI backend
- **Backend:** FastAPI (Python) on Railway — `backend/server.py`
- **DB:** MongoDB on Railway (primary) — env var `MONGO_URL`
- **AI:** Anthropic Claude API — `claude-sonnet-4-6` (Director), `claude-haiku-4-5` (Helper)
- **Auth:** JWT HS256, role-based (`executive_admin` → `admin` → `instructor` → `student`)

---

## Current System State (as of 2026-05-22)

### What's Working
- Server deploys and starts
- All API endpoints live
- Director 4.0 with 8 tools live
- PRT + The 9 system installed
- Staff meeting endpoint (`POST /api/exec/staff-meeting`) installed
- Cultural Scout background scanner running (every 6h)
- Revenue Operations System integrated (billing, CRM, financial reporting)
- 199/199 tests passing

### What's Broken / Pending
- **Custom domain** `wai-institute.org` not connected to Railway (Namecheap login issues)
- **Email not sending** — Director `send_email` falls back to MongoDB queue; needs `GMAIL_USER` + `GMAIL_APP_PASSWORD` in Railway vars
- **Reddit scout** — All 6 subreddits return 403; needs Reddit API credentials
- **Google Trends + Poetry Foundation** feed URLs are stale (404)
- **Revenue System Testing** — Billing endpoints created but not yet tested in production

---

## 502 History — What's Been Fixed

The server was returning 502 "Application failed to respond." Three root causes found and fixed:

### Fix 1 — commit `756bbf5`
`backend/server.py` lines 882-890: Nine DB operations in `on_startup()` had zero error handling. Any MongoDB timeout crashed the entire startup.  
**Fix:** Wrapped all 9 calls (`ensure_indexes`, `seed_modules`, `seed_users`, `seed_labs`, `seed_compliance`, `seed_sites_inventory`, `backfill_verification_codes`, `run_escalation_check`, `run_engagement_check`) in individual try/except blocks. Also bumped `healthcheckTimeout` from 30 to 60 in `railway.toml`.

### Fix 2 — commit `c94cc40`
`backend/server.py` line 80: Primary MongoDB client had no timeout set (default = 30s per operation). With 9 sequential startup ops, worst case was 270s of hanging — far beyond the 60s healthcheck.  
**Fix:**
```python
client = AsyncIOMotorClient(
    mongo_url,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=5000,
    socketTimeoutMS=10000,
)
```

### Fix 3 — commit `cf3843e` (earlier session)
`backend/server.py` staff meeting DB writes: All 4 collection inserts in one try/except — one failure silently killed all subsequent writes. Also `PRTEnforcementEngine.to_governance_dict()` was called in server.py but never defined (AttributeError silently swallowed).  
**Fix:** 4 independent try/except blocks; added missing `to_governance_dict` static method to `backend/wai_institute/personas/prt/prt_enforcement_engine.py`.

---

## Key Files

| File | Purpose |
|---|---|
| `backend/server.py` | Main FastAPI app — all endpoints, startup, auth |
| `backend/tools/director_tools.py` | Director's 8 tools (web_search, send_email, etc.) |
| `backend/prompts/director_prompt.py` | Director system prompt |
| `backend/ai/persona_loader.py` | 12 AI personas |
| `backend/wai_institute/personas/prt/prt_enforcement_engine.py` | PRT enforcement layer |
| `backend/wai_institute/core/the9_fusion_engine.py` | The 9 fusion engine |
| `backend/wai_institute/core/prt_the9_authority.py` | PRT/The 9 authority (ESDAL model) |
| `backend/wai_institute/scripts/system_activation.py` | Startup: persona bootstrap + scout scheduler |
| `src/agents/pipeline_manager.py` | LLM intent routing pipeline |
| `src/tests/test_prt_the9.py` | 144 PRT + The 9 tests |
| `src/tests/test_pipeline_manager.py` | 55 pipeline tests |
| `railway.toml` | Railway deploy config (healthcheckTimeout = 60) |
| `Dockerfile` | Root Dockerfile used by Railway |
| `backend/revenue_operations_integration.py` | Revenue system init + router registration |
| `backend/config.py` | Revenue system configuration (Stripe, email, Slack) |
| `backend/database.py` | Revenue system database setup |
| `backend/jobs.py` | Scheduled jobs: payouts, revenue recognition, renewals |
| `backend/billing/routes.py` | Billing API: subscriptions, invoices, financial reporting |
| `backend/billing/stripe_service.py` | Stripe integration: payments, payouts, webhooks |
| `backend/billing/financial_reporting.py` | Financial metrics: MRR, LTV, CAC, forecasting |
| `backend/billing/models.py` | Pydantic models: Subscription, Invoice, etc. |
| `backend/crm/routes.py` | CRM API: leads, opportunities, pipeline |
| `backend/crm/models.py` | Pydantic models: Lead, Opportunity, etc. |
| `backend/contracts/templates.py` | Contract generation: Consumer, Enterprise, Research |

---

## Railway Environment Variables

### Currently set (assumed working)
- `MONGO_URL` — primary MongoDB connection string
- `DB_NAME` — database name
- `ANTHROPIC_API_KEY` — Claude API key
- `SECRET_KEY` — JWT signing key

### Not set — needed for full functionality

| Var | What it unlocks |
|---|---|
| `GMAIL_USER` | Director email sending |
| `GMAIL_APP_PASSWORD` | Director email sending (Google App Password) |
| `REDDIT_CLIENT_ID` | Cultural Scout Reddit access |
| `REDDIT_CLIENT_SECRET` | Cultural Scout Reddit access |
| `SCOUT_ENABLED=false` | Disable background scout if memory/CPU is a concern |
| `SCOUT_INTERVAL_HOURS` | Override 6h scout interval |

---

## Staff Meeting Endpoint

```
POST /api/exec/staff-meeting
Authorization: Bearer <executive_token>

{
  "brief": "Launch a healing campaign for Juneteenth",
  "agenda": ["content strategy", "monetization", "cultural integrity"],
  "participants": [],        // empty = all active personas
  "priority": "high"         // "high" triggers The 9 synthesis
}
```
Requires `executive_admin` role. Returns domain briefs from all personas + The 9 synthesis if high priority.

---

## Director Tools (8 — all installed)

| Tool | Status | Notes |
|---|---|---|
| `web_search` | Working | 4-tier: DDG → DDG API → Wikipedia → Bing |
| `fetch_url` | Working | 3-tier: httpx → requests → urllib |
| `send_email` | Queue only | Needs `GMAIL_USER` + `GMAIL_APP_PASSWORD` in Railway |
| `get_incident_register` | Working | Live DB → cache → static |
| `create_incident` | Working | Auto-emails exec on HIGH/CRITICAL |
| `get_system_health` | Working | Monitor → MongoDB → static |
| `set_mode` | Working | Modes: nam/balanced/creative/aggressive/conservative/recovery |
| `read_file` | Working | Reads files uploaded in session |

---

## Custom Domain (wai-institute.org)

Domain registered at **Namecheap**. Delon is currently locked out (password reset loop — likely temp account lock from too many attempts).

**To connect domain once Namecheap access is restored:**
1. Railway → ancestral-sage-debug → Settings → Custom Domains → add `wai-institute.org` and `www.wai-institute.org`
2. Railway shows a CNAME value (e.g. `xxxxxxxx.proxy.railway.app`)
3. Namecheap → Domain List → wai-institute.org → Manage → Advanced DNS
4. Add: `CNAME` record, Host: `www`, Value: the Railway CNAME
5. Add: `ALIAS` record, Host: `@`, Value: same Railway CNAME
6. SSL auto-provisions in 5–15 minutes

**Namecheap unlock:** Try private/incognito browser first (rules out autofill). If still locked, call **1-888-965-4263** or live chat — say account is locked after multiple password resets.

---

## PRT + The 9 Authority Model (ESDAL)

- **Sage OR Executive** can command PRT — either authority is sufficient
- **PRT, Sage, OR Executive** can activate The 9
- All other personas are blocked regardless of tier
- This is intentional doctrine — do not change without explicit instruction from Delon

---

## Running Tests

```bash
cd C:\Users\lenovo\ancestral-sage-debug
python -m pytest src/tests/ -v   # 199 tests total
```

---

## If You See 502

1. Check Railway deploy logs — look for ERROR or the last line before it stops
2. Determine: startup crash (logs end before "STARTUP COMPLETE") or post-startup crash
3. If startup crash: find which seed/init function is hanging — add tighter try/except
4. If post-startup crash: check Railway metrics for OOM kill; consider `SCOUT_ENABLED=false`
5. Do NOT use `asyncio.wait_for` around Motor coroutines — use `serverSelectionTimeoutMS` on the client
6. Do NOT wrap `on_startup()` itself — wrap individual operations only

---

## Recent Commits

```
c94cc40  fix: MongoDB client timeouts — prevent 270s startup hang
756bbf5  fix: wrap all on_startup() DB calls in try/except
cf3843e  fix: security/architecture hardening — 5 bugs corrected
3cd6000  feat: PRT + The 9 full system + staff meeting endpoint
```

---

## Revenue Operations System (NEW — as of 2026-05-22)

The system now includes a complete revenue operations infrastructure integrated into the main FastAPI app:

### Billing System
- **Endpoints:** `/api/billing/subscribe`, `/api/billing/invoices`, `/api/billing/subscription`, etc.
- **Features:** Subscription management, invoice tracking, payment method storage
- **Stripe Integration:** Test mode ready (use sk_test_* keys), automatic payment processing
- **Creator Payouts:** Track creator earnings with 70/30 revenue split, monthly payout jobs

### Financial Reporting
- **Endpoints:** `/api/billing/reporting/summary`, `/api/billing/reporting/mrr`, `/api/billing/reporting/revenue/{year}/{month}`, etc.
- **Metrics:** MRR, churn rate, LTV/CAC, cohort analysis, cash flow forecasting
- **Revenue Recognition:** ASC 606 compliant monthly revenue recognition

### Sales Pipeline (CRM)
- **Endpoints:** `/api/crm/leads`, `/api/crm/opportunities`, `/api/crm/metrics/pipeline`, etc.
- **Features:** Lead management, opportunity tracking, sales stage forecasting
- **Metrics:** Pipeline value, win rate, sales cycle length, deal size

### Scheduled Jobs
- **Creator Payouts:** 1st of month at 2am UTC
- **Revenue Recognition:** Last day of month at 3am UTC
- **Renewal Reminders:** Daily at 6am UTC (enterprise contracts within 90 days)
- **Failed Payment Checks:** Daily at 7am UTC

### Deployment Notes
- All collections and indexes initialized automatically on startup
- Services attached to `app.state` for dependency injection
- Routers registered with main `api_router` automatically
- Requires MongoDB collections (12 new collections for revenue, CRM, and jobs)
- No additional databases or external services required (test mode Stripe is free)

---

## What Delon Wants Next (priority order)

1. Test revenue operations system end-to-end (create subscription, verify payment, check metrics)
2. Connect `wai-institute.org` domain (blocked on Namecheap)
3. `GMAIL_USER` + `GMAIL_APP_PASSWORD` set so Director can send email
4. Reddit API credentials for Cultural Scout
5. Monitor first production deployment of revenue system
