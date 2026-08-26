# FEATURE ACCESS MATRIX

**Date:** August 23, 2026
**Generated from:** `backend/routers/features.py` FEATURE_REGISTRY (live, 48 features)
**Enforcement:** `security/feature_control.py` + exec flags + router rank checks

Legend: INT = internal_only · CUST = customer_access_allowed · COST = cost_bearing ·
PAI = platform_ai · BYOK = byok_allowed · Roles/Tiers = `default_roles`/`default_tiers`
(rank-ordered, legacy labels normalized). Enforcement = the layers that actually protect
the real API surface (FCC = Feature Control Center middleware; FLAG = exec platform flag
+ tier; RANK = router-level role check; AUTH = authenticated only).

## AI ecosystem

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| AI Tutor `nam.chat` | /ai | `/api/ai/chat`, `/api/nam` | N | Y | Y | student+ | free+ | Y | Y | FCC + FLAG(ai_chat) |
| Personal Helper `nam.helper` | /helper | `/api/ai/helper` | N | Y | Y | student+ | free+ | Y | Y | FCC + FLAG(ai_chat) |
| Admin Assistant `nam.assistant` | /assistant | (none — no route) | Y | N | Y | admin+ | — | Y | Y | frontend BoundedAdmin only (no backend surface) |
| Orchestrator `nam.orchestrator` | /orchestrator | `/api/ai/orchestrator` | Y | N | Y | admin+ | — | Y | Y | FCC + RANK |
| Site Guide `nam.site_guide` | /site-guide | `/api/site-guide/*` | N | Y | Y | student+ | free+ | Y | N | FCC |
| Council (Sage) `nam.council` | /council | `/api/ai/sage/*` | N | Y | Y | student+ | plus+ | Y | Y | FCC + FLAG(ai_chat) |
| Jamil `nam.jamil` | /jamil | `/api/jamil/*` | Y | N | Y | admin+ | — | Y | Y | FCC + RANK |
| My AI Keys `nam.byok` | /byok | `/api/byok/*` | N | Y | N | student+ | free+ | N | Y | AUTH |

## Creation ecosystem

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| Creator Studio `create.studio` | /studio | `/api/studio/*` | N | Y | Y | student+ | member+ | Y | Y | FLAG(studio, plus) + AUTH |
| Course Manager `create.courses` | /creator/courses | `/api/lms/courses` | N | Y | N | student+ | member+ | N | N | FLAG(courses, plus) |
| Ghost Producer `create.ghost` | /ghost-producer | calls `/api/ai/chat` | N | Y | Y | student+* | member+ | Y | Y | page admin-gated; ai_chat FLAG |
| Social Blast `create.social` | /social/publish | `/api/ai/social-blast` | N | Y | Y | student+ | member+ | Y | Y | FLAG(publisher_ai, member) |
| Creator Lounge `create.lounge` | /creator-lounge | `/api/creator-lounge` | N | Y | N | student+ | member+ | N | N | FLAG(lounge, member) |
| My Earnings `create.earnings` | /creator/earnings | `/api/billing/earnings` | N | Y | N | student+ | member+ | N | N | FLAG(earnings, plus) |
| Payout Dashboard `create.payouts` | /creator/payouts | `/api/billing/payouts` | N | Y | N | student+ | member+ | N | N | FLAG(payouts, plus) |

## Learning ecosystem

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| Modules `learn.modules` | /modules | `/api/lms/modules` | N | Y | N | student+ | free+ | N | N | FLAG(courses, plus) |
| Learning Path `learn.adaptive` | /adaptive | `/api/adaptive/me` | N | Y | Y* | student+ | plus+ | Y | N | **AUTH only — GAP** (rule-based, no provider call) |
| Competencies `learn.competencies` | /competencies | `/api/lms/competencies` | N | Y | N | student+ | free+ | N | N | AUTH |
| Workforce Labs `learn.labs` | /labs | `/api/lms/labs` | N | Y | N | student+ | free+ | N | N | FLAG(courses, plus) |
| Lab Simulations `learn.simulations` | /lab-simulations | `/api/lms/simulations` | N | Y | N | student+ | free+ | N | N | AUTH |
| Compliance `learn.compliance` | /compliance | `/api/lms/compliance` | N | Y | N | student+ | free+ | N | N | AUTH |
| Credentials `learn.credentials` | /credentials | `/api/lms/credentials` | N | Y | N | student+ | free+ | N | N | AUTH |
| Certificates `learn.certificates` | /certificates | `/api/lms/certificates` | N | Y | N | student+ | free+ | N | N | AUTH |
| Portfolio `learn.portfolio` | /portfolio | `/api/lms/portfolio` | N | Y | N | student+ | free+ | N | N | AUTH |

