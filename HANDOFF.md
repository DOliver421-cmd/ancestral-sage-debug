# WAI Institute — Agent Handoff Document
**Date:** June 1 2026  
**Repo:** DOliver421-cmd/ancestral-sage-debug  
**Deploy:** Railway — two services (frontend nginx + backend uvicorn)  
**Domains:** wai-institute.org (main) · morehelp.center (M.O.R.E. subdomain)  
**Last merged PR:** #23  

---

## YOUR FIRST ACTION: NO-MERCY SYSTEM AUDIT

Before touching anything, run this sequence. Do not skip steps.

```bash
# 1. Confirm you are on main and it's current
git fetch origin main && git log --oneline origin/main | head -5

# 2. Check for any open PRs or uncommitted work
git status && git branch -r | grep claude

# 3. Verify backend syntax is clean
cd backend && python -m py_compile server.py && echo "OK" || echo "SYNTAX ERROR"

# 4. Count endpoints — should be ~170+
grep -c "^@api_router\." server.py

# 5. Check all creator economy collections exist in server code
grep -c "db\.creator_" server.py

# 6. Confirm SubscribePage has Sanctuary tiers
grep "sanctuary_trial\|sanctuary_paid" frontend/src/pages/SubscribePage.jsx

# 7. Confirm morehelp.center Routes fix is on main
grep -n "path.*login" frontend/src/App.js | head -5

# 8. Confirm SiteControlPanel route exists
grep "admin/control" frontend/src/App.js
```

**If any of these fail, stop and diagnose before doing any new work.**

---

## PERMANENT MANDATES — NEVER VIOLATE

1. **Sequential commits** — one unit of work per PR, wait for merge before starting next
2. **No accumulation** — never let more than one PR sit open without user merge approval
3. **Never remove ANY site control/feature** without explicit user instruction to remove that specific feature
4. **No cosmetic mocks** — every metric, control, and display must be real and functional
5. **All controls must function as intended** — no dead buttons, no fake toggles
6. **API keys** — encrypted at rest via Fernet (`PROVIDER_KEY_ENCRYPTION_SECRET`), `encrypted_key` field NEVER returned in API responses
7. **Cash refunds** require ALL 5 conditions: `is_extreme_violation`, `user_not_at_fault`, `is_legal`, `no_harm_to_wai`, `supervisor_approved`
8. **Never call Anthropic/LLMs directly** — always use `call_llm()` from `backend/ai/llm_gateway.py`
9. **Never scam/exploit/misrepresent/fake compliance**
10. **Development branch for this session:** `claude/dreamy-volta-F3tzj` (or create a new `claude/` branch from main for each PR)

---

## ARCHITECTURE

### Infrastructure
- **Frontend:** React 18 SPA, React Router v6, Tailwind CSS, built by Vite, served by nginx
- **Backend:** FastAPI + Motor (async MongoDB), 12,362 lines in `backend/server.py`
- **DB:** MongoDB via Motor — all collections listed below
- **Auth:** JWT Bearer tokens, role-based (`student` < `instructor` < `admin` < `executive_admin`)
- **Email:** Resend (primary) + Gmail SMTP (fallback)
- **Payments:** Stripe — checkout sessions, webhooks, customer portal, subscriptions
- **AI:** `backend/ai/llm_gateway.py` → `call_llm()` — routes to providers by tier; Anthropic is last-resort paid tier

### Key Environment Variables
```
STRIPE_SECRET_KEY          sk_live_... or sk_test_...
STRIPE_WEBHOOK_SECRET      whsec_...
STRIPE_PUBLISHABLE_KEY     pk_...
PROVIDER_KEY_ENCRYPTION_SECRET   (Fernet key for AI provider keys)
CORS_ORIGINS               https://www.wai-institute.org,...
FRONTEND_URL               https://www.wai-institute.org
MONGO_URI / DATABASE_URL   MongoDB connection string
RESEND_API_KEY             email
GMAIL_USER / GMAIL_APP_PASSWORD   email fallback
```

### Domain Routing (App.js)
```javascript
// morehelp.center → MoreHelpCenter.jsx (with /login and /register routed to real pages)
if (hostname.includes("morehelp.center")) {
  return <Routes>
    <Route path="/login"    element={<Login />} />
    <Route path="/register" element={<Register />} />
    <Route path="*"         element={<MoreHelpCenter />} />
  </Routes>
}
// wai-institute.org → full SPA with all routes
```

---

## COMPLETE FILE MAP

