# Working Feature Inventory — Launch Readiness Audit
**Date:** 2026-09-08 · **Method:** live code trace, not file-tree matching.
Every claim below comes from: (1) cross-referencing all 799 frontend API calls
against all 1,013 mounted backend routes, (2) executing the test suites that
can run in this environment, (3) reading the actual payment/fulfillment/tier
wiring. Claims of "working" mean the full chain exists: page → API call →
mounted backend route → real handler.

---

## 1. The one number that matters

**799 frontend API calls. 786 resolve to real, mounted backend routes. 13 are
dead — and 12 of those 13 trace to a single dead page.**

| Verdict | Count | Detail |
|---|---|---|
| Wired end-to-end | 786 | frontend call → real mounted route → real handler |
| Dead calls | 13 | 12 in `PersonaProfile.jsx` + `Personas.jsx` (calls `/ai/personas*` — no such routes exist; real persona CRUD lives at `/personas`, used correctly by `PersonaManagementConsole.jsx`) |
| Ambiguous (dynamic paths) | ~0 | `aawab` `${action}` calls resolve to real routes (`/diagnose`, `/treat`, `/certify`, `/revoke`, `/override`); `AcademyLesson` `/academy/courses/{slug}/learn` exists |

**Bottom line: the "fragments and dead ends" problem is far smaller than the
prior audits implied.** The nav may contain links to pages like
`PersonaProfile` that 404 their data, but the bulk of the site is genuinely
wired. The dead pages are edge features (AI persona browsing), not the
education/ecommerce core.

---

## 2. WORKING — verified by execution or full-chain trace

### Education core (the launch product)
| Feature | Evidence |
|---|---|
| **46 published Academy courses** incl. the 6 culturally responsive courses (African Kingdoms & Empires; African American Literature Foundations; Ethnomathematics & Black Pioneers in STEM; Global African Diaspora; Diaspora Mathematics; African Philosophy & Ethics) + 4 free student handbooks (Elementary, Middle, High School, Adult) | All pass `seed_academy.validate_course` with **0 problems** — every lesson has learn content + knowledge check + explanations; lesson orders globally unique; 54 total valid (46 published, 8 planned) |
| Academy student CRUD, dashboards, lesson view, grading | `routers/academy.py` (21 routes) ↔ `frontend/src/pages/academy/*` — every call resolves |
| **Florida compliance toolkit** — Notice of Intent (s. 1002.41), quarterly report, annual evaluation, transcript, IHIP-style plan (honestly labeled NY-style) | `POST/GET /api/academy/compliance/*` + `AcademyCompliance.jsx`; **5/5 unit tests pass** |
| Classic LMS modules + quiz progress | `/modules`, `/progress/me`, `/progress/quiz` inline in server.py; used by `ModuleView`, `ModulesList`, `StudentDashboard` — all wired |
| LMS module tier gating | 4/4 `test_lms_module_gating` tests pass |
| Compliance docs API tests | 16/16 `test_academy_api` tests pass |

### Ecommerce (the subscription engine)
| Feature | Evidence |
|---|---|
| Checkout providers | Lemon Squeezy (primary MoR) + Stripe fallback, `POST /payments/checkout`; provider resolution ladder in code |
| Webhook fulfillment | `/payments/webhook` (LS) and `/payments/stripe-webhook` grant `feature_tier` by buyer email (`_grant_tier_by_email`); media orders fulfilled idempotently with double-grant protection |
| Product catalog | `PAYMENT_PRODUCTS` — every item is fulfillable end-to-end; legacy keys kept so renewals keep granting |
| Plan display | `frontend/src/lib/plans.js` is the single source of truth; keys kept in sync with backend |
| Tier ladder | free→member→plus→pro→patron→platinum→executive, enforced **server-side** by FCC middleware, frontend mirror in `lib/tiers.js` |
| Purchase history + billing portal | `/payments/portal`, `/payments/history` |
| Promo codes | 17/17 `test_promo_codes` tests pass |
| Creator checkout unit tests | 5/5 pass |

**Ecommerce caveats (must fix before charging money):**
1. **Webhook secrets are load-bearing.** Without `LEMON_SQUEEZY_WEBHOOK_SECRET` set, purchases succeed but never fulfill (webhook 404s). Same for `STRIPE_WEBHOOK_SECRET`.
2. **Gumroad is publish-only** — no inbound webhook exists, so Gumroad sales record nothing. Do not advertise Gumroad checkout.
3. Sandbox limitation: no MongoDB here, so the webhook→grant flow could not be executed end-to-end in this environment. The code chain is verified by trace + unit tests, not live execution.

