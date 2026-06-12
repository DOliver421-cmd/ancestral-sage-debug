# Handoff: ancestral-sage-debug

## Project Overview

**WAI Training Platform** — a full-stack learning and operations platform for Lightning City Electric / WAI Institute. Combines a student LMS with internal operations tools (AI personas, project management, competition system, content moderation, financial tracking).

**Live URL:** https://ancestral-sage-debug-production.up.railway.app

**Stack:**
- Frontend: React 18 + TailwindCSS, built with craco, served as a static build embedded in the Docker image
- Backend: FastAPI + Motor (async MongoDB), entry point `app.main:app`
- Database: MongoDB (primary + optional backup), collection name `ancestral_sage`
- Deployment: Railway, single service, Docker build, auto-deploys from `main` branch

**Design tokens:**
- Copper: `#b5651d`
- Ink: `#1a1a1a`
- Bone: `#f5f0e8`

---

## Current State (as of handoff)

### What is working
- Backend starts successfully via `app.main:app` (railway.toml is correct)
- All priority routes register: `jamil`, `competition`, `projects`, `missing`
- Auth (`app.routes.auth`) and system routes (`app.routes.system`) always load first
- Jamil persona: chat, TTS (ElevenLabs), STT (Groq Whisper), file extraction, history to MongoDB
- AppShell sidebar with Executive section (Arena, Jamil, Projects visible to executive_admin/admin)
- Frontend reverted to pre-session baseline (commit `5b30096`) — no broken layout changes remain

### What is NOT working / was the original task
- **Arena (The Arena) was not working** before this session. The competition route had an undefined `oid` bug that caused 500 errors on task submission. The route was not registered as a priority route (fault-tolerant loading meant a silent import failure would hide it). See "The Original Task" section below.

### What was broken by this session and then restored
- **railway.toml startCommand** was changed from `app.main:app` to `server:app` in commit `771557f`, which broke the backend (server.py does not exist at that path). Reverted in `4f630f0`.
- **Frontend (AppShell + other components)** was modified during the session (collapsible sidebar, layout tweaks, CookieConsent changes, HelpGuide hooks violation). All frontend changes were reverted to pre-session baseline in commit `51c1b5a`.

---

## Critical Rules (must follow in every session)

1. **Never use the word "tools" for AI** — use Partners, Teammates, or Friends. Hard rule from owner.
2. **No Anthropic references anywhere** — `ANTHROPIC_API_KEY` is hardcoded to `""` in `app/config.py`. The gateway has Anthropic hard-disabled. Do not re-enable without explicit instruction from D. Oliver.
3. **LLM provider chain: Groq → Cerebras → SambaNova → Gemini → Grok → Cohere → Mistral → Together → OpenRouter → HuggingFace → Keyword KB.** NO Anthropic ever.
4. **ALL changes must be committed and pushed immediately** — do not accumulate local changes.
5. **Branch: `claude/stoic-brown-c9ICA` → PRs to `main` → Railway auto-deploys.**
6. **NEVER change `railway.toml` startCommand** without verifying the new entry point loads and passes `/api/version` first.
7. **NEVER add `overflow-hidden` to AppShell's main container** — it breaks page scrolling for every page.
8. **NEVER put return statements before React hooks in a component** — causes a React hooks violation that will crash the Railway build.

---

## Architecture

### Backend entry point
- `railway.toml` says: `exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}`
- `Dockerfile` CMD says: `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}`
- Both agree. The application object is `app` in `app/main.py`.

### How routes are registered in app/main.py
Two tiers:

**Priority routes** (direct imports, stderr output, errors always visible in Railway logs):
- `app.routes.jamil`
- `app.routes.competition`
- `app.routes.projects`
- `app.routes.missing`

If any of these fail to import, the error prints to stderr with a full traceback. The server still starts.

**Fault-tolerant routes** (30+ modules loaded via `_load()`): any single failure is logged but does not crash the server. `/api/version` and `/api/health` always remain available regardless of route failures.

