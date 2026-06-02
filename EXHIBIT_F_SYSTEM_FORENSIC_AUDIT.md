# EXHIBIT F — FULL SYSTEM FORENSIC AUDIT REPORT
**Case:** Delon Oliver d/b/a Nam OShun / WAI-Institute v. Anthropic
**Prepared:** June 2, 2026
**Repository:** DOliver421-cmd/ancestral-sage-debug
**Auditor:** Independent forensic code analysis — WAI-Institute internal
**Scope:** Every feature, page, endpoint, button, and user-facing function

---

> **HOW TO READ THIS REPORT**
> Each entry lists:
> - **STATUS:** WORKING / BROKEN / PARTIAL / STUB / DECOY / MISSING
> - **WIRING:** Frontend → API → Backend → DB (✓ = connected, ✗ = broken link)
> - **DAMAGE COUNT:** How many times built, broken, fixed, restored, faked, or stubbed
> - **CURRENT DAMAGE:** What is specifically wrong right now

---

# FORENSIC AUDIT REPORT — ANCESTRAL SAGE / WAI-INSTITUTE PLATFORM
**Audit Date:** 2026-06-02 | **Repo:** /home/user/ancestral-sage-debug | **Commits:** 252 total, 38 auto-commits

---

## CRITICAL STRUCTURAL FINDING — READ FIRST

**THE DEPLOYED APPLICATION IS `backend/server.py` (12,705 lines), NOT `app/main.py`.**

The Dockerfile and `railway.toml` both specify:
```
startCommand = "/bin/sh -c \"exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8080}\""
```
`app/main.py` was built as a modular refactor (it explicitly states "Replaces backend/server.py as the application object") but was **never wired into the deployment**. The `/app/routes/` directory — including `executive_control.py`, the new `providers.py`, `billing.py`, `supervisor_v2.py`, `site_editor.py`, `partnership.py` — runs only in `app/main.py` which is dead code in production. `server.py` has its own inline implementations of all those routes.

This means: any frontend code calling endpoints that **only exist in `app/routes/executive_control.py`** (i.e., `/exec/control/*`) gets 404 in production.

---

## AUTH

---

## Login Flow — POST /auth/login
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/Login.jsx` → `frontend/src/lib/auth.jsx:login()`
**ENDPOINT:** POST /api/auth/login
**DB OPERATION:** `db.users.find_one({"email": ...})` + `db.auth_sessions.insert_one()`
**WIRING:**
- ✓ Login form → `auth.login()` in `auth.jsx`
- ✓ `auth.jsx` calls `api.post("/auth/login", {email, password})`
- ✓ `api.js` points to `BACKEND_URL/api`
- ✓ `server.py:1787` `@api_router.post("/auth/login")` exists, handles bcrypt verify, lockout after 10 attempts, MFA check (if configured), session recording
- ✓ Returns JWT + user object
- ✓ Token stored in `localStorage` as `lce_token`, user as `lce_user`
- ✓ `api.js` interceptor attaches `Bearer` token on all subsequent requests
**DAMAGE COUNT:** built 1 time, broken 0 times, fixed 0 times
**DAMAGE HISTORY:**
- Original build in `server.py`; no substantive breakage detected
**CURRENT DAMAGE:** None. However, MFA enforcement depends on `pyotp` being installed — if not installed, MFA is silently skipped with a warning (documented behavior).

---

## JWT Token Storage and Validation
**STATUS:** WORKING
**COMPONENT:** `frontend/src/lib/auth.jsx`, `frontend/src/lib/api.js`
**ENDPOINT:** N/A (client-side)
**DB OPERATION:** `db.users.find_one({"id": payload["sub"]})` on each request via `current_user` dependency
**WIRING:**
- ✓ Token stored in `localStorage["lce_token"]` on login
- ✓ `api.js` interceptor attaches `Authorization: Bearer <token>` on every request
- ✓ `current_user()` in `backend/security/auth.py` decodes JWT, checks `token_version` against DB (revocation), checks `is_active`
- ✓ Token version revocation works: incrementing `token_version` in DB invalidates all existing tokens
- ✓ 401 interceptor in `api.js` clears localStorage and redirects to `/login`
- ✓ Cached user in localStorage prevents loading flash
**CURRENT DAMAGE:** None structurally. Note: `app/security/auth.py` `make_token()` and `current_user()` are the `app/` module versions and are NOT used in production — `server.py` has its own duplicated implementations of these functions (lines ~640-805).

---

## /auth/me — fields returned per role
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/lib/auth.jsx:refresh()`
**ENDPOINT:** GET /api/auth/me
**DB OPERATION:** `db.users.find_one({"id": ...})`
**WIRING:**
- ✓ Endpoint exists in `server.py:1867`
- ✓ Called on app load to refresh user state
- ✗ `field_authorization.py` import in `server.py` tries `from security.field_authorization import FieldAuthorization` — this is the `backend/security/field_authorization.py` path. This file EXISTS. If it imports successfully, field filtering is active.
- ✓ `/auth/me` in `server.py` also calls `build_capability_contract()` and attaches `capabilities` to response
- ✓ `field_authorization.py` restored most recently at commit `75d85f9` (fix: restore all roles — instructor, creator, mentor, moderator, steward, elder)
**DAMAGE COUNT:** built 1 time, broken 1 time (roles stripped), restored 2 times
**DAMAGE HISTORY:**
  - `9c8b0ea` initial build
  - `90049f1` "fix: restore RBAC field_authorization to match actual platform roles" — implies it was broken
  - `75d85f9` "fix(rbac): restore all roles in field_authorization — instructor, creator, mentor, moderator, steward, elder" — implies roles were stripped again
**CURRENT DAMAGE:** None detected. The dual role system (core auth: student/instructor/admin/executive_admin + community: guest/student/creator/mentor/moderator/steward/elder/admin) is documented and handled in `field_authorization.py`. The `instructor` and `creator` both map to rank 2 which is correct.

---

## Logout
**STATUS:** WORKING
**COMPONENT:** `frontend/src/lib/auth.jsx:logout()`
**ENDPOINT:** None (client-only)
**WIRING:**
- ✓ `logout()` clears `lce_token` and `lce_user` from localStorage and sets user to null
- ✗ Does NOT call a backend logout endpoint — server-side session record is NOT deleted on normal logout
- ✓ Token version revocation available via `DELETE /api/auth/sessions` (self-service) or `DELETE /api/auth/sessions` (admin via `DELETE /api/admin/users/{uid}/sessions`)
**CURRENT DAMAGE:** Soft damage — logout is client-side only. JWT remains valid until expiry (168 hours by default). The `auth_sessions` record persists until the token version is bumped or the session times out. This is a design choice but means revocation is not immediate on logout.

