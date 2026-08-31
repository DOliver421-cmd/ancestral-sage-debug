# FEATURE MAP — MoreHelp Center

**Date:** August 22, 2026

This is the canonical product map. Every capability appears exactly once.

---

## AI ECOSYSTEM

### AI Assistants
```
├── NAM Tutor
│   ├── Capabilities: nam.chat, nam.memory, nam.identity
│   ├── Route: /ai
│   ├── API: /api/ai/tutor, /api/nam/*
│   ├── Cost: AI tokens per request (platform-paid)
│   ├── Roles: member+
│   ├── Tiers: free (limited)
│   └── Nav: NAM → AI Assistants
│
├── Personal Helper
│   ├── Capabilities: helper.chat, helper.memory
│   ├── Route: /helper
│   ├── API: /api/ai/helper
│   ├── Cost: AI tokens per request
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: NAM → AI Assistants
│
├── Admin Assistant
│   ├── Capabilities: assistant.chat
│   ├── Route: /assistant
│   ├── API: /api/ai/assistant
│   ├── Cost: AI tokens per request
│   ├── Roles: admin+
│   ├── Tiers: —
│   └── Nav: NAM → AI Assistants
│
├── Orchestrator
│   ├── Capabilities: orchestrator.workflow
│   ├── Route: /orchestrator (not in nav currently)
│   ├── API: /api/ai/orchestrator
│   ├── Cost: AI tokens per request
│   ├── Roles: admin+
│   ├── Tiers: —
│   └── Nav: NAM → AI Assistants
│
└── Site Guide
    ├── Capabilities: siteguide.chat
    ├── Route: /site-guide
    ├── API: /api/site-guide/*
    ├── Cost: AI tokens per request
    ├── Roles: member+
    ├── Tiers: free
    └── Nav: NAM → AI Assistants
```

### AI Leadership
```
├── Council (Sage)
│   ├── Capabilities: sage.chat, sage.reflection
│   ├── Route: /council
│   ├── API: /api/ai/sage/*, /api/sovereign/*
│   ├── Cost: AI tokens per request
│   ├── Roles: member+
│   ├── Tiers: pro+
│   └── Nav: NAM → Leadership
│
├── Jamil — Director AI
│   ├── Capabilities: jamil.chat, jamil.protocol
│   ├── Route: /jamil
│   ├── API: /api/jamil/*
│   ├── Cost: AI tokens per request
│   ├── Roles: admin+
│   ├── Tiers: —
│   └── Nav: NAM → Leadership
│
└── My AI Keys (BYOK)
    ├── Capabilities: byok.manage
    ├── Route: /byok
    ├── API: /api/byok/*
    ├── Cost: $0 (user's own key)
    ├── Roles: member+
    ├── Tiers: free
    └── Nav: NAM → Leadership
```

---

## CREATE ECOSYSTEM

### Content Creation
```
├── Creator Studio
│   ├── Capabilities: studio.create, studio.edit
│   ├── Route: /studio
│   ├── API: /api/studio/*
│   ├── Cost: AI tokens for generation
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
├── Course Manager
│   ├── Capabilities: learn.create_courses
│   ├── Route: /creator/courses
│   ├── API: /api/lms/courses/*
│   ├── Cost: $0 (content management)
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
├── Ghost Producer
│   ├── Capabilities: ghost.produce
│   ├── Route: /ghost-producer
│   ├── API: /api/studio/ghost/*
│   ├── Cost: AI tokens for generation
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
├── Social Blast
│   ├── Capabilities: publish.create
│   ├── Route: /social/publish
│   ├── API: /api/community/publish/*
│   ├── Cost: AI tokens for generation
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
├── Creator Lounge
│   ├── Capabilities: lounge.access
│   ├── Route: /creator-lounge
│   ├── API: /api/creator-lounge/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
├── My Earnings
│   ├── Capabilities: marketplace.earnings
│   ├── Route: /creator/earnings
│   ├── API: /api/billing/earnings/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Create
│
└── Payout Dashboard
    ├── Capabilities: marketplace.payouts
    ├── Route: /creator/payouts
    ├── API: /api/billing/payouts/*
    ├── Cost: $0
    ├── Roles: member+
    ├── Tiers: creator+
    └── Nav: Create
```

---

## LEARN ECOSYSTEM

