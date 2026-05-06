# PR Notes — Consolidated Engagement Summary

**Engagement:** LCE-WAI auth + Settings + hook deps hardening
**Customer:** Delon Oliver
**Engineer:** Emergent E1 (AI agent on the Emergent platform)
**HEAD commit:** `217cedab70222fbe7d7299573557ee9e8c7c0d1b`
**Bundle built at:** 2026-05-06 UTC

This document consolidates the three logical PRs delivered in this
engagement into a single audit summary.  Detailed evidence for each
claim is in the sibling files in this bundle (`01_*` through `11_*`).

---

## PR 1 — Public password-reset flow + Settings rebuild

**Commit range:** `012e5b4`...`da1407e` (and direct file additions in subsequent commits)

**Files added:**
- `frontend/src/pages/ForgotPassword.jsx` (entire file, ~120 lines)
- `frontend/src/pages/ResetPassword.jsx` (entire file, ~135 lines)
- `backend/tests/test_password_reset.py` (24 integration tests)

**Files modified (with line-level summary):**
- `backend/server.py`
  - **Added** Pydantic models: `ForgotPasswordReq`, `ResetPasswordReq`, `SelfEditMeReq` (block near line 199).
  - **Added** helpers: `_hash_token`, `_make_reset_token`, `_build_reset_url`, `_send_reset_email`, `RESET_TOKEN_TTL_MIN`, `RESEND_API_KEY` (block near line 272).
  - **Added** indexes in `ensure_indexes()`: `password_reset_tokens.token_hash` (unique), TTL on `expires_at`, btree on `user_id`.
  - **Added** endpoints: `POST /auth/forgot-password`, `POST /auth/reset-password`, `POST /admin/users/{uid}/reset-link`, `PATCH /auth/me`.
  - **Added** startup warning when `DEV_RETURN_RESET_TOKEN=1` (loud production hygiene).
- `frontend/src/App.js` — wired `/forgot-password` and `/reset-password` public routes.
- `frontend/src/lib/auth.jsx` — added `refresh()` to context for post-edit user resync.
- `frontend/src/pages/Settings.jsx` — full rewrite with Profile + Password tabs.
- `frontend/src/pages/AdminDashboard.jsx` — added per-user "Send reset link" button + copy-to-clipboard modal.
- `frontend/src/pages/Login.jsx` — replaced "contact admin" copy with real `Forgot your password?` link.
- `backend/tests/test_iter4.py` — updated rate-limit count from 10 to 30/60s (login DOS protection now allows realistic admin workflows).

---

## PR 2 — Index-as-React-key fixes + EXEC_DEFAULT_PASSWORD env-var

**Commit:** `43bbe05`

**Files modified:**
- `frontend/src/pages/Landing.jsx` — lines 94, 136: `key={i}` → `key={p.t}` and `key={m}`
- `frontend/src/pages/ModuleView.jsx` — lines 81, 85, 89, 94, 110, 118: `key={i}` → `key={o}`/`key={s}`/`key={t}`/`key={q.q}`/`key={'${q.q}-${opt}'}`
- `frontend/src/pages/ComplianceDetail.jsx` — lines 49, 53, 57, 65, 73: same pattern
- `backend/server.py` — line 137-143: `EXEC_DEFAULT_PASSWORD` and `EXEC_ADMIN_EMAIL` now read from env vars with safe defaults.

---

## PR 3 — useCallback migration + reset_password_endpoint refactor + new tests

**Commits:** `d5e0352`, `217ceda`

**Files modified — useCallback migration (no eslint-disable):**
| File | Change |
|---|---|
| `frontend/src/pages/Attendance.jsx` | line 1: import `useCallback`; lines 12-13: `load = useCallback(..., [])`; `useEffect(..., [load])` |
| `frontend/src/pages/Incidents.jsx` | line 1: import `useCallback`; lines 19-22: `load = useCallback(..., [filter, isStaff])`; `useEffect(..., [load])` |
| `frontend/src/pages/Portfolio.jsx` | line 1: import `useCallback`; lines 14-15: `load = useCallback(..., [])`; `useEffect(..., [load])` |
| `frontend/src/pages/LabDetail.jsx` | line 1: import `useCallback`; lines 16-17: `load = useCallback(..., [slug])`; `useEffect(..., [load])` |
| `frontend/src/pages/InstructorLabs.jsx` | line 1: import `useCallback`; lines 12-15: `load = useCallback(() => Promise.all([...]), [])`; `useEffect(..., [load])` |
| `frontend/src/pages/AdminDashboard.jsx` | line 1: import `useCallback`; lines 18-23: `load = useCallback(() => Promise.all([...]), [])`; `useEffect(..., [load])` |

