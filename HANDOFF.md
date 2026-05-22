# WAI-Institute — Engineering Handoff
*Last updated: 2026-05-22*

---

## The One Problem Blocking Everything

The backend service (`ancestral-sage-debug` on Railway) keeps returning **502 Bad Gateway**.
Until it is stable, the owner cannot log in and the platform is unusable.

**Symptom:** Every request to `ancestral-sage-debug-production.up.railway.app` returns:
```
HTTP/1.1 502 Bad Gateway
X-Railway-Fallback: true
{"status":"error","code":502,"message":"Application failed to respond"}
```

The frontend (`arts-and-tech-production.up.railway.app`) is **healthy and deployed correctly**.
The 502 is entirely a backend issue.

---

## What Is Confirmed True

| Fact | Evidence |
|------|----------|
| Backend DOES start | Railway showed "Active" in deploy logs; `/api/version` returned 200 |
| Backend crashes shortly after starting | Returns 502 minutes/seconds after showing Active |
| No Python syntax errors | `python -m py_compile server.py` passes clean |
| Frontend build is fixed | Three pages had wrong `import api` — fixed in `47e3982` |
| pydantic CORS crash is fixed | `CORS_ORIGINS: list` removed from Settings — fixed in `4836ac2` |
| Exec accounts bootstrap is in place | `seed_users()` creates exec seats on startup if missing |
| Gmail SMTP fallback is wired | Falls back from Resend → Gmail for password reset emails |

---

## What Is NOT Known (The Actual Crash Cause)

**The deploy logs showing the crash were never successfully read.**

Every fix attempt was based on code review and pattern matching — not the actual error.
The owner shared deploy log screenshots but they were too small to read the traceback.
This is the root cause of every "blind attempt" in this session.

### Step 1 for whoever picks this up — get the real error:

1. Railway → `ancestral-sage-debug` service
2. Click the most recent deployment
3. **Deploy Logs** tab
4. Scroll to the **very bottom**
5. Find the Python traceback (`Traceback (most recent call last):`) or `ERROR:` lines
6. That single piece of information ends all guessing

---

## Commits Made This Session

```
915710e  fix: health check timeout 60→120s, max retries 3→10, scout 5-min startup delay
100a1a9  feat: Gmail SMTP fallback + backup collection update
8d219bc  fix: bootstrap exec accounts on startup if missing from DB
4836ac2  fix: remove CORS_ORIGINS from pydantic Settings (confirmed crash fix)
47e3982  fix: correct api import in three pages (confirmed crash fix)
d05da1f  revert: restore python:3.11-slim
```

**`915710e` — SPECULATIVE.** Not based on a confirmed error. Increased timeout and retries,
added 5-minute initial delay before cultural scout fires HTTP requests. May help, may not.

**`4836ac2` and `47e3982` — CONFIRMED fixes.** These were real errors identified from
Railway build/deploy log screenshots.

---

## Railway Variables Required

Set in Railway → `ancestral-sage-debug` → Variables:

| Variable | Status | Notes |
|----------|--------|-------|
| `MONGO_URL` | Must exist | Primary MongoDB URI |
| `DB_NAME` | Must exist | MongoDB database name |
| `JWT_SECRET` | Must exist | Any strong random string |
| `ANTHROPIC_API_KEY` | Must exist | AI chat features |
| `PUBLIC_APP_URL` | Must exist | `https://arts-and-tech-production.up.railway.app` |
| `GMAIL_USER` | For email | Gmail address for password reset |
| `GMAIL_APP_PASSWORD` | For email | 16-char Google App Password |
| `EXEC_FORCE_RESET` | **REMOVE IT** | Set to `1` — causes a logged startup error every deploy. Remove once login works. |
| `RESEND_API_KEY` | Optional | Primary email provider. Gmail is fallback. |

---

## Executive Login Credentials (defaults)

| Email | Default Password |
|-------|-----------------|
| `delon.oliver@lightningcityelectric.com` | `Executive@LCE2026` |
| `youpickeddoliver@gmail.com` | `NamOshun@WAI2026` |
| `souppoetry@gmail.com` | `NamOshun@WAI2026` |

If these don't work, the accounts existed in MongoDB with different passwords.
The bootstrap code creates accounts if missing but does NOT overwrite existing passwords.

### Force-reset procedure (already wired in code):

1. Railway → Variables → Add `EXEC_FORCE_RESET_PASSWORD` = (new password of your choice)
2. `EXEC_FORCE_RESET=1` is already set
3. Redeploy
4. Log in with `delon.oliver@lightningcityelectric.com` + your new password
5. Remove both `EXEC_FORCE_RESET` and `EXEC_FORCE_RESET_PASSWORD` from Variables

---

## Key Files

| File | What it does |
|------|-------------|
| `backend/server.py` | Main FastAPI app — all routes, startup, exec bootstrap |
| `backend/config.py` | Settings — `CORS_ORIGINS` intentionally absent (see comment inside file) |
| `backend/wai_institute/scripts/system_activation.py` | Cultural scout — 5-min delay added |
| `backend/revenue_operations_integration.py` | Module-level import of `jobs.py` — break here = server won't start |
| `backend/jobs.py` | APScheduler — imports `database`, `billing.stripe_service`, `billing.financial_reporting` at module level |
| `railway.toml` | Health check path `/api/version`, timeout 120s, 10 retries |
| `Dockerfile` | Python 3.11-slim, `PYTHONPATH=/app/backend:/app`, port 10000 |

## Import Chain (any failure here = immediate 502, no startup)

```
server.py
  → revenue_operations_integration.py
      → jobs.py
          → database.py
          → billing/stripe_service.py
          → billing/financial_reporting.py
          → config.py
  → recovery.py
  → prompts/ancestral_sage_prompt.py
  → prompts/orchestrator.py
  → prompts/more_department_system.py
  → security/field_authorization.py
```

---

## Service URLs

| | URL |
|-|-----|
| Frontend | `https://arts-and-tech-production.up.railway.app` |
| Backend | `https://ancestral-sage-debug-production.up.railway.app` |
| Health check | `https://ancestral-sage-debug-production.up.railway.app/api/version` |
| GitHub | `https://github.com/DOliver421-cmd/ancestral-sage-debug` |

---

## Honest Assessment

The 502 was not fixed in this session because **the actual crash traceback was never read**.
Two confirmed fixes landed (pydantic crash, frontend imports). The login/502 issue remains.

The right next step is one thing: read the bottom of the deploy logs, find the traceback, fix that line.
