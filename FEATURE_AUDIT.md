# M.O.R.E. HELP CENTER — COMPLETE FEATURE INVENTORY

**Date:** August 21, 2026
**Method:** Direct code inspection of all 126 routed pages + 516 backend endpoints

---

## FEATURE FAMILY 1: AI & ASSISTANTS

### 1.1 AI Tutor (`/ai` — 746 lines)
- **Purpose:** Educational AI chat for learning
- **APIs:** `/ai/chat`, `/ai/consent`, `/ai/sage/integrity`, `/ai/sage/resolve_mode`
- **User Type:** All authenticated users
- **Dependencies:** LLM Gateway, consent system, persona system
- **Status:** ✅ Working
- **Retention Loop:** Ask → Learn → Practice → Track progress → Return for next lesson

### 1.2 Admin Assistant (`/assistant` — 433 lines)
- **Purpose:** Business AI for emails, documents, tasks
- **APIs:** `/assistant/chat` (with TTS, speech recognition)
- **User Type:** Admin+
- **Dependencies:** LLM Gateway, TTS engine
- **Status:** ✅ Working
- **Retention Loop:** Draft → Send → Track → Manage → Return for next task

### 1.3 Orchestrator (`/orchestrator` — 540 lines)
- **Purpose:** Multi-persona AI coordination
- **APIs:** `/ai/orchestrator`
- **User Type:** Executive+
- **Dependencies:** LLM Gateway, persona system
- **Status:** ✅ Working
- **Retention Loop:** Coordinate → Execute → Review → Optimize → Return for next project

### 1.4 Helper (`/helper` — 820 lines)
- **Purpose:** Community Q&A assistant
- **APIs:** `/ai/helper` (via fetch), `/public/helper/ask`
- **User Type:** All (public + authenticated)
- **Dependencies:** LLM Gateway, knowledge base
- **Status:** ✅ Working
- **Retention Loop:** Ask → Get answer → Save → Ask follow-up → Build knowledge

### 1.5 Site Guide (`/site-guide` — 324 lines)
- **Purpose:** Interactive platform navigation
- **APIs:** `/site-guide/chat`, `/site-guide/status`
- **User Type:** All
- **Dependencies:** LLM Gateway
- **Status:** ✅ Working
- **Retention Loop:** Navigate → Discover → Use feature → Return for guidance

### 1.6 Creative Partner Hub (`/creative-partner` — 453 lines)
- **Purpose:** AI creative collaboration
- **APIs:** `/creative-partner/chat`, `/creative-partner/contribution`, `/creative-partner/contributions`
- **User Type:** Instructor+
- **Dependencies:** LLM Gateway
- **Status:** ✅ Working
- **Retention Loop:** Create → Collaborate → Publish → Analyze → Return for next project

### 1.7 Jamil (`/jamil` — 363 lines)
- **Purpose:** AI persona with TTS, transcription, knowledge
- **APIs:** `/jamil/chat`, `/jamil/transcribe`
- **User Type:** Admin+
- **Dependencies:** LLM Gateway, ElevenLabs, knowledge base
- **Status:** ✅ Working
- **Retention Loop:** Chat → Transcribe → Learn → Remember → Return for continuity

### 1.8 Personas (`/personas` — 97 lines)
- **Purpose:** AI persona listing
- **APIs:** `/personas`
- **User Type:** All
- **Dependencies:** Persona loader
- **Status:** ✅ Working

### 1.9 Persona Profile (`/personas/:slug` — 432 lines)
- **Purpose:** Individual persona chat + controls
- **APIs:** `/personas/{slug}`, `/personas/{slug}/chat`, `/personas/{slug}/controls`
- **User Type:** All
- **Dependencies:** LLM Gateway, persona system
- **Status:** ✅ Working

---

## FEATURE FAMILY 2: PUBLISHING & CONTENT

### 2.1 Creator Studio (`/studio` — 600 lines)
- **Purpose:** Multi-modal content creation
- **APIs:** Studio endpoints (altar, cheer, lyric, metadata, script, sound, sovereign)
- **User Type:** Pro+
- **Dependencies:** LLM Gateway, media system
- **Status:** ✅ Working
- **Retention Loop:** Create → Edit → Refine → Publish → Share → Return