```
├── Modules (Curriculum)
│   ├── Capabilities: learn.browse, learn.enroll
│   ├── Route: /modules, /modules/:slug
│   ├── API: /api/lms/modules/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Curriculum
│
├── Learning Path
│   ├── Capabilities: learn.adaptive
│   ├── Route: /adaptive
│   ├── API: /api/lms/adaptive/*
│   ├── Cost: AI tokens for personalization
│   ├── Roles: member+
│   ├── Tiers: pro+
│   └── Nav: Learn → Curriculum
│
├── Competencies
│   ├── Capabilities: learn.competencies
│   ├── Route: /competencies
│   ├── API: /api/lms/competencies/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Curriculum
│
├── Workforce Labs
│   ├── Capabilities: learn.labs
│   ├── Route: /labs, /labs/:slug
│   ├── API: /api/lms/labs/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Labs & Practice
│
├── Lab Simulations
│   ├── Capabilities: learn.simulations
│   ├── Route: /lab-simulations
│   ├── API: /api/lms/simulations/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Labs & Practice
│
├── Compliance
│   ├── Capabilities: learn.compliance
│   ├── Route: /compliance, /compliance/:slug
│   ├── API: /api/lms/compliance/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Compliance
│
├── Credentials
│   ├── Capabilities: learn.credentials
│   ├── Route: /credentials
│   ├── API: /api/lms/credentials/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Credentials
│
├── Certificates
│   ├── Capabilities: learn.certificates
│   ├── Route: /certificates
│   ├── API: /api/lms/certificates/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Learn → Credentials
│
└── Portfolio
    ├── Capabilities: learn.portfolio
    ├── Route: /portfolio
    ├── API: /api/lms/portfolio/*
    ├── Cost: $0
    ├── Roles: member+
    ├── Tiers: free
    └── Nav: Learn → Credentials
```

---

## COMMUNITY ECOSYSTEM

```
├── Members' Palace
│   ├── Capabilities: community.palace
│   ├── Route: /palace
│   ├── API: /api/community/palace/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Community
│
├── XP Leaderboard
│   ├── Capabilities: community.leaderboard
│   ├── Route: /leaderboard
│   ├── API: /api/community/leaderboard/*
│   ├── Cost: $0
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Community
│
├── Community Chat
│   ├── Capabilities: community.chat
│   ├── Route: /more/chat
│   ├── API: /api/chat/*
│   ├── Cost: AI tokens for moderation
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Community
│
├── Legal Tools
│   ├── Capabilities: community.legal
│   ├── Route: /more/litigation
│   ├── API: —
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Community
│
├── Report Incident
│   ├── Capabilities: community.incidents
│   ├── Route: /incidents
│   ├── API: /api/community/incidents/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Community
│
├── Vonns Saga
│   ├── Capabilities: community.saga
│   ├── Route: /vonns-saga
│   ├── API: /api/saga/*
│   ├── Cost: $0 (bandcamp embeds)
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Community
│
└── Ascension Protocols
    ├── Capabilities: community.ascension
    ├── Route: /ascension-protocols
    ├── API: —
    ├── Cost: $0
    ├── Roles: public
    ├── Tiers: —
    └── Nav: Community
```

---

## MARKETPLACE ECOSYSTEM

```
├── Media Store
│   ├── Capabilities: marketplace.browse, marketplace.buy
│   ├── Route: /store
│   ├── API: /api/commerce/store/*
│   ├── Cost: $0 (browsing)
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Marketplace
│
├── Plans & Pricing
│   ├── Capabilities: marketplace.plans
│   ├── Route: /plans
│   ├── API: —
│   ├── Cost: $0
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Marketplace
│
├── Membership
│   ├── Capabilities: marketplace.subscribe
│   ├── Route: /subscribe
│   ├── API: /api/billing/subscribe/*
│   ├── Cost: $0 (UI only)
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Marketplace
│
├── Donate
│   ├── Capabilities: marketplace.donate
│   ├── Route: /donate
│   ├── API: /api/billing/donate/*
│   ├── Cost: $0
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Marketplace
│
├── Payment History
│   ├── Capabilities: marketplace.payments
│   ├── Route: /payment/history
│   ├── API: /api/billing/history/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Marketplace
│
└── Partnerships
    ├── Capabilities: marketplace.partnerships
    ├── Route: /partnership
    ├── API: /api/billing/partnerships/*
    ├── Cost: $0
    ├── Roles: member+
    ├── Tiers: free
    └── Nav: Marketplace
```

---

## SANCTUARY ECOSYSTEM

```
├── Sanctuary
│   ├── Capabilities: sanctuary.journal, sanctuary.reflection
│   ├── Route: /sanctuary
│   ├── API: /api/sovereign/*
│   ├── Cost: AI tokens for reflection
│   ├── Roles: member+
│   ├── Tiers: pro+
│   └── Nav: Sanctuary
│
└── Knowledge Base
    ├── Capabilities: sanctuary.knowledge
    ├── Route: /knowledge-base
    ├── API: —
    ├── Cost: $0
    ├── Roles: public
    ├── Tiers: —
    └── Nav: Sanctuary
```

