# PHASE 17 — BUSINESS-SAFE ACCESS, VISUAL LIFE & CONTROL FOUNDATION — VERIFICATION

**Date:** August 23, 2026
**Status:** AUDIT COMPLETE + TARGETED FIXES APPLIED; production verification BLOCKED in sandbox

---

## WHAT WAS VERIFIED (with evidence)

### 17A — Feature classifications (VERIFIED)
- `FEATURE_REGISTRY` contains **48 features**; every feature now carries all 9 required
  fields (`enabled`, `internal_only`, `customer_access_allowed`, `cost_bearing`,
  `allowed_roles`, `allowed_tiers`, `navigation_visible`, `platform_ai`, `byok_allowed`).
- **Fixed:** `nam.byok` was missing 3 classification fields — added
  (`internal_only=False`, `customer_access_allowed=True`, `cost_bearing=False`).
- **Fixed:** ~30 features had invented tier labels (`creator/studio/director`) in their
  source `default_tiers` — normalized to real tiers (`member/plus/patron`). Re-scan:
  **zero missing fields, zero invented labels** across all 48 entries.
- 8 internal-only, 9 customer cost-bearing, 31 customer free (see FEATURE_ACCESS_MATRIX.md).

### 17B — Routes/APIs vs registry (VERIFIED, with gaps listed)
- Corrected 4 stale `api_endpoints` in the registry to the **real route table**
  (verified by grep):
  - `nam.chat`: `/api/ai/tutor` (nonexistent) → `/api/ai/chat` + `/api/nam`
  - `create.social`: `/api/community/publish` → `/api/ai/social-blast` (routers/chat.py)
  - `create.ghost`: `/api/studio/ghost` (nonexistent) → page calls `/api/ai/chat`
  - `learn.adaptive`: `/api/lms/adaptive` → `/api/adaptive/me` (routers/admin.py)
  - `sanctuary.reflection`: `/api/sovereign` (exec-gated; not the sanctuary surface) → `[]`
- Coverage confirmed for every customer cost-bearing surface (FCC / exec flag / router
  rank). Gaps documented in FEATURE_ACCESS_MATRIX.md (adaptive gate, assistant no-route,
  sanctuary redirect, pantheon `/trash` route label, ghost roles).

### 17C — Internal-only enforcement (VERIFIED at decision level)
- Arena: FCC (exec rank 7 only) **+** `competition.py` `_require_rank("executive_admin")`.
- Jamil: FCC (admin+), Orchestrator: FCC (admin+), both backed by router auth.
- Admin surfaces: `/api/admin/*` exempt + admin.py `_require_rank("admin")` +
  exec_command.py `_require_rank("executive_admin")` + AccessGateway (31 controls).
- 15/15 decision-level tests in `tests/test_fcc_enforcement.py` (Jamil/Arena/Orchestrator
  matrix: students→DENY, admin/exec→ALLOW as classified).

### 17D — Cost-bearing AI enforcement (PARTIALLY VERIFIED)
- Access checks run in HTTP middleware **before** any route handler / provider
  invocation; BYOK resolution happens after authorization (never before).
- Gateway budget guards exist (`HOURLY_TOKEN_CAP`, per-user daily budget via
  `user_budget`); per-feature quotas = **CONFIGURATION REQUIRED** (not invented).
- `learn.adaptive` API is auth-only (rule-based, no provider call) — flagged for
  executive decision, not silently reclassified.

### 17E — Role/tier separation (VERIFIED)
- Real roles (7 stored) and real tiers (6) verified against `roles.py`, `roles.js`,
  `tiers.js`, `TIER_RANK`, `_BUILTIN_TIERS`. No invented names remain.

### 17F — Navigation (VERIFIED + fixed)
- Arena: only in admin-only Director section (AppShell line 403), `BoundedAdmin exec`
  route, FCC exec-only, hidden from customer nav by gate map.
- **Fixed:** internal-only registry defaults now flow into the frontend gate map
  (`ec_access_public`), so Jamil / Admin Assistant / Orchestrator are hidden from
  non-authorized users' nav (unit-tested) — previously they were visible to all students.
- **Fixed:** removed dead `/orchestrator` nav link (route never existed; the
  OrchestratorChat component is the Council/Sage page at `/council` — the canonical home).