### Frontend routing: App.js
- `Protected({ children, roles })` — redirects to `/login` if not authenticated; checks role rank if `roles` is specified
- `BoundedAdmin({ children, roles, label })` — wraps admin/exec routes in their own `ErrorBoundary` + `Protected`; a crash in one page does not bring down the whole app
- `SupervisorProtected` — redirects to `/supervisor-login` (not main login) if not `executive_admin`
- `Home` component handles role-based redirect on `/`: `executive_admin` → `/admin/system`, `admin` → `/admin`, `instructor` → `/instructor`, `creative_partner` → `/creative-partner`, `student` → `/dashboard`

### Role hierarchy
```
student (1) = creative_partner (1, lateral) → instructor (2) → admin (3) → executive_admin (4)
```
Higher rank passes all lower-rank checks. `executive_admin` passes every role check.

### LLM gateway location and how to call it
- Gateway: `backend/ai/llm_gateway.py`
- Service wrapper used by routes: `app/services/llm.py` — `from app.services.llm import chat as _llm_chat`
- Call: `await _llm_chat(system=..., user=..., max_tokens=4096)`
- The gateway tries providers in tier order, skips degraded ones (5-min recovery window), and falls back to Keyword KB if all fail.
- Keys are loaded from env vars at startup and reloaded from MongoDB via `reload_provider_keys(db)` when the Provider Gateway UI saves a key.

