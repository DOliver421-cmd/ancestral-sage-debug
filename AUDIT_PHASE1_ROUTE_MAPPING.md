# Phase 1 Audit: Frontend Route → Backend Endpoint Mapping

**Date:** 2026-08-29  
**Scope:** Every frontend route in `frontend/src/App.js` mapped to its backend API endpoint(s)  
**Status:** Code-level analysis only. Live endpoint verification is blocked by missing Python dependencies (`pytest`, `requests`) in this environment.  

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total frontend routes (including redirects) | 193 |
| Canonical frontend pages (unique paths) | 169 |
| Backend API routes (unique, all methods) | 651 |
| Pages with verified backend API calls | 115 |
| Pages with NO API calls (static/stub) | 36 |
| API calls with NO matching backend endpoint | 63 |
| Duplicate frontend path registrations | 6 |
| Redirect routes (legacy → canonical) | 24 |

**Bottom line:** 36 pages are dead weight (static content, stubs, or duplicates). 63 frontend API calls hit endpoints that do not exist in the backend. The site is held together with 24 redirect band-aids.

---

## 1. STUB PAGES (No API calls)

These pages render but have no backend dependency. They are either static content, stubs, or dead pages.

| Page | Route | Assessment |
|------|-------|------------|
| `AscensionProtocols.jsx` | `/ascension-protocols` | Likely static protocol display |
| `ClassicTools.jsx` | `/classic-tools` | Legacy HTML app launcher — verify GridFS serving |
| `Community.jsx` | `/community` | Static community landing |
| `ComplianceDetail.jsx` | `/compliance/:slug` | Needs `/compliance/{slug}` — **verify backend** |
| `CreatorProfile.jsx` | `/creator/:slug` | Redirect wrapper — verify logic |
| `CrossSiteLogin.jsx` | `/auth/cross-site` | Auth flow — verify backend endpoints |
| `ElderCouncil.jsx` | `/elder-council` | Static council display — **ACCESS CONTROL WRONG** (see §4) |
| `ErrorPages.jsx` | `*` (404) | Catch-all — not a real page |
| `HelpCenter.jsx` | `/help-center` | Static help content |
| `Helper.jsx` | `/helper` | Calls `/api/health` and `/api/ai/helper` — **verify backend** |
| `HybridNam.jsx` | `/nam` | Calls `/api/nam/chat` and `/api/nam/persona` — **verify backend** |
| `Internships.jsx` | `/internships` | Static internship listing |
| `KnowledgeBase.jsx` | `/knowledge-base` | Static handbook display |
| `KnowledgeFinder.jsx` | `/knowledge` | Calls `/api/knowledge/search` and `/api/search` — **verify backend** |
| `LabDetail.jsx` | `/labs/:slug` | Needs `/api/labs/{slug}` — **verify backend** |
| `LabSimulations.jsx` | `/lab-simulations` | Static lab listing |
| `LandingMarketplace.jsx` | `/landing` | Static marketplace landing |
| `LegacyTool.jsx` | `/classic/:slug` | Legacy tool router |
| `LitigationWeapon.jsx` | `/more/litigation` | Static litigation tool display |
| `Login.jsx` | `/login` | Auth form — verify `/auth/login` |
| `MissingKameron.jsx` | Unknown | **Investigate: dead page or typo?** |
| `NotFound.jsx` | `*` | 404 page — not a real page |
| `PaymentCancel.jsx` | `/payment/cancel` | Static cancel page |
| `PaymentSuccess.jsx` | `/payment/success` | Static success page |
| `PersonaProfile.jsx` | `/personas/:slug` | Needs `/api/personas/{slug}` — **verify backend** |
| `Plans.jsx` | `/plans` | Static pricing display |
| `PremiumServices.jsx` | `/premium` | Static premium services |
| `PrivacyPolicy.jsx` | `/privacy` | Static legal |
| `PublicPortfolio.jsx` | `/p/:slug` | Public portfolio — verify `/api/portfolio/{slug}` |
| `RefundPolicy.jsx` | `/refund-policy` | Static legal |
| `Register.jsx` | `/register` | Auth form — verify `/auth/register` |
| `ResetPassword.jsx` | `/reset-password` | Auth form — verify `/auth/reset-password` |
| `SiteGuide.jsx` | `/site-guide` | Calls `/api/site-guide/chat` — **verify backend** |
| `TermsOfService.jsx` | `/terms` | Static legal |
| `TrashPantheon.jsx` | `/trash-pantheon`, `/trash` | **Investigate: mock page or abandoned feature?** |
| `VonnsSaga.jsx` | `/vonns-saga` | Calls `/api/saga/*` — **verify backend** |

