# CUSTOMER ACCESS MATRIX (TIER-FIRST)

**Date:** August 23, 2026
**Generated from:** live `FEATURE_REGISTRY` (`backend/routers/features.py`), normalized tiers.
**Columns:** PUBLIC (anonymous) · FREE (registered) · BYOK (unlock-eligible) ·
MEMBER · PLUS · PRO · PATRON (cumulative — a higher tier inherits lower ones) ·
EXECUTIVE = internal/role-gated, never a customer tier.
**Y** = eligible now (registry default), **—** = not eligible, **(BYOK)** = eligible
only when funded by the user's own key, **[FLAG]** = additionally enforced by an exec
platform flag at the API.

## PUBLIC SET (anonymous — no dashboard, no AI)

Landing · public discovery · plans/pricing · legal/help · sign in · register.
Every other feature requires a registered session. No registry feature is `public`
today; the registry has no `public_access` field yet (TIER_ACCESS_ARCHITECTURE G2).

## AI

| Feature | Public | Free | BYOK | Member | Plus | Pro | Patron | PAI | BYOK key | Cost |
|---------|--------|------|------|--------|------|-----|--------|-----|----------|------|
| AI Tutor | — | Y | (BYOK) | Y | Y | Y | Y | Y | Y | Y |
| Personal Helper | — | Y | (BYOK) | Y | Y | Y | Y | Y | Y | Y |
| Site Guide | — | Y | — | Y | Y | Y | Y | Y | N | Y |
| Council (Sage) | — | — | (BYOK) | — | Y | Y | Y | Y | Y | Y |
| My AI Keys (BYOK) | — | Y | n/a | Y | Y | Y | Y | N | Y | N |

## Creation

| Feature | Public | Free | BYOK | Member | Plus | Pro | Patron | PAI | BYOK key | Cost |
|---------|--------|------|------|--------|------|-----|--------|-----|----------|------|
| Creator Studio | — | — | (BYOK) | Y | Y | Y | Y | Y | Y | Y |
| Course Manager | — | — | — | Y | Y | Y | Y | N | N | N |
| Ghost Producer | — | — | (BYOK) | Y | Y | Y | Y | Y | Y | Y |
| Social Blast | — | — | (BYOK) | Y | Y | Y | Y | Y | Y | Y |
| Creator Lounge | — | — | — | Y | Y | Y | Y | N | N | N |
| My Earnings | — | — | — | Y | Y | Y | Y | N | N | N |
| Payout Dashboard | — | — | — | Y | Y | Y | Y | N | N | N |

## Learning

| Feature | Public | Free | BYOK | Member | Plus | Pro | Patron | PAI | BYOK key | Cost |
|---------|--------|------|------|--------|------|-----|--------|-----|----------|------|
| Modules | — | Y | — | Y | Y | Y | Y | N | N | N |
| Learning Path | — | — | — | — | Y | Y | Y | Y* | N | Y* |
| Competencies | — | Y | — | Y | Y | Y | Y | N | N | N |
| Workforce Labs | — | Y | — | Y | Y | Y | Y | N | N | N |
| Lab Simulations | — | Y | — | Y | Y | Y | Y | N | N | N |
| Compliance | — | Y | — | Y | Y | Y | Y | N | N | N |
| Credentials | — | Y | — | Y | Y | Y | Y | N | N | N |
| Certificates | — | Y | — | Y | Y | Y | Y | N | N | N |
| Portfolio | — | Y | — | Y | Y | Y | Y | N | N | N |

\* `learn.adaptive` API (`/api/adaptive/me`) is rule-based (no provider call); marked
cost-bearing conservatively. Executive decision required (Phase 17 finding).

## Community / Commerce / Wellness / Music / Games

| Feature | Public | Free | BYOK | Member | Plus | Pro | Patron | Cost |
|---------|--------|------|------|--------|------|-----|--------|------|
| Members' Palace | — | Y | — | Y | Y | Y | Y | N |
| XP Leaderboard | — | Y | — | Y | Y | Y | Y | N |
| Community Chat | — | Y | — | Y | Y | Y | Y | N |
| Legal Tools | — | Y | — | Y | Y | Y | Y | N |
| Report Incident | — | Y | — | Y | Y | Y | Y | N |
| Vonns Saga | — | Y | — | Y | Y | Y | Y | N |
| Ascension Protocols | — | Y | — | Y | Y | Y | Y | N |
| Media Store | — | Y | — | Y | Y | Y | Y | N |
| Plans & Pricing | — | Y | — | Y | Y | Y | Y | N |
| Membership | — | Y | — | Y | Y | Y | Y | N |
| Donate | — | Y | — | Y | Y | Y | Y | N |
| Payment History | — | Y | — | Y | Y | Y | Y | N |
| Partnerships | — | Y | — | Y | Y | Y | Y | N |
| Sanctuary | — | — | — | — | Y | Y | Y | Y (page redirects to /helper — decision pending) |
| Knowledge Base | — | Y | — | Y | Y | Y | Y | N |
| Band on a Page | — | — | — | Y | Y | Y | Y | N |
| Playlist Manager | — | Y | — | Y | Y | Y | Y | N |
| Virtual Arcade | — | Y | — | Y | Y | Y | Y | N |
| M.O.R.E. Pantheon | — | Y | — | Y | Y | Y | Y | N |

## INTERNAL (never customer-facing)

| Feature | Role gate | Cost | PAI | BYOK |
|---------|-----------|------|-----|------|
| Arena | executive_admin ONLY | Y | Y | N |
| Jamil | admin+ | Y | Y | Y |
| Orchestrator | admin+ | Y | Y | Y |
| Admin Assistant | admin+ | Y | Y | Y |
| Admin Dashboard / IAM / Health | admin+ | N | N | N |
| Command Center | executive_admin | N | Y | N |

## FUNDING RULE (no accidental free AI)

Platform-funded AI (`PAI=Y`) runs only for users whose tier + role passed the FCC and
who are within the global hourly cap + daily budget. BYOK-funded usage (`BYOK key=Y`)
requires `byok_allowed=true` AND the $3 entitlement; it never funds an internal or
role-restricted feature. A feature with `PAI=N, BYOK=N` runs no inference at all.

## DELTA vs CURRENT SIDEBAR

This matrix is the target for nav visibility (STEP 5–6). Today the sidebar shows all
customer features to every registered user regardless of tier (TIERED_NAVIGATION_AUDIT
F1). The matrix above is what the FCC tier matrix should drive: `isPageEnabled` +
tier-rank check per nav item, computed from this same registry data — no second access
system.
