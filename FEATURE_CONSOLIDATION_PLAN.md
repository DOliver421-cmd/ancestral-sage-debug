# FEATURE AUDIT, CONSOLIDATION & TIERING ARCHITECTURE

**Date:** August 21, 2026
**Status:** Phase 1 — Complete Audit & Architecture (pre-implementation)
**Audience:** Executive (Delon Oliver)

---

## A. FEATURE INVENTORY

Every existing feature, its current location, capability, and status.

### 1. PUBLISHING & CONTENT CREATION

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Creator Studio | `/studio` | Multi-modal content creation (video, audio, scripts, metadata) | ✅ Working |
| Ghost Producer | `/ghost-producer` | AI-assisted content production via `/ai/chat` | ✅ Working |
| Social Publish | `/social/publish` | AI social media publishing via `/ai/social-blast` | ✅ Working |
| Video Presenter | `/studio/video-presenter` | Scene-based video script builder | ✅ Working |
| Ascension Protocols | `/ascension-protocols` | 1051-line content creation system | ✅ Working |
| Vonns Saga | `/vonns-saga` | AI narrative/story creation | ✅ Working |
| Trash Pantheon | `/trash` | Worst-idea brainstorming tool | ✅ Working |
| Legacy Tool | `/classic/:slug` | Legacy tool redirector | ⚠️ Legacy |
| Classic Tools | `/classic-tools` | Legacy tool listing | ⚠️ Legacy |

### 2. MUSIC & AUDIO

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Media Store | `/store` | Browse, buy, sell, library — full media marketplace | ✅ Working |
| Band On Page | `/band` | Music band listings, bookings | ✅ Working |
| Creator Lounge | `/creator-lounge` | Music project collaboration | ✅ Working |
| Playlist Dashboard | `/playlist/dashboard` | Spotify playlist management | ✅ Working |
| Playlist Submit | `/playlist/:slug/submit` | Submit tracks to playlists | ✅ Working |
| More (Community) | `/more` | Posts, needs board | ✅ Working |

### 3. AI ASSISTANTS & PERSONAS

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| AI Tutor | `/ai` | Educational AI chat with consent, integrity checks | ✅ Working |
| Admin Assistant | `/assistant` | Business AI (emails, docs, tasks) via `/assistant/chat` | ✅ Working |
| Orchestrator | `/orchestrator` | Multi-persona AI coordination | ✅ Working |
| Jamil | `/jamil` | AI persona with TTS, transcription, knowledge | ✅ Working |
| Helper | `/helper` | Community Q&A assistant | ✅ Working |
| Site Guide | `/site-guide` | Interactive navigation guide | ✅ Working |
| Creative Partner Hub | `/creative-partner` | AI creative collaboration | ✅ Working |
| Personas | `/personas` | Persona listing | ✅ Working |
| Persona Profile | `/personas/:slug` | Individual persona chat + controls | ✅ Working |
| Elder Council | `/elder-council` | Gateway to council chat | ⚠️ Redirect |

### 4. LEARNING & EDUCATION

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Modules List | `/modules` | Course catalog | ✅ Working |
| Module View | `/modules/:slug` | Individual module with quizzes | ✅ Working |
| Labs Hub | `/labs` | Lab listing | ✅ Working |
| Lab Detail | `/labs/:slug` | Individual lab submission | ✅ Working |
| Lab Simulations | `/lab-simulations` | Interactive simulations (no API) | ✅ Working |
| Competencies | `/competencies` | Skill tracking | ✅ Working |
| Certificates | `/certificates` | Certificate display | ✅ Working |
| Credentials | `/credentials` | Credential management | ✅ Working |
| Attendance | `/attendance` | Attendance tracking | ✅ Working |
| Adaptive | `/adaptive` | Adaptive learning path | ✅ Working |
| Portfolio | `/portfolio` | Portfolio builder | ✅ Working |
| Public Portfolio | `/u/:username` | Public portfolio view | ✅ Working |
| Internships | `/internships` | Internship listings | ⚠️ Static |

### 5. COMMUNITY & SOCIAL

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Community | `/community` | Community landing | ✅ Working |
| More Hub | `/app/more` | Community posts + needs board | ✅ Working |
| More Chat | `/more/chat` | Community chat rooms | ✅ Working |
| More Admin | `/more/admin` | Community moderation | ✅ Working |
| More Ops | `/more/ops` | Community operations | ✅ Working |
| Leaderboard | `/leaderboard` | XP leaderboard | ✅ Working |
| Staff Meeting History | `/staff-meetings` | Meeting logs | ✅ Working |
| Seshats Hub Public | `/seshats-hub` | Public supervisor view | ✅ Working |

