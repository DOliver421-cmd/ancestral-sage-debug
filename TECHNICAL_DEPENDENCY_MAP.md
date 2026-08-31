# TECHNICAL DEPENDENCY MAP — SHARED SERVICES

Every ecosystem consumes shared infrastructure. No ecosystem rebuilds what already exists.

---

## SHARED SERVICES LAYER

```
┌─────────────────────────────────────────────────────────────┐
│                    SHARED SERVICES                           │
├─────────────┬─────────────┬─────────────┬───────────────────┤
│    AUTH     │    AI       │   STORAGE   │    BILLING        │
│  (JWT,      │  (Gateway,  │  (MongoDB,  │  (Lemon Squeezy, │
│   bcrypt,   │   Budget,   │   GridFS,   │   Gumroad,       │
│   RBAC)     │   BYOK)     │   CDN)      │   Webhooks)      │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│  ENTITLE-   │   MEMBERSHIP│   NOTIFI-   │    AUDIT          │
│  MENTS      │   (Tiers,   │   CATIONS   │    LOG            │
│  (Feature   │    Plans,   │  (In-app,   │  (Actions,        │
│   gates)    │    Billing) │   Email)    │   Compliance)     │
├─────────────┼─────────────┼─────────────┼───────────────────┤
│  ANALYTICS  │  SEARCH     │  MODERATION │    CONTENT        │
│  (Events,   │  (Full-text,│  (Auto-flag,│  (CRUD, Versions, │
│   Metrics)  │   Filters)  │   Reports)  │   Publishing)     │
└─────────────┴─────────────┴─────────────┴───────────────────┘
```

---

## ECOSYSTEM → SERVICE MAP

### AI / NAM

```
AI/NAM consumes:
├── AUTH           (user identity, session)
├── AI GATEWAY     (LLM routing, budget enforcement, BYOK)
├── ENTITLEMENTS   (tier-based feature gates)
├── MEMBERSHIP     (tier detection)
├── CONTENT        (conversation history storage)
├── ANALYTICS      (usage metrics, cost tracking)
├── NOTIFICATIONS  (alerts, reminders)
└── AUDIT LOG      (conversation audit for compliance)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` → `get_current_user` | Every NAM request |
| AI Gateway | `llm_gateway.py` | All LLM calls |
| Entitlements | `entitlements.py` | Token limits, model access |
| Membership | `users.py` | Tier-based routing |
| Content | `conversations` collection | Chat history |
| Analytics | `events` collection | Usage tracking |
| Notifications | `notifications` collection | Reminders |
| Audit Log | `audit_log` collection | Compliance logging |

---

### CREATE (Creator Studio)

