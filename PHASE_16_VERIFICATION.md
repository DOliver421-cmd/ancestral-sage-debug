# PHASE 16 — ACCESS, TIER, ROLE, COST & NAVIGATION ENFORCEMENT — VERIFICATION

**Date:** August 23, 2026
**Status:** ENFORCEMENT IMPLEMENTED + VERIFIED AT DECISION-FUNCTION LEVEL; live HTTP matrix BLOCKED in sandbox (no MongoDB)

---

## CORRECTION TO PRIOR REPORTS

Earlier Phase 16 documents claimed "zero source code" in this repository. **That was
false** (a broken glob). The codebase contains 238 `.py` files and tens of thousands of
frontend files. Prior documents carrying that claim are retracted.

Earlier docs also claimed `backend/routers/features.py`,
`frontend/src/pages/FeatureControlCenter.jsx`, `backend/ai/hybrid_nam/persistence.py` and
`store.py` were "sandbox only, never committed." **That was also false** — all four are
tracked in git (verified `git ls-files` + `git show --stat HEAD`).

---

## WHAT THIS PHASE IMPLEMENTED

The Feature Control Center (`routers/features.py`) previously wrote admin overrides to
`db.feature_configs`, but **nothing enforced them**. This phase closed that gap with the
minimum authoritative-enforcement changes:

### 1. Backend enforcement reads the FCC (`backend/security/feature_control.py`)

- Added `FCC_FEATURE_API_PATHS` — feature_id → verified API prefixes (checked against the
  live route table 2026-08-23):

  | feature_id | API surface | Registry classification |
  |------------|-------------|------------------------|
  | `nam.jamil` | `/api/jamil/*` | internal_only, roles `[admin, executive_admin]` |
  | `games.arena` | `/api/competition/*` | internal_only, roles `[executive_admin]` |
  | `nam.orchestrator` | `/api/ai/orchestrator` | internal_only, roles `[admin, executive_admin]` |
  | `nam.helper` | `/api/ai/helper` | customer-accessible, cost-bearing |
  | `nam.council` | `/api/ai/sage` | customer-accessible (tiers pro+) |
  | `nam.chat` | `/api/ai/chat`, `/api/nam` | customer-accessible, cost-bearing |
  | `nam.site_guide` | `/api/site-guide` | customer-accessible |

- Added `load_fcc_config()` — effective config = registry default + `db.feature_configs`
  override (async, fail-closed on unavailable policy store).
- Added an FCC decision block inside `check_user_feature_access()` (the exact function the
  HTTP middleware calls), which:
  - **`enabled=false` → 403 for EVERYONE**, including admins/execs (runs before the
    staff tier-exemption so staff cannot reach a disabled feature).
  - **`internal_only=true` → 403 unless the user's role rank ≥ the lowest allowed role**
    (rank-based, so `admin` also admits `executive_admin`).
  - **`allowed_roles` override → binds** (rank-based) only when an admin explicitly set it.
  - **`allowed_tiers` override → binds** (rank-based) only when an admin explicitly set it.
  - Registry defaults for *non-internal* features never gate by themselves (no surprise
    lockouts — preserves the safe-default contract).
- Safe-default contract preserved: absent config == allow; unknown feature == deny
  (503, mapped surface only).

### 2. Middleware wiring (`backend/server.py`)

- The per-user enforcement middleware now triggers on FCC-mapped paths too
  (`feature_for_path(path) or fcc_feature_for_path(path)`), and the fail-closed 503
  branch covers FCC-mapped paths.

### 3. FCC control plane fixes (`backend/routers/features.py`)

- **Fixed a real bug:** `get_feature_config()` had a duplicated block and a broken
  asyncio dance that made DB overrides **never load** — the admin UI could not see its
  own saved changes. Replaced with a clean sync helper + `get_feature_config_async()`;
  all endpoints now use the async variant.
- **Fixed the tier model:** the FCC used invented tier labels
  (`free, creator, pro, studio, director`). The real product tiers are
  `free, member, plus, pro, patron, executive` (verified against
  `security/feature_control.py TIER_RANK`, `routers/exec_control.py _BUILTIN_TIERS`,
  `frontend/src/lib/tiers.js`). Added `REAL_TIERS` + `LEGACY_TIER_MAP`
  (`creator→member, studio→plus, director→patron`) and `normalize_tiers()`; stored and
  enforced configs can never reference a nonexistent tier.
- **Fixed the role model:** FCC role matrix now uses all 7 real stored roles
  (`student, trial_pass, instructor, support_staff, oversight, admin, executive_admin`).
- `update_feature` normalizes/validates roles + tiers on write and returns a JSON result.

### 4. Frontend nav wiring (`routers/exec_control.py` + `FeatureControlCenter.jsx`)

- `ec_access_public` (the gate map the frontend `accessGates.js` consumes) now merges
  **explicit FCC DB overrides** (`enabled`, `allowed_roles`) into the pages map, so an
  admin toggle in the Feature Control Center actually hides/disables the nav entry and
  route. Registry defaults alone never gate the nav (no surprise lockouts).
- `FeatureControlCenter.jsx` `ALL_TIERS`/`ALL_ROLES` updated to the real tier/role names.

---

## TEST EVIDENCE

### New: `backend/tests/test_fcc_enforcement.py` — 15/15 PASS

