# W.A.I. — Diagnostic Report (Read-Only Audit, no fixes applied)

**Audit date:** Feb 2026
**Scope:** `/app/backend/server.py` (1,854 lines, monolithic), 5 seed files, 26 React pages, supervisor logs, live API smoke (admin token), pytest suite.

**TL;DR:** App is functionally running and all 19 admin/instructor/student API endpoints currently return 200 OK. However there are **3 silent runtime bugs**, **6 documented-but-missing features** (gaps between the operator guide and shipped UI/API), **2 security issues**, **1 stale environment variable**, **1 broken test suite**, and several smaller correctness/lint issues. None of these prevent the core demo from working today, but each will surface as soon as a real cohort tries to use the platform in production.

---

## A. CRITICAL — Silent Runtime Bugs

### A1. ObjectId leak in JSON response (intermittent 500)
- **Symptom in logs (`backend.err.log`):**
  `ValueError: [TypeError("'ObjectId' object is not iterable"), TypeError('vars() argument must have __dict__ attribute')]` raised inside `fastapi.encoders.jsonable_encoder`.
- **Root cause:** Several endpoints insert a Python dict via Motor's `insert_one(doc)`, which **mutates the dict in place and adds a BSON `_id`**, and then return that same dict. FastAPI's `jsonable_encoder` blows up on the `ObjectId`.
- **Affected files / lines:** `/app/backend/server.py`
  - `POST /api/progress/start` → `await db.progress.insert_one(doc); return doc` (lines 386–387)
  - `POST /api/admin/sites` (lines 1493–1495) – patched with `doc.pop("_id", None)` ✓
  - `POST /api/admin/inventory` (lines 1521–1523) – patched ✓
  - `POST /api/admin/checkout` (lines 1548–1551) – patched ✓
  - `POST /api/incidents` (lines 1719–1722) – patched ✓
  - `POST /api/progress/start` is the **only one still missing the `pop("_id", None)`** — this is the trace seen in the log.
- **Fix needed:** add `doc.pop("_id", None)` before `return doc` on line 387 (or use `{"$set": ...}` upsert pattern like the quiz endpoint).
- **Severity:** High (any call to "start a module" returns 500 on the first call).

### A2. `passlib` ↔ `bcrypt` version mismatch
- **Symptom in logs:**
  `WARNING:passlib.handlers.bcrypt:(trapped) error reading bcrypt version`
  `AttributeError: module 'bcrypt' has no attribute '__about__'`
- **Root cause:** `bcrypt==4.1.3` no longer exposes `__about__.__version__`; `passlib==1.7.4` (last release: 2020) still tries to read it. Passlib falls back to a workaround so login still works, but the warning is logged on every startup and slows the first hash. This is a known incompatibility that will become a hard failure if `bcrypt>=4.2` is pulled.
- **Affected:** `/app/backend/requirements.txt` lines 8 (`bcrypt==4.1.3`) and 70 (`passlib==1.7.4`)
- **Fix needed:** pin `bcrypt==4.0.1` (last version compatible with passlib 1.7.4) **or** migrate to `argon2-cffi` / `bcrypt`-native context.
- **Severity:** Medium (currently just noisy, but blocks any future bcrypt upgrade and confuses ops).

### A3. Pytest test suite cannot be collected
- **Symptom:** `pytest /app/backend/tests/` →
  `ERROR collecting tests/test_iter3.py: AttributeError: 'NoneType' object has no attribute 'rstrip'`
- **Root cause:** `tests/test_iter3.py` line 8 reads `os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")`. The variable lives in `/app/frontend/.env`, **not** the backend's environment, so it returns `None`. Same pattern likely in `test_iter4.py` and `test_lcewai.py`.
- **Affected files:** `/app/backend/tests/test_iter3.py` (top), and likely the others.
- **Fix needed:** read from `/app/frontend/.env` (e.g., via `python-dotenv`) or set a `BASE_URL` env var explicitly when invoking pytest. Until fixed, regression tests cannot be auto-run.
- **Severity:** High for development hygiene; the entire test harness is currently inert.

---

