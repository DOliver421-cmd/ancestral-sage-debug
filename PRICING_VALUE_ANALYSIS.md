# PRICING / VALUE ANALYSIS

**Date:** August 21, 2026
**Method:** Ground-truth audit of existing capabilities, cost structures, and upgrade pressure points.

---

## PART 1: THE 5 QUESTIONS

### Question 1: What is the core value of each ecosystem?

| Ecosystem | Core Value | Why Someone Pays |
|-----------|-----------|-----------------|
| **AI / NAM** | Personal AI that remembers you and gets smarter over time | Switching cost — leaving means starting over with an AI that knows nothing about you |
| **CREATE** | AI-assisted content creation with publishing pipeline | Output quality — AI help makes professional-grade content accessible to non-professionals |
| **PUBLISH** | One-click publishing to marketplace with analytics | Distribution — reach an audience without building your own platform |
| **LEARN** | Structured skill development with AI tutoring and credentials | Career value — credentials are platform-specific, portfolio compounds |
| **COMMUNITY** | Belonging, reputation, relationships | Social capital — reputation, history, relationships can't be transferred |
| **MARKETPLACE** | Buy/sell digital products with built-in audience | Revenue — existing customer base + payment infrastructure |
| **SANCTUARY** | Private healing space with AI reflection | Emotional data — journaling history and mood patterns are deeply personal |
| **MUSIC** | AI-assisted music production with distribution | Revenue + audience — discography, fans, licensing relationships compound |
| **GAMES** | Competitive gaming with rewards | Engagement — competitive ranking, achievements, community |
| **DIRECTOR** | Executive control over the entire platform | Governance — operational control, analytics, compliance |

### Question 2: What does each tier materially improve?

The correction: **Not "more features." Deeper capability within the same unified feature.**

| Capability | Free | Creator | Pro | Studio | Director |
|-----------|------|---------|-----|--------|----------|
| **AI depth** | Basic chat | Personal memory | Goal tracking + coaching | Team awareness | Org-level intelligence |
| **Creation scope** | 3 projects | 10 projects + AI assist | Unlimited + advanced formatting | Team collaboration | Enterprise + white-label |
| **Publishing reach** | Basic (internal only) | Internal + marketplace | Professional + analytics | Studio + distribution | Full + custom channels |
| **Learning depth** | 1 course | 5 courses + tutoring | All courses + coaching | Create courses + team training | Academy admin |
| **Community power** | Read + basic post | Create hubs + moderate | Featured + analytics | Guild creation | Platform governance |
| **Marketplace access** | Browse only | Sell (standard fees) | Sell (reduced fees) | Storefront customization | Vendor management |
| **Sanctuary depth** | Basic journal | AI reflection + mood | Advanced analytics | Group sessions | Org wellness |
| **Music scope** | Basic composition | Full studio + 5 projects | Unlimited + production | Team production | Label tools |
| **NAM relationship** | Generic AI | Personal memory | Persistent + coaching | Team + project aware | Full orchestration |

### Question 3: What causes a user to hit the next tier naturally?

| Transition | Natural Trigger | Upgrade Pressure |
|-----------|----------------|-----------------|
| **Free → Creator** | User creates 3 projects and wants more | Project limit hit. AI suggestions are basic. Publishing is internal-only. |
| **Creator → Pro** | User's content gets traction. They want analytics, deeper AI, reduced fees. | Creator sees revenue potential but limited by basic tools. AI coaching would help them grow. |
| **Pro → Studio** | User has team members or multiple projects. Needs collaboration. | Solo workflow breaks down when collaborating. White-label becomes relevant. |
| **Studio → Director** | Organization needs governance, compliance, full platform control. | Operational complexity exceeds what individual tools can handle. |

**Key insight:** The upgrade pressure should come from **natural usage growth**, not artificial restrictions. A free user who creates 3 great projects should WANT more because they see the value — not because the 4th project is arbitrarily blocked.

### Question 4: Which capabilities are expensive enough to justify higher pricing?

