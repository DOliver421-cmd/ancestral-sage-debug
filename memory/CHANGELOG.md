## Feb 2026 — Ancestral Sage AI persona
- **NEW persona** in AI Tutor: **Ancestral Sage** — Pan-African, pro-Black, spiritually-grounded mentor and guide, using the Compass icon in copper. Joins the existing 6 modes as a 7th option.
- **Backend (`server.py`)**:
  - `AIChatReq` extended with optional `depth`, `intensity`, `cultural_focus`, `divination_mode`, `safety_level`, `consent_log_id`, `scope` fields (Literal-validated where the spec dictates).
  - New `AIConsentReq` model + `POST /api/ai/consent` — validates the canonical YES + verbatim comprehension phrase (`"I understand and accept the risks of this practice."`), writes to `ai_consents` collection, returns `{consent_log_id, expires_at, ttl_minutes}`. Default TTL: 120 minutes.
  - `ai_chat` gating runs **before** the LLM call (zero LLM cost on a refusal):
    - If `intensity=deep` OR `safety_level in {exploratory, extreme}` → require valid, unexpired, user-scoped `consent_log_id` else 403.
    - Crisis short-circuit: if user message contains explicit suicidal phrasing, return canonical safety reply with crisis-line resources (988, Crisis Text Line, findahelpline.com) and `safety_intervention: true` — no LLM call.
    - All five session parameters injected into the system prompt at request time, plus `consent_log_id (consent granted)` line when present.
    - `scope=wai_training_only` appends a strict-scope override directive that confines the persona to W.A.I. curriculum.
  - `chat_history` rows for sage sessions now record `intensity`, `safety_level`, `consent_log_id`, `scope`, and `refusal_reason` for auditability.
  - System prompt for `ancestral_sage` faithfully encodes all 5 immutable rules, output format ("Summary / Consent status / Response / Aftercare"), provenance tags for living-tradition rituals, and the "Fringe interpretation — non-mainstream" labeling rule.
- **Frontend (`pages/AITutor.jsx`)**:
  - New `Ancestral Sage` mode pill with `Compass` lucide icon (copper / `text-copper`); accessible `aria-label` and tooltip "Ancestral Sage — Guidance & Readings".
  - `SageParamPanel` reveals 5 dropdowns when persona is active.
  - `ConsentModal` posts to `/api/ai/consent` with two-step verbatim verification; submit disabled until both fields validate locally; consent badge ("Consent active — revoke") appears after grant.
  - Send button auto-switches to a `Lock` icon + "Consent" label when consent is required and not yet granted; restored to `Send` afterwards.
  - 403 responses with "Consent required" reopen the consent modal automatically.
- **Tests (`backend/tests/test_ancestral_sage.py`):** 14 new tests covering consent endpoint phrase validation, RBAC, deep/exploratory/extreme gating, invalid-consent-id rejection, crisis short-circuit, and consented happy-path gate-pass. **All 14/14 green.** Total backend pytest now: **223/223 passing**.
- **Files added:** `pages/AITutor.jsx` (rewrite), `tests/test_ancestral_sage.py`. Files updated: `server.py` (AIChatReq, AIConsentReq, helpers, /ai/consent endpoint, /ai/chat gating).

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