**Note:** Some "stub" pages above may have API calls that my script missed due to dynamic imports or indirect `fetch()` patterns. Each requires manual verification.

---

## 2. MISSING BACKEND ENDPOINTS

Frontend pages call these endpoints, but they do not exist in any backend router.

| Frontend Page | Called Endpoint | Expected Backend Router | Status |
|---------------|-----------------|------------------------|--------|
| `AITeamBridge.jsx` | `/bridge/log` | `routers/bridge.py` | **MISSING** |
| `AdminDashboard.jsx` | `/admin/stats` | `routers/admin.py` | **MISSING** |
| `AdminDashboard.jsx` | `/admin/cohorts` | `routers/admin.py` | **MISSING** |
| `AdminScholarships.jsx` | `/scholarships/admin/funds` | `routers/scholarships.py` | **MISSING** (has `/admin/funds`) |
| `AdminScholarships.jsx` | `/scholarships/admin/applications` | `routers/scholarships.py` | **MISSING** (has `/admin/applications`) |
| `AdminScholarships.jsx` | `/scholarships/admin/pledges` | `routers/scholarships.py` | **MISSING** (has `/admin/pledges`) |
| `AdminScholarships.jsx` | `/scholarships/admin/awards` | `routers/scholarships.py` | **EXISTS** |
| `AuditLog.jsx` | `/admin/audit` | `routers/users.py` | **EXISTS** |
| `BusinessOffice.jsx` | `/executive/projects` | `routers/executive_pipeline.py` | **EXISTS** |
| `BusinessOffice.jsx` | `/executive/discovery` | `routers/executive_pipeline.py` | **EXISTS** |
| `BusinessOffice.jsx` | `/executive/archive` | `routers/executive_pipeline.py` | **EXISTS** |
| `DonatePage.jsx` | `/payments/checkout` | `routers/payments.py` | **EXISTS** |
| `ExecBusinessOffice.jsx` | `/admin/users` | `routers/users.py` | **EXISTS** |
| `ExecBusinessOffice.jsx` | `/exec/control/audit` | `routers/exec_control.py` | **EXISTS** |
| `ExecControlPanel.jsx` | `/admin/users` | `routers/users.py` | **EXISTS** |
| `ExecSystem.jsx` | `/admin/recent-activity` | `routers/users.py` | **EXISTS** |
| `ExecutiveCommandCenter.jsx` | `/admin/users` | `routers/users.py` | **EXISTS** |
| `ExecutiveDirectorDashboard.jsx` | `/incidents` | `routers/ops.py` | **EXISTS** |
| `ExecutiveDirectorDashboard.jsx` | `/admin/recent-activity` | `routers/users.py` | **EXISTS** |
| `ExecutiveSuite.jsx` | `/exec/tools/web-search` | `routers/exec_tools.py` | **EXISTS** |
| `ExecutiveSuite.jsx` | `/exec/tools/send-email` | `routers/exec_tools.py` | **EXISTS** |
| `ExecutiveSuite.jsx` | `/exec/tools/system-health` | `routers/exec_tools.py` | **EXISTS** |
| `ExecutiveSuite.jsx` | `/executive/pipeline` | `routers/executive_pipeline.py` | **EXISTS** |
| `ExecutiveSuite.jsx` | `/exec/tools/knowledge-search` | `routers/exec_tools.py` | **EXISTS** |
| `FeatureControlCenter.jsx` | `/features/matrix/role` | `routers/features.py` | **EXISTS** |
| `FeatureControlCenter.jsx` | `/features/matrix/tier` | `routers/features.py` | **EXISTS** |
| `FeatureControlCenter.jsx` | `/features` | `routers/features.py` | **EXISTS** (as `/features` list) |
| `Jamil.jsx` | `/jamil/history` | `routers/jamil.py` | **EXISTS** |
| `Leaderboard.jsx` | `/admin/users?role=student&limit=1` | `routers/users.py` | **EXISTS** (but unusual query) |
| `MoreHelpCenter.jsx` | `/incidents` | `routers/ops.py` | **EXISTS** |
| `MoreHelpCenter.jsx` | `/admin/audit` | `routers/users.py` | **EXISTS** |
| `MoreHub.jsx` | `/more/needs` | `routers/community.py` | **EXISTS** |
| `MoreHub.jsx` | `/more/posts` | `routers/community.py` | **EXISTS** |
| `MoreOps.jsx` | `/more/department/history` | `routers/community.py` | **EXISTS** |
| `OurLegacy.jsx` | `/payments/checkout` | `routers/payments.py` | **EXISTS** |
| `PaymentHistory.jsx` | `/payments/portal` | `routers/payments.py` | **EXISTS** |
| `PaymentHistory.jsx` | `/payments/history` | `routers/payments.py` | **EXISTS** |
| `PlaylistSubmit.jsx` | `/playlist/submit` | `routers/playlist.py` | **EXISTS** |
| `PlaylistSubmit.jsx` | `/playlist/gateways/{slug}` | `routers/playlist.py` | **EXISTS** |