| Capability | Cost Driver | Marginal Cost | Justifies Higher Tier? |
|-----------|------------|---------------|----------------------|
| **AI conversations** | LLM API tokens | $0.001-0.01 per conversation | Yes — direct cost scales with usage |
| **AI orchestration** | Multiple LLM calls per request | $0.01-0.10 per orchestration | Yes — 10-100x more expensive than basic chat |
| **AI coaching** | Persistent memory + context window | $0.005-0.05 per session | Yes — memory storage + retrieval costs |
| **Team features** | Multi-user licensing | $0.50-2.00 per team member/month | Yes — per-seat cost |
| **White-label** | Custom branding + support | $5-20/month per instance | Yes — infrastructure cost |
| **Storage** | MongoDB/GridFS | $0.02-0.10 per GB/month | Yes — scales with content |
| **Publishing distribution** | CDN + bandwidth | $0.01-0.05 per download | Marginal — mostly fixed costs |
| **Analytics** | Query processing | $0.001-0.01 per query | No — negligible at scale |
| **Community** | Real-time + storage | $0.01-0.05 per active user/month | No — mostly fixed costs |
| **Sanctuary** | AI conversations + storage | Same as AI costs | Yes — AI costs scale |
| **Music production** | AI composition + storage | $0.10-1.00 per track | Yes — AI + storage costs |
| **Games** | Compute + storage | Negligible | No — fixed costs |

**Conclusion:** AI-heavy features and team features justify higher pricing. Storage-heavy features have marginal cost. Community and analytics are mostly fixed costs.

### Question 5: Which features should never be artificially paywalled?

**Foundational platform features that must be free:**

| Feature | Why It Must Be Free |
|---------|-------------------|
| **Account creation** | Barrier to entry kills growth |
| **Basic AI chat** | Core value proposition — users must experience NAM to understand the platform |
| **Community participation** | Network effects require critical mass. Paywalling community kills it. |
| **Basic publishing** | Content creation drives the marketplace. More content = more buyers. |
| **Marketplace browsing** | Buyers must be able to browse. Paywalling browsing kills seller revenue. |
| **Basic learning** | Education is the mission. Paywalling all learning contradicts the institution's purpose. |
| **Sanctuary basic access** | Healing should not be gated behind payment. Basic journaling must be free. |
| **GDPR/data export** | Legal requirement, not a feature |
| **Self-service account deletion** | Legal requirement, not a feature |
| **Password reset** | Security requirement, not a feature |

**Features that CAN be paywalled (value-add):**

| Feature | Why It's Fair to Paywall |
|---------|------------------------|
| Advanced AI (orchestration, coaching, memory) | Direct cost to platform scales with usage |
| Unlimited projects | Storage + compute costs scale |
| Team collaboration | Per-seat licensing costs |
| White-label | Infrastructure + support costs |
| Advanced analytics | Query processing costs |
| Professional publishing tools | Development + maintenance costs |
| Reduced marketplace fees | Revenue model — lower fees = higher tier value |
| AI-assisted music production | AI + storage costs scale |
| Academy/course creation tools | Platform investment costs |

---

## PART 2: CURRENT STATE AUDIT

### What Exists Now

| System | Status | Evidence |
|--------|--------|----------|
| Payments (Lemon Squeezy) | Real code, zero verified transactions | `routers/payments.py` — checkout flow exists |
| Payments (Gumroad) | Real code, zero verified transactions | `routers/payments.py` — Gumroad integration exists |
| Membership tiers | **NOT IMPLEMENTED** | No `membership` field on user model |
| Entitlements | **NOT IMPLEMENTED** | No feature gating system |
| Pricing page | **NOT IMPLEMENTED** | No `/plans` or `/pricing` page |
| Subscription management | **NOT IMPLEMENTED** | No upgrade/downgrade/cancel flow |

### The Gap

The platform has payment processing infrastructure but no membership system. Users can buy individual products but cannot subscribe to tiers. The entire tiering architecture is theoretical.

### What Needs to Be Built

1. **Membership model on user** — Add `membership.tier` field
2. **Entitlements service** — Capability-based feature gating
3. **Pricing page** — Show 5 tiers with clear value proposition
4. **Checkout flow** — Integrate with Lemon Squeezy for subscriptions
5. **Subscription management** — Upgrade, downgrade, cancel, billing history
6. **Entitlement enforcement** — Backend + frontend gating

---

## PART 3: RECOMMENDED PRICING STRUCTURE

### Why These Prices

