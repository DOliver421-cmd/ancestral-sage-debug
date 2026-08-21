# MIGRATION PLAN — HOW EXISTING FUNCTIONALITY MOVES

This plan ensures no user loses access to any capability during consolidation. Every deprecated page gets a redirect. Every data model gets a migration path. Every API gets a sunset period.

---

## PHASE 0: PREPARATION (No User Impact)

### 0.1 Database Migration: Add Membership Fields

```python
# Add to users collection
{
    "membership": {
        "tier": "free",           # free | creator | pro | studio | director
        "billing_provider": None,  # lemon_squeezy | gumroad
        "billing_id": None,
        "current_period_end": None,
        "features": {}             # per-feature entitlement overrides
    }
}
```

**Migration script:** `backend/scripts/migrate_membership.py`
- Runs once
- Sets all existing users to `"tier": "free"`
- Users who paid via Lemon Squeezy or Gumroad get mapped to their paid tier
- Non-destructive — adds fields, doesn't remove anything

### 0.2 Entitlement Service

```python
# backend/services/entitlements.py
def get_user_entitlements(user: dict) -> dict:
    """Returns the full entitlement set for a user based on their tier."""
    tier = user.get("membership", {}).get("tier", "free")
    return MEMBERSHIP_MATRIX[tier]
```

This is the single source of truth for what a user can do. All pages query this.

### 0.3 Route Redirect Map

Every deprecated page gets a redirect in `App.js`:

| Old Route | New Route | Migration Type |
|-----------|-----------|---------------|
| `/store` | `/media` (Storefront tab) | Already done |
| `/admin/health-report` | `/system-health` | Already done |
| `/admin/tools` | `/admin/dashboard` | Already done |
| `/admin/office-control` | `/admin/office` | Already done |
| `/admin/exec-control` | `/admin/office` | Already done |
| `/dashboard/exec` | `/admin/command` | Already done |
| `/admin/system` | `/admin/command` | Already done |
| `/admin/director` | `/admin/command` | Already done |

**Redirect implementation:** React Router `Navigate` component, no server-side changes needed.

---

## PHASE 1: UI CONSOLIDATION (Week 1-2)

### 1.1 AppShell Navigation Update

**Current:** 20+ nav items scattered across sections
**Target:** 10 navigation domains

```
OLD NAV                          NEW NAV
─────────────────────────────────────────────────
Dashboard                →       Dashboard
AI Tutor                 →       NAM (AI tab)
AI Orchestrator          →       NAM (Orchestrator tab)
Helper                   →       NAM (Helper tab)
Site Guide               →       NAM (Guide tab)
Creator Studio           →       Create
Creator Courses          →       Create (Courses tab)
Creator Earnings         →       Create (Earnings tab)
Creator Lounge           →       Create (Lounge tab)
Creator PayoutDashboard  →       Create (Earnings tab)
Creator Profile          →       Profile
Creator ProfileEdit      →       Profile (Edit tab)
Publishing Studio        →       Publish
Book Publisher           →       Publish (Books tab)
More                     →       Community
MoreHub                  →       Community (Hub tab)
MoreChat                 →       Community (Chat tab)
Community                →       Community (Overview)
Store                    →       Marketplace
MediaStore               →       Marketplace (Media tab)
Modules                  →       Learn
Courses                  →       Learn (Courses tab)
Workshops                →       Learn (Workshops tab)
Plans                    →       Pricing
Sanctuary                →       Sanctuary
GamingArcade             →       Games
MusicStudio              →       Music
Guilds                   →       Community (Guilds tab)
```

### 1.2 Page Component Changes

No pages are deleted in Phase 1. They are **relocated** in navigation:

```jsx
// AppShell.jsx — new nav structure
const NAV_DOMAINS = [
    { key: 'dashboard', label: 'Dashboard', icon: '🏠', path: '/dashboard' },
    { key: 'nam', label: 'NAM', icon: '🧠', children: [
        { label: 'Chat', path: '/assistant' },
        { label: 'Orchestrator', path: '/orchestrator' },
        { label: 'Helper', path: '/helper' },
        { label: 'Site Guide', path: '/site-guide' },
    ]},
    { key: 'create', label: 'Create', icon: '✏️', children: [
        { label: 'Studio', path: '/creator/studio' },
        { label: 'Courses', path: '/creator/courses' },
        { label: 'Earnings', path: '/creator/earnings' },
    ]},
    { key: 'publish', label: 'Publish', icon: '📚', path: '/publishing' },
    { key: 'learn', label: 'Learn', icon: '🎓', path: '/modules' },
    { key: 'community', label: 'Community', icon: '👥', children: [
        { label: 'Hub', path: '/more/hub' },
        { label: 'Chat', path: '/more/chat' },
        { label: 'Guilds', path: '/guilds' },
    ]},
    { key: 'marketplace', label: 'Marketplace', icon: '🛒', children: [
        { label: 'Browse', path: '/store' },
        { label: 'Media', path: '/media' },
    ]},
    { key: 'sanctuary', label: 'Sanctuary', icon: '🧘', path: '/sanctuary' },
    { key: 'music', label: 'Music', icon: '🎵', path: '/music-studio' },
    { key: 'games', label: 'Games', icon: '🎮', path: '/gaming-arcade' },
];
```