### Backend
- `backend/server.py` — 12,362 lines, ALL routes, models, business logic
- `backend/ai/llm_gateway.py` — ONLY way to call LLMs
- `backend/seed.py` — MODULES data (electrical trades curriculum)
- `backend/seed_labs.py` — ONLINE_LABS, IN_PERSON_LABS, COMPETENCIES
- `backend/seed_credentials.py` — CREDENTIALS
- `backend/seed_compliance.py` — COMPLIANCE_MODULES, COMPLIANCE_QUIZZES
- `backend/seed_inventory.py` — SITES, INVENTORY
- `backend/security/field_authorization.py` — field-level auth (avatar_url in visible fields)
- `backend/social_routes.py` — social publisher routes (included via `api_router.include_router`)

### Frontend Pages (95 total)
```
/                    Landing.jsx (home)
/login               Login.jsx
/register            Register.jsx
/dashboard           StudentDashboard.jsx
/admin               AdminDashboard.jsx
/admin/control       SiteControlPanel.jsx  ← NEW (exec only)
/admin/system        ExecSystem.jsx
/admin/director      ExecutiveDirectorDashboard.jsx
/admin/sage-audit    SageAudit.jsx
/admin/staff-meetings StaffMeetingHistory.jsx
/admin/health        SystemHealth.jsx
/admin/moderation    ModerationAnalytics.jsx
/admin/providers     ProviderGateway.jsx
/admin/payments      AdminPayments.jsx
/admin/prices        PlatformPrices.jsx
/admin/users         AdminDashboard.jsx
/admin/tools         AdminTools.jsx
/admin/analytics     Analytics.jsx
/admin/audit         AuditLog.jsx
/instructor          InstructorDashboard.jsx
/instructor/labs     InstructorLabs.jsx
/creator/courses     CreatorCourses.jsx    ← NEW
/creator/earnings    CreatorEarnings.jsx   ← NEW
/creator/profile/edit CreatorProfileEdit.jsx ← NEW
/creator/:slug       CreatorProfile.jsx    (fetches DB first, falls back to hardcoded)
/plans               Plans.jsx             (5-tier, all wired to Stripe)
/subscribe           SubscribePage.jsx     (handles ?plan= param for all tiers)
/more-help-center    MoreHelpCenter.jsx
/app/more            MoreHub.jsx
/more/admin          MoreAdmin.jsx
/more/ops            MoreOps.jsx
/more/chat           MoreChat.jsx
/more/litigation     LitigationWeapon.jsx
/ghost-producer      GhostProducer.jsx
/helper              Helper.jsx (public AI assistant — calls /api/ai/helper)
/revenue             RevenueDivision.jsx
/auditor             AuditorDashboard.jsx
/supervisor          SeshatsHub.jsx (supervisor-protected)
```

### Static HTML Tool Pages (`frontend/public/tools/`)
```
hub_client.js              Shared client for all tool pages
djedi-oracle.html          Sage Oracle / DJEDI Oracle (4 skills)
electrical-courses.html    Technical Skills Hub (4 skills)
media-strategist.html      Media Empire Builder (4 skills)
publisher-prime.html       Book & Content Publishing Empire (4 skills)
creators-sanctuary.html    Full hub SPA — tier system, Sage modal, admin console
litigation-weapon.html     Legal tool
```
All tool pages have WAI nav bar injected at top. Tier buttons on creators-sanctuary.html redirect to `/subscribe?plan=sanctuary_*`.

---

## MONGODB COLLECTIONS (all active)

### Core
- `users` — id, email, full_name, role, is_active, avatar_url, stripe_customer_id, more_member
- `audit_log` — every privileged action (actor_id, action, at, meta)
- `notifications` — per-user alerts
- `platform_flags` — feature switches (platform_locked, marketplace_disabled, ai_disabled, community_disabled, labs_disabled)
- `platform_config` — key/value config (provider ranking, MFA config, greeter config, etc.)
- `broadcasts` — site-wide banner messages

### Payments & Subscriptions
- `payments` — every completed Stripe transaction (user_id, product_key, amount_cents, status, created_at)
- `subscriptions` — Stripe subscription records (stripe_subscription_id, status, current_period_end)
- `wai_refunds` — refund requests (status: pending/approved/denied)
- `escalations` — escalated issues

### Creator Economy (ALL NEW)
- `creator_courses` — course_id, creator_id, title, description, price_cents, sections[], status (draft/published/archived), enrollment_count
- `creator_earnings` — per-sale ledger (creator_id, course_id, gross_cents, creator_share_cents [70%], platform_share_cents [30%], period YYYY-MM, payout_status)
- `creator_payouts` — disbursement records (payout_id, creator_id, amount_cents, status)
- `creator_bank_accounts` — routing_number, account_number_masked, account_type
- `creator_profiles` — slug, display_name, bio, socials[], more_offerings[], commerce[]
- `creator_enrollments` — free course enrollments