```
CREATE consumes:
├── AUTH           (user identity)
├── AI GATEWAY     (AI assistance in creation)
├── ENTITLEMENTS   (project limits, feature access)
├── MEMBERSHIP     (tier detection)
├── STORAGE        (file uploads, images, media)
├── CONTENT        (project CRUD, versions)
├── ANALYTICS      (creation metrics)
├── NOTIFICATIONS  (publish notifications)
└── AUDIT LOG      (creation audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Every creation request |
| AI Gateway | `llm_gateway.py` | AI writing assistance |
| Entitlements | `entitlements.py` | Project limits, AI credits |
| Storage | `storage.py` / GridFS | File uploads |
| Content | `projects` collection | CRUD operations |
| Analytics | `events` collection | Creation tracking |
| Notifications | `notifications` collection | Publish alerts |
| Audit Log | `audit_log` collection | Content audit |

---

### PUBLISH

```
PUBLISH consumes:
├── AUTH           (user identity, authorship)
├── ENTITLEMENTS   (publishing limits, formatting depth)
├── MEMBERSHIP     (tier detection)
├── STORAGE        (file storage, CDN)
├── CONTENT        (draft → review → publish workflow)
├── ANALYTICS      (read metrics, engagement)
├── MARKETPLACE    (monetization, sales)
├── NOTIFICATIONS  (publish alerts, subscriber notifications)
└── AUDIT LOG      (publication audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Authorship |
| Entitlements | `entitlements.py` | Publishing limits |
| Storage | `storage.py` / CDN | File storage |
| Content | `content` collection | CRUD + workflow |
| Analytics | `events` + `content_analytics` | Read tracking |
| Marketplace | `payments.py` | Sales integration |
| Notifications | `notifications` collection | Subscriber alerts |
| Audit Log | `audit_log` collection | Publication audit |

---

### LEARN

```
LEARN consumes:
├── AUTH           (user identity, enrollment)
├── AI GATEWAY     (AI tutoring, hints)
├── ENTITLEMENTS   (course limits, certification access)
├── MEMBERSHIP     (tier detection)
├── CONTENT        (course content, progress)
├── STORAGE        (course materials, attachments)
├── ANALYTICS      (learning metrics, completion)
├── NOTIFICATIONS  (deadline reminders, progress)
└── AUDIT LOG      (certification audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Enrollment verification |
| AI Gateway | `llm_gateway.py` | AI tutoring |
| Entitlements | `entitlements.py` | Course limits |
| Content | `courses` + `enrollments` | Course data |
| Storage | `storage.py` | Course materials |
| Analytics | `events` + `learning_progress` | Progress tracking |
| Notifications | `notifications` collection | Reminders |
| Audit Log | `audit_log` collection | Certification audit |

---

### COMMUNITY

```
COMMUNITY consumes:
├── AUTH           (user identity, reputation)
├── ENTITLEMENTS   (posting limits, moderation access)
├── MEMBERSHIP     (tier detection)
├── CONTENT        (posts, comments, reactions)
├── STORAGE        (media uploads)
├── ANALYTICS      (engagement metrics)
├── SEARCH         (content discovery)
├── MODERATION     (content flagging, reports)
├── NOTIFICATIONS  (replies, mentions, reactions)
└── AUDIT LOG      (moderation audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Identity, reputation |
| Entitlements | `entitlements.py` | Posting limits |
| Content | `community_posts` + `reactions` | CRUD |
| Storage | `storage.py` | Media uploads |
| Analytics | `events` collection | Engagement tracking |
| Search | `search.py` | Content discovery |
| Moderation | `moderation.py` | Flagging, reports |
| Notifications | `notifications` collection | Social alerts |
| Audit Log | `audit_log` collection | Moderation audit |

---

### SANCTUARY

```
SANCTUARY consumes:
├── AUTH           (user identity, privacy)
├── AI GATEWAY     (healing conversations)
├── ENTITLEMENTS   (journal limits, analytics depth)
├── MEMBERSHIP     (tier detection)
├── CONTENT        (journal entries, mood logs)
├── STORAGE        (audio, media)
├── ANALYTICS      (mood patterns, progress)
├── NOTIFICATIONS  (grounding reminders)
└── AUDIT LOG      (privacy audit — who accessed)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Privacy enforcement |
| AI Gateway | `llm_gateway.py` | Healing conversations |
| Entitlements | `entitlements.py` | Journal limits |
| Content | `journal_entries` + `mood_logs` | Personal data |
| Storage | `storage.py` | Audio, media |
| Analytics | `events` + `mood_patterns` | Progress tracking |
| Notifications | `notifications` collection | Reminders |
| Audit Log | `audit_log` collection | Privacy audit |

---

### MUSIC

```
MUSIC consumes:
├── AUTH           (user identity, artist profile)
├── AI GATEWAY     (AI composition, mastering)
├── ENTITLEMENTS   (project limits, export quality)
├── MEMBERSHIP     (tier detection)
├── STORAGE        (audio files, stems)
├── CONTENT        (tracks, albums, discography)
├── ANALYTICS      (stream counts, revenue)
├── MARKETPLACE    (licensing, sales)
├── NOTIFICATIONS  (release alerts)
└── AUDIT LOG      (royalty audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Artist identity |
| AI Gateway | `llm_gateway.py` | AI composition |
| Entitlements | `entitlements.py` | Project limits |
| Storage | `storage.py` / GridFS | Audio files |
| Content | `tracks` + `albums` | Discography |
| Analytics | `events` + `stream_counts` | Performance |
| Marketplace | `payments.py` | Sales/licensing |
| Notifications | `notifications` collection | Release alerts |
| Audit Log | `audit_log` collection | Royalty audit |

---

### MARKETPLACE

```
MARKETPLACE consumes:
├── AUTH           (buyer/seller identity)
├── ENTITLEMENTS   (seller limits, fee structure)
├── MEMBERSHIP     (tier detection, seller tier)
├── BILLING        (payment processing, webhooks)
├── CONTENT        (product listings)
├── STORAGE        (product files, digital delivery)
├── ANALYTICS      (sales metrics, conversion)
├── SEARCH         (product discovery)
├── MODERATION     (product review, flagging)
├── NOTIFICATIONS  (purchase alerts, payouts)
└── AUDIT LOG      (transaction audit)
```

| Service | API/Module | Usage |
|---------|-----------|-------|
| Auth | `deps.py` | Buyer/seller identity |
| Entitlements | `entitlements.py` | Seller limits |
| Billing | `payments.py` + webhooks | Payment processing |
| Content | `products` + `listings` | Product CRUD |
| Storage | `storage.py` | Digital delivery |
| Analytics | `events` + `sales` | Sales tracking |
| Search | `search.py` | Product discovery |
| Moderation | `moderation.py` | Product review |
| Notifications | `notifications` collection | Purchase alerts |
| Audit Log | `audit_log` collection | Transaction audit |

---

### ADMIN / GOVERNANCE

```
ADMIN consumes:
├── AUTH           (admin identity, RBAC)
├── ENTITLEMENTS   (admin feature gates)
├── MEMBERSHIP     (user management)
├── AI GATEWAY     (AI operations)
├── CONTENT        (site content management)
├── ANALYTICS      (platform metrics)
├── MODERATION     (content moderation)
├── NOTIFICATIONS  (broadcast, alerts)
├── AUDIT LOG      (compliance, security)
└── BILLING        (payment oversight)
```

---

## SERVICE DEPENDENCY GRAPH

```
                    ┌─────────┐
                    │  AUTH   │
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
         ┌────┴────┐ ┌───┴───┐ ┌───┴────┐
         │ENTITLE- │ │MEMBER-│ │AUDIT   │
         │MENTS    │ │SHIP   │ │LOG     │
         └────┬────┘ └───┬───┘ └───┬────┘
              │          │         │
    ┌─────────┼──────────┼─────────┼─────────┐
    │         │          │         │         │
┌───┴───┐ ┌───┴───┐ ┌────┴───┐ ┌──┴──┐ ┌───┴───┐
│CONTENT│ │AI GW  │ │STORAGE │ │BILL │ │ANALYT-│
└───┬───┘ └───┬───┘ └────┬───┘ └──┬──┘ │ICS    │
    │         │          │        │    └───┬───┘
    └─────────┼──────────┼────────┘        │
              │          │                 │
         ┌────┴──────────┴─────────────────┴────┐
         │           ECOSYSTEMS                  │
         ├──────┬──────┬──────┬──────┬──────┬────┤
         │AI/NAM│CREATE│PUBLISH│LEARN│COMMUN│SANCT│
         └──────┴──────┴──────┴──────┴──────┴────┘
```

---

## NEW SERVICES TO BUILD

| Service | Priority | Complexity | Used By |
|---------|----------|-----------|---------|
| **Entitlements** | P0 | Low | All ecosystems |
| **Membership** | P0 | Medium | All ecosystems |
| **Content** (unified) | P1 | High | Create, Publish, Learn |
| **Search** (unified) | P1 | Medium | Community, Marketplace |
| **Moderation** (unified) | P2 | Medium | Community, Marketplace |
| **Notifications** (unified) | P2 | Low | All ecosystems |

---

## SERVICES THAT ALREADY EXIST

| Service | Module | Status |
|---------|--------|--------|
| Auth | `routers/auth.py` | ✅ Complete |
| AI Gateway | `llm_gateway.py` | ✅ Complete |
| Storage | `storage.py` + GridFS | ✅ Complete |
| Billing | `payments.py` | ✅ Complete |
| Analytics | `routers/analytics.py` | ✅ Complete |
| Audit Log | `server.py` + `routers/ops.py` | ✅ Complete |

---

## IMPLEMENTATION ORDER

```
1. Entitlements Service    (new, ~200 lines)
2. Membership Fields       (DB migration, ~50 lines)
3. Feature Gate Component  (React, ~30 lines)
4. Frontend Entitlement Hook (React, ~20 lines)
5. Navigation Consolidation (AppShell, ~100 lines)
6. Route Redirects         (App.js, ~50 lines)
7. Content Service         (unified CRUD, ~300 lines)
8. Search Service          (full-text, ~200 lines)
9. Moderation Service      (flagging, ~150 lines)
10. Notification Service   (in-app, ~100 lines)
```

**Total new code:** ~1,200 lines across 10 services.
**Total refactored code:** ~5,000 lines consolidated from duplicates.
**Net reduction:** ~3,800 lines of code.
