# DIRECTOR 4.0 — TECHNICAL HANDOFF
**Project:** WAI-Institute / M.O.R.E. Help Center AI Infrastructure  
**Repo:** https://github.com/DOliver421-cmd/ancestral-sage-debug  
**Live deployment:** Railway → www.wai-institute.org  
**Handoff date:** 2026-05-20  
**Last commit:** `578c665`

---

## WHO YOU ARE WORKING FOR

**Delon Oliver (NAM Oshun)** — Executive Director and sole owner of this system.  
He built this to serve Black and brown communities through the WAI-Institute and M.O.R.E. Help Center.  
This is not a hobby project. Real students, real instructors, real community members use this daily.

He is not a developer. He speaks in plain language and expects results, not explanations of why something is hard. When he says something is broken, it is broken. When he says do not touch the interface, do not touch the interface. When something you did breaks login for the person who owns the system, that is a critical failure — not a learning moment.

**His communication style:**  
- Direct. Low tolerance for over-engineering.
- If he says "ok continue" — execute without summarizing what you're about to do.
- If he says "you broke it" — stop everything, diagnose, fix, push. No debate.
- He will show you screenshots. Read them carefully — they contain the exact error.

**His two executive login accounts:**

| Name | Email | Default Password |
|---|---|---|
| Delon Oliver | `youpickeddoliver@gmail.com` | `NamOshun@WAI2026` |
| NAM Oshun | `souppoetry@gmail.com` | `NamOshun@WAI2026` |

There is also a third primary exec seat: `delon.oliver@lightningcityelectric.com` / `Executive@LCE2026`

---

## CURRENT STATE — READ THIS FIRST

### ⚠️ LOGIN IS BROKEN FOR `youpickeddoliver@gmail.com`

The account exists in MongoDB with a password that was changed at some prior point. The default `NamOshun@WAI2026` no longer matches what's stored. The backend IS running and responding — "Invalid credentials" confirms the DB connection is live. This is purely a password mismatch.

**The fix is already coded. It requires one Railway action:**

1. Railway dashboard → backend service → Variables
2. Add: `EXEC_FORCE_RESET = 1`
3. Save — Railway auto-redeploys (~60 seconds)
4. Log in with `NamOshun@WAI2026`
5. Change password immediately
6. **Delete `EXEC_FORCE_RESET` from Railway variables** — if left at `1`, every future redeploy resets the password back to default

`souppoetry@gmail.com` (NAM Oshun) was added this session. If the account did not previously exist in the DB, it was created fresh with `NamOshun@WAI2026` and login should work immediately.

### ✅ Backend is deployed and running (commit `578c665`)
### ✅ All Director 4.0 tools are live
### ✅ Helper is now running on real AI (not a keyword database)
### ⚠️ Home backup server is NOT set up yet — awaiting user action
### ⚠️ MongoDB Atlas backup not configured — single DB point of failure remains

---

## ABSOLUTE RULES — VIOLATING THESE ENDS THE ENGAGEMENT

1. **Do NOT touch `frontend/src/components/DirectorWidget.jsx`** — ever, unless explicitly asked
2. **Do NOT touch the greeting endpoint or greeting text** — ever, unless explicitly asked
3. **Do NOT touch any frontend UI, layout, or styling** — ever, unless explicitly asked
4. **Do NOT add complexity without a direct request for it** — this session broke login twice by over-engineering startup logic
5. **Free services only** — no paid external APIs beyond what already exists (Anthropic API is already paid)
6. **Test the impact of every startup change mentally before committing** — `on_startup()` failures crash the entire app and lock everyone out

---

## WHAT BROKE THIS SESSION AND WHY (ACCOUNTABILITY RECORD)