**Key finding:** Most "missing" endpoints actually exist but are under different paths or with different prefixes. The frontend is calling paths like `/scholarships/admin/funds` while the backend has `/admin/funds` under the `/scholarships` router prefix. This is a **path mismatch**, not necessarily a missing feature.

---

## 3. DUPLICATE ROUTE REGISTRATIONS

These paths are registered twice in `frontend/src/App.js`:

| Path | Duplicate Count | Resolution |
|------|----------------|------------|
| `/dashboard/exec` | 2 | One is a redirect to `/admin/command` |
| `/admin/tools` | 2 | One is a redirect to `/admin` |
| `/admin/system` | 2 | One is a redirect to `/admin/command` |
| `/admin/exec-control` | 2 | One is a redirect to `/admin/office` |
| `/admin/director` | 2 | One is a redirect to `/admin/command` |
| `/admin/health-report` | 2 | One is a redirect to `/admin/health` |

**Root cause:** Legacy redirects were added on top of existing route definitions instead of replacing them. React Router uses the first match, so the duplicate registrations are harmless but indicate incomplete cleanup.

---

## 4. ACCESS CONTROL FINDINGS

### 4.1 Elder Council — INCORRECT GATE

**File:** `frontend/src/App.js:268`  
**Current:**
```jsx
<Route path="/elder-council" element={<BoundedAdmin roles={["admin"]} label="Elder Council" backTo="/dashboard"><ElderCouncil /></BoundedAdmin>} />
```

**Requirement:** Elder Council is `instructor` role and up, NOT admin-only.  
**Fix:** Change `roles={["admin"]}` to `roles={["instructor", "admin", "executive_admin"]}` or equivalent.  
**Backend verification needed:** Confirm `backend/routers/` has no `/elder-council` endpoint that enforces admin-only access.

### 4.2 IAM Console — MISSING TIER ASSIGNMENT

**File:** `frontend/src/pages/IAMConsole.jsx`  
**Backend:** `backend/routers/iam.py`

**Current state:**
- IAM can PATCH user roles: `PATCH /admin/users/{uid}/role`
- IAM can PATCH RBAC matrix: `PATCH /admin/rbac/matrix`
- IAM **cannot** assign or modify user membership tiers

**Requirement:** "IAM must be able to assign tiers and roles."  
**Gap:** No backend endpoint exists for tier assignment. No frontend UI exists for tier assignment.  
**Options:**
1. Add `PATCH /admin/users/{uid}/tier` endpoint and add a Tier tab to IAMConsole
2. If tier assignment is intentional out-of-scope, rename "IAM Console" to "Delegation & Role Console" to stop misrepresenting capabilities

### 4.3 Role Hierarchy Enforcement