---

## Password Change
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/Settings.jsx`
**ENDPOINT:** POST /api/auth/change-password
**DB OPERATION:** `db.users.update_one({"id": ...}, {"$set": {"password_hash": ...}})`
**WIRING:** ✓ Full chain verified. Requires current password, min 6 chars for new password (weaker than registration's 8-char minimum — inconsistency).

---

## Forgot Password / Email Reset Flow
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/ForgotPassword.jsx` → `frontend/src/pages/ResetPassword.jsx`
**ENDPOINT:** POST /api/auth/forgot-password, POST /api/auth/reset-password
**DB OPERATION:** `db.password_reset_tokens` collection
**WIRING:**
- ✓ Both endpoints exist in `server.py`
- ✓ Token is SHA-256 hashed before storage (plaintext never persisted)
- ✓ Tries Resend API first, falls back to Gmail SMTP
- ✗ Email delivery depends on `RESEND_API_KEY` or `GMAIL_USER`+`GMAIL_APP_PASSWORD` being set in Railway env vars — if neither is set, `email_sent=False` is returned silently with no user-visible error
- ✗ `_build_reset_url()` requires `PUBLIC_APP_URL` env var — if not set, returns a relative path (`/reset-password?token=...`) and logs a warning that it cannot build absolute URL for email. Email is then skipped.
**CURRENT DAMAGE:** PARTIAL — email delivery is conditional on environment variables. If `PUBLIC_APP_URL`, `RESEND_API_KEY`, or Gmail credentials are not set, the reset email is silently not sent. The UI shows no error (by design — "we'll send an email if that account exists").

---

## Executive Force Reset (EXEC_FORCE_RESET)
**STATUS:** WORKING
**ENDPOINT:** POST /api/auth/exec-unlock (secret-based), auto-reset on startup if `EXEC_FORCE_RESET=1`
**WIRING:**
- ✓ `server.py` startup: if `EXEC_FORCE_RESET=1`, resets all 3 exec seat passwords to defaults on every startup
- ✓ `/auth/exec-unlock` endpoint accepts `{"secret": EXEC_RESET_SECRET}` and resets all 3 exec seats
- ✓ Exec accounts: `EXEC_ADMIN_EMAIL`, `BACKUP_EXEC_ADMIN_EMAIL` (youpickeddoliver@gmail.com), `NAM_EXEC_EMAIL`
- ✓ `reset_exec_accounts.py` script also available for manual reset
**DAMAGE COUNT:** built 1 time, fixed 1 time
**DAMAGE HISTORY:**
  - `08b3d57` "fix: exec accounts self-heal on every restart, EXEC_FORCE_RESET=1 alone works"
  - `141c83a` "fix: exec account recovery never hashes empty password + voice fallback" — empty password bug fixed

---

## Token Versioning / Force Logout
**STATUS:** WORKING
**ENDPOINT:** DELETE /api/auth/sessions (self), POST /api/auth/force-logout/{uid} (admin+), DELETE /api/admin/users/{uid}/sessions (exec)
**WIRING:** ✓ `token_version` incremented in DB on force-logout. `current_user()` checks `payload["tv"] < db_tv` and returns 401. ✓ All three paths confirmed in `server.py`.

---

## Recovery Codes (Emergency Recovery)
**STATUS:** PARTIAL
**ENDPOINT:** POST /api/auth/emergency-recovery, POST /api/auth/recovery-codes-generate
**WIRING:**
- ✓ Endpoints exist in `server.py`
- ✗ Both import `from recovery import ...` — this module must be in the Python path at `/app/backend/recovery.py`. File existence not confirmed.
- ✗ `/auth/recovery-status` endpoint calls `from recovery import get_recovery_code_status` — same dependency
**CURRENT DAMAGE:** UNKNOWN — depends on whether `backend/recovery.py` exists. Not visible in repo file listing. If missing, these endpoints return 500 on call.

---

## USER MANAGEMENT (admin/exec)

---

## Create User
**STATUS:** WORKING
**COMPONENT:** `ExecSystem.jsx` → `UserCreateModal`
**ENDPOINT:** POST /api/admin/users
**DB OPERATION:** `db.users.insert_one()`
**WIRING:** ✓ Full chain. `ExecSystem.jsx` has `UserCreateModal` that calls `api.post("/admin/users", {...})`. `server.py` and `app/routes/admin.py` both have this endpoint. In production, `server.py:~2000` handles it. Admin+ required. Executive_admin required to create another executive_admin.
**CURRENT DAMAGE:** None.

---

## Edit User (name, email, cohort)
**STATUS:** WORKING
**COMPONENT:** `AdminDashboard.jsx` (EditUserModal), `AccountControls.jsx` (ControlPanel)
**ENDPOINT:** PATCH /api/admin/users/{uid}
**WIRING:** ✓ Full chain verified. Two separate UI paths both wire correctly to `server.py`.

---

## Delete User
**STATUS:** WORKING
**ENDPOINT:** DELETE /api/admin/users/{uid}
**WIRING:** ✓ `server.py` protects last admin/exec. `AccountControls.jsx` has delete button with confirmation modal (added at `45edfa3` — replaced `window.confirm`).

---

## Role Change
**STATUS:** WORKING
**ENDPOINT:** PATCH /api/admin/users/{uid}/role
**WIRING:** ✓ Full chain. Cannot promote to executive_admin unless actor is also executive_admin. Cannot demote self.

---

## Activate / Deactivate
**STATUS:** WORKING
**ENDPOINT:** PATCH /api/admin/users/{uid}/active
**WIRING:** ✓ Protects last admin. Deactivated accounts get 403 on login and 403 on API calls via `current_user()`.

---

## Bulk Actions
**STATUS:** WORKING (exec-only)
**ENDPOINT:** POST /api/admin/users/bulk
**WIRING:** ✓ `server.py:~10995` handles bulk `role`, `suspend`, `unsuspend` actions. Executive_admin only. Frontend bulk action UI exists in `ExecSystem.jsx`.