### 6. CREATOR ECONOMY

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Creator Courses | `/creator/courses` | Course management | ✅ Working |
| Creator Profile | `/creator/:slug` | Public creator profile | ✅ Working |
| Creator Profile Edit | `/creator/profile/edit` | Profile editor | ✅ Working |
| Creator Earnings | `/creator/earnings` | Earnings + bank setup | ✅ Working |
| Creator Payout Dashboard | `/creator/payouts` | Payout summary | ✅ Working |
| Creators | `/creators` | Creator listing | ✅ Working |
| MoreHelpCenter | `/more-help-center` | Mega-dashboard (2369 lines, 28 APIs) | ⚠️ Overflow |

### 7. MONETIZATION & PAYMENTS

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Subscribe Page | `/subscribe` | Subscription checkout | ✅ Working |
| Payment History | `/payment/history` | Transaction history | ✅ Working |
| Payment Success | `/payment/success` | Success redirect | ✅ Working |
| Payment Cancel | `/payment/cancel` | Cancel redirect | ✅ Working |
| Donate Page | `/donate` | Donation checkout | ✅ Working |
| Platform Prices | `/admin/prices` | Price configuration | ✅ Working |
| BYOK | `/byok` | Bring Your Own Key | ✅ Working |
| Scholarships | `/scholarships/apply` | Scholarship application | ✅ Working |
| Sponsor Scholarship | `/sponsor` | Scholarship sponsorship | ✅ Working |
| Admin Scholarships | `/admin/scholarships` | Scholarship management | ✅ Working |
| Admin Payments | `/admin/payments` | Payment admin view | ✅ Working |
| Revenue Division | `/revenue` | Revenue sharing system | ✅ Working |
| Partnership Dashboard | `/partnership` | Partnership management | ✅ Working |
| Partnership Discounts | `/partnership/discounts` | Partner pricing | ✅ Working |

### 8. ADMIN & GOVERNANCE

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Admin Dashboard | `/admin` | Stats, users, incidents, audit, sites, inventory, checkout | ✅ Working |
| IAM Console | `/admin/iam` | User CRUD, role/tier, matrix | ✅ Working |
| Account Controls | `/admin/accounts` | User search + admin actions | ✅ Working |
| Audit Log | `/admin/audit` | Audit trail viewer | ✅ Working |
| Analytics | `/admin/analytics` | Program + benchmark analytics | ✅ Working |
| Billing Admin | `/admin/billing` | Credits, refunds, provider keys | ✅ Working |
| Moderation Analytics | `/admin/moderation` | Content moderation stats | ✅ Working |
| AAWAB | `/aawab` | Agent wellness board | ✅ Working |
| AAWAB Admin | `/admin/aawab` | Agent admin | ✅ Working |
| Certification Chamber | `/aawab/chamber` | Agent certification | ✅ Working |
| AI Team Bridge | `/admin/bridge` | Cross-persona dispatch | ✅ Working |

### 9. EXEC & SOVEREIGN CONTROL

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Executive Command Center | `/admin/command` | Stats, users, role/tier, system, health, projects, agenda | ✅ Working |
| Exec Business Office | `/admin/office` | 15+ exec controls, ABO config, break-glass, budget | ✅ Working |
| Business Office | `/business-office` | Revenue engine, deals, jobs, tools | ✅ Working |
| Executive Site Report | `/admin/exec-report` | Site health report | ✅ Working |
| Sage Audit | `/admin/sage-audit` | AI persona audit | ✅ Working |
| Site Control Panel | `/admin/control` | Feature flags, AI spend, broadcast | ✅ Working |
| System Health | `/admin/health` | Health checks + AI costs | ✅ Working |

### 10. COMPLIANCE & SECURITY

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Compliance List | `/compliance` | Compliance modules | ✅ Working |
| Compliance Detail | `/compliance/:slug` | Individual compliance | ✅ Working |
| Auditor Dashboard | `/auditor` | Debt, ledger, risks, summary | ✅ Working |
| Sentinel Research | `/s-research` | Protocol research | ✅ Working |
| Incidents | `/incidents` | Incident reporting | ✅ Working |
| Settings | `/settings` | User settings, sessions, export, delete | ✅ Working |

