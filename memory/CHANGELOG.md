## Feb 2026 — Catch-all 404 route (blank-page guardrail)
- **NEW:** `pages/NotFound.jsx` — branded 404 page (blueprint hero left, "Wrong turn" copy right) that displays the unmatched pathname and a context-aware CTA (lands user back on their role-correct dashboard if signed in, or landing if not).
- **App.js:** added `<Route path="*" element={<NotFound />} />` catch-all so any future stale bookmark, typo, or pre-route-deploy URL no longer silently white-screens.
- **Diagnosis driver:** user reported `/admin/users` blank in production. Console showed `No routes matched location '/admin/users'` — production bundle was stale (current preview already defines the route at App.js:76). 404 fallback ensures the failure mode is now graceful instead of silent.
- **Files added:** `pages/NotFound.jsx`. Files updated: `App.js`.

## Feb 2026 — Auth + Password Reset + Settings hotfix
- **NEW:** Public password-reset flow.
  - `POST /api/auth/forgot-password` — no-enumeration response, per-IP + per-email rate limit, sha256-hashed single-use token with 30-min TTL.
  - `POST /api/auth/reset-password` — single-use enforcement, invalidates all other unused tokens for the user, audit logged.
  - `POST /api/admin/users/{uid}/reset-link` — admin-mediated reset link with copy-to-clipboard UI; honours `can_modify()` immunity.
- **NEW:** `PATCH /api/auth/me` — self-service profile edit of `full_name` and `email`. Role/associate stay admin-only.
- **Settings page rebuilt** with Profile + Password tabs. Forced-rotation banner preserved.
- **Login page:** real "Forgot your password?" link replacing the "contact admin" copy.
- **Admin dashboard:** new per-user "Send reset link" button (lucide `Link2`) with modal showing the URL + email-sent status.
- **Optional Resend integration:** when `RESEND_API_KEY` and `PUBLIC_APP_URL` are set, the reset link is emailed via Resend; otherwise the admin-mediated link UI keeps the flow functional.
- **Indexes:** added `password_reset_tokens.token_hash` (unique), `expires_at` (TTL 0), and `user_id`.
- **Rate limits relaxed for realistic admin workflows:** login 30/60s (was 10), forgot-password IP 30/5min (was 10).
- **Tests:** new `tests/test_password_reset.py` (24 tests). Suite total: 185/185 passing.
- **Files added:** `pages/ForgotPassword.jsx`, `pages/ResetPassword.jsx`. Files updated: `server.py`, `Settings.jsx`, `AdminDashboard.jsx`, `Login.jsx`, `App.js`, `lib/auth.jsx`, `tests/test_iter4.py` (rate-limit count update).

## Feb 2026 — P1 hotfix: /admin/cohorts N+1 elimination
(see prior CHANGELOG entry; 161/161 pytest)

