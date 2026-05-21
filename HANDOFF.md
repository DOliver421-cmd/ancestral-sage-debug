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

> I'm Delon Oliver (NAM Oshun), Executive Director of WAI-Institute and M.O.R.E. Help Center.  
> Read `C:\Users\lenovo\ancestral-sage-debug\HANDOFF.md` — that is the full project context.  
> Repo: https://github.com/DOliver421-cmd/ancestral-sage-debug  
> Deployed to Railway at www.wai-institute.org  
> Pick up from the last session and continue without asking me to re-explain the project.

---

# SESSION 2 UPDATE — 2026-05-21

**Last commit this session:** `0a6d4df`  
**Status:** All 4 new personas live. Memory system live. ElevenLabs wired. Login was already fixed (user resolved independently).

---

## WHAT WAS BUILT THIS SESSION

### 1. ElevenLabs TTS Client (`backend/ai/elevenlabs_client.py`) — commit `1591493`

3-tier voice system for THE CIPHER:

**Tier 1: ElevenLabs** — `eleven_multilingual_v2` model  
- Performance markup engine: `[whisper]` / `[fire]` / `[rise]` / `[crescendo]` / `[tender]` / `[shout]` etc. → ElevenLabs `voice_settings`
- `parse_performance_markup(text)` → strips tags, averages voice_settings across all found tags  
- `preserve_performance_markup(text)` → readable stage directions for Text Performance Mode
- Budget: 29,500 chars/month hard cap (500 char buffer from $5 Starter), 25,000 soft warning  
- Budget tracked in `db.cipher_audio_budget`, auto-resets monthly  
- Audio cache in `db.cipher_tts_cache` (SHA-256 keyed, base64)  
- Budget refunded on API failure (no phantom charges)

**Tier 2: OpenAI TTS** — returns `{fallback_endpoint: "/api/ai/sage/tts", fallback_voice: "onyx"}` so client routes to existing infrastructure  
**Tier 3: Text Performance Mode** — `display_text` with `‹stage directions›`, zero cost, always available

### 2. `/api/ai/cipher/tts` endpoint (server.py) — commit `1591493`

```
POST /api/ai/cipher/tts
Body: {text, force_tier?, session_id?}
Access: admin, executive_admin | Rate: 20/min
```

- T1/cached → `StreamingResponse(audio/mpeg)` + `X-Tier`, `X-Budget-Remaining`, `X-Budget-Warning` headers  
- T2 → JSON with `{tier:"openai", fallback_endpoint, fallback_voice, clean_text}`  
- T3 → JSON with `{tier:"text", display_text, clean_text}`  
- `force_tier` override: "elevenlabs" | "openai" | "text"

### 3. THE AMBASSADOR 4.0 (`backend/tools/ambassador_tools.py`) — commit `e66157f`

Campaign coordination authority. Runs Oracle → Cipher → Architect pipeline.

**9 tools:**
- `ambassador_coordinate_oracle` — calls Anthropic with Oracle persona (one-shot, Haiku)  
- `ambassador_coordinate_cipher` — calls Anthropic with Cipher persona (one-shot, includes Oracle brief)  
- `ambassador_coordinate_architect` — calls Anthropic with Architect persona (one-shot, visual brief)  
- `ambassador_package_campaign` — packages deliverables to `db.ambassador_campaigns`  
- `ambassador_publish_campaign` — Gumroad T1 → MongoDB T2 → exec notification T3  
- `ambassador_request_director_approval` — logs to `db.director_approvals` + exec notification  
- `ambassador_get_campaign_status` — MongoDB lookup  
- `ambassador_list_active_campaigns` — MongoDB list with status filter  
- `ambassador_list_revenue_streams` — preloaded catalog