### 2.2 Ghost Producer (`/ghost-producer` — 534 lines)
- **Purpose:** AI-assisted content production
- **APIs:** `/ai/chat`
- **User Type:** Pro+
- **Dependencies:** LLM Gateway
- **Status:** ✅ Working
- **Retention Loop:** Describe → Generate → Edit → Publish → Monetize → Return

### 2.3 Social Publish (`/social/publish` — 303 lines)
- **Purpose:** AI social media publishing
- **APIs:** `/ai/social-blast`
- **User Type:** Pro+
- **Dependencies:** LLM Gateway
- **Status:** ✅ Working
- **Retention Loop:** Write → Adapt → Schedule → Publish → Analyze → Return

### 2.4 Video Presenter (`/studio/video-presenter` — 403 lines)
- **Purpose:** Scene-based video script builder
- **APIs:** None (pure frontend)
- **User Type:** Pro+
- **Status:** ✅ Working

### 2.5 Ascension Protocols (`/ascension-protocols` — 1051 lines)
- **Purpose:** Content creation system
- **APIs:** None (pure frontend)
- **User Type:** All
- **Status:** ✅ Working

### 2.6 Vonns Saga (`/vonns-saga` — 643 lines)
- **Purpose:** AI narrative/story creation
- **APIs:** `/ai/sage/tts`
- **User Type:** All
- **Dependencies:** LLM Gateway, TTS
- **Status:** ✅ Working

### 2.7 Trash Pantheon (`/trash` — 218 lines)
- **Purpose:** Worst-idea brainstorming
- **APIs:** None
- **User Type:** All
- **Status:** ✅ Working

---

## FEATURE FAMILY 3: MUSIC & AUDIO

### 3.1 Media Store (`/store` — 731 lines)
- **Purpose:** Browse, buy, sell, library — full media marketplace
- **APIs:** `/media/products`, `/media/products/mine`, `/media/purchases`, `/media/upload`
- **User Type:** All
- **Dependencies:** Payments, media system
- **Status:** ✅ Working
- **Retention Loop:** Browse → Buy → Listen → Discover → Buy again

### 3.2 Band On Page (`/band` — 426 lines)
- **Purpose:** Music band listings, bookings
- **APIs:** `/band/listings`, `/band/book`, `/band/my-listing`, `/band/bookings`
- **User Type:** All
- **Status:** ✅ Working

### 3.3 Creator Lounge (`/creator-lounge` — 342 lines)
- **Purpose:** Music project collaboration
- **APIs:** `/creator-lounge/projects`, `/creator-lounge/my-projects`
- **User Type:** Creator+
- **Status:** ✅ Working

### 3.4 Playlist Dashboard (`/playlist/dashboard` — 390 lines)
- **Purpose:** Spotify playlist management
- **APIs:** `/playlist/dashboard`, `/playlist/gateway/create`
- **User Type:** Creator+
- **Status:** ✅ Working

### 3.5 Playlist Submit (`/playlist/:slug/submit` — 402 lines)
- **Purpose:** Submit tracks to playlists
- **APIs:** `/playlist/submit`, `/playlist/complete-step`
- **User Type:** Creator+
- **Status:** ✅ Working

---

## FEATURE FAMILY 4: LEARNING & EDUCATION

### 4.1 Modules List (`/modules` — 236 lines)
- **Purpose:** Course catalog
- **APIs:** `/creator/courses/published`, `/creator/enrollments/me`, `/progress/me`
- **User Type:** All
- **Status:** ✅ Working
- **Retention Loop:** Browse → Enroll → Learn → Complete → Next course

