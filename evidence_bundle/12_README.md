# Evidence Bundle — Index

**Engagement:** LCE-WAI auth + Settings + hook-deps hardening
**Bundle built at:** 2026-05-06T01:32:41Z
**Commit at HEAD:** `217cedab70222fbe7d7299573557ee9e8c7c0d1b`
**Bundle archive:** `EVIDENCE_BUNDLE.zip`

## Contents

| File | Purpose |
|---|---|
| `00_bundle_built_at.txt` | UTC timestamp the bundle was generated. |
| `_PR_NOTES.md` | Consolidated engagement summary — files changed, lines, acceptance-criteria mapping, honest disclosures. |
| `01_diff_useCallback_PR.patch` | Git diff for PR 3 (useCallback hook-dep migration on 6 files). |
| `02_diff_reset_password_refactor.patch` | Git diff for the `reset_password_endpoint()` refactor in `server.py`. |
| `03_new_test_files.txt` | Full source of the two new test files (`test_password_reset_unit.py` + `test_cross_account_update.py`) as added in commit `217ceda`. |
| `04_ci_test_log.txt` | Full backend pytest run output: 207 passed, with timestamps and commit SHA. |
| `05_targeted_tests.txt` | Targeted runs: `test_password_reset.py`, `test_password_reset_unit.py`, `test_cross_account_update.py`, and exec-admin RBAC. |
| `06_curl_password_reset_transcript.txt` | Live curl transcript: forgot → reset → login → reuse-fails → fake-fails. HTTP status sequence 200/200/200/400/400. |
| `07_smtp_or_dev_token_evidence.txt` | Confirms SMTP/Resend not configured in preview env; documents dev-token return path; shows captured token (first 12 chars + length) matches token used in `06_*`. |
| `08_security_checklist.md` | Per-file localStorage audit; security claims with linked test names. |
| `09_rollback_plan.md` | Emergent-dashboard rollback (recommended) + git-level rollback (advanced) + DB and env-var rollback (none required). |
| `10_time_log_and_changed_files.md` | Per-commit log + machine-readable JSON manifest of changed files; honest disclosure that this is an AI-engagement, not contractor hours. |
| `11_playwright_smoke.txt` | Frontend Playwright smoke results for the 5 named pages. |
| `12_README.md` | This file. |

## Acceptance-criteria checklist

| Criterion | Status | Evidence |
|---|---|---|
| Full test suite passes | ✅ 207/207 | `04_ci_test_log.txt` |
| `test_password_reset.py` passes | ✅ 24/24 | `05_targeted_tests.txt` |
| Settings tests pass | ✅ 16/16 (unit + integration) | `05_targeted_tests.txt` |
| Curl transcript shows single-use enforcement | ✅ HTTP 400 on reuse | `06_curl_password_reset_transcript.txt` step 4 |
| Curl transcript shows expiration behavior | partial — covered by deterministic unit test (`test_load_reset_token_rejects_expired`); waiting 30 min in a curl loop is impractical | `04_ci_test_log.txt`, `08_security_checklist.md` |
| SMTP / dev-token capture matches curl token | ✅ matching first-12-chars + length | `07_smtp_or_dev_token_evidence.txt` |
| PR_NOTES with files + lines | ✅ | `_PR_NOTES.md` |
| Time log tied to commits | ✅ | `10_time_log_and_changed_files.md` |
| No new sensitive tokens in localStorage for modified flows | ✅ verified by `git diff | grep -i localStorage` | `08_security_checklist.md` |
| Rollback plan with exact commands | ✅ | `09_rollback_plan.md` |
| No `exec()` in `test_rbac_matrix.py` | ✅ (was always 0; static-analyzer false-positive triaged) | `08_security_checklist.md` |
| All authorized scope items delivered | ✅ | `_PR_NOTES.md` PR 1 / PR 2 / PR 3 sections |

## How to verify everything yourself

From the project root in the Emergent host shell:
```bash
# Confirm HEAD matches
git rev-parse HEAD
# expect: 217cedab70222fbe7d7299573557ee9e8c7c0d1b

# Re-run the full backend test suite
cd /app/backend && pytest -q

# Re-run targeted password-reset tests
cd /app/backend && pytest tests/test_password_reset.py tests/test_password_reset_unit.py tests/test_cross_account_update.py -v

# Re-run frontend lint
cd /app/frontend && npx eslint src

# Re-run backend lint
cd /app/backend && ruff check server.py

# Re-execute the curl password-reset round-trip
bash /app/evidence_bundle/12_replay_curl.sh   # (provided in this bundle)
```

## Honesty disclosures

The following items in your engagement frame I cannot honestly produce
and have substituted with the closest verifiable artifact:

1. **Contractor invoice with hourly rate** — I am an AI agent on the Emergent platform. Billing for this work flows through Emergent's credit system (visible in your dashboard), not via contractor invoicing. Substitute: per-commit time log in `10_time_log_and_changed_files.md`.
2. **SMTP test mailbox capture** — preview env has no Resend key configured by intentional configuration. Substitute: dev-token return path documented in `07_smtp_or_dev_token_evidence.txt` and the same token is used end-to-end in the curl transcript.
3. **Human tester signature on the smoke checklist** — Playwright executed all 5 named pages automatically. Customer must add a human signature if your governance requires one.
4. **Live expired-token curl** — would require a 30-minute wait. Substitute: deterministic unit test `test_load_reset_token_rejects_expired` injects an expired record directly. PASSED in `04_ci_test_log.txt`.

These substitutions are documented openly here and in each affected
sub-file rather than hidden, in keeping with your engagement frame's
non-negotiable: "Do not alter or fabricate CI logs, test outputs, or
SMTP captures."
