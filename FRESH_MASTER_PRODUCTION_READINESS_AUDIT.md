# FRESH MASTER PRODUCTION READINESS AUDIT

**Date:** 2026-08-23 · **Method:** ground-up, this session only. Every claim below was produced by a command run or a file read performed during this audit. No previous phase report, test result, or document was used as evidence. No code was modified.

## EVIDENCE CLASSES (used throughout)

- **VERIFIED** — demonstrated from current source/runtime this session (file:line or live request).
- **FAILED** — demonstrated broken.
- **PARTIAL** — some of the required path works, the complete requirement does not.
- **BLOCKED** — cannot be verified because a live dependency/environment is unavailable (MongoDB, provider keys, Railway, browser — all unavailable in this sandbox).
- **UNKNOWN** — insufficient evidence in code to establish behavior.

Environment facts (apply to every BLOCKED): no MongoDB (`MONGO_URL` unset; server boots in no-DB mode), no provider API keys, no Railway access, no browser tooling. Stated once; not repeated per item.

---

## EXECUTIVE SUMMARY

The platform is a coherent, real implementation at the code level: bcrypt + JWT-with-revocation auth, rank-based RBAC, a signed payment webhook, a tier-first nav driven by a feature registry, bounded public AI, GDPR export/delete endpoints, and disabled-by-default API docs. Fresh runtime probes confirm 401s on admin/exec/payment/BYOK endpoints without auth, an exec-only Arena, and a correct 60-key gate map — all independent of any prior report.

However, the audit also confirms, with fresh evidence, several **real defects** (not environment limitations): (1) payment webhooks handle `order_created` only — cancellations/refunds never revoke entitlements; (2) the $3 BYOK entitlement can be activated without payment; (3) three separate tier maps disagree (Studio: Member in nav, Plus at API/page); (4) stored media is served inline with a client-supplied content type (HTML/SVG stored-XSS vector); (5) cross-site SSO propagates role elevation from a partner site; (6) the SPA catch-all returns 200 HTML for unknown `/api/*` paths. Plus an entirely unverified production surface (DB, providers, payments, browser).

**VERDICT: CONDITIONAL LAUNCH** — conditions are the P0 list in §18. If P0-1 (payment lifecycle) or P0-2 (production verification) cannot be met, the verdict is NO.

---

## CRITICAL LAUNCH BLOCKERS (P0)

1. **P0 — Payment entitlement lifecycle is one-way.** Webhook handles `order_created` only (VERIFIED, `routers/payments.py:212-367`). `subscription_cancelled`, `subscription_updated`, `refunded` events are ignored → a cancelled/refunded subscriber keeps `feature_tier` indefinitely. **Repro:** cancel a subscription in Lemon Squeezy; observe no webhook handler, no tier change.
2. **P0 — Production is entirely unverified.** No MongoDB, no provider keys, no Railway, no browser in this environment. Nothing about production DB behavior, provider connectivity, checkout, or UI is demonstrated (BLOCKED, all of it).
3. **P0 — Bootstrap privilege on a fresh instance.** First user on an empty DB is created as `executive_admin` (VERIFIED, `routers/auth.py` register handler). A campaign hitting an unseeded DB hands the owner role to the first registrant.
4. **P0 — No campaign-funnel verification.** Landing → register → login → dashboard and a real $3 checkout have never been exercised (BLOCKED).

---

## 1. SECURITY FINDINGS