### 4.2 Module View (`/modules/:slug` — 214 lines)
- **Purpose:** Individual module with quizzes
- **APIs:** `/progress/start`, `/progress/quiz`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.3 Labs Hub (`/labs` — 89 lines)
- **Purpose:** Lab listing
- **APIs:** `/labs`, `/competencies`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.4 Lab Detail (`/labs/:slug` — 159 lines)
- **Purpose:** Individual lab submission
- **APIs:** `/labs/{slug}`, `/labs/{slug}/submit`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.5 Lab Simulations (`/lab-simulations` — 650 lines)
- **Purpose:** Interactive simulations
- **APIs:** None (pure frontend)
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.6 Competencies (`/competencies` — 70 lines)
- **Purpose:** Skill tracking
- **APIs:** `/competencies`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.7 Certificates (`/certificates` — 56 lines)
- **Purpose:** Certificate display
- **APIs:** `/certificates/me`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.8 Credentials (`/credentials` — 127 lines)
- **Purpose:** Credential management
- **APIs:** `/credentials/me`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.9 Attendance (`/attendance` — 99 lines)
- **Purpose:** Attendance tracking
- **APIs:** `/attendance`, `/attendance/roster`
- **User Type:** Instructor+
- **Status:** ✅ Working

### 4.10 Adaptive (`/adaptive` — 101 lines)
- **Purpose:** Adaptive learning path
- **APIs:** `/adaptive/me`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.11 Portfolio (`/portfolio` — 86 lines)
- **Purpose:** Portfolio builder
- **APIs:** `/portfolio/me`, `/portfolio/publish`
- **User Type:** Enrolled users
- **Status:** ✅ Working

### 4.12 Public Portfolio (`/u/:username` — 66 lines)
- **Purpose:** Public portfolio view
- **APIs:** `/creator/profiles/public`
- **User Type:** Public
- **Status:** ✅ Working

### 4.13 Courses (`/courses` — 212 lines)
- **Purpose:** Public course listing
- **APIs:** `/creator/courses/published`, `/creator/enrollments/me`
- **User Type:** Public
- **Status:** ✅ Working

---

## FEATURE FAMILY 5: COMMUNITY

### 5.1 More (`/more` — 813 lines)
- **Purpose:** Posts + needs board
- **APIs:** `/more/posts`, `/more/need`
- **User Type:** Member+
- **Status:** ✅ Working
- **Retention Loop:** Post → Get responses → Help others → Build reputation → Return

### 5.2 More Hub (`/app/more` — 420 lines)
- **Purpose:** Community hub
- **APIs:** `/more/posts`, `/more/need`, `/more/needs`
- **User Type:** Member+
- **Status:** ✅ Working

### 5.3 Community (`/community` — 125 lines)
- **Purpose:** Community landing
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

### 5.4 More Chat (`/more/chat` — 189 lines)
- **Purpose:** Community chat rooms
- **APIs:** `/more/chat/send`
- **User Type:** Member+
- **Status:** ✅ Working

### 5.5 More Admin (`/more/admin` — 130 lines)
- **Purpose:** Community moderation
- **APIs:** `/more/admin/flags`, `/more/purge`
- **User Type:** Admin+
- **Status:** ✅ Working

### 5.6 More Ops (`/more/ops` — 922 lines)
- **Purpose:** Community operations
- **APIs:** `/more/department/chat`, `/more/department/history`
- **User Type:** Admin+
- **Status:** ✅ Working

### 5.7 MoreHelpCenter (`/more-help-center` — 2369 lines)
- **Purpose:** Mega-dashboard (everything in one page)
- **APIs:** 28 unique APIs
- **User Type:** Admin+
- **Status:** ⚠️ Overflow — needs decomposition

### 5.8 Seshats Hub (`/seshats-hub` — 1229 lines)
- **Purpose:** Supervisor operations center
- **APIs:** 22 unique APIs (supervisor, backup, moderation, escalations)
- **User Type:** Supervisor+
- **Status:** ✅ Working

---

## FEATURE FAMILY 6: CREATOR ECONOMY

### 6.1 Creator Courses (`/creator/courses` — 435 lines)
- **Purpose:** Course management
- **APIs:** `/creator/courses`
- **User Type:** Creator+
- **Status:** ✅ Working
- **Retention Loop:** Create → Publish → Sell → Track → Optimize → Return

