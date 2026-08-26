# WAI Platform Remediation Plan

**Created:** 2026-08-21
**Status:** Phase 0 ✅ + Phase 1 ✅ + IAM Console ✅ + Security Headers ✅ + JWT_SECRET hardened ⚠️ + exec-pipeline auth/DB fix ✅ + gateway text-provider wiring ✅ + per-tier AI budget ✅ — see Addendum 2 for the deploy-status truth and the two remaining launch proofs
**Audience:** Executive (Delon Oliver)
**Last verified:** 2026-08-26 (against committed `main`; live human-proofs still open)
**CRITICAL NOTE:** Prior session claimed JWT_SECRET was "fail-closed" — it was NOT. Previous agent wrote false verification. JWT_SECRET still silently regenerated on every boot with only a warning. Fixed in this session: now emits CRITICAL log. Still ephemeral in dev — must set persistent JWT_SECRET in Railway.

---

## Audit Findings (verified against deployed code, not handoff documents)

### What actually runs

- **`backend/server.py`** — 2,447-line FastAPI monolith. Real auth (JWT HS256 + bcrypt),
  8-tier RBAC, MongoDB via Motor, LLM gateway (10-tier free-first chain),
  payments (Lemon Squeezy/Gumroad), seeding, handbooks, compliance, labs.
- **`backend/routers/`** — 41 route modules (auth, admin, users, billing, ai, jamil,
  competition, creator, payments, scholarships, social, playlist, etc.).
- **`frontend/`** — React 18 + Tailwind, 131 page components. Built with craco,
  served from the same Docker image.
- **`backend/seed*.py`** — seed data for modules, labs, credentials, compliance.
  Real and used.
- **`backend/ai/`** — AI subsystem: persona_loader (17 personas + unified model),
  llm_gateway, jamil persona/extractor, team_monitor, source_protocol, prompt_guard.

### What was dead code (DELETED in Phase 1)

- **`app/`** — 86 Python files. A parallel FastAPI app that was NEVER deployed.
  Three surviving files (Jamil persona, Jamil extractor, team monitor) were migrated
  to `backend/ai/`. The rest was dead. **Deleted.**
- **`src/`** — PipelineManager, ShopifyService, AudioService + tests. Imported
  lazily in server.py with fallback. Near-zero production value.
  **Deleted; PipelineManager routes removed from server.py.**
- **`tests/test_smoke.py`** — imported from deleted `app/` tree. **Deleted.**
- **`backend/tests/test_auth_config.py`** — imported `app.config`. **Deleted.**
- **`backend/tests/test_supabase_config.py`** — imported `app.core.supabase`. **Deleted.**
- **`public/Ai racist data.pdf`** and **UNIVERSAL LITIGATION WEAPON v1.html** —
  toxic public files. **Deleted.**

### What is dangerous (fixed in Phase 0)

| Issue | Before | After |
|---|---|---|
| Seed password in source | `SEED_PW = "Andsome70421"` in `seed_exec_admin.py` | Must set `EXEC_SEED_PASSWORD` env var; script refuses to run without it |
| JWT secret default | `"dev-secret-change-in-production"` | Now emits CRITICAL log when JWT_SECRET not set (still generates ephemeral key for dev). **Set persistent JWT_SECRET in Railway.** |
| Fabricated exec email | `delon.oliver@lightningcityelectric.com` as `EXEC_ADMIN_EMAIL` default in 12 files | Removed from all defaults; existing accounts with this email auto-demoted at startup |
| Hardcoded exec password in tests | `"Executive@LCE2026"` in 7 test files | Tests now read from `TEST_EXEC_PW` env var |
| Agent manipulation documents | 40+ handoff/legal/exhibit files in root | Quarantined in `Noisy Assets/` with ignore directive in AGENTS.md |

---

## Phase 0: Security & Fabrication Cleanup ✅ COMPLETE

- [x] Remove hardcoded seed password — env-driven, fail-closed.
- [x] Remove fabricated exec email — no auto-created phantom accounts.
- [x] JWT secret hardened — CRITICAL log when missing, ephemeral key still generated (set persistent key in Railway). |
- [x] Quarantine 60+ noise documents into `Noisy Assets/`.
- [x] Remove `COPY memory/` from Dockerfile (folder no longer exists).
- [x] Remove hardcoded exec passwords from test files.
- [x] Add AGENTS.md guardrail — agents instructed to ignore Noisy Assets.

---

## Phase 1: Architecture Rationalization ✅ COMPLETE

### 1.1 Extract surviving dependencies from `app/`

Three files from `app/` were actually used by deployed `server.py`:
- `app/services/jamil/persona.py` → **Migrated** to `backend/ai/jamil_persona.py`
- `app/services/jamil/extractor.py` → **Migrated** to `backend/ai/jamil_extractor.py`
- `app/services/team_monitor.py` → **Migrated** to `backend/ai/team_monitor.py`

