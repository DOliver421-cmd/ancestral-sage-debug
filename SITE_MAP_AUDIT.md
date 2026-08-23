# SITE MAP AUDIT — MoreHelp Center

**Date:** August 22, 2026
**Method:** Automated scan of App.js routes, AppShell.jsx nav, page components, and backend routers.

---

## SUMMARY

| Category | Count |
|----------|-------|
| Total routes in App.js | 148 |
| Unique page components | 120 |
| Backend routers | 46 |
| Nav sections | 13 |
| Nav items (links) | 74 |
| Duplicate routes | 7 |
| Routes with role protection | 43 |
| Routes with TierGate | 9 |
| AI-powered backend routers | 20 |

---

## DUPLICATE ROUTES (same path, defined twice)

| Route | First Definition | Second Definition | Action Needed |
|-------|-----------------|-------------------|---------------|
| `/admin/director` | Line 290 (Redirect → /admin/command) | — | Keep redirect |
| `/admin/exec-control` | Line 289 (Redirect → /admin/office) | — | Keep redirect |
| `/admin/health-report` | Line 341 (BoundedAdmin) | Line 342 redirect | CONFLICT |
| `/admin/system` | Line 291 (Redirect → /admin/command) | Line 342 redirect | CONFLICT |
| `/admin/tools` | Line 290 (Redirect → /admin) | Line 323 redirect | CONFLICT |
| `/dashboard/exec` | Line 252 (Redirect → /admin/command) | Line 361 redirect | CONFLICT |
| `/store` | Line 352 (MediaStore) | Line 418 (MediaStore with Protected) | CONFLICT |

---

## NAV SECTIONS AND ITEMS

### Home (everyone)
- Home / Landing (`/`)
- Dashboard (`/dashboard`)
- My Profile (`/profile`)
- Settings (`/settings`)

### NAM (student+)
**AI Assistants:**
- AI Tutor (`/ai`)
- Personal Helper (`/helper`)
- Admin Assistant (`/assistant`)
- Orchestrator (`/orchestrator`)
- Site Guide (`/site-guide`)

**Leadership:**
- Council (Sage) (`/council`)
- Jamil (`/jamil`)
- My AI (BYOK) (`/byok`)

### Create (student+)
- Creator Studio (`/studio`)
- Course Manager (`/creator/courses`)
- Ghost Producer (`/ghost-producer`)
- Social Blast (`/social/publish`)
- Creator Lounge (`/creator-lounge`)
- My Earnings (`/creator/earnings`)
- Payout Dashboard (`/creator/payouts`)

### Learn (student+)
**Curriculum:**
- Modules (`/modules`)
- Learning Path (`/adaptive`)
- Competencies (`/competencies`)

**Labs & Practice:**
- Workforce Labs (`/labs`)
- Lab Simulations (`/lab-simulations`)

**Compliance:**
- Compliance (`/compliance`)

**Credentials:**
- Credentials (`/credentials`)
- Certificates (`/certificates`)
- Portfolio (`/portfolio`)

### Community (student+)
- Members' Palace (`/palace`)
- XP Leaderboard (`/leaderboard`)
- Community Chat (`/more/chat`)
- Legal Tools (`/more/litigation`)
- Report Incident (`/incidents`)
- Vonns Saga (`/vonns-saga`)
- Ascension Protocols (`/ascension-protocols`)

### Marketplace (student+)
- Media Store (`/store`)
- Plans & Pricing (`/plans`)
- Membership (`/subscribe`)
- Donate (`/donate`)
- Payment History (`/payment/history`)
- Partnerships (`/partnership`)

### Sanctuary (student+)
- Sanctuary (`/sanctuary`)
- Knowledge Base (`/knowledge-base`)

### Music (student+)
- Band on a Page (`/band`)
- Playlist Manager (`/playlist/dashboard`)

### Games (student+)
- Virtual Arcade (`/arcade`)
- M.O.R.E. Pantheon (`/trash`)

### Agent Wellness (oversight+)
- Agent Registry (`/aawab`)
- Certification (`/aawab/chamber`)

### Director (admin+)
**Overview:** Admin Overview, IAM Console, Business Office, Command Center, System Health
**Finance:** Payments, Billing, Prices, Revenue
**Operations:** Analytics, Audit Log, Moderation, Sage Audit
**Tools:** The Arena, Sites & Inventory, AI Team Bridge, Provider Gateway, Site Report

### Instructor (instructor+)
- My Roster (`/instructor`)
- Lab Approvals (`/instructor/labs`)
- Attendance (`/attendance`)

### Site Support (support_staff+)
- Audit Log (`/admin/audit`)
- Moderation (`/admin/moderation`)

---

## ROUTES WITH ROLE PROTECTION (BoundedAdmin or Protected with roles)