### 6.2 Creator Profile (`/creator/:slug` — 410 lines)
- **Purpose:** Public creator profile
- **APIs:** None (pure frontend)
- **User Type:** Public
- **Status:** ✅ Working

### 6.3 Creator Profile Edit (`/creator/profile/edit` — 241 lines)
- **Purpose:** Profile editor
- **APIs:** `/creator/profile`, `/creator/profile/me`
- **User Type:** Creator+
- **Status:** ✅ Working

### 6.4 Creator Earnings (`/creator/earnings` — 320 lines)
- **Purpose:** Earnings + bank setup
- **APIs:** `/creator/earnings`, `/creator/bank-account`, `/creator/payouts`
- **User Type:** Creator+
- **Status:** ✅ Working

### 6.5 Creator Payout Dashboard (`/creator/payouts` — 121 lines)
- **Purpose:** Payout summary
- **APIs:** `/creator/payout-summary`
- **User Type:** Creator+
- **Status:** ✅ Working

### 6.6 Creators (`/creators` — 66 lines)
- **Purpose:** Creator listing
- **APIs:** `/creator/profiles/public`
- **User Type:** Public
- **Status:** ✅ Working

### 6.7 Creative Partner Hub (`/creative-partner` — 453 lines)
- **Purpose:** AI creative collaboration
- **APIs:** `/creative-partner/chat`, `/creative-partner/contribution`
- **User Type:** Instructor+
- **Status:** ✅ Working

---

## FEATURE FAMILY 7: MONETIZATION

### 7.1 Subscribe Page (`/subscribe` — 265 lines)
- **Purpose:** Subscription checkout
- **APIs:** `/payments/checkout`, `/payments/portal`
- **User Type:** Public
- **Status:** ✅ Working

### 7.2 Payment History (`/payment/history` — 108 lines)
- **Purpose:** Transaction history
- **APIs:** `/payments/history`, `/payments/portal`
- **User Type:** Member+
- **Status:** ✅ Working

### 7.3 Payment Success (`/payment/success` — 44 lines)
- **Purpose:** Success redirect
- **APIs:** None
- **User Type:** Member+
- **Status:** ✅ Working

### 7.4 Payment Cancel (`/payment/cancel` — 28 lines)
- **Purpose:** Cancel redirect
- **APIs:** None
- **User Type:** Member+
- **Status:** ✅ Working

### 7.5 Donate Page (`/donate` — 107 lines)
- **Purpose:** Donation checkout
- **APIs:** `/payments/checkout`
- **User Type:** Public
- **Status:** ✅ Working

### 7.6 Platform Prices (`/admin/prices` — 284 lines)
- **Purpose:** Price configuration
- **APIs:** `/admin/prices`
- **User Type:** Admin+
- **Status:** ✅ Working

### 7.7 BYOK (`/byok` — 292 lines)
- **Purpose:** Bring Your Own Key
- **APIs:** `/byok/key`, `/byok/status`, `/byok/checkout`, `/byok/admin`
- **User Type:** Pro+
- **Status:** ✅ Working

### 7.8 Scholarship Apply (`/scholarships/apply` — 125 lines)
- **Purpose:** Scholarship application
- **APIs:** `/scholarships/apply`, `/scholarships/funds`
- **User Type:** Student+
- **Status:** ✅ Working

### 7.9 Sponsor Scholarship (`/sponsor` — 312 lines)
- **Purpose:** Scholarship sponsorship
- **APIs:** `/scholarships/pledge`, `/scholarships/sponsor/mine`
- **User Type:** Member+
- **Status:** ✅ Working

### 7.10 Admin Scholarships (`/admin/scholarships` — 244 lines)
- **Purpose:** Scholarship management
- **APIs:** `/scholarships/admin/applications`, `/scholarships/admin/awards`
- **User Type:** Admin+
- **Status:** ✅ Working

### 7.11 Revenue Division (`/revenue` — 721 lines)
- **Purpose:** Revenue sharing system
- **APIs:** `/revenue/api-keys`, `/revenue/courses/license`, `/revenue/exec-overview`
- **User Type:** Admin+
- **Status:** ✅ Working

