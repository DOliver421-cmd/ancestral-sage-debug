# PHASE 20 — FULL PRE-LAUNCH READINESS AUDIT

**Date:** 2026-08-23 · **Method:** direct inspection of source in this session (backend routers, security layer, gateway, byok, payments, frontend routes/pages/tests). No prior report was used as evidence. No code was changed during this audit.

## EVIDENCE-LEVEL LEGEND

| Level | Meaning |
|---|---|
| **SRC** | VERIFIED IN SOURCE (read the code this session) |
| **TEST** | VERIFIED BY AUTOMATED TEST (ran this session) |
| **LIVE** | VERIFIED BY LIVE API (made a real HTTP request this session) |
| **BROWSER** | VERIFIED IN BROWSER (not performed — no browser tooling) |
| **PROD** | VERIFIED IN PRODUCTION (not performed — no Railway access) |
| **BLOCKED** | verification impossible in this environment (reason stated) |
| **UNKNOWN** | not determinable from available evidence |

Environment limits that apply to everything below: **MongoDB is unavailable in the sandbox** (`MONGO_URL not set` → server runs in no-DB mode), **provider API keys are unavailable**, **Railway is not accessible**, **browser E2E tooling is not installed**. These are stated once; every affected claim says BLOCKED rather than passing.

---

## AUDIT 1 — PUBLIC READINESS (SRC)

**Public routes verified in `frontend/src/App.js` (no auth wrapper):** `/` (UnifiedGateway or WAIInstitute), `/login`, `/register`, `/forgot-password`, `/factory-reset`, `/reset-password`, `/helper` (public Helper), `/app/helper` (auth variant), `/plans`, `/help-center`, `/knowledge-base`, `/seshats-hub`, `/more-help-center`, `/classic-tools`, `/classic/:slug`, `/search`, `/site-guide`, `/landing`, `/wai-institute`, `/vonns-saga`, `/supervisor-login`, `/terms`, `/privacy`, `/courses`, `/ascension-protocols`, `/community`, `/creators`, `/modules`, `/modules/:slug`, `/p/:slug`, `/leaderboard`, `/trash-pantheon`, `/internships`, `/store`, `/merch`, `/subscribe`, `/donate`, `/payment/success`, `/payment/cancel`, `/u/:username`, `/trash`, `/welcome`, `/more`, `/more/litigation`.

Findings:
- **No public dashboard** — `/dashboard` is wrapped in `Protected` (SRC). Sidebar hides Dashboard for anonymous (SRC + nav test).
- **No accidental admin links in public navigation** — public nav = Home/Explore (Courses, Creators, Community, Store, Help) + Sign In/Register (SRC, Phase-19 rewrite inspected this session).
- **Dead-link integrity:** ran the repo's own `scripts/route-integrity.js` — **161 routes, 102 registry entries, 428 link candidates, 31 redirects: all resolve, no dead paths** (TEST).
- **Public AI surface exists deliberately:** `POST /api/public/helper/ask` and `POST /api/helper/ask` are both **auth-less**, KB-first, IP-rate-limited (15/min), IP-budgeted, 4000-char capped, prompt-guarded (SRC). LLM tokens are consumed **only when the KB has no match**; on quota exhaustion/degradation the endpoints return a curated KB response, never an unbounded call (SRC). Both endpoints are identical in behavior; the name `/helper/ask` implies auth but requires none (SRC). **Disposition (KEEP / MODIFY / REMOVE) is an executive decision — not changed.**
- **Other public AI:** `/helper` page itself renders a public helper UI (SRC). No other public AI endpoints found in the route scan of `routers/ai.py`.
- **SEO/trust:** `public/robots.txt` and `public/sitemap.xml` exist; `index.html` has description + OG tags pointing at morehelp.center (SRC).
- **Auth pages exist:** login/register/forgot/reset/factory-reset/supervisor-login/cross-site (SRC).
- **Content quality:** `Landing.jsx` 474 lines; strict placeholder scan (`Lorem ipsum`, `TODO: implement`, `under construction`) across `src/` returned **zero matches** (SRC). Visual quality is **BROWSER-BLOCKED** (cannot confirm rendering/mobile).