### Verified controls (VERIFIED)
- Passwords: bcrypt via passlib (`server.py:197,597-602`).
- JWT: HS256, default 168 h expiry, `token_version` in payload; stale `tv` rejected; missing/invalid token → 401 (`server.py:789-826`).
- `is_active` enforced: `403 "Account deactivated"` in the auth path (`server.py:817`).
- Rank-based RBAC: `_require_rank(*roles)` resolves min-rank and 403s below it; `_dep_current_user` delegates to the real `current_user` (no parallel auth implementation) (VERIFIED, `routers/ai.py:287-306`).
- Admin user mutations: `_require_rank("admin")` + `can_modify` (actor rank ≥ target rank; admins cannot touch exec accounts) + self-demotion refusal (`routers/users.py:164-227`, `server.py:872`).
- Live probes (VERIFIED, this session): no-auth → 401 on `/api/admin/stats`, `/api/exec/site-report`, `/api/payments/checkout`, `/api/byok/activate`, `/api/jamil/chat`; all real `/api/competition/*` endpoints 401 without auth.
- Rate limits: in-memory sliding window → 429 (register 5/min, helper 15/min, ai_chat 20/min, ai_tool_chat 15/min) (VERIFIED, `server.py:357-364`, `routers/ai.py`).
- Audit log PII redaction (`_PII_KEYS` → `[REDACTED]`) (VERIFIED, `server.py`).
- Webhook HMAC-SHA256 verified with `compare_digest`; unconfigured → 404 (VERIFIED, `routers/payments.py:227-234`).
- Security-headers middleware; CORS env-configurable with credentials disabled for `*` (VERIFIED).
- API docs: **disabled** — `/api/openapi.json` returns the SPA HTML fallback, not JSON (VERIFIED live; the 200s are the frontend catch-all).
- IP-whitelist middleware for exec paths, open mode when collection empty (VERIFIED, `server.py:285-300`).

### Findings
- **S1 (P2) — Stored media served inline with client-controlled content type.** Upload accepts any `content_type` (50 MB cap only) and serves it via `StreamingResponse(media_type=metadata.get("content_type"))` with **no Content-Disposition: attachment** and no CSP on the file response (VERIFIED, `routers/media.py:204-248, 263-270`). An authenticated user can upload a file declaring `text/html` or `image/svg+xml`; it is served from the API origin. Store-XSS/HTML-injection vector if any surface renders it in a document/iframe context.
- **S2 (P2) — Cross-site SSO trusts partner role claims.** `/api/auth/cross-site-login` (public) validates a token signed with `CROSS_SITE_SECRET`, then **raises the local user's role if the token claims a higher one** and **auto-creates users** (VERIFIED, `routers/auth.py:1024-1060`; `cross_site_auth.py`). Both sites also share `JWT_SECRET`. If the partner's token path or either secret is compromised, role elevation here follows. Tokens are single-use, 5-min TTL — mitigates but does not remove the trust dependency.
- **S3 (P2) — SPA catch-all returns 200 HTML for unknown API paths.** `/api/nonexistent-xyz` → `200 text/html` (VERIFIED live). Masks 404s; monitoring/API-surface confusion; any future API typo returns HTML, and the docs URLs look "open" (200) while actually returning HTML.
- **S4 (P2) — In-memory rate limiter is per-process** (VERIFIED, `server.py` `_RATE` dict). Multi-worker deploys reset limits per worker.
- **S5 (P2/P3) — SSRF surface is admin/exec-controlled only.** Bridge webhook URL (admin-configured) and provider `base_url` (exec-managed) drive outbound requests (VERIFIED, `routers/bridge.py:507`, `routers/billing.py:335-342`) — acceptable, document.
- **S6 (P3) — `file_url` on media products is client-set and unvalidated**; can point to external URLs (VERIFIED, `routers/media.py:109`).
- **Untested (not claimed):** no IDOR sweep beyond spot checks, no injection/XSS/CSRF testing, no penetration testing, no live security testing (BLOCKED).

## 2. ACCESS-CONTROL FINDINGS (FCC chain, traced fresh)

**Chain (VERIFIED end-to-end with fresh reads/live probes):**
`FEATURE_REGISTRY` (`routers/features.py`, 48 features) → FCC saves to `db.feature_configs` → middleware `enforce_platform_flags` → `check_user_feature_access` (`security/feature_control.py:277`) applies: per-user overrides → AI access override → FCC config (enabled, internal_only, override roles/tiers) → `FEATURE_MIN_TIER` matrix → decision (allow/block/unavailable). Parallel: gate map `ec_access_public` merges registry + FCC overrides → frontend `navAccess.isNavItemVisible` (nav). Endpoint-level: `_require_rank` / `current_user`.

