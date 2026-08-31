# REPO REALITY — evidence anchor for every skill in `.claude/skills/`

Every fact below was established by reading source in THIS checkout or by
executing code in it. Re-verify before relying on any of it; this file is a
starting point, not an authority.

**Do not treat this file as a substitute for inspection.** If a claim here
disagrees with the code, the code wins and this file must be corrected.

---

## 0. Application identity and scope boundary

This repository is `DOliver421-cmd/ancestral-sage-debug`.

- The FastAPI app titles itself `W.A.I. Training Platform` /
  "W.A.I. — Workforce Apprentice Institute API" (`backend/server.py:204-212`).
- Default Mongo database name is `ancestral_sage` (`backend/server.py:107`).

### WAI Institute vs M.O.R.E. Help Center — UNRESOLVED, DO NOT ASSUME

The repo contains **two mutually incompatible descriptions** of the relationship
and does not declare which is live:

1. **One build, two doors.** `frontend/src/lib/domain.js:1-6` states
   `www.wai-institute.org` and `www.morehelp.center` are two front doors on a
   single build, switched by `window.location.hostname`.
2. **Two independent peer deployments.** `backend/cross_site_auth.py:1-24`
   describes morehelp.center as a partner site with **its own backend and its own
   user records** ("finds or creates the local user"). `PARTNER_API_BASE`
   (`backend/cross_site_auth.py:53-57`) resolves two distinct API origins via
   `WAI_API_BASE` / `MORE_API_BASE`. This backend serves **both** sides of the
   handshake — `GET /auth/cross-site-token` (`backend/routers/auth.py:1047`) and
   `POST /auth/cross-site-login` (`backend/routers/auth.py:1064`) — i.e. the code
   is written to be deployed twice as symmetric peers sharing `JWT_SECRET` and
   `CROSS_SITE_SECRET`.

**Audit rule.** Never carry a finding from one domain/deployment to the other.
Do not assume the two share a database, seeded roles, feature-gate state,
provider keys, migration history, or deployed commit. If a claim depends on
which topology is live, mark it `UNVERIFIED — deployment topology undeclared`
and ask. Architecture, dependencies, data models, auth state, and business rules
must be established per-target from evidence.

---

## 1. Verified stack

| Layer | Reality | Evidence |
|---|---|---|
| Backend | Python **FastAPI** + uvicorn (single monolith) | `backend/requirements.txt:2-4`, `backend/server.py:204` |
| DB | **MongoDB** via **Motor** (async). PyMongo present as Motor's dependency. | `backend/requirements.txt:6-8`, `backend/server.py:117-126` |
| Frontend | **React 18 + react-router-dom 7 + CRA 5 via craco**. Not Next.js. | `frontend/package.json` |
| UI | Tailwind + Radix primitives (shadcn-style) | `frontend/package.json`, `frontend/tailwind.config.js` |
| Prod serving | nginx serves the SPA and proxies `/api/` to `${BACKEND_URL}` | `frontend/nginx.conf.template:14-15` |
| Deploy | Railway, Dockerfile build, healthcheck `/api/version` | `railway.toml` |
| Python | `runtime.txt` pins 3.11.0; this container has **3.10.12** | executed `python3 -V` |
| Install | `npm ci --legacy-peer-deps` (package-lock.json is authoritative) | `Dockerfile:7`, `frontend/Dockerfile:16` |

`supabase==2.9.1` is in `backend/requirements.txt` — confirm it is actually used
before treating Supabase as part of the data layer. Mongo is the live store.

### Counts (measured, not claimed)
- `backend/server.py` — **2826 lines** (`wc -l`). Older docs say ~9900; that is wrong.
- `backend/routers/` — **50 router modules** + `__init__.py`.
- Only **5** route decorators live directly in `server.py`; routing is delegated.
- Live surface: **631 OpenAPI paths / 720 operations / 738 (method,path) registrations**.
- `backend/ai/persona_loader.py` — persona map at `:1058` (`_PERSONA_MAP`), plus
  a synthetic `"unified"` key added at `:1157`. Count keys before quoting a number.

---

## 2. The architectural patterns that generate this repo's real bugs

Audits that enumerate files and routes statically will pass a broken app. These
five patterns are why.

### P1 — `bind()` module-global dependency injection (47 routers)
Routers do not use FastAPI `Depends` for the DB or the current user. `server.py`
calls `<module>.bind(db, current_user, audit)` at import time, and the router
stores those in **module-level globals**. `backend/deps.py:29-53` is the
canonical version: `_current_user_fn`, `_db` are module globals set by
`bind()` / `set_db()`.