**Revenue streams:**
| ID | Price | Description |
|---|---|---|
| `full_campaign_package` | $199.00 | Oracle + Cipher + Architect package |
| `quarterly_content_calendar` | $349.00 | 13-week coordinated content plan |
| `launch_campaign_kit` | $299.00 | Full product/movement launch sequence |
| `movement_intelligence_brief` | $79.99 | Oracle-powered campaign brief |
| `community_activation_pack` | $99.99 | Community engagement campaign |
| `wai_campaign_production` | $0 | Internal WAI/M.O.R.E. |

**Endpoint:** `POST /api/ai/ambassador`  
- claude-sonnet-4-6 (8192 tokens), MAX_TOOL_TURNS=12, rate 10/min  
- Escapes to haiku-4-5 on failure, then static message

### 4. THE ARCHITECT 4.0 (`backend/tools/architect_tools.py`) — commit `e66157f`

Visual intelligence authority. DALL-E 3 image generation.

**8 tools:**
- `architect_generate_cover_art` — DALL-E 3, WAI visual philosophy applied to every prompt  
- `architect_design_social_asset` — DALL-E 3, 10 platform dimension presets  
- `architect_build_brand_brief` — structured brand identity brief (no image generation)  
- `architect_create_visual_storyboard` — 4-8 scene narrative with emotional arc  
- `architect_audit_brand_consistency` — reviews `db.architect_assets` against visual standard  
- `architect_get_asset_gallery` — MongoDB lookup of generated assets  
- `architect_publish_design_product` — Gumroad T1 → MongoDB T2  
- `architect_list_revenue_streams` — preloaded catalog