### 1.3 Admin Nav Consolidation

```jsx
const ADMIN_NAV = [
    { label: 'Dashboard', path: '/admin/dashboard', icon: '📊' },
    { label: 'Business Office', path: '/admin/office', icon: '🏢' },
    { label: 'Command Center', path: '/admin/command', icon: '⚡' },
    { label: 'IAM Console', path: '/admin/iam', icon: '🔐' },
    { label: 'Payments', path: '/admin/payments', icon: '💰' },
    { label: 'Analytics', path: '/admin/analytics', icon: '📈' },
    { label: 'System Health', path: '/system-health', icon: '🏥' },
    { label: 'Sage Audit', path: '/admin/sage-audit', icon: '🔍' },
];
```

---

## PHASE 2: FEATURE CONSOLIDATION (Week 2-4)

### 2.1 Creator Pages Merge

**Current state:** 5 separate Creator pages
**Target state:** 1 Creator page with tabs

```
/creator (CreatorDashboard)
├── Overview tab        ← from CreatorLounge (342 lines)
├── Courses tab         ← from CreatorCourses (435 lines)
├── Earnings tab        ← from CreatorEarnings (320 lines) + CreatorPayoutDashboard (121 lines)
├── Audience tab        ← new (analytics from existing data)
└── Settings tab        ← from CreatorProfileEdit (241 lines)
```

**Redirect map:**
- `/creator/courses` → `/creator` (Courses tab)
- `/creator/earnings` → `/creator` (Earnings tab)
- `/creator/lounge` → `/creator` (Overview tab)
- `/creator/payouts` → `/creator` (Earnings tab)
- `/creator/profile/edit` → `/creator` (Settings tab)

**Data migration:** None needed — same API endpoints, just consolidated UI.

### 2.2 Publishing Pages Merge

**Current state:** PublishingStudio (388 lines), BookPublisher (214 lines), BookBuilder (341 lines)
**Target state:** 1 Publish page with tabs

```
/publish (PublishingStudio)
├── Books tab           ← from BookBuilder (341 lines)
├── Articles tab        ← from BookPublisher (214 lines) — repurposed
├── Media tab           ← existing media tools
├── Templates tab       ← existing template system
├── Scheduled tab       ← existing scheduling
├── Analytics tab       ← new (from existing data)
└── Distribution tab    ← existing distribution channels
```

### 2.3 More Help Center Split

**Current state:** MoreHelpCenter is 2369 lines — does everything
**Target state:** Split into focused pages

```
MORE HELP CENTER (2369 lines) splits into:

1. MoreHub (240 lines)     — community hub (unchanged)
2. MoreAdmin (204 lines)   — admin tools (unchanged)
3. MoreOps (922 lines)     — operations (unchanged)
4. AdminDashboard          — gains: broadcast, platform flags, recent activity
5. SystemHealth            — gains: system checks, incidents
6. NAM (Chat tab)          — gains: AI costs, gateway status, sage metrics
```

The 2369-line mega-page distributes its 28 API calls to the pages that own those domains.

### 2.4 Learning Pages Consolidation

**Current state:** Modules, Workshops, Certificates, Competencies, Attendance, Courses, Leaderboard
**Target state:** 1 Learn page with sub-routes

```
/learn
├── /learn/courses        ← from Modules + Courses
├── /learn/workshops      ← from Workshops
├── /learn/certificates   ← from Certificates
├── /learn/competencies   ← from Competencies
├── /learn/attendance     ← from Attendance
└── /learn/leaderboard    ← from Leaderboard
```

### 2.5 Community Consolidation

**Current state:** MoreHub, MoreChat, More, Community, Guilds
**Target state:** 1 Community page with tabs

```
/community
├── Hub tab              ← from MoreHub (240 lines)
├── Chat tab             ← from MoreChat (273 lines)
├── Guilds tab           ← from Guilds (723 lines)
└── Creators tab         ← from Creators (66 lines) + CreatorDiscovery
```

---

## PHASE 3: ENTITLEMENT ENFORCEMENT (Week 4-6)

### 3.1 Backend Entitlement Middleware

```python
# backend/middleware/entitlements.py
def require_tier(minimum_tier: str):
    """Decorator that checks user's membership tier."""
    tier_levels = {"free": 0, "creator": 1, "pro": 2, "studio": 3, "director": 4}
    
    def decorator(func):
        async def wrapper(request, *args, **kwargs):
            user = request.state.user
            user_tier = user.get("membership", {}).get("tier", "free")
            if tier_levels.get(user_tier, 0) < tier_levels.get(minimum_tier, 0):
                return {"error": "Upgrade required", "minimum_tier": minimum_tier}
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
```

