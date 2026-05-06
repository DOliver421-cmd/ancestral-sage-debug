# Rollback Plan

**Commit SHA at HEAD of this engagement:** `217cedab70222fbe7d7299573557ee9e8c7c0d1b`
**Previous stable checkpoint:** `5e970e459` (auto-commit `ffabb64d-aa07-409a-a260-e8b9370c6341` — pre-feature-branch state)

## Scope of changes that may need reversal

This engagement landed three logical PRs on top of preview HEAD:

| PR | First commit | Last commit | Files changed |
|---|---|---|---|
| (P1 prior session) reset-password feature build | `da1407e` | `366d6c2` | server.py, frontend/src/pages/{ForgotPassword,ResetPassword,Settings,AdminDashboard,Login}.jsx, App.js, lib/auth.jsx, tests/test_password_reset.py |
| Index-as-key + EXEC_DEFAULT_PASSWORD env-var | `43bbe05` | `43bbe05` | frontend/src/pages/{Landing,ModuleView,ComplianceDetail}.jsx, server.py |
| useCallback + reset_password_endpoint refactor + new tests | `d5e0352` | `217ceda` | server.py, frontend/src/pages/{Attendance,Incidents,Portfolio,LabDetail,InstructorLabs,AdminDashboard}.jsx, tests/test_password_reset_unit.py, tests/test_cross_account_update.py |

## Rollback options (least disruptive first)

### Option A — Emergent dashboard rollback (recommended)

This is the official, supported path and preserves the platform's
checkpoint history.

1. Open the project in the Emergent dashboard.
2. Navigate to the **Checkpoints** view.
3. Select a checkpoint dated before this engagement (any commit `<= 5e970e4`).
4. Click **Rollback to this checkpoint**.
5. Redeploy.

### Option B — Git-level rollback (advanced; only if Option A unavailable)

Because Emergent auto-commits each step, individual commits can be
reverted directly. From the project root in the Emergent host shell:

```bash
# Show the commit graph for these PRs
git log --oneline da1407e..217ceda

# Revert all engagement commits in reverse order with a single merge commit.
# This produces a clean, auditable revert chain.
git revert --no-edit 217ceda d5e0352 43bbe05 da31e71 012e5b4 8029475 \
                    5e970e4 2d63d2a d4a54b6 bee299f cd1dc30 366d6c2 \
                    303b2c5 70db2d4 29f325e 61e742f fbf3abd ec8acd0 \
                    59d2d88 da1407e

# Restart services so the reverted code loads.
sudo supervisorctl restart backend frontend
```

## Database rollback

**No DB rollback required.** All DB changes in this engagement are additive:

| Change | Forward-compatible? | Reverse needed? |
|---|---|---|
| New collection `password_reset_tokens` | YES — older code simply never touches it | NO. Collection can be left in place; if desired, drop with `db.password_reset_tokens.drop()` from a Mongo shell. |
| New index `progress(status, user_id)` | YES — older code's queries still work, just without this index's optimization | NO. Optional drop with `python3 backend/migrations/2026_02_cohorts_n1_indexes.py down`. |
| New index `users(associate, role)` | YES — same as above | NO. |
| TTL index on `password_reset_tokens.expires_at` | YES — only affects the new collection | NO. |
| New unique index on `password_reset_tokens.token_hash` | YES — only affects the new collection | NO. |

## Environment variable rollback

**No env-var rollback required.** All new env vars (`PASSWORD_RESET_TTL_MIN`,
`RESEND_API_KEY`, `RESEND_FROM`, `PUBLIC_APP_URL`, `DEV_RETURN_RESET_TOKEN`,
`EXEC_ADMIN_EMAIL`, `EXEC_DEFAULT_PASSWORD`) have safe defaults; absence does
not break anything.

If the customer wishes to clean up the preview-only `DEV_RETURN_RESET_TOKEN=1`
flag from `/app/backend/.env`, remove that one line and restart backend:
```
sed -i '/^DEV_RETURN_RESET_TOKEN=/d' /app/backend/.env
sudo supervisorctl restart backend
```

## Verifying rollback

After either rollback path, run:
```bash
cd /app/backend && pytest -q
```
The test count should drop from 207 to whatever the pre-engagement baseline
was (161 before the password-reset PR; 159 before the cohort N+1 fix).