Imports updated in `server.py`, `backend/routers/jamil.py`, `backend/routers/billing.py`.
`app/` directory deleted (86 files). Dockerfile updated to remove `COPY app/` and `COPY src/`.

### 1.2 Dead code removal

- `app/` — 86 files deleted (all deps migrated to `backend/ai/`).
- `src/` — deleted (PipelineManager, ShopifyService, AudioService, tests).
- PipelineManager removed from `server.py` startup + 2 dead endpoints (`/exec/pipeline/process`, `/exec/pipeline/process-batch`) deleted.
- `backend/ai/controller.py` import fixed: `from backend.server` → `from server`.
- Three dead test files deleted (`test_smoke.py`, `test_auth_config.py`, `test_supabase_config.py`).
- `PYTHONPATH` in Dockerfile simplified: `/app/backend:/app` → `/app/backend`.

### 1.3 Configuration cleanup

- `backend/config.py` was the only config source after `app/config.py` deletion. No further consolidation needed.

---

## Phase 2: IAM Console — Built ✅

### 2.1 Identity & Access Management (IAM) Console

Built a dedicated `/admin/iam` module with:

**Backend** (`backend/routers/users.py`):
- `GET /admin/users` — search by name/email, filter by role/active/associate
- `GET /admin/users/{uid}` — single-user read for atomic enforcement verification
- `POST /admin/users` — create with any role (exec-only for executive_admin)
- `PATCH /admin/users/{uid}/role` — change role with verified re-read (atomic enforcement)
- `PATCH /admin/users/{uid}/active` — activate/deactivate with guards
- `POST /admin/users/{uid}/password` — admin password reset (forces rotation on next login)
- `DELETE /admin/users/{uid}` — delete with safety guards
- `GET /admin/rbac/matrix` — read privilege matrix (exec-only)
- `PATCH /admin/rbac/matrix` — update privilege matrix (exec-only)

**Atomic enforcement:** After role change, the API re-reads the document from DB and returns
`{verified: {role, is_active, token_version}}` in the same response. The frontend also issues
a secondary GET to `GET /admin/users/{uid}` after every mutation to prove DB state matches intent.

**Frontend** (`frontend/src/pages/IAMConsole.jsx`):
- Two tabs: **Users** (searchable table with inline role/action controls) and **Privilege Matrix** (role × permission grid)
- Clean "AI business office" design using project theme (bone/ink/copper)
- Atomic enforcement: spinner shows during verification, toast confirms verified state
- Role dropdown shows only roles the actor can grant; self-edit blocked
- Password reset prompts for temp password; forces `must_change_password` on target
- Privilege matrix: toggle each permission per role, saved to platform config store

**Wiring:**
- Route: `/admin/iam` → `IAMConsole` (admin+ roles, with back link to `/admin`)
- Nav: AppShell Administration section → "IAM Console" nav entry

### 2.2 Other platform features (verified working)

- **Landing page:** scroll works (no body overflow:hidden); NotificationBell portal fix deployed
- **NotificationBell:** now renders via `createPortal(document.body)` — no longer clipped by sidebar `overflow-y-auto`
- **Backend CRUD:** All user management endpoints functional with role guards, session invalidation, and audit logging

---

## Phase 3: Compliance & Legal

### 3.1 Human oversight
- Audit log captures every privileged action (who, what, when, target).
- Dashboard endpoints exist (`GET /admin/audit`, `GET /admin/users/{uid}/audit`).
- LLM gateway has full provider health tracking and token budget enforcement.

### 3.2 E-commerce compliance
- Payment providers: Lemon Squeezy (digital products + subscriptions) + Gumroad (one-time).
- Env vars must be set in Railway (LEMON_SQUEEZY_API_KEY, GUMROAD_API_KEY).

### 3.3 AI compliance
- Anthropic disabled by default (`ANTHROPIC_IS_ENABLED` must be explicitly set).
- All calls go through `call_llm()` gateway with per-user daily budgets.
- Token budget enforced; provider fallback chain documented.

### 3.4 CRUD matrix
Every entity has Create/Read/Update/Delete, RBAC-gated:
- **Users:** full CRUD (GET/POST/PATCH/DELETE /admin/users)
- **Modules, Labs, Compliance:** seeded + editable via admin
- **Courses (Creator):** full CRUD via creator routes + admin moderation
- **Payments:** checkout + admin view
- **Posts/Needs/Chats:** CRUD via M.O.R.E. routes
- **Projects:** CRUD via projects routes
- **Personas:** loaded from persona_loader, toggleable via mode_system