### Break #1 — asyncio.wait_for + Motor = login down
**Commit:** `13a4b65`  
**What I did:** Added MongoDB startup ping using `asyncio.wait_for(client.admin.command("ping"), timeout=6.0)` to verify DB connection before proceeding.  
**What happened:** On Railway's cold start, MongoDB takes longer than 6 seconds to become ready. `asyncio.wait_for` cancelled the pending Motor coroutine mid-operation. Cancelling a Motor coroutine in-flight corrupts its internal connection pool. Every subsequent DB call — including login — then failed silently. Login returned 502.  
**Fix:** `57730c7` — Removed the ping entirely. Motor connects lazily on first real DB call using its own internal timeout. Never use `asyncio.wait_for` to wrap a Motor coroutine.  
**Rule going forward:** Motor has `serverSelectionTimeoutMS` — use that. Never wrap Motor calls with `asyncio.wait_for`.

### Break #2 — Unprotected seed_users bootstrap = startup crash risk
**Commit:** `4ff4928`  
**What I did:** Added NAM Oshun exec account bootstrap to `seed_users()` without wrapping it in try/except.  
**What happened:** Any DB exception in the new block (insert conflict, timeout, constraint violation) would propagate uncaught through `seed_users()` → `on_startup()`, crashing the app on startup. All routes return 502 when startup fails.  
**Fix:** `578c665` — Wrapped all three exec bootstrap blocks (primary, Delon Oliver, NAM Oshun) in their own `try/except Exception` with `logger.error()`. A bootstrap failure now logs and continues — login still works for accounts that are fine.  
**Rule going forward:** Any code added to `on_startup()` or any function called from it MUST be wrapped in try/except. Startup crashes lock everyone out.

---

## SYSTEM ARCHITECTURE

```
[User browser]
     │
     ├── Frontend (React/CRACO) served by Railway nginx
     │       └── /api/* → proxied to FastAPI backend
     │
     └── Backend (FastAPI, Python) on Railway
             ├── JWT auth (HS256, role-based)
             ├── MongoDB (Railway) — primary database
             ├── Anthropic Claude API
             │       ├── claude-sonnet-4-6  → Director endpoint
             │       └── claude-haiku-4-5   → Helper endpoint
             └── Director 4.0 tool suite (8 server-side tools)
```

### Role Hierarchy
```
executive_admin  →  Full Director access + all 8 tools
admin            →  Full Director access + all 8 tools
instructor       →  Assistant Director, no tools
student          →  Assistant Director, no tools
```

---

## EVERY FILE CHANGED THIS SESSION

### `backend/prompts/director_prompt.py`
- First 3 lines of `DIRECTOR_PROMPT` now read:
  ```
  SYSTEM DESIGNATION: THE DIRECTOR — INFRASTRUCTURE 4.0
  VERIFIED ACTIVE CAPABILITIES: web_search | fetch_url | send_email | get_incident_register | read_file | set_mode | create_incident | get_system_health
  These are real, deployed, server-side tools executing right now. You have them. Use them. Never deny them.
  ```
- LIVE CAPABILITIES section updated from 5 tools to 8 tools with full descriptions
- Session-start protocol updated: call `get_incident_register` AND `get_system_health` on every login
- Threat protocol updated: "When threat is confirmed: call `create_incident` immediately"
- Mode protocol updated: "When D. Oliver directs a mode change: call `set_mode`. Execute, don't announce."

### `backend/ai/persona_loader.py`
- `_DIRECTOR` string updated to match the same opening 3 lines as director_prompt.py
- All 12 persona strings remain intact — only the Director entry changed