- Middleware-governed API surfaces (VERIFIED, `security/feature_control.py:63-105`): ai_chat (`/api/ai/`), courses (`/api/modules|progress|labs|credentials`), studio, band, lounge, earnings, payouts, publisher, tracks, posts (`/api/more/`), sovereign, publisher_ai, profile; FCC: jamil, arena (`/api/competition/`), orchestrator, helper, council (sage), chat (`/api/nam`), site_guide.
- **Middleware runs before handlers** → authorization precedes provider invocation on these surfaces (VERIFIED, `server.py:216-285`).
- Fail-closed: mapped-surface DB error → 503 (VERIFIED source); unknown feature → treated as unavailable policy store.
- **Gap (PARTIAL): FCC `allowed_tiers` binds only when an admin explicitly overrides tiers (`_override_tiers`)**; registry `default_tiers` are NOT enforced at the API layer by the middleware — the `FEATURE_MIN_TIER` matrix is a separate map. Changing a tier in the FCC changes nav (gate map) but not API enforcement unless the matrix also matches (VERIFIED, `feature_control.py` step 3 vs step 4).
- **Gap (PARTIAL): endpoints outside the middleware map** (payments, byok, media, most admin/exec) are governed only by endpoint-level auth — FCC toggles do not reach them (VERIFIED, path-map + probe results).
- Live: gate map verified with 60 keys incl. arena exec-only, jamil admin+, public store (VERIFIED live).
- FCC tests 16/16, integration 42/42 re-run fresh this session (VERIFIED TEST).

## 3. TIER FINDINGS

- Real ladder (VERIFIED): `free(0), member(1), plus(2), pro(3), patron(4), executive(5)` — identical in `security/feature_control.py`, `routers/payments.py`, frontend `src/lib/tiers.js`.
- **Three tier maps disagree (VERIFIED):**
  1. Registry `default_tiers` → nav gate map. `create.studio` = member+ (gate-map payload shows `allowed_tiers: ["member","plus","pro","patron"]` — VERIFIED live).
  2. `FEATURE_MIN_TIER` → API enforcement. `studio` = **plus** (VERIFIED, `feature_control.py:193-208`).
  3. Frontend `TIER_FOR_FEATURE` → in-page `TierGate`. `studio` = **plus** (VERIFIED, `frontend/src/lib/tiers.js`).
  **Consequence (PARTIAL/FAILED by requirement):** a Member sees Creator Studio in nav but the page and API require Plus. A Plus customer is fine; Member is misled. Same pattern applies to other member-vs-plus surfaces.
- Payments grant tiers **upgrade-only** (never downgrade) (VERIFIED, `routers/payments.py`).
- Tier enforcement in the middleware requires a valid session; anonymous users bypass the tier step by design (public surfaces only) (VERIFIED).

## 4. ROLE / STAFF FINDINGS

- Real roles (VERIFIED, `roles.py`): `student(1), trial_pass(2), instructor(3), support_staff(4), oversight(5), admin(6), executive_admin(7)`, `public(0)`; legacy map normalizes old strings; unknown → `student` (least privilege).
- Role ≠ tier: separate User fields; enforced independently (VERIFIED).
- Staff BYOK: `FREE_BYOK_ROLES` = instructor+ (VERIFIED).
- **Staff cannot touch exec accounts** (`can_modify`), exec can modify exec (VERIFIED).
- Shared staff pool: `_SHARED_BYOK_POOL` used after platform free providers fail, before KB fallback; in-memory; provider-priority (VERIFIED, `ai/llm_gateway.py`). **Gaps (VERIFIED source, unchanged):** no per-member attribution of pool use; no explicit "shared pool used" audit event; if `PROVIDER_KEY_ENCRYPTION_SECRET` is absent, encrypted keys cannot be decrypted (behavior: feature disabled or plaintext risk — code path for missing secret is failure, not plaintext, per gateway load logic; the risk is operational).
- **Customer/staff separation:** role sections in nav are role-gated (VERIFIED, `AppShell.jsx` + nav tests); backend rank checks are the enforcement.

## 5. BYOK FINDINGS