## AUDIT 2 — REGISTRATION / AUTHENTICATION (SRC)

Verified in `routers/auth.py` + `server.py`:
- Register: rate-limited 5/min per email-prefix; requires `agreed_terms` + `over_13`; role is forced to `student` (schema explicitly rejects client-supplied role/associate); **first user ever on a fresh DB bootstraps as `executive_admin`** (documented intent for factory reset — on a publicly reachable instance the first registrant claims the owner role; must be mitigated before/at launch) (SRC).
- Passwords: bcrypt via passlib (SRC).
- JWT: HS256, `JWT_EXPIRE_HOURS` default **168** (7 days), payload carries `token_version`; `current_user` rejects tokens whose `tv` is older than the stored `token_version` (revocation) (SRC). Sessions tracked in `db.auth_sessions`; listing + revocation endpoints exist (SRC).
- Password reset: forgot → single-use TTL link (admin reset-link also exists); recovery codes; emergency recovery; exec-unlock gated on `EXEC_RESET_SECRET` (disabled when unset — 404); factory-reset endpoint (SRC).
- Account lifecycle: `DELETE /auth/account`, `GET /auth/account/export` (GDPR), `POST /auth/reconsent`, change-password (SRC).
- **Email verification: NOT implemented** — no verify/confirm-email route in auth.py and no `email_verified` field on the User model (SRC).
- Suspended accounts: `is_active` field exists on User; enforcement of `is_active` in `current_user` was not traced to a live check this session (SRC partial — **UNKNOWN**).
- Defaults: new users default `feature_tier="free"`, `byok_enabled=False` (SRC).

## AUDIT 3 — TIER SYSTEM (SRC)

- Real ladder (verified in `security/feature_control.py` + `routers/payments.py`): `free(0) → member(1) → plus(2) → pro(3) → patron(4) → executive(5)`. No invented tiers found anywhere in source (SRC).
- **Three separate tier maps exist and disagree in places:**
  1. Feature Registry `default_tiers` per feature (drives gate-map nav) — e.g. `create.studio` = member+, `learn.adaptive` = plus+ (SRC).
  2. `FEATURE_MIN_TIER` authz matrix in `security/feature_control.py` (drives API tier enforcement step 4) — e.g. `studio` = plus, `courses` = plus, `ai_chat` = free (SRC).
  3. Frontend `src/lib/tiers.js` `TIER_FOR_FEATURE` (drives in-page `TierGate`) — e.g. `studio` = plus, `courses` = plus (SRC).
  Example disagreement: **Creator Studio shows in nav at Member** (registry), **but the API matrix and page gate require Plus**. A Member who sees Studio in nav may be blocked at the page/API. This is a real cross-layer mismatch (P1 to reconcile).
- Tier enforcement chain: FCC `allowed_tiers` binds **only when an admin overrides tiers** (`_override_tiers`); the `FEATURE_MIN_TIER` matrix binds always when a requirement exists; admin/executive bypass tiers (`TIER_EXEMPT_ROLES`), instructors bypass `courses`/`tracks` (SRC).
- Payment grants are **upgrade-only** (never downgrade an active tier) (SRC).
- Definitive per-feature access matrix: see `FEATURE_ACCESS_MATRIX.md`/`CUSTOMER_ACCESS_MATRIX.md` — regenerated from registry data in Phases 17–18; the three-map disagreement above is the headline mismatch.

## AUDIT 4 — ROLE / STAFF SYSTEM (SRC)

- `roles.py` (single source of truth): `student(1), trial_pass(2), instructor(3), support_staff(4), oversight(5), admin(6), executive_admin(7)`, `public(0)` unauthenticated; legacy role map (`priority_member→trial_pass`, `creator→instructor`, `moderator→instructor`, `steward→oversight`, etc.); unknown roles fall back to `student` (least privilege) (SRC).
- `_require_rank` / rank-based 403 enforcement used across routers (SRC).
- **Role ≠ tier:** independent fields on the User model (`role` vs `feature_tier`); FCC checks role and tier separately (SRC).
- Free BYOK for `instructor+` (`FREE_BYOK_ROLES`) (SRC).
- Customer vs staff separation: nav has separate customer/role sections (Phase 19, inspected); backend rank checks are the enforcement (SRC).

