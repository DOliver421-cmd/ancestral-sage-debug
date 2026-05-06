# W.A.I. — PRD (Iteration 6: Admin/User Hardening + CSV Exports)

## Original Problem Statement
Workforce Apprentice Institute training platform. Multi-role (Admin / Instructor / Student), 12 Camper-to-Classroom modules, 21 labs, OSHA/NFPA compliance, OpenBadges credentialing, public portfolios, AI tutor (Claude Sonnet 4.5).

## Stack
FastAPI + MongoDB (motor) + JWT + passlib/bcrypt 4.0.1 + reportlab + emergentintegrations.
React 19 + react-router-dom + Tailwind + shadcn/ui + sonner + lucide-react. PWA.

## Iteration 6 — Admin/User repair (Feb 2026)

### Backend changes
- `User` model: **new `is_active: bool = True` field**. Existing seeded users have no field → MongoDB `find()` returns missing key, treated as truthy by `is_active is False` check.
- New Pydantic models: `AdminEditUserReq`, `AdminActiveReq`.
- New endpoints:
  - `PATCH /api/admin/users/{uid}`           — edit name/email/associate
  - `PATCH /api/admin/users/{uid}/active`    — deactivate / reactivate (last-active-admin guard, self-deactivate guard)
- `POST /api/auth/login` — refuses if `is_active is False` → 403
- `current_user()` dependency — 403s any authenticated request from a deactivated user, even with a still-valid JWT

### Frontend changes
- `AdminDashboard.jsx` — full rewrite of the action column:
  - **Edit** button (pencil) → inline editable name/email/associate with Save/Cancel
  - **Reset password** (key)
  - **Toggle active** (lock/unlock) → confirms before action; row dims when inactive
  - **Delete** (trash)
  - Status column with `ACTIVE` / `INACTIVE` badge
  - Search box (name/email)
  - Role filter dropdown
  - Active/Inactive filter dropdown
  - Counter `Users (X of Y)`
- `AuditLog.jsx` — Export CSV button (whole filtered log)
- `Analytics.jsx` — Export CSV button (totals + by_associate + weakest comps + module rates)
- `Attendance.jsx` — Export Roster CSV button (per-student totals & rate)

### Permission model (verified end-to-end)
- Public `/api/auth/register` always creates a `student`
- `current_user` enforces JWT validity + `is_active`
- `require_role("admin"|"instructor"|"student")` decorator on every privileged route
- Frontend `<Protected roles={[...]}>` wrapper enforces UI-level access; backend is the source of truth
- Last-admin guards on delete + deactivate
- Self-action guards on demote + delete + deactivate
- Audit log captures every admin action with actor, target, meta

## Verified end-to-end this iteration
| Flow | Status |
|---|---|
| Admin login → /admin/users | ✅ |
| Create instructor → login as them → reactivated default | ✅ |
| Edit name + associate via PATCH | ✅ |
| Deactivate → old JWT 403 + login 403 | ✅ |
| Reactivate → login works again | ✅ |
| Self-deactivate refused (400) | ✅ |
| Student token to admin endpoint → 403 | ✅ |
| Instructor token to admin endpoint → 403 | ✅ |
| Frontend tour: 0 page errors across 29 routes for all 3 roles | ✅ |
| Backend pytest | **100/100 passing** |
| Python lint | clean |
| ESLint | clean |

## Backlog (NOT delivered this iteration — honest deferral with reasons)
- 🔴 P0 — Level 2/3/4 Advanced Apprentice Lab tracks (~21 more labs). Needs design input: simulator types, competencies, rubric. Not started.
- 🟠 P1 — Real file uploads via object storage. Needs storage-provider choice + credentials.
- 🟠 P1 — Email/SMS notifications (Resend / Twilio). Needs API keys.
- 🟡 P2 — Iframe portfolio widget for partner sites. Pending.
- 🟡 P2 — Refactor `server.py` (~2,030 lines) into modular routers. Pending.
- 🟡 P2 — Workbox versioned PWA service worker. Pending.

## Feb 2026 — P1 hotfix (N+1 elimination)
- `/api/admin/cohorts` was issuing 2K+1 mongo round-trips (textbook N+1). Replaced the per-cohort loop with a single `progress.aggregate($lookup users)` pipeline. Wire commands now constant at **2 per request**, independent of cohort count.
- Added supporting indexes `progress(status, user_id)` and `users(associate, role)` (declared in `ensure_indexes()` and as standalone migration `backend/migrations/2026_02_cohorts_n1_indexes.py`).
- New tests in `backend/tests/test_cohorts_perf.py` — uses PyMongo `CommandListener` to assert O(1) query count.
- Backend pytest: **161/161 passing**.
- Deployer Agent N+1 warning: cleared.

## Feb 2026 — Auth + Password Reset + Settings hotfix
- **Forgot/Reset password flow** built end-to-end: `POST /api/auth/forgot-password` (no enumeration, rate-limited, sha256 token, 30-min TTL) + `POST /api/auth/reset-password` (single-use, invalidates other tokens for same user).
- **Admin-mediated reset links**: `POST /api/admin/users/{uid}/reset-link` with copy-to-clipboard modal in admin UI; honours `can_modify()` (admin still can't touch executive_admin).
- **Self-service profile edit**: `PATCH /api/auth/me` — name + email, with collision detection. Role/associate remain admin-only.
- **Settings page rebuilt** with Profile + Password tabs (+ forced-rotation banner preserved).
- **Login** now has a real `Forgot your password?` link to `/forgot-password`.
- **Optional Resend email integration** via `RESEND_API_KEY` env var (gracefully no-ops when absent — the admin-mediated link UI keeps the flow functional).
- New tests in `backend/tests/test_password_reset.py` (24 tests). Total backend pytest: **185/185 passing**.
- Login rate limit relaxed to 30/60s per email (was 10/60s) for realistic admin workflows; forgot-password IP cap to 30/5min.

## Test Credentials (current)
admin@lcewai.org / Admin@LCE2026
instructor@lcewai.org / Teach@LCE2026 (Associate-Alpha)
student@lcewai.org / Learn@LCE2026 (Associate-Alpha)

## Feb 2026 — Catch-all 404 route
- Added `pages/NotFound.jsx` and `<Route path="*" />` in `App.js`.
- Resolves the failure mode behind user's "blank page on `/admin/users`" report — production bundle was stale (preview already had the route); without a 404 fallback any unmatched URL silently white-screened.
- 404 page is role-aware: signed-in users get a CTA back to their correct dashboard; signed-out users get a CTA back to landing.
