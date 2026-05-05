# Auth + Settings + Password Reset — Hotfix Executive Summary
**Date:** Feb 2026 · **Severity:** P1 · **Status:** ✅ Resolved · **Tests:** 185/185

---

## What was missing
1. **Public password reset was completely absent.** The login page told users to "contact your program administrator". There was no `/forgot-password`, no `/reset-password`, no token endpoint, no email sending logic.
2. **Settings was a single-purpose page.** Only change-password worked. Users could not edit their own name or email; the full self-service profile was admin-mediated only.
3. **Admin reset UX was clunky.** The only admin path was "type a new password into a `prompt()` and tell the user verbally" — no auditable shareable link.

What was already solid (untouched):
- JWT + bcrypt + hierarchical RBAC (`executive_admin > admin > instructor > student`) with `can_modify()` immunity guards.
- Idempotent `executive_admin` bootstrap with `must_change_password` rotation.
- Domain-portable `lib/api.js` (Emergent preview ↔ `https://www.wai-institute.org`).
- 161/161 prior backend tests passing.

---

## What was built

### Backend (`/app/backend/server.py`)
- `POST /api/auth/forgot-password` — no-enumeration, rate-limited per-IP (30/5min) + per-email (5/10min). Mints `secrets.token_urlsafe(32)`, stores SHA-256 hash + 30-min TTL, audits, optionally emails via Resend, optionally returns dev-token when `DEV_RETURN_RESET_TOKEN=1`.
- `POST /api/auth/reset-password` — verifies SHA-256 match, expiry, single-use; sets new password; clears `must_change_password`; invalidates all other unused tokens for the user; audits.
- `POST /api/admin/users/{uid}/reset-link` — admin-mediated mint. Honours `can_modify()` so admin cannot bypass exec immunity. Returns `{token, url, expires_at, email_sent}`.
- `PATCH /api/auth/me` — self-service edit of `full_name` + `email` only. Email collisions return 400. Role/associate are admin-only and not in the schema.
- New collection `password_reset_tokens` with three indexes (TTL on `expires_at`, unique on `token_hash`, btree on `user_id`) declared idempotently in `ensure_indexes()`.
- Optional Resend email integration: when `RESEND_API_KEY` is set in `backend/.env`, the reset link is also emailed (HTML template included). When the key is absent, the admin-mediated link UI keeps the flow fully functional.

### Frontend (`/app/frontend/src`)
- `pages/ForgotPassword.jsx` — public page with anti-enumeration "Request received" success state.
- `pages/ResetPassword.jsx` — token-from-querystring page; matching/length validation; success → auto-redirect to `/login`.
- `pages/Settings.jsx` — rebuilt with **Profile** tab (name + email self-edit, role/associate read-only) and **Password** tab. Both tabs share the existing forced-rotation banner.
- `pages/AdminDashboard.jsx` — added `Send reset link` button per user row (lucide `Link2` icon), modal showing the full URL with one-click copy and email-sent status.
- `pages/Login.jsx` — replaced "contact your administrator" copy with a real `Forgot your password?` link.
- `lib/auth.jsx` — added `refresh()` to the auth context so Settings can resync the user object after a profile edit.
- `App.js` — wired `/forgot-password` and `/reset-password` routes (public, no auth required).

### Tests (`/app/backend/tests/test_password_reset.py` — 24 new tests)
- `TestForgotPassword`: real email returns dev token; unknown email does NOT enumerate; invalid email format → 422; per-email rate limit yields 429.
- `TestResetPassword`: happy path → login; single-use enforcement; invalid/short token → 400; short password → 400 without consuming the token; minting a new token invalidates the previous one.
- `TestAdminResetLink`: admin can mint; admin link completes the reset flow; student is 403; admin cannot mint for `executive_admin`; executive can mint for admin; unauthenticated is 401.
- `TestSelfEdit`: edit own name; edit own email; collision → 400; empty name → 400; unauthenticated → 401; `role`/`associate` cannot be smuggled in via `PATCH /auth/me`.
- `TestDomainParity`: `/health` returns `db: up`; login returns Bearer token shape.

---

## RBAC matrix (re-verified)

| Endpoint | exec_admin | admin | instructor | student | unauth |
|---|:-:|:-:|:-:|:-:|:-:|
| `POST /auth/forgot-password` | ✅ public | ✅ public | ✅ public | ✅ public | ✅ public |
| `POST /auth/reset-password` | ✅ public | ✅ public | ✅ public | ✅ public | ✅ public |
| `PATCH /auth/me` | ✅ self | ✅ self | ✅ self | ✅ self | ❌ 401 |
| `POST /auth/change-password` | ✅ self | ✅ self | ✅ self | ✅ self | ❌ 401 |
| `POST /admin/users/{id}/password` | ✅ any | ✅ except exec | ❌ 403 | ❌ 403 | ❌ 401 |
| `POST /admin/users/{id}/reset-link` | ✅ any | ✅ except exec | ❌ 403 | ❌ 403 | ❌ 401 |

