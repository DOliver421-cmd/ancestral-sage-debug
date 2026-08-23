# PHASE 16 — NAVIGATION ACCESS AUDIT

**Date:** August 23, 2026
**Status:** CORRECTED — source code exists; nav wiring implemented, label redesign deferred

> **Correction:** an earlier version claimed no source code existed (false — broken
> glob). Navigation today: `frontend/src/components/AppShell.jsx` filters nav via
> `lib/accessGates.js` against the gate map served by `GET /api/exec/control/access/public`.
> This phase wired the **Feature Control Center** into that map: FCC DB overrides
> (`enabled`, `allowed_roles`) now merge into the gate map, so an admin toggle actually
> hides/disables nav + routes. Full label rewrite / sidebar consolidation is a later
> phase (Phase 16 is enforcement). Canonical nav plan: FEATURE_MAP.md +
> NAVIGATION_LABEL_AUDIT.md.

---

## CURRENT NAVIGATION ARCHITECTURE (from documentation)

The sidebar (`AppShell.jsx`) is described as having sections:

| Section | Items | Access |
|---------|-------|--------|
| Home | Dashboard, Profile, Settings | Member+ |
| NAM | AI Tutor, Helper, Orchestrator, Site Guide, Council, Jamil | Role/tier gated |
| Create | Studio, Courses, Ghost Producer, Social Blast, Lounge, Earnings, Payouts | Creator+ |
| Learn | Modules, Learning Path, Competencies, Labs, Simulations, Compliance, Credentials, Certificates, Portfolio | Student+ |
| Community | Palace, Leaderboard, Chat, Legal, Incidents, Saga, Ascension | Student+ |
| Marketplace | Store, Plans, Membership, Donate, Payments, Partnerships | Public/Member |
| Sanctuary | Sanctuary, Knowledge Base | Pro+ |
| Music | Band, Playlist | Creator+ |
| Games | Arcade, Pantheon | Student+ |
| Admin | Dashboard, IAM, Command, Health | Admin/Exec |
| Director | Tools, Arena | Exec only |

**NOTE:** `AppShell.jsx` does NOT exist in this repository. This is from documentation.

---

## GATE DATA SOURCES

| Source | Endpoint | Used By | Status |
|--------|----------|---------|--------|
| `PAGE_ACCESS_REGISTRY` | `exec_control.py` | `accessGates.js` → `AppShell` | ❌ No code |
| Feature Registry | `features.py` | `/api/features/gate-map` | ❌ No code |
| Tier definitions | `exec_control.py` | `TierGate` | ❌ No code |
| Role checks | `roles.js` | `Protected`, `BoundedAdmin` | ❌ No code |

---

## NAVIGATION LABEL ISSUES (from NAVIGATION_LABEL_AUDIT.md)

| Label | Rating | Issue |
|-------|--------|-------|
| MORE | ❌ | Internal jargon — opaque |
| Palace | ⚠️ | "Palace" is brand name — unclear function |
| Sanctuary | ⚠️ | What is Sanctuary? Healing? Journaling? |
| Orchestrator | ❌ | Internal jargon — user doesn't know what this does |
| Jamil | ⚠️ | Name means nothing to new users |
| BYOK | ❌ | Developer jargon |
| Labs | ⚠️ | Ambiguous — experiments? Simulations? |
| Bridge | ❌ | Internal term |
| Command | ⚠️ | Sounds military |
| AAWAB | ❌ | Acronym — no meaning to users |

---

## DUPLICATE ROUTES (from SITE_MAP_AUDIT.md)

| Duplicate | Count | Issue |
|-----------|-------|-------|
| Course-related pages | 5 | Multiple routes for courses |
| Creator pages | 4 | Earnings, payouts, courses, studio overlap |
| Admin pages | 8+ | Dashboard, IAM, Command, Health, etc. |

---

## VERIFICATION

**STATUS: NOT VERIFIED**

Cannot verify:

- AppShell renders correctly
- Navigation items appear for correct roles
- Tier-gated items show lock state
- Route protection works
- Navigation matches Feature Registry policy
- Labels are clear to users
- Duplicates are resolved

---

*Audit based on documentation only. No source code exists.*
