# P1 Hotfix — /admin/cohorts N+1 Elimination — Runbook

## What changed
- `backend/server.py` — `cohort_summary()` collapsed the per-cohort
  `find` + `count_documents` loop into a single `progress.aggregate`
  with `$lookup` to `users`.
- Added two supporting indexes via `ensure_indexes()` (declared
  idempotently on every backend startup) **and** as a standalone
  migration in `backend/migrations/2026_02_cohorts_n1_indexes.py`.

## Apply on staging / production

```bash
# 1) Pull latest code on the host.
cd /app

# 2) Apply migration (idempotent — fine to re-run).
cd backend
python3 migrations/2026_02_cohorts_n1_indexes.py up

# 3) Idempotent exec-admin seed (only required if the account was wiped).
python3 seed_exec_admin.py

# 4) Restart the backend so the new code is loaded.
sudo supervisorctl restart backend

# 5) Smoke-test.
curl -fsS "$REACT_APP_BACKEND_URL/api/" | head -1

# 6) Run the full backend test suite.
cd /app/backend && pytest -q

# 7) Run the performance proof.
cd /app/backend && python3 scripts/perf_check.py
```

## Rollback

```bash
# Revert the code with whatever VCS strategy the project uses,
# OR keep the patched server.py and just drop the new indexes:
cd /app/backend
python3 migrations/2026_02_cohorts_n1_indexes.py down
sudo supervisorctl restart backend
```

The code change is fully backward-compatible — even if the new indexes
are missing the aggregation still works (just slightly slower).

## Verification

```bash
# 1) Login as exec admin.
TOKEN=$(curl -s -X POST "$REACT_APP_BACKEND_URL/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"delon.oliver@lightningcityelectric.com","password":"Executive@LCE2026"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# 2) Cohorts endpoint returns 200 + correct shape.
curl -s "$REACT_APP_BACKEND_URL/api/admin/cohorts" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

# 3) Performance proof — should print "PASS — query count is O(1)".
cd /app/backend && python3 scripts/perf_check.py
```

## Required env vars (already configured — do not modify)

| Var                   | Where           | Example value (DO NOT commit real)                 |
|-----------------------|-----------------|----------------------------------------------------|
| `MONGO_URL`           | backend/.env    | `mongodb://localhost:27017`                        |
| `DB_NAME`             | backend/.env    | `lcewai`                                           |
| `JWT_SECRET`          | backend/.env    | 32+ random chars                                   |
| `JWT_EXPIRE_HOURS`    | backend/.env    | `168`                                              |
| `CORS_ORIGINS`        | backend/.env    | `https://www.wai-institute.org,https://wai-institute.org` |
| `EMERGENT_LLM_KEY`    | backend/.env    | (from Emergent Universal Key)                      |
| `REACT_APP_BACKEND_URL` | frontend/.env | `https://www.wai-institute.org`                    |

> **Domain parity:** `frontend/src/lib/api.js` auto-selects same-origin
> when the browser host differs from the build-time
> `REACT_APP_BACKEND_URL`, so the same React build serves both the
> Emergent preview and `https://www.wai-institute.org` without rebuilds.
