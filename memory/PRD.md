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

## Test Credentials (current)
admin@lcewai.org / Admin@LCE2026
instructor@lcewai.org / Teach@LCE2026 (Associate-Alpha)
student@lcewai.org / Learn@LCE2026 (Associate-Alpha)