## AUDIT 5 — FEATURE CONTROL CENTER (SRC + TEST)

- Registry: 48 features in `routers/features.py`, each with `enabled, internal_only, customer_access_allowed, cost_bearing, public_access, allowed_roles, allowed_tiers, platform_ai, byok_allowed, navigation_visible` (SRC).
- FCC UI exposes: enabled, internal_only, customer_access_allowed, cost_bearing, public_access, platform_ai, byok_allowed, navigation_visible toggles + role/tier matrices (SRC, `FeatureControlCenter.jsx`).
- Enforcement chain (SRC): FCC save → `db.feature_configs` → middleware `check_user_feature_access` (enabled, internal_only, override roles/tiers) + gate map (`ec_access_public`) → frontend nav. `navigation_visible` now reaches the gate map (Phase 19, this session).
- Fail-closed: DB error on a mapped path → 503 rejection; unknown feature → pass-through only if unmapped (SRC + 16/16 FCC tests TEST).
- **Live browser verification of the FCC UI: BLOCKED** (no browser, no DB).

## AUDIT 6 — AI / PROVIDER / COST CONTROL (SRC)

- Gateway (`ai/llm_gateway.py`): **11 providers** (groq, cerebras, sambanova, gemini, grok/xAI, cohere, mistral, together, openrouter, huggingface, anthropic[disabled by directive]) + `kb_fallback` (zero cost) + `byok_shared` pool. Availability = `bool(key)` per provider (SRC).
- Budget: `HOURLY_TOKEN_CAP` default 200k (global), per-user daily cap (`USER_DAILY_TOKEN_CAP`), anonymous fallback budget key (`ip:...`) (SRC).
- Credential priority (SRC): user BYOK first → platform free providers → shared staff pool → KB fallback.
- **Funding-mode gap (confirmed this session, unchanged):** the gateway resolves user BYOK whenever a key exists **without consulting the feature's `byok_allowed` flag** (SRC, byok resolution precedes provider chain). A feature configured `byok_allowed=false` can still silently run on the user's key. Saves platform money, violates declared funding policy. (P1/P2 — executive decision.)
- Access before spend: FCC middleware runs on mapped API paths before handlers; AI routers use `check_rate` + `current_user`; the anonymous helper is bounded (see Audit 1) (SRC).
- **No per-feature AI quotas exist** (global caps only) — marked CONFIGURATION REQUIRED, not invented (SRC).
- API keys never returned to client: BYOK endpoints return masked/status only; gateway uses server-side env keys (SRC).
- Provider connectivity in production: **BLOCKED** (no keys in sandbox). The gateway's health endpoint exposes per-provider `key_set`/`available` (SRC) — run `/api/admin/health` in production to get the real table.

## AUDIT 7 — SECURITY (SRC)

- Auth: bcrypt, JWT HS256 168h, token_version revocation, session records (SRC).
- Webhook: HMAC-SHA256 signature verified against `LEMON_SQUEEZY_WEBHOOK_SECRET` with `compare_digest`; unconfigured → 404 (SRC).
- Rate limits (in-memory sliding window, 429): register 5/min, public helper 15/min, ai_chat 20/min, ai_tool_chat 15/min (SRC). **In-memory limiter = per-process state — multi-worker deploys reset limits per worker** (P2).
- Audit log: PII redaction (`_PII_KEYS` → `[REDACTED]`) (SRC).
- Headers: security-headers middleware present (SRC). CORS: env-configurable, default `*` with `allow_credentials` off (SRC).
- IP whitelist middleware: opt-in, **open mode when collection empty** (SRC).
- API docs: **disabled by default** (`ENABLE_API_DOCS` ≠ 1) (SRC).
- Media: uploads require auth; file serving requires auth with entitlement-aware preview boundary; GridFS (SRC).
- Prompt guard on public AI endpoints (SRC).
- **Untested surfaces (not claimed):** IDOR depth, injection, XSS, CSRF, upload abuse, escalation chains — **no live or penetration testing performed** (BLOCKED). See SECURITY_AUDIT.md.