### 11. GAMES & ENGAGEMENT

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Arcade Landing | `/arcade` | Game listing | ✅ Working |
| Arcade Game | `/arcade/:slug` | Individual game | ✅ Working |
| Competition Arena | `/arena` | Multi-persona competition | ✅ Working |
| My Position | `/my-position` | User's standing + exit flow | ✅ Working |

### 12. PROFILES & IDENTITY

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Unified Profile | `/profile` | Profile + settings + AI + credentials + courses | ✅ Working |
| User Profile | `/profile/:id` | Admin user profile view | ✅ Working |
| Avatar Setup | `/avatar-setup` | Avatar configuration | ✅ Working |
| Login | `/login` | Authentication | ✅ Working |
| Register | `/register` | Account creation | ✅ Working |
| Forgot Password | `/forgot-password` | Password reset | ✅ Working |
| Reset Password | `/reset-password` | Password reset confirm | ✅ Working |
| Factory Reset | `/factory-reset` | Emergency reset | ✅ Working |

### 13. LANDING & ONBOARDING

| Feature | Location | Capability | Status |
|---------|----------|-----------|--------|
| Landing | `/` | Main MORE landing | ✅ Working |
| Landing Marketplace | `/landing` | Marketplace landing | ✅ Working |
| WAI Institute | `/wai-institute` | WAI door | ✅ Working |
| Welcome | `/welcome` | Welcome redirect | ✅ Working |
| Courses | `/courses` | Public course listing | ✅ Working |
| Plans | `/plans` | Membership plans | ✅ Working |
| Help Center | `/help-center` | Help resources | ✅ Working |
| Knowledge Base | `/knowledge-base` | Handbooks | ✅ Working |
| Terms of Service | `/terms` | Legal terms | ✅ Working |
| Privacy Policy | `/privacy` | Privacy policy | ✅ Working |
| Missing Kameron | `/missing-kameron` | Memorial page | ✅ Working |
| Litigation Weapon | `/more/litigation` | Legal reference | ✅ Working |

---

## B. DUPLICATE MAP

Capabilities that overlap, share functions, or serve the same purpose.

### DUPLICATE CLUSTER 1: EXECUTIVE DASHBOARDS (RESOLVED)

**Before:** ExecBusinessOffice (779 lines) + ExecControlPanel (674 lines) + ExecControl (347 lines) + ExecutiveCommandCenter (650 lines) + ExecutiveDirectorDashboard (716 lines) + ExecSystem (1117 lines)

**Status:** ✅ RESOLVED — Merged into ExecBusinessOffice + ExecutiveCommandCenter

### DUPLICATE CLUSTER 2: ADMIN DASHBOARDS (RESOLVED)

**Before:** AdminDashboard (1022 lines) + AdminTools (191 lines)

**Status:** ✅ RESOLVED — Merged AdminTools into AdminDashboard

### DUPLICATE CLUSTER 3: STORE/MEDIA (RESOLVED)

**Before:** Store (68 lines) + MediaStore (731 lines)

**Status:** ✅ RESOLVED — Redirected Store to MediaStore storefront tab

### DUPLICATE CLUSTER 4: HEALTH REPORTS (RESOLVED)

**Before:** SystemHealth (221 lines) + SiteHealthReport (229 lines)

**Status:** ✅ RESOLVED — Merged into SystemHealth

### DUPLICATE CLUSTER 5: PUBLISHING (UNRESOLVED)

**Current state:**
- Creator Studio (`/studio`) — 600 lines, multi-modal creation
- Ghost Producer (`/ghost-producer`) — 534 lines, AI content production
- Social Publish (`/social/publish`) — 303 lines, social media publishing
- Video Presenter (`/studio/video-presenter`) — 403 lines, video scripts
- Ascension Protocols (`/ascension-protocols`) — 1051 lines, content creation
- Vonns Saga (`/vonns-saga`) — 643 lines, narrative creation

**Problem:** Six different content creation tools. All call `/ai/chat`. Each creates different types of content but shares the same AI engine.

### DUPLICATE CLUSTER 6: AI ASSISTANTS (UNRESOLVED)