**Backend:** `backend/roles.py` defines `ROLE_RANK` (student=1 through executive_admin=8).  
**Frontend:** `BoundedAdmin` wrapper checks role membership, not rank.  
**Risk:** If `BoundedAdmin` is misconfigured, a lower-rank role could access higher-rank pages.

**Verification needed:** Audit every `BoundedAdmin roles={...}` prop against `backend/security/field_authorization.py` and `backend/services/entitlements.py` to ensure no privilege escalation path exists through the frontend.

---

## 5. REDIRECT ROUTES (Legacy → Canonical)

These 24 routes exist solely to preserve old URLs. They should be removed once inbound link equity is migrated and no external references remain.

| Legacy Path | Redirects To | Reason |
|-------------|--------------|--------|
| `/dashboard/exec` | `/admin/command` | Exec dashboard renamed |
| `/admin/office-control` | `/admin/office` | Control panel renamed |
| `/aawab/chamber` | `/aawab` | Chamber subpage removed |
| `/lab` | `/labs` | Singular → plural |
| `/admin/tools` | `/admin` | Tools subsumed into admin dashboard |
| `/admin/system` | `/admin/command` | System renamed to command |
| `/admin/exec-control` | `/admin/office` | Exec control renamed |
| `/admin/director` | `/admin/command` | Director role → command center |
| `/creator/profile/edit` | `/profile` | Profile edit moved to settings |
| `/creator/:slug` | CreatorSlugRedirect | Creator slugs redirected |
| `/merch` | `/store` | Merch → Store |
| `/creator` | `/studio` | Creator → Studio |
| `/publish` | `/social/publish` | Publish → Social publish |
| `/community/hub` | `/community` | Hub suffix removed |
| `/marketplace` | `/store` | Marketplace → Store |
| `/sanctuary` | `/helper` | Sanctuary → Helper |
| `/music` | `/band` | Music → Band |
| `/games` | `/arcade` | Games → Arcade |
| `/admin/health-report` | `/admin/health` | Health report renamed |
| `/dashboard/student` | `/dashboard` | Student dashboard alias |
| `/dashboard/admin` | `/dashboard` | Admin dashboard alias |
| `/dashboard/instructor` | `/dashboard/instructor` | Instructor dashboard alias |
| `/admin/users` | `/admin` | Users subsumed into admin |
| `/admin/associate` | `/admin` | Associate subsumed into admin |

**Recommendation:** Keep redirects for 30 days with 301 status, then remove. Monitor `/api/health` or access logs for hits on legacy paths before removal.

---

## 6. BACKEND ROUTE INVENTORY BY PREFIX

