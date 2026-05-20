# WAI-Institute / M.O.R.E. Help Center — Session Handoff

## Who You Are
- **Name:** Delon Oliver (NAM Oshun)
- **Role:** Executive Director, owner of M.O.R.E. Help Center and WAI-Institute (wai-institute.org)
- **Preference:** Direct, literal communication. Use exact table formats for instructions. No ambiguity.

---

## The Project
- **GitHub Repo:** https://github.com/DOliver421-cmd/ancestral-sage-debug
- **Local Clone:** `C:\Users\lenovo\ancestral-sage-debug`
- **Stack:**
  - Frontend: React (CRACO) — `/frontend`
  - Backend: FastAPI/Python — `/backend`
  - AI Personas: Director, Ancestral Sage, Scholar, Assistant Director, Council of 24 Elders
- **Custom Domain:** `wai-institute.org` (DNS managed on Namecheap)

---

## Current Deployment State (as of 2026-05-20)

### Railway (PRIMARY — temporarily down)
- **Outage cause:** Google Cloud blocked Railway's account on 2026-05-19
- **Status:** Recovering — non-enterprise deploys paused, workloads gradually coming back
- **Monitor:** https://status.railway.app
- **Frontend URL:** `ancestral-sage-debug-production.up.railway.app`
- **Backend URL:** Unknown — confirm in Railway dashboard when back online
- **Latest code is here** — Railway has the most up-to-date deployed version

### Render (FALLBACK — currently serving wai-institute.org)
- **Frontend:** `ancestral-sage-debug` (Static site) — `ancestral-sage-debug.onrender.com`
  - Deployed but running OLD version (last successful build was ~1 day ago)
  - Out of free build minutes — newer commits have NOT deployed
  - Billing catch-22: upgrade requires successful deploy, deploy requires build minutes
  - **Fix:** Contact Render support at render.com/support — explain the catch-22
- **Backend:** `ancestral-sage-backend` (Python/FastAPI web service, free tier)
  - URL: `https://ancestral-sage-backend.onrender.com`
  - Running but on free tier (spins down after inactivity, 50s cold start)
  - Latest deploy also blocked due to build minute exhaustion

### Namecheap DNS (wai-institute.org) — CURRENT STATE
| Type | Host | Value |
|------|------|-------|
| CNAME Record | www | `ancestral-sage-debug.onrender.com` |
| URL Redirect Record | @ | `https://www.wai-institute.org` |

- **www.wai-institute.org** → Render frontend (live, SSL valid)
- **wai-institute.org** → redirects to www (live)

---

## What Was Done This Session

### Code Commits (all pushed to main)
1. `7f2849c` — Added `beautifulsoup4==4.13.4` to `backend/requirements.txt` (was missing, needed by `director_tools.py` for web search/fetch). Aligned port fallback to 10000 in Dockerfile and railway.toml.
2. `a3caacb` — Stub deploy attempt (minimal HTML splash page) to try to clear Render build block. Did not work.
3. `245cee0` — Reverted `render.yaml` back to real frontend build after stub experiment.

### DNS Changes Made
- Removed old Railway A Record (`216.24.57.4`) and Railway CNAME records
- Set `www` CNAME to Render
- Set `@` to URL Redirect → `https://www.wai-institute.org`
- Result: site is now live on Render with valid SSL while Railway recovers

---

## What Still Needs To Be Done

### When Railway Comes Back Online
1. **Verify Railway frontend is serving** — visit `ancestral-sage-debug-production.up.railway.app`
2. **Find Railway backend URL** — check Railway dashboard for the backend service URL
3. **Fix `api.wai-institute.org` DNS** — currently missing from Namecheap, needs to be added:

| Type | Host | Value |
|------|------|-------|
| CNAME Record | api | `[Railway backend URL]` |

4. **Flip DNS back to Railway** in Namecheap:

| Type | Host | Value |
|------|------|-------|
| CNAME Record | www | `ancestral-sage-debug-production.up.railway.app` |
| A Record | @ | `216.24.57.4` |

5. **Delete the Render URL Redirect** for `@` after flipping back

### Render Billing Catch-22
- Contact Render support: explain you're out of free build minutes and the upgrade requires a successful deploy
- Email: support@render.com or render.com/support
- They can grant build minutes or manually flip the account

### Frontend API Config
- `frontend/src/lib/api.js` reads `REACT_APP_BACKEND_URL` env var
- On Render dashboard for `ancestral-sage-debug`: set `REACT_APP_BACKEND_URL` = `https://ancestral-sage-backend.onrender.com`
- On Railway: should already be set to Railway backend URL — verify when Railway is back

---

## Windows Environment Notes
- PowerShell execution policy may be set to Restricted — fix with:
  `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force`
- Node.js/npm may not be installed — install via:
  `winget install OpenJS.NodeJS.LTS`
- Always use PowerShell syntax (not bash) for commands on this machine

---

## Key Files
| File | Purpose |
|------|---------|
| `render.yaml` | Render frontend static site config |
| `railway.toml` | Railway backend Docker build config |
| `Dockerfile` | Backend Docker image (Python/FastAPI) |
| `backend/requirements.txt` | Python dependencies |
| `backend/server.py` | Main FastAPI app (5000+ lines) |
| `backend/tools/director_tools.py` | Director AI tool suite (web search, email, file read) |
| `frontend/src/lib/api.js` | API base URL config |
| `frontend/src/components/DirectorWidget.jsx` | Director AI chat widget |

---

## Paste This Into New Claude Session To Resume
> "I am Delon Oliver (NAM Oshun), owner of WAI-Institute and M.O.R.E. Help Center. 
> My GitHub repo is https://github.com/DOliver421-cmd/ancestral-sage-debug, local clone at C:\Users\lenovo\ancestral-sage-debug. 
> Read HANDOFF.md in the repo root for full context on where we left off. 
> Railway is recovering from a Google Cloud outage. Site is temporarily on Render at www.wai-institute.org. 
> Continue from where the handoff left off."