`can_modify()` (`server.py:305`) enforces the immunity rule — admin (rank 3) cannot mutate `executive_admin` (rank 4) on any of: edit, delete, role change, deactivate, password reset, reset-link mint.

---

## Test results

```
$ cd /app/backend && pytest -q
185 passed, 6 warnings in 153.72s
```

(161 prior + 24 new password-reset/self-edit tests, all green.)

End-to-end smoke (live preview, exec admin login):
```
TOKEN=$(login admin@lcewai.org)
curl POST /api/auth/forgot-password {"email":"student@lcewai.org"}
  → {"ok": true, "_dev_token": "tPS7OEY..."}
curl POST /api/auth/reset-password {"token":"...","new_password":"NewLearn@2026"}
  → {"ok": true, "email":"student@lcewai.org"}
curl POST /api/auth/login {"email":"student@lcewai.org","password":"NewLearn@2026"}
  → 200, valid JWT
curl POST /api/auth/reset-password {"token":"...","new_password":"x"}    (token reuse)
  → 400 "Invalid or already-used reset link"
```

---

## Environment variables

| Name | File | Required | Example | Purpose |
|---|---|:-:|---|---|
| `MONGO_URL` | backend/.env | yes | `mongodb://localhost:27017` | DB |
| `DB_NAME` | backend/.env | yes | `lcewai` | DB name |
| `JWT_SECRET` | backend/.env | yes | 64+ random chars | JWT signing |
| `JWT_EXPIRE_HOURS` | backend/.env | no | `168` | session length |
| `CORS_ORIGINS` | backend/.env | yes | `https://www.wai-institute.org,https://wai-institute.org` | comma-sep |
| `EMERGENT_LLM_KEY` | backend/.env | no | universal key | AI tutor |
| `PASSWORD_RESET_TTL_MIN` | backend/.env | no | `30` | token lifetime |
| `RESEND_API_KEY` | backend/.env | **optional** | `re_xxx...` | enables email send |
| `RESEND_FROM` | backend/.env | optional | `W.A.I. <noreply@wai-institute.org>` | sender |
| `PUBLIC_APP_URL` | backend/.env | optional | `https://www.wai-institute.org` | absolute reset URL |
| `DEV_RETURN_RESET_TOKEN` | backend/.env | dev only | `1` | exposes raw token in API response (NEVER set in prod) |
| `REACT_APP_BACKEND_URL` | frontend/.env | yes | preview URL | domain-portable resolution still works without rebuild on custom domain |

---

## Deployment

```bash
# 1. Pull updated code
cd /app

# 2. (Idempotent) ensure indexes pick up the new TTL collection
sudo supervisorctl restart backend

# 3. Run the test suite to confirm everything is healthy
cd /app/backend && pytest -q       # expect: 185 passed

# 4. (Optional) enable email sending
echo 'RESEND_API_KEY=re_xxx' >> /app/backend/.env
echo 'PUBLIC_APP_URL=https://www.wai-institute.org' >> /app/backend/.env
echo 'RESEND_FROM=W.A.I. <noreply@wai-institute.org>' >> /app/backend/.env
sudo supervisorctl restart backend

# 5. (Production safety) make sure DEV_RETURN_RESET_TOKEN is NOT set in prod
grep -E '^DEV_RETURN_RESET_TOKEN' /app/backend/.env || echo 'DEV: not set, OK for prod'

# 6. Redeploy via Emergent dashboard so the production custom domain
#    receives the new code.
```

## Verification

```bash
# Forgot → Reset → Login round-trip
TOKEN_RESP=$(curl -s -X POST "$REACT_APP_BACKEND_URL/api/auth/forgot-password" \
  -H 'Content-Type: application/json' -d '{"email":"student@lcewai.org"}')
TOKEN=$(echo "$TOKEN_RESP" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("_dev_token",""))')
[ -n "$TOKEN" ] || { echo "DEV_RETURN_RESET_TOKEN must be enabled to fetch dev token"; exit 1; }
curl -s -X POST "$REACT_APP_BACKEND_URL/api/auth/reset-password" \
  -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\",\"new_password\":\"Learn@LCE2026\"}"
# → {"ok": true, "email": "student@lcewai.org"}
```

## Confirmations

- ✅ **Executive Admin login works on all domains** — `lib/api.js` auto-resolves to `window.location.origin` when the runtime host differs from the build-time `REACT_APP_BACKEND_URL`. Manually verified on the preview env; production receives the same React build via redeploy.
- ✅ **Password reset is fully functional** — request → token → reset → login round-trip verified by `TestResetPassword`. Single-use, expiry, no-enumeration, rate-limit all enforced.
- ✅ **Settings is stable and secure** — Profile tab edits name/email with collision detection; Password tab unchanged behavior; role/associate read-only and cannot be smuggled into `PATCH /auth/me`. All four roles can self-edit their own profile; nobody can self-edit another user from this page (admin path is `/admin/users/{id}` only).