| Route | Required Role(s) | Component |
|-------|-----------------|-----------|
| `/arena` | executive_admin | CompetitionArena |
| `/admin/command` | executive_admin | ExecutiveCommandCenter |
| `/admin/control` | executive_admin | SiteControlPanel |
| `/admin/office` | executive_admin | ExecBusinessOffice |
| `/admin/sage-audit` | executive_admin | SageAudit |
| `/admin/staff-meetings` | executive_admin | StaffMeetingHistory |
| `/admin/exec-report` | executive_admin | ExecutiveSiteReport |
| `/admin/providers` | executive_admin | ProviderGateway |
| `/team/ops` | executive_admin | TeamOps |
| `/admin` | admin | AdminDashboard |
| `/admin/iam` | admin | IAMConsole |
| `/admin/accounts` | admin | AccountControls |
| `/admin/analytics` | admin | Analytics |
| `/admin/health` | admin | SystemHealth |
| `/admin/health-report` | admin, executive_admin | SystemHealth |
| `/admin/payments` | admin | AdminPayments |
| `/admin/billing` | admin | BillingAdmin |
| `/admin/prices` | admin | PlatformPrices |
| `/admin/bridge` | admin | AITeamBridge |
| `/elder-council` | admin | ElderCouncil |
| `/business-office` | admin | BusinessOffice |
| `/aawab` | admin | AgentRegistryView |
| `/aawab/chamber` | admin | CertificationChamber |
| `/auditor` | admin | AuditorDashboard |
| `/revenue` | admin, executive_admin | RevenueDivision |
| `/jamil` | admin | Jamil |
| `/projects` | admin | ProjectDashboard |
| `/admin/audit` | support_staff, admin | AuditLog |
| `/admin/moderation` | support_staff, admin | ModerationAnalytics |
| `/instructor` | instructor, admin | InstructorDashboard |
| `/instructor/labs` | instructor, admin | InstructorLabs |
| `/attendance` | instructor, admin | Attendance |
| `/creative-partner` | instructor, executive_admin | CreativePartnerHub |
| `/more/admin` | admin | MoreAdmin |
| `/more/ops` | admin | MoreOps |

---

## ROUTES WITH TIER GATE (membership tier required)

| Route | Feature Key | Component |
|-------|------------|-----------|
| `/adaptive` | tracks | Adaptive |
| `/creator/courses` | courses | CreatorCourses |
| `/creator/earnings` | earnings | CreatorEarnings |
| `/ghost-producer` | ghost | GhostProducer |
| `/creator-lounge` | lounge | CreatorLounge |
| `/band` | band | BandOnPage |
| `/social/publish` | publisher_ai | SocialPublish |
| `/studio` | studio | CreatorStudio |
| `/creator/payouts` | payouts | CreatorPayoutDashboard |

---

## AI-POWERED BACKEND ROUTERS (use call_llm / llm_gateway)

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `ai.py` | 46 | AI Tutor, chat, personas |
| `nam.py` | 32 | NAM engines, knowledge, memory, dreams |
| `jamil.py` | 7 | Jamil persona |
| `competition.py` | 7 | Arena competition |
| `sovereign.py` | 12 | Revenue Director persona |
| `sentinel.py` | 14 | Confidentiality Sentinel |
| `site_guide.py` | 3 | Site Guide persona |
| `chat.py` | 6 | Community chat AI |
| `bridge.py` | 7 | AI Team Bridge |
| `exec_command.py` | 2 | Executive Command Center |
| `studio.py` | 15 | Creator Studio AI features |
| `lms.py` | 26 | Learning Management AI |
| `community.py` | 20 | Community features |
| `billing.py` | 19 | Billing AI |
| `abo.py` | 19 | AI Business Office |
| `ops.py` | 12 | Operations AI |
| `revenue.py` | 15 | Revenue AI |
| `supervisor.py` | 19 | Supervisor AI |
| `byok.py` | 7 | BYOK key management |

---

## DEAD/ORPHANED COMPONENTS

Components in `frontend/src/pages/` that don't appear in App.js routes:

- `AdminTools` — appears unused
- `CreatorProfile` — replaced by UnifiedProfile
- `CreatorProfileEdit` — comment says "retired"
- `ExecControl` — not in routes
- `ExecControlPanel` — not in routes
- `ExecSystem` — not in routes
- `ExecutiveDirectorDashboard` — not in routes
- `MissingKameron` — not in routes
- `NotFound` — likely Error404 replacement
- `SiteHealthReport` — not in routes

---

## PHASE 17 UPDATE (2026-08-23) — ROUTE/API vs REGISTRY CROSS-CHECK

- All 48 features in `FEATURE_REGISTRY` were cross-checked against the live route
  table; 4 stale `api_endpoints` were corrected (see PHASE_17_VERIFICATION.md).
- New findings:
  - `/orchestrator` route does NOT exist — dead nav link removed; OrchestratorChat
    component is the Council/Sage page at `/council` (canonical home).
  - `/sanctuary` redirects to `/helper` — Sanctuary has no canonical page/API.
  - `/trash` is the route for `games.pantheon` (M.O.R.E. Pantheon) — suspicious
    legacy label, rename pending.
  - `/api/adaptive/me` (Learning Path) has no feature gate — auth-only, rule-based.
- Full route→feature→access mapping: FEATURE_ACCESS_MATRIX.md.
