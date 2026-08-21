# Public Launch Readiness Audit — M.O.R.E. / W.A.I. Platform

**Date:** August 21, 2026 · **Method:** direct code inspection of `main` (backend, frontend, deploy config). No fluff. Every claim below is checkable against the code.

---

## Verdict

**Not ready for public launch — but closer than the repo's history suggests.** The core is real: MongoDB data layer with proper indexes, JWT auth with hashing + rate limiting + recovery codes, RBAC with rank-based 403 enforcement, a real payments pipeline (Lemon Squeezy → Gumroad fallback) with a signed webhook that grants tiers, GDPR export/deletion endpoints, privacy policy + terms + cookie consent, and a single-service Docker deploy on Railway with a healthcheck.

What separates you from launch is **not** missing features. It is: unverified behavior under production conditions, config that silently degrades, no monitoring, no CI gate, and a 146-route frontend nobody has triaged.

---

## What is REAL (verified in code)

| Area | Evidence |
|---|---|
| Auth | `routers/auth.py` — register/login/reset/recovery codes; Resend email + Gmail SMTP fallback |
| RBAC | Role ranks, `_require_rank`, `test_rbac_matrix.py` exists |
| Data | `database.py` — Mongo collections + indexes for subscriptions, invoices, payment methods, usage events |
| Payments | `routers/payments.py` — checkout via Lemon Squeezy, Gumroad fallback, signed `/webhook` granting tiers |
| GDPR | `GET /auth/account/export` + gdpr erasure path (`gdpr_deleted_at`) |
| Compliance pages | PrivacyPolicy.jsx (substantive), TermsOfService.jsx, CookieConsent mounted in App.js |
| SEO | robots.txt, sitemap.xml, title/description meta |
| Deploy | Dockerfile multi-stage (React build served by FastAPI), Railway healthcheck `/api/version` |

## Launch Blockers (in priority order)

### B1. `JWT_SECRET` silently regenerates on every boot
`server.py:167`: `JWT_SECRET = os.environ.get('JWT_SECRET') or _secrets.token_hex(32)`.
If the env var is unset in production, **every deploy logs out every user** and any second instance rejects tokens from the first. Fix: set a strong persistent `JWT_SECRET` in Railway variables and fail startup if it's missing (no fallback).

### B2. Zero security headers
No CSP, no `X-Frame-Options`, no HSTS, no HTTPS-redirect middleware anywhere in server.py. Trivial clickjacking/sniffing exposure and an automatic flag in any security review. Fix: ~20 lines of middleware.

### B3. No error monitoring, no uptime alerting
No Sentry/equivalent in backend or frontend. You will learn about outages from users, not dashboards. For a site taking money this is non-negotiable.

### B4. Tests exist but nothing runs them
25+ test files in `backend/tests/`, but pytest isn't even installed in the dev sandbox and there is **no CI**. Nothing prevents a red deploy. Fix: CI job running `pytest` on every push; fix or delete failing tests honestly.

### B5. Email deliverability is unproven
`RESEND_FROM` defaults to a bare gmail address. Resend requires domain verification to send from your own domain; without it, password-reset emails (your #1 support burden at launch) land in spam or get rejected. Also: personal Gmail addresses are hardcoded as fallbacks in `auth.py` (`BACKUP_EXEC_EMAIL`). Move all identity config to env vars.

### B6. Payments never verified end-to-end
The flow creates products on-the-fly via Lemon Squeezy's publish API and grants tiers on webhook. Clever, but **zero evidence of a completed test purchase**. One bad webhook signature check = paying users who don't get access. Fix: LS test-mode purchase → verify tier grant → verify refund path. Write a refund policy first (LS requires one).

### B7. 146 frontend routes, untriaged
Every route is public attack/maintenance surface. Some work, many are shells left from prior sessions. Fix: full inventory scored keep / fix / cut; delete the cuts. A smaller honest site beats a big broken one.

### B8. Privacy policy makes promises to verify
It promises self-service Export and Delete Account. Export exists (`/auth/account/export`). Deletion: admin-side deletion confirmed; **self-service deletion endpoint needs verification** — if it's missing, either build it or amend the policy before launch.

### B9. No database backup strategy
MongoDB on Railway/local volume with no stated backup schedule. Losing the DB loses user accounts AND purchase records — the latter is a legal/tax problem, not just an ops one.

### B10. AI disclosure gap
Only GhostProducer.jsx mentions AI-generated content. If any persona/chat output is user-facing, add a global AI-content disclosure — cheap now, expensive later.

---

## Phased Plan (reality-based)

**Phase 0 — Hardening (days, do before anything else)**
1. Set persistent `JWT_SECRET`, lock `CORS_ORIGINS` to real domains, remove hardcoded personal-email defaults.
2. Add security headers middleware.
3. Verify/build self-service account deletion.
4. Verify Resend sending domain; set branded from-address.

**Phase 1 — Route triage (week)**
5. Inventory all 146 routes; mark keep/fix/cut with reasons; execute cuts.
6. Landing page scroll + notification bell: confirm fixed on the deployed URL, not just in code.

**Phase 2 — End-to-end verification (week)**
7. Stand up CI running the existing test suite; fix failures truthfully.
8. Full test-mode purchase: checkout → webhook → tier grant → refund.
9. Auth flows on prod URL: register, reset email arrives + works, recovery codes, IAM console role change with atomic re-read.

**Phase 3 — Ops baseline (week)**
10. Error monitoring (Sentry free tier covers both ends).
11. Uptime monitoring hitting `/api/version`.
12. MongoDB backups on a schedule + one documented restore test.

**Phase 4 — Legal/compliance closeout**
13. ToS + refund policy reviewed against actual product behavior.
14. Global AI-content disclosure.
15. Privacy policy final pass matching verified reality.

**Launch gate:** Phases 0–3 complete + one friend successfully registers, resets a password, buys a product, and gets their tier — on the production URL.

---

*Honest bottom line: you have a real skeleton. Spend the next two weeks making it verifiable instead of adding features. A small platform where every promise works outranks a large one where most don't.*