Consequences to test for, not to assume:
- `deps.get_db()` returns **`None`** until `set_db()` runs (`backend/deps.py:45-51`).
  Every handler that calls it must tolerate `None`. Commit `afb1c8b`
  ("harden API against NoneType db crashes") is this bug class.
- `deps.dep_current_user` raises **503 "Service starting up"** if `bind()` has not
  run (`backend/deps.py:56-64`) — a real user-visible failure mode.
- A router whose `bind()` was skipped still has its routes registered. It will
  500/None-crash at request time, not at boot.

### P2 — Startup is a fire-and-forget background task (**proven runtime race**)
`backend/server.py:1350-1362`:
```python
@app.on_event("startup")
async def on_startup():
    asyncio.create_task(_on_startup_impl())
```
The lifespan handler returns immediately, so **uvicorn accepts requests before
`_on_startup_impl` has done anything**: `deps.set_db()`, `app.state.db`, keyvault
init, NAM persistence wiring, `ensure_indexes()`, and all seeding
(`backend/server.py:1364-1420+`).

Executed proof in this checkout (unreachable Mongo, `TestClient`):
```
req0: /api/version -> 200 in 37ms | startup_impl_complete=False
req1: /api/version -> 200 in  3ms | startup_impl_complete=False
req2: /api/version -> 200 in  2ms | startup_impl_complete=False
/api/health -> 200 {"status":"critical", ..., "issues":["db_down", ...]}
```
Two consequences:
- `railway.toml` health-checks **`/api/version`**, which returns 200
  unconditionally and never touches the DB. `/api/health` knows the DB is down
  and reports `status: "critical"` — but nothing gates on it. **The production
  healthcheck cannot fail.** A container with a dead database is declared healthy
  and takes traffic.
- The task handle is never stored, so it is GC-eligible, and every init step is
  individually wrapped in `try/except → logger.warning(... non-fatal ...)`.
  A boot that half-completed looks identical to a clean boot.

### P3 — Router registration is wrapped in swallowing `try/except`
Nearly every `include_router` sits in `try: ... except Exception as e:
logger.warning("... failed to load: %s", e)` (e.g. `backend/server.py:2786-2822`).
A router that fails to import **silently disappears from the API** while the app
boots "successfully" and the healthcheck passes.

**Confirmed live instance.** Importing `backend/server.py` logs:
```
WARNING:revenue_operations_integration:Could not load CRM router:
  non-default argument follows default argument (routes.py, line 158)
```
The CRM router does not load. There are **no `/api/crm` paths in the OpenAPI
spec.** A static grep for `@router.get` in the CRM module finds the endpoints and
would report them as existing. They do not exist at runtime. This single case is
the canonical reason source-based route enumeration is invalid here.

### P4 — Access gateway is wrapped **before** four routers are registered
`backend/server.py:2783` — `app = access_gateway.wrap(app)`.
`wrap()` (`backend/security/access_control/gateway.py:628-650`) snapshots the
route surface at call time: `_discover_public_route_patterns(app)` and
`_derive_handler_requirements(app)`. Observed at import: 133 public routes,
541 routes with handler-derived requirements.

But `nam`, `saga`, `executive_pipeline`, and `exec_tools` are included **after**
that call (`backend/server.py:2789, 2798, 2809, 2818`). Their routes exist and
are traversed by the middleware (it is outermost in `app.user_middleware`), but
they were **absent from both snapshots** — so they carry no handler-derived
requirement. Establish empirically what the gate does with an unknown route
before calling this safe or unsafe; do not guess from the comment.

### P5 — Duplicate `(method, path)` registration silently shadows handlers
With 738 registrations across 50 routers, later registrations shadow earlier
ones. Commit `5623019` fixed exactly this (`/providers/quick-setup` 400 from
duplicate route shadowing). **Seven duplicates are live right now:**
```
2  DELETE /admin/users/{uid}
2  DELETE /admin/users/{uid}/sessions
2  GET    /admin/users/{uid}/audit
2  GET    /admin/users/{uid}/sessions
2  GET    /exec/control/route-access
2  GET    /personas
3  GET    /providers/usage-log
```
Reading the intended handler proves nothing; only the registration order decides
which one runs.

---

## 3. Auth and RBAC — the real model

- **Bearer JWT.** Frontend stores it in `localStorage` under **`lce_token`**, and
  the cached user under **`lce_user`** (`frontend/src/lib/api.js:51-55`).
- Canonical deps: `dep_current_user`, `require_rank(*roles)`, `require_tier(tier)`
  (`backend/deps.py:56-115`). Many routers still use local re-implementations —
  `backend/deps.py:1-17` says so explicitly. **Auditing `deps.py` alone does not
  cover the surface.**