## AUDIT 8 — ECOMMERCE / MONEY (SRC)

- Provider: **Lemon Squeezy primary, Gumroad fallback (one-time only); Stripe removed by owner decision** (SRC).
- Products verified (`PAYMENT_PRODUCTS`): member $9/mo, plus $15, pro $29, patron $59, more membership $9.99/$79.99, BYOK $3 one-time, sanctuary trial $3 (grants Plus 3d33m33s), donation, scholarship, arena workbooks, credential cert $25 (physical → 501 not sold online by design) (SRC).
- Checkout: `POST /payments/checkout` (auth) → LS checkout URL; audit event; 501 when unconfigured (SRC).
- Webhook: `order_created` handled — BYOK grant, scholarship pledge, **upgrade-only tier grant**, notify + audit (SRC).
- **GAPS (P0/P1):**
  1. **No `subscription_cancelled` / `subscription_updated` / `refunded` event handling** — a cancelled or refunded subscription leaves `feature_tier` granted indefinitely (SRC). This is the highest-risk money-path defect (users receive entitlements they stopped paying for).
  2. **No webhook idempotency** on payment records — duplicate deliveries insert duplicate payment rows (tier grant is upgrade-only, limiting damage) (P1).
  3. **BYOK entitlement can be activated without payment:** `POST /api/byok/activate` flips `byok_enabled` for any authenticated user with no payment check, and `POST /api/byok/checkout` has a documented **grace path** that directly activates when payments are unconfigured or checkout throws (SRC). Staff (instructor+) get it free by design; below-instructor users can bypass the $3. (P1 revenue leak — platform does not pay for their AI, but the price is bypassable.)
  4. Payment records store `user_id: None` at webhook time and match by email later — an unregistered buyer's payment never attaches to an account until they register (SRC; P2 workflow note).
- Billing history: `GET /payments/history`; portal: `GET /payments/portal` → LS customer portal (SRC).
- Refunds: admin cash/site-credit refund routes exist (`routers/billing.py`, `_require_rank("admin")`) (SRC). **Refund policy TEXT on public pages: not found** (see Audit 9).
- **No automated payment/webhook tests exist** (SRC — test directory listing). Payment money-flow is **NOT live-verified** (BLOCKED).

## AUDIT 9 — COMPLIANCE / TRUST (SRC)

- `/terms` (`TermsOfService.jsx`, 126 lines) and `/privacy` (`PrivacyPolicy.jsx`, **45 lines**) exist and are public (SRC). Privacy content is thin for a platform handling accounts, payments, and AI — **REQUIRES LEGAL REVIEW** (P1).
- Cookie consent: component mounted globally; posts to `/consent/cookie` (SRC).
- Account deletion + data export endpoints exist (SRC); a GDPR erasure test exists (`tests/test_erasure.py`) (TEST).
- Age gate: registration requires `over_13` (SRC).
- **Missing/not found this session:** refund policy text on public pages; acceptable-use / content-moderation policy text; creator/publisher terms; marketplace terms; AI-generated-content disclosure; accessibility statement; data-retention description. Marked MISSING/INCOMPLETE — verify before campaign if these are promised anywhere.

## AUDIT 10 — HUMAN OVERSIGHT / OPERATIONS (SRC)

- Admin: `/admin/stats`, `/admin/recent-activity`, `/admin/cohorts`, `/admin/courses` + moderate, user management surface (admin router) (SRC).
- Incidents: `POST /incidents` (any authenticated user reports), list (instructor+), resolve (admin) (SRC).
- Moderation: `/more/admin/moderation-log` + `/more/admin/moderation-stats`; admin course moderation (SRC).
- Finance ops: auditor ledger/summary/report/debt; billing refunds; exec site-report (SRC).
- Emergency: exec-unlock (secret-gated), factory-reset, broadcast notifications (SRC).
- Budget/AI oversight: gateway health endpoint, per-hour cap, budget alert ratio for TTS (SRC).
- **Operational processes (runbooks, SLA, escalation policy, incident response procedure, provider-failure playbook): not found in code** — mark DOCUMENTED-ONLY/MISSING (SRC scan found none; may live outside the repo — UNKNOWN).