**Current state:**
- AI Tutor (`/ai`) — educational chat
- Admin Assistant (`/assistant`) — business AI
- Orchestrator (`/orchestrator`) — multi-persona coordination
- Helper (`/helper`) — community Q&A
- Site Guide (`/site-guide`) — navigation help
- Jamil (`/jamil`) — persona chat
- Creative Partner (`/creative-partner`) — creative collaboration

**Problem:** Seven AI interfaces. All use the same LLM gateway. Each has a different system prompt and persona but the underlying mechanism is identical.

### DUPLICATE CLUSTER 7: COMMUNITY (UNRESOLVED)

**Current state:**
- More (`/more`) — posts + needs board
- More Hub (`/app/more`) — community hub
- More Chat (`/more/chat`) — chat rooms
- More Admin (`/more/admin`) — moderation
- More Ops (`/more/ops`) — operations
- Community (`/community`) — landing
- Seshats Hub (`/seshats-hub`) — supervisor view

**Problem:** Seven community-related pages. More, MoreHub, and Community serve overlapping purposes. MoreAdmin and MoreOps are admin views of the same data.

### DUPLICATE CLUSTER 8: CREATOR PAGES (UNRESOLVED)

**Current state:**
- Creator Courses (`/creator/courses`) — course management
- Creator Profile (`/creator/:slug`) — public profile
- Creator Profile Edit (`/creator/profile/edit`) — profile editor
- Creator Earnings (`/creator/earnings`) — earnings + bank
- Creator Payout Dashboard (`/creator/payouts`) — payout summary
- Creators (`/creators`) — creator listing
- Unified Profile (`/profile`) — also shows creator data

**Problem:** Creator Earnings + Creator Payout Dashboard share the same domain. Creator Profile + Creator Profile Edit + Unified Profile overlap on profile management.

### DUPLICATE CLUSTER 9: SCHOLARSHIPS (UNRESOLVED)

**Current state:**
- Scholarship Apply (`/scholarships/apply`) — applicant view
- Sponsor Scholarship (`/sponsor`) — sponsor view
- Admin Scholarships (`/admin/scholarships`) — admin view

**Problem:** Three pages for one feature. Could be one page with role-based tabs.

### DUPLICATE CLUSTER 10: PAYMENT FLOW (UNRESOLVED)

**Current state:**
- Subscribe Page (`/subscribe`) — subscription checkout
- Payment History (`/payment/history`) — transaction history
- Payment Success (`/payment/success`) — success redirect
- Payment Cancel (`/payment/cancel`) — cancel redirect
- Donate Page (`/donate`) — donation checkout
- Admin Payments (`/admin/payments`) — admin view

**Problem:** Subscribe + Donate use the same checkout endpoint. Success + Cancel are 28-44 line redirects. Could be consolidated.

### DUPLICATE CLUSTER 11: COMPLIANCE & AUDIT (UNRESOLVED)

**Current state:**
- Compliance List (`/compliance`) — module listing
- Compliance Detail (`/compliance/:slug`) — individual module
- Auditor Dashboard (`/auditor`) — debt/ledger/risks
- Sage Audit (`/admin/sage-audit`) — AI persona audit
- Audit Log (`/admin/audit`) — audit trail

**Problem:** Audit Log + Auditor Dashboard + Sage Audit are three views of audit data. Compliance is a separate feature but shares the compliance domain.

### DUPLICATE CLUSTER 12: SCHOLARSHIPS (UNRESOLVED)

**Current state:**
- Scholarship Apply (`/scholarships/apply`) — 125 lines, 3 APIs
- Admin Scholarships (`/admin/scholarships`) — 244 lines, 5 APIs
- Sponsor Scholarship (`/sponsor`) — 312 lines, 3 APIs

**Problem:** Three pages for one feature. Could be one page with role-based tabs.

---

## C. CONSOLIDATION PLAN

What merges into what, organized by capability family.

### C.1 PUBLISHING ECOSYSTEM → UNIFIED PUBLISHING STUDIO

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| Creator Studio | 600 | KEEP as primary | Publishing Studio |
| Ghost Producer | 534 | MERGE into Studio | Publishing Studio |
| Social Publish | 303 | MERGE into Studio | Publishing Studio |
| Video Presenter | 403 | MERGE into Studio | Publishing Studio |
| Ascension Protocols | 1051 | MERGE into Studio | Publishing Studio |
| Vonns Saga | 643 | MERGE into Studio | Publishing Studio |

**Result:** One Publishing Studio with tabs: Write, Produce, Publish, Analyze. Tier access controls depth.

