# Executive Feature Toggle Protocol

## Principle

No feature, page, API route, or revenue path is ever deleted, stubbed, or hardcoded-disabled.
Runtime availability is governed exclusively by database-backed executive toggles.

## Architecture

### Backend Enforcement

| Store | Purpose | Toggle Endpoint |
|-------|---------|-----------------|
| `db.platform_flags` | Feature flags (e.g. `ai_chat`, `courses`, `payouts`) | `POST /api/exec/control/feature-flag` |
| `db.page_access` | Page visibility + role overrides | `POST /api/exec/control/access` |
| `db.feature_configs` | FCC per-feature overrides (enabled, roles, tiers) | `POST /api/features/config` |

**Enforcement module:** `backend/security/feature_control.py`  
**Control panel:** `backend/routers/exec_control.py`  
**Safe-default contract:** absent config == allow. Only an explicit `enabled: false` written by an executive blocks access.

### Frontend Gate

| Component | Role |
|-----------|------|
| `AccessGate.jsx` | Wraps `<Routes>`; renders offline page when exec disables current route |
| `accessGates.js` | Fetches gate map from `/exec/control/access/public`; maps pathnames to page keys |
| `navAccess.js` | Pure tier-first nav visibility decision (sidebar + router share logic) |
| `useFeatureToggle.js` | React hook for component-level feature flag checks |

### Restored Pages — Toggle Integration

All 9 pages deleted in prior sessions are restored and registered in all three layers:

| Page | Route | PAGE_ACCESS_REGISTRY Key | Frontend PATH_POLICIES | PAGE_API_PATHS |
|------|-------|--------------------------|------------------------|----------------|
| `ExecBusinessOffice` | `/admin/office` | `exec-business-office` | `/admin/office` → `exec-business-office` | `/api/admin/users`, `/api/exec/control/audit` |
| `SiteControlPanel` | `/admin/control` | `site-control` | `/admin/control` → `site-control` | `/api/admin/control-panel`, `/api/admin/platform/flags` |
| `FeatureControlCenter` | `/admin/features` | `feature-control` | `/admin/features` → `feature-control` | `/api/features` |
| `ExecutiveDirectorDashboard` | `/admin/director` | `director` | `/admin/director` → `director` | `/api/admin/stats`, `/api/incidents`, `/api/admin/users`, `/api/admin/recent-activity`, `/api/admin/platform/flags` |
| `AccountControls` | `/admin/accounts` | `account-controls` | `/admin/accounts` → `account-controls` | `/api/admin/users` |
| `CreatorPayoutDashboard` | `/creator/payouts` | `creator-payouts` | `/creator/payouts` → `creator-payouts` | `/api/creator/payouts`, `/api/creator/payout-summary`, `/api/creator/bank-account` |
| `PartnershipDiscounts` | `/partnership/discounts` | `partnership-discounts` | `/partnership/discounts` → `partnership-discounts` | `/api/partnership/status` |
| `MissingKameron` | `/missing-kameron` | `missing-kameron` | `/missing-kameron` → `missing-kameron` | none (static page) |
| `TrashPantheon` | `/trash-pantheon`, `/trash` | n/a (public) | n/a | none (static page) |

### Toggle Behavior

- **Enabled by default.** All restored pages and features default to `enabled: true`.
- **Executive-only write.** Only `executive_admin` role can flip toggles via the control panel.
- **Audit logged.** Every toggle change writes to the executive audit trail with actor, timestamp, and reason.
- **Frontend + backend enforced.** The `AccessGate` wrapper hides disabled pages from the router; the `feature_control.py` middleware returns `403` for disabled API paths.

## Executive Control Surfaces

| Surface | Path | Purpose |
|---------|------|---------|
| Executive Command Center | `/admin/command` | Primary executive dashboard |
| Sovereign Command | `/admin/exec-control` | Feature flags, tiers, matrices |
| Site Control Panel | `/admin/control` | Platform flags, budgets, broadcasts |
| Feature Control Center | `/admin/features` | FCC registry + per-feature overrides |
| Business Office | `/admin/office` | User controls, audit, budgets |
| Director Dashboard | `/admin/director` | Stats, incidents, users, flags |
| Account Controls | `/admin/accounts` | User management |
| Creator Payouts | `/creator/payouts` | Creator payout visibility |
| Partnership Discounts | `/partnership/discounts` | Partnership pricing |

## Prohibited Patterns

- ❌ Deleting files to "clean up" duplicates
- ❌ Labeling features "coming soon" or "under construction"
- ❌ Hardcoding `disabled={true}` in frontend without a toggle backend
- ❌ Using audit classifications as justification for removal
- ✅ Restoring deleted code from git history
- ✅ Adding pages to the toggle registry with default `enabled: true`
- ✅ Documenting toggle state in all reports