### 7.12 Partnership Dashboard (`/partnership` — 241 lines)
- **Purpose:** Partnership management
- **APIs:** `/partnership/status`, `/partnership/ledger`
- **User Type:** Admin+
- **Status:** ✅ Working

### 7.13 Partnership Discounts (`/partnership/discounts` — 225 lines)
- **Purpose:** Partner pricing
- **APIs:** `/partnership/status`
- **User Type:** Admin+
- **Status:** ✅ Working

---

## FEATURE FAMILY 8: ADMIN

### 8.1 Admin Dashboard (`/admin` — 1231 lines)
- **Purpose:** Stats, users, incidents, audit, sites, inventory, checkout
- **APIs:** `/admin/stats`, `/admin/users`, `/incidents`, `/admin/audit`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.2 IAM Console (`/admin/iam` — 381 lines)
- **Purpose:** User CRUD, role/tier, matrix
- **APIs:** `/admin/users`, `/admin/rbac/matrix`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.3 Account Controls (`/admin/accounts` — 665 lines)
- **Purpose:** User search + admin actions
- **APIs:** `/admin/users`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.4 Audit Log (`/admin/audit` — 60 lines)
- **Purpose:** Audit trail viewer
- **APIs:** `/admin/audit`
- **User Type:** Support Staff+
- **Status:** ✅ Working

### 8.5 Analytics (`/admin/analytics` — 160 lines)
- **Purpose:** Program + benchmark analytics
- **APIs:** `/analytics/program`, `/analytics/benchmark`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.6 Billing Admin (`/admin/billing` — 302 lines)
- **Purpose:** Credits, refunds, provider keys
- **APIs:** `/billing/credits/grant`, `/billing/refunds/cash`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.7 Moderation Analytics (`/admin/moderation` — 124 lines)
- **Purpose:** Content moderation stats
- **APIs:** `/more/admin/moderation-stats`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.8 AAWAB (`/aawab` — agent registry)
- **Purpose:** Agent wellness board
- **APIs:** `/aawab/agents`, `/aawab/registry`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.9 AI Team Bridge (`/admin/bridge` — 588 lines)
- **Purpose:** Cross-persona dispatch
- **APIs:** `/bridge/config`, `/bridge/dispatch`, `/bridge/personas`
- **User Type:** Admin+
- **Status:** ✅ Working

### 8.10 Provider Gateway (`/admin/providers` — 326 lines)
- **Purpose:** AI provider key management
- **APIs:** `/providers/quick-setup`, `/providers/usage-log`
- **User Type:** Executive+
- **Status:** ✅ Working

---

## FEATURE FAMILY 9: EXECUTIVE

### 9.1 Executive Command Center (`/admin/command` — 650 lines)
- **Purpose:** Mission control — stats, users, role/tier, system, health, projects
- **APIs:** `/admin/stats`, `/admin/users`, `/exec/control/user/role`, `/health`
- **User Type:** Executive+
- **Status:** ✅ Working

### 9.2 Exec Business Office (`/admin/office` — 850 lines)
- **Purpose:** 15+ exec controls, ABO config, break-glass, budget
- **APIs:** `/exec/control/state`, `/exec/control/audit`, `/exec/control/break-glass`
- **User Type:** Executive+
- **Status:** ✅ Working

### 9.3 Business Office (`/business-office` — 1286 lines)
- **Purpose:** Revenue engine, deals, jobs, tools
- **APIs:** `/abo/overview`, `/abo/tools`, `/abo/deals`, `/abo/jobs`
- **User Type:** Admin+
- **Status:** ✅ Working

### 9.4 Executive Site Report (`/admin/exec-report` — 179 lines)
- **Purpose:** Site health report
- **APIs:** `/exec/site-report`
- **User Type:** Executive+
- **Status:** ✅ Working

