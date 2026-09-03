# MoreHelp Center — Security Hardening Plan

**Date:** 2026-09-03
**Scope:** planning and reporting only. No code was changed to produce this
document; every finding below was verified against the current `main` source
and the live Railway target (`https://charming-analysis-morehelpcenter.up.railway.app`).
**Constraint honored:** every recommendation preserves existing customer-visible
behavior — changes are staged behind flags or as strict supersets, each with a
rollback, and nothing is labelled "fixed" without a live/automated proof per
`AGENTS.md`.

---

## 1. What is already solid (verified — do not disturb)

These were confirmed in source and, where noted, against the live target.
Hardening work must not regress them.

| Area | Evidence |
|---|---|
| Security response headers | `server.py` sets `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `HSTS`, and a CSP (`default-src 'self'; script-src 'self'; ... frame-ancestors 'none'`) on responses (~lines 267–275). |
| Fail-closed auth | Bearer token required; `jwt.decode` validated (not presence-checked); deactivated accounts → 403; `token_version` revocation rejects pre-revocation tokens (server.py `current_user`, `C-2` comment). Live probes: invalid tokens → 401 JSON on every guarded route. |
| Least-privilege SSO | `routers/auth.py` cross-site login hard-codes `role = "student"`, never elevates an existing local user, auto-creates new users as student, audits the exchange, and tracks a session row. |
| Role model | Canonical 8-rank ladder with legacy normalization to least privilege; unknown roles fall back to `student` (`roles.py`). |
| BYOK at rest | Keys stored Fernet-encrypted via the shared keyvault; save **refused** when no encryption secret exists (never silent plaintext); keys never returned to the frontend (masked suffix only); $3 activation requires staff role or recorded payment (`402` otherwise) — `byok.py`, `routers/byok.py`. |
| Auth-path throttling | Register 5/min/email; login 5/min/email; forgot/reset/recovery throttles by IP and email (`server.py` ~1735–2650). |
| Upload handling (reference example) | Director upload: 5 MB hard cap read-bounded, filename sanitized to safe characters (no path traversal), 24h TTL storage in MongoDB (`routers/ai.py` ~1793). |
| Audit + PII | Central `audit()` log with a `_PII_KEYS` redaction helper; binding financial actions carry `human_authorization_meta` (HITL) metadata (`server.py`, `legal_compliance.py`, `routers/abo.py`). |
| Frontend hygiene | Zero `dangerouslySetInnerHTML` uses; a single shared API client attaches the bearer token; the SPA is same-origin behind the API. |
| Runtime config guard | `config.py` `validate_config()` rejects `DEBUG=True` in production and a missing/placeholder `JWT_SECRET` when `ENVIRONMENT=production`; `server.py` reads `JWT_SECRET` via `os.environ[...]` (crash-on-missing = fail closed at boot). |

---

## 2. Findings (risk-ranked)

Severity scale: **High** = exploitable or structurally weak today;
**Medium** = latent or conditional; **Low/Ops** = hygiene.

### High

**H1 — Session token + user profile live in `localStorage`.**
`lce_token` (JWT) and `lce_user` (profile) are read/written from
`localStorage` in `frontend/src/lib/api.js` and `lib/auth.jsx`. Any injected
script on the page can read and exfiltrate the token. The CSP restricts
`script-src` to `'self'`, which blocks external script loads, but stored
content rendered unsanitized (community posts, AI output, course content)
would be the delivery path. Default token lifetime is 168 hours
(`JWT_EXPIRE_HOURS`) — a long theft window.
*Why it matters:* token theft = full account takeover, including admin/exec
sessions if an operator's browser is compromised.

**H2 — CORS defaults to wildcard in production.**
`allow_origins` comes from `CORS_ORIGINS` with a default of `'*'`
(`server.py` ~10418–10435). The code correctly disables
`allow_credentials` under wildcard (bearer auth survives), but wildcard still
means any website may make authenticated reads **if** it can obtain a token,
and it defeats origin-based abuse signals. `BACKUP_ORIGIN` is auto-appended.
*Fix direction:* pin `CORS_ORIGINS` to the real domains on Railway; keep the
`*` fallback only for local dev.

**H3 — Rate limiting is per-process and trusts the raw socket IP.**
`_RATE` is an in-memory dict with an asyncio lock (`server.py` ~300–320) —
fine for a single process, but it resets on restart and is silently bypassed
if the app ever runs on multiple workers/instances. Separately, limits keyed
on `request.client.host` (e.g. `ai_helper:ip:{ip}`, forgot/reset) see the
reverse-proxy address when the app sits behind Railway's proxy unless
forwarded headers are trusted — which would make per-IP limits either
"everyone shares one bucket" or spoofable. There is also no per-IP cap on
`/auth/login` across different emails (only 5/min **per email**), leaving
credential-stuffing headroom.
*Fix direction:* proxy-headers trust + external counter store behind the
existing `check_rate(key, max_calls, window_sec)` signature so no handler
changes; add per-IP login throttling.

**H4 — No second factor on privileged roles.**
Admin/exec (ranks 6–7) operate the most sensitive surface — RBAC matrix,
feature toggles, restore/rollback, personas console, financial admin — behind
a single long-lived JWT. One stolen token or one compromised workstation
grants all of it. The platform already has session revocation
(`token_version`) and a recovery path, so adding a step-up does not require
building identity infrastructure from scratch.

### Medium

**M1 — Encryption secret can live beside the ciphertext.**
`keyvault.py` resolves `PROVIDER_KEY_ENCRYPTION_SECRET` → a **self-generated
secret persisted in `platform_config` inside the same MongoDB** that holds the
encrypted BYOK/provider keys → ephemeral in-memory. The DB-stored option means
a full database compromise also yields the decryption key for the keys stored
in that same database. (Ephemeral mode, by contrast, is safe but loses keys on
restart.) *Fix direction:* set a strong `PROVIDER_KEY_ENCRYPTION_SECRET` in the
Railway secret store, then migrate DB-stored secrets out; document rotation.

**M2 — `byok.decrypt_key` fails open to garbage.**
When Fernet decryption fails, `decrypt_key` returns the ciphertext itself
("already plaintext or decryption failed"), and `resolve_byok`/the shared
support pool would then hand that string to a provider as a bearer token.
Legacy plaintext rows would be returned the same way. *Fix direction:* return
`None` on decrypt failure, log, and skip the key; add a scan for any plaintext
key rows in `db.user_byok_keys`.

**M3 — `legal_compliance.is_human_officer` has a broken guard.**
The final line returns true for **any** authenticated role:
`return (role in roles) or bool(role)` — the `roles` allow-list is bypassed.
Today it is latent (no router calls it; `abo.py`/`sentinel.py` use only
`human_authorization_meta`, which is audit metadata, on top of their own rank
checks), so enforcement is not currently weakened — but any future caller that
uses it as a gate would authorize broadly. *Fix direction:* correct the
predicate or delete it; add a test asserting the intended semantics.

**M4 — Audit failures are silently swallowed on binding actions.**
`routers/abo.py` wraps every `audit(...)` in `try/except Exception: pass` for
financial-ledger actions (config changes, deal create/update). A failing audit
store means binding actions proceed with no trail. *Fix direction:* log audit
failures loudly and decide per action class whether to fail closed; add a
health check on the audit collection.

**M5 — Session surface is smaller than it could be.**
Session rows (`db.auth_sessions`) are written for cross-site logins only;
normal logins get a JWT with a `session_id` claim but no user-visible session
list/termination UI beyond whole-account `token_version` revocation. Default
7-day tokens with no renewal sliding window make revocation the only lever.
*Fix direction:* record sessions for all logins → "sessions" page + per-session
revoke; consider shorter access tokens with refresh.

**M6 — Upload surface is broad and unevenly hardened.**
Twelve routers import `UploadFile` (admin, ai, auditor, band, chat, commerce,
creator, creator_lounge, exec_control, jamil, …). Only the director upload was
verified to have a size cap, filename sanitization, and TTL. Each of the others
needs the same treatment audited: size cap, extension/content-type allow-list,
content sniffing, no web-root disk writes, per-user quota, and tests.

**M7 — Mass-assignment hygiene is not systematically enforced.**
Some routers use `ConfigDict(extra="forbid")` on request models; many bind
update payloads as free-form dicts merged into DB `$set`. If any handler
mirrors user-supplied keys (e.g. `role`, `feature_tier`, `byok_enabled`) into
an update, entitlement escalation is possible. *Fix direction:* grep-audit all
`$set` constructions fed by request bodies; assert `extra="forbid"` on models
that carry identity/entitlement fields; regression-test the RBAC matrix paths.

### Low / Operations

**O1 — Secret inventory and rotation.** Set/verify in the Railway secret
store: strong persistent `JWT_SECRET`, strong
`PROVIDER_KEY_ENCRYPTION_SECRET`, explicit `CORS_ORIGINS`,
`EXEC_ADMIN_EMAIL`, `CROSS_SITE_SECRET` (only if partner SSO is desired),
payment and AI provider keys. Never print values; verify presence only.
**O2 — Dependency vulnerability scans.** `pip-audit` on
`backend/requirements.txt` and `npm audit` in `frontend/` on a schedule;
pin transitive deps that matter.
**O3 — Secrets-in-logs discipline.** Audit-log redaction exists for known PII
keys; extend the same rule to headers/query strings that might carry tokens or
keys; grep the codebase for logging of raw `Authorization`/API keys.
**O4 — Repository hygiene.** Confirm `Noisy Assets/` and archives stay
git-ignored and uncommitted (per `AGENTS.md`); run a historical-secret scan
(trufflehog/gitleaks) before any public push of history.
**O5 — Backup and failover drills.** MongoDB backup/restore plus the
keyvault secret (so encrypted keys survive restore); exercise the documented
primary → backup → emergency failover (`emergency_panel.py`).
**O6 — Critical-action alerting.** The Slack webhook setting exists; wire
exec-class actions (role changes, RBAC writes, rollback, persona toggles) to
it so the owner sees them outside the audit DB.
**O7 — Immutable audit trail.** Verify nothing can delete/overwrite
`audit_log` rows through any API (append-only enforcement + restricted
collection access at the DB level).

---

## 3. Improvement pass (what changed between first draft and this plan)

The plan was revised against the code before being written down:

1. **Claims were converted to evidence.** Every "risk" was traced to a file
   and line, and every "already good" was verified — several candidate alarms
   were dropped because the code already handles them (partner-role trust,
   plaintext key saves, upload path traversal on the reference handler,
   deactivated-account enforcement, invalid-token rejection).
2. **The `is_human_officer` bug was reclassified.** Initial read suggested an
   active authorization hole; closer inspection showed it is currently dead
   code used only for audit metadata, so it is **Medium/latent**, not a live
   exploit — the plan says fix or delete with a test rather than treating it
   as an incident.
3. **Non-issues were explicitly listed** (Section 1) so no one "hardens" them
   and breaks working behavior — e.g. the wildcard-CORS credential
   auto-disable is deliberate, cross-site role pinning is correct, BYOK
   refuse-to-save is correct.
4. **Everything ships as a superset with a rollback.** No recommendation
   removes a capability; each change is staged, tested against the existing
   44-test backend suite plus the live probe matrix, and reversible (flag
   off / env revert / code revert).

---

## 4. Phased execution plan (no code changed yet — proposed order)

Each phase lists: change, blast radius, why it cannot break existing behavior,
verification, rollback.

### Phase 0 — Baseline (no behavior change)
- Freeze the current live route probe matrix (`PUBLIC_READINESS_REPORT.md`
  Update 2) and the 44 passing backend tests as the regression gate.
- Record current Railway env **key presence** (not values) for O1.
- Gate: nothing changes; evidence snapshot is committed for later comparison.

### Phase 1 — Configuration hardening (env-only, reversible)
- H2: set `CORS_ORIGINS` to the real domains on Railway (keep `*` for local
  dev only).
- H3 (part 1): enable proxy-headers trust so `request.client.host` is the real
  visitor IP behind Railway; verify via a live probe from two distinct IPs.
- M1: set a strong `PROVIDER_KEY_ENCRYPTION_SECRET`; confirm `keyvault.source()`
  reports `env`; plan the DB-secret migration.
- Rollback: unset the env var(s) and redeploy — behavior returns to today's
  default. Verification: live `/api/health`, readiness, and the auth-guard
  probes stay green; one real browser session each for a visitor, a member,
  and admin flow.

### Phase 2 — Auth/session architecture (flagged, dual-path)
- H1/H4/M5: introduce httpOnly `SameSite=Lax` session cookie for new sessions
  while the bearer-token path remains active behind a feature flag; record
  every login in `db.auth_sessions`; add per-session revoke and a "sessions"
  page for the account owner; add step-up re-auth (TOTP or password) for
  rank ≥ 6 sensitive actions.
- Rollback: flip the flag off — bearer path is untouched and continues to
  work. Verification: full register → sign-in → paid-tier → exec flows in a
  staging preview before production; automated auth regression suite.

### Phase 3 — Authorization audit pass (tests-first, code after)
- H3 remainder, M6, M7: inventory every route that writes to the DB from a
  request body; assert rank gates and `extra="forbid"`; harden each upload
  endpoint to the director-upload standard; write regression tests that **fail
  on today's code** and pass after the fix (red/green per `AGENTS.md`).
- M2, M3, M4: fail-closed `decrypt_key` (returns `None`, logs, skips) with a
  plaintext-row scan; correct or delete `is_human_officer`; make audit
  failures loud on binding actions.
- Rollback: revert the offending commit — each change is isolated so a single
  revert restores the prior behavior. Verification: 44+ new tests green +
  live probe matrix green + one real end-to-end purchase remains the launch
  gate (unchanged).

### Phase 4 — Detection and hygiene (ongoing)
- H4 final state, O2–O7: dependency scans in CI, secrets-in-history scan,
  exec-action Slack alerts, append-only audit verification, backup/failover
  drills, periodic re-run of the live probe matrix.
- Rollback: n/a (detection only). Verification: scheduled report output.

---

## 5. Explicit non-goals (so scope stays honest)

- No third-party security vendor or new paid service is proposed.
- No change to the funding model: customers still never receive
  platform-funded AI; BYOK and KB fallback behavior is preserved exactly.
- No change to the role/tier ladder, the FCC registry, or access semantics —
  only to *how* identity is carried and verified.
- No Anthropic enablement, no new providers, no credential handling changes
  outside the approved secret store.
- Nothing in this plan is "done" until it has the same evidence standard as
  the readiness work: automated proof plus a live owner-visible demonstration
  where behavior is affected.

---

## 6. Source-of-truth map

- Access/AI-funding policy: `BUSINESS_ACCESS_POLICY.md`, `AGENTS.md`
- System behavior as built: `MOREHELP_SYSTEM_MANUAL.md` (§10 technical appendix)
- Live route status: `PUBLIC_READINESS_REPORT.md` (Update 2, 2026-09-03)
- Canonical role/tier code: `backend/roles.py`, `backend/security/feature_control.py`
- This plan's evidence lines: `backend/server.py` (CORS ~10418, rate store ~300,
  headers ~267, auth ~750), `backend/keyvault.py`, `backend/byok.py`,
  `backend/legal_compliance.py`, `backend/cross_site_auth.py`,
  `backend/routers/auth.py`, `backend/routers/byok.py`, `backend/routers/abo.py`,
  `frontend/src/lib/api.js`, `frontend/src/lib/auth.jsx`