## Community ecosystem

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| Members' Palace `community.palace` | /palace | `/api/community/palace` | N | Y | N | student+ | free+ | N | N | AUTH |
| XP Leaderboard `community.leaderboard` | /leaderboard | `/api/community/leaderboard` | N | Y | N | student+ | free+ | N | N | AUTH |
| Community Chat `community.chat` | /more/chat | `/api/chat` | N | Y | N | student+ | free+ | N | N | AUTH |
| Legal Tools `community.legal` | /more/litigation | — | N | Y | N | student+ | free+ | N | N | page gate (legal-tools) |
| Report Incident `community.incidents` | /incidents | `/api/community/incidents` | N | Y | N | student+ | free+ | N | N | AUTH |
| Vonns Saga `community.saga` | /vonns-saga | `/api/saga` | N | Y | N | student+ | free+ | N | N | AUTH |
| Ascension Protocols `community.ascension` | /ascension-protocols | — | N | Y | N | student+ | free+ | N | N | page gate |

## Commerce ecosystem

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| Media Store `marketplace.store` | /store | `/api/commerce/store` | N | Y | N | student+ | free+ | N | N | AUTH |
| Plans & Pricing `marketplace.plans` | /plans | — | N | Y | N | student+ | free+ | N | N | public page |
| Membership `marketplace.subscribe` | /subscribe | `/api/billing/subscribe` | N | Y | N | student+ | free+ | N | N | AUTH |
| Donate `marketplace.donate` | /donate | `/api/billing/donate` | N | Y | N | student+ | free+ | N | N | AUTH |
| Payment History `marketplace.payments` | /payment/history | `/api/billing/history` | N | Y | N | student+ | free+ | N | N | AUTH |
| Partnerships `marketplace.partnerships` | /partnership | `/api/billing/partnerships` | N | Y | N | student+ | free+ | N | N | AUTH |

## Wellness / Music / Games

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| Sanctuary `sanctuary.reflection` | /sanctuary (→/helper) | — | N | Y | Y* | student+ | plus+ | Y | N | redirect; no dedicated API |
| Knowledge Base `sanctuary.knowledge` | /knowledge-base | — | N | Y | N | student+ | free+ | N | N | page gate |
| Band on a Page `music.band` | /band | `/api/band` | N | Y | N | student+ | member+ | N | N | FLAG(band, plus) |
| Playlist Manager `music.playlist` | /playlist/dashboard | `/api/playlist` | N | Y | N | student+ | free+ | N | N | FLAG(publisher, plus) |
| Virtual Arcade `games.arcade` | /arcade | — | N | Y | N | student+ | free+ | N | N | page gate |
| M.O.R.E. Pantheon `games.pantheon` | /trash | — | N | Y | N | student+ | free+ | N | N | page gate |

## Internal / Admin

| Feature | Route | API surface | INT | CUST | COST | Roles | Tiers | PAI | BYOK | Enforcement |
|---------|-------|-------------|-----|------|------|-------|-------|-----|------|-------------|
| **Arena `games.arena`** | /arena | `/api/competition/*` | **Y** | **N** | Y | **executive_admin** | — | Y | N | FCC + RANK (exec) |
| Admin Dashboard `admin.dashboard` | /admin | `/api/admin` | Y | N | N | admin+ | — | N | N | /api/admin exempt + RANK + AccessGateway |
| IAM Console `admin.iam` | /admin/iam | `/api/admin/users` | Y | N | N | admin+ | — | N | N | RANK + AccessGateway |
| Command Center `admin.command` | /admin/command | `/api/exec-command` | Y | N | N | executive_admin | — | Y | N | RANK (exec) |
| System Health `admin.health` | /admin/health | `/api/admin/health` | Y | N | N | admin+ | — | N | N | RANK |

## Coverage gaps (documented, not hidden)

1. **`learn.adaptive` (`/api/adaptive/me`)** — authenticated-only, no FCC/flag gate.
   Endpoint is rule-based (computes recommendations from progress/lab data; no provider
   invocation verified), so the `cost_bearing`/`platform_ai` classification is
   conservative. **Decision required:** map into FCC or reclassify as free/rule-based.
2. **`nam.assistant`** — no backend route exists; protection is frontend-only
   (`BoundedAdmin`). Acceptable while no API surface exists; revisit if one is added.
3. **`sanctuary.reflection`** — `/sanctuary` redirects to `/helper`; registry reflects
   "no dedicated API". The Sanctuary product identity needs an executive decision
   (restore a real page/API or keep the redirect).
4. **`games.pantheon` route `/trash`** — suspicious legacy route label; page works, label
   needs renaming (NAVIGATION_LABEL_AUDIT).
5. **Ghost Producer roles** — registry default roles list `student+` but the page is
   admin-gated in `routers/abo.py`; classification should be reconciled
   (customer vs admin) by an executive decision.