### 3.5 Exec control matrix
- Emergency password reset (exec-unlock endpoint, force-reset flag). ✅
- Provider key management (add, remove, test API keys). ✅
- User account suspension/reinstatement. ✅ (via /admin/users/{uid}/active)
- Site mode (maintenance, active). ✅ (via platform_flags + enforce_platform_flags middleware)
- AI budget and spend enforcement. ✅ (via LLM gateway hourly token cap)
- RBAC privilege matrix. ✅ (via /admin/rbac/matrix)

---

## Phase 4: Launch Readiness

### 4.1 Go-live checklist
- [ ] Domain resolves to Railway deployment (wai-institute.org → Railway)
- [ ] HTTPS enforced (Railway handles this)
- [ ] No default passwords in any env (verified: EXEC_DEFAULT_PASSWORD empty in code)
- [ ] No fabricated emails in any default (verified: `delon.oliver@lightningcityelectric.com` only in LEGACY_EXEC_EMAILS demotion set)
- [ ] Payments test transaction completed
- [ ] All 4 baseline tests pass (auth, course, commerce, admin flows)
- [ ] Remediation Plan is current and truthful ← this document

---

## Verification Log

### Grep proofs (2026-08-21)
```
app/ imports in backend runtime:     0
src/ imports in backend:             0
_require_reason references:          0
Hardcoded exec passwords:            0
Fabricated email in defaults:        0 (only in LEGACY_EXEC_EMAILS demotion set)
server.py syntax:                    OK
server.py line count:                2,447
app/ directory exists:               NO
src/ directory exists:               NO
tests/test_smoke.py exists:          NO
tests/test_auth_config.py exists:    NO
tests/test_supabase_config.py exists: NO
```

### Files changed this session
| File | Change |
|---|---|
| `app/` (86 files) | DELETED |
| `src/` (11 files) | DELETED |
| `tests/test_smoke.py` | DELETED |
| `backend/tests/test_auth_config.py` | DELETED |
| `backend/tests/test_supabase_config.py` | DELETED |
| `public/Ai racist data.pdf` | DELETED |
| `public/UNIVERSAL LITIGATION WEAPON v1.html` | DELETED |
| `Dockerfile` | Removed `COPY src/`, `COPY app/`, fixed PYTHONPATH |
| `backend/server.py` | Removed PipelineManager import + 2 dead endpoints |
| `backend/ai/controller.py` | Fixed `from backend.server` → `from server` |
| `backend/routers/users.py` | Added `GET /admin/users/{uid}` + atomic enforcement re-read |
| `frontend/src/pages/IAMConsole.jsx` | NEW: IAM Console page |
| `frontend/src/App.js` | Added IAMConsole import + route |
| `frontend/src/components/AppShell.jsx` | Added IAM Console nav entry |
| `frontend/src/components/NotificationBell.jsx` | Portal fix (createPortal) |

---

## How This Plan Stays Real

1. **Every checkbox refers to code, not prose.** A task is done when a diff proves it.
2. **This document is overwritable by future sessions but must report true state.**
3. **"Delete" means delete.** Shell pages with no API will be removed, not hidden.
4. **The platform ships with only working features.** If it's not tested, it's not in the navigation.
5. **Verification log is live proof**, not claims.

---

*Generated from verified code inspection, not handoff documents.*
*No fabricated emails, no hardcoded passwords, no dead architectures.*

---

## Addendum 2 — August 26, 2026: deploy-status truth + remaining proof

**What is verified and on `main` (pushed, deploying on next Railway build):**
- `64c3106` + `ac4f003` — executive pipeline + member-project routers now auth/read the DB through the same secret/handle the rest of the app uses (they previously rejected every valid token / crashed on a missing DB handle).
- `1797a26` — executive dashboard no longer hides $0 revenue / critical runway behind a healthy-looking frame.
- `98c79cd` — OpenAI and DeepSeek are now text-AI tiers (were set in Railway but invisible to the chat chain); per-user daily AI budget scales by feature tier (free base, member +25%, plus +35%, pro +45%, patron +50%); Arena/exec health surfaces count the owner keys.

**What the plan's older lines mean after this:** the items that earlier read "working tree / not deployed" (root-file serving, Saga crash, CSP, store catalog) are committed on `main` and deploy together. Any line claiming "verified against deployed code" should now be read as "verified against committed `main`, deploy pending."

**The two launch proofs that remain code-independent (cannot be signed off here):**
1. One real purchase end-to-end against the real DB (the revenue/model gate — see REPORT 3/5).
2. One real account created+used against the real DB (the identity gate — includes the owner create-account control in the exec panel).

Until a human runs those two on the deployed site, the platform is wired and deploying but **not launch-ready** — the verdict stays NO-GO (REPORT 5).