Chain: `POST /api/byok/checkout` (free for instructor+, else $3 via payments) → webhook flips `byok_enabled` → `/api/byok/key` stores Fernet-encrypted key in `user_byok_keys` → gateway resolves user key FIRST → provider call.

- **B1 (P1) — BYOK can be activated without payment (VERIFIED, `routers/byok.py:79-131`).**
  - `POST /api/byok/activate` flips `byok_enabled` for ANY authenticated user with no payment/entitlement check (comment says "post-payment hook" but nothing enforces that).
  - `POST /api/byok/checkout` has a **grace path**: when `PAYMENTS_ENABLED` is false OR checkout raises, it calls `activate_byok` directly and returns `activated: true, grace: true`. In production with payments unconfigured or failing, every registered user gets the $3 unlock free.
  - **Repro:** register a user, `POST /api/byok/activate` with a valid token → `byok_enabled: true`, no payment. (401 without token — auth present.)
- Encryption: Fernet with `PROVIDER_KEY_ENCRYPTION_SECRET`; keys never returned raw (status/masked only) (VERIFIED).
- **B2 (PARTIAL) — BYOK silently becomes platform-funded?** No: gateway uses user BYOK first; platform keys only when no BYOK key (VERIFIED). The reverse risk is real: **platform-funded fallback happens only when the user has no key** — but a feature configured `byok_allowed=false` still runs on the user's key (gateway does not consult `byok_allowed`) (VERIFIED, `ai/llm_gateway.py` BYOK resolution precedes provider chain). Saves money; violates declared funding policy.
- Expired/cancelled entitlement: no expiry field on `byok_enabled` observed (UNKNOWN whether any revoke path exists besides admin DB edit).

## 6. AI / PROVIDER / COST FINDINGS

- Entry points (VERIFIED): `/api/ai/chat` (20/min, auth), `/api/ai/helper` (auth + anon via `/helper/ask`), `/api/ai/sage` (council), `/api/ai/orchestrator` (admin+), `/api/jamil/*` (admin+), `/api/nam`, `/api/site-guide`, `/api/ai/social-blast`, plus bounded anon `/api/public/helper/ask` + `/api/helper/ask` (15/min, IP-budgeted, KB-first — VERIFIED live: both return 200 without auth).
- Providers (VERIFIED, `ai/llm_gateway.py` health block): groq, cerebras, sambanova, gemini, grok, cohere, mistral, together, openrouter, huggingface (availability = key present), anthropic (OFF by directive), kb_fallback (zero), byok_shared.
- Budget: `HOURLY_TOKEN_CAP` default 200k global; per-user daily cap; anonymous `ip:` budget key (VERIFIED).
- Authorization-before-invocation: middleware + rate limits run before handlers on mapped AI paths (VERIFIED).
- **A1 (PARTIAL) — anonymous platform-funded AI exists** via the two helper endpoints (KB-first, bounded, IP-limited — the deliberate teaser; tokens are platform-funded on KB miss, within the IP budget). Disposition is an executive decision; not changed.
- **A2 (PARTIAL) — no per-feature quotas**; global caps only (VERIFIED). No per-feature `platform_ai` enforcement in the gateway (the flag exists in the registry/FCC but the gateway does not read it before spending) (VERIFIED).
- **A3 (BLOCKED) — provider connectivity unverified**; no keys in sandbox. `/api/admin/health` exists to check in production.

## 7. ECOMMERCE / PAYMENT FINDINGS