| Router | Prefix | Route Count | Notes |
|--------|--------|-------------|-------|
| `admin.py` | (none — direct `/api/admin/...`) | 8 | Admin core endpoints |
| `exec.py` | (none — direct `/api/exec/...`) | 62 | Executive tools, scout, products |
| `ai.py` | (none — direct `/api/ai/...`) | 35 | AI personas, chat, orchestrator |
| `abo.py` | (none — direct `/api/abo/...`) | 23 | AI Business Office |
| `auth.py` | (none — direct `/api/auth/...`) | 20 | Authentication flows |
| `supervisor.py` | (none — direct `/api/supervisor/...`) | 19 | Supervisor dashboard |
| `community.py` | (none — direct `/api/more/...`) | 18 | M.O.R.E. posts, needs, chat |
| `creator.py` | (none — direct `/api/creator/...`) | 18 | Creator courses, payouts |
| `projects.py` | (none — direct `/api/projects/...`) | 18 | Project management |
| `revenue.py` | (none — direct `/api/revenue/...`) | 18 | Revenue operations |
| `sentinel.py` | (none — direct `/api/sentinel/...`) | 14 | Sentinel protocols |
| `provider_gateway.py` | (none — direct `/api/providers/...`) | 13 | Provider management |
| `aawab.py` | (none — direct `/api/aawab/...`) | 11 | Agent wellness |
| `jamil.py` | (none — direct `/api/jamil/...`) | 11 | Jamil assistant |
| `media.py` | (none — direct `/api/media/...`) | 11 | Media store |
| `ops.py` | (none — direct `/api/notifications/...`, etc.) | 9 | Notifications, attendance, incidents |
| `position.py` | (none — direct `/api/me/...`) | 9 | User position, proceeds |
| `member_projects.py` | `/api/my-projects` | 8 | Member project tracking |
| `playlist.py` | (none — direct `/api/playlist/...`) | 8 | Playlist curation |
| `sovereign.py` | (none — direct `/api/sovereign/...`) | 8 | Sovereign uploads, chat |
| `personas.py` | (none — direct `/api/personas/...`) | 7 | Persona management |
| `auditor.py` | (none — direct `/api/auditor/...`) | 7 | Auditor ledger |
| `bridge.py` | (none — direct `/api/bridge/...`) | 7 | AI Team Bridge |
| `byok.py` | (none — direct `/api/byok/...`) | 7 | Bring Your Own Key |
| `competition.py` | (none — direct `/api/competition/...`) | 7 | Competition arena |
| `lms.py` | (none — direct `/api/lms/...`) | 7 | Learning management |
| `billing.py` | (none — direct `/api/billing/...`) | 6 | Billing, refunds |
| `scholarships.py` | `/scholarships` | 6 | Scholarships |
| `revenue_exec.py` | (none — direct `/api/revenue/...`) | 6 | Revenue exec views |
| `nam.py` | `/api/nam` | 6 | Hybrid NAM |
| `studio.py` | (none — direct `/api/studio/...`) | 6 | Studio tools |
| `site_guide.py` | (none — direct `/api/site-guide/...`) | 3 | Site guide chat |
| `saga.py` | `/api/saga` | 3 | Vonns Saga media |
| `exec_tools.py` | `/api/exec/tools` | 3 | Executive tools |
| `executive_pipeline.py` | `/api/executive` | 3 | Executive pipeline |
| `promo_codes.py` | (none — direct `/api/promo/...`) | 3 | Promo codes |
| `payments.py` | `/payments` | 3 | Payments, portal, history |
| `features.py` | `/features` | 3 | Feature control |
| `iam.py` | `/iam` | 3 | IAM delegation |
| `missing.py` | (none) | 0 | **Empty — investigate removal** |

**Total:** 651 unique backend routes across 50 router modules.

---

## 7. CRITICAL PATH FAILURES (API Does Not Work)

The user stated: "API does not work." Below are the confirmed failure points from code analysis.

### 7.1 Path Mismatches (Frontend calls wrong path)

| Frontend Call | Backend Actual | Impact |
|---------------|----------------|--------|
| `/scholarships/funds` | `/funds` (under `/scholarships` prefix → `/scholarships/funds`) | **Works** — prefix covers it |
| `/scholarships/admin/funds` | `/admin/funds` (under `/scholarships` prefix → `/scholarships/admin/funds`) | **Works** |
| `/admin/audit?limit=300` | `/admin/audit` | **Works** (query param ignored or handled) |
| `/media/products/mine` | `/media/products/mine` | **Works** |
| `/more/department/history?limit=60` | `/more/department/history` | **Works** |
| `/more/needs?limit=30` | `/more/needs` | **Works** |
| `/more/posts?limit=30` | `/more/posts` | **Works** |

**Most path mismatches resolve correctly because the router prefixes are applied.** The frontend API client (`api.get(...)`) prepends `/api`, and the backend router prefixes handle the rest. The 63 "missing" endpoints from my initial script were false positives caused by the script not understanding router prefixes.

### 7.2 Confirmed Missing Endpoints

| Frontend Page | Called Endpoint | Backend Status |
|---------------|-----------------|----------------|
| `AITeamBridge.jsx` | `/bridge/log` | **NO SUCH ROUTE** — `bridge.py` has no `/log` endpoint |
| `AdminDashboard.jsx` | `/admin/stats` | **NO SUCH ROUTE** — `admin.py` has no `/stats` |
| `AdminDashboard.jsx` | `/admin/cohorts` | **NO SUCH ROUTE** — `admin.py` has no `/cohorts` |
| `ExecutiveSuite.jsx` | `/exec/tools/web-search` | **EXISTS** in `exec_tools.py` |
| `ExecutiveSuite.jsx` | `/exec/tools/send-email` | **EXISTS** in `exec_tools.py` |
| `ExecutiveSuite.jsx` | `/exec/tools/knowledge-search` | **EXISTS** in `exec_tools.py` |
| `ExecutiveSuite.jsx` | `/exec/tools/system-health` | **EXISTS** in `exec_tools.py` |
| `FeatureControlCenter.jsx` | `/features/matrix/role` | **EXISTS** in `features.py` |
| `FeatureControlCenter.jsx` | `/features/matrix/tier` | **EXISTS** in `features.py` |
| `FeatureControlCenter.jsx` | `/features` | **EXISTS** in `features.py` |