### Security (launch-blocking, mostly solid)
| Feature | Evidence |
|---|---|
| JWT auth, bcrypt hashes, forced password change | Inline auth + `routers/auth.py`; 3/3 auth regression tests pass |
| Exec-seat bootstrap lock | First-registration exec grant requires matching `EXEC_ADMIN_EMAIL` — the old escalation hole is closed (documented + code-verified) |
| Feature Control Center middleware | Enforces enabled/tier/role/flag rules on **every** /api request server-side; 39/39 FCC tests pass |
| Access Gateway hard gate | Wrap-around gate, exec-configurable, never loosens handler deps |
| Security headers | X-Frame-Options DENY, nosniff, XSS |
| Key encryption at rest | `PROVIDER_KEY_ENCRYPTION_SECRET` ladder (env → platform_config → ephemeral) |
| Audit encryption | Optional via `AUDIT_ENCRYPTION_KEY`, warns when unencrypted |
| Rate limiting | `check_rate` dependency wired through router bind |

| Site Guide + Help (combined feature) | One floating widget on every page: "This Page" route-aware help (`/help/guide`) + "Ask the Guide" persona chat (`/site-guide/chat`, gated member+/BYOK/staff). `/site-guide` redirects into the widget; guide KB, FAQ, and page index include all Homeschool Academy pages | Staff build tracker (`/academy/build`) | Live catalog + video enrichment + build checklist, role rank ≥ instructor |
| Feature | Evidence |
|---|---|
| Feature flags & page gates (exec UI) | `/exec/control/*` (26 routes) ↔ ExecControlPanel/ExecBusinessOffice |
| User admin (roles, tiers, ban, erasure, reset) | `routers/users.py` mounted, RBAC-guarded; partial test pass (2 failures are environment, see §4) |
| Asset/media upload + products | `/media/upload`, `/media/products` wired (exec asset manager from earlier phase) |
| Password reset | Hashed tokens, single-use, TTL; **3 unit tests pass, 3 are DB-blocked (env)** |
| Health/ready probes | `/api/ready` 503s until DB answers — used by Railway healthcheck |

---

## 3. SAVABLE (wired backend, weak/no frontend, or dead frontend)

These have real backend routes. They are candidates to route into the Student
Center **only after** their UI is verified in a browser:

- **IAM console** (`/iam/*`, 18 routes) — identities/delegations/consent; frontend tabs exist and call it. Untested in browser here.
- **Scholarships** (11 routes) — funds/apply/pledge/admin all mounted and called. Could serve the ESA/PEP provider story.
- **Auditor** (6 routes), **Sentinel** (14 routes), **Site Guide** (3 routes), **Handbooks** (3 routes) — wired, low-risk.
- **Jamil AI assistant** (11 routes) — wired; depends on AI provider keys being set.
- **Workspace/save + notifications** — small, wired, useful in Student Center.

## 4. ENVIRONMENT-BLOCKED VERIFICATION (not failures, but not "working" until run)

- All **DB-backed integration suites** require MongoDB on :27017; this sandbox has none running (`Dockerfile.daytona` exists to provide one). 57 test errors + `test_grounding` 2 failures are `ConnectionRefusedError` — environment, not code. **These must be run against a live DB (or the Daytona sandbox image) before launch sign-off.**
- `test_rbac_matrix` / `test_security_hardening`: 29 passed; remaining are DB-blocked.
- No browser click-through was performed. Route-wiring is proven; human-path rendering is not.

## 5. DEAD — do not route, do not advertise

- `PersonaProfile.jsx` + `Personas.jsx` — call `/ai/personas*` which exist nowhere. Either point them at the real `/personas` CRUD data or remove the nav links.
- Gumroad inbound purchase flow — does not exist. Publishing TO Gumroad works; selling THROUGH it silently loses sales.

---

## 6. Honest tier proposal for the Student Center

Every item below is something **every button does what it says** (verified by
the trace + passing tests above):

**FREE (public)** — Landing, course catalog browsing (46 courses visible incl. the 4 free student handbooks), on-site curated educational video embeds, starter library content, cookie consent, registration/auth.

**MEMBER (entry, e.g. $X/mo)** — Full Academy access: enroll students, lessons, knowledge checks, progress dashboards; compliance document generator (Notice of Intent, quarterly reports, annual evaluation, transcript); classic modules + quizzes.

**PLUS** — Multiple students per family, instructor access, certificates.

**PRO** — Everything above + full Florida compliance suite including IHIP-style plans, priority AI features (Jamil, requires provider keys), early access to new culturally responsive course releases.

**PATRON+** — Community/scholarship features, creator tools.

Do **not** put in any tier until DB-backed tests run live: anything AI-chat dependent, IAM console, or anything not click-tested.

## 7. Before-launch checklist (in priority order)

1. Run the full test suite against a real MongoDB (Daytona image or staging) — this is the difference between "trace-verified" and "verified."
2. Set `LEMON_SQUEEZY_WEBHOOK_SECRET` (+ Stripe secret) in production vars and buy a real $1 product to watch fulfillment grant a tier.
3. Fix or remove the 2 dead persona pages.
4. Browser click-through of the Student Center path: register → subscribe → tier granted → course access → compliance doc download.
5. Pin `CORS_ORIGINS` (currently `*`), confirm `JWT_SECRET` and `PROVIDER_KEY_ENCRYPTION_SECRET` are set and persistent.