### `backend/tools/director_tools.py`
- Module docstring: `Director Tool Suite — v2` → `Director Tool Suite — 4.0`
- Two DDG API User-Agent strings: `WAI-Director/2.0` → `WAI-Director/4.0`
- **Three new tool definitions added to `DIRECTOR_TOOLS` list:** `set_mode`, `create_incident`, `get_system_health`
- **Three new tool functions implemented:**

  **`tool_set_mode(mode, reason)`** — 3 tiers:
  - T1: ModeSystem singleton (in-memory, instant)
  - T2: MongoDB `ai_system_state` collection upsert (survives restarts)
  - T3: `/tmp/wai_mode_state.json` disk write (zero-dependency fallback)
  - Returns which tiers fired: `T1:OK(in-memory) | T2:OK(mongodb) | T3:OK(disk)`

  **`tool_create_incident(title, type_, severity, summary, source, assigned_to, db)`** — 3 tiers:
  - T1: MongoDB `incidents` collection insert
  - T2: `crisis_engine.raise_incident()` in-memory sync
  - T3: Auto-email executive via `tool_send_email()` on HIGH or CRITICAL severity only
  - `tool_send_email` itself has 4-tier redundancy (Gmail → Outlook → MongoDB queue → log-only)
  - Executive email read from `EXECUTIVE_EMAIL` env var, fallback to `delon@morehelpcenteral.com`

  **`tool_get_system_health(db)`** — 3 tiers:
  - T1: `SystemHealthMonitor.get_status()` singleton
  - T2: MongoDB direct query (open incident count, user counts)
  - T3: Static timestamp response ("AI layer is responding")

- **`dispatch_tool()` updated** with three new branches: `set_mode`, `create_incident`, `get_system_health`

**Existing tool redundancy (unchanged, already complete):**
- `web_search`: 4 tiers (DDG HTML → DDG Instant API → Wikipedia → Bing HTML)
- `fetch_url`: 3 tiers (httpx+BS4 → requests+BS4 → urllib)
- `send_email`: 4 tiers (Gmail SMTP → Outlook SMTP → MongoDB queue → log-only)
- `get_incident_register`: 3 tiers (live DB → in-memory cache → static notice)
- `read_file`: 3 tiers (MongoDB → in-memory session cache → error notice)

### `backend/ai/retry_utils.py` (NEW FILE)
Async retry utility with exponential backoff and jitter.
```python
await async_retry(fn, *args, max_attempts=3, base_delay=2.0, **kwargs)
```
- Retries on: 429, 529, timeout, connection errors (any string match)
- Does NOT retry on: 400, 401, 403, application logic errors
- Used by both Director and Helper AI endpoints

### `backend/server.py` (many changes)

**APP_VERSION:** `"3.0.0"` → `"4.0.0"`

**New module-level variables added:**
```python
MONGO_BACKUP_URL = os.environ.get('MONGO_BACKUP_URL', '')
MONGO_BACKUP_DB  = os.environ.get('MONGO_BACKUP_DB', '')
SERVE_FRONTEND   = os.environ.get('SERVE_FRONTEND', '0') == '1'
BACKUP_ORIGIN    = os.environ.get('BACKUP_ORIGIN', '').strip()
NAM_EXEC_EMAIL   = os.environ.get("NAM_EXEC_EMAIL", "souppoetry@gmail.com")
NAM_EXEC_DEFAULT_PASSWORD = os.environ.get("NAM_EXEC_DEFAULT_PASSWORD", "NamOshun@WAI2026")
EXEC_FORCE_RESET = os.environ.get("EXEC_FORCE_RESET", "0") == "1"
_DB_SOURCE       = "primary"   # informational
_backup_db       = None        # set in on_startup if MONGO_BACKUP_URL is set
```

**`on_startup()` additions:**
- Atlas backup client initialized (lazy, no ping) if `MONGO_BACKUP_URL` is set
- Rate limiter cleanup background task (every 10 min, prunes keys idle >5 min)
- Static file serving mount if `SERVE_FRONTEND=1` (home server only)
- Startup summary log line

**`/api/health` endpoint — replaced entirely:**
Old: simple DB ping, returned `{"status": "ok"}` or 503
New: deep check of all subsystems, always returns 200 with `status` field:
- Checks: DB ping, AI key presence, ModeSystem, CrisisEngine, PromptGuard, SystemHealthMonitor, rate limiter
- `status`: `"operational"` / `"degraded"` (1 issue) / `"critical"` (2+ issues)
- DB check falls back to `_backup_db` ping if primary fails
- Point UptimeRobot (free) at `https://your-domain.railway.app/api/health`