## AUDIT 11 — REAL SYSTEM FUNCTIONALITY (workflow status)

| Workflow | Status | Basis |
|---|---|---|
| Landing → Register → Login → Dashboard | YELLOW | routes + auth code SRC; not browser/live-verified |
| Dashboard → Learn → Course → Module | YELLOW | routes SRC; DB BLOCKED |
| Dashboard → AI → eligible AI | YELLOW | gateway SRC; provider BLOCKED |
| Dashboard → BYOK → purchase → key → AI | **ORANGE** | checkout + grace path SRC; payment not verified; free-activation gap |
| Plans → Checkout → Payment → Entitlement | **ORANGE** | checkout/webhook SRC; **no cancel/refund handling**; no live test |
| Creator → Create → Publish | YELLOW | creator router SRC; not verified |
| Store → Product → Checkout → Download | YELLOW | media router SRC (preview-boundary); not verified |
| Community → Post → Moderation | YELLOW | community router SRC; moderation log exists |
| Admin → User → Change Role/Tier | YELLOW | admin router SRC; not verified |
| Admin → Feature Control → Save → Enforcement | YELLOW | FCC tests 16/16 TEST; not browser/DB-verified |
| Executive → Command/Arena | YELLOW | rank-gated SRC; **Arena exec-only enforced** (competition.py `_require_rank`) |
| Anonymous → helper teaser | GREEN (behavior bounded in SRC) | bounded KB-first, IP-limited; not live-tested |

## AUDIT 12 — NAVIGATION / DISCOVERABILITY

- Tier-first sidebar verified in code + `scripts/nav-integrity.js` **all checks passed** this session (TEST): public → no dashboard; free hides member+ items; Create at Member; Council/Sanctuary/Adaptive at Plus; Arena + Command Center exec-only; BYOK as state not tier.
- **BROWSER-BLOCKED:** actual rendering, mobile presentation, hover/label clarity for a real new user not verified.
- Terminology: customer sections are plain-language (AI, Learn, Create, Community, Marketplace, Sanctuary, Music, Games, Your Access). Internal terminology stays out of customer nav (SRC).

## AUDIT 13 — CONTENT / VISUAL READINESS

- Landing pages exist (`Landing.jsx` 474 lines, `WAIInstitute.jsx` 164, `UnifiedGateway`, `LandingMarketplace`); meta/OG present; robots/sitemap present (SRC).
- No placeholder markers found in `src/` (SRC scan).
- **No image generation performed** (per constraint). Existing image architecture (DALL-E/gpt-image, GridFS, Pillow, asset metadata) remains available; `IMAGE_ASSET_PLAN.md` lists 14 purposeful assets awaiting approval (SRC).
- Visual verification (hero, imagery, empty states, mobile/desktop, loading/error states): **BROWSER-BLOCKED**.

## AUDIT 14 — PERFORMANCE / RELIABILITY

