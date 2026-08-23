# PHASE 16 — ROLE vs TIER MATRIX (REAL DEFINITIONS)

**Date:** August 23, 2026
**Status:** CORRECTED — uses the actual role/tier definitions in the repository

*Prior versions of this file were written when the repository was (incorrectly) believed
to be empty. Retracted.*

## ROLE (authorization identity) — real stored roles

Source of truth: `backend/roles.py` ROLE_RANK + `frontend/src/lib/roles.js` (they mirror
each other exactly). `public` is rank 0 (unauthenticated baseline), never a stored role.

| Rank | Role | Meaning |
|------|------|---------|
| 1 | student | registered learner |
| 2 | trial_pass | trial / priority member |
| 3 | instructor | instructor / moderator |
| 4 | support_staff | site support operations |
| 5 | oversight | oversight / governance |
| 6 | admin | administrator |
| 7 | executive_admin | executive owner |

Role checks are **rank-based** (`role_rank(role) >= needed`). Enforcement examples this
phase: Arena `allowed_roles=["executive_admin"]` → only rank ≥ 7 passes; Jamil
`allowed_roles=["admin","executive_admin"]` → rank ≥ 6 passes.

## TIER (commercial entitlement) — real product tiers

Source of truth: `security/feature_control.py` TIER_RANK,
`routers/exec_control.py` `_BUILTIN_TIERS`, `frontend/src/lib/tiers.js`,
`routers/payments.py`.

| Rank | Tier | Label | Price hint (existing config) |
|------|------|-------|------------------------------|
| 0 | free | Free | community access |
| 1 | member | Member | $9/mo |
| 2 | plus | Plus | $15/mo |
| 3 | pro | Pro | $29/mo |
| 4 | patron | Patron | $59/mo |
| 5 | executive | Executive | admin-granted |

## FIX APPLIED: FCC used invented labels

The Feature Control Center previously offered tiers `free, creator, pro, studio, director`
and roles `student, instructor, support_staff, admin, executive_admin`. Neither list
matches the real platform. This phase:

- Added `REAL_TIERS` (free, member, plus, pro, patron, executive) and `REAL_ROLES`
  (all 7 stored roles) to `backend/routers/features.py`.
- Added `LEGACY_TIER_MAP` (`creator→member`, `studio→plus`, `director→patron`) so stored
  configs from the old UI normalize to real tiers before display **and** enforcement.
- `update_feature` now normalizes `allowed_tiers` and drops unknown role names on write.
- `FeatureControlCenter.jsx` `ALL_TIERS`/`ALL_ROLES` updated to the real lists.

## ROLE × TIER ARE INDEPENDENT (verified usage)

| Person | Role | Tier | Consequence |
|--------|------|------|-------------|
| Free member | student | free | platform-funded AI only where explicitly configured; no internal features |
| Creator customer | creator? | member | **No `creator` role exists** — the role ladder has no `creator`; product value lives in tiers |
| Admin | admin | pro | staff tier-exemption applies to tier gates; FCC internal features still enforced by role |
| Executive | executive_admin | executive | passes every FCC role gate (rank 7) |

## CURRENT FEATURE × ROLE DEFAULTS (canonical registry, AI ecosystem subset)

| Feature | Internal | Default roles | Cost-bearing |
|---------|----------|---------------|--------------|
| AI Tutor (nam.chat) | No | student+ | Yes (platform_ai) |
| Personal Helper | No | student+ | Yes |
| Council (Sage) | No | student+ (tiers pro+) | Yes |
| Site Guide | No | student+ | Yes |
| Admin Assistant | Yes | admin+ | Yes |
| Orchestrator | Yes | admin+ | Yes |
| Jamil | Yes | admin+ | Yes |
| Arena | Yes | executive_admin | Yes |

Full matrix is served live by `GET /api/features/matrix/tier` and
`GET /api/features/matrix/role` (admin/exec only) and editable via the Feature Control
Center.