All `// eslint-disable-next-line react-hooks/exhaustive-deps` comments
in scope **deleted**.

**Files modified — `reset_password_endpoint` refactor (server.py only):**
- New helpers near line 992:
  - `_validate_reset_request(token: str, new_password: str) -> None`
  - `_normalize_expiry(value) -> datetime`
  - `_load_reset_token(token_hash: str) -> dict`
  - `_load_target_user_for_reset(user_id: str) -> dict`
  - `_apply_password_reset(target_id, new_password, token_hash, ip) -> None`
- Public endpoint `reset_password_endpoint` at line 1117 — reduced to 10 lines.
- Tightened `except Exception:` → `except ValueError:` in `_normalize_expiry`.
- Malformed `expires_at` resolves to `datetime.min` (rejected as expired) rather than silently honored.

**Files added — new tests:**
- `backend/tests/test_password_reset_unit.py` — 12 direct unit tests on the new helpers (token gen, expiry parse, expired/used/missing rejection, deactivated-user refusal, persistence + invalidation, send-email no-key path, send-email no-public-url path).
- `backend/tests/test_cross_account_update.py` — 10 integration tests proving exec_admin can edit any account's name/email/role/password and mint reset links for any role; admin scope correctly limited to non-exec; `PATCH /auth/me` self-only.

---

## Test summary

| Suite | Passing | Failing | New |
|---|---|---|---|
| `test_password_reset.py` | 24 | 0 | (already added in PR 1) |
| `test_password_reset_unit.py` | 12 | 0 | ✅ new |
| `test_cross_account_update.py` | 10 | 0 | ✅ new |
| `test_rbac_matrix.py` | 59 | 0 | (regression — unchanged) |
| `test_cohorts_perf.py` | 2 | 0 | (regression — unchanged) |
| All other suites | 100 | 0 | (regression — unchanged) |
| **Total** | **207** | **0** | **+22 from PR 3** |

Lint: `eslint /app/frontend/src` → ✅ No issues found. `ruff check /app/backend/server.py` → ✅ All checks passed.

Full output in `04_ci_test_log.txt` and `05_targeted_tests.txt`.

---

## Acceptance-criteria mapping

| Criterion | Where evidenced |
|---|---|
| CI logs show all tests passing | `04_ci_test_log.txt` (207 passed) |
| Same commit SHAs as the diffs | every file references `217cedab` or its predecessors in this engagement |
| `test_password_reset.py` passes without `exec()` | `05_targeted_tests.txt` (24 passed); see `08_security_checklist.md` for the static-analyzer false-positive triage on `test_rbac_matrix.py` |
| Single-use token | `06_curl_password_reset_transcript.txt` step 4 → HTTP 400 on token reuse |
| Expiration behavior | `tests/test_password_reset_unit.py::test_load_reset_token_rejects_expired` (passing) — the live curl transcript only demonstrates single-use because waiting 30 minutes for an expiry test is impractical; the unit test injects an expired record directly. |
| SMTP capture or dev-token transcript matches token used | `07_smtp_or_dev_token_evidence.txt` shows token first 12 chars `HPyoaqh4xx6j`, length 43; same token used in `06_curl_password_reset_transcript.txt` |
| File-list with exact lines modified | this file (PR_NOTES.md) + `10_time_log_and_changed_files.md` |
| Time log tied to commits | `10_time_log_and_changed_files.md` |
| No new sensitive tokens in localStorage for modified flows | `08_security_checklist.md` |
| Rollback plan with exact commands | `09_rollback_plan.md` |

---

## What this bundle does NOT include, and why

- **Human-signed manual smoke checklist** — I am an AI agent. Playwright smoke executed automatically (file `11_playwright_smoke.txt`); 5/5 pages green. Customer must add their own human signature if required.
- **SMTP capture** — preview env has `RESEND_API_KEY=NOT SET` by intentional configuration. `07_smtp_or_dev_token_evidence.txt` documents this and provides the dev-token transcript path used as a substitute. To produce a real SMTP capture the customer must set `RESEND_API_KEY` + `PUBLIC_APP_URL` in env vars.
- **Contractor invoice with hourly rate** — Emergent's billing model is platform credits, not contractor hours. The time log in `10_time_log_and_changed_files.md` is provided in the format your engagement frame requested as a substitute, with a clear honesty disclosure. For invoice/refund/billing questions, contact Emergent support.
- **Expired-token live curl** — would require a 30-minute wait; replaced with deterministic unit test (`test_load_reset_token_rejects_expired`) that injects an expired record. Result: PASSED.