### C.2 AI ASSISTANTS → UNIFIED AI CONSOLE

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| AI Tutor | 746 | KEEP as primary | AI Console |
| Admin Assistant | 433 | MERGE as tab | AI Console |
| Orchestrator | 540 | MERGE as tab | AI Console |
| Helper | 820 | MERGE as tab | AI Console |
| Site Guide | 324 | MERGE as tab | AI Console |
| Creative Partner | 453 | MERGE as tab | AI Console |

**Result:** One AI Console with persona selector. Tier controls which personas are available.

### C.3 COMMUNITY → UNIFIED COMMUNITY HUB

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| More | 813 | KEEP as primary | Community Hub |
| More Hub | 420 | MERGE into More | Community Hub |
| Community | 125 | REDIRECT to More | Community Hub |
| More Chat | 189 | MERGE as tab | Community Hub |
| More Admin | 130 | MERGE as tab | Community Hub |
| More Ops | 922 | MERGE as tab | Community Hub |
| Seshats Hub | 1229 | KEEP as separate (supervisor) | Seshats Hub |

**Result:** One Community Hub with tabs: Feed, Needs, Chat, Moderation, Operations.

### C.4 CREATOR ECONOMY → UNIFIED CREATOR DASHBOARD

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| Creator Courses | 435 | KEEP as tab | Creator Dashboard |
| Creator Earnings | 320 | MERGE with Payout | Creator Dashboard |
| Creator Payout Dashboard | 121 | MERGE into Earnings | Creator Dashboard |
| Creator Profile Edit | 241 | MERGE into Unified Profile | Unified Profile |
| Creator Profile | 410 | KEEP as public view | Public Profile |
| Creators | 66 | KEEP as listing | Creators |

**Result:** Creator Dashboard with tabs: Courses, Earnings, Payouts.

### C.5 SCHOLARSHIPS → UNIFIED SCHOLARSHIPS

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| Scholarship Apply | 125 | MERGE as tab | Scholarships |
| Sponsor Scholarship | 312 | MERGE as tab | Scholarships |
| Admin Scholarships | 244 | MERGE as tab | Scholarships |

**Result:** One Scholarships page with role-based tabs: Apply, Sponsor, Admin.

### C.6 PAYMENT FLOW → UNIFIED BILLING

| Current Page | Lines | Action | Target |
|-------------|-------|--------|--------|
| Subscribe Page | 265 | KEEP as primary | Billing |
| Donate Page | 107 | MERGE as tab | Billing |
| Payment History | 108 | MERGE as tab | Billing |
| Payment Success | 44 | REDIRECT to Billing | Billing |
| Payment Cancel | 28 | REDIRECT to Billing | Billing |
| Admin Payments | 95 | MERGE as tab | Billing |

**Result:** One Billing page with tabs: Subscribe, Donate, History, Admin.

---

## D. CAPABILITY ARCHITECTURE

The unified systems that replace duplicates.

### D.1 CORE ENGINE: AI ORCHESTRATION

```
                    LLM GATEWAY (existing)
                           │
              ┌────────────┼────────────┐
              │            │            │
         PERSONAS      TOOLS        MEMORY
              │            │            │
              └────────────┼────────────┘
                           │
                    AI CONSOLE (unified)
                           │
              ┌────────────┼────────────┐
              │            │            │
           TUTOR        ASSISTANT    ORCHESTRATOR
           HELPER       CREATIVE     SITE GUIDE
```

One gateway. One console. Multiple personas. Tier controls access.

### D.2 CORE ENGINE: CONTENT CREATION

```
                 PUBLISHING STUDIO
                        │
         ┌──────────────┼──────────────┐
         │              │              │
       WRITE          PRODUCE       PUBLISH
         │              │              │
    ┌────┼────┐    ┌────┼────┐    ┌────┼────┐
    │    │    │    │    │    │    │    │    │
  Text  Video Audio AI  TTS  Social Sched Analytics Monetize
```

One engine. Multiple creation modes. Tier controls depth.

### D.3 CORE ENGINE: COMMUNITY

```
                 COMMUNITY HUB
                        │
         ┌──────────────┼──────────────┐
         │              │              │
       FEED           CHAT          NEEDS
         │              │              │
    ┌────┼────┐    ┌────┼────┐    ┌────┼────┐
    │    │    │    │    │    │    │    │    │
  Posts Stories Rooms DMs  AI  Requests Offers Matching
```

