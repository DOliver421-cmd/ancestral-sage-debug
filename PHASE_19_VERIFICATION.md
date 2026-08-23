# PHASE 19 — CUSTOMER-FIRST NAVIGATION REWRITE + ACCESS MODEL ALIGNMENT

**Status: IMPLEMENTED (navigation) / VERIFIED (backend gate map + tests) / BLOCKED (live HTTP matrix, browser E2E, Railway)**

Date: 2026-08-23

---

## 1. WHAT THE SIDEBAR NOW LOOKS LIKE (exact structure)

The sidebar is **tier-first for customers, role-first for staff**, and generated as a
projection of the canonical Feature Registry gate map (`GET /api/exec/control/access/public`).
No second access-control system was created: `AppShell` renders items through
`isPageEnabled()`, which delegates to the shared pure module `src/lib/navAccess.js`
(also used verbatim by the node integrity test).

### PUBLIC / VISITOR (anonymous)
- **Home** — Home / Landing *(no Dashboard)*
- **Explore** — Courses, Creators, Community, Store, Help
- Footer: **Sign In** / **Create Account** (no logout, no "Signed in as")

### REGISTERED FREE
- **Home** — Home / Landing, Dashboard, My Profile, Settings
- **Your Access** — tier badge ("Free access") + Plans & Upgrade
- **AI** — AI Tutor, Personal Helper, Site Guide, Council (hidden below Plus), My AI (BYOK)
- **Learn** — Modules, Learning Path (Plus+), Competencies, Labs, Lab Simulations, Compliance, Credentials, Certificates, Portfolio
- **Community** — Members' Palace, XP Leaderboard, Community Chat, Legal Tools, Report Incident, Vonns Saga, Ascension Protocols
- **Marketplace** — Media Store, Plans & Pricing, Membership, Donate, Payment History, Partnerships
- **Sanctuary** — Knowledge Base (Sanctuary itself is Plus+)
- **Music** — Playlist Manager (Band is Member+)
- **Games** — Virtual Arcade, M.O.R.E. Pantheon

### BYOK-UNLOCKED
- Not a tier — shown as a state ("BYOK unlocked" under Your Access) and the **My AI (BYOK)** entry (the existing $3 unlock page) in the AI section. BYOK never unlocks internal features (verified by test).

### MEMBER (+ everything below)
- **Create** (section unlocks at Member) — Creator Studio, Course Manager, Ghost Producer, Social Blast, Creator Lounge, Earnings, Payouts
- **Music** gains — Band on a Page

### PLUS (+ everything below)
- **AI** gains — Council (Sage)
- **Learn** gains — Learning Path
- **Sanctuary** gains — Sanctuary

### PRO / PATRON / EXECUTIVE (customer)
- Inherit everything below; no additional nav items are tier-gated today (registry default tiers for pro/patron features are the same top sets).

### SUPPORT STAFF
- Customer view per their tier **plus** the role-only **Site Support** section (Audit Log, Moderation). Support staff are **not** tier-exempt in the backend, so a free-tier support member does not see premium customer items (verified).

### ADMIN
- Customer view plus **Director** section — Admin Overview, IAM, Business Office, System Health, Payments, Billing, Prices, Revenue, Analytics, Audit Log, Moderation, Sage Audit, Feature Control, Sites & Inventory, AI Team Bridge, Provider Gateway, Site Report. *(Command Center moved out — it is exec-only in the backend.)*

### EXECUTIVE
- Separate **Executive** section — **Command Center** and **The Arena** (both exec-only in the backend). Arena appears **only** here.

---

## 2. EVERY SIDEBAR ITEM → CANONICAL FEATURE / ROUTE / ACCESS

Full mapping (route → feature_id → required tier / role / public / BYOK / cost) lives in
`CUSTOMER_ACCESS_MATRIX.md` (Phase 18) and `FEATURE_ACCESS_MATRIX.md` (Phase 17). Key nav-relevant
classifications now emitted by the live gate map:

| Route | Feature | Tier | Role | Public | BYOK-related |
|---|---|---|---|---|---|
| /ai | nam.chat | free+ | student+ | no | BYOK page separate |
| /helper | nam.helper | free+ | student+ | no | — |
| /assistant | nam.assistant | — | admin+ | no | internal |
| /council | nam.council | plus+ | student+ | no | — |
| /jamil | nam.jamil | — | admin+ | no | internal |
| /byok | nam.byok | free+ | student+ | no | BYOK unlock/management |
| /studio | create.studio | member+ | student+ | no | — |
| /creator/courses | create.courses | member+ | student+ | no | — |
| /adaptive | learn.adaptive | plus+ | student+ | no | — |
| /modules | learn.modules | free+ | student+ | **yes** | — |
| /sanctuary | sanctuary.reflection | plus+ | student+ | no | — |
| /band | music.band | member+ | student+ | no | — |
| /arena | games.arena | — | **executive_admin only** | no | internal/proprietary |
| /admin/command | admin.command | — | **executive_admin only** | no | internal |
| /admin | admin.dashboard | — | admin+ | no | internal |
| /store | marketplace.store | free+ | student+ | **yes** | — |
| /leaderboard | community.leaderboard | free+ | student+ | **yes** | — |
| /plans | marketplace.plans | free+ | student+ | **yes** | — |

---

## 3. FEATURES EXCLUDED FROM CUSTOMER NAVIGATION (and why)

