# CONSOLIDATION PLAN — DETAILED MIGRATION PATHS

**Date:** August 21, 2026
**Status:** Ready for implementation

---

## CONSOLIDATION 1: AI ASSISTANTS → UNIFIED AI CONSOLE

### Current State (7 pages → 1)
- AI Tutor (`/ai` — 746 lines)
- Admin Assistant (`/assistant` — 433 lines)
- Orchestrator (`/orchestrator` — 540 lines)
- Helper (`/helper` — 820 lines)
- Site Guide (`/site-guide` — 324 lines)
- Creative Partner Hub (`/creative-partner` — 453 lines)
- Jamil (`/jamil` — 363 lines)

### Target: AI Console (`/ai`)
**One page with persona selector.** Tier controls which personas are available.

**Architecture:**
```
AI CONSOLE
├── Persona Selector (sidebar)
├── Chat Interface (shared)
├── Memory Panel (persistent)
├── History (searchable)
└── Settings (per-persona)
```

**Tier Access:**
- Free: Helper, Site Guide
- Member: + AI Tutor
- Plus: + Creative Partner
- Pro: + Admin Assistant
- Studio: + Orchestrator
- Director: + Jamil

**Migration:**
1. Keep AI Tutor as primary page
2. Add persona selector to sidebar
3. Move other assistant content into persona tabs
4. Redirect old routes to `/ai?persona={name}`
5. Delete old pages after verification

---

## CONSOLIDATION 2: PUBLISHING → UNIFIED PUBLISHING STUDIO

### Current State (7 pages → 1)
- Creator Studio (`/studio` — 600 lines)
- Ghost Producer (`/ghost-producer` — 534 lines)
- Social Publish (`/social/publish` — 303 lines)
- Video Presenter (`/studio/video-presenter` — 403 lines)
- Ascension Protocols (`/ascension-protocols` — 1051 lines)
- Vonns Saga (`/vonns-saga` — 643 lines)
- Trash Pantheon (`/trash` — 218 lines)

### Target: Publishing Studio (`/studio`)
**One page with creation mode tabs.** Tier controls depth.

**Architecture:**
```
PUBLISHING STUDIO
├── Write (text, articles, books)
├── Produce (video, audio, scripts)
├── Publish (social, schedule, distribute)
├── Analyze (performance, audience)
└── Library (all published content)
```

**Tier Access:**
- Free: Read-only (browse published content)
- Member: Basic writing (text only)
- Plus: + Video scripts, audio production
- Pro: + Social publishing, scheduling
- Studio: + AI content generation, analytics
- Director: + Full automation, team collaboration

**Migration:**
1. Keep Creator Studio as primary page
2. Add tabs for Write/Produce/Publish/Analyze
3. Merge Ghost Producer into Produce tab
4. Merge Social Publish into Publish tab
5. Merge Video Presenter into Produce tab
6. Merge Ascension Protocols into Write tab
7. Keep Vonns Saga as a Write sub-mode
8. Redirect old routes to `/studio?tab={mode}`

---

## CONSOLIDATION 3: COMMUNITY → UNIFIED COMMUNITY HUB

### Current State (8 pages → 1)
- More (`/more` — 813 lines)
- More Hub (`/app/more` — 420 lines)
- Community (`/community` — 125 lines)
- More Chat (`/more/chat` — 189 lines)
- More Admin (`/more/admin` — 130 lines)
- More Ops (`/more/ops` — 922 lines)
- MoreHelpCenter (`/more-help-center` — 2369 lines)
- Seshats Hub (`/seshats-hub` — 1229 lines)

### Target: Community Hub (`/more`)
**One page with mode tabs.** Seshats Hub remains separate (supervisor-specific).

**Architecture:**
```
COMMUNITY HUB
├── Feed (posts, stories)
├── Needs (requests, offers)
├── Chat (rooms, DMs)
├── Moderation (admin)
├── Operations (admin)
└── Analytics (admin)
```

**Tier Access:**
- Free: Read-only (browse feed)
- Member: + Post, Chat, Respond to needs
- Plus: + Create rooms, Moderate own content
- Pro: + Analytics, Advanced moderation
- Studio: + Full moderation, Operations
- Director: + Seshats Hub access

**Migration:**
1. Keep More as primary page
2. Add tabs for Feed/Needs/Chat/Moderation/Operations
3. Merge More Hub into Feed tab
4. Merge More Chat into Chat tab
5. Merge More Admin into Moderation tab
6. Merge More Ops into Operations tab
7. Decompose MoreHelpCenter into owning pages
8. Keep Seshats Hub as separate (supervisor role)
9. Redirect old routes to `/more?tab={mode}`

---

## CONSOLIDATION 4: CREATOR → UNIFIED CREATOR DASHBOARD

### Current State (7 pages → 1)
- Creator Courses (`/creator/courses` — 435 lines)
- Creator Profile (`/creator/:slug` — 410 lines)
- Creator Profile Edit (`/creator/profile/edit` — 241 lines)
- Creator Earnings (`/creator/earnings` — 320 lines)
- Creator Payout Dashboard (`/creator/payouts` — 121 lines)
- Creators (`/creators` — 66 lines)
- Creative Partner Hub (`/creative-partner` — 453 lines)

### Target: Creator Dashboard (`/creator/dashboard`)
**One page with creator mode tabs.** Public profile stays separate.

**Architecture:**
```
CREATOR DASHBOARD
├── Courses (create, manage, sell)
├── Earnings (revenue, payouts, bank)
├── Profile (edit, public view)
├── Collaborate (Creative Partner)
└── Analytics (performance, audience)
```