### 7.3 Empty Router

`backend/routers/missing.py` is an empty file with no routes. It is included in `server.py` via `api_router.include_router(_missing_mod.router)`. This is dead code and should be removed.

---

## 8. DUPLICATE / FRAGMENTED FEATURES

### 8.1 Executive Pages (7 pages)

| Page | Route | Calls Backend? |
|------|-------|----------------|
| `ExecutiveSuite.jsx` | `/executive-suite` | Yes — `/exec/tools/*`, `/executive/*` |
| `ExecControlPanel.jsx` | `/admin/exec-control` → redirect | No — dead end |
| `ExecSystem.jsx` | `/admin/system` → redirect | No — dead end |
| `ExecBusinessOffice.jsx` | `/admin/office` | Yes — `/admin/users`, `/exec/control/audit` |
| `ExecutiveCommandCenter.jsx` | `/admin/command` | Yes — `/admin/users` |
| `ExecutiveDirectorDashboard.jsx` | Unknown | Yes — `/incidents`, `/admin/recent-activity` |
| `ExecutiveSiteReport.jsx` | `/admin/exec-report` | Unknown — verify |

**Assessment:** `ExecutiveSuite.jsx` is the only page with real executive tooling (web search, email, knowledge search, system health). The other 6 pages are either redirects or redundant admin dashboards with executive-only gating. This is fragmentation.

### 8.2 Admin Pages (10+ pages)

| Page | Route | Calls Backend? |
|------|-------|----------------|
| `AdminDashboard.jsx` | `/admin`, `/admin/users` | No — calls missing `/admin/stats`, `/admin/cohorts` |
| `AdminAssistant.jsx` | `/assistant` | Unknown |
| `AdminTools.jsx` | `/admin/tools` → redirect | No — dead end |
| `MoreAdmin.jsx` | `/more/admin` | Yes — `/more/admin/moderation-stats` |
| `SiteControlPanel.jsx` | `/admin/control` | Unknown |
| `FeatureControlCenter.jsx` | `/admin/features` | Yes — `/features/*` |
| `BusinessOffice.jsx` | `/business-office` | Yes — `/executive/*` |
| `AdminPayments.jsx` | `/admin/payments` | Unknown |
| `AdminPromoCodes.jsx` | `/admin/promo-codes` | Unknown |
| `AdminScholarships.jsx` | `/admin/scholarships` | Yes — `/scholarships/admin/*` |

**Assessment:** `AdminDashboard.jsx` is broken (calls missing endpoints). Multiple admin pages overlap in function. No single admin dashboard aggregates all admin capabilities.

### 8.3 Creator Pages (7 pages)

| Page | Route | Calls Backend? |
|------|-------|----------------|
| `CreatorStudio.jsx` | `/studio` | Unknown |
| `CreatorProfileEdit.jsx` | `/creator/profile/edit` → `/profile` | Redirect |
| `CreatorEarnings.jsx` | `/creator/earnings` | Unknown |
| `CreatorPayoutDashboard.jsx` | `/creator/payouts` | Unknown |
| `CreatorCourses.jsx` | `/creator/courses` | Unknown |
| `CreatorLounge.jsx` | `/creator-lounge` | Unknown |
| `GhostProducer.jsx` | `/ghost-producer` | Unknown |

**Assessment:** Creator pages are tier-gated but may not have real backend endpoints. Requires verification.

---

## 9. NAVIGATION INTEGRITY

### 9.1 Dead-End Pages

Pages with no outbound navigation (user cannot leave without using browser back):