### 9.5 Sage Audit (`/admin/sage-audit` — 409 lines)
- **Purpose:** AI persona audit
- **APIs:** `/admin/sage/audit`, `/admin/sage/cap`, `/admin/sage/metrics`
- **User Type:** Executive+
- **Status:** ✅ Working

### 9.6 Site Control Panel (`/admin/control` — 712 lines)
- **Purpose:** Feature flags, AI spend, broadcast
- **APIs:** `/admin/control-panel`, `/admin/ai-spend-budget`
- **User Type:** Executive+
- **Status:** ✅ Working

---

## FEATURE FAMILY 10: COMPLIANCE & SECURITY

### 10.1 Compliance List (`/compliance` — 38 lines)
- **Purpose:** Compliance modules
- **APIs:** `/compliance`
- **User Type:** All
- **Status:** ✅ Working

### 10.2 Compliance Detail (`/compliance/:slug` — 100 lines)
- **Purpose:** Individual compliance module
- **APIs:** None (pure frontend)
- **User Type:** All
- **Status:** ✅ Working

### 10.3 Auditor Dashboard (`/auditor` — 685 lines)
- **Purpose:** Debt, ledger, risks, summary
- **APIs:** `/auditor/debt`, `/auditor/ledger`, `/auditor/risks`, `/auditor/summary`
- **User Type:** Admin+
- **Status:** ✅ Working

### 10.4 Sentinel Research (`/s-research` — 682 lines)
- **Purpose:** Protocol research
- **APIs:** `/sentinel/protocols`, `/sentinel/research`, `/sentinel/ai-brief`
- **User Type:** Admin+
- **Status:** ✅ Working

### 10.5 Incidents (`/incidents` — 145 lines)
- **Purpose:** Incident reporting
- **APIs:** `/incidents`
- **User Type:** All authenticated
- **Status:** ✅ Working

### 10.6 Settings (`/settings` — 522 lines)
- **Purpose:** User settings, sessions, export, delete
- **APIs:** `/auth/me`, `/auth/sessions`, `/auth/account/export`, `/auth/account`
- **User Type:** All authenticated
- **Status:** ✅ Working

---

## FEATURE FAMILY 11: GAMES & ENGAGEMENT

### 11.1 Arcade Landing (`/arcade` — 226 lines)
- **Purpose:** Game listing
- **APIs:** `/arcade/leaderboard`, `/arcade/my-scores`
- **User Type:** Member+
- **Status:** ✅ Working

### 11.2 Arcade Game (`/arcade/:slug` — 103 lines)
- **Purpose:** Individual game
- **APIs:** `/arcade/scores`
- **User Type:** Member+
- **Status:** ✅ Working

### 11.3 Competition Arena (`/arena` — 748 lines)
- **Purpose:** Multi-persona competition
- **APIs:** `/competition/leaderboard`, `/competition/projects`, `/competition/score`
- **User Type:** Executive+
- **Status:** ✅ Working

### 11.4 Leaderboard (`/leaderboard` — 141 lines)
- **Purpose:** XP leaderboard
- **APIs:** `/xp/leaderboard`, `/xp/me`
- **User Type:** All
- **Status:** ✅ Working

### 11.5 My Position (`/my-position` — 545 lines)
- **Purpose:** User's standing + exit flow
- **APIs:** `/me/position`, `/me/request-exit`, `/me/step-down`
- **User Type:** Member+
- **Status:** ✅ Working

---

## FEATURE FAMILY 12: PROFILES & IDENTITY

### 12.1 Unified Profile (`/profile` — 1427 lines)
- **Purpose:** Profile + settings + AI + credentials + courses
- **APIs:** `/auth/me`, `/creator/profile`, `/certificates`, `/credentials`
- **User Type:** All authenticated
- **Status:** ✅ Working

### 12.2 User Profile (`/profile/:id` — 733 lines)
- **Purpose:** Admin user profile view
- **APIs:** `/auth/me`, `/partnership/status`, `/progress/me`
- **User Type:** Admin+
- **Status:** ✅ Working

### 12.3 Avatar Setup (`/avatar-setup` — 126 lines)
- **Purpose:** Avatar configuration
- **APIs:** `/auth/me`
- **User Type:** All authenticated
- **Status:** ✅ Working