### Learning
- `modules` — seeded electrical trades curriculum
- `progress` — user progress per module
- `labs` / `lab_submissions` — workforce lab submissions
- `compliance_modules` / `compliance_progress` — compliance tracking
- `certificates` — issued certificates
- `user_credentials` — Open Badges credentials
- `user_xp` — gamification XP

### M.O.R.E. Community
- `more_posts` — community posts
- `more_needs` — resource needs
- `more_flags` — flagged content (status: pending)
- `more_chats` — AI chat sessions
- `more_appeals` — appeal requests
- `more_moderation_log` — moderation actions

### AI / System
- `ai_usage_log` — every LLM call (provider, model, cost_usd, created_at)
- `ai_providers` / `ai_provider_keys` — provider gateway config
- `sage_sessions` / `sage_conduct_sessions` — Sage AI sessions
- `governance_log` — staff meeting decisions
- `staff_meetings` — meeting records

---

## STRIPE PAYMENT PRODUCTS

All defined in `PAYMENT_PRODUCTS` dict (~line 7422 in server.py):

```python
# Physical goods
"tshirt"           $25.00  one-time
"workbook"         $15.00  one-time  
"kit"              $45.00  one-time  (t-shirt + workbook)
"credential"       $25.00  one-time

# M.O.R.E. membership
"more_monthly"     $9.99/mo subscription
"more_annual"      $79.99/yr subscription

# WAI Institute tiers (Plans.jsx → /subscribe?plan=xxx)
"member_monthly"   $9/mo   subscription
"plus_monthly"     $15/mo  subscription
"pro_monthly"      $29/mo  subscription
"patron_monthly"   $59/mo  subscription

# Creators Sanctuary (creators-sanctuary.html → /subscribe?plan=xxx)
"sanctuary_trial"  $3.00   one-time  (3-day trial)
"sanctuary_paid"   $7/mo   subscription
"sanctuary_creator" $11/mo subscription
"sanctuary_mod"    $15/mo  subscription

# Other
"donation"         variable one-time
"creator_course"   dynamic  one-time  (set per course, metadata carries creator_id + course_id)
```

### Webhook Flow
`POST /payments/webhook` → `_stripe_checkout_done()`:
- Writes to `db.payments`
- If `product_key == "creator_course"`: writes to `db.creator_earnings` (70% creator, 30% WAI), increments `enrollment_count`
- Notifies creator of each sale

---

## ROLE SYSTEM

```
student          Default. Access to curriculum, labs, M.O.R.E., store, creator tools
instructor       + roster, lab approvals, attendance  
admin            + all admin routes, analytics, audit, moderation
executive_admin  + system controls, provider gateway, staff meetings, control panel
```

**Supervisor** is a separate auth entirely (`/supervisor-login`) — not a role, gated by `SupervisorProtected`.

---

## CREATOR ECONOMY — HOW IT WORKS

1. **Creator publishes a course** via `POST /creator/courses` (any authenticated user)
2. **Student buys it** via `POST /creator/courses/{id}/checkout` → Stripe session created with `product_key: "creator_course"`, `creator_id`, `course_id` in metadata
3. **Webhook fires** `checkout.session.completed` → `_stripe_checkout_done()` → writes to `db.creator_earnings` with 70/30 split
4. **Creator views earnings** at `/creator/earnings` → `GET /creator/earnings` aggregates by period
5. **Payout processing** → `POST /admin/creator-payouts/process` (executive_admin) marks prior-period earnings paid, writes payout records, notifies creators
6. **Bank account** stored via `POST /creator/bank-account` (account number masked after save)

**The landing page promise: "You keep 70%. Monthly. On the 1st." — this is now real.**

---

## SITE CONTROL PANEL

**Route:** `/admin/control` — executive_admin only  
**Not linked from:** M.O.R.E., public nav, any non-exec sidebar  
**Backend:** `GET /admin/control-panel` pulls live data from every collection + Stripe API  

**9 tabs:**
1. Overview — key metrics + failure log + audit trail
2. Revenue — today/month/alltime, Stripe balance, product breakdown
3. Platform Flags — 5 real feature switches with dangerous-action confirmation modal
4. Creator Economy — course/profile counts, pending payouts
5. Learning — completions, labs pending, credentials, incidents
6. AI Spend — real cost_usd from ai_usage_log, by provider
7. Community — M.O.R.E. health metrics
8. Governance — audit event count, pending refunds/escalations
9. Broadcast — push site-wide info/warning/critical banners