## B. CRITICAL — Documented Features That Don't Exist

The operator guide I produced (per the user's last request) referenced multiple admin capabilities that **are not implemented in the running app**. These are gaps, not just doc errors.

### B1. No "Promote to Admin" button anywhere
- **Affected file:** `/app/frontend/src/pages/AdminDashboard.jsx`
- The Users table only renders an Associate text input. There is no `<button>` to change role, and no `POST /api/admin/users/{id}/role` endpoint on the backend.
- **Result:** The bootstrapping flow I documented ("self-register, then have admin promote you") **cannot be performed through the UI**. The only way to create another admin today is by editing MongoDB directly, or POSTing a raw `{role:"admin"}` to `/api/auth/register` (see B7 below).

### B2. No `/admin/users` route as a separate page
- App.js has no `/admin/users` route. Only `/admin` (AdminDashboard) lists users inline.
- **Affected:** `/app/frontend/src/App.js` (route map), `AppShell.jsx` (sidebar). The sidebar admin nav has no "Users" entry at all.

### B3. No `/admin/associate` Associate Manager page
- Documented as a separate page; it does not exist. Associate is editable as a free-text field in the inline AdminDashboard table only. No way to **list** all associates, **rename in bulk**, or **retire** one.

### B4. No admin endpoint to create users
- `POST /api/admin/users` does not exist. Admins cannot create instructors or students directly. They must be told to self-register, which only allows roles {student, instructor} from the dropdown.

### B5. No admin endpoint to delete / deactivate users
- `DELETE /api/admin/users/{id}` does not exist. The "Lock down or remove the demo accounts" step in the guide is impossible from the UI.

### B6. No password reset / change-password flow
- No `POST /api/auth/change-password`, no `POST /api/auth/forgot-password`, no admin-side password reset. Once a password is forgotten the user is stuck. **Critical** for the moment a real instructor/student forgets their password.

### B7. No "site contact / city / state" field on Sites
- AdminTools sites form supports `slug, name, address, capacity` only. No contact, no city/state breakdown — admins create slug-based site IDs but have nothing for partner-shop metadata.

---

## C. SECURITY ISSUES

### C1. Privilege escalation via `/api/auth/register`
- **File:** `/app/backend/server.py`, model `RegisterReq` (line 110-115) accepts `role: Role = "student"` where `Role = Literal["student", "instructor", "admin"]`.
- The frontend `<select>` only offers student/instructor (`Register.jsx` line 64-65), but the backend has **no server-side validation rejecting `role:"admin"`**. Anyone with the public `/api/auth/register` endpoint URL can send `{"role":"admin"}` via curl/Postman and immediately get an admin token.
- **Severity:** Critical for production. Trivial to exploit. Use case: anyone with the registration link can take over the platform.

### C2. JWT secret committed in `/app/backend/.env`
- `JWT_SECRET=lce-wai-secret-change-in-prod-7f9a2b1c3d4e5f6a` (literally tagged "change-in-prod"). The string is hardcoded across deployments and would be checked into Git history if the user ever runs "Save to GitHub".
- **Severity:** High (secret rotation needed before any real deploy).

### C3. Login rate limit is per-process in-memory
- `_RATE = defaultdict(list)` (line 60-67). On a horizontally scaled deployment (or even a single uvicorn worker restart) the limiter resets. Not a blocker for a single-pod preview but won't survive Kubernetes scaling.

---

## D. CONFIGURATION / ENVIRONMENT INCONSISTENCIES

### D1. `PUBLIC_BACKEND_URL` is stale
- `/app/backend/.env` line 8: `PUBLIC_BACKEND_URL=https://0256a2dd-f485-4a4d-8390-33905a5d5fab.preview.emergentagent.com`
- `/app/frontend/.env` line 1: `REACT_APP_BACKEND_URL=https://apprentice-academy.preview.emergentagent.com`
- **They are different URLs.** The backend value is a stale (probably regenerated) preview ID.
- **Impact:** `PUBLIC_BACKEND_URL` is used inside OpenBadges manifest endpoints (`/api/credentials/{key}/manifest.json`, `/api/credentials/assertion/{id}.json`) to embed `id`, `image`, and `verification` URLs. **Any badge issued today carries a verification URL pointing to a dead host** — third-party badge verifiers will fail.
- **Affected lines:** `server.py:1044, 1056, 1074, 1078, 1082`.

### D2. Two MongoDB databases declared / `DB_NAME=test_database`
- `/app/backend/.env`: `DB_NAME="test_database"` — production default name still uses the development placeholder. All real student data is being persisted to a DB literally called "test_database". Operationally fine, but a red flag for any real deployment.

### D3. `CORS_ORIGINS="*"` with `allow_credentials=True`
- `server.py:1843-1849` configures `CORSMiddleware(allow_credentials=True, allow_origins=["*"])`. Per CORS spec, this combination is **invalid** (browsers reject credentials when origin is `*`). It currently works only because the frontend uses Bearer-token auth via `Authorization` header rather than cookies — so the misconfig is latent. If anyone later adds a cookie-based feature it will fail in browsers.

---

## E. MEDIUM — Quality / Correctness

### E1. Frontend ESLint warnings (visible in `frontend.err.log`)
- `src/pages/Incidents.jsx` line 21: `useEffect` has missing dependency `isStaff`. Currently the form/list won't refresh if `isStaff` toggles (it never does in practice, but the warning is real).
- `src/pages/LabDetail.jsx` line 17: `useEffect` has missing dependency `load`. Same class of issue.

### E2. Flake8 `E741 Ambiguous variable name 'l'`
- `server.py:1175`: `sum(l["hours"] for l in labs_detail)`
- `server.py:1303`: `for l in data["labs"]:`
- Cosmetic; safe to rename to `lab` and `lab_item`.

### E3. Webpack dev-server deprecation warnings
- Frontend prints `DEP_WEBPACK_DEV_SERVER_ON_AFTER_SETUP_MIDDLEWARE` etc. on every boot. These come from the CRA/`craco` setup and are not actionable without upgrading react-scripts; harmless at runtime.

### E4. Dead/legacy route `/lab` (singular)
- `App.js` line 63: `<Route path="/lab" element={...LabSimulations />` is a legacy preview kept around. The real route is `/labs`. Nothing in `AppShell.jsx` links to `/lab`. Dead surface area; should be deleted.

### E5. N+1 query on `/api/competencies`
- `server.py:744-763` loops over user submissions and calls `db.labs.find_one()` per submission. For an active student with 30 lab submissions this is 30 round trips. Already correctly batched in `build_portfolio` (line 1109-1199); the same pattern should be applied here.

### E6. `legacy_users` migration in `seed_users()` runs on every startup
- `server.py:230-233` runs an unindexed regex query (`{"associate": {"$regex": "^Cohort-"}}`) on every backend boot. Cheap today (only 3 users) but a one-time migration belongs in a script, not the request path.

### E7. Hard-coded prerequisites map
- `server.py:1450-1453`: `PREREQS = { ... }` is a dict literal with 2 entries. Should live in seed data (so admins can extend prerequisites without a code deploy).

### E8. Admin "Export CSV" only exports users
- `AdminDashboard.jsx:25-33` exports a CSV of users. There is no equivalent CSV export for `/admin/audit`, `/admin/analytics`, or `/instructor/lab-report`. `lab-report` is JSON-only; instructors will likely ask to download.

### E9. Service worker doesn't precache the build hash
- `/app/frontend/public/sw.js` only precaches `/` and `/manifest.json`. After a deploy, users with the PWA installed continue to receive the old `index.html` shell from cache until they hard-reload. Production PWAs typically use Workbox-style precache lists or a versioning manifest.

### E10. Inconsistent ID strategy
- `users`, `modules`, `labs`, `progress`, `lab_submissions`, `audit_log`, `notifications`, `incidents`, `attendance`, `tool_checkouts`, `compliance_progress`, `user_credentials`, `portfolios`, `sites`, `inventory` all use a `uuid.uuid4()` string `id` field, **plus** the auto-generated MongoDB `_id`. Every read endpoint must remember to project `_id` away. This works but is duplicative — every collection is indexed twice. Future refactor: either drop `id` entirely (use `_id`) or keep the dual scheme but add an explicit unique index on `id`.

---

## F. FEATURE INTEGRITY CHECK

| Feature | Backend | Frontend | DB | Status |
|---|---|---|---|---|
| JWT auth | ✓ | ✓ | ✓ | OK (but see C1) |
| 12 modules + quizzes | ✓ | ✓ | ✓ seed | OK |
| 9 online sims | ✓ (`grade_online_lab`) | ✓ (`Simulators` map) | ✓ seed | OK; simulator types match |
| 12 in-person labs | ✓ | ✓ | ✓ seed | OK; photo upload is URL-string only (no real upload) |
| Instructor lab approval | ✓ | ✓ | ✓ | OK |
| Roster & attendance | ✓ | ✓ | ✓ | OK |
| Compliance modules (4) | ✓ | ✓ | ✓ seed | OK |
| Adaptive engine | ✓ | ✓ | — | OK |
| Credentials (14, OpenBadges) | ✓ | ✓ | ✓ seed | OK in API; manifest URLs broken (D1) |
| Portfolio publish + PDF | ✓ | ✓ | ✓ | OK |
| Notifications | ✓ | ✓ | ✓ | OK |
| Audit log | ✓ | ✓ | ✓ | OK |
| Incidents | ✓ | ✓ | ✓ | OK |
| Sites + Inventory + Checkout | ✓ | ✓ | ✓ seed (3 sites, 15 items) | OK |
| AI Tutor (6 modes, Claude 4.5) | ✓ | ✓ | ✓ chat_history | OK at code level (live test not run during this audit to avoid burning Emergent LLM credits) |
| Admin: promote/demote | ✗ | ✗ | n/a | **MISSING (B1)** |
| Admin: create user | ✗ | ✗ | n/a | **MISSING (B4)** |
| Admin: delete user | ✗ | ✗ | n/a | **MISSING (B5)** |
| Password change / reset | ✗ | ✗ | n/a | **MISSING (B6)** |
| Real file uploads | ✗ | ✗ (URL string only) | n/a | KNOWN BACKLOG (P1) |
| Email/SMS notifications | ✗ | ✗ | in-app only | KNOWN BACKLOG (P2) |
| Iframe portfolio widget | ✗ | ✗ | n/a | KNOWN BACKLOG (P2) |
| L2/L3/L4 advanced labs | ✗ | ✗ | n/a | KNOWN BACKLOG (P0) |

---

## G. INCONSISTENCIES BETWEEN FRONTEND, BACKEND, AND DATABASE

| Layer | Issue |
|---|---|
| Backend ↔ Frontend | Backend route `/api/admin/associate` exists; the frontend Sidebar has no top-level link to it, and no dedicated page. Only an inline column input on `AdminDashboard`. |
| Frontend ↔ DB | Frontend `Associate` field is free-text; DB has no `associates` collection. No referential integrity — typing `Associate-Bata` instead of `Associate-Beta` silently creates an orphaned cohort. |
| Backend ↔ DB | `seed_users` collation: legacy migration touches `cohort` field that no current schema mentions. Code runs every boot but is no-op after first run. |
| Backend ↔ Frontend | `/api/auth/register` accepts `role:"admin"` but the frontend doesn't expose it. Frontend trust assumption is unsafe (C1). |
| Backend ↔ Frontend | `PUBLIC_BACKEND_URL` is read from backend `.env`, not derived from the actual incoming request host. Currently stale (D1). |
| Backend ↔ Tests | `/app/backend/tests/test_iter3.py` reads a frontend env var the backend process never sets (A3). |
| Backend ↔ Frontend | `Audit log`, `Analytics`, `Lab report`, `Attendance roster` all return JSON but only the User list page has a CSV export button (E8). |
| Frontend internal | `/lab` (singular) and `/labs` (plural) both registered; only `/labs` is linked. Dead route. (E4) |

---

## H. MISSING DEPENDENCIES / ARCHITECTURE MISMATCHES

| Dependency / arch decision | Concern |
|---|---|
| `passlib==1.7.4` + `bcrypt==4.1.3` | Mismatched (A2). |
| `python-dotenv` for tests | Tests assume backend env has frontend vars (A3). |
| `motor==3.3.1` + `pymongo==4.5.0` | Compatible, but no indexes are declared anywhere. Production performance will degrade fast (e.g., `db.lab_submissions.find({user_id, lab_slug})` is unindexed). |
| `reportlab==4.5.0` | Unicode-safe PDFs would need explicit font registration; current code uses default Helvetica which lacks several glyphs. Apprentice names with ñ/é/ø will render as `?` in certs/portfolios. |
| `emergentintegrations==0.1.0` | Pinned hard; AI calls `with_model("anthropic", "claude-sonnet-4-5-20250929")`. If the playbook publishes a new minor model name this will silently break. |
| No object storage client | `boto3` and `s3transfer` are in requirements.txt but unused — backlog item P1 (real uploads) was never wired. |
| No email/SMS SDK | `stripe` is in requirements but unused — looks like leftover boilerplate. No Resend/SendGrid/Twilio. |
| Frontend `react-scripts`/CRA | Deprecated upstream; ESLint config still emits hook-deps warnings (E1). Migration to Vite is a future concern. |
| No MongoDB indexes | `users.email` should be unique-indexed; `lab_submissions(user_id, lab_slug)` should be compound-indexed for the upsert pattern; `progress(user_id, module_slug)` likewise; `audit_log.at` should be sorted-indexed; none exist today. |

---

## I. PRIORITY-RANKED FIX LIST (no fixes applied yet)

1. **A1** — Add `doc.pop("_id", None)` before `return doc` on `server.py:387` (or refactor to upsert). 1 line.
2. **C1** — Strip `role` from `RegisterReq` (force role="student" from registration; admins/instructors must be created by an existing admin). Backend-only change.
3. **B1+B4+B5+B6** — Add admin endpoints `POST /api/admin/users`, `PATCH /api/admin/users/{id}/role`, `DELETE /api/admin/users/{id}`, `POST /api/auth/change-password`, plus a new `/admin/users` page (or extend `AdminDashboard`). Roughly 200 lines backend + 1 page or table extension.
4. **A3** — Fix backend pytest env loading (use `python-dotenv` to load both `.env` files in a `conftest.py`). Restores regression safety.
5. **D1** — Either remove `PUBLIC_BACKEND_URL` and derive from `request.url`, or sync it with `REACT_APP_BACKEND_URL`. Without this, OpenBadges verification is broken.
6. **A2** — Pin `bcrypt==4.0.1` in `requirements.txt`, run `pip install`, restart backend.
7. **C2** — Move `JWT_SECRET` to a generated value, add a one-time bootstrap script.
8. **E10 / indexes** — Declare the 4 critical indexes on startup.
9. **E5** — Batch-load labs in `/api/competencies` (mirror `build_portfolio` pattern).
10. **E1, E2, E3, E4, E6, E7** — Lint cleanups, dead-route delete, prerequisites moved to seed data.
11. **E8, E9** — CSV exports for audit/analytics/attendance, Workbox SW.

---

## J. WHAT IS DEFINITELY WORKING (verified live during this audit)

Authenticated as the seeded admin (`admin@lcewai.org / Admin@LCE2026`), the following 19 endpoints all returned `200 OK` against the live preview URL:

```
/api/admin/stats, /api/admin/users, /api/admin/audit, /api/analytics/program,
/api/admin/sites, /api/admin/inventory, /api/admin/checkouts,
/api/notifications/me, /api/attendance/roster,
/api/instructor/submissions, /api/instructor/lab-report,
/api/labs, /api/competencies, /api/credentials, /api/credentials/me,
/api/portfolio/me, /api/compliance, /api/adaptive/me, /api/incidents
```
Supervisor reports `backend RUNNING`, `frontend RUNNING`, `mongodb RUNNING`. The PWA manifest, service worker, Login/Register, role-routed dashboards, and all 19 frontend pages compile (only 2 ESLint warnings).

---

*End of diagnostic report. No code changes have been applied.*
