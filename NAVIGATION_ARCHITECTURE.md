# NAVIGATION ARCHITECTURE

**Date:** August 21, 2026
**Status:** Design complete, ready for implementation

---

## PRINCIPLE

One canonical home for every capability. Other areas may reference it, but each capability has exactly one place to go.

---

## SIDEBAR NAVIGATION (AppShell)

### Student View
```
┌─────────────────────┐
│ 🏠 Dashboard        │
│ 🧠 AI Console       │
│ 📚 Learn            │
│    ├── Courses      │
│    ├── Labs         │
│    └── Portfolio    │
│ 👥 Community        │
│    ├── Feed         │
│    ├── Chat         │
│    └── Needs        │
│ 🎵 Music            │
│    └── Store        │
│ ⚔️ Games            │
│    ├── Arcade       │
│    └── Leaderboard  │
│ 🏛️ Sanctuary        │
│    └── Protocols    │
│ ⚙️ Settings         │
│ 💳 Billing          │
└─────────────────────┘
```

### Creator View (adds)
```
┌─────────────────────┐
│ ... Student items   │
│ ─────────────────── │
│ ✍️ Create           │
│    ├── Write        │
│    ├── Produce      │
│    └── Publish      │
│ 💰 Earnings         │
│    ├── Dashboard    │
│    ├── Courses      │
│    └── Payouts      │
│ 📊 Analytics        │
└─────────────────────┘
```

### Admin View (adds)
```
┌─────────────────────┐
│ ... Creator items   │
│ ─────────────────── │
│ ⚙️ Admin            │
│    ├── Dashboard    │
│    ├── IAM Console  │
│    ├── Payments     │
│    ├── Scholarships │
│    ├── Analytics    │
│    ├── Audit        │
│    └── Health       │
└─────────────────────┘
```

### Executive View (adds)
```
┌─────────────────────┐
│ ... Admin items     │
│ ─────────────────── │
│ 👑 Executive        │
│    ├── Command      │
│    ├── Office       │
│    ├── Reports      │
│    └── Control      │
└─────────────────────┘
```

---

## HEADER NAVIGATION (Top Bar)

```
┌──────────────────────────────────────────────────────────────┐
│ [Logo] M.O.R.E.    [Search]    [Notifications]  [Profile]  │
└──────────────────────────────────────────────────────────────┘
```

### Quick Actions (header)
- Search (global)
- Notifications (bell)
- Profile dropdown
- Theme toggle (dark/light)

---

## PAGE ROUTES (canonical homes)

### Public
| Route | Page | Purpose |
|-------|------|---------|
| `/` | Landing | Main entry point |
| `/login` | Login | Authentication |
| `/register` | Register | Account creation |
| `/plans` | Plans | Membership plans |
| `/courses` | Courses | Public course listing |
| `/creators` | Creators | Creator directory |
| `/store` | Media Store | Media marketplace |
| `/help-center` | Help Center | Support resources |
| `/terms` | Terms | Legal terms |
| `/privacy` | Privacy | Privacy policy |

### Authenticated (Student)
| Route | Page | Purpose |
|-------|------|---------|
| `/dashboard` | Student Dashboard | Personal hub |
| `/ai` | AI Console | AI assistants |
| `/modules` | Courses | Course catalog |
| `/labs` | Labs | Lab simulations |
| `/competencies` | Competencies | Skill tracking |
| `/certificates` | Certificates | Achievements |
| `/portfolio` | Portfolio | Work showcase |
| `/more` | Community Hub | Social feed |
| `/more/chat` | Community Chat | Chat rooms |
| `/arcade` | Games | Arcade games |
| `/leaderboard` | Leaderboard | Rankings |
| `/settings` | Settings | Account settings |
| `/billing` | Billing | Subscriptions |

### Creator
| Route | Page | Purpose |
|-------|------|---------|
| `/studio` | Publishing Studio | Content creation |
| `/studio/video-presenter` | Video Presenter | Video scripts |
| `/creator/dashboard` | Creator Dashboard | Creator hub |
| `/creator/courses` | Creator Courses | Course management |
| `/creator/earnings` | Creator Earnings | Revenue tracking |
| `/creator/:slug` | Creator Profile | Public profile |
| `/creator/profile/edit` | Profile Editor | Edit profile |
| `/playlist/dashboard` | Playlists | Playlist management |
| `/creator-lounge` | Creator Lounge | Collaboration |

