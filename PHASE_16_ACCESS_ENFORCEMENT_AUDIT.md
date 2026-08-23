# PHASE 16 — ACCESS ENFORCEMENT AUDIT

**Date:** August 23, 2026
**Status:** ENFORCEMENT IMPLEMENTED — see PHASE_16_VERIFICATION.md for evidence

*Prior versions of this file claimed the repository contained no source code. That was
false and is retracted.*

---

## THE GAP THAT WAS CLOSED

The Feature Control Center (`backend/routers/features.py`) wrote admin overrides to
`db.feature_configs`, but **no enforcement layer read them**. Toggling a feature in the
FCC changed the database and nothing else. This phase made the FCC the authoritative
control plane by adding a read-side enforcement path.

## ENFORCEMENT ARCHITECTURE (as implemented)

```
Admin/Exec → Feature Control Center UI → PUT /api/features/{id}
                                              ↓
                                       db.feature_configs (overrides)
                                              ↓
   ┌──────────────────────────────────────────┴──────────────────────────┐
   │ security/feature_control.py (HTTP middleware, every mapped request) │
   │   check_user_feature_access(db, user, path)                          │
   │     1. per-user exec override (revoke/grant)                         │
   │     2. AI access override ("revoke AI")                              │
   │     3. FCC config: enabled=false → 403 (everyone)                    │
   │        internal_only → 403 unless role rank ≥ allowed                │
   │        allowed_roles / allowed_tiers overrides → bind                │
   │     4. feature-tier requirement (existing authz matrix)              │
   └──────────────────────────────────────────┬──────────────────────────┘
                                              ↓
                    routers/exec_control.py ec_access_public()
                    (FCC DB overrides merged into frontend gate map)
                                              ↓
                    frontend accessGates.js → AppShell nav + App.js routes
```

## ENFORCEMENT MATRIX (decision-function verified)

| Path | Feature | Student | Instructor | Support | Admin | Exec |
|------|---------|---------|-----------|---------|-------|------|
| `/api/jamil/*` | nam.jamil (internal) | DENY 403 | DENY 403 | DENY 403 | ALLOW | ALLOW |
| `/api/competition/*` | games.arena (internal) | DENY 403 | DENY 403 | DENY 403 | DENY 403 | ALLOW |
| `/api/ai/orchestrator` | nam.orchestrator (internal) | DENY 403 | DENY 403 | DENY 403 | ALLOW | ALLOW |
| `/api/ai/helper` | nam.helper (customer) | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW |
| `/api/ai/helper` + `enabled=false` override | | DENY | DENY | DENY | DENY | DENY |
| `/api/ai/helper` + `allowed_roles=["admin"]` override | | DENY | DENY | DENY | ALLOW | ALLOW |
| `/api/ai/helper` + `allowed_tiers=["pro"]` override | | DENY (free) | DENY (free) | — | ALLOW (pro tier) | ALLOW |

Verified by `backend/tests/test_fcc_enforcement.py` (15/15 pass).

## SAFE-DEFAULT CONTRACT (preserved)

- Absent config == ALLOW (an untouched feature behaves exactly as before — no rollout risk).
- Registry defaults for **non-internal** features never gate by themselves.
- Registry defaults for **internal** features bind immediately (Jamil admin+, Arena exec)
  — that is the fail-closed classification the business rules require.
- Unknown feature / unreadable policy store on a mapped surface → 503, never allow.
- Role checks are rank-based (`roles.role_rank`), so `allowed_roles=["admin"]` admits
  `executive_admin` too, and `allowed_roles=["executive_admin"]` admits only exec.
- Tier checks are rank-based (`TIER_RANK`), and legacy labels (`creator/studio/director`)
  are normalized to real tiers (`member/plus/patron`) before enforcement.

## SURFACES DELIBERATELY NOT MAPPED

- `/api/admin/*` — already exempt from the feature middleware (admin routers enforce
  their own rank checks).
- Features with no real backend route (e.g. `nam.assistant`'s `/api/ai/assistant` does
  not exist in the route table) — frontend `BoundedAdmin` protection only.
- The `security/access_control/` gateway (31 exec controls) and this FCC layer are
  complementary: the gateway hard-gates admin/exec surfaces; the FCC gates product
  features. Neither was replaced.

## GAPS (documented, not papered over)

1. **Live HTTP matrix** — BLOCKED in sandbox (no MongoDB). `tests/live_fcc_matrix.py`
   is ready; run it in Railway.
2. **Per-feature AI quotas** — global gateway caps exist (`HOURLY_TOKEN_CAP`, per-user
   daily budget via `user_budget`); per-feature quotas are CONFIGURATION REQUIRED.
3. **`tests/test_access_gateway.py` 29/30** — `exec_pipeline` handler-derived-route gap,
   pre-existing (reproduced at HEAD before this phase's changes).
