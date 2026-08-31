# CAPABILITY ARCHITECTURE — UNIFIED SYSTEMS

**Date:** August 21, 2026
**Status:** Design complete, ready for implementation

---

## CORE PRINCIPLE

One engine per capability. Multiple tier experiences. Not duplicated codebases.

```
                CORE CAPABILITY ENGINE
                       │
              ┌────────┴────────┐
              │                 │
        PERMISSION ENGINE   TIER ENGINE
              │                 │
              └────────┬────────┘
                       │
               USER EXPERIENCE
```

---

## 1. AI ORCHESTRATION ENGINE

### Shared Infrastructure
```
LLM GATEWAY (existing — 10-tier free-first chain)
       │
  ┌────┼────┐
  │    │    │
PERSONAS TOOLS MEMORY
  │    │    │
  └────┼────┘
       │
  AI CONSOLE (unified frontend)
```

### What's Shared
- LLM Gateway (`/backend/ai/llm_gateway.py`) — single entry point
- Persona Loader (`/backend/ai/persona_loader.py`) — persona definitions
- Prompt Guard (`/backend/ai/prompt_guard.py`) — safety
- Source Protocol (`/backend/ai/source_protocol.py`) — controls
- Memory System (`/backend/ai/memory.py`) — conversation memory

### What's Different Per Tier
- **Available personas** — Free gets 2, Director gets all 17
- **Memory depth** — Free=session, Director=permanent
- **Budget** — Free=limited tokens, Director=unlimited
- **Tools** — Free=basic, Director=full tool access
- **TTS** — Free=none, Director=full voice

### API Endpoints (shared)
- `/ai/chat` — universal chat endpoint
- `/ai/consent` — consent management
- `/ai/memory` — memory access
- `/ai/history/{session_id}` — conversation history

---

## 2. PUBLISHING ENGINE

### Shared Infrastructure
```
CONTENT STORAGE (MongoDB + file storage)
       │
  ┌────┼────┐
  │    │    │
WRITE PRODUCE DISTRIBUTE
  │    │    │
  └────┼────┘
       │
  PUBLISHING STUDIO (unified frontend)
```

### What's Shared
- Content storage model (MongoDB collections)
- File upload system (`/media/upload`)
- AI generation (via LLM Gateway)
- Analytics tracking

### What's Different Per Tier
- **Content types** — Free=text, Director=all
- **AI assistance** — Free=none, Director=full
- **Scheduling** — Free=none, Pro+=yes
- **Analytics** — Free=basic, Director=enterprise
- **Collaboration** — Free=none, Studio+=team

### Content Model
```javascript
{
  _id: ObjectId,
  user_id: String,
  type: "text" | "video" | "audio" | "social",
  title: String,
  content: String,       // or file_url for media
  status: "draft" | "published" | "scheduled",
  metadata: {
    format: String,
    duration: Number,
    tags: [String],
    category: String,
  },
  analytics: {
    views: Number,
    likes: Number,
    shares: Number,
  },
  created_at: Date,
  updated_at: Date,
}
```

---

## 3. COMMUNITY ENGINE

### Shared Infrastructure
```
USER PROFILES (shared)
       │
  ┌────┼────┐
  │    │    │
FEED CHAT NEEDS
  │    │    │
  └────┼────┘
       │
  COMMUNITY HUB (unified frontend)
```

### What's Shared
- User profiles and authentication
- Notification system
- Moderation system
- XP/Reputation system

### What's Different Per Tier
- **Post frequency** — Free=read-only, Member=5/day, Director=unlimited
- **Chat access** — Free=none, Member=basic, Director=full
- **Moderation** — Free=none, Pro+=basic, Director=full
- **Analytics** — Free=none, Pro+=basic, Director=enterprise

### Content Model
```javascript
// Posts
{
  _id: ObjectId,
  user_id: String,
  type: "post" | "need" | "offer",
  content: String,
  tags: [String],
  upvotes: Number,
  responses: Number,
  status: "active" | "flagged" | "removed",
  created_at: Date,
}

// Chat Messages
{
  _id: ObjectId,
  room_id: String,
  user_id: String,
  content: String,
  type: "text" | "image" | "file",
  created_at: Date,
}
```

---

## 4. CREATOR ECONOMY ENGINE

### Shared Infrastructure
```
USER PROFILES (shared)
       │
  ┌────┼────┐
  │    │    │
COURSES EARNINGS PROFILE
  │    │    │
  └────┼────┘
       │
  CREATOR DASHBOARD (unified frontend)
```

### What's Shared
- User profiles and authentication
- Payment processing (Lemon Squeezy)
- Content storage
- Analytics

### What's Different Per Tier
- **Course creation** — Free=0, Member=1, Director=unlimited
- **Earnings dashboard** — Free=none, Member=basic, Director=full
- **Payout frequency** — Free=none, Member=monthly, Director=on-demand
- **Analytics** — Free=none, Plus+=basic, Director=enterprise

### Course Model
```javascript
{
  _id: ObjectId,
  creator_id: String,
  title: String,
  description: String,
  price_cents: Number,
  category: String,
  modules: [{
    title: String,
    content: String,
    quiz: { questions: [Object] },
  }],
  published: Boolean,
  enrollment_count: Number,
  created_at: Date,
}
```