### 3.2 Frontend Entitlement Hook

```jsx
// frontend/src/hooks/useEntitlements.js
export function useEntitlements() {
    const { user } = useAuth();
    const tier = user?.membership?.tier || 'free';
    const limits = MEMBERSHIP_MATRIX[tier];
    
    const canAccess = (feature) => limits.features[feature] || false;
    const getLimit = (feature) => limits.limits[feature] || 0;
    
    return { tier, canAccess, getLimit, limits };
}
```

### 3.3 Feature Gate Component

```jsx
// frontend/src/components/FeatureGate.jsx
function FeatureGate({ feature, children, fallback }) {
    const { canAccess } = useEntitlements();
    if (!canAccess(feature)) return fallback || <UpgradePrompt feature={feature} />;
    return children;
}
```

Usage:
```jsx
<FeatureGate feature="advanced_analytics">
    <AdvancedAnalyticsPanel />
</FeatureGate>
```

---

## PHASE 4: DATA MIGRATION (Week 6-8)

### 4.1 Publishing Content Migration

**Source:** Multiple publisher collections
**Target:** Unified `content` collection

```python
# backend/scripts/migrate_content.py
async def migrate_publishing_content():
    """Move all publishing data to unified content collection."""
    async for doc in db.books.find():
        await db.content.insert_one({
            "user_id": doc["author_id"],
            "type": "book",
            "title": doc["title"],
            "content": doc.get("content", ""),
            "metadata": doc,
            "status": doc.get("status", "draft"),
            "created_at": doc.get("created_at"),
        })
    # Similar for articles, newsletters, posts, media
```

### 4.2 Learning Progress Migration

**Source:** Separate course enrollment + competency tracking
**Target:** Unified `learning_progress` collection

```python
async def migrate_learning_data():
    """Consolidate all learning data into one collection."""
    async for enrollment in db.course_enrollments.find():
        await db.learning_progress.insert_one({
            "user_id": enrollment["user_id"],
            "type": "course",
            "item_id": enrollment["course_id"],
            "progress": enrollment.get("progress", 0),
            "status": enrollment.get("status", "enrolled"),
            "completed_at": enrollment.get("completed_at"),
        })
```

### 4.3 Community Data Migration

**Source:** Separate hub, chat, guild data
**Target:** Unified `community_activity` collection

```python
async def migrate_community_data():
    """Consolidate community data."""
    async for post in db.more_posts.find():
        await db.community_activity.insert_one({
            "user_id": post["author_id"],
            "type": "post",
            "hub_id": post.get("hub_id"),
            "content": post["content"],
            "reactions": post.get("reactions", {}),
            "created_at": post.get("created_at"),
        })
```

---

## PHASE 5: DEPRECATION (Week 8-10)

### 5.1 Deprecated Page Redirects

All old routes get permanent redirects:

```jsx
// App.js — deprecated routes
<Route path="/creator/courses" element={<Navigate to="/creator" replace />} />
<Route path="/creator/earnings" element={<Navigate to="/creator" replace />} />
<Route path="/creator/lounge" element={<Navigate to="/creator" replace />} />
<Route path="/publishing/books" element={<Navigate to="/publish" replace />} />
<Route path="/more" element={<Navigate to="/community" replace />} />
<Route path="/more/hub" element={<Navigate to="/community" replace />} />
<Route path="/more/chat" element={<Navigate to="/community" replace />} />
```

### 5.2 API Sunset

Deprecated API endpoints remain active for 90 days:

```python
# backend/routers/deprecated.py
@router.post("/books")
async def create_book_DEPRECATED(request: Request):
    """DEPRECATED: Use POST /content with type=book instead."""
    # Forward to new endpoint
    return await content_router.create_content(request, content_type="book")
```

### 5.3 Database Collection Sunset

Old collections remain read-only for 90 days, then are archived:

```python
# backend/scripts/archive_collections.py
async def archive_old_collections():
    """Move old collections to archive after 90-day sunset."""
    old_collections = ["books", "articles", "newsletters", "more_posts", "more_hubs"]
    for name in old_collections:
        cursor = db[name].find({})
        async for doc in cursor:
            await db.archive.insert_one({"original_collection": name, **doc})
        # Don't drop — just mark as archived
```

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| User loses access to a feature | Redirects ensure every old route still works |
| Data loss during migration | Migrations are additive — old collections remain |
| API breaks for external consumers | 90-day sunset with forwarding |
| Navigation confusion | Clear domain-based nav with breadcrumbs |
| Mobile experience degrades | Test responsive design at each phase |

---

## SUCCESS CRITERIA

- [ ] Every old route redirects to new location
- [ ] No 404 errors from deprecated pages
- [ ] All data migrated and verified
- [ ] Entitlements enforced server-side
- [ ] No user reports of missing features
- [ ] Navigation is intuitive (user testing)
- [ ] Page count reduced by 15-20%
- [ ] Code duplication reduced by 30%+