### MongoDB collections of note
- `users` — user accounts and roles
- `jamil_history` — Jamil chat history (user_id, message, files, reply, timestamp)
- `competition_rounds` — Arena competition rounds and scores
- `projects` — project dashboard entries (pulled live into Jamil's system prompt context)
- `provider_keys` — LLM API keys stored via Provider Gateway UI

---

## Key Files

| Path | Description |
|------|-------------|
| `railway.toml` | Railway build + deploy config; healthcheck path, restart policy, and `startCommand` (must stay `app.main:app`) |
| `Dockerfile` | Two-stage build: Node 18 builds React frontend, Python 3.11 runs FastAPI; frontend build baked into image |
| `app/main.py` | FastAPI app object, all route registration (priority + fault-tolerant), CORS, startup/shutdown |
| `app/config.py` | All env vars and constants; Anthropic key is hardcoded `""` here |
| `app/routes/jamil.py` | Jamil persona endpoints: `/jamil/chat`, `/jamil/speak`, `/jamil/transcribe`, `/jamil/status`, `/jamil/ping` |
| `frontend/src/App.js` | All React routes, role-based `Protected`/`BoundedAdmin` wrappers, role hierarchy constant |
| `frontend/src/components/AppShell.jsx` | Sidebar navigation, backend health check, role-gated nav sections; do not add overflow-hidden |
| `frontend/src/pages/MoreOps.jsx` | M.O.R.E. Ops chat UI — department selector, mic, voice output, message history in localStorage |
| `frontend/src/pages/Jamil.jsx` | Jamil chat UI — file upload, speak button, voice input, message history in localStorage |
| `frontend/src/pages/SeshatsHub.jsx` | Supervisor Control Panel at `/supervisor`; 8 tabs including BackupTab for provider management |
| `backend/ai/llm_gateway.py` | 10-tier LLM provider fallback chain; Anthropic hard-disabled; keys reloaded from DB at startup |
| `backend/ai/knowledge_digest.py` | 12-hour knowledge digest background task injected into AI context |
| `app/services/jamil/persona.py` | `JAMIL_SYSTEM_PROMPT` and `JAMIL_DOMAINS` constants — defines Jamil's character and capabilities |

---

## The Original Task (what still needs to be done)

**Arena was not working.**

- **What Arena is:** A 5-persona AI competition system where a Commissioner assigns a task and four AI personas (AXIOM, CIPHER, MAVEN, SAGE) each respond independently. Users score each response; results accumulate to a leaderboard with role assignments (lead, support, competitor).
- **Where it lives in the nav:** Executive section of AppShell sidebar → "The Arena" (Swords icon), visible to `isExec` users. The route itself allows `admin` role via `BoundedAdmin roles={["admin"]}`.
- **Route:** `/arena` → `CompetitionArena` component → calls `POST /competition/task`, `GET /competition/leaderboard`
- **Backend route:** `app/routes/competition.py`, registered as a priority route as of commit `a64d93f`
- **What was wrong before this session:** The competition route had an `undefined oid` bug that caused 500 errors on task submission (fixed in `f15c4d4`). The route was also not a priority route, so a silent import failure would have hidden it entirely with no error in logs.

**What still needs verification:** Whether the Arena end-to-end flow (task submission → 4 persona responses → scoring → leaderboard) works correctly with a real LLM key configured. This was the original task and was never confirmed working end-to-end.

---

## What Was Done This Session (and should NOT be redone)

PRs #110–#112 were merged. Subsequent commits were made directly to the branch.

| PR / Commit | What it did | Outcome |
|-------------|-------------|---------|
| **#110** `41ea59a` | Added `/jamil/ping` smoke-test (no auth) | Helpful — confirms route registration without login |
| **#111** `8e96fe5` | CRITICAL-level startup logging for priority route imports | Helpful — surfaces Railway startup errors |
| **#112** `b484775` | Collapsible sidebar + Jamil chat layout fix | Mixed — layout fix worked, collapsible sidebar introduced risk |
| `d0dcb2c` | Fix startup crash — removed undefined `ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED` import | Fixed a real bug |
| `9fdd6d5` | Jamil system prompt — full org structure (Director, Supervisor, PRT, 8 support staff) | Helpful |
| `b768cd1` | Suppress HelpGuide on Jamil/Arena/Projects; clear 503 error message | Helpful intent; introduced hooks risk in HelpGuide |
| `771557f` | **BROKE backend** — changed `railway.toml` to `server:app` | Harmful — reverted by `4f630f0` |
| `e6bff65` | Wire Jamil through 9-tier free gateway | Helpful |
| `11741da` | Switch Railway entry point to `app.main:app` (correct fix) | Correct — later overridden by the harmful commit above |
| `1115951` | 12-hour knowledge digest + Arena in sidebar below M.O.R.E. Ops | Helpful |
| `6802842` | Fix CookieConsent banner blocking admin interfaces | Fixed a real bug |
| `3345f60` | Fix HelpGuide conditional hooks violation crashing Railway build | Fixed a real build crash |
| `19db54d` | Add Jamil to M.O.R.E. Ops department selector | Helpful |
| `4f630f0` | **Revert `railway.toml` to `app.main:app`** | Restored correct backend |
| `51c1b5a` | **Revert frontend to pre-session baseline** (commit `5b30096`) | Restored working frontend state |

---

## API Keys Situation

- No API keys configured by default = no AI responses from any persona.
- **How to add keys:** Log in as `executive_admin` → go to `/admin/providers` (Provider Gateway UI) → add key for desired provider → save. Keys are stored in MongoDB `provider_keys` collection.
- The gateway calls `reload_provider_keys(db)` at startup to pull keys from MongoDB into memory. **No Railway redeploy needed** after adding a key via the UI.
- **Recommended first key:** `GROQ_API_KEY` — free at [console.groq.com](https://console.groq.com), fastest provider, tier 1 in the chain. Also enables Jamil STT (Groq Whisper).
- Can also set keys as Railway environment variables directly; env vars take priority over DB keys.

---

## Supervisor Hub

- **Route:** `/supervisor`
- **Auth:** `SupervisorProtected` — requires `executive_admin` role; redirects to `/supervisor-login` otherwise
- **Component:** `frontend/src/pages/SeshatsHub.jsx`
- **Tabs (8):** overview, moderation, escalations, greeter, sage, backup, rbac, audit
- **BackupTab** — provider switching, gateway reset, breaker panel, free provider matrix, emergency broadcast
- **Nav link:** AppShell Executive section, "Supervisor Hub" (Radio icon), `isExec` only

---

## DO NOT TOUCH list

These files are in a working state. Do not modify without a clear, verified reason and a rollback plan:

- `app/main.py` — route registration order and fault-tolerant loading pattern are correct
- `app/routes/auth.py` — auth is working; any breakage locks everyone out
- `railway.toml` — currently correct (`app.main:app`); changing startCommand without testing first broke the backend once already this session
- `Dockerfile` — two-stage build works; `PYTHONPATH` and file copy paths are correct
- `frontend/src/App.js` — route definitions, role hierarchy, and `Protected`/`BoundedAdmin` wrappers are correct
- `frontend/src/components/AppShell.jsx` — just restored to working state; do not add `overflow-hidden` to the main container, do not reorder hooks