---

## 5. PAYMENT ENGINE

### Shared Infrastructure
```
LEMON SQUEEZY (existing integration)
       │
  ┌────┼────┐
  │    │    │
SUBSCRIBE DONATE HISTORY
  │    │    │
  └────┼────┘
       │
  BILLING (unified frontend)
```

### What's Shared
- Lemon Squeezy checkout
- Webhook handling
- Tier management
- Transaction logging

### What's Different Per Tier
- **Payment methods** — Free=none, Member=card, Director=all
- **Invoice history** — Free=none, Member=30 days, Director=full
- **Refunds** — Free=none, Member=self-service, Director=full

---

## 6. LEARNING ENGINE

### Shared Infrastructure
```
COURSE CONTENT (MongoDB)
       │
  ┌────┼────┐
  │    │    │
MODULES LABS CERTS
  │    │    │
  └────┼────┘
       │
  LEARNING HUB (unified frontend)
```

### What's Shared
- Course content storage
- Progress tracking
- Quiz engine
- Certificate generation

### What's Different Per Tier
- **Course access** — Free=2, Member=5, Director=all
- **Lab access** — Free=none, Plus+=basic, Director=full
- **Certificates** — Free=none, Member=basic, Director=professional
- **Competencies** — Free=none, Plus+=basic, Director=full

---

## 7. ANALYTICS ENGINE

### Shared Infrastructure
```
EVENT TRACKING (MongoDB)
       │
  ┌────┼────┐
  │    │    │
USER CONTENT REVENUE
  │    │    │
  └────┼────┘
       │
  ANALYTICS DASHBOARD (unified frontend)
```

### What's Shared
- Event tracking system
- Data aggregation
- Visualization components

### What's Different Per Tier
- **Basic analytics** — Free=user stats, Member=content stats
- **Advanced analytics** — Pro=audience insights, Director=enterprise
- **Export** — Free=none, Pro+=CSV, Director=API

---

## 8. NOTIFICATION ENGINE

### Shared Infrastructure
```
NOTIFICATION QUEUE (MongoDB)
       │
  ┌────┼────┐
  │    │    │
IN-APP EMAIL PUSH
  │    │    │
  └────┼────┘
       │
  NOTIFICATION CENTER (unified frontend)
```

### What's Shared
- Notification storage
- Delivery channels
- Preference management

### What's Different Per Tier
- **Channels** — Free=in-app, Member=+email, Director=all
- **Frequency** — Free=daily digest, Member=real-time, Director=configurable
- **Custom alerts** — Free=none, Pro+=basic, Director=full

---

## SHARED SERVICES MAP

Every feature consumes these services:

| Service | AI | Publish | Learn | Community | Music | Earn | Admin |
|---------|-----|---------|-------|-----------|-------|------|-------|
| Auth | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| LLM Gateway | ✓ | ✓ | — | — | — | — | — |
| Media | — | ✓ | — | — | ✓ | — | — |
| Payments | — | ✓ | — | — | ✓ | ✓ | ✓ |
| Notifications | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| Audit | — | — | ✓ | ✓ | — | ✓ | ✓ |
| RBAC | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Memory | ✓ | — | — | — | — | — | — |
| Storage | — | ✓ | ✓ | — | ✓ | — | — |
| Search | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |

---

## TECHNICAL DEPENDENCY MAP

### Backend Modules (shared)
```
backend/
├── ai/
│   ├── llm_gateway.py          # Shared by all AI features
│   ├── persona_loader.py       # Shared by all persona features
│   ├── prompt_guard.py         # Shared safety
│   ├── source_protocol.py      # Shared controls
│   └── memory.py              # Shared memory
├── billing/
│   ├── routes.py              # Shared payment processing
│   └── models.py              # Shared payment models
├── security/
│   ├── rbac.py                # Shared RBAC
│   └── feature_control.py     # Shared feature gating
├── routers/
│   ├── auth.py                # Shared authentication
│   ├── users.py               # Shared user management
│   ├── admin.py               # Shared admin operations
│   └── notifications.py       # Shared notifications
└── database.py                # Shared MongoDB connection
```

### Frontend Modules (shared)
```
frontend/src/
├── lib/
│   ├── api.js                 # Shared API client
│   ├── auth.jsx               # Shared auth context
│   ├── roles.js               # Shared RBAC
│   ├── tiers.js               # Shared tier gating
│   └── accessGates.js         # Shared page access
├── components/
│   ├── AppShell.jsx           # Shared layout
│   ├── NotificationBell.jsx   # Shared notifications
│   ├── CookieConsent.jsx      # Shared compliance
│   └── ErrorBoundary.jsx      # Shared error handling
└── hooks/
    └── useMic.js              # Shared voice input
```

---

## ACCEPTANCE CRITERIA

- [ ] One LLM Gateway shared by all AI features
- [ ] One content storage shared by all publishing features
- [ ] One user profile shared by all features
- [ ] One payment system shared by all monetization features
- [ ] One notification system shared by all features
- [ ] One audit system shared by all admin features
- [ ] One RBAC system shared by all features
- [ ] No duplicate database collections for same data
- [ ] No duplicate API endpoints for same operation
- [ ] No duplicate frontend components for same UI