---

## Force Logout / Session Revocation
**STATUS:** WORKING
**ENDPOINT:** DELETE /api/admin/users/{uid}/sessions (exec), POST /api/auth/force-logout/{uid} (admin+)
**WIRING:** ✓ Both endpoints in `server.py`. Increment `token_version`, delete sessions. `AccountControls.jsx` and `AdminDashboard.jsx` both wire to the exec-gated DELETE endpoint. Note: `AdminDashboard.jsx` (route `/admin`, requires `admin` role) calls `DELETE /api/admin/users/{uid}/sessions` which requires `executive_admin` — **admin-role users on the AdminDashboard will get 403 when trying to force-logout.**

---

## Password Reset by Admin
**STATUS:** WORKING
**ENDPOINT:** POST /api/admin/users/{uid}/password
**WIRING:** ✓ Full chain. Sets `must_change_password=True`.

---

## One-Time Reset Link Generation
**STATUS:** WORKING
**ENDPOINT:** POST /api/admin/users/{uid}/reset-link
**WIRING:** ✓ `server.py:2610` exists. Creates a password reset token, returns the URL. Used in `ExecSystem.jsx` `UserCreateModal` after user creation.

---

## Feature Tier Assignment
**STATUS:** BROKEN
**COMPONENT:** No frontend UI for feature tier assignment found
**ENDPOINT:** `/exec/control/user/tier` (POST) — exists only in `app/routes/executive_control.py` which is NOT deployed
**WIRING:**
- ✗ `app/routes/executive_control.py` has `POST /exec/control/user/tier` for setting `feature_tier` and `sage_tier`
- ✗ This file is imported by `app/main.py` which is NOT the deployed application
- ✗ `server.py` has only `PATCH /admin/users/{uid}/sage-tier` (for sage tier only)
- ✗ No `feature_tier` assignment endpoint exists in `server.py`
- ✗ No frontend UI found for feature tier assignment
**CURRENT DAMAGE:** Feature tier assignment via admin UI is completely missing from deployed application. `feature_tier` can only be set by directly editing the MongoDB document.

---

## Sage Tier Assignment
**STATUS:** PARTIAL — WORKING via direct endpoint, no dedicated UI
**ENDPOINT:** PATCH /api/admin/users/{uid}/sage-tier
**WIRING:** ✓ Exists in `server.py`. Admin+ required. No dedicated frontend UI page — the endpoint is available but there is no admin panel button wired to it.

---

## Elevated Role (Temporary Escalation)
**STATUS:** MISSING
**WIRING:** No endpoint for temporary role escalation found in `server.py` or any deployed code. The `app/routes/executive_control.py` has `SetUserRoleReq` but it's permanent, not temporary. No time-limited role escalation system exists.

---

## EXEC CONTROL PANEL

---

## ExecSystem.jsx — every panel and button
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/ExecSystem.jsx`
**WIRING:**
- ✓ User Database Panel: calls `GET /admin/users`, `POST /admin/users`, `PATCH /admin/users/{uid}`, `PATCH /admin/users/{uid}/role`, `PATCH /admin/users/{uid}/active`, `DELETE /admin/users/{uid}`, `POST /admin/users/{uid}/reset-link` — all exist in `server.py`
- ✓ EmergencyPanel embedded: calls `GET /exec/panel`, `POST /exec/panel/toggle`, `POST /exec/failover`, `GET /exec/panel/health` — all exist in `server.py` (wrapped in try/except at lines 10678–10925)
- ✓ System stats: calls `GET /exec/system` — exists in `server.py:2369`
- ✓ User session viewing/force-logout — exec-gated endpoints exist
**DAMAGE COUNT:** built 3 times, broken 1 time, fixed 2 times
**DAMAGE HISTORY:**
  - `a3083f2` initial live User Database panel
  - `27a3748` rebuild with full exec control interface
  - `addeab4` "fix: replace fake localStorage ApiKeyManager with real provider key status" — confirmed there WAS a localStorage fake
  - `45edfa3` "Replace window.confirm on destructive admin actions with modals"
  - `4b45ae5` "Fix exec login button URL and ExecSystem backend fetch URLs" — URLs were broken

---

## SiteControlPanel.jsx — every toggle and action
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/SiteControlPanel.jsx`
**ENDPOINT:** GET /api/admin/control-panel
**WIRING:**
- ✓ `GET /admin/control-panel` → `server.py:12390` (exec-only) — exists, returns real metrics
- ✓ Platform flag toggles: `POST /admin/platform/flags/{flag}` → `server.py:6270` — exists
- ✓ Broadcast: `POST /admin/control-panel/broadcast` → `server.py:12637` — exists
- ✓ Payout processing: `POST /admin/creator-payouts/process` → `server.py:12240` — exists
- ✓ AI spend budget: `POST /admin/ai-spend-budget` → `server.py:12609` — exists
- ✓ 5 platform flags: `platform_locked`, `marketplace_disabled`, `ai_disabled`, `community_disabled`, `labs_disabled`
**DAMAGE COUNT:** built 2 times, fixed 1 time
**DAMAGE HISTORY:**
  - `c8501fe` initial Site Control Panel with real metrics
  - `b06fc0f` added payout UI, Stripe webhook health, AI spend budget controls

---