---

## MUSIC ECOSYSTEM

```
├── Band on a Page
│   ├── Capabilities: music.create
│   ├── Route: /band
│   ├── API: /api/band/*
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: creator+
│   └── Nav: Music
│
└── Playlist Manager
    ├── Capabilities: music.playlist
    ├── Route: /playlist/dashboard
    ├── API: /api/playlist/*
    ├── Cost: $0
    ├── Roles: member+
    ├── Tiers: free
    └── Nav: Music
```

---

## GAMES ECOSYSTEM

```
├── Virtual Arcade
│   ├── Capabilities: games.play
│   ├── Route: /arcade, /arcade/:slug
│   ├── API: —
│   ├── Cost: $0
│   ├── Roles: member+
│   ├── Tiers: free
│   └── Nav: Games
│
├── M.O.R.E. Pantheon
│   ├── Capabilities: games.pantheon
│   ├── Route: /trash
│   ├── API: —
│   ├── Cost: $0
│   ├── Roles: public
│   ├── Tiers: —
│   └── Nav: Games
│
└── Arena (Exec Only)
    ├── Capabilities: arena.run, arena.score
    ├── Route: /arena
    ├── API: /api/competition/*
    ├── Cost: AI tokens (4 personas × rounds)
    ├── Roles: executive_admin
    ├── Tiers: —
    └── Nav: Director → Tools
```

---

## ADMIN ECOSYSTEM

```
├── Admin Dashboard
│   ├── Route: /admin
│   ├── Roles: admin+
│
├── IAM Console
│   ├── Route: /admin/iam
│   ├── Roles: admin+
│
├── Business Office
│   ├── Route: /admin/office (exec) or /business-office (admin)
│   ├── Roles: admin+
│
├── Command Center
│   ├── Route: /admin/command
│   ├── Roles: executive_admin
│
├── System Health
│   ├── Route: /admin/health
│   ├── Roles: admin+
│
├── Payments
│   ├── Route: /admin/payments
│   ├── Roles: admin+
│
├── Billing
│   ├── Route: /admin/billing
│   ├── Roles: admin+
│
├── Prices
│   ├── Route: /admin/prices
│   ├── Roles: admin+
│
├── Revenue
│   ├── Route: /revenue
│   ├── Roles: admin+
│
├── Analytics
│   ├── Route: /admin/analytics
│   ├── Roles: admin+
│
├── Audit Log
│   ├── Route: /admin/audit
│   ├── Roles: support_staff+
│
├── Moderation
│   ├── Route: /admin/moderation
│   ├── Roles: support_staff+
│
├── AI Team Bridge
│   ├── Route: /admin/bridge
│   ├── Roles: admin+
│
├── Provider Gateway
│   ├── Route: /admin/providers
│   ├── Roles: executive_admin
│
├── Team Ops
│   ├── Route: /team/ops
│   ├── Roles: executive_admin
│
├── Projects
│   ├── Route: /projects
│   ├── Roles: admin+
│
├── Scholarships
│   ├── Route: /admin/scholarships
│   ├── Roles: admin+
│
└── Account Controls
    ├── Route: /admin/accounts
    ├── Roles: admin+
```

---

## ACCESS SUMMARY

| Capability | Public | Free | Creator | Pro | Studio | Director |
|------------|--------|------|---------|-----|--------|----------|
| AI Chat (NAM) | ❌ | ✅ limited | ✅ | ✅ | ✅ | ✅ |
| AI Chat (Helper) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Jamil | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Council (Sage) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Arena | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ exec only |
| Creator Studio | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Ghost Producer | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Social Blast | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Course Manager | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Learning Path | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Sanctuary | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Band on a Page | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| Marketplace | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Community | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Leaderboard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Modules | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## PHASE 17 UPDATE (2026-08-23) — CANONICAL FEATURE MAP NOW LIVE

The canonical product map is now generated from the live registry and published in
**FEATURE_ACCESS_MATRIX.md** (48 features: route → API → internal/customer →
cost-bearing → roles → tiers → platform AI → BYOK → enforcement layer).

Key deltas since this file was written:
- Tier names normalized to real tiers (`free/member/plus/pro/patron/executive`).
- 4 stale registry `api_endpoints` corrected against the real route table.
- Enforcement is now layered: FCC middleware + exec flags + router rank checks
  (see ACCESS_CONTROL_ARCHITECTURE.md).
