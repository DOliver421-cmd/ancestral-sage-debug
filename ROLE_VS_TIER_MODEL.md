# ROLE vs TIER MODEL — Current State + Proposed Separation

**Date:** August 22, 2026

---

## CURRENT STATE: CONFUSED

The platform currently uses both roles and tiers, but conflates them in practice:

### Current Roles (backend/roles.py)
```
rank 1: student
rank 2: trial_pass
rank 3: instructor
rank 4: support_staff
rank 5: oversight
rank 6: admin
rank 7: executive_admin
```

### Current Membership Tiers (services/entitlements.py)
```
free, creator, pro, studio, director
```

### Where They Get Confused

1. **`director` appears in BOTH** — it's a membership tier AND the executive role
2. **Route protection uses roles**, but TierGate uses membership tiers — these are different systems that don't talk to each other
3. **Nav visibility** is controlled by `hasRank()` (roles) but feature access is controlled by `TierGate` (tiers) — two separate systems
4. **"admin" in nav** refers to admin role, but "admin" in membership refers to the Director tier

---

## PROPOSED CLEAN MODEL

### Roles = WHO YOU ARE (organizational identity)

| Role | Purpose |
|------|---------|
| `public` | Not logged in |
| `member` | Standard authenticated user (replaces `student`) |
| `creator` | Content creator (replaces creator tier overlap) |
| `instructor` | Teacher/facilitator |
| `support_staff` | Support team |
| `moderator` | Content moderation |
| `admin` | Platform administrator |
| `executive_admin` | Executive authority |

### Tiers = WHAT YOU PURCHASED (commercial entitlement)

| Tier | Monthly | Purpose |
|------|---------|---------|
| `free` | $0 | Basic access |
| `creator` | $9.99 | Creator tools |
| `pro` | $29.99 | Advanced features |
| `studio` | $59.99 | Team/white-label |
| `directorial` | $99.99 | Full governance |

### Capabilities = WHAT YOU CAN DO (atomic permissions)

| Capability | Category |
|------------|----------|
| `nam.chat` | AI |
| `jamil.chat` | AI |
| `arena.run` | AI |
| `creator.publish` | Content |
| `music.create` | Content |
| `course.enroll` | Learning |
| `marketplace.sell` | Commerce |
| `sanctuary.journal` | Wellness |

### Access Policy = WHO GETS WHAT (configurable per feature)

Each feature has:
- `allowed_roles: [role1, role2, ...]` — organizational access
- `allowed_tiers: [tier1, tier2, ...]` — commercial access
- A user must satisfy BOTH to access the feature

---

## KEY RULES

1. **ROLE ≠ TIER** — Never use role to represent purchased access
2. **TIER ≠ ROLE** — Never use tier to represent organizational authority
3. **CAPABILITY** is the atomic unit, not the page
4. **NAVIGATION** is a UX concern, not an authorization concern
5. **ACCESS POLICY** is configurable per feature via admin UI
6. **DEFAULT** for new features: admin/executive_admin roles, no tiers, platform AI off

---

## MIGRATION PATH

This model requires:
1. Rename `student` → `member` (backward compatible with alias)
2. Rename tier `director` → `directorial` (to avoid confusion with executive_admin role)
3. Create `Capability` registry
4. Create `AccessPolicy` per capability
5. Build Feature Control Center UI
6. Update frontend to use unified access check (role AND tier)
7. Deprecate standalone role-based nav checks in favor of capability-based checks

---

## PHASE 17 UPDATE (2026-08-23) — REAL DEFINITIONS VERIFIED

- The real stored roles are `student(1), trial_pass(2), instructor(3), support_staff(4),
  oversight(5), admin(6), executive_admin(7)` (source: `backend/roles.py` +
  `frontend/src/lib/roles.js` — they mirror exactly). `public` (0) is the
  unauthenticated baseline, never a stored role.
- The real product tiers are `free(0), member(1), plus(2), pro(3), patron(4),
  executive(5)` (source: `security/feature_control.py TIER_RANK`,
  `routers/exec_control.py _BUILTIN_TIERS`, `frontend/src/lib/tiers.js`).
- **There is no `creator`, `studio`, or `director` tier.** Phase 17 normalized every
  registry `default_tiers` entry to real tiers and verified zero invented labels
  remain (see FEATURE_ACCESS_MATRIX.md).
- Role and tier remain independent: internal/proprietary features check ROLE first;
  commercial entitlements check TIER; funding (platform vs BYOK) is a separate
  decision enforced after authorization.