One hub. Multiple interaction modes. Tier controls reach.

### D.4 CORE ENGINE: CREATOR ECONOMY

```
              CREATOR DASHBOARD
                      │
         ┌────────────┼────────────┐
         │            │            │
      COURSES      EARNINGS     PROFILE
         │            │            │
    ┌────┼────┐   ┌────┼────┐   ┌────┼────┐
    │    │    │   │    │    │   │    │    │
  Create Sell Analytics Bank Payouts Public Edit Portfolio
```

One dashboard. Multiple creator tools. Tier controls capabilities.

---

## E. MEMBERSHIP MATRIX

| Capability | Free | Member ($9.99) | Plus ($19.99) | Pro ($39.99) | Studio ($59.99) | Director ($99.99) |
|-----------|------|----------------|---------------|--------------|-----------------|-------------------|
| **AI Access** |
| AI Tutor | Basic | ✓ | ✓ | ✓ | ✓ | ✓ |
| AI Helper | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| AI Site Guide | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| AI Assistant | — | Basic | ✓ | ✓ | ✓ | ✓ |
| AI Creative Partner | — | — | Basic | ✓ | ✓ | ✓ |
| AI Orchestrator | — | — | — | Basic | ✓ | ✓ |
| AI Jamil | — | — | — | — | Basic | ✓ |
| **Publishing** |
| Text Creation | Read-only | Write | Write + Edit | Full | Full | Full + AI |
| Video Scripts | — | Basic | ✓ | ✓ | Advanced | Full |
| Audio Production | — | — | Basic | ✓ | Advanced | Full |
| Social Publishing | — | — | Basic | ✓ | Advanced | Full |
| AI Content Gen | Limited | Basic | ✓ | Advanced | Advanced | Maximum |
| **Learning** |
| Course Access | 2 courses | 5 courses | 10 courses | All courses | All + labs | All + mentorship |
| Lab Access | — | Basic | ✓ | ✓ | Advanced | Full |
| Competencies | — | Basic | ✓ | ✓ | Advanced | Full |
| Certificates | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Community** |
| Posts | Read | ✓ | ✓ | ✓ | ✓ | ✓ |
| Chat | — | ✓ | ✓ | ✓ | ✓ | ✓ |
| Needs Board | Read | ✓ | ✓ | ✓ | ✓ | ✓ |
| Moderation | — | — | — | Basic | ✓ | Full |
| **Creator Economy** |
| Course Creation | — | 1 course | 5 courses | 10 courses | Unlimited | Unlimited |
| Earnings Dashboard | — | Basic | ✓ | ✓ | Advanced | Full |
| Payout | — | Monthly | Monthly | Bi-weekly | Weekly | On-demand |
| **Storage** |
| Content | 100MB | 1GB | 5GB | 25GB | 100GB | Custom |
| Media | — | 500MB | 2GB | 10GB | 50GB | Custom |
| **Governance** |
| Audit Log | — | — | Read | Read | Read + Export | Full |
| Admin Dashboard | — | — | — | Basic | ✓ | Full |
| Exec Controls | — | — | — | — | — | ✓ |
| **Soul/Memory** |
| NAM Personality | Basic | Basic | ✓ | ✓ | ✓ | ✓ |
| Memory | Session | 7 days | 30 days | 90 days | 1 year | Permanent |
| Goal Tracking | — | — | Basic | ✓ | Advanced | Full |
| Dream Engine | — | — | — | — | Basic | Advanced |

---

## F. PRICING/VALUE ANALYSIS

Current tier structure from the codebase:
- Free ($0) — basic access
- Member ($9.99/mo) — community + courses
- Plus ($19.99/mo) — creator tools
- Pro ($39.99/mo) — advanced AI + analytics
- Studio ($59.99/mo) — professional tools
- Director ($99.99/mo) — full platform

**Value mapping:**
- Free → Discovery (can see everything, can do little)
- Member → Participation (community + learning)
- Plus → Creation (publish + sell)
- Pro → Professional (advanced tools + analytics)
- Studio → Business (team + automation)
- Director → Enterprise (full control + orchestration)

---

## G. NAVIGATION ARCHITECTURE

One canonical home for every capability.

