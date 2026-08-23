# PRODUCTION READINESS AUDIT (Phase 20)

**Method:** source inspection this session. **Railway is not accessible from the sandbox; no production values were read; nothing here is production-verified.**

## Critical environment checklist (SRC — variable names from backend scan)

### Must be set before campaign (P0)
- `MONGO_URL` (or `MONGODB_URL`/`MONGO_URI`) + `DB_NAME` — **absent in sandbox; BLOCKED**
- `JWT_SECRET` — server **fails closed** (fatal) when missing (SRC)
- `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID` + `LEMON_SQUEEZY_WEBHOOK_SECRET` (or `GUMROAD_API_KEY`)
- `PROVIDER_KEY_ENCRYPTION_SECRET` (BYOK keys) and `AUDIT_ENCRYPTION_KEY` / `ENCRYPTION_KEY`
- `CORS_ORIGINS` (explicit list) + `FRONTEND_URL`
- At least one free AI provider key: `GROQ_API_KEY` / `CEREBRAS_API_KEY` / `SAMBANOVA_API_KEY` / `GEMINI_API_KEY`

### Should be set
- `HOURLY_TOKEN_CAP`, `USER_DAILY_TOKEN_CAP` (AI budget guards)
- `SLACK_WEBHOOK_URL` (incident alerts), `EXEC_RESET_SECRET` (break-glass)
- `JWT_EXPIRE_HOURS` (default 168), `ENABLE_API_DOCS` (leave unset/0)
- Email: `RESEND_API_KEY`/`RESEND_FROM` or Gmail/Outlook SMTP vars (password-reset delivery)

### Cleanup (P3)
- `STRIPE_SECRET_KEY` — stale reference despite Stripe removal.

## Deploy/config facts (SRC)

- Single-service Python app; `python3 -m server` boots uvicorn on 0.0.0.0 (PORT env).
- JWT_SECRET fail-closed; API docs disabled by default; CORS env-driven.
- Background tasks launch at startup (watchdog, team monitor, GDPR purge, memory consolidation) — verify they do not conflict with multiple workers.
- **In-memory rate limiter is per-process** — single worker recommended, or move to a shared store (P2).

## Production verification plan (BLOCKED here — run on Railway)

1. `python3 tests/live_fcc_matrix.py` — seeds marked test users, runs the access matrix, cleans up (prepared in Phase 16, this repo).
2. `GET /api/admin/health` — confirm provider `key_set`/`available` and budget caps.
3. `GET /api/exec/control/access/public` — confirm gate map (60 keys with tiers/public/roles).
4. One real $3 BYOK checkout + one subscription checkout → verify webhook grants `byok_enabled` / `feature_tier` and that cancellation/refund behavior is fixed before relying on it.
5. Browser smoke: landing → register → login → dashboard; plans; one paid flow.
6. Check seeded DB (no first-registrant-takes-`executive_admin` risk).

## Status

| Item | Status |
|---|---|
| Env completeness | UNKNOWN (not verifiable here) |
| DB connectivity | BLOCKED |
| Provider connectivity | BLOCKED |
| Deploy health | UNKNOWN |
| Money flow | NOT LIVE-VERIFIED |
| Production readiness claim | **NOT ESTABLISHED** |