- Background tasks at startup: team monitor (300s), failover watchdog, GDPR purge cron, memory consolidation cron, rate-limiter cleanup (SRC — from startup log this session).
- Degradation: no-DB mode serves the gate map from pure registry data (this session's fix); JWT_SECRET missing → fatal at boot (fail-closed) (SRC).
- Timeouts: gateway/provider calls and payment portal call have explicit timeouts (SRC).
- **No load testing performed** (BLOCKED). In-memory rate limiter is per-process (multi-worker caveat, P2). Caching: none observed for API responses (SRC scan) — campaign traffic will hit Mongo directly (P2 consideration).

## AUDIT 15 — DEPLOYMENT / PRODUCTION ENVIRONMENT

- ~100 env vars referenced across the backend (SRC scan). Critical set for launch:
  - `MONGO_URL` (or `MONGODB_URL`/`MONGO_URI`) — **not present in sandbox** (BLOCKED)
  - `JWT_SECRET` — fail-closed if missing (SRC)
  - `LEMON_SQUEEZY_API_KEY`, `LEMON_SQUEEZY_STORE_ID`, `LEMON_SQUEEZY_WEBHOOK_SECRET`, `GUMROAD_API_KEY` — payment enablement
  - `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`, `ENCRYPTION_KEY` — encryption
  - `CORS_ORIGINS`, `FRONTEND_URL` — CORS/redirects
  - `HOURLY_TOKEN_CAP`, `USER_DAILY_TOKEN_CAP` — AI budget
  - Provider keys: `GROQ_API_KEY` (etc., 10+)
  - `SLACK_WEBHOOK_URL` (incident alerts), `EXEC_RESET_SECRET` (break-glass)
  - Stale: `STRIPE_SECRET_KEY` still referenced in env inventory despite Stripe removal (cleanup P3)
- Railway/deploy state: **not verifiable from sandbox** (BLOCKED). No production env values were read (none exist here).
- See PRODUCTION_READINESS_AUDIT.md for the checklist.

## AUDIT 16 — API / ROUTE INVENTORY

- ~35 routers mounted in `server.py` (SRC): auth, users, admin, exec, exec_control, features, ai, media, payments, byok, creator, community, ops, auditor, billing, lms, competition, chat, band, playlist, social, scholarships, jamil, site_guide, aawab, sovereign, revenue, supervisor, projects, position, bridge, access_control, misc, abo, missing, sentinel.
- Frontend: 161 routes, all link targets resolve (TEST, route-integrity).
- **Endpoints intentionally outside the Feature Registry gate map:** auth, payments, byok, media, admin, ops — these are gated by their own auth (`current_user`/`_require_rank`) rather than FCC feature classification (SRC). The FCC maps nav pages; API enforcement for these surfaces relies on role/rank checks. Documented, not a defect per se — but "cost-bearing endpoints bypassing FCC" = the BYOK free-activation and any auth-less AI path (only the two helper endpoints found).
- Redirects/aliases: `/nam→/ai`, `/creator→/studio`, `/publish→/social/publish`, `/marketplace→/store`, `/sanctuary→/helper`, `/music→/band`, `/games→/arcade`, `/admin/exec-control→/admin/office`, `/dashboard/exec→/admin/command` etc. (SRC).

## AUDIT 17 — DATA / DATABASE

- Collections referenced in source: `users`, `auth_sessions`, `audit_log`, `notifications`, `feature_configs`, `page_access`, `user_feature_overrides`, `authz_matrix`, `tier_definitions`, `payments`, `wai_credits`, `wai_refunds`, `scholarship_pledges`, `scholarship_funds`, `media products`, `byok` user keys (`user_byok_keys`), `sage_conduct_sessions` (SRC).
- **Duplicate sources of truth for tier access** (Audit 3): registry `default_tiers` vs `FEATURE_MIN_TIER` vs frontend `TIER_FOR_FEATURE`. **Duplicate role/legacy maps** handled by `roles.py` normalization (SRC).
- Inconsistency risks: payment record `user_id=None` until email match; tier granted upgrade-only (never auto-downgraded → stale entitlements); `byok_enabled` without payment possible (Audit 8).
- MongoDB behavior: unavailable in sandbox — **all DB-dependent claims are BLOCKED** (SRC only).

## AUDIT 18 — TEST COVERAGE (TEST + SRC)

Ran this session: FCC enforcement **16/16**, integration **42/42**, access gateway **29/30** (1 pre-existing `exec_pipeline` failure reproduced at git HEAD), nav-integrity **all pass**, route-integrity **all resolve** (TEST).

Existing test files: rbac_matrix, password_reset (+unit), erasure, cross_account_update, feature_control, grounding, lcewai, sage (v2/caps/perf), wai_core/pipeline, cohorts_perf, critical_paths, iter3/iter4, platform_services_unit, seed_role_heal, ancestral_sage, revenue_simulation.

**Not tested (gaps):** real payment/checkout, webhook signature + event handling, refund/cancellation, BYOK purchase → entitlement, provider calls (live), anonymous access matrix, role/tier escalation, direct-API bypass at scale, account lifecycle E2E, browser workflows, mobile nav, image/media failures, provider outage behavior, load. Each is BLOCKED by environment (no Mongo/providers/browser/Railway).

---

## EXECUTIVE SCORECARD

| Category | Status | Evidence | Blocker | Required action | Launch impact |
|---|---|---|---|---|---|
| PUBLIC | GOOD | routes, nav, route-integrity TEST | browser/DB | browser smoke of landing→register | LOW |
| AUTH | GOOD | bcrypt/JWT/tv/sessions SRC; reset tests TEST | DB | verify reset emails in prod | LOW |
| TIERS | **MISMATCH** | 3 tier maps disagree (Studio: member vs plus) | — | reconcile registry vs matrix vs TierGate | MEDIUM |
| ROLES | GOOD | roles.py + rank checks SRC | DB | — | LOW |
| BYOK | **GAP** | free activation without payment (SRC) | — | gate activate on payment/admin; keep staff free | MEDIUM |
| STAFF BYOK | OK | shared pool, priority, in-memory SRC | keys | attribution + audit event; encryption-secret-missing behavior | LOW |
| AI | BLOCKED | gateway SRC | provider keys | verify connectivity in prod (`/admin/health`) | HIGH |
| AI COST CONTROL | PARTIAL | global caps SRC; no per-feature quotas | — | decide funding policy; `byok_allowed` not consulted | MEDIUM |
| INTERNAL PROPRIETARY | GOOD | Arena exec-only (competition + FCC + nav) | DB/browser | — | LOW |
| SECURITY | PARTIAL | good primitives SRC; **no live/pentest** | env | prod smoke + pentest post-launch | MEDIUM |
| ECOMMERCE | **GAP** | no cancel/refund webhook events (SRC) | keys | add subscription/refund handling or disable subs | **HIGH** |
| PAYMENTS | NOT LIVE-VERIFIED | checkout/webhook SRC | keys/env | test real $1 in prod | HIGH |
| COMPLIANCE | **THIN** | privacy 45 lines; refund policy text missing | legal | legal review of privacy/terms/refunds | MEDIUM |
| HUMAN OVERSIGHT | PARTIAL | incidents/moderation/audit SRC | — | runbooks/escalation; verify moderation workflow | MEDIUM |
| NAVIGATION | GOOD | nav-integrity TEST | browser | browser walkthrough | LOW |
| CONTENT | OK | landing + zero placeholders SRC | browser | visual pass | MEDIUM |
| IMAGES | AUDIT-ONLY | no generation (per constraint) | decision | approve IMAGE_ASSET_PLAN batch ($0.30) or stay SVG/CSS | LOW |
| PERFORMANCE | UNVERIFIED | no load test; in-memory rate limits | env | load smoke on campaign day | MEDIUM |
| DATABASE | BLOCKED | no Mongo in sandbox | env | verify indexes/state in prod | HIGH |
| API | GOOD | 35 routers; no dead links TEST | — | — | LOW |
| DEPLOYMENT | **UNVERIFIED** | env inventory SRC | Railway | complete prod env checklist | **HIGH** |
| TESTING | PARTIAL | suites green; money/AI/browser untested | env | prod verification runs | MEDIUM |
| PRODUCTION READINESS | **NOT ESTABLISHED** | — | env | see P0 | **HIGH** |

## P0 — MUST FIX BEFORE CAMPAIGN

1. **Payment entitlement lifecycle** — handle `subscription_cancelled`/`refunded` in the webhook (or disable subscription products until handled). Today a cancelled subscriber keeps their tier forever. Directly risks "users receive something they did not pay for."
2. **Production environment completeness + live verification** — set and verify: `MONGO_URL`, `JWT_SECRET`, `LEMON_SQUEEZY_API_KEY`/`STORE_ID`/`WEBHOOK_SECRET`, `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`, `CORS_ORIGINS`, `FRONTEND_URL`; then run `python3 tests/live_fcc_matrix.py` against production (it seeds marked test users, verifies, cleans up).
3. **Provider connectivity** — run `/api/admin/health` in production; confirm the free-tier chain (groq/cerebras/sambanova/gemini) actually serves tokens before letting customers depend on AI.
4. **Bootstrap/admin claim** — confirm the production DB is NOT a fresh empty instance the campaign's first registrant would claim as `executive_admin`; if seeding is needed, do it before the campaign.
5. **Browser smoke of the campaign funnel** — landing → register → login → dashboard; plans → $3 BYOK checkout; one subscription checkout. If no browser tooling is available, do it manually before flipping the switch.

## P1 — SHOULD FIX BEFORE CAMPAIGN IF POSSIBLE

- BYOK entitlement: require a paid order record or admin action for below-instructor activation (kill the free grace path in production).
- Reconcile tier maps (registry `default_tiers` vs `FEATURE_MIN_TIER` vs `TIER_FOR_FEATURE`) — at minimum for Creator Studio (nav says Member, gate says Plus).
- Webhook idempotency on payment records.
- Legal review of Privacy (45 lines), Terms, refund policy text; publish refund policy.
- Anonymous-helper disposition (KEEP/MODIFY/REMOVE) — executive decision; also decide whether `/api/helper/ask` should require auth.
- Verify `is_active` (suspended) enforcement is applied in `current_user`.

## P2 — SAFE TO FIX AFTER LAUNCH

- Funding-mode enforcement: gateway should honor per-feature `byok_allowed` / `platform_ai`.
- Per-feature AI quotas (CONFIGURATION REQUIRED — none exist).
- Payment-record → user linkage for unregistered buyers; reconsent/session UX.
- Multi-worker rate limiter (shared store); API caching strategy for campaign traffic.
- Incident/moderation runbooks + escalation policy documentation; moderation workflow verification.
- `STRIPE_SECRET_KEY` stale env reference cleanup.

## P3 — FUTURE ENHANCEMENT

- Email verification flow; email-verified badge.
- Refund self-service; subscription upgrade/downgrade UX beyond LS portal.
- Load testing harness; CI gate for route/nav integrity; per-audience visual regression tests.
- Image asset batch (per approved `IMAGE_ASSET_PLAN.md`, ~$0.30 one-time) — not before audit approval.

---

## LAUNCH RECOMMENDATION

**LAUNCH WITH CONDITIONS** — the platform has real, coherent implementation (auth + RBAC + signed-payment webhook + GDPR surfaces + tier-first nav + bounded public AI), and the code-level integrity tests all pass. But **nothing is live-verified**: no MongoDB, no provider keys, no Railway, no browser in this environment, and there is one unambiguously dangerous money-path gap.

**Exact conditions (all P0, smallest set that changes the verdict):**
1. Payment webhook handles cancellation/refund **or** subscription products are disabled for the campaign.
2. The P0 production env checklist is complete and `live_fcc_matrix.py` passes against production.
3. `/api/admin/health` shows at least one working free-tier AI provider.
4. Production DB confirmed seeded/claimed (no first-registrant-takes-exec risk).
5. One manual browser pass of landing → register → dashboard and a $3 checkout.

If the campaign must launch without conditions 1–3, the verdict is **DO NOT LAUNCH** — the specific blockers are P0-1 (users retain paid entitlements after cancellation) and P0-2/P0-3 (production behavior is entirely unverified).

---

## HONEST-LIMITS STATEMENT

- No penetration testing was performed. No load testing was performed. No browser verification was performed. No production verification was performed.
- "Verified" above means verified in source or by automated tests this session, per the legend.
- MongoDB is unavailable in this sandbox; provider keys are unavailable; Railway is not accessible. Every DB-, AI-, payment-, and deploy-dependent claim is BLOCKED or SRC-level only.
- No code was changed during this audit.
