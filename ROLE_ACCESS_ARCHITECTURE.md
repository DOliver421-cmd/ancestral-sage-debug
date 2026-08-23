# ROLE ACCESS ARCHITECTURE

**Date:** August 23, 2026
**Status:** AUDIT COMPLETE — roles verified; role≠tier separation confirmed in enforcement

## 1. THE REAL ROLES (source of truth)

Verified against `backend/roles.py` (`ROLE_RANK`) + `frontend/src/lib/roles.js`
(they mirror exactly). `public` (0) is the unauthenticated baseline, never stored.

| Rank | Role | Meaning |
|------|------|---------|
| 1 | student | registered learner |
| 2 | trial_pass | trial / priority member |
| 3 | instructor | instructor / moderator |
| 4 | support_staff | site support operations |
| 5 | oversight | governance |
| 6 | admin | administrator |
| 7 | executive_admin | executive owner |

## 2. ROLE ≠ TIER (confirmed in code)

- A user's **role** is `user.role` (authority). A user's **tier** is
  `user.feature_tier` (commercial entitlement). They are independent fields.
- The FCC enforces them independently: `allowed_roles` (rank-based via
  `roles.role_rank`) and `allowed_tiers` (rank-based via `TIER_RANK`).
- **Admin/exec are NOT customer tiers.** `TIER_EXEMPT_ROLES = ("admin",
  "executive_admin")` lets staff bypass *tier gates* — but the FCC `internal_only`
  and `enabled` checks run BEFORE the tier exemption, so staff cannot reach a
  disabled or internal-only feature without the correct role rank.
- An admin's `feature_tier` may be `"free"` — role grants authority, not a
  purchased tier. An executive's tier is `"executive"` (admin-granted), which is
  not a purchasable customer tier.

## 3. ENFORCEMENT LAYERS

| Layer | Mechanism | Verified |
|-------|-----------|----------|
| Router handlers | `require_role` / `_require_rank` (e.g. competition exec, exec_command exec, admin.py admin) | YES |
| FCC middleware | `allowed_roles` rank check + `internal_only` gate | YES (tests 15/15) |
| Exec AccessGateway | 31 controls over admin/exec surfaces | YES (29/30 suite; 1 pre-existing unrelated failure) |
| Admin exemption | `/api/admin/*` exempt from feature middleware; own rank checks + IP whitelist | YES |

## 4. ROLE RESTRICTIONS THAT MUST NOT WEAKEN

- **Arena:** `executive_admin` ONLY (FCC + `competition.py` `_require_rank`). Not a
  customer feature, not a tier feature.
- **Jamil:** `admin`+ (FCC + router auth). Proprietary persona, not public.
- **Orchestrator:** `admin`+ (FCC).
- **Admin surfaces:** `admin`+ (router rank).
- **Command Center:** `executive_admin` (`exec_command.py`).

## 5. ROLE-BASED NAVIGATION (internal only)

After tier filtering (future), role sections apply:
- **Instructor** section: roster, lab approvals, attendance (role-gated, correct).
- **Site Support** section: support tools (role-gated).
- **Director** section (admin+): admin/exec control surfaces — includes Arena
  (exec-only) and Feature Control.
- **Agent Wellness** section (`oversight`+): agent registry/certification.

These are internal/staff surfaces and must NOT be presented as customer navigation
(tier-first sidebar keeps them separate).

## 6. ACCEPTANCE STATUS (role dimension)

Verified now: tests 6, 11, 12 (BYOK no internal; Arena exec-only; Jamil admin+) pass
in `tests/test_fcc_enforcement.py`; admin ≠ paid tier (staff tier-exemption is
bypass-only, and FCC classification runs first — unit-tested `enabled=false` blocks
admin).

Not yet verifiable without Mongo/browser: role-gated nav rendering (instructor/support
sections), live HTTP matrix (blocked in sandbox).
