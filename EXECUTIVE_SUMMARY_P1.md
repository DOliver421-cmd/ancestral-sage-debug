# P1 Hotfix — Executive Summary
**Date:** Feb 2026 · **Severity:** P1 · **Status:** ✅ Resolved

---

## What was fixed
The Deployer Agent flagged a final N+1 database query in the analytics
suite. Root cause was localized to **`GET /api/admin/cohorts`** in
`backend/server.py`: the per-cohort completion count was computed by a
sequential Python loop that issued **2 MongoDB queries per associate**
(`users.find` + `progress.count_documents`). At K cohorts this was
`2K + 1` round-trips — a textbook N+1 that would degrade linearly
under production load.

The loop has been replaced with a **single `progress.aggregate`
pipeline** that joins `progress` → `users` (`$lookup`) and groups
completions by associate. Total round-trips for the endpoint are now
**exactly 2 (one users.aggregate + one progress.aggregate),
constant in K**.

Two supporting indexes were added (idempotent, declared in
`ensure_indexes()` and as a standalone migration):
- `progress(status, user_id)` — accelerates the aggregation `$match`/`$lookup`
- `users(associate, role)` — accelerates the cohort grouping query

## Why it matters
At realistic production scale (10 associates × 100 students × 12
modules) the old endpoint issued **21 sequential queries** and would
eventually time out under concurrent admin dashboard usage. The fix
collapses this to a constant 2 queries with proper indexes, removing
the only remaining deployment-blocking warning from the Deployer
Agent's analytics scan.

## Proof
```
=== /api/admin/cohorts — N+1 proof (PyMongo command monitoring) ===
[k=5     ] K=5   cohorts | mongo_cmds=2 | elapsed=  2.8 ms | cohorts_returned=7
[k=20    ] K=20  cohorts | mongo_cmds=2 | elapsed=  6.4 ms | cohorts_returned=22
[k=50    ] K=50  cohorts | mongo_cmds=2 | elapsed= 13.9 ms | cohorts_returned=52

PASS - query count is constant (2) regardless of K. No N+1.
```
- Full backend pytest suite: **161/161 passing** (159 prior + 2 new
  perf tests in `tests/test_cohorts_perf.py`).
- Functional curl probes against `/api/admin/cohorts` and
  `/api/admin/recent-activity` return correct shapes.

## RBAC re-verified
| Role             | Self routes | Roster | Admin routes | Exec routes | Modify Exec |
|------------------|:-----------:|:------:|:------------:|:-----------:|:-----------:|
| executive_admin  | ✅ 200      | ✅ 200 | ✅ 200       | ✅ 200      | ✅ allowed  |
| admin            | ✅ 200      | ✅ 200 | ✅ 200       | ❌ 403      | ❌ 403      |
| instructor       | ✅ 200      | ✅ 200 | ❌ 403       | ❌ 403      | ❌ 403      |
| student          | ✅ 200      | ❌ 403 | ❌ 403       | ❌ 403      | ❌ 403      |

Server-side immunity: `can_modify()` (server.py:305) compares actor vs
target rank using `ROLE_RANK`. An admin (rank 3) cannot mutate an
executive (rank 4) — guarded on every admin user-management route plus
delete and deactivate.

## Exec admin parity
- Idempotent bootstrap: `seed_users()` upgrades/creates
  `delon.oliver@lightningcityelectric.com` with role `executive_admin`,
  active=true, and `must_change_password=true` whenever the password
  still verifies as the seed default. Standalone script:
  `backend/seed_exec_admin.py`.
- First login redirects the user to `/settings?force=1` (frontend) and
  the flag is cleared only on a successful self-change. Existing
  E2E coverage in `tests/test_rbac_matrix.py`.

## Domain parity (Emergent preview ↔ www.wai-institute.org)
- `frontend/src/lib/api.js` auto-selects same-origin when the browser
  host differs from the build-time `REACT_APP_BACKEND_URL` — no rebuild
  required for the production custom domain.
- `CORS_ORIGINS` in `backend/.env` should list both
  `https://www.wai-institute.org` and `https://wai-institute.org`.
  When `CORS_ORIGINS=*`, credentials are disabled (auth uses Bearer
  tokens in the `Authorization` header, so this is safe).

## Deployment
- Apply: `cd /app/backend && python3 migrations/2026_02_cohorts_n1_indexes.py up && sudo supervisorctl restart backend`
- Roll back: `python3 migrations/2026_02_cohorts_n1_indexes.py down`
  (the new code is forward-compatible with both index states)
- Full runbook: `/app/RUNBOOK_P1.md`

## Next recommended steps
1. **Deploy** — Emergent dashboard → Deploy. Code fixes made in the
   preview environment must be redeployed for `www.wai-institute.org`.
2. **Smoke test in prod** with the curl block from `RUNBOOK_P1.md`.
3. Resume the deferred P0/P1 backlog (Level 2/3/4 lab tracks, real
   file uploads, Resend/Twilio notifications) — no longer blocked.