---

## FEATURE FAMILY 13: LANDING & ONBOARDING

### 13.1 Landing (`/` — 474 lines)
- **Purpose:** Main MORE landing
- **APIs:** `/creator/courses/published`
- **User Type:** Public
- **Status:** ✅ Working

### 13.2 Landing Marketplace (`/landing` — 244 lines)
- **Purpose:** Marketplace landing
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

### 13.3 WAI Institute (`/wai-institute` — 164 lines)
- **Purpose:** WAI door
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

### 13.4 Plans (`/plans` — 89 lines)
- **Purpose:** Membership plans
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

### 13.5 Help Center (`/help-center` — 72 lines)
- **Purpose:** Help resources
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

### 13.6 Knowledge Base (`/knowledge-base` — 165 lines)
- **Purpose:** Handbooks
- **APIs:** `/handbooks/{name}`
- **User Type:** Public
- **Status:** ✅ Working

### 13.7 Terms of Service (`/terms` — 126 lines)
- **Purpose:** Legal terms
- **APIs:** `/users/accept-terms`
- **User Type:** Public
- **Status:** ✅ Working

### 13.8 Privacy Policy (`/privacy` — 45 lines)
- **Purpose:** Privacy policy
- **APIs:** None (static)
- **User Type:** Public
- **Status:** ✅ Working

---

## FEATURE FAMILY 14: AUTH

### 14.1 Login (`/login` — 190 lines)
- **Purpose:** Authentication
- **APIs:** `/auth/login`
- **User Type:** Public
- **Status:** ✅ Working

### 14.2 Register (`/register` — 269 lines)
- **Purpose:** Account creation
- **APIs:** `/auth/register`
- **User Type:** Public
- **Status:** ✅ Working

### 14.3 Forgot Password (`/forgot-password` — 186 lines)
- **Purpose:** Password reset request
- **APIs:** `/auth/forgot-password`
- **User Type:** Public
- **Status:** ✅ Working

### 14.4 Reset Password (`/reset-password` — 143 lines)
- **Purpose:** Password reset confirm
- **APIs:** `/auth/reset-password`
- **User Type:** Public
- **Status:** ✅ Working

### 14.5 Factory Reset (`/factory-reset` — 144 lines)
- **Purpose:** Emergency reset
- **APIs:** `/auth/factory-reset`
- **User Type:** Executive+
- **Status:** ✅ Working

### 14.6 Cross-Site Login (`/auth/cross-site` — 75 lines)
- **Purpose:** Cross-domain auth
- **APIs:** `/auth/cross-site-login`
- **User Type:** All
- **Status:** ✅ Working

---

## SUMMARY

| Family | Pages | Total Lines | Working | Needs Consolidation |
|--------|-------|-------------|---------|-------------------|
| AI & Assistants | 9 | 4,337 | 9 | Yes (7 → 1 console) |
| Publishing & Content | 7 | 3,752 | 7 | Yes (6 → 1 studio) |
| Music & Audio | 5 | 1,890 | 5 | Partial |
| Learning & Education | 13 | 2,342 | 13 | No |
| Community | 8 | 6,449 | 8 | Yes (7 → 1 hub) |
| Creator Economy | 7 | 2,166 | 7 | Yes (3 → 1 dashboard) |
| Monetization | 13 | 3,568 | 13 | Yes (6 → 1 billing) |
| Admin | 10 | 4,654 | 10 | No |
| Executive | 6 | 4,037 | 6 | No |
| Compliance & Security | 6 | 2,174 | 6 | Partial |
| Games & Engagement | 5 | 1,763 | 5 | No |
| Profiles & Identity | 3 | 2,286 | 3 | No |
| Landing & Onboarding | 8 | 1,385 | 8 | No |
| Auth | 6 | 1,007 | 6 | No |

**Total:** 126 pages, 44,267 lines, 126 working
**Consolidation candidates:** 32 pages → 8 unified pages
**After consolidation:** ~94 pages
