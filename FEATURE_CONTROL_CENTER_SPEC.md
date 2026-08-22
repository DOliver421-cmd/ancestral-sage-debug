# FEATURE CONTROL CENTER — Specification

**Date:** August 22, 2026

---

## PURPOSE

A single admin page where the administrator can see every platform feature and configure:
1. WHO can access it (roles + tiers)
2. HOW it appears in navigation (visible/hidden/locked)
3. Whether platform AI is enabled for it
4. Usage limits

**One feature = one control record. No duplicate controls.**

---

## ROUTE

`/admin/features` (admin+ only)

---

## FEATURE REGISTRY

Every feature is defined in a single canonical registry:

```python
FEATURE_REGISTRY = [
    {
        "feature_id": "nam.chat",
        "name": "AI Tutor",
        "description": "Chat with NAM AI assistant",
        "category": "ai",
        "ecosystem": "NAM",
        "route": "/ai",
        "api_endpoints": ["/api/ai/tutor", "/api/nam/*"],
        "default_roles": ["member"],
        "default_tiers": ["free"],
        "platform_ai": True,        # platform-funded AI available
        "byok_allowed": True,       # user can use own key
        "usage_limit": None,         # None = unlimited (subject to gateway budget)
        "navigation_group": "NAM",
        "navigation_label": "AI Tutor",
        "navigation_description": "Chat with your AI assistant",
        "navigation_visible_by_default": True,
    },
    # ... one entry per feature
]
```

---

## UI LAYOUT

### Page Header
```
FEATURE CONTROL CENTER
Platform feature access configuration

[Feature Count: 42]  [Active: 38]  [Restricted: 4]
```

### Filter Bar
```
[All] [AI] [Create] [Learn] [Community] [Marketplace] [Music] [Games] [Admin]
[Search: _______________]
```

### Feature Card (per feature)
```
┌─────────────────────────────────────────────────────────────────┐
│ AI Tutor                                         [ON] [OFF]    │
│ Chat with NAM AI assistant                                     │
│                                                                │
│ CATEGORY: AI          ECOSYSTEM: NAM                           │
│ ROUTE: /ai            API: /api/ai/tutor                       │
│                                                                │
│ ACCESS                                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ROLES                          │ TIERS                     │ │
│ │ ☐ Public                       │ ☐ Free                    │ │
│ │ ☑ Member                       │ ☐ Creator                 │ │
│ │ ☐ Support Staff                │ ☐ Pro                     │ │
│ │ ☐ Moderator                    │ ☐ Studio                  │ │
│ │ ☐ Admin                        │ ☐ Director                │ │
│ │ ☐ Executive Admin              │                           │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                │
│ AI CONFIGURATION                                                │
│ Platform AI: [ON/OFF]    BYOK: [ON/OFF]                        │
│                                                                │
│ NAVIGATION                                                      │
│ Visible: [Yes/Locked/Hidden]    Group: [NAM]                   │
│                                                                │
│ USAGE LIMIT                                                     │
│ [Unlimited] or [___] requests per [hour/day/month]             │
│                                                                │
│ [Save Changes]                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Matrix View (toggle)
```
TIER ACCESS MATRIX
┌──────────────┬──────┬─────────┬─────┬───────┬──────────┐
│ Feature      │ Free │ Creator │ Pro │ Studio │ Director │
├──────────────┼──────┼─────────┼─────┼───────┼──────────┤
│ AI Tutor     │  ✓   │    ✓    │  ✓  │   ✓   │    ✓     │
│ Jamil        │      │         │  ✓  │   ✓   │    ✓     │
│ Arena        │      │         │     │       │    ✓*    │
│ Studio       │      │    ✓    │  ✓  │   ✓   │    ✓     │
│ Sanctuary    │      │         │  ✓  │   ✓   │    ✓     │
│ Band         │      │    ✓    │  ✓  │   ✓   │    ✓     │
└──────────────┴──────┴─────────┴─────┴───────┴──────────┘
* = exec-only, not a membership tier
```

### Role Matrix (toggle)
```
ROLE ACCESS MATRIX
┌──────────────┬────────┬────────┬──────────┬──────────┬───────┬───────┐
│ Feature      │ Public │ Member │ Support  │ Moderator│ Admin │ Exec  │
├──────────────┼────────┼────────┼──────────┼──────────┼───────┼───────┤
│ AI Tutor     │        │   ✓    │    ✓     │    ✓     │   ✓   │   ✓   │
│ Jamil        │        │        │          │          │   ✓   │   ✓   │
│ Arena        │        │        │          │          │       │   ✓   │
│ Modules      │   ✓    │   ✓    │    ✓     │    ✓     │   ✓   │   ✓   │
│ Marketplace  │   ✓    │   ✓    │    ✓     │    ✓     │   ✓   │   ✓   │
└──────────────┴────────┴────────┴──────────┴──────────┴───────┴───────┘
```

---

## BACKEND

### API Endpoints

```
GET  /api/features              — List all features with current config
GET  /api/features/:id          — Get single feature config
PUT  /api/features/:id          — Update feature config
GET  /api/features/matrix/tier  — Tier access matrix
GET  /api/features/matrix/role  — Role access matrix
```

### Storage

Feature configs stored in MongoDB `feature_configs` collection:
```json
{
    "feature_id": "nam.chat",
    "enabled": true,
    "allowed_roles": ["member", "admin", "executive_admin"],
    "allowed_tiers": ["free", "creator", "pro", "studio", "director"],
    "platform_ai": true,
    "byok_allowed": true,
    "usage_limit": null,
    "navigation_visible": true,
    "navigation_group": "NAM",
    "updated_by": "exec_admin_id",
    "updated_at": "2026-08-22T00:00:00Z"
}
```

### Default Behavior

When no config exists for a feature:
- `enabled`: true
- `allowed_roles`: from FEATURE_REGISTRY defaults
- `allowed_tiers`: from FEATURE_REGISTRY defaults
- `platform_ai`: from FEATURE_REGISTRY
- `navigation_visible`: from FEATURE_REGISTRY

---

## ENFORCEMENT LAYERS

1. **Frontend nav** — hides/shows nav items based on role + tier
2. **Frontend route** — TierGate + Protected check role/tier
3. **Backend route** — middleware checks role + tier against feature config
4. **API gateway** — platform AI toggle per feature

---

## MIGRATION

### Phase 1: Build Feature Registry + Control Center UI
- Create `FEATURE_REGISTRY` in `backend/routers/features.py`
- Create `/admin/features` page in frontend
- Wire API endpoints

### Phase 2: Wire Enforcement
- Update `accessGates.js` to use feature registry
- Update `Protected` component to check feature config
- Update `TierGate` to check feature config
- Add backend middleware for feature access

### Phase 3: Navigation Cleanup
- Rename confusing labels
- Remove duplicates
- Organize by user goal
- Separate admin nav from customer nav