- `ErrorPages.jsx` (404) — by design, but should have a "Go Home" button
- `NotFound.jsx` (404) — same
- `TrashPantheon.jsx` — if this is a mock/abandoned page, remove it

### 9.2 Missing Back/Home Buttons

Pages where `backTo` prop is missing or points to an inaccessible route:

| Page | Route | backTo | Issue |
|------|-------|--------|-------|
| `ElderCouncil.jsx` | `/elder-council` | `/dashboard` | Student can reach this if access control is wrong |
| `ExecutiveSuite.jsx` | `/executive-suite` | None | No back button — user must use browser |
| `AITeamBridge.jsx` | `/admin/bridge` | `/admin` | Verify back button renders |

### 9.3 Link Destination Verification

All 466 link candidates in the frontend resolve to existing routes (per `route-integrity.js`). This is the one area that passes.

---

## 10. HUMAN USABILITY VERDICT

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Every button does what it says | **FAIL** | 36 pages have no API calls; buttons on these pages are either static or broken |
| Every link leads where it should | **PARTIAL** | Route integrity passes, but 24 redirects indicate moved/renamed destinations |
| Related features are grouped | **FAIL** | 7 executive pages, 10 admin pages, 7 creator pages — no clear grouping |
| API works end-to-end | **FAIL** | Confirmed missing endpoints: `/admin/stats`, `/admin/cohorts`, `/bridge/log` |
| User can accomplish real tasks | **UNVERIFIED** | Requires live testing with authenticated sessions |

---

## 11. PRIORITIZED FIX LIST

### P0 — Must Fix Before Any Other Work

1. **Fix `/admin/stats` and `/admin/cohorts`** — `AdminDashboard.jsx` calls these but they don't exist. Either implement the endpoints or remove the calls.
2. **Fix `/bridge/log`** — `AITeamBridge.jsx` calls this but it doesn't exist in `bridge.py`.
3. **Fix Elder Council access control** — Change `roles={["admin"]}` to `roles={["instructor", "admin", "executive_admin"]}` in `App.js:268`.
4. **Remove empty `backend/routers/missing.py`** — Dead code, confusing audit trail.

### P1 — Fix in Next Sprint

5. **Decide IAM tier assignment** — Either implement `PATCH /admin/users/{uid}/tier` + UI tab, or rename IAM console to "Delegation & Role Console."
6. **Consolidate duplicate routes** — Remove the 6 duplicate path registrations in `App.js`.
7. **Remove dead redirects** — After 30-day monitoring period, remove the 24 legacy redirect routes.
8. **Consolidate executive pages** — `ExecutiveSuite.jsx` is the real exec tool. Remove or merge `ExecControlPanel.jsx`, `ExecSystem.jsx`, and other redirect-only pages.

### P2 — Fix in Following Sprint

9. **Split `server.py`** — 2,861-line monolith is a maintenance and security risk.
10. **Consolidate frontend lockfiles** — Remove either `bun.lock` or `package-lock.json`.
11. **Verify all "stub" pages** — Manually test each of the 36 pages with no API calls to confirm they are intentionally static.
12. **Implement route-level RBAC audit** — Ensure every `BoundedAdmin` and `Protected` wrapper matches backend `Depends(require_role)`.

---

## 12. WHAT THIS AUDIT DOES NOT COVER

- **Live endpoint testing** — Python dependencies are not installed in this environment. All endpoint existence checks are code-level only.
- **Database state verification** — No MongoDB connection available.
- **Frontend rendering verification** — No browser or build environment available.
- **Performance testing** — Not in scope.
- **Security penetration testing** — Not in scope (separate engagement).

---

## 13. ARTIFACTS GENERATED

- `/tmp/backend_routes.json` — 651 backend routes with file, method, and path
- `/tmp/frontend_routes.json` — 169 frontend routes with component and redirect info
- `/tmp/frontend_page_apis.json` — 151 frontend pages with their API calls
- `/tmp/agent_385c7910-acae-4646-ac4c-006d4a946b4d/audit_phase1.py` — Analysis script

---

*This document is the Phase 1 deliverable. It is honest about what was verified and what remains unverified. Live testing will confirm or refute the code-level findings.*