**WAI Visual Philosophy (baked into every DALL-E prompt):**
- Primary: Deep gold (#C9A84C) + Midnight black (#0A0A0A) + Cream (#F5F0E8)
- Accent: Royal purple (#4B0082) + Copper (#B87333)
- Tone: Cinematic, Afro-centric, high contrast, culturally sovereign
- Prohibitions: No stock-photo energy. No poverty aesthetics. No cultural caricature.

**Visual-Content bridge:** `[fire]` → hot colors + high contrast, `[whisper]` → intimate + soft light, etc.

**DALL-E 3 formats:** square 1024x1024, portrait 1024x1792, landscape 1792x1024

Assets saved to `db.architect_assets`. Storyboards to `db.architect_storyboards`. Brand briefs to `db.architect_brand_briefs`.

**Revenue streams:**
| ID | Price |
|---|---|
| `brand_identity_kit` | $299.00 |
| `social_asset_pack` | $99.99 |
| `cover_art_single` | $49.99 |
| `visual_storyboard` | $149.99 |
| `brand_audit_report` | $79.99 |
| `wai_internal_design` | $0 |

**Endpoint:** `POST /api/ai/architect`  
- claude-sonnet-4-6 (4096 tokens), MAX_TOOL_TURNS=8, rate 10/min

### 5. Persona strings added (`backend/ai/persona_loader.py`) — commit `e66157f`

- `_AMBASSADOR` — Pipeline protocol (5-step: SCAN→CREATE→DESIGN→PACKAGE→PUBLISH), decision rules, revenue streams, prohibitions
- `_ARCHITECT` — Visual philosophy, image generation protocol, platform intelligence, visual-content bridge, prohibitions

**Total personas: 16** (was 14)  
Registry: director, assistant_director, ancestral_sage, savant_scholar, apprentice, revenue_director, wai_success_engine, product_designer, risk_officer, strategic_navigator, confidentiality_sentinel, elder_council, **cipher, oracle, ambassador, architect**

### 6. Memory System Phase 1 (`backend/ai/memory.py`) — commit `0a6d4df`

**Episodic Memory:**
- `log_episode(db, session_id, persona, user_id, message, reply, tools_used)` → `db.persona_episodes`
- `get_recent_episodes(db, persona, user_id, limit=3)` → last N episodes in chronological order
- Automatically injected into all 4 persona endpoints' system prompts

**Policy Memory:**
- `set_policy_order(db, persona, order_id, content, set_by)` → `db.persona_policies`
- `remove_policy_order(...)` → soft delete (audit trail preserved)
- `get_policy_orders(db, persona)` → global orders + persona-specific orders
- Scope: per-persona OR `__global__` (applies to all personas)
- Automatically injected above episodic memory in system prompts

**Context Injection:** `format_memory_context(episodes, policies, persona)` → compact text block:
```
STANDING ORDERS (set by Executive Director — follow always):
  [always_wai_brand] Always include WAI-Institute branding in content

RECENT MEMORY (last 3 conversations with cipher):
  [2026-05-21 | Tools: cipher_trend_scan]
  User: write a piece about healing...
  Reply: I opened with the wound...
```

**Memory API endpoints:**
```
GET    /api/ai/memory/{persona}           — episodes + policies (admin+)
GET    /api/ai/memory                     — all policy orders (exec only)
POST   /api/ai/memory/policy              — {persona, order_id, content} (exec only)
DELETE /api/ai/memory/policy/{p}/{id}     — deactivate (exec only)
```

All 4 persona endpoints now log every conversation and inject memory context.

---

## CURRENT SYSTEM STATE

### ✅ LIVE AND OPERATIONAL
- Director 4.0 — all 8 tools, dual-model fallback, memory-injected
- Oracle 4.0 — 9 tools, dual-model fallback, episodic + policy memory
- Cipher 4.0 — 9 tools, dual-model fallback, episodic + policy memory
- Ambassador 4.0 — 9 tools, 12-turn pipeline, episodic + policy memory
- Architect 4.0 — 8 tools, DALL-E 3 ready, episodic + policy memory
- /api/ai/cipher/tts — 3-tier voice: ElevenLabs → OpenAI → Text Mode
- Memory System — episodic logs + executive policy orders

### ⚠️ NEEDS ENV VARS SET IN RAILWAY TO UNLOCK FULL CAPABILITY
```
ELEVENLABS_API_KEY  = [from elevenlabs.io → Profile → API Keys → "WAI-Cipher"]
CIPHER_VOICE_ID     = [from elevenlabs.io → Voices → My Voices → copy Voice ID]
CIPHER_BACKUP_VOICE = onyx                          (already default, set explicitly)
GUMROAD_API_KEY     = [from gumroad.com → Settings → Applications → Access Tokens]
```

### ⚠️ STILL PENDING
- **Dormant Mode triggers** — MongoDB-tracked triggers for Ambassador's dormant state (not started)
- **Memory Phase 2** — persona product memory (what each persona has produced), engagement tracking
- **Frontend interface for new personas** — no UI built yet for Cipher, Oracle, Ambassador, Architect
- **Home backup server** — code ready, user hasn't completed setup (see original instructions above)
- **MongoDB Atlas backup** — code ready, user hasn't configured (see original instructions above)

---

## ALL NEW API ENDPOINTS (this session)

```
POST   /api/ai/ambassador                 — Ambassador pipeline (admin+, 10/min)
POST   /api/ai/architect                  — Architect visual intelligence (admin+, 10/min)
POST   /api/ai/cipher/tts                 — Cipher voice 3-tier TTS (admin+, 20/min)
GET    /api/ai/memory/{persona}           — Episodic + policy memory (admin+)
GET    /api/ai/memory                     — All policy orders (exec only)
POST   /api/ai/memory/policy              — Set standing order (exec only)
DELETE /api/ai/memory/policy/{p}/{id}     — Remove standing order (exec only)
```

Plus from prior session (already committed):
```
POST   /api/ai/cipher                     — Cipher spoken word (admin+, 15/min)
POST   /api/ai/oracle                     — Oracle intelligence (admin+, 15/min)
```

---

## GIT COMMIT HISTORY — SESSION 2

```
0a6d4df  feat: Memory System Phase 1 — episodic + policy memory for persona network
e66157f  feat: build THE AMBASSADOR 4.0 and THE ARCHITECT 4.0 personas
1591493  feat: add ElevenLabs TTS client and /api/ai/cipher/tts endpoint
0be2f7b  feat: THE CIPHER 4.0 + THE ORACLE 4.0 personas with full tool suites
e55bc0e  fix: re-apply DirectorWidget touch drag + expand button changes
```

---

## NEW MONGODB COLLECTIONS (this session)

All created automatically on first use — no setup required.

| Collection | Purpose |
|---|---|
| `db.persona_episodes` | Episodic memory — every persona conversation |
| `db.persona_policies` | Policy memory — executive standing orders |
| `db.cipher_audio_budget` | ElevenLabs monthly char budget tracking |
| `db.cipher_tts_cache` | ElevenLabs audio cache (base64) |
| `db.cipher_products` | Cipher revenue products |
| `db.cipher_orders` | Cipher product delivery records |
| `db.oracle_intelligence_reports` | Oracle intelligence report archive |
| `db.oracle_products` | Oracle revenue products |
| `db.oracle_orders` | Oracle product delivery records |
| `db.ambassador_campaigns` | Ambassador campaign packages |
| `db.ambassador_oracle_briefs` | Ambassador Oracle brief archive |
| `db.ambassador_cipher_content` | Ambassador Cipher content archive |
| `db.architect_assets` | Architect generated image assets |
| `db.architect_storyboards` | Architect visual storyboards |
| `db.architect_brand_briefs` | Architect brand identity briefs |
| `db.architect_products` | Architect revenue products |
| `db.director_approvals` | Director approval requests from Ambassador |
| `db.executive_notifications` | Executive notification queue |

---

# SESSION 3 UPDATE — 2026-05-21

**Last commit this session:** `12c9b75`
**Status:** WAI-Institute Level 4 autonomous multi-agent revenue pipeline fully built, tested, committed, and live on Railway.

---

## WHAT WAS BUILT THIS SESSION

### Overview — The Autonomous Revenue Pipeline

The system now runs a continuous, self-operating revenue pipeline:

```
[Social Platforms]
Reddit / RSS / YouTube / Twitter
         │
         ▼
    CulturalScout          ← discovers culturally resonant content
         │ leads
         ▼
  ContextualMatcher        ← matches leads to WAI products
         │ match result
         ▼
 ConversationalEngine      ← crafts authentic outreach (Claude Haiku)
         │ response + preview
         ▼
   TransactionNode         ← generates Lemon Squeezy checkout link
         │ campaign logged
         ▼
   MerchPipeline           ← DALL-E 3 design + Printify POD product
         │
         ▼
  AnalyticsPipeline        ← monthly performance report + recommendations
```

All scanning runs in the background automatically, every 6 hours. No manual trigger required.

---

### Module 1: PersonaManager (`backend/wai_institute/core/persona_manager.py`)

Lifecycle management for all personas.

**Methods:**
- `activate(name, config, mode, scope, activated_by)` — upserts to `db.persona_activations`
- `deactivate(name, reason, archive_memory, can_reactivate, deactivated_by)`
- `evolve(name, add_capabilities, remove_capabilities, update_mandate, ...)` — appends to evolution_log
- `clone(source, new_name, overrides, cloned_by)` — creates derivative persona
- `merge(source_a, source_b, new_name, merged_by)` — union capabilities, combined memory policy
- `status(name)` — returns activation doc from MongoDB
- `list_active()` — returns all active personas
- `bootstrap_core_personas(activated_by)` — idempotent startup bootstrap for all 7 personas

**Called automatically:** `activate_system()` calls `bootstrap_core_personas()` on every startup.

---

### Module 2: PersonaRegistry (`backend/wai_institute/core/persona_registry.py`)

Static configuration for all 7 core personas.

| Persona | Tier | Reports To | Audio Budget |
|---|---|---|---|
| director | 1 | — | 3000 chars/month |
| revenue_director | 1 | director | 2000 chars/month |
| ancestral_sage | 2 | director | 4000 chars/month |
| ambassador | 2 | director | 3000 chars/month |
| cipher | 2 | director | 10000 chars/month |
| oracle | 3 | director | 2000 chars/month |
| architect | 3 | director | 1500 chars/month |

Also loads 10 persona template blueprints from `backend/wai_institute/personas/templates/`.

---

### Module 3: HierarchyEnforcer (`backend/wai_institute/core/hierarchy_enforcer.py`)

Approval gates and policy enforcement.

**Requires Director approval:** system_changes, persona_creation, persona_retirement, major_release, budget_override, new_paid_tool, merge_personas

**Requires Ambassador approval:** campaign_publish (≤$99), persona_deployment, tool_assignment, content_release

**Key methods:**
- `check_action(requesting_persona, action, context)` → {approved, approver, reason}
- `check_audio_budget(persona, chars_requested)` → {approved, status, remaining, pct_used}
- `enforce_free_first(tool)` → {approved, policy}
- `check_cultural_alignment(content, flags)` → keyword-based block check
- `approve_revenue_action(action)` → checks required env keys
- `log_decision(action, persona, decision)` → writes to `db.governance_log`

---

### Module 4: CulturalScout (`backend/wai_institute/pipelines/cultural_scout.py`)

Discovers culturally resonant content across 4 platforms.

**Platforms:**
- **Reddit** — 7 subreddits: blackpoetry, spokenword, poetry, blackculture, afrobeats, blackart, poetryslam. Uses public JSON API (no auth needed).
- **RSS** — Google Trends RSS + Poetry Foundation RSS + NYT Arts RSS
- **YouTube** — YouTube Data API v3 (needs `YOUTUBE_API_KEY`)
- **Twitter/X** — API v2 search (needs `TWITTER_BEARER_TOKEN`, conservative 500 posts/month quota)

**Scoring:** `_score_content(text)` → (score 0-5, theme, intent: seeking|sharing|trending|none)

**Storage:** Deduplicates by `source_id` → stores to `db.scout_leads`

**Env vars needed:** `YOUTUBE_API_KEY`, `TWITTER_BEARER_TOKEN` (optional — degrades gracefully)

---

### Module 5: ContextualMatcher (`backend/wai_institute/pipelines/contextual_matcher.py`)

Matches scout leads to WAI-Institute products using keyword overlap scoring.

**Algorithm:** Jaccard similarity with stopword removal. Boosts: +0.3 for content_type match, +0.2 if product has a published URL.

**Fallback:** When no match found or DB unavailable, returns a curated fallback product so every lead gets a response.

**Strategy mapping:** seeking → direct_recommendation, sharing → community_engagement, trending → trend_response

---

### Module 6: AudioPipeline (`backend/wai_institute/pipelines/audio_pipeline.py`)

ElevenLabs TTS → MongoDB GridFS storage pipeline.

- Stores full audio in GridFS bucket `audio_assets` as `{asset_id}.mp3`
- Stores metadata in `db.audio_asset_meta`
- Returns `access_url: /api/exec/audio/{asset_id}` for streaming
- `CHARS_PER_SECOND = 12` — preview truncates to 15 seconds (180 chars)
- Degrades gracefully without ElevenLabs key (returns text tier)

---

### Module 7: ConversationalEngine (`backend/wai_institute/pipelines/conversational_engine.py`)

Crafts authentic outreach responses using Cipher's voice.

- Calls Claude Haiku with Cipher persona prompt
- Response is 3-5 sentences — acknowledgment first, offer second
- Never sounds like an ad; identifies as a curator
- Includes optional audio preview + checkout link
- Logs campaign to `db.scout_campaigns`
- Falls back to template response if API unavailable

---

### Module 8: TransactionNode (`backend/wai_institute/pipelines/transaction_node.py`)

Generates Lemon Squeezy checkout sessions.

**Checkout tiers:**
- T1: Lemon Squeezy `/v1/checkouts` API (JSON:API format) — needs `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID`
- T2: Direct platform_url from product record
- T3: `{type: "unavailable"}` with clear message

Logs all checkout links to `db.checkout_links`. Records conversions via webhook.

---

### Module 9: MerchPipeline (`backend/wai_institute/pipelines/merch_pipeline.py`)

Print-on-demand pipeline from viral text to live product.

**Flow:** DALL-E 3 typography design → Printify product → Lemon Squeezy listing

**Products:** classic_tee ($29.99), poster_18x24 ($24.99), unisex_hoodie ($49.99), tote_bag ($22.99), mug_11oz ($17.99)

**Without `PRINTIFY_API_KEY`:** Saves as draft with design concept. Draft products appear in the merch list and can be manually uploaded to Printify later.

**WAI brand defaults:** Deep gold (#C9A84C) on midnight black (#0A0A0A), bold serif typography, Afro-centric, cinematic.

---

### Module 10: AnalyticsPipeline (`backend/wai_institute/pipelines/analytics_pipeline.py`)

Full pipeline performance reporting.

**Report sections:** scout, audio, merch, revenue, ab_performance, recommendations

**Recommendations engine:** Flags HIGH priority if no leads, no published products. Flags MEDIUM if drafts pending or match rate < 50%.

---

### Module 11: System Activation (`backend/wai_institute/scripts/system_activation.py`)

Called from FastAPI `on_startup()` — idempotent, safe every restart.

1. Bootstraps all 7 core personas in `db.persona_activations`
2. Creates MongoDB indexes for all pipeline collections
3. Starts background scout scheduler (`asyncio.create_task`)
4. Logs activation event to `db.system_events`

**Background loop:** Scans all platforms → matches unmatched leads → sleeps → repeats. Interval: `SCOUT_INTERVAL_HOURS` (default: 6h).

---

### Module 12: Persona Templates (10 blueprints)

Location: `backend/wai_institute/personas/templates/`

| Template | Tier | Reports To | Role |
|---|---|---|---|
| strategist | 2 | director | Campaign & Growth Strategist |
| producer | 2 | cipher | Content & Audio Production |
| scribe | 3 | ancestral_sage | Documentation & Knowledge |
| analyst | 2 | revenue_director | Data & Revenue Intelligence |
| curator | 2 | cipher | Cultural Content Curator |
| engineer | 2 | architect | Systems Integration |
| storyteller | 2 | cipher | Narrative & Brand Storyteller |
| merchant | 2 | revenue_director | Sales & Commerce |
| guardian | 1 | director | Ethics & Cultural Integrity |
| apprentice | 4 | ancestral_sage | Learning & Development |

Templates are loaded via `get_template(name)` in persona_registry.py. Any template can be activated, cloned, or evolved using PersonaManager.

---

## NEW API ENDPOINTS — SESSION 3 (16 endpoints)

```
POST   /api/exec/scout/run              — Manual full platform scan (exec only, 3/5min)
GET    /api/exec/scout/leads            — List leads (status, min_score, limit filters)
GET    /api/exec/scout/status           — Platform config + lead counts + last scan
POST   /api/exec/scout/match-all        — Batch match all unmatched leads (exec only)
POST   /api/ai/cipher/generate-audio    — ElevenLabs TTS → GridFS (admin+)
GET    /api/exec/audio/{asset_id}       — Stream MP3 from GridFS (any authenticated)
GET    /api/exec/audio                  — List audio assets (persona, limit filters)
POST   /api/exec/merch/create           — POD product from viral text (exec only)
GET    /api/exec/merch                  — List merch products (status filter)
GET    /api/exec/analytics              — Full pipeline analytics (exec only)
GET    /api/exec/personas               — List all persona activation states + registry
POST   /api/exec/personas/{name}/evolve — Add/remove capabilities (exec only)
POST   /api/exec/personas/{name}/activate
POST   /api/exec/personas/{name}/deactivate
POST   /api/exec/scout/craft-response   — Craft personalized outreach for a lead
POST   /api/exec/checkout/conversion    — Record Lemon Squeezy webhook conversion
```

---

## NEW ENVIRONMENT VARIABLES — SESSION 3

Add these to Railway as you acquire the accounts. System runs in degraded/draft mode without them — it will never crash.

```
# Cultural Scout (optional — Reddit and RSS work without keys)
YOUTUBE_API_KEY          = [console.cloud.google.com → YouTube Data API v3]
TWITTER_BEARER_TOKEN     = [developer.twitter.com → App → Bearer Token]

# Scout scheduler
SCOUT_ENABLED            = true    (set to "false" to disable background scanning)
SCOUT_INTERVAL_HOURS     = 6       (how often scout runs — default 6)

# Merch Pipeline
PRINTIFY_API_KEY         = [printify.com → Account → API access]
PRINTIFY_SHOP_ID         = [printify.com → Your shop ID from dashboard URL]

# Sales (already needed, still needed)
LEMON_SQUEEZY_API_KEY    = [app.lemonsqueezy.com → Settings → API]
LEMON_SQUEEZY_STORE_ID   = [app.lemonsqueezy.com → your store ID]
```

---

## NEW MONGODB COLLECTIONS — SESSION 3

All created automatically. No setup required.

| Collection | Purpose |
|---|---|
| `db.scout_leads` | Culturally resonant content discovered by CulturalScout |
| `db.scout_scan_log` | Log of every platform scan run |
| `db.scout_campaigns` | Outreach campaigns crafted by ConversationalEngine |
| `db.audio_asset_meta` | Metadata for all produced audio assets |
| `db.merch_products` | Printify POD product records |
| `db.checkout_links` | Lemon Squeezy checkout sessions |
| `db.persona_activations` | Activation state for all personas |
| `db.governance_log` | All hierarchy enforcement decisions |
| `db.persona_tts_budgets` | Per-persona audio budget tracking |
| `db.system_events` | System activation and event log |

Audio assets stored in MongoDB GridFS bucket `audio_assets` as `{asset_id}.mp3`.

---

## CURRENT SYSTEM STATE — AFTER SESSION 3

### ✅ FULLY OPERATIONAL (needs no new keys)
- All 7 core personas bootstrapped on startup
- CulturalScout running on Reddit + RSS (no API keys needed)
- ContextualMatcher matching leads to products
- ConversationalEngine crafting outreach (uses existing Anthropic key)
- AudioPipeline in text-tier mode (no ElevenLabs key needed for basic operation)
- MerchPipeline creating draft products (no Printify key needed)
- AnalyticsPipeline tracking all pipeline stages
- All 16 new API endpoints live
- 10 persona templates available

### ⚡ UNLOCKED WHEN KEYS ADDED
- `YOUTUBE_API_KEY` → Scout scans YouTube comments
- `TWITTER_BEARER_TOKEN` → Scout scans Twitter/X
- `ELEVENLABS_API_KEY` → Audio pipeline produces real MP3s
- `PRINTIFY_API_KEY` + `PRINTIFY_SHOP_ID` → Merch goes live automatically
- `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID` → Checkout sessions instead of direct links

### ⚠️ STILL PENDING
- Memory Phase 2 — per-persona product memory and engagement tracking
- Frontend UI for new pipeline (admin dashboard for scout leads, analytics view)
- Home backup server — code ready, user hasn't completed setup
- MongoDB Atlas backup — code ready, user hasn't configured

---

## GIT COMMIT HISTORY — SESSION 3

```
12c9b75  feat: WAI-Institute autonomous multi-agent revenue pipeline (Level 4)
9a69ce5  feat: unified autonomous_publish() — replace inline Gumroad in all 4 tools
0f0ae02  feat: ai/publishing.py — 4-tier Lemon Squeezy T1 unified publisher
```