- Provider: Lemon Squeezy primary, Gumroad fallback (one-time); Stripe removed (VERIFIED, `routers/payments.py:36-42`).
- Products/pricing server-side (VERIFIED): member $9, plus $15, pro $29, patron $59, more $9.99/$79.99, BYOK $3, sanctuary trial $3, donation, scholarship, arena products, credential $25 (physical → 501 by design).
- **E1 (P0) — no cancellation/refund handling** (see Critical Blockers). Webhook = `order_created` only (VERIFIED).
- **E2 (P1) — no webhook idempotency.** Duplicate deliveries insert duplicate `payments` rows (tier grant is upgrade-only → tier damage limited) (VERIFIED).
- **E3 (P1) — BYOK free activation** (see B1).
- **E4 (P2) — unregistered buyer linkage.** Webhook stores `user_id: None`; entitlement grants happen only when the buyer's email matches a registered user (VERIFIED). A buyer who hasn't registered pays and receives nothing until they register.
- **E5 (VERIFIED) — server-side price integrity.** Media checkout and product checkout use stored server-side amounts; client cannot set price (VERIFIED, `routers/payments.py`, `routers/media.py:152-190`).
- Upgrade-only grants; sanctuary trial timeboxed 3d33m33s with revert (VERIFIED).
- **E6 (BLOCKED) — no money moved in this environment; no automated payment/webhook tests exist** (VERIFIED: no payment/webhook/refund test files in `tests/`).

## 8. HUMAN OVERSIGHT FINDINGS

- Incident reporting/triage/resolution: any-authed report, instructor+ list, admin resolve (VERIFIED, `routers/ops.py:241-277`).
- Moderation: log + stats endpoints (VERIFIED, `routers/community.py:443-457`); admin course moderation (VERIFIED).
- Audit: PII-redacted `audit_log`; auditor ledger/summary/report/debt; exec site-report (VERIFIED).
- Broadcast + notifications (VERIFIED).
- **PARTIAL/UNKNOWN:** no runbook/escalation policy/incident-response procedure found in code; moderation workflow not end-to-end verified; whether a human actually watches the moderation queue is an operational question, not code.

## 9. PUBLIC-READINESS FINDINGS

