# W.A.I. — Workforce Apprentice Institute (PRD)

## Original Problem Statement
Full-stack training application for the Workforce Apprentice Institute (W.A.I., an LCE-WAI partner program). Electrical apprenticeship training, 12-project Camper-to-Classroom curriculum, safety/solar/off-grid modules, student progress, instructor tools, assessments, certifications. Must serve youth, adults, returning citizens, and workforce trainees. Faith-forward + safety + hands-on.

## User Choices (confirmed)
- Auth: JWT with email/password (Admin/Instructor/Student roles)
- AI: Claude Sonnet 4.5 via Emergent Universal LLM key
- Certificates: Downloadable PDFs (ReportLab)
- Design: Industrial trade-school (ink #0B203F, bone #F7F7F5, copper #C96A35, signal #FFD100)

## Architecture
- Backend: FastAPI + MongoDB (motor), JWT auth (pyjwt + passlib + bcrypt 4.0.1), emergentintegrations for Claude Sonnet 4.5, ReportLab for PDFs.
- Frontend: React 19 + React Router + Tailwind + shadcn/ui + sonner + lucide-react. PWA-installable (manifest.json + sw.js).
- Seed on startup: 12 modules, 9 online labs, 12 in-person labs, 8 competencies, 4 compliance modules, 14 credentials, 3 sites, 15 inventory items, 3 demo users.
- Critical MongoDB indexes declared on startup (`ensure_indexes()`): users.email unique, lab_submissions(user_id, lab_slug) unique, progress(user_id, module_slug) unique, audit_log.at, etc.

## Implemented (rolling changelog)

### Iteration 5 — Diagnostic Fix Pass (Feb 2026)
Acted on `/app/memory/DIAGNOSTIC_REPORT.md`. **All 14 issues resolved or remediated.** 100/100 backend pytest passing.

| Fix | Change |
|---|---|
| **A1** ObjectId leak | `POST /api/progress/start` now `doc.pop("_id", None)` before return. |
| **A2** bcrypt/passlib mismatch | Pinned `bcrypt==4.0.1` (compat with passlib 1.7.4); installed and verified — startup warning gone. |
| **A3** pytest broken | Added `/app/backend/tests/conftest.py` that loads `/app/frontend/.env` so `REACT_APP_BACKEND_URL` is available. **100/100 tests now pass.** |
| **B1** Promote/demote | New `PATCH /api/admin/users/{id}/role` + role `<select>` per row in Admin Dashboard table. |
| **B2/B3** Missing admin pages | Inline extension of Admin Dashboard with create-user form, role select, password-reset, delete buttons. |
| **B4** Create user | New `POST /api/admin/users` (any role). UI: "New User" button on Admin Dashboard. |
| **B5** Delete user | New `DELETE /api/admin/users/{id}` with last-admin-guard + self-delete-guard. UI: trash icon per row. |
| **B6** Password reset | New `POST /api/auth/change-password` (self) + `POST /api/admin/users/{id}/password` (admin). UI: `/settings` page (sidebar nav for all roles) + key icon in Admin Users table. |
| **C1** Privilege escalation | `RegisterReq` no longer accepts `role`. Public `/api/auth/register` is hard-coded to `student`. Frontend Register form replaced role `<select>` with informational notice. Verified: `curl … role:"admin"` now returns `student`. |
| **C2** Hardcoded JWT secret | Documented in operator guide; rotation noted as deploy-time step (no code change here). |
| **D1** Stale PUBLIC_BACKEND_URL | New helper `public_url_from(request)` honors `X-Forwarded-Host`/`X-Forwarded-Proto`; `PUBLIC_BACKEND_URL` env var becomes optional override. OpenBadges manifests/assertions now embed the live preview URL. |
| **D3** CORS wildcard + credentials | Refactored to set `allow_credentials=False` when origins is `*`, `True` when explicit origin list. |
| **E1** ESLint hook deps | `Incidents.jsx` adds `isStaff` to deps; `LabDetail.jsx` adds eslint-disable comment for the intentional exclusion. |
| **E2** Flake8 E741 | Renamed `l` → `lab_item` in `server.py` (lines 1175, 1303). |
| **E4** Dead `/lab` route | Replaced with `<Navigate to="/labs" replace />`; removed unused `LabSimulations` import. |
| **E5** N+1 query | `/api/competencies` now batch-loads labs once via `$in`. |
| **E10** No indexes | Declared 13 indexes on `on_startup` (users, labs, progress, attendance, incidents, etc.). |

### Iteration 4 — Enterprise Hardening
Audit log, in-app notifications, program analytics, attendance, incident reporting, health/version, login rate-limit.

### Iteration 3 — PWA + Adaptive + Compliance + AI Modes
PWA installable, adaptive learning, 4 compliance modules, program-level admin tools (sites + inventory + checkout), AI Tutor `nec_lookup` and `blueprint` modes.

### Iteration 2 — W.A.I. Rebrand + Credentialing + Portfolio
Rebrand to W.A.I., 14 OpenBadges credentials with auto-award engine, portfolio builder + public `/p/{slug}` route + multi-page PDF export.

### Iteration 1 — MVP
JWT auth, 3 dashboards, 12 modules, 9 simulators, 12 in-person labs, 8 competencies, AI Tutor (Claude 4.5), PDF certificates.

## Backend route inventory (all `/api`)
Auth: `/auth/register, /auth/login, /auth/me, /auth/change-password`
Curriculum: `/modules, /modules/{slug}, /progress/me, /progress/start, /progress/quiz`
Labs: `/labs, /labs/{slug}, /labs/{slug}/submit, /labs/submissions/me, /competencies`
Instructor: `/roster, /instructor/submissions, /instructor/submissions/{id}/review, /instructor/lab-report`
Admin users: `/admin/users (GET, POST), /admin/users/{id}/role (PATCH), /admin/users/{id} (DELETE), /admin/users/{id}/password (POST), /admin/associate (POST)`
Admin core: `/admin/stats, /admin/sites (GET/POST), /admin/inventory (GET/POST), /admin/checkout (POST), /admin/checkout/{id}/return (POST), /admin/checkouts (GET), /admin/audit (GET)`
AI: `/ai/chat (6 modes), /ai/history/{session}`
Credentials: `/credentials, /credentials/me, /credentials/{key}/manifest.json, /credentials/assertion/{id}.json`
Portfolio: `/portfolio/me, /portfolio/publish, /portfolio/public/{slug}, /portfolio/export.pdf`
Compliance: `/compliance, /compliance/{slug}, /compliance/{slug}/quiz`
Adaptive: `/adaptive/me`
Notifications: `/notifications/me, /notifications/{id}/read, /notifications/read-all`
Attendance: `/attendance (POST), /attendance/me, /attendance/roster`
Incidents: `/incidents (GET/POST), /incidents/{id}/resolve`
Analytics: `/analytics/program`
Health: `/health, /version, /docs, /openapi.json`
Certs: `/certificates/me, /certificates/{slug}.pdf?token=`

## Frontend pages
Landing, Login, Register, StudentDashboard, InstructorDashboard, AdminDashboard (now with full user management), AdminTools, Analytics, AuditLog, Attendance, Incidents, ModulesList, ModuleView, LabsHub, LabDetail, LabSimulations (legacy), Competencies, InstructorLabs, AITutor, Certificates, Credentials, Portfolio, PublicPortfolio, Adaptive, ComplianceList, ComplianceDetail, **Settings (new — change password)**.

## Test Credentials
admin@lcewai.org / Admin@LCE2026
instructor@lcewai.org / Teach@LCE2026 (Associate-Alpha)
student@lcewai.org / Learn@LCE2026 (Associate-Alpha)

## Test Status
- Backend pytest: **100/100 passing**.
- Live API smoke (admin token): all 19 endpoints + new admin user CRUD + change-password verified 200 OK.
- Frontend: ESLint clean (no hook-deps warnings).

## Backlog / Next Actions

### P0
- Level 2/3/4 Advanced Apprentice Lab Tracks (~21 more intermediate labs).

### P1
- Real file uploads (skill demonstration videos/photos) via object storage.
- Email/SMS notifications (Resend / Twilio) for credential expiry, lab approval/rejection.

### P2
- Iframe-embeddable portfolio widget for partner employer sites.
- Refactor `server.py` (now ~1,990 lines) into a `routers/` package (auth, labs, admin, ai, enterprise, credentials).
- CSV exports on `/admin/audit`, `/admin/analytics`, `/attendance`.
- Workbox-style versioned PWA service worker (avoid stale-shell after deploys).
- Replace in-memory rate limiter with Redis when scaling beyond a single pod.

### P3
- Forgot-password (email magic link) for self-service when users lose access.
- 2FA (TOTP) for admin accounts.
- MFA-protected admin actions (delete user, reset password).