Runs without pytest/MongoDB (stdlib-only, fake async DB) and exercises the exact
decision functions the HTTP middleware calls:

| Test | Result |
|------|--------|
| FCC path mapping (jamil/arena/orchestrator/helper/sage/chat/nam/site-guide) | PASS |
| Registry default merge (jamil internal_only, roles) | PASS |
| DB override merge + legacy tier normalization | PASS |
| **Jamil: student/trial/instructor/support/oversight → block; admin/exec → pass** | PASS |
| **Arena: student→admin all → block; executive_admin → pass** | PASS |
| Orchestrator: student block, admin pass | PASS |
| Helper: open to students by default (no lockout) | PASS |
| `enabled=false` blocks student **and admin and exec** | PASS |
| `allowed_roles=["admin"]` override: student/support block, admin/exec pass (rank-based) | PASS |
| `allowed_tiers=["pro"]` override: free/member block, pro/patron pass | PASS |
| Legacy tier label `["creator"]` admits member users (normalization in enforcement) | PASS |
| Unmapped paths pass (safe default) | PASS |
| `ec_access_public` merges FCC overrides into the frontend gate map | PASS |

### Existing suites

| Suite | Result | Note |
|-------|--------|------|
| `tests/test_integration.py` | **42/42 PASS** | run after all changes |
| `tests/test_access_gateway.py` | 29/30 | the 1 failure (`exec_pipeline` handler-derived route) is **pre-existing** — reproduced identically at `git HEAD` in a throwaway worktree before my changes |
| `tests/test_critical_paths.py` | not run | requires `pytest` (not installed in sandbox); pre-existing |

### Server boot

- `python3 -m server` boots cleanly with all changes; `/api/exec/control/access/public`
  and `/api/features/gate-map` respond 200.

---

## BLOCKED IN SANDBOX (honest)

| Item | Why |
|------|-----|
| **Live HTTP access matrix** (`tests/live_fcc_matrix.py`, ready to run) | No MongoDB in this sandbox (`MONGO_URL not set — database disabled`), and `current_user` requires `db.users`. Run in Railway/prod: `cd backend && python3 -m server` then `python3 tests/live_fcc_matrix.py` (seeds 4 clearly-marked test users, verifies the matrix, cleans up). |
| Provider connectivity for the AI gateway | No provider API keys in the sandbox; health endpoint reports `key_present: false` for all. Depends on Railway env. |
| Browser E2E | No browser automation tooling installed; not introduced per standing constraint. |

---

## FINAL STATUS

| Category | Item | Status |
|----------|------|--------|
| VERIFIED | FCC enforcement (internal_only, enabled, role/tier overrides) at decision-function level | ✅ 15/15 unit tests |
| VERIFIED | Arena executive-only at API layer (FCC + competition.py `_require_rank`) | ✅ |
| VERIFIED | Jamil admin+ at API layer | ✅ |
| VERIFIED | No lockout of non-internal features by registry defaults | ✅ |
| VERIFIED | FCC admin UI reads back its own saved overrides | ✅ (async loader fix) |
| VERIFIED | Real tier/role names in FCC (no invented labels) | ✅ |
| VERIFIED | FCC overrides reach the frontend gate map | ✅ unit test |
| VERIFIED | Existing suites still pass (42/42) | ✅ |
| PARTIALLY VERIFIED | End-to-end HTTP enforcement | decision layer verified; HTTP layer blocked by no-Mongo sandbox |
| BLOCKED | Live HTTP matrix | no MongoDB in sandbox — runnable in Railway (`tests/live_fcc_matrix.py`) |
| BLOCKED | Provider connectivity audit | no API keys in sandbox — needs Railway env |
| NOT IMPLEMENTED | Budget/rate-limit guard for cost-bearing AI beyond existing gateway caps | gateway already has `HOURLY_TOKEN_CAP` + per-user daily budget (`user_budget`); per-feature quotas = CONFIGURATION REQUIRED (none exist) |
| NOT IMPLEMENTED | Navigation label rewrite / sidebar consolidation | deferred by design (Phase 16 is enforcement, not nav redesign) |

---

## REMAINING GAPS

| Issue | Impact | Root cause | Recommended fix | Next test |
|-------|--------|------------|-----------------|-----------|
| Live HTTP matrix unverified in sandbox | Enforcement proven at decision layer, not over HTTP | No MongoDB in sandbox | Run `tests/live_fcc_matrix.py` in Railway/prod | HTTP 403/200 matrix |
| `tests/test_access_gateway.py` 1 failure | Access-gateway route table has a gap for `/api/exec/pipeline/` | Pre-existing; route pattern vs handler-derived rank mismatch (not caused by this phase) | Add handler-derived requirement for exec_pipeline routes or widen the registry pattern | rerun suite |
| No per-feature AI quotas | Platform-funded AI cost is capped globally, not per feature | Quotas were never built | Design quota fields in FCC (CONFIGURATION REQUIRED) | budget-exhaustion test |
| Railway env completeness (`MONGO_URL`, `JWT_SECRET`, provider keys, `PROVIDER_KEY_ENCRYPTION_SECRET`, `AUDIT_ENCRYPTION_KEY`) | Production enforcement/persistence/AI unavailable until set | External to repo | Set in Railway Variables | live matrix in prod |

*This report replaces the retracted "no source code" versions of the Phase 16 documents.*