The pricing is based on:
1. **AI cost structure** — Each tier costs the platform more in LLM tokens
2. **Value delivered** — Higher tiers provide genuinely more capability
3. **Competitive positioning** — Comparable platforms charge $10-50/month for similar features
4. **Upgrade pressure** — Natural usage growth drives tier transitions

### The Tiers

| Tier | Monthly | Annual (per month) | Target User | Value Proposition |
|------|---------|-------------------|-------------|------------------|
| **Free** | $0 | $0 | Anyone | Experience the platform. Basic AI, 3 projects, community access. |
| **Creator** | $9.99 | $7.99 | Content creators | More projects, AI assistance, marketplace selling, basic analytics. |
| **Pro** | $24.99 | $19.99 | Serious creators | Unlimited projects, advanced AI coaching, professional publishing, reduced fees. |
| **Studio** | $49.99 | $39.99 | Teams + professionals | Team collaboration, white-label, advanced production, academy tools. |
| **Director** | $99.99 | $79.99 | Organizations | Full platform control, enterprise governance, API access, custom branding. |

### Revenue Projections (Conservative)

| Scenario | Free Users | Creator | Pro | Studio | Director | Monthly Revenue |
|----------|-----------|---------|-----|--------|----------|----------------|
| **Launch** | 100 | 10 (10%) | 3 (3%) | 1 (1%) | 0 | $1,025 |
| **6 months** | 500 | 50 (10%) | 15 (3%) | 5 (1%) | 1 | $5,375 |
| **12 months** | 1,000 | 100 (10%) | 30 (3%) | 10 (1%) | 2 | $10,950 |
| **24 months** | 3,000 | 300 (10%) | 90 (3%) | 30 (1%) | 5 | $32,850 |

**Key assumption:** 10% free-to-paid conversion is conservative. Industry average for freemium is 2-5%. The platform's AI value proposition should drive higher conversion.

---

## PART 4: THE ENTITLEMENT ARCHITECTURE

### Principle: Capability-Based, Not Page-Based

Don't create:
```
canAccessPublishPage
canAccessProPublishPage
```

Create:
```
publish.create
publish.ai_assist
publish.advanced_formatting
publish.analytics
publish.collaboration
publish.automation
publish.white_label
```

Then tiers are configurations of those capabilities.

### This gives flexibility to change pricing later WITHOUT rewriting the application.

### The Schema

```python
# Capability definitions (static)
CAPABILITIES = {
    # AI / NAM
    "nam.chat": {"category": "ai", "description": "Basic AI conversations"},
    "nam.memory": {"category": "ai", "description": "Persistent conversation memory"},
    "nam.coaching": {"category": "ai", "description": "AI-guided coaching sessions"},
    "nam.orchestration": {"category": "ai", "description": "Multi-step AI workflows"},
    "nam.autonomous": {"category": "ai", "description": "Autonomous AI suggestions"},
    
    # CREATE
    "create.projects": {"category": "creation", "description": "Content creation projects"},
    "create.ai_assist": {"category": "creation", "description": "AI writing assistance"},
    "create.advanced_formatting": {"category": "creation", "description": "Professional formatting tools"},
    "create.collaboration": {"category": "creation", "description": "Team collaboration on projects"},
    "create.white_label": {"category": "creation", "description": "Custom branding on outputs"},
    
    # PUBLISH
    "publish.create": {"category": "publishing", "description": "Create published content"},
    "publish.marketplace": {"category": "publishing", "description": "Publish to marketplace"},
    "publish.analytics": {"category": "publishing", "description": "Read/engagement analytics"},
    "publish.distribution": {"category": "publishing", "description": "External distribution channels"},
    "publish.scheduling": {"category": "publishing", "description": "Scheduled publishing"},
    
    # LEARN
    "learn.courses": {"category": "learning", "description": "Access courses"},
    "learn.ai_tutor": {"category": "learning", "description": "AI tutoring assistance"},
    "learn.coaching": {"category": "learning", "description": "Personal learning coaching"},
    "learn.certificates": {"category": "learning", "description": "Earn certificates"},
    "learn.create_courses": {"category": "learning", "description": "Create and sell courses"},
    
    # COMMUNITY
    "community.read": {"category": "community", "description": "Read community content"},
    "community.post": {"category": "community", "description": "Post in community"},
    "community.create_hub": {"category": "community", "description": "Create community hubs"},
    "community.moderate": {"category": "community", "description": "Moderate community content"},
    "community.guild": {"category": "community", "description": "Create and manage guilds"},
    
    # MARKETPLACE
    "marketplace.browse": {"category": "marketplace", "description": "Browse marketplace"},
    "marketplace.sell": {"category": "marketplace", "description": "Sell products"},
    "marketplace.storefront": {"category": "marketplace", "description": "Custom storefront"},
    "marketplace.analytics": {"category": "marketplace", "description": "Sales analytics"},
    "marketplace.vendor_mgmt": {"category": "marketplace", "description": "Vendor management tools"},
    
    # SANCTUARY
    "sanctuary.journal": {"category": "sanctuary", "description": "Basic journaling"},
    "sanctuary.ai_reflection": {"category": "sanctuary", "description": "AI-guided reflection"},
    "sanctuary.mood_tracking": {"category": "sanctuary", "description": "Mood pattern analytics"},
    "sanctuary.group": {"category": "sanctuary", "description": "Group healing sessions"},
    "sanctuary.org_wellness": {"category": "sanctuary", "description": "Organization wellness dashboard"},
    
    # MUSIC
    "music.compose": {"category": "music", "description": "Basic music composition"},
    "music.studio": {"category": "music", "description": "Full production studio"},
    "music.ai_production": {"category": "music", "description": "AI-assisted production"},
    "music.collaboration": {"category": "music", "description": "Team production"},
    "music.label_tools": {"category": "music", "description": "Label management tools"},
    
    # GAMES
    "games.play": {"category": "games", "description": "Play games"},
    "games.compete": {"category": "games", "description": "Competitive ranking"},
    "games.create": {"category": "games", "description": "Create custom games"},
    
    # DIRECTOR
    "director.analytics": {"category": "director", "description": "Platform analytics"},
    "director.governance": {"category": "director", "description": "Governance controls"},
    "director.api": {"category": "director", "description": "API access"},
    "director.compliance": {"category": "director", "description": "Compliance tools"},
}
```

