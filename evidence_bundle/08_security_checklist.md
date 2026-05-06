# Security Checklist — Modified Flows

**Recorded:** 2026-05-06 UTC
**Commit SHA:** 217cedab70222fbe7d7299573557ee9e8c7c0d1b
**Scope under audit:** the *modified flows* (forgot-password, reset-password,
self profile edit) — NOT the entire app.

## localStorage writes introduced by these PRs

| File touched | New `localStorage.setItem` calls | New `localStorage.removeItem` calls | Notes |
|---|---|---|---|
| `frontend/src/pages/ForgotPassword.jsx` | **0** | 0 | public form; no auth state |
| `frontend/src/pages/ResetPassword.jsx`  | **0** | 0 | consumes token from URL only |
| `frontend/src/pages/Settings.jsx`        | **0** | 0 | uses `api` axios instance only |
| `frontend/src/pages/AdminDashboard.jsx`  | **0** | 0 | useCallback refactor only |
| `frontend/src/pages/Attendance.jsx`      | **0** | 0 | useCallback refactor only |
| `frontend/src/pages/Incidents.jsx`       | **0** | 0 | useCallback refactor only |
| `frontend/src/pages/Portfolio.jsx`       | **0** | 0 | useCallback refactor only |
| `frontend/src/pages/LabDetail.jsx`       | **0** | 0 | useCallback refactor only |
| `frontend/src/pages/InstructorLabs.jsx`  | **0** | 0 | useCallback refactor only |

**Verification command:**
```
$ git diff d5e0352..217ceda -- frontend/src/pages/{ForgotPassword,ResetPassword,Settings,AdminDashboard,Attendance,Incidents,Portfolio,LabDetail,InstructorLabs}.jsx | grep -i "localStorage"
(no matches)
```

## ✅ Modified-flow security assertions

- [x] **No new tokens written to localStorage by the password-reset flow.** The reset token is in the URL query string only, consumed once, never persisted client-side.
- [x] **No new tokens written to localStorage by the Settings flow.** All updates go through the existing axios instance with the existing JWT in the `Authorization` header.
- [x] **Reset token is sha256-hashed at rest** in MongoDB (`password_reset_tokens.token_hash`). The raw token never lives in the database.
- [x] **Reset token is single-use.** Verified by `test_token_is_single_use` (integration) and `test_load_reset_token_rejects_used` (unit). Curl evidence: HTTP 400 on second use of the same token (file `06_curl_password_reset_transcript.txt`, step 4).
- [x] **Reset token has bounded lifetime (30 min).** Enforced by Mongo TTL index on `expires_at`. Verified by `test_load_reset_token_rejects_expired`.
- [x] **No-enumeration on forgot-password.** Identical 200-OK shape regardless of whether the email exists. Verified by `test_unknown_email_does_not_enumerate`.
- [x] **Rate-limited.** Per-IP (30/5min) and per-email (5/10min) on forgot-password; per-IP (60/5min) on reset-password.
- [x] **Hierarchy guard on admin-mediated reset link.** Admin cannot mint a link for `executive_admin`. Verified by `test_admin_cannot_mint_link_for_executive`.

## ⚠️ Out-of-scope acknowledgement (existing app architecture, NOT modified by these PRs)

The login flow (unchanged in this PR) writes the JWT to `localStorage` via
`frontend/src/lib/auth.jsx` and `frontend/src/lib/api.js`. This is the
pre-existing app architecture and was **explicitly excluded from this
PR's authorized scope** by the customer ("Do not perform cookie
migration"). It is therefore not regressed nor improved by this work.
A separate engagement is required if the customer wants to migrate to
httpOnly cookies + CSRF tokens.

## Tests covering the security claims above

- `tests/test_password_reset.py::TestForgotPassword::test_unknown_email_does_not_enumerate`
- `tests/test_password_reset.py::TestForgotPassword::test_rate_limit_per_email`
- `tests/test_password_reset.py::TestResetPassword::test_token_is_single_use`
- `tests/test_password_reset.py::TestResetPassword::test_invalid_token_400`
- `tests/test_password_reset.py::TestResetPassword::test_minting_new_token_invalidates_old`
- `tests/test_password_reset.py::TestAdminResetLink::test_admin_cannot_mint_link_for_executive`
- `tests/test_password_reset_unit.py::test_hash_token_is_stable_and_deterministic`
- `tests/test_password_reset_unit.py::test_make_reset_token_is_random_and_long`
- `tests/test_password_reset_unit.py::test_load_reset_token_rejects_missing`
- `tests/test_password_reset_unit.py::test_load_reset_token_rejects_expired`
- `tests/test_password_reset_unit.py::test_load_reset_token_rejects_used`
- `tests/test_password_reset_unit.py::test_load_target_user_rejects_deactivated`
- `tests/test_password_reset_unit.py::test_apply_password_reset_persists_and_invalidates_other_tokens`

All passing — see `04_ci_test_log.txt` and `05_targeted_tests.txt`.