```
HOME
│
├── 🏠 DASHBOARD (Student / Creator / Admin / Exec)
│
├── 🧠 AI CONSOLE
│   ├── Tutor
│   ├── Assistant
│   ├── Helper
│   ├── Site Guide
│   ├── Creative Partner
│   ├── Orchestrator
│   └── Jamil
│
├── ✍️ PUBLISHING STUDIO
│   ├── Write (text, articles, books)
│   ├── Produce (video, audio, scripts)
│   ├── Publish (social, schedule, distribute)
│   └── Analyze (performance, audience)
│
├── 📚 LEARN
│   ├── Courses
│   ├── Labs
│   ├── Competencies
│   ├── Certificates
│   └── Portfolio
│
├── 👥 COMMUNITY
│   ├── Feed
│   ├── Chat
│   ├── Needs Board
│   ├── Events
│   └── Moderation (admin)
│
├── 🎵 MUSIC
│   ├── Store
│   ├── Creator Lounge
│   ├── Playlists
│   └── Band
│
├── 💰 EARNINGS
│   ├── Courses (sell)
│   ├── Media (sell)
│   ├── Earnings Dashboard
│   ├── Payouts
│   └── Partnerships
│
├── 🏛️ SANCTUARY
│   ├── Ascension Protocols
│   ├── Vonns Saga
│   ├── Trash Pantheon
│   └── Elder Council
│
├── ⚔️ COMPETE
│   ├── Arena
│   ├── Arcade
│   ├── Leaderboard
│   └── Scholarships
│
├── ⚙️ ADMIN (admin+)
│   ├── Dashboard
│   ├── IAM Console
│   ├── Payments
│   ├── Analytics
│   ├── Audit
│   └── System Health
│
└── 👑 EXEC (executive)
    ├── Command Center
    ├── Business Office
    ├── Site Control
    └── Reports
```

---

## H. RETENTION LOOPS

Why users return to each ecosystem.

### AI CONSOLE
```
Ask question → Get answer → Save to memory → Ask follow-up → Build relationship → Return for context
```

### PUBLISHING STUDIO
```
Idea → Draft → Edit → Publish → Share → Get feedback → Analyze → Improve → Next project
```

### LEARN
```
Enroll → Study → Complete module → Take quiz → Earn certificate → Build portfolio → Take next course
```

### COMMUNITY
```
Post → Get responses → Help others → Build reputation → Earn XP → Climb leaderboard → Return for status
```

### EARNINGS
```
Create course → Set price → Get first sale → See earnings → Optimize → Scale → Monthly payout → Reinvest
```

### SANCTUARY
```
Reflect → Create → Share → Connect → Heal → Grow → Return for continuity
```

---

## I. MIGRATION PLAN

How existing functionality moves without breaking users.

### Phase 1: No-Break Redirects (Week 1)
- All old routes get `<Navigate to={newRoute} replace />`
- Old URLs still work, just redirect
- Zero user disruption

### Phase 2: Feature Merging (Week 2-3)
- Pages are combined (tabs, not new pages)
- Old imports cleaned from App.js
- File cleanup

### Phase 3: Navigation Update (Week 4)
- AppShell nav updated to reflect new structure
- Sidebar shows consolidated items
- Old nav items removed

### Phase 4: Backend Consolidation (Week 5-6)
- Shared services extracted
- Duplicate endpoints consolidated
- Entitlement system enhanced

---

## J. TECHNICAL DEPENDENCY MAP

Shared services consumed by each ecosystem.

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

## ACCEPTANCE CHECKLIST

- [ ] No significant duplicate user-facing capabilities
- [ ] One canonical location for each major capability
- [ ] Shared underlying engines wherever practical
- [ ] Central membership entitlement system
- [ ] Higher tiers provide genuinely superior capability
- [ ] Existing functionality preserved through consolidation
- [ ] Existing users can migrate safely
- [ ] Navigation is understandable
- [ ] NAM can orchestrate the ecosystem
- [ ] Publishing capabilities are unified
- [ ] AI capabilities are unified
- [ ] Analytics are unified
- [ ] Memory is unified
- [ ] Billing is unified
- [ ] Storage is unified
- [ ] Permissions are centralized
- [ ] Retention loops exist for major ecosystems
- [ ] Upgrade paths are understandable
- [ ] Feature limits are enforced server-side
- [ ] No artificial duplicate products exist merely to justify tiers
- [ ] Deprecated features have migration paths
- [ ] Technical debt is reduced rather than increased
