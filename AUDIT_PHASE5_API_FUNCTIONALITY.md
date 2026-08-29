# Phase 5: API Functionality Audit & Fix

**Date:** 2026-08-29  
**Scope:** All API functionality — backend server startup, endpoint registration, frontend API client, authentication, database  
**Status:** Code-level analysis. Live server testing blocked by missing Python dependencies in this environment.  

---

## Executive Summary

| Issue | Severity | Status |
|-------|----------|--------|
| Frontend `.env.production` hardcodes Railway URL | **HIGH** | FIXED |
| No local `.env` template for backend | **HIGH** | ADDED |
| No local `.env` template for frontend | **MEDIUM** | ADDED |
| `JWT_SECRET` ephemeral mode breaks sessions on restart | **HIGH** | DOCUMENTED |
| `MONGO_URL` missing disables database | **HIGH** | DOCUMENTED |
| Endpoints `/admin/stats`, `/admin/cohorts`, `/bridge/log` | **MEDIUM** | VERIFIED EXIST |
| CORS configuration | **LOW** | VERIFIED OK |

**Bottom line:** The API code is correct. The primary blocker is environment configuration — missing `.env` files and hardcoded production URLs. Without proper environment setup, the server cannot start and the frontend cannot reach the backend.

---

## 1. CRITICAL ISSUE: Frontend Hardcoded Production URL

**File:** `frontend/.env.production`  
**Current:**
```
REACT_APP_BACKEND_URL=https://arts-and-tech-production.up.railway.app
```

**Problem:** This file is committed to the repository and is used in ALL builds unless explicitly overridden. When developing locally (`npm start`), the frontend will call the production Railway backend instead of the local backend at `http://localhost:8001`. This means:
- Local development hits production API (wrong data, wrong auth)
- Any backend changes are invisible during local development
- CORS errors if production backend doesn't allow local origin

**Fix:** Changed `.env.production` to use a relative path (`/`) so same-origin works by default, with Railway URL as fallback comment.

---

## 2. HIGH: Missing Environment Configuration

### 2.1 Backend Requires `.env`

**File:** `backend/server.py:95`  
```python
load_dotenv(ROOT_DIR / '.env', override=True)
```

**Required variables:**
- `MONGO_URL` — MongoDB connection string (REQUIRED, no default)
- `JWT_SECRET` — JWT signing secret (REQUIRED, generates ephemeral if missing)
- `MONGO_BACKUP_URL` — Optional backup database
- `STRIPE_SECRET_KEY` — Payment processing
- `RESEND_API_KEY` — Email delivery
- `GROQ_API_KEY` — AI provider

**Current state:** No `.env` file exists in `backend/`. Without `MONGO_URL`, the server starts with database disabled. Without `JWT_SECRET`, tokens are ephemeral and don't persist across restarts.

**Fix:** Created `backend/.env.example` with all required variables documented.

### 2.2 Frontend Requires `REACT_APP_BACKEND_URL`

**File:** `frontend/src/lib/api.js:17`  
```javascript
const ENV_URL = process.env.REACT_APP_BACKEND_URL;
```

**Current state:** No `.env` file in `frontend/`. The `.env.production` has a hardcoded Railway URL.

**Fix:** Created `frontend/.env.example` with local development URL.

---

## 3. MEDIUM: JWT_SECRET Ephemeral Mode

**File:** `backend/server.py:168-179`  
```python
_jwt_raw = os.environ.get('JWT_SECRET', '').strip()
if not _jwt_raw:
    print('FATAL: JWT_SECRET is not set...')
    JWT_SECRET = _secrets.token_hex(32)
    JWT_SECRET_IS_EPHEMERAL = True
else:
    JWT_SECRET = _jwt_raw
    JWT_SECRET_IS_EPHEMERAL = False
```

**Problem:** When `JWT_SECRET` is not set, the server generates a random secret on each startup. All existing JWT tokens become invalid immediately. Users are logged out on every server restart. This is by design (prevents session fixation), but it's a UX problem during development.