---

## COMPLETED WORK (this session)

| PR | What | Merged |
|----|------|--------|
| #14 | Ghost Producer × Publisher Prime React page at /ghost-producer | ✅ |
| #15 | 5 static HTML tool pages + hub_client.js | ✅ |
| #16 | Remove placeholder commerce items, avatar sync to backend, Helper AI label | ✅ |
| #17 | 5-tier Stripe wiring (member/plus/pro/patron plans) | ✅ |
| #18 | Creator course publishing — full CRUD backend + CreatorCourses.jsx | ✅ |
| #19 | Creator earnings backend + CreatorEarnings.jsx (70/30, bank account, payouts) | ✅ |
| #20 | Creator profile self-edit — backend + CreatorProfileEdit.jsx | ✅ |
| #21 | Creators Sanctuary tiers → real Stripe checkout | ✅ |
| #22 | Site Control Panel — real metrics, real governance | ✅ |
| #23 | Fix morehelp.center/login routes + AbortSignal.timeout error | ✅ |

---

## REMAINING WORK (priority order)

### Medium Priority — Known Gaps
| # | What | Detail |
|---|------|--------|
| M3 | "Creators Like You" section on Landing.jsx is hardcoded | 4 static cards with fake student counts. Should query `db.creator_profiles` + `db.creator_courses` to show real published creators |
| H1b | Creator profile fetch uses `user_id` for owner check but `user_id` not returned in public profile GET | `GET /creator/profile/{slug}` strips `user_id` — but `CreatorProfile.jsx` checks `dbProfile.user_id === user.id` which will never match. Fix: return `is_owner: bool` from the endpoint instead |

### Known Issues to Investigate
- `favicon.ico` and `logo-192.png` both return `text/html` (200) — nginx is serving the SPA for these instead of actual image files. Check `frontend/public/` for these assets.
- The "Creators Like You" landing section has image paths `/images/creators/creator-1-poet.jpg` etc. — these files likely don't exist, falling back to inline SVG placeholder. Not broken but not real.

---

## WHAT GOOD LOOKS LIKE FOR THE NEXT SESSION

Run the no-mercy audit above. Then look at:

1. **H1b fix** (5 min) — `GET /creator/profile/{slug}` should return `is_owner: true/false` based on JWT if present, instead of stripping `user_id`. This makes the "Edit Profile" button work correctly.

2. **M3** — Wire "Creators Like You" section on Landing.jsx to real DB data: `GET /creator/courses/published` already exists, query it and show top creators.

3. **favicon/logo** — Check `frontend/public/` for `favicon.ico` and `logo-192.png`. If missing, nginx returns the index.html. Add real files or fix nginx config.

4. **Creator course enrollment** — `db.creator_enrollments` is written for free courses but there's no endpoint to check if a user is enrolled. Add `GET /creator/enrollments/me` and use it in CreatorCourses.jsx to show "Enrolled" vs "Buy" on published courses.

5. **Admin payout trigger UI** — The `POST /admin/creator-payouts/process` endpoint exists but there's no UI button for it. Add a "Process Payouts" button to the Creator Economy tab in SiteControlPanel.jsx.

---

## HARDCODED CREATOR PROFILES (fallback data)

`CreatorProfile.jsx` has 3 hardcoded entries in `CREATORS` object:
- `nam-oshun` — Delon Oliver, poet/community organizer, founding member
- `royal-black-falcon` — Kamau Baruti, poet/cultural warrior
- `nova-highborn` — Ebony Oliver, visual artist/mentor

These render when no DB record exists for that slug. Any user can claim their own slug via `PUT /creator/profile` and the DB version takes precedence.

---

## LLM GATEWAY RULE

**NEVER** import anthropic/openai/etc directly in server.py.  
**ALWAYS** use:
```python
from ai.llm_gateway import call_llm
result = await call_llm(messages=[...], system="...", model="...", user_id="...")
```

---

## GIT WORKFLOW

```bash
# Start each new feature:
git checkout -b claude/feature-name origin/main

# Commit:
git commit -m "Description\n\nhttps://claude.ai/code/session_01RhtoStypiC6WZN5VojusBS"

# Push and open PR — then WAIT for user to merge before starting next feature
git push -u origin claude/feature-name
```

Use `mcp__github__create_pull_request` tool to open PRs.  
Use `mcp__github__pull_request_read` to check if merged before continuing.

**One PR at a time. Always.**