### 17G — Feature Control Center drives enforcement (VERIFIED)
- FCC DB overrides are read by the enforcement middleware (`load_fcc_config`), merged
  into the frontend gate map, and normalize roles/tiers on write.
- Tests: `tests/test_fcc_enforcement.py` **15/15 PASS**; `tests/test_integration.py`
  **42/42 PASS**; server boots; gate-map + features endpoints return 200.

### 17H/17I — Image capability + asset plan (VERIFIED audit, plan produced)
- DALL-E 3 exists only inside `tools/architect_tools.py`, dispatched through the
  feature-gated AI handler — no public generate endpoint.
- IMAGE_ASSET_PLAN.md produced: 14 purposeful assets mapped to canonical destinations,
  static-first, no generation executed, no new services.

---

## WHAT WAS CHANGED

| File | Change |
|------|--------|
| `backend/routers/features.py` | `nam.byok` classification fields; 5 stale `api_endpoints` corrected; all `default_tiers` normalized to real tiers |
| `backend/routers/exec_control.py` | `ec_access_public` now pushes registry defaults for **internal-only** features into the gate map (nav hiding, admin-override wins) |
| `frontend/src/components/AppShell.jsx` | Removed dead `/orchestrator` nav link |
| `backend/tests/test_fcc_enforcement.py` | Added gate-map assertions for internal-only nav hiding |
| New docs | BUSINESS_ACCESS_POLICY.md, FEATURE_ACCESS_MATRIX.md, IMAGE_ASSET_PLAN.md, PHASE_17_VERIFICATION.md + update sections in 7 existing docs |

## WHAT WAS NOT CHANGED

- No features deleted or disabled (no broad lockdown).
- No navigation labels renamed except the dead-link removal (renames documented in
  NAVIGATION_LABEL_AUDIT.md, pending review).
- No image generation executed. No external image service added.
- No provider, gateway, BYOK, or budget architecture replaced.
- No pricing/quota invented.

## WHAT REMAINS BLOCKED

| Item | Blocker | How to unblock |
|------|---------|----------------|
| Live HTTP access matrix | No MongoDB in sandbox (`MONGO_URL not set`) | Run `cd backend && python3 -m server` + `python3 tests/live_fcc_matrix.py` in Railway/prod (seeds marked test users, cleans up) |
| Provider connectivity (11 providers) | No API keys in sandbox | Set provider keys in Railway Variables |
| Browser E2E | No browser automation installed (not introduced) | Manual browser pass or existing tooling |
| Railway deploy issue | No Railway access from this sandbox | User checks Railway build logs; env completeness: `MONGO_URL`, `JWT_SECRET`, provider keys, `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY` |
| `tests/test_access_gateway.py` 29/30 | `exec_pipeline` handler-derived-route gap — **pre-existing** (reproduced at git HEAD) | Add handler-derived rank for `/api/exec/pipeline/*` or widen registry pattern |

## TEST COUNTS (exact)

- `tests/test_fcc_enforcement.py` — **15/15 PASS**
- `tests/test_integration.py` — **42/42 PASS**
- `tests/test_access_gateway.py` — **29/30** (1 pre-existing failure, above)
- `tests/test_critical_paths.py` — not run (requires pytest, not installed; pre-existing)

## REQUIRES EXECUTIVE DECISION

1. **`learn.adaptive`** — map `/api/adaptive/me` into the FCC or reclassify as
   free/rule-based (currently auth-only, no feature gate; rule-based, no provider cost).
2. **`create.ghost` roles** — registry says `student+`, page is admin-gated
   (`routers/abo.py`). Reconcile: customer tier feature or internal admin tool?
3. **Sanctuary** — `/sanctuary` currently redirects to `/helper`. Restore a real
   Sanctuary page/API or keep the redirect (registry now says "no dedicated API").
4. **Per-feature AI quotas** — approve a quota model (currently global caps only).
5. **Image batch** — approve the 7–9 one-time P0 DALL-E images (~$0.30) or keep static
   CSS/SVG only.

## NOT CLAIMED

- Not claimed: "site is production-ready", "nav is finished", "all AI works",
  "dashboard verified in browser". Those require production/browser evidence
  (see BLOCKED).