- 44+ public routes verified in `App.js` (VERIFIED, route list this session).
- No public dashboard; public nav = Explore (Courses/Creators/Community/Store/Help) + Sign In/Register (VERIFIED).
- **Route integrity: 161 routes, 428 link candidates — all resolve** (VERIFIED TEST, repo's own script).
- Public AI = the two bounded helper endpoints (VERIFIED live, 200 no-auth; bounded in source).
- SEO: robots.txt, sitemap.xml, description/OG meta present (VERIFIED).
- No placeholder markers in `src/` (VERIFIED scan).
- **PARTIAL:** `/trash` ("M.O.R.E. Pantheon") and `/supervisor-login` are public routes whose purpose is unclear to a visitor; landing/visual quality is BROWSER-BLOCKED.

## 10. NAVIGATION FINDINGS

- Tier-first nav verified: anonymous → no dashboard; free hides member+ items; Create at Member; Council/Sanctuary/Adaptive at Plus; Arena + Command Center exec-only; BYOK as state (VERIFIED TEST — nav-integrity suite passed fresh this session; source read of `AppShell.jsx`).
- **Nav vs access mismatch (VERIFIED):** Studio appears at Member in nav but requires Plus at page/API (tier-map disagreement). Nav is presentation; the backend gate is what actually blocks — so a Member sees a dead-end link (nav says yes, API says 403). Direction: nav over-promises, backend under-delivers → confusing, not insecure.
- BROWSER-BLOCKED: rendered layout, mobile, hover states.

## 11. COMPLIANCE / OPERATIONAL FINDINGS

- Terms (126 lines) + Privacy (**45 lines**) public pages; cookie consent + `/consent/cookie`; registration requires terms + over-13 consent; `terms_accepted_at` recorded; account delete + data export; erasure test exists (VERIFIED).
- **PARTIAL:** Privacy is thin for payments/AI/BYOK/data handling; **refund policy text not found** on public pages; no acceptable-use/moderation policy text, creator/marketplace terms, AI-generated-content disclosure, accessibility statement found (VERIFIED scan). No legal review has occurred (BLOCKED — no lawyer).
- Retention/deletion: GDPR delete/export endpoints exist; full retention policy not found (UNKNOWN).

## 12. REAL FUNCTIONALITY FINDINGS

- **VERIFIED TEST (fresh this session):** FCC 16/16, integration 42/42; nav-integrity pass; route-integrity pass; live gate map correct; 401s on protected endpoints without auth.
- **FAILED by requirement (code-level):** cancellation/refund revocation (E1); BYOK payment gate (B1); tier-map consistency (studio member vs plus).
- **BLOCKED (require live env):** DB persistence, provider calls, checkout money flow, browser journeys, email delivery, webhook delivery.
- Dead buttons/routes: none found via route-integrity; dead links to **nowhere** do not exist in the link graph (VERIFIED TEST). "Placeholder/mocked" functionality: none flagged in source scans; the BYOK grace path is the only documented dev-mode behavior that also runs in production (B1).

## 13. PRODUCTION / DEPLOYMENT FINDINGS

- Startup: JWT_SECRET missing → **fatal** (fail-closed) (VERIFIED, `server.py:168-179`). No-DB mode boots and serves the gate map from registry data (VERIFIED live).
- Background tasks at startup: team monitor, failover watchdog, GDPR purge cron, memory-consolidation cron, rate-limiter cleanup (VERIFIED, startup log this session).
- Health/version endpoints live and OK (VERIFIED).
- ~100 env vars referenced (VERIFIED scan). Critical: `MONGO_URL`, `JWT_SECRET`, `LEMON_SQUEEZY_API_KEY/STORE_ID/WEBHOOK_SECRET`, `GUMROAD_API_KEY`, `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`, `ENCRYPTION_KEY`, `CORS_ORIGINS`, `FRONTEND_URL`, `HOURLY_TOKEN_CAP`, `USER_DAILY_TOKEN_CAP`, `SLACK_WEBHOOK_URL`, `EXEC_RESET_SECRET`, provider keys (10+), email (RESEND or SMTP). Stale: `STRIPE_SECRET_KEY` (VERIFIED).
- Migrations: `seed_modules`, `seed_users` (cohort→associate), `backfill_verification_codes` at startup (VERIFIED) — automatic on boot.
- **BLOCKED:** no production env, no Railway, no deploy verification, no monitoring/backup verification.

## 14. MISSING ENVIRONMENT / DEPENDENCY REQUIREMENTS

Not present in this sandbox; required in production (each BLOCKED): MongoDB + `DB_NAME`; `JWT_SECRET`; Lemon Squeezy API key/store/webhook secret or Gumroad key; `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`, `ENCRYPTION_KEY`; `CORS_ORIGINS`, `FRONTEND_URL`; ≥1 free provider key; `HOURLY_TOKEN_CAP`/`USER_DAILY_TOKEN_CAP`; `SLACK_WEBHOOK_URL`; `EXEC_RESET_SECRET`; email delivery vars. Also: a browser (for funnel verification) and a human (for moderation/incident response).

## 15. EXACT REPRODUCTION / EVIDENCE FOR EVERY FAILURE

- **E1 (P0):** `grep -n "event_name" routers/payments.py` → only `order_created` branch; no `subscription_cancelled|refunded|subscription_updated` anywhere in the handler.
- **B1 (P0/P1):** `routers/byok.py:87-92` — `byok_activate` flips entitlement with no payment check; `routers/byok.py:124-131` — checkout grace path calls `activate_byok` when payments unconfigured/failing. Live: `POST /api/byok/activate` → 401 without token (auth present), but with any valid user token it grants.
- **Tier mismatch:** gate-map live payload `studio → allowed_tiers: [member, plus, pro, patron]`; `FEATURE_MIN_TIER["studio"] = "plus"`; `frontend/src/lib/tiers.js TIER_FOR_FEATURE.studio = "plus"`.
- **S1 (media XSS):** `routers/media.py:263-270` — `StreamingResponse(media_type=metadata.get("content_type"))`, no `Content-Disposition`; upload stores client `content_type` (`media.py:204-248`).
- **S2 (SSO role elevation):** `routers/auth.py:1043-1050` — `if role_rank(role) > role_rank(existing_role): update_one(role)`; auto-create for unknown email.
- **S3 (SPA swallow):** `curl /api/nonexistent-xyz` → `200 text/html` (live).
- **Docs disabled:** `curl /api/openapi.json` → HTML (live), `server.py:199-209` (`docs_url=None` unless `ENABLE_API_DOCS=1`).

## 16. SEVERITY SUMMARY

| ID | Finding | Severity |
|---|---|---|
| E1 | No cancellation/refund webhook handling → entitlements persist | **P0** |
| — | Production entirely unverified (DB/providers/payments/browser) | **P0** |
| — | First-registrant-becomes-executive_admin on fresh DB | **P0** |
| — | No campaign-funnel verification | **P0** |
| B1 | BYOK free activation (direct activate + grace path) | P1 |
| — | Tier maps disagree (Studio member vs plus; others) | P1 |
| E2 | Webhook idempotency | P1 |
| — | Privacy 45 lines; refund policy text missing | P1 |
| — | Anonymous helper disposition (executive decision) | P1 (decision) |
| S1 | Stored media inline serving, client content type | P2 |
| S2 | Cross-site SSO role elevation trust | P2 |
| S3 | SPA catch-all masks API 404s | P2 |
| S4 | Per-process rate limiter (multi-worker) | P2 |
| E4 | Unregistered buyer linkage | P2 |
| A2 | No per-feature AI quotas; gateway ignores platform_ai/byok_allowed | P2 |
| — | Shared-pool attribution/audit event | P2 |
| S6 / E5-stale | file_url unvalidated; STRIPE_SECRET_KEY stale env | P3 |

## 17. LAUNCH TOMORROW?

**CONDITIONAL.**

- **YES on:** code-level integrity (all fresh tests green, no dead links, protected endpoints 401, Arena exec-only, gate map correct, docs disabled, auth primitives sound).
- **NO unless these are met (P0):**
  1. Payment lifecycle: handle `subscription_cancelled`/`refunded` (revoke tier) **or** disable subscription products for the campaign.
  2. Production verification: DB up, `live_fcc_matrix.py` passes against production, `/api/admin/health` shows ≥1 working free provider, a real $3 checkout completes end-to-end.
  3. DB pre-seeded/claimed (no first-registrant-takes-exec).
  4. One manual browser pass of landing → register → login → dashboard + a $3 checkout.
- If 1–3 cannot be completed, the honest verdict is **NO**.

## 18. PRE-LAUNCH REMEDIATION LIST (ordered by risk)

1. Fix webhook to handle cancellation/refund (revoke/rollback entitlement) — or gate subscription products off at launch. (P0)
2. Complete production env + run the live verification matrix + provider health + one real payment. (P0)
3. Seed/claim the production DB before any traffic. (P0)
4. Manual browser funnel pass. (P0)
5. Close the BYOK free-activation path: require a paid order record or admin grant for below-instructor users; remove the grace path in production. (P1)
6. Reconcile tier maps (registry vs `FEATURE_MIN_TIER` vs `TIER_FOR_FEATURE`) — align Studio and every other surface. (P1)
7. Add webhook idempotency; add payment/webhook unit tests. (P1)
8. Legal review of Privacy/Terms; publish refund/cancellation policy text; add AI disclosure. (P1)
9. Serve media with `Content-Disposition: attachment` + content-type allowlist. (P2)
10. Cap cross-site role elevation (e.g., max `student`/`trial_pass` unless pre-registered); document secret-sharing. (P2)
11. Decide the anonymous helper disposition (KEEP/MODIFY/REMOVE). (P1 decision)
12. Per-feature AI quotas + gateway honoring `platform_ai`/`byok_allowed` (CONFIGURATION REQUIRED). (P2)
13. Post-launch: shared-pool attribution/audit, multi-worker rate limiting, media file_url validation, remove stale `STRIPE_SECRET_KEY` reference. (P2/P3)

---

## HONESTY STATEMENT

- VERIFIED means demonstrated this session (source read and/or live request and/or test run). Nothing from any earlier phase was used as evidence.
- BLOCKED items are not passes: no MongoDB, no provider keys, no Railway, no browser in this environment — DB persistence, AI connectivity, money flow, and UI behavior remain unproven.
- No penetration testing, load testing, browser testing, or production testing occurred. No code was modified during this audit.