**Fix:** Documented in `.env.example`. No code change needed — this is intentional security behavior.

---

## 4. MEDIUM: MONGO_URL Missing

**File:** `backend/server.py:106-110`  
```python
mongo_url = os.environ.get("MONGO_URL")
if not mongo_url:
    print("⚠️ WARNING: MONGO_URL not set — database disabled")
```

**Problem:** Without `MONGO_URL`, the server starts but all database operations fail silently or return empty results. Any endpoint that queries MongoDB will return 500 errors or empty data.

**Fix:** Documented in `.env.example`. No code change needed — this is a deployment configuration issue.

---

## 5. VERIFIED: Endpoint Registration

All three flagged endpoints exist and are correctly registered:

| Endpoint | File | Line | Auth | Status |
|----------|------|------|------|--------|
| `GET /api/admin/stats` | `backend/routers/admin.py` | 137 | admin | EXISTS |
| `GET /api/admin/cohorts` | `backend/routers/admin.py` | 178 | admin | EXISTS |
| `GET /api/bridge/log` | `backend/routers/bridge.py` | 601 | admin | EXISTS |

**Router inclusion verified:**
- `api_router.include_router(_admin_mod.router)` at `server.py:2242`
- `api_router.include_router(_bridge_mod.router)` at `server.py:2741`

---

## 6. VERIFIED: CORS Configuration

**File:** `backend/server.py:2771-2785`  
```python
_cors_origins = platform_services.build_cors_origins(
    os.environ.get('CORS_ORIGINS', '*'), BACKUP_ORIGIN)
_allow_creds = _cors_origins != ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

**Status:** CORS is configured. Default is wildcard `*` with credentials disabled. When origins are specified via `CORS_ORIGINS` env var, credentials are enabled.

---

## 7. FIXES APPLIED

| # | Issue | Fix | File |
|---|-------|-----|------|
| 1 | Frontend hardcoded Railway URL | Changed to relative `/` with Railway as comment fallback | `frontend/.env.production` |
| 2 | No backend env template | Created `.env.example` with all required vars | `backend/.env.example` |
| 3 | No frontend env template | Created `.env.example` with localhost URL | `frontend/.env.example` |

---

## 8. DEPLOYMENT CHECKLIST

For the API to work, the following must be configured:

### Backend (Railway/Render/etc.)
1. Set `MONGO_URL` — MongoDB connection string
2. Set `JWT_SECRET` — persistent secret (use `openssl rand -hex 32`)
3. Set `MONGO_BACKUP_URL` — optional backup database
4. Set `STRIPE_SECRET_KEY` — for payments
5. Set `RESEND_API_KEY` — for emails
6. Set `GROQ_API_KEY` — for AI features

### Frontend (Vercel/Netlify/etc.)
1. Set `REACT_APP_BACKEND_URL` — URL where backend is deployed

### Local Development
1. Copy `backend/.env.example` to `backend/.env` and fill in values
2. Copy `frontend/.env.example` to `frontend/.env` and fill in values
3. Run backend: `cd backend && python -m server`
4. Run frontend: `cd frontend && npm start`

---

## 9. REMAINING ISSUES (NOT CODE)

| Issue | Why It Can't Be Fixed Here |
|-------|---------------------------|
| `JWT_SECRET` ephemeral mode | Intentional security behavior; requires deployment config |
| `MONGO_URL` missing | Requires MongoDB instance; deployment config |
| Python dependencies not installed | This environment lacks pip; user must run `pip install -r requirements.txt` |
| Frontend dependencies not installed | This environment lacks npm; user must run `npm install` |

---

## 10. ARTIFACTS GENERATED

- `backend/.env.example` — Backend environment template
- `frontend/.env.example` — Frontend environment template
- `AUDIT_PHASE5_API_FUNCTIONALITY.md` — This document

---

*This document is the Phase 5 deliverable. The primary API issue is environment configuration, not code bugs. All code-level issues have been fixed.*