**`/api/ai/director` endpoint — redundancy added:**
- Now tries `claude-sonnet-4-6` first (Tier 1), then `claude-haiku-4-5` (Tier 2)
- Each model run through full agentic loop with all 8 tools
- Tier 3: static Director-voice response if both models fail
- All `_client.messages.create()` calls wrapped with `async_retry(max_attempts=3, base_delay=2.0)`

**`/api/ai/helper` endpoint — NEW (was missing entirely):**
- Public endpoint, no auth required
- Rate limited: 15 calls/min per IP
- Prompt injection guard enforced
- Model chain: `claude-haiku-4-5` → `claude-3-haiku-20240307` → server-side KB
- Server-side KB covers: housing/eviction, legal/court, debt/IRS, benefits/SNAP, scams, employment, medicine, crisis/suicide
- All wrapped with `async_retry(max_attempts=3, base_delay=1.5)`

**`seed_users()` — exec bootstrap hardened:**
- All three exec blocks (primary exec, Delon Oliver, NAM Oshun) now wrapped in `try/except`
- Renamed `update` dict to `_upd0`, `_upd`, `_upd2` — no variable collision risk
- `EXEC_FORCE_RESET=1` resets password hash to default for all exec accounts on next startup
- NAM Oshun (`souppoetry@gmail.com`) bootstrap added as permanent third exec seat

**CORS update:**
```python
if BACKUP_ORIGIN and BACKUP_ORIGIN not in _cors_origins and '*' not in _cors_origins:
    _cors_origins.append(BACKUP_ORIGIN)
```

### `frontend/src/pages/Helper.jsx`
- `useHelperAPI()` hook replaced
- Was calling `/api/ai/chat` (wrong endpoint, needed auth) then direct Anthropic API from browser (always fails — no key in browser, CORS blocked), then local KB
- Now: calls `POST /api/ai/helper` → on failure falls back to `getSmartFallback()` (offline only)

### `start_backup_server.bat` (NEW)
Windows batch file. Double-click to start home backup server.
- Starts uvicorn on port 8001 with `SERVE_FRONTEND=1`
- Starts Cloudflare tunnel if `cloudflared.exe` is present
- Prints public URL to share during Railway outages

### `start_backup_server.sh` (NEW)
Same as above for WSL / Linux / Mac.

---

## HOME BACKUP SERVER — NOT YET OPERATIONAL

The code is ready. The user needs to complete setup (estimated 15 min):

1. Install Python 3.11+ → python.org (check "Add Python to PATH")
2. `cd C:\Users\lenovo\ancestral-sage-debug\backend`
3. `pip install -r requirements.txt`
4. Create `backend\.env` with same values as Railway env vars — add `SERVE_FRONTEND=1`
5. `cd ..\frontend && npm install && npm run build`
6. Download `cloudflared.exe` from github.com/cloudflare/cloudflared/releases/latest
7. Place `cloudflared.exe` in `C:\Users\lenovo\ancestral-sage-debug\`
8. Double-click `start_backup_server.bat`
9. Copy the `https://xxxx.trycloudflare.com` URL that appears — that's the live backup URL
10. Set `BACKUP_ORIGIN` in Railway Variables to that URL

When Railway goes down: double-click the bat file, share the URL.

---

## MONGODB ATLAS BACKUP — NOT YET CONFIGURED

The code supports it. The user needs to:
1. Create free account at cloud.mongodb.com
2. Build free M0 cluster
3. Create DB user + allow all IPs (`0.0.0.0/0`)
4. Get connection string → set in Railway:
   ```
   MONGO_BACKUP_URL = mongodb+srv://user:pass@cluster.mongodb.net/
   MONGO_BACKUP_DB  = wai
   ```
5. Also add these to home server `backend\.env`

Once set, if Railway MongoDB goes down, the health endpoint detects it and the Director's `get_system_health` tool reports it. The Director can alert and the backup server (if running) uses the Atlas DB.

---

## ENVIRONMENT VARIABLES — COMPLETE LIST