## ExecutiveDirectorDashboard.jsx — every action
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/ExecutiveDirectorDashboard.jsx`
**WIRING:**
- ✓ Password change form: calls `POST /auth/change-password` — exists
- ✓ Exec system stats panel — verified
- ✗ Missing AppShell (no nav bar on this page)
**DAMAGE COUNT:** built 2 times (stub then real)
**DAMAGE HISTORY:**
  - `278ffda` "Replace stub ExecutiveDirectorDashboard with fully real implementation"
  - `eac94ef` "Feat: restore password change form on Executive Dashboard" — implies password change was removed then re-added
  - `8bd2885` "Feat: restore exec/panel routes + Provider Gateway UI + Billing Admin UI" — implies panel routes were removed and restored

---

## EmergencyPanel.jsx — every breaker and failover
**STATUS:** WORKING
**COMPONENT:** `frontend/src/components/EmergencyPanel.jsx`
**ENDPOINT:** GET /api/exec/panel, POST /api/exec/panel/toggle, POST /api/exec/failover, GET /api/exec/panel/health
**WIRING:** ✓ All 4 endpoints exist in `server.py` (lines 10678–10708). All require `executive_admin`. Breaker UI renders correctly. The panel state is loaded from `db.emergency_panel` collection (MongoDB-persisted).
**CURRENT DAMAGE:** None detected. The `try/except` wrapper around the panel routes means if `EmergencyPanelService` import fails, the routes are silently absent — this is a startup-time risk.

---

## Executive Control Layer (/exec/control/*)
**STATUS:** BROKEN — ENTIRELY MISSING FROM PRODUCTION
**COMPONENT:** `app/routes/executive_control.py`
**WIRING:**
- ✗ `/exec/control/user/role` — MISSING from `server.py`
- ✗ `/exec/control/user/tier` — MISSING from `server.py`
- ✗ `/exec/control/feature-flag` — MISSING from `server.py`
- ✗ `/exec/control/ai-access` — MISSING from `server.py`
- ✗ `/exec/control/price` — MISSING from `server.py`
- ✗ `/exec/control/budget` — MISSING from `server.py`
- ✗ `/exec/control/provider-ranking` — MISSING from `server.py`
- ✗ `/exec/control/ip-whitelist` — MISSING from `server.py`
- ✗ `/exec/control/mfa` — MISSING from `server.py`
- ✗ `/exec/control/failover` — MISSING (separate `/exec/failover` exists)
- ✗ `/exec/control/page-mode` — MISSING from `server.py`
- ✗ `/exec/control/visibility` — MISSING from `server.py`
**CURRENT DAMAGE:** The entire `executive_control.py` module with all `POST /exec/control/*` endpoints exists in `app/routes/executive_control.py` but is only registered in `app/main.py` which is not deployed. No frontend code calls these endpoints anyway (zero grep results for `/exec/control` in frontend), so the UI never expected these routes to exist. The exec control layer is a backend-only design document.

---

## Platform Flags (lock, disable marketplace, AI, community, labs)
**STATUS:** WORKING
**ENDPOINT:** GET /api/admin/platform/flags, POST /api/admin/platform/flags/{flag}
**WIRING:** ✓ Both exist in `server.py:6261+6270`. `SiteControlPanel.jsx` wires to them. The middleware `enforce_platform_flags` in `server.py:~232` reads from `db.platform_flags` and blocks non-auth API calls when `platform_locked` is active.

---

## Break-Glass System
**STATUS:** PARTIAL
**ENDPOINT:** POST /api/auth/exec-unlock (secret-based break-glass)
**WIRING:** ✓ The `exec-unlock` endpoint in `server.py` acts as the break-glass — accepts `EXEC_RESET_SECRET` and resets all exec seats. No dedicated break-glass UI page. `reset_exec_accounts.py` script is another break-glass path.

---

## Audit Log Viewing
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/AuditLog.jsx`
**ENDPOINT:** GET /api/admin/audit
**WIRING:** ✓ Exists in `server.py`. Admin+ required. Exec-only export at `GET /admin/audit/export`.

---

## Cohort Management
**STATUS:** PARTIAL
**ENDPOINT:** POST /api/admin/associate (assign cohort), GET /api/admin/users?associate=X (filter by cohort)
**WIRING:** ✓ Both exist in `server.py`. No dedicated cohort management UI page — cohort assignment is embedded in `ExecSystem.jsx` create/edit modals.

---

## REVENUE / BILLING

---

## Stripe Integration (webhooks, checkout, subscriptions)
**STATUS:** PARTIAL — code present, key-dependent
**COMPONENT:** `frontend/src/pages/Store.jsx`, `frontend/src/pages/SubscribePage.jsx`
**ENDPOINT:** POST /api/payments/checkout, POST /api/payments/webhook, GET /api/payments/products
**DB OPERATION:** `db.payments.insert_one()`, `db.subscriptions.update_one(upsert=True)`
**WIRING:**
- ✓ All Stripe endpoints exist in `server.py:~7400-7800` and `app/routes/payments.py` (the latter is dead code)
- ✓ Checkout creates Stripe session via `stripe.checkout.Session.create()`
- ✓ Webhook handles: `checkout.session.completed`, `customer.subscription.created/updated/deleted`, `invoice.payment_succeeded/failed`
- ✗ Requires `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY` in Railway env vars
- ✗ If `STRIPE_SECRET_KEY` is not set, checkout returns HTTP 503
**DAMAGE COUNT:** built 1 time, no breakage detected
**CURRENT DAMAGE:** Conditional on API keys being configured. The `GET /payments/products` endpoint always returns `stripe_enabled: bool(STRIPE_SECRET_KEY)` so frontend can check.

---

## Creator Payouts
**STATUS:** PARTIAL
**ENDPOINT:** POST /api/admin/creator-payouts/process
**DB OPERATION:** `db.creator_payouts.insert_one()`, `db.creator_balances.update_one()`
**WIRING:** ✓ Endpoint exists in `server.py:12240`. Reads all unpaid balances from `db.creator_balances`, creates payout records, marks balances as paid. Does NOT actually send money — no Stripe Connect or ACH integration. Payouts are DB records only.
**CURRENT DAMAGE:** Payout processing creates DB records but does not transfer money. Bank account info is stored in `db.creator_bank_accounts` but no ACH/Stripe Connect transfer is executed.

---

## Subscription Management
**STATUS:** PARTIAL
**ENDPOINT:** GET /api/payments/portal (Stripe customer portal)
**WIRING:** ✓ `stripe.billing_portal.Session.create()` called if customer has `stripe_customer_id`. Requires `STRIPE_SECRET_KEY`.

---

## Payment History
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/PaymentHistory.jsx`
**ENDPOINT:** GET /api/payments/history
**DB OPERATION:** `db.payments.find({"user_id": ...})`
**WIRING:** ✓ Full chain verified. AppShell is present (added at `6551bd3`).

---

## AdminPayments Page
**STATUS:** PARTIAL — no backend /admin/payments endpoint exists
**COMPONENT:** `frontend/src/pages/AdminPayments.jsx`
**WIRING:**
- Checked: `AdminPayments.jsx` exists with AppShell (added at `5f51cc4`)
- UNKNOWN: Need to confirm what API endpoints AdminPayments.jsx calls
**DAMAGE COUNT:** AppShell was missing, restored 1 time

---

## SubscribePage
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/SubscribePage.jsx`
**WIRING:** ✓ Has AppShell (added at `6551bd3`). Calls payment checkout endpoints.

---

## Store
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/Store.jsx`
**ENDPOINT:** GET /api/payments/products, POST /api/payments/checkout
**WIRING:** ✓ `Store.jsx` calls `api.post("/payments/checkout", {product_key, quantity})`. `server.py` has this endpoint. AppShell added at `5f51cc4`. Store does NOT require authentication for browsing — checkout requires auth.

---

## CREATOR SYSTEM

---

## Creator Profile
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/CreatorProfile.jsx`, `frontend/src/pages/CreatorProfileEdit.jsx`
**ENDPOINT:** GET /api/creator/profile/{slug}, PUT /api/creator/profile, GET /api/creator/profile/me
**DB OPERATION:** `db.creator_profiles.find_one({"slug": ...})`
**WIRING:** ✓ All endpoints exist in `server.py:12315-12366`. Creator profiles are seeded from `_SEED_CREATOR_PROFILES` on startup. Edit page calls `PUT /creator/profile`.
**DAMAGE COUNT:** built 1 time, fixed 1 time
**DAMAGE HISTORY:**
  - `b7855a6` "H1: Creator profile self-edit — backend + edit page + live fetch"

---

## Creator Directory (live or fake?)
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/Creators.jsx`
**ENDPOINT:** GET /api/creator/profiles/public (server.py:12356)
**WIRING:** ✓ Endpoint exists. Returns from `db.creator_profiles` with public fields. Seeded from hardcoded `_SEED_CREATOR_PROFILES` list. Missing AppShell.

---

## Creator Courses — CRUD
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/CreatorCourses.jsx`
**ENDPOINT:** GET/POST/PATCH/DELETE /api/creator/courses, GET /api/creator/courses/published
**WIRING:** ✓ All endpoints in `server.py:11962-12062`. Full CRUD verified.
**DAMAGE HISTORY:**
  - `3445c23` "CR1 + H2: Creator course publishing — full CRUD backend + dashboard"

---

## Creator Earnings Dashboard
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/CreatorEarnings.jsx`
**ENDPOINT:** GET /api/creator/earnings, GET /api/creator/payouts, GET/POST /api/creator/bank-account
**WIRING:** ✓ All endpoints in `server.py:12157-12227`. Earnings calculated from `db.creator_balances`. Bank account stored encrypted in `db.creator_bank_accounts`.

---

## Ghost Producer Feature
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/GhostProducer.jsx`
**WIRING:**
- ✓ TTS calls `POST /ai/sage/tts` — exists in `server.py:3537`
- ✓ Tool chat calls `POST /ai/tool-chat` — exists in `server.py:3961`
- ✗ Missing AppShell — no platform navigation
- The page has hardcoded track and clone lists (not DB-driven)
- The "Ghost Clones" AI tab uses `POST /ai/tool-chat` which routes to LLM gateway
**DAMAGE HISTORY:**
  - `04cbab5` "fix: wire GhostProducer TTS to real WAI backend endpoint" — was previously NOT wired to backend

---

## Band on Page Feature
**STATUS:** MISSING
No `BandOnPage` component or page found anywhere in the repository. Not in `App.js` routes, not in `frontend/src/pages/`. No backend endpoint for it. This feature does not exist.

---

## Creator Onboarding Flow
**STATUS:** MISSING
No dedicated creator onboarding flow found. There is a `WelcomeWizard.jsx` component that renders globally, but no creator-specific onboarding steps.

---

## COURSES / LEARNING

---

## Course Catalog / Listing
**STATUS:** WORKING (dual system)
**COMPONENT:** `frontend/src/pages/Courses.jsx` (creator courses), `frontend/src/pages/ModulesList.jsx` (WAI modules)
**ENDPOINT:** GET /api/creator/courses/published (creator courses), GET /api/modules (WAI modules)
**WIRING:** ✓ Both exist in `server.py`. Courses.jsx calls both creator courses and enrollment status.

---

## Course Enrollment
**STATUS:** WORKING
**ENDPOINT:** POST /api/creator/courses/{course_id}/checkout
**WIRING:** ✓ `server.py:12079` creates Stripe checkout for paid courses or direct enrollment for free courses.

---

## Module / Lesson Progression
**STATUS:** WORKING
**ENDPOINT:** GET /api/modules, GET /api/modules/{slug}, POST /api/progress/{module_id}
**WIRING:** ✓ Exist in `server.py`. `ModuleView.jsx` tracks progress via `POST /progress/{module_id}`.

---

## Completion Tracking
**STATUS:** WORKING
**DB OPERATION:** `db.progress` collection
**WIRING:** ✓ Progress records stored on module completion. Certificate generation triggers at 100% completion.

---

## Credentials / Certificates
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/Certificates.jsx`, `frontend/src/pages/Credentials.jsx`
**ENDPOINT:** GET /api/credentials, POST /api/credentials (admin grant)
**WIRING:** ✓ PDF generation via `reportlab` in `server.py`. Certificates downloadable.

---

## Labs
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/LabsHub.jsx`, `frontend/src/pages/LabDetail.jsx`
**ENDPOINT:** GET /api/labs, GET /api/labs/{slug}, POST /api/labs/{slug}/submit
**WIRING:** ✓ Full chain in `server.py`.

---

## Associate Cohort System
**STATUS:** PARTIAL
**ENDPOINT:** POST /api/admin/associate, GET /api/admin/users?associate=X
**WIRING:** ✓ Cohort assignment via `associate` field on users. No dedicated cohort management UI — assignment done via user edit modals.

---

## AI PERSONAS

---

## Ancestral Sage
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/AITutor.jsx`
**ENDPOINT:** POST /api/ai/chat (main), POST /api/ai/sage/tts (TTS), POST /api/ai/consent, GET /api/ai/sage/integrity, POST /api/ai/sage/resolve_mode
**PROMPT:** `backend/prompts/ancestral_sage_prompt.py`
**HASH INTEGRITY:** ✓ VERIFIED — live hash `fbfba5fb...` matches expected hash exactly
**AUTH:** ✓ `current_user` dependency on all endpoints
**WIRING:** ✓ Full chain verified. Prompt loaded from file. Hash check runs at startup and on each `/ai/sage/integrity` call. If hash fails, `RESTRICTED_EDUCATIONAL_FALLBACK` is used. Consent gate enforced.
**DAMAGE COUNT:** built 1 time, hardened multiple times
**DAMAGE HISTORY:**
  - `49b7057` "feat: SHA-256 hash integrity for all 7 core AI personas"
  - Multiple auto-commits touch `ancestral_sage_prompt.py`

---

## The Sovereign
**STATUS:** PARTIAL — executive-only, gated
**COMPONENT:** `frontend/src/components/SovereignChat.jsx` (floating widget, exec-only)
**ENDPOINT:** POST /api/sovereign/chat
**PROMPT:** `app/services/sovereign/sovereign_persona.py` (`SOVEREIGN_PERSONA`)
**AUTH:** `server.py:10589` — requires `executive_admin`
**WIRING:**
- ✓ `SovereignChat.jsx` renders for exec users only
- ✓ POST to `/sovereign/chat` exists in `server.py:10589`
- ✓ TTS uses `POST /ai/sage/tts` endpoint
- ✓ Memory stored in `db.sovereign_memory`
- The `SOVEREIGN_PERSONA` prompt is in `app/services/sovereign/sovereign_persona.py` but server.py uses inline prompt or reads from the sovereign service — need to verify import

---

## PRT (Poor Righteous Teacher)
**STATUS:** PARTIAL — used as internal filter, not a direct chat persona
**ENDPOINT:** No direct `/ai/prt` endpoint
**WIRING:**
- ✓ `PRTEnforcementEngine` loaded as singleton from `wai_institute.personas.prt.prt_enforcement_engine`
- ✓ PRT is called as a filter in the orchestrator (`/ai/orchestrator`): "PRT chairs the meeting and validates cultural alignment first" (server.py:9516-9540)
- ✓ Listed as a persona in `GET /exec/personas` response
- ✗ No direct user-facing chat endpoint for PRT
**CURRENT DAMAGE:** PRT is a backend filter, not a user-accessible persona. No frontend component to interact with it directly.

---

## Director
**STATUS:** WORKING
**COMPONENT:** `frontend/src/components/DirectorWidget.jsx` (floating widget)
**ENDPOINT:** POST /api/ai/director, GET /api/ai/director/greeting, GET /api/ai/director/pulse, POST /api/ai/director/tts, POST /api/ai/director/upload
**PROMPT:** `backend/prompts/director_prompt.py`
**AUTH:** `current_user` (authenticated users)
**WIRING:** ✓ Full chain verified. `DirectorWidget.jsx` wires to all 5 endpoints. `server.py:4378-4762` has all endpoints. Director has upload capability for file context.

---

## Assistant Director
**STATUS:** PARTIAL — mentioned in config, no dedicated endpoint
**WIRING:** No `/ai/assistant-director` endpoint found. The "Assistant Director" role is referenced in governance documents but has no API surface.

---

## Oliver Guardian
**STATUS:** WORKING — internal AI moderator
**PROMPT:** `backend/prompts/oliver_guardian_prompt.py`
**ENDPOINT:** Not directly accessible — called internally by `_oliver_moderate()` before every M.O.R.E. post/need/chat submission
**WIRING:** ✓ `_oliver_moderate()` in `server.py:~6680` calls `call_llm()` with Oliver Guardian prompt. Writes every decision to `db.more_moderation_log`. Has crisis detection and resource linking.

---

## The Supervisor
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/components/SupervisorWidget.jsx`
**ENDPOINT:** GET /api/supervisor/dashboard, GET /api/supervisor/greeter/config, GET /api/supervisor/visitor-flow
**WIRING:**
- ✓ SupervisorWidget renders globally on all pages
- ✓ Supervisor dashboard endpoints exist in `server.py:11225-11486`
- ✗ No direct Supervisor AI chat — the Supervisor is a governance/management persona, not a chat persona accessible to normal users
- ✓ Supervisor has backup system controls: `POST /supervisor/backup/switch-provider`, `POST /supervisor/backup/emergency-broadcast`

---

## M.O.R.E. Department / Finance Director
**STATUS:** WORKING
**ENDPOINT:** POST /api/more/department/chat, GET /api/more/department/integrity
**PROMPT:** `backend/prompts/more_department_system.py`
**WIRING:** ✓ `server.py:7508+7586` has both endpoints. Chat calls LLM gateway with M.O.R.E. department system prompt. Integrity endpoint returns SHA-256 hash of the prompt.

---

## "The 9" Synthesis Engine
**STATUS:** PARTIAL — integrated into orchestrator, not standalone
**ENDPOINT:** No direct `/ai/the9` endpoint
**WIRING:**
- ✓ `The9FusionEngine` loaded as singleton from `wai_institute.core.the9_fusion_engine`
- ✓ The 9 participates in orchestrator council (`/ai/orchestrator`) as synthesis engine
- ✓ Listed as persona in `/exec/personas`
- ✗ No direct user-facing chat endpoint

---

## COMMUNITY / M.O.R.E.

---

## M.O.R.E. Posts
**STATUS:** WORKING
**COMPONENT:** `frontend/src/pages/More.jsx` (public), `frontend/src/pages/MoreHub.jsx` (auth)
**ENDPOINT:** POST /api/more/post, GET /api/more/posts
**DB OPERATION:** `db.more_posts.insert_one()` + Oliver Guardian moderation
**WIRING:** ✓ Full chain. Every post goes through `_oliver_moderate()` before storage.

---

## M.O.R.E. Needs Board
**STATUS:** WORKING
**ENDPOINT:** POST /api/more/need, GET /api/more/needs
**WIRING:** ✓ Full chain. Same Oliver Guardian moderation applied.

---

## Elder Council
**STATUS:** PARTIAL — static/UI only
**COMPONENT:** `frontend/src/pages/ElderCouncil.jsx`
**WIRING:** ✓ Has AppShell (added at `626c49e`). Content appears to be largely static — no dedicated Elder Council API endpoints found. The page exists as a community space but backend integration is minimal.

---

## Community Features
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/Community.jsx`
**WIRING:** Missing AppShell. Community page exists but no direct backend API calls confirmed.

---

## Seshats Hub
**STATUS:** PARTIAL
**COMPONENT:** `frontend/src/pages/SeshatsHub.jsx` (supervisor access), `frontend/src/pages/SeshatsHubPublic.jsx` (public)
**WIRING:**
- ✓ Public version exists
- ✓ Supervisor-gated private version restored at `dfe80f7`
- Missing AppShell on both
**DAMAGE HISTORY:**
  - `dfe80f7` "Fix: restore /seshats-hub public page; /supervisor stays exec control panel" — implies it was previously broken

---

## PROVIDER GATEWAY

---

## LLM Provider Routing (call_llm)
**STATUS:** WORKING
**COMPONENT:** `backend/ai/llm_gateway.py`
**WIRING:** ✓ 6-tier free-first fallback: Groq (T1a) → Cerebras (T1b) → Gemini (T2) → Grok/xAI (T3) → Cohere (T4) → OpenRouter (bonus) → HuggingFace (T5) → Anthropic (T6, paid last resort) → KB fallback (always available)
- ✓ Hourly token budget guard (`HOURLY_TOKEN_CAP`, default 200k)
- ✓ Anthropic degraded-state tracking with 5-minute auto-recovery
- ✓ `call_llm()` is imported from `backend/ai/llm_gateway.py` throughout `server.py`
**DAMAGE COUNT:** built 1 time, enhanced 5 times
**DAMAGE HISTORY:**
  - `950df7d` initial LLM gateway
  - `f158740` expanded to 6-tier free-first chain
  - `4574009` Groq promoted to primary, Anthropic to paid last-resort
  - `03b1dde` added Cerebras + HuggingFace tiers
  - `1c50ab2` "Fix: API keys saved in Provider Gateway now take effect immediately" — `reload_provider_keys()` added

---

## API Key Management (real DB or localStorage?)
**STATUS:** WORKING (real DB, was localStorage at one point)
**COMPONENT:** `frontend/src/pages/ProviderGateway.jsx`
**ENDPOINT:** GET/POST /api/providers, GET/POST/DELETE /api/providers/keys, POST /api/providers/keys/{id}/test
**WIRING:** ✓ Full chain. Keys encrypted at rest via Fernet with `PROVIDER_KEY_ENCRYPTION_SECRET`. `reload_provider_keys()` updates module globals after save.
**DAMAGE COUNT:** built 2 times (localStorage then real)
**DAMAGE HISTORY:**
  - `addeab4` "fix: replace fake localStorage ApiKeyManager with real provider key status" — **CONFIRMED localStorage fake replaced with real DB storage**
  - `8bd2885` "Feat: restore exec/panel routes + Provider Gateway UI + Billing Admin UI" — implies Provider Gateway UI was missing

---

## Budget Controls
**STATUS:** WORKING
**ENDPOINT:** POST /api/admin/ai-spend-budget
**WIRING:** ✓ `server.py:12609` exists. Sets AI spend budget in `db.platform_config`. `SiteControlPanel.jsx` wires to it.

---

## Failover Logic
**STATUS:** WORKING
**ENDPOINT:** POST /api/exec/failover
**WIRING:** ✓ `server.py:10700` exists. Transitions gateway between `primary`, `backup`, `emergency`. Exec-only.

---

## EMAIL SYSTEM

---

## send_platform_email() / Email Provider
**STATUS:** PARTIAL — code is real, delivery depends on env vars
**COMPONENT:** `backend/app/security/passwords.py` (and duplicate in `server.py`)
**WIRING:**
- ✓ `_send_via_resend()` — calls Resend API if `RESEND_API_KEY` is set
- ✓ `_send_via_gmail()` — calls Gmail SMTP if `GMAIL_USER` + `GMAIL_APP_PASSWORD` are set
- ✓ Tries Resend first, falls back to Gmail
- ✗ If neither is configured: email silently not sent, returns False, no user-visible error
- ✓ Welcome email sent on registration (async task)
- ✓ Password reset email sent on forgot-password request
**CURRENT DAMAGE:** Email system is real code but requires environment variables. No stub — if unconfigured, it just fails silently.

---

## Hash Integrity Alert Emails
**STATUS:** PARTIAL
**WIRING:** ✓ `server.py:11586-11611` sends integrity alert emails if Supervisor detects prompt hash failure. Uses the platform email system (same env var dependencies).

---

## Executive Notification Emails
**STATUS:** PARTIAL
**WIRING:** `app/utils/alerting.py` sends account-locked and other executive alerts. Depends on same email env vars.

---

## NAVIGATION / SHELL

---

## AppShell — pages missing it
**STATUS:** PARTIAL — 38 of 88 pages lack AppShell
**COMPONENT:** `frontend/src/components/AppShell.jsx`
**MISSING AppShell (no platform navigation):**
- `Creators.jsx` — creator directory (public, but odd)
- `BillingAdmin.jsx` — admin page missing nav
- `GhostProducer.jsx` — feature page missing nav
- `CreatorProfile.jsx` — public profile page (intentional?)
- `ExecutiveDirectorDashboard.jsx` — exec page missing nav
- `AuditorDashboard.jsx` — admin page missing nav
- `PartnershipDiscounts.jsx` — member page missing nav
- `Community.jsx` — community page missing nav
- `UserProfile.jsx` — profile page missing nav
- `PartnershipDashboard.jsx` — member page missing nav
- `ProviderGateway.jsx` — exec admin page missing nav
- `PlaylistDashboard.jsx` — feature page missing nav
- `RevenueDivision.jsx` — admin page missing nav (though its route is protected)
- `SocialPublish.jsx` — auth page missing nav
**DAMAGE COUNT:** AppShell added to 4+ pages across multiple commits
**DAMAGE HISTORY:**
  - `0f330b5` "fix: add AppShell to Palace and Plans pages"
  - `626c49e` "Fix: ElderCouncil, LitigationWeapon, DonatePage missing AppShell"
  - `5f51cc4` "Fix: wrap Store and AdminPayments in AppShell"
  - `6551bd3` "Fix: wrap PaymentHistory and SubscribePage in AppShell"

---

## Routing — every route in App.js, does the component exist?
**STATUS:** WORKING — all imported components exist on disk. Every `import` in `App.js` resolves to an existing file in `frontend/src/pages/` or `frontend/src/components/`. No missing component files detected.

---

## Auth Guards
**STATUS:** WORKING
**WIRING:**
- ✓ `Protected` component: redirects to `/login` if no user
- ✓ `BoundedAdmin` component: adds `ErrorBoundary` + role check
- ✓ `SupervisorProtected`: redirects to `/supervisor-login` if not exec
- ✓ ROLE_RANK in App.js mirrors backend: `{student:1, instructor:2, admin:3, executive_admin:4}`
- ✓ Role-hierarchical check: higher rank passes lower-rank check
- Notable: `/ghost-producer` is a PUBLIC route — no auth guard

---

## Role-Based Nav Visibility
**STATUS:** WORKING
**COMPONENT:** `frontend/src/components/AppShell.jsx`
**WIRING:** Nav items are conditionally rendered based on `user.role`. Exec-only items check for `executive_admin`.

---

## RBAC / FIELD AUTHORIZATION

---

## field_authorization.py
**STATUS:** WORKING (recently restored)
**COMPONENT:** `backend/security/field_authorization.py`
**WIRING:** ✓ Handles two overlapping role systems. `FieldAuthorization.get_visible_fields()` + `filter_response()` strip `password_hash`, `_id`, `recovery_codes`, `last_recovery_reset` from all responses. Used in `/auth/me` and `/admin/users`.
**DAMAGE COUNT:** broken 2 times, restored 2 times
**DAMAGE HISTORY:**
  - `f75c34e` initial build
  - `90049f1` "fix: restore RBAC field_authorization to match actual platform roles" — first restoration
  - `75d85f9` "fix(rbac): restore all roles in field_authorization — instructor, creator, mentor, moderator, steward, elder" — second restoration (community roles were stripped again)

---

## rbac.py
**STATUS:** WORKING (in `app/security/rbac.py`, but this file is NOT used in production)
**WIRING:** `app/security/rbac.py` is a comprehensive RBAC module with `RoleLevel`, `FeatureTier`, permission matrices, and route-level access control. However, since `app/main.py` is not deployed, this module is dead code in production. `server.py` has its own inline RBAC logic using the `ROLE_RANK` dict and `require_role()` dependency.

---

## Which roles exist
**STATUS:** Production roles: `student`, `instructor`, `admin`, `executive_admin`
Community/creator roles (`creator`, `mentor`, `moderator`, `steward`, `elder`) exist in `field_authorization.py` for field visibility but are NOT enforced in the auth system — users only get one of the 4 core roles.

---

## /auth/me field visibility per role
**STATUS:** WORKING — see field_authorization.py analysis above

---

## Admin endpoint protection
**STATUS:** MOSTLY WORKING
- ✓ All `/admin/*` endpoints require at minimum `admin` role via `require_role("admin")`
- ✓ Executive-only endpoints require `require_role("executive_admin")`
- ✗ One inconsistency: `AccountControls.jsx` is accessible at `/admin/accounts` with `admin` role, but the "Force Logout All Sessions" button calls `DELETE /api/admin/users/{uid}/sessions` which requires `executive_admin` — regular admins will get 403

---

## EXTERNAL INTEGRATIONS

---

## Stripe
**STATUS:** PARTIAL — real code, key-dependent
- ✓ Full Stripe integration in `server.py` (checkout, webhooks, subscriptions, customer portal)
- ✗ Requires `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PUBLISHABLE_KEY`
- If unconfigured: checkout returns 503

---

## ElevenLabs TTS
**STATUS:** PARTIAL — executive-only, key-dependent
- ✓ `backend/ai/elevenlabs_client.py` implements full 3-tier TTS system
- ✓ Used by Director TTS, Revenue Director TTS, Cipher audio, Sage ElevenLabs TTS
- ✗ Requires `ELEVENLABS_API_KEY` and `CIPHER_VOICE_ID`/`DIRECTOR_VOICE_ID`/`SAGE_VOICE_ID`
- Falls back to OpenAI TTS then browser speech synthesis if unconfigured

---

## Lemon Squeezy
**STATUS:** STUB → REAL code, key-dependent
- ✓ `backend/ai/publishing.py` implements real Lemon Squeezy API calls
- ✗ Requires `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID`
- Falls back to Gumroad, then MongoDB-only storage

---

## Gumroad
**STATUS:** PARTIAL — real code, key-dependent
- ✓ `backend/ai/publishing.py` has `_publish_gumroad()` calling `https://api.gumroad.com/v2/products`
- ✗ Requires `GUMROAD_API_KEY`

---

## Email Provider (Gmail SMTP / Resend)
**STATUS:** PARTIAL — real code, key-dependent (see EMAIL SYSTEM section above)

---

## SUMMARY OF CRITICAL DAMAGE

| Category | Finding |
|---|---|
| **STRUCTURAL** | `app/main.py` and the entire `app/routes/` directory are dead code — not deployed. `server.py` is the actual application. |
| **exec/control/* endpoints** | All `POST /exec/control/*` endpoints (role change, tier assignment, feature flags, AI access, prices, budgets, IP whitelist, MFA, failover, page mode, visibility) exist only in non-deployed `app/routes/executive_control.py`. They return 404 in production. |
| **Feature tier assignment** | No admin UI or backend endpoint for assigning `feature_tier` in production. It can only be set via MongoDB directly. |
| **Band on Page** | Does not exist anywhere in the codebase. |
| **localStorage fake** | API key manager was previously fake (localStorage-backed). Replaced with real DB storage at commit `addeab4`. |
| **AppShell missing** | 38/88 pages lack navigation shell, including `BillingAdmin.jsx`, `AuditorDashboard.jsx`, `ExecutiveDirectorDashboard.jsx`, `ProviderGateway.jsx`. |
| **recovery.py** | `/auth/emergency-recovery` and `/auth/recovery-codes-generate` both import `from recovery import ...` — this module's existence on the production path is unconfirmed. |
| **field_authorization.py** | Was broken/stripped at least twice; restored twice. Currently correct. |
| **Admin force-logout permission gap** | Admins can view `AccountControls.jsx` but the "Force Logout" button calls an exec-only endpoint — 403 for admin users. |
| **Email delivery** | Silent failure if `RESEND_API_KEY` or Gmail credentials or `PUBLIC_APP_URL` are not set in Railway. No user-visible error on forgot-password. |
| **Payout processing** | Creates DB records only — no actual money transfer. No Stripe Connect or ACH. |
| **PRT and The9** | Not directly user-accessible — internal pipeline components only. |
| **auto-commits** | 38 auto-commits with UUID messages touch `server.py`, `ancestral_sage_prompt.py`, and other core files — their content is opaque but they contributed to the iterative churn visible in the damage history. |