### Tier Configurations

```python
TIER_LIMITS = {
    "free": {
        "nam.chat": True,
        "nam.memory": False,
        "nam.coaching": False,
        "nam.orchestration": False,
        "nam.autonomous": False,
        
        "create.projects": 3,
        "create.ai_assist": False,
        "create.advanced_formatting": False,
        "create.collaboration": False,
        "create.white_label": False,
        
        "publish.create": True,
        "publish.marketplace": False,
        "publish.analytics": False,
        "publish.distribution": False,
        "publish.scheduling": False,
        
        "learn.courses": 1,
        "learn.ai_tutor": False,
        "learn.coaching": False,
        "learn.certificates": False,
        "learn.create_courses": False,
        
        "community.read": True,
        "community.post": True,
        "community.create_hub": False,
        "community.moderate": False,
        "community.guild": False,
        
        "marketplace.browse": True,
        "marketplace.sell": False,
        "marketplace.storefront": False,
        "marketplace.analytics": False,
        "marketplace.vendor_mgmt": False,
        
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": False,
        "sanctuary.mood_tracking": False,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        "music.compose": True,
        "music.studio": False,
        "music.ai_production": False,
        "music.collaboration": False,
        "music.label_tools": False,
        
        "games.play": True,
        "games.compete": False,
        "games.create": False,
        
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        "ai_daily_tokens": 1000,
        "storage_mb": 100,
        "projects": 3,
        "courses": 1,
        "marketplace_fee": 0.30,
    },
    "creator": {
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": False,
        "nam.orchestration": False,
        "nam.autonomous": False,
        
        "create.projects": 10,
        "create.ai_assist": True,
        "create.advanced_formatting": False,
        "create.collaboration": False,
        "create.white_label": False,
        
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": False,
        "publish.scheduling": False,
        
        "learn.courses": 5,
        "learn.ai_tutor": True,
        "learn.coaching": False,
        "learn.certificates": True,
        "learn.create_courses": False,
        
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": False,
        "community.guild": False,
        
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": False,
        "marketplace.analytics": False,
        "marketplace.vendor_mgmt": False,
        
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": False,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": False,
        "music.collaboration": False,
        "music.label_tools": False,
        
        "games.play": True,
        "games.compete": True,
        "games.create": False,
        
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        "ai_daily_tokens": 5000,
        "storage_mb": 500,
        "projects": 10,
        "courses": 5,
        "marketplace_fee": 0.25,
    },
    "pro": {
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": False,
        
        "create.projects": -1,  # unlimited
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": False,
        
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        "learn.courses": -1,  # unlimited
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": False,
        
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": False,
        
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": False,
        
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": False,
        "sanctuary.org_wellness": False,
        
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": False,
        "music.label_tools": False,
        
        "games.play": True,
        "games.compete": True,
        "games.create": False,
        
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        "ai_daily_tokens": 25000,
        "storage_mb": 2000,
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.20,
    },
    "studio": {
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": True,
        
        "create.projects": -1,
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": True,
        
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        "learn.courses": -1,
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": True,
        
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": True,
        
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": True,
        
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": True,
        "sanctuary.org_wellness": False,
        
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": True,
        "music.label_tools": False,
        
        "games.play": True,
        "games.compete": True,
        "games.create": True,
        
        "director.analytics": False,
        "director.governance": False,
        "director.api": False,
        "director.compliance": False,
        
        "ai_daily_tokens": 100000,
        "storage_mb": 10000,
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.15,
    },
    "director": {
        "nam.chat": True,
        "nam.memory": True,
        "nam.coaching": True,
        "nam.orchestration": True,
        "nam.autonomous": True,
        
        "create.projects": -1,
        "create.ai_assist": True,
        "create.advanced_formatting": True,
        "create.collaboration": True,
        "create.white_label": True,
        
        "publish.create": True,
        "publish.marketplace": True,
        "publish.analytics": True,
        "publish.distribution": True,
        "publish.scheduling": True,
        
        "learn.courses": -1,
        "learn.ai_tutor": True,
        "learn.coaching": True,
        "learn.certificates": True,
        "learn.create_courses": True,
        
        "community.read": True,
        "community.post": True,
        "community.create_hub": True,
        "community.moderate": True,
        "community.guild": True,
        
        "marketplace.browse": True,
        "marketplace.sell": True,
        "marketplace.storefront": True,
        "marketplace.analytics": True,
        "marketplace.vendor_mgmt": True,
        
        "sanctuary.journal": True,
        "sanctuary.ai_reflection": True,
        "sanctuary.mood_tracking": True,
        "sanctuary.group": True,
        "sanctuary.org_wellness": True,
        
        "music.compose": True,
        "music.studio": True,
        "music.ai_production": True,
        "music.collaboration": True,
        "music.label_tools": True,
        
        "games.play": True,
        "games.compete": True,
        "games.create": True,
        
        "director.analytics": True,
        "director.governance": True,
        "director.api": True,
        "director.compliance": True,
        
        "ai_daily_tokens": -1,  # unlimited
        "storage_mb": -1,  # unlimited
        "projects": -1,
        "courses": -1,
        "marketplace_fee": 0.10,
    },
}
```