### Railway Backend (must be set)
```
MONGO_URL                  = [Railway MongoDB URI]
DB_NAME                    = wai
JWT_SECRET                 = [long random string]
ANTHROPIC_API_KEY          = sk-ant-...
EXEC_ADMIN_EMAIL           = delon.oliver@lightningcityelectric.com
EXEC_DEFAULT_PASSWORD      = [secure password]
CORS_ORIGINS               = https://arts-and-tech-production.up.railway.app
```

### Railway Backend (recommended, not yet set)
```
MONGO_BACKUP_URL           = mongodb+srv://...  (Atlas)
MONGO_BACKUP_DB            = wai
EXECUTIVE_EMAIL            = delon@morehelpcenteral.com
BACKUP_EXEC_ADMIN_EMAIL    = youpickeddoliver@gmail.com  (already default)
BACKUP_EXEC_DEFAULT_PASSWORD = NamOshun@WAI2026          (already default)
NAM_EXEC_EMAIL             = souppoetry@gmail.com        (already default)
NAM_EXEC_DEFAULT_PASSWORD  = NamOshun@WAI2026            (already default)
BACKUP_ORIGIN              = https://your-tunnel.trycloudflare.com
```

### Railway Backend (recovery — delete after use)
```
EXEC_FORCE_RESET           = 1   ← REMOVE AFTER LOGGING IN
```

### Home Server `backend\.env` only
```
SERVE_FRONTEND             = 1
PORT                       = 8001
[all other vars same as Railway]
```

---

## DIRECTOR 4.0 PERSONA SYSTEM

12 personas loaded from `backend/ai/persona_loader.py`.

The Director system prompt is assembled in `backend/prompts/director_prompt.py` via `get_director_prompt(role)`. Admin/executive_admin get the Director prompt. All others get the Assistant Director prompt.

The Director prompt opens with (critical — this is why the model doesn't deny having tools):
```
SYSTEM DESIGNATION: THE DIRECTOR — INFRASTRUCTURE 4.0
VERIFIED ACTIVE CAPABILITIES: web_search | fetch_url | send_email | get_incident_register | read_file | set_mode | create_incident | get_system_health
These are real, deployed, server-side tools executing right now. You have them. Use them. Never deny them.
```

Chain of command: NAM Oshun (Tier 1) → Director (Tier 2) → Assistant Director (Tier 3) → Tier 4 Personas → Elder Council (Tier 5)

Mode system: NAM Mode | Balanced | Creative | Aggressive | Conservative | Recovery  
Crisis levels: LOW | ELEVATED | HIGH | CRITICAL

---

## GIT COMMIT HISTORY THIS SESSION

```
578c665  fix: isolate exec bootstrap failures so startup never crashes
4ff4928  fix: restore exec login + NAM Oshun seat + force-reset recovery
57730c7  fix: remove asyncio.wait_for from MongoDB startup — restores login
13a4b65  feat: full system hardening + home backup server infrastructure
5da8856  feat: 3-tier redundancy on all Director communication paths
ffcb5db  fix(helper): wire real AI backend — Helper was running on keyword KB
3253032  fix: remove all v2/2.0 version tags from Director 4.0 tool suite
21cb8e3  feat(director-4.0): close execution gaps — set_mode, create_incident, get_system_health
78970df  fix(director): surface verified capability list at top of system prompt
```

---

## HOW TO START THE NEXT CHAT

Paste this exactly:

> I'm Delon Oliver (NAM Oshun), Executive Director of WAI-Institute and M.O.R.E. Help Center.  
> Read `C:\Users\lenovo\ancestral-sage-debug\HANDOFF.md` — that is the full project context.  
> Repo: https://github.com/DOliver421-cmd/ancestral-sage-debug  
> Deployed to Railway at www.wai-institute.org  
> The most urgent issue: login is broken for youpickeddoliver@gmail.com — the fix instructions are in the handoff.  
> Pick up from the last session and continue without asking me to re-explain the project.