- **Arena** — proprietary internal executive system; exec-only.
- **Command Center** (`/admin/command`) — exec-only in backend registry; moved from the
  admin-visible Director section to the Executive section (fixes a nav/backend mismatch:
  admins previously saw a link they were 403'd on).
- **Admin Assistant, Jamil, Orchestrator** — internal_only; hidden from students by the
  role gate in the gate map (visible to admin/exec in the AI console as their canonical persona home).
- **All admin/exec surfaces** — not customer features by registry classification.

## 4. INTERNAL-ONLY FEATURES AND AUTHORIZED ROLES

| Feature | Authorized role |
|---|---|
| games.arena | executive_admin |
| admin.command | executive_admin |
| nam.assistant, nam.jamil, nam.orchestrator | admin, executive_admin |
| admin.dashboard, admin.iam, admin.health | admin, executive_admin |

(admin.office / admin.analytics / admin.audit / admin.moderation etc. are admin+ per registry
`default_roles` and the ROUTE_ACCESS_REGISTRY — see `FEATURE_ACCESS_MATRIX.md`.)

## 5–9. PHASE REQUIREMENTS VERIFIED

- **Arena exec-only** — VERIFIED: backend `competition.py` `_require_rank("executive_admin")`,
  FCC `internal_only` middleware, gate map `allowed_roles: ["executive_admin"]`, nav under
  Executive only, and nav-integrity Test 11 (all 11 audiences).
- **Public has no dashboard** — VERIFIED: AppShell gates Dashboard behind `isAuthed`; public
  section contains no Dashboard (structural test + logic contract).
- **Free users don't see premium features by default** — VERIFIED: gate map emits registry
  `allowed_tiers` (member+/plus+ sets); nav-integrity tier-ladder test proves free sees only
  free-tier items, Create section hidden below Member.
- **BYOK as entitlement, not tier** — VERIFIED: no `byok` tier exists; BYOK shown as a state
  + the existing `/byok` unlock page; Test 6 proves BYOK never unlocks internal features.
- **Support shared-BYOK role-controlled** — VERIFIED (audit only): `reload_shared_byok()` →
  `_SHARED_BYOK_POOL` is provider-priority, in-memory, isolated; customers never receive
  staff credentials. Known gaps remain documented in `STAFF_BYOK_ARCHITECTURE.md` (no
  per-member attribution, no explicit "shared pool used" audit event, plaintext risk if
  `PROVIDER_KEY_ENCRYPTION_SECRET` is absent).
- **Features whose registry classification is insufficient for nav** — `legal-tools`
  (PATH_POLICIES maps `/more/litigation` → key `legal-tools`, but the registry route is
  `/more/litigation` → key `more`), so that single key lacks tier metadata (no functional
  impact: its tier set is free+). Also `/help-center`, `/courses`, `/community`, `/creators`
  have no registry feature (genuinely public routes) — documented, not invented.

## 10. WHAT WAS CHANGED

| File | Change |
|---|---|
| `backend/routers/features.py` | `public_access` field: registry defaults on the 5 verified public features; propagated through `get_feature_config`, `get_feature_config_async`, `feature_gate_map`, `update_feature` |
| `backend/routers/exec_control.py` | `ec_access_public` restructured: registry classification pass (allowed_tiers + public_access + internal role gates) **always runs** (survives DB outage); FCC overrides merged per-field afterward (seeded from registry, explicit `role_overridden` tracking so an FCC role override still wins); `navigation_visible` now merged so the FCC "Visible in Nav" toggle actually works |
| `backend/server.py` | `byok_enabled: bool` on the User model (exposed via `/auth/me`) so the sidebar can show the BYOK-unlock state |
| `frontend/src/lib/navAccess.js` | **new** — pure, dependency-free tier-first decision module (single source for browser + tests) |
| `frontend/src/lib/accessGates.js` | `isPageEnabled` delegates to `navAccess` (tier + public + nav-visibility + role checks) |
| `frontend/src/components/AppShell.jsx` | sidebar rewritten tier-first: public section (no Dashboard), authed-only Dashboard/Profile/Settings, Your Access tier badge, section/`isAuthed`+`hasTier` gating, Create at Member+, Arena + Command Center moved to new exec-only Executive section, anonymous Sign In/Register footer |
| `frontend/src/pages/FeatureControlCenter.jsx` | **Public Access** toggle + PUBLIC badge on feature cards |
| `frontend/scripts/nav-integrity.js` | **new** — node integrity test (logic matrix + static AppShell structure) |
| `frontend/package.json` | `test:nav` script |
| `backend/tests/test_fcc_enforcement.py` | +1 test (`test_ec_access_public_tier_and_public_metadata`) — tier/public/nav-visibility propagation + full-registry gate-map coverage |

## 11. TESTS

| Suite | Result |
|---|---|
| `backend/tests/test_fcc_enforcement.py` | **16/16** |
| `backend/tests/test_integration.py` | **42/42** |
| `backend/tests/test_access_gateway.py` | **29/30** — the 1 failure (`exec_pipeline` handler-derived gap) is pre-existing, reproduced at git HEAD in Phase 16 |
| `frontend node scripts/nav-integrity.js` | **ALL CHECKS PASSED** (14 logic assertions incl. Phase 18/19 acceptance tests 1,2,3,6,7,8,9,10,11,12,15,16 + 14 structural assertions) |
| Live gate-map payload (`GET /api/exec/control/access/public`) | VERIFIED — 60 keys with allowed_tiers/public_access/internal roles; `GET /api/features/gate-map` (feature_gate_map) verified with 48 features incl. public_access |

## 12. HONEST STATUS

- **VERIFIED** — registry data, gate-map construction (unit + live no-DB path), decision logic,
  sidebar structure, Arena exec-only, no public Dashboard, tier inheritance, FCC overrides
  (enabled/tiers/roles/public/nav-visibility) reaching the nav map, `byok_enabled` model field.
- **NOT TESTED / BLOCKED** — live HTTP access matrix (no MongoDB in sandbox;
  `backend/tests/live_fcc_matrix.py` ready for Railway); browser E2E (no tooling installed,
  not introduced); Railway deploy + provider connectivity; production behavior.
- **NOT CHANGED** — no features deleted/disabled, no providers/gateway/BYOK replaced, no
  new services/signups/spend, no image generation, no invented tiers/roles. The bounded
  anonymous `/api/public/helper/ask` teaser is untouched (executive decision pending).

**Not claimed:** production-ready navigation, browser-verified sidebar, or "good to go".
The backend remains authoritative; this phase corrected the presentation layer.