---

## PART 5: RETENTION CORRECTION

### Original Statement (Incorrect)
> "Music — discography, fans, revenue are platform-locked"

### Corrected Statement
> "Music — discography, audience history, analytics, licensing relationships, and revenue tools compound over time. The accumulated value makes the platform the natural home for an artist's career."

### The Principle

Retention should come from **accumulated value**, not artificial captivity.

A user stays because:
1. Their work has generated revenue here
2. Their audience knows them here
3. Their reputation is established here
4. Their data (analytics, patterns, history) is irreplaceable
5. Their relationships (community, collaborators) are here
6. Their AI (NAM) knows them deeply

A user does NOT stay because:
1. Their data is held hostage
2. There's no export option
3. Leaving would lose everything

**The difference:** The first list is natural value accumulation. The second is artificial lock-in. Build for the first. Never build for the second.

---

## ACCEPTANCE CRITERIA

- [ ] Every capability in the matrix is real (not theoretical)
- [ ] Tier boundaries create natural upgrade pressure
- [ ] No foundational feature is artificially paywalled
- [ ] AI costs are properly reflected in tier pricing
- [ ] Team features justify Studio tier pricing
- [ ] Director tier provides genuine organizational value
- [ ] Retention comes from accumulated value, not captivity
- [ ] Pricing is competitive with similar platforms
- [ ] Revenue projections are conservative and realistic
- [ ] The entitlement schema is capability-based, not page-based