### Admin
| Route | Page | Purpose |
|-------|------|---------|
| `/admin` | Admin Dashboard | Admin hub |
| `/admin/iam` | IAM Console | User management |
| `/admin/payments` | Admin Payments | Payment admin |
| `/admin/prices` | Platform Prices | Price config |
| `/admin/billing` | Billing Admin | Billing ops |
| `/admin/scholarships` | Scholarships | Scholarship mgmt |
| `/admin/analytics` | Analytics | Program analytics |
| `/admin/audit` | Audit Log | Audit trail |
| `/admin/moderation` | Moderation | Content moderation |
| `/admin/bridge` | AI Team Bridge | Persona dispatch |
| `/admin/aawab` | AAWAB | Agent wellness |
| `/admin/health` | System Health | Health checks |
| `/admin/tools` | Admin Tools | Sites, inventory |

### Executive
| Route | Page | Purpose |
|-------|------|---------|
| `/admin/command` | Executive Command Center | Mission control |
| `/admin/office` | Exec Business Office | Exec controls |
| `/admin/office-control` | ABO Config | Office config |
| `/admin/exec-report` | Executive Site Report | Site health |
| `/admin/sage-audit` | Sage Audit | AI audit |
| `/admin/control` | Site Control Panel | Feature flags |
| `/admin/providers` | Provider Gateway | AI providers |

### Sanctuary
| Route | Page | Purpose |
|-------|------|---------|
| `/ascension-protocols` | Ascension Protocols | Content creation |
| `/vonns-saga` | Vonns Saga | Narrative creation |
| `/trash` | Trash Pantheon | Brainstorming |
| `/elder-council` | Elder Council | Council chat |

### Competition
| Route | Page | Purpose |
|-------|------|---------|
| `/arena` | Competition Arena | Multi-persona |
| `/arcade` | Arcade | Games |
| `/scholarships/apply` | Scholarship Apply | Apply |
| `/sponsor` | Sponsor Scholarship | Sponsor |

---

## REDIRECT MAP

Old routes that redirect to new canonical homes:

| Old Route | New Route | Reason |
|-----------|-----------|--------|
| `/assistant` | `/ai?persona=assistant` | AI Console |
| `/orchestrator` | `/ai?persona=orchestrator` | AI Console |
| `/helper` | `/ai?persona=helper` | AI Console |
| `/site-guide` | `/ai?persona=guide` | AI Console |
| `/creative-partner` | `/ai?persona=creative` | AI Console |
| `/jamil` | `/ai?persona=jamil` | AI Console |
| `/ghost-producer` | `/studio?tab=produce` | Publishing Studio |
| `/social/publish` | `/studio?tab=publish` | Publishing Studio |
| `/app/more` | `/more` | Community Hub |
| `/community` | `/more` | Community Hub |
| `/more/admin` | `/more?tab=moderation` | Community Hub |
| `/more/ops` | `/more?tab=operations` | Community Hub |
| `/creator/courses` | `/creator/dashboard?tab=courses` | Creator Dashboard |
| `/creator/earnings` | `/creator/dashboard?tab=earnings` | Creator Dashboard |
| `/creator/profile/edit` | `/creator/dashboard?tab=profile` | Creator Dashboard |
| `/payment/history` | `/billing?tab=history` | Billing |
| `/payment/success` | `/billing?tab=success` | Billing |
| `/payment/cancel` | `/billing?tab=cancel` | Billing |
| `/admin/tools` | `/admin` | Admin Dashboard |
| `/admin/exec-control` | `/admin/office` | Exec Business Office |
| `/admin/office-control` | `/admin/office` | Exec Business Office |
| `/admin/system` | `/admin/command` | Exec Command Center |
| `/admin/director` | `/admin/command` | Exec Command Center |
| `/admin/health-report` | `/admin/health` | System Health |

---

## BREADCRUMB TRAIL

Every page shows its location in the hierarchy:

```
Home > Community > Feed
Home > AI Console > Tutor
Home > Create > Write
Home > Admin > IAM Console
Home > Executive > Command Center
```

---

## SEARCH INTEGRATION

Global search (`/search`) searches across:
- Courses
- Creators
- Community posts
- Help articles
- Admin users (admin+)
- Content (creator+)

---

## ACCEPTANCE CRITERIA

- [ ] One canonical home for each capability
- [ ] No duplicate navigation locations for same function
- [ ] Breadcrumbs show clear hierarchy
- [ ] Search finds relevant content across all domains
- [ ] Old URLs redirect to new canonical homes
- [ ] Navigation is understandable to new users
- [ ] Role-based navigation shows appropriate items
- [ ] Mobile navigation is usable