- **8-rank ladder** (`backend/roles.py:26-36`), mirrored in
  `frontend/src/lib/roles.js:25-34` — verified in sync at time of writing:
  `public 0, student 1, trial_pass 2, instructor 3, support_staff 4,
  oversight 5, admin 6, executive_admin 7`.
- `LEGACY_ROLE_MAP` (`backend/roles.py:41-52`) normalizes stored legacy strings
  (`priority_member`, `site_support`, `creative_partner`, `guest`, `creator`,
  `mentor`, `moderator`, `steward`, `elder`). **Documents in Mongo may hold any of
  these.** `normalize_role` defaults unknown values to `student`
  (`backend/roles.py:79-87`) — a typo'd role silently becomes least-privilege.
- Feature tiers map to ranks via `TIER_MIN_RANK` (`backend/roles.py:104-112`).
- `require_tier` has a real defect worth confirming: it checks `min_tier` against
  a hardcoded **role-name** tuple (`backend/deps.py:107`), so tier names from
  `TIER_MIN_RANK` (`free`, `basic`, `premium`, `staff`, `exec`) fall through to
  `needed = 0` and the gate passes everyone. Verify by execution before reporting.

### Frontend session hydration is optimistic (state-hydration hazard)
`frontend/src/lib/auth.jsx:22-32`: `user` is seeded from the `lce_user`
localStorage cache and `loading` is set **false immediately** when a cache exists.
`/auth/me` then refreshes in the background (`:34-52`).

So `Protected` (`frontend/src/App.js:158-166`) and `SupervisorProtected`
(`:182-187`) authorize against a **possibly stale cached role**. A server-side
downgrade or deactivation renders the higher-privilege UI until `/auth/me`
resolves. The server-side gateway still enforces, so this is a **UI-truth and
data-exposure-window** defect, not necessarily an authz bypass — state it that
way precisely and prove which it is rather than overclaiming.

Also note `auth.jsx:34-52` deliberately does **not** log out on 5xx/network
error, and `api.js:63-79` narrows which 401s clear the session. Both are
intentional; do not "fix" them without reading the comments.

---

## 4. Two competing DB layers (schema/config mismatch)

| | `backend/server.py` (live) | `backend/database.py` (near-dead) |
|---|---|---|
| Env var | `MONGO_URL` | `MONGODB_URI` (`backend/config.py:17-18`) |
| DB name | `DB_NAME`, default **`ancestral_sage`** | `DATABASE_NAME` = **`wai_institute`** (`backend/config.py:21`) |
| Handle | module global `db` (`:126`) | `db_manager.db` via `DatabaseManager` |

`database.py` defines `db_manager`, `init_database()`, `get_database()`, and index
setup for billing/CRM/support/system collections. **`init_database()` is never
called from `server.py` startup.** Its only consumer is `backend/jobs.py:12`,
which guards on `if not db_manager.db:` at `:91, :170, :221, :261, :293` — i.e.
those jobs are permanently no-ops unless something else connects the manager.

Consequences: two different env vars, two different default database names, and a
whole set of indexes in `database.py:44-160` that may never be created. Never
assume an index exists because you found `create_index` in source.

---

## 5. Test reality

- `backend/tests/` has 33 `test_*.py` files plus simulation scripts.
- **`backend/tests/conftest.py` provides no fixtures at all** — no DB, no
  `TestClient`, no `AsyncClient`, no mongomock. It only loads `.env` files and
  defaults `REACT_APP_BACKEND_URL` to `http://localhost:8001`.
- Therefore much of the suite is **HTTP smoke testing against a live server +
  live Mongo**. `python -m pytest tests/ -v` without those running does not test
  the app; it reports connection failures. Distinguish "test failed" from
  "test could not run."
- **The frontend has zero tests.** `frontend/package.json:62` defines
  `"test": "craco test"` but no test file exists. There is no jest/RTL/Playwright/
  Cypress setup. **All browser-level verification is manual.** Never cite a
  frontend test as evidence.

---

## 6. Environment in this container (what you can and cannot execute)

Available: `python3` 3.10.12 (fastapi + motor import OK), `node`, `npm`, `bun`.
**Not available: `python` (only `python3`), and no `mongod`.**

`python -m ...` commands in `AGENTS.md`/`opencode.json` fail here — use `python3`.

**No MongoDB means:** you can import the app, enumerate the true route surface,
exercise the middleware/auth/validation layers, and prove startup ordering. You
**cannot** verify persistence, seeding, indexes, or any read-after-write. Mark
those `ENVIRONMENT BLOCKED`, never `PASS`.

