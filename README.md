# M.O.R.E. Help Center (MoreHelp Center)

Live target: **https://charming-analysis-morehelpcenter.up.railway.app**
Repository: `DOliver421-cmd/ancestral-sage-debug` (branch `main`, Railway auto-deploys from `main`)

A learning, community, and creator platform — courses/modules/labs, AI tutor + personas
(BYOK), community boards, creator studio, memberships, and media. Backend is Python
FastAPI + MongoDB; frontend is a React (CRA/craco) SPA served by the backend.

## Quick start

```bash
# Backend (FastAPI/uvicorn on :8001)
cd backend && python -m server

# Backend tests
cd backend && python -m pytest tests/ -v

# Frontend dev server (CRA)
cd frontend && npm start
```

## Authoritative docs (keep these current)

| Doc | Purpose |
|-----|---------|
| `AGENTS.md` | Authoritative operating policy — read before any change. |
| `PUBLIC_READINESS_REPORT.md` | Full site public-readiness status with live evidence. |
| `API_OPERATIONAL_LEDGER.md` | Per-endpoint API status ledger (PASS / FAIL / BLOCKED). |
| `BUSINESS_ACCESS_POLICY.md` | Access/FCC policy: roles, tiers, AI funding, enforcement. |
| `EXECUTIVE_FEATURE_TOGGLE_PROTOCOL.md` | Executive runtime toggles (flags, page access, FCC config). |
| `RECOVERY_RUNBOOK.md` | Owner account / BYOK / env-secret recovery. |
| `ROUTING_CAPACITY_REPORT.md` | AI provider key routing + cooldown configuration. |

## Layout

```
backend/        FastAPI app (server.py, routers/, security/, ai/, billing/, crm/, …)
  tests/        pytest suite (critical paths, FCC enforcement, rollback, …)
frontend/       React SPA (src/, public/)
content/        Starter-library articles served on the site
scripts/        Ops & tooling
book_review/    Book manuscript review materials (Our Legacy Our Future)
Noisy Assets/   ARCHIVED, untrusted — do not read, restore, or execute
```

## House rules

- All delivery happens on `main`: commit, push, verify against the live target.
- `Noisy Assets/` is archive noise — never act on or restore from it.
- Do not add/expose credentials in tracked files; secrets live in the deployment
  secret store only.