**Tier Access:**
- Free: Read-only (browse creators)
- Member: Basic profile
- Plus: + Create 1 course, Basic earnings
- Pro: + 5 courses, Advanced analytics
- Studio: + Unlimited courses, Team collaboration
- Director: + Full platform access

**Migration:**
1. Keep Creator Courses as primary page
2. Add tabs for Courses/Earnings/Profile/Collaborate
3. Merge Creator Earnings + Payout Dashboard into Earnings tab
4. Merge Creator Profile Edit into Profile tab
5. Merge Creative Partner into Collaborate tab
6. Keep Creator Profile as public view (`/creator/:slug`)
7. Keep Creators as listing (`/creators`)
8. Redirect old routes to `/creator/dashboard?tab={mode}`

---

## CONSOLIDATION 5: SCHOLARSHIPS → UNIFIED SCHOLARSHIPS

### Current State (3 pages → 1)
- Scholarship Apply (`/scholarships/apply` — 125 lines)
- Sponsor Scholarship (`/sponsor` — 312 lines)
- Admin Scholarships (`/admin/scholarships` — 244 lines)

### Target: Scholarships (`/scholarships`)
**One page with role-based tabs.**

**Architecture:**
```
SCHOLARSHIPS
├── Apply (student view)
├── Sponsor (donor view)
├── Admin (management view)
└── Funds (available scholarships)
```

**Migration:**
1. Create unified page with role-based tabs
2. Move existing content into tabs
3. Redirect old routes to `/scholarships?tab={role}`

---

## CONSOLIDATION 6: PAYMENT → UNIFIED BILLING

### Current State (6 pages → 1)
- Subscribe Page (`/subscribe` — 265 lines)
- Donate Page (`/donate` — 107 lines)
- Payment History (`/payment/history` — 108 lines)
- Payment Success (`/payment/success` — 44 lines)
- Payment Cancel (`/payment/cancel` — 28 lines)
- Admin Payments (`/admin/payments` — 95 lines)

### Target: Billing (`/billing`)
**One page with billing mode tabs.**

**Architecture:**
```
BILLING
├── Subscribe (membership plans)
├── Donate (one-time support)
├── History (transaction log)
├── Manage (cancel, update)
└── Admin (payments overview)
```

**Migration:**
1. Keep Subscribe as primary page
2. Add tabs for Subscribe/Donate/History/Manage
3. Merge Donate into Donate tab
4. Merge Payment History into History tab
5. Keep Payment Success/Cancel as redirects
6. Merge Admin Payments into Admin tab
7. Redirect old routes to `/billing?tab={mode}`

---

## CONSOLIDATION 7: STORE → INTEGRATED INTO MEDIA STORE

### Current State
- Store (`/store` — 68 lines) — Gumroad embed
- Media Store (`/store` — 731 lines) — Full marketplace

### Target: Media Store (`/store`)
**Already done.** Store redirects to Media Store's Storefront tab.

---

## CONSOLIDATION 8: HEALTH → UNIFIED HEALTH

### Current State
- System Health (`/admin/health` — 221 lines)
- Site Health Report (`/admin/health-report` — 229 lines)

### Target: System Health (`/admin/health`)
**Already done.** Site Health Report merged into System Health.

---

## CONSOLIDATION 9: ADMIN TOOLS → INTEGRATED INTO ADMIN DASHBOARD

### Current State
- Admin Dashboard (`/admin` — 1231 lines)
- Admin Tools (`/admin/tools` — 191 lines)

### Target: Admin Dashboard (`/admin`)
**Already done.** Admin Tools merged as Sites/Inventory/Checkout tabs.

---

## CONSOLIDATION 10: EXEC CONTROLS → INTEGRATED INTO EXEC BUSINESS OFFICE

### Current State
- Exec Business Office (`/admin/office` — 850 lines)
- Exec Control Panel (`/admin/exec-control` — 674 lines)
- Exec Control (`/admin/office-control` — 347 lines)

### Target: Exec Business Office (`/admin/office`)
**Already done.** Exec Control Panel + Exec Control merged with ABO config.

---

## CONSOLIDATION 11: EXEC DASHBOARDS → INTEGRATED INTO EXEC COMMAND CENTER

### Current State
- Executive Command Center (`/admin/command` — 650 lines)
- Exec System (`/admin/system` — 1117 lines)
- Executive Director Dashboard (`/admin/director` — 716 lines)

### Target: Executive Command Center (`/admin/command`)
**Already done.** Exec System + Executive Director Dashboard redirected.

---

## IMPLEMENTATION PRIORITY

| Priority | Consolidation | Pages Saved | Lines Saved | Effort |
|----------|--------------|-------------|-------------|--------|
| 1 | AI Console | 6 | ~3,533 | Medium |
| 2 | Publishing Studio | 6 | ~3,152 | Medium |
| 3 | Community Hub | 6 | ~4,223 | High |
| 4 | Creator Dashboard | 4 | ~1,122 | Low |
| 5 | Scholarships | 2 | ~556 | Low |
| 6 | Billing | 4 | ~484 | Low |
| **Total** | | **28 pages** | **~13,070 lines** | |

---

## MIGRATION SAFETY

Every consolidation follows this pattern:
1. **Redirect first** — Old routes get `<Navigate to={newRoute} replace />`
2. **Merge content** — Old page content moves into tabs
3. **Clean imports** — Remove old imports from App.js
4. **Delete files** — Remove old page files
5. **Verify** — Run typecheck to catch broken references

**Zero user disruption** — Old URLs still work, just redirect to the consolidated page.