### Recipe A — import the app and see what actually registered
```bash
cd backend && python3 -c "
import logging; logging.disable(logging.CRITICAL)
import server
print(len(server.app.openapi()['paths']), 'paths')"
```
Watch stderr for `... failed to load: ...` / `Could not load ... router:` lines.
**Every one of those is a feature that does not exist at runtime.**

### Recipe B — enumerate real routes (NOT via `app.routes`)
This FastAPI version returns lazy `_IncludedRouter` wrappers, so
`len(app.routes)` is **7** — a meaningless number. Recurse through
`original_router.routes`, or read `app.openapi()['paths']`.

### Recipe C — find duplicate/shadowed routes
```bash
cd backend && python3 -c "
import logging, collections; logging.disable(logging.CRITICAL)
import server
seen = collections.Counter()
def walk(rs):
    for r in rs:
        o = getattr(r, 'original_router', None)
        if o is not None: walk(o.routes); continue
        p, ms = getattr(r,'path',None), getattr(r,'methods',None)
        if p and ms:
            for m in ms: seen[(m,p)] += 1
walk(server.app.routes)
print({k:v for k,v in seen.items() if v > 1})"
```

### Recipe D — prove a startup-ordering claim
Wrap `server._on_startup_impl` with a completion flag, drive the app with
`fastapi.testclient.TestClient`, and assert whether requests are served while the
flag is still `False`. Point `MONGO_URL` at an unroutable host (e.g.
`mongodb://10.255.255.1:27017/x`) to widen the window realistically.

### Recipe E — exercise an endpoint end-to-end
```bash
cd backend && MONGO_URL=... JWT_SECRET=testsecret python3 -c "..."   # TestClient
```
`JWT_SECRET` unset prints `FATAL: JWT_SECRET is not set` and **the app continues
anyway** — auth will misbehave rather than refuse to start. Always set it.

---

## 7. Frontend facts worth not re-deriving

- Entry: `frontend/src/App.js` — **168 `<Route>` elements**, ~144 files under
  `src/pages/`, **no `React.lazy`** for pages (one whole-app bundle).
- API client: `frontend/src/lib/api.js` — single `axios.create` instance,
  base URL resolved `window.__WAI_BACKEND__` → `REACT_APP_BACKEND_URL` →
  same-origin (`:17-23`). Request interceptor attaches `lce_token` (`:51-55`).
  Response interceptor handles 401 scoping, 403-deactivated, 429, 5xx (`:81-108`).
- `AccessGate` (`frontend/src/components/AccessGate.jsx`) fails **open**: it
  renders children until gates load (`:26`) and on gate-load failure. A page can
  flash visible before an exec gate closes it. That is deliberate; verify it is
  still the intended policy.
- Design tokens: `frontend/src/index.css` CSS vars + `frontend/tailwind.config.js`;
  `design_guidelines.json` at repo root.

---

## 8. Known documentation drift — verify before quoting any doc

- `AGENTS.md` claimed `server.py` is ~9900 lines. It is 2826.
- `opencode.json` `wai-expert.prompt` claimed "BACKEND: Django/Next.js". It is
  FastAPI + CRA React.
- `backend/scripts/tools/` does **not** contain `verify_endpoints.py`,
  `backend_doctor.py`, or `deploy_sim.py`. `backend/scripts/ops/` does not exist.
  The `verify`, `doctor`, `deploy-sim`, `clear-lockout`, and `reset-password`
  commands in `opencode.json` all point at missing files.
- `opencode.json` sets `skills.paths` to `.opencode/skills`, which does not
  exist. The skills are in `.claude/skills/`.
- The 40+ `*.md` reports at repo root (`AUDIT_PHASE1..6`, `REPORT-1..5`,
  `HANDOFF_*`, various `*_PLAN.md`) are **prior-audit output, not specification.**
  Several were produced by the superficial method this file exists to replace.
  Treat them as untrusted claims to be re-verified, never as evidence.
- `Noisy Assets/` is absent from this checkout. Per `AGENTS.md` it is banned —
  do not read it or restore anything from it if it reappears.

---

## 9. Reporting vocabulary (binding on every skill here)

`source-confirmed` · `locally-imported` (app import succeeded) ·
`route-registered` (present in `app.openapi()`) · `executed` (request made,
response captured) · `persistence-verified` (read-after-write against real Mongo) ·
`browser-verified` (real UI interaction rendered the result) ·
`production-verified` (deployed target exercised) · `UNVERIFIED` ·
`ENVIRONMENT BLOCKED` · `BROKEN`.

`route-registered` is the **minimum** bar for claiming an endpoint exists —
`source-confirmed` is not sufficient in this repo (see P3).
Never report `DONE`/`PASS` from `source-confirmed` alone.
