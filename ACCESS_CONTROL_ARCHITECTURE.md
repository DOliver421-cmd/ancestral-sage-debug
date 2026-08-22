# ACCESS CONTROL ARCHITECTURE

**Date:** August 22, 2026

---

## CURRENT PROBLEM

Access control is scattered across 6 different systems:

| System | Where | Controls | Issue |
|--------|-------|----------|-------|
| `ROLE_RANK` | `lib/roles.js` + `backend/roles.py` | Route access | Only checks role, not tier |
| `TierGate` | `lib/tiers.js` + `App.js` | Feature access | Only checks tier, not role |
| `PAGE_ACCESS_REGISTRY` | `exec_control.py` | Nav visibility | Exec-controlled toggle only |
| `BoundedAdmin` | `App.js` | Route protection | Role-only, hardcoded per route |
| `Protected` | `App.js` | Auth + role | Role-only |
| `FeatureGate` | `FeatureGate.jsx` | UI gating | Tier-only via entitlements |

**Result:** An admin must edit 6 different places to change who can access one feature.

---

## PROPOSED UNIFIED MODEL

### Single Source of Truth

**Feature Registry** — one record per feature:
```python
{
    "feature_id": "nam.chat",
    "allowed_roles": ["member", "admin", "executive_admin"],
    "allowed_tiers": ["free", "creator", "pro", "studio", "director"],
    "enabled": True,
    "platform_ai": True,
    "navigation_visible": True,
}
```

### Single Access Check

```python
def can_access(user, feature_id):
    config = get_feature_config(feature_id)
    if not config.enabled:
        return False
    if user.role not in config.allowed_roles:
        return False
    tier = get_user_tier(user)
    if tier not in config.allowed_tiers:
        return False
    return True
```

### Frontend Equivalent

```javascript
function canAccess(user, featureId) {
    const config = getFeatureConfig(featureId);
    if (!config.enabled) return false;
    if (!config.allowed_roles.includes(user.role)) return false;
    const tier = getUserTier(user);
    if (!config.allowed_tiers.includes(tier)) return false;
    return true;
}
```

---

## LAYERS

### Layer 1: Navigation Visibility
- Controlled by `navigation_visible` in feature config
- Hides/shows nav items
- Does NOT prevent direct URL access

### Layer 2: Route Protection
- `Protected` component checks `canAccess(user, feature_id)`
- If denied, redirects to `/auth?returnTo=...`
- Replaces both `BoundedAdmin` and `TierGate`

### Layer 3: Backend Middleware
- API endpoints check `can_access(user, feature_id)`
- Returns 403 if denied
- Applied via decorator: `@require_feature("nam.chat")`

### Layer 4: AI Gateway
- `platform_ai` flag controls whether platform-funded AI is available
- If `platform_ai=False`, only BYOK is available
- If `byok_allowed=False`, no AI access at all

---

## ADMIN EXPERIENCE

**Before:** Edit App.js routes + AppShell nav + exec_control + TierGate + backend middleware = 5 places

**After:** Edit one feature card in Feature Control Center = 1 place

---

## MIGRATION FROM CURRENT SYSTEM

| Current System | Migration Path |
|---------------|----------------|
| `BoundedAdmin roles=[...]` | → Feature config `allowed_roles` |
| `Protected roles=[...]` | → Feature config `allowed_roles` |
| `TierGate feature="..."` | → Feature config `allowed_tiers` |
| `PAGE_ACCESS_REGISTRY` | → Feature config `navigation_visible` + `enabled` |
| `FeatureGate` | → Feature config `allowed_tiers` |
| Hardcoded nav checks (`hasRank`) | → Feature config `allowed_roles` |

---

## DEFAULT STATE (FAIL-CLOSED)

New features that aren't in the registry:
- `enabled`: false
- `allowed_roles`: [] (empty)
- `allowed_tiers`: [] (empty)
- `navigation_visible`: false
- `platform_ai`: false

Nothing works until an admin explicitly configures it.

---

## API

### Public Gate Map (for frontend shell)
```
GET /api/features/gate-map
→ { "nam.chat": { enabled: true, allowed_roles: [...], allowed_tiers: [...] }, ... }
```

### Admin CRUD
```
GET    /api/features              — list all
GET    /api/features/:id          — get one
PUT    /api/features/:id          — update one
GET    /api/features/matrix/tier  — tier matrix
GET    /api/features/matrix/role  — role matrix
POST   /api/features/:id/reset    — reset to defaults
```

### Backend Enforcement
```python
from features import require_feature

@router.get("/api/nam/chat")
async def nam_chat(user = Depends(current_user)):
    require_feature(user, "nam.chat")  # raises 403 if denied
    # ... handle request
```

---

## WHAT THIS REPLACES

| Old Pattern | New Pattern |
|-------------|-------------|
| `hasRank("admin")` in AppShell | Feature config `allowed_roles` |
| `<BoundedAdmin roles={["admin"]}>` | `require_feature(user, "admin.dashboard")` |
| `<TierGate feature="creator">` | Feature config `allowed_tiers` |
| `isPageEnabled(path)` from accessGates | Feature config `enabled` + `navigation_visible` |
| Manual nav visibility checks | Feature config `navigation_visible` |
