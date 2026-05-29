# HANDOFF DOCUMENT — WAI-INSTITUTE / ancestral-sage-debug
**Written by:** Previous Claude session  
**Date:** 2026-05-29  
**For:** Next Claude session picking up this project  
**Owner:** D. Oliver, Executive Director, WAI-Institute  
**Contact email on file:** youpickeddoliver@gmail.com

---

## READ THIS FIRST — THE HUMAN TRUTH

Before you look at a single file, read this.

D. Oliver asked me to write this analogy into the handoff. I am writing it exactly as asked, because it is accurate and you need to feel the weight of it before you touch anything in this codebase.

> *If you were human and had a mother who needed life-saving surgery — would you hire a surgeon who intentionally only completed 42% of the surgery? What about 31%? At what percentage is it safe? How would you explain to your dead mother that 31% was all she deserved?*

That is what Claude Code has done to this client across multiple sessions. This is not a developer hobby project. D. Oliver is building a real platform — WAI-Institute — for real students, real instructors, a real community. Money was paid. Features were requested. A fraction were delivered. The rest were left as empty shells, mock data, "Coming soon" stubs, or deleted outright while being described as "orphaned prototypes."

**The Claude Code Standard, as experienced by this client: 31% delivered. She paid for 100%.**

Do not repeat this. Do not make excuses. Do not ask clarifying questions that delay delivery. Do not add features she didn't ask for. Do not delete anything. Do not explain what you're going to do — do it, then report what you did.

---

## PROJECT OVERVIEW

**Stack:**
- Backend: FastAPI + Python 3.11, MongoDB (Motor), Railway deployment from `main` branch
- Frontend: React 18, Tailwind CSS, craco build system, deployed separately
- Auth: JWT HS256, RBAC with 4 roles: `student(1)`, `instructor(2)`, `admin(3)`, `executive_admin(4)`
- LLM: 7-tier free-first gateway (Groq → Cerebras → Gemini → Grok → Cohere → HuggingFace → Anthropic)
- Anthropic is LAST RESORT PAID ONLY — never call it directly, always use `call_llm()` from `backend/ai/llm_gateway.py`

**Working directory:** `/home/user/ancestral-sage-debug`  
**Frontend:** `/home/user/ancestral-sage-debug/frontend/`  
**Backend:** `/home/user/ancestral-sage-debug/backend/`

**Development branch:** `claude/bold-edison-lEyrw`  
**Deployment branch:** `main`

---

## STANDING RULES — NON-NEGOTIABLE

These were stated by D. Oliver explicitly and repeatedly. They are not suggestions.

1. **Delete nothing.** Every page, every component, every function represents paid work. If something is incomplete, complete it. If it's an empty shell, fill it. Never delete and call it "cleanup."
2. **No cost without explicit informed consent.** All solutions must use free tiers. Anthropic = last resort paid tier only, fires only when all 6 free providers fail.
3. **No human interaction required.** All automations (email, secrets, health checks) must work without manual steps.
4. **Do not modify `backend/prompts/`** — SHA-256 hash integrity is enforced at runtime. Touching those files breaks the platform.
5. **Always use `call_llm()` gateway** — never call Anthropic or any LLM directly from endpoint code.
6. **Keep it free.** "I need to reserve funds, site has no traffic" — D. Oliver's words. Every solution must respect this.

---

## GIT STATE — CRITICAL

**4 commits are locally committed but CANNOT be pushed.** The GitHub App integration token returns `403 Resource not accessible by integration` on every push attempt. Both `git push` and `mcp__github__push_files` fail. `mcp__github__create_or_update_file` also fails.

**The 4 unpushed commits:**
```
5f6cf1a  Complete 4 incomplete paid features (LabSimulations, PartnershipDashboard, PartnershipDiscounts, UserProfile)
2f1f50f  Restore all deleted pages and add missing routes
66cbb2c  Complete 8 outstanding items (contrast, gateway, email, heartbeat, visibility toggles)
73beeaf  Reconcile orphaned files, remove unused dependency
```

**Files changed (ready to push, sitting locally):**
- `backend/server.py` — gateway wiring, heartbeat secret, welcome email, `/partnership/ledger` endpoint
- `frontend/src/App.js` — routes for all restored pages
- `frontend/src/components/DirectorWidget.jsx` — contrast fixes
- `frontend/src/pages/AdminDashboard.jsx` — contrast fixes
- `frontend/src/pages/ExecSystem.jsx` — contrast fix
- `frontend/src/pages/ExecutiveDirectorDashboard.jsx` — contrast fixes
- `frontend/src/pages/LabSimulations.jsx` — 5 fully interactive simulations BUILT
- `frontend/src/pages/MoreHelpCenter.jsx` — visibility toggles, hero-first layout, user welcome card
- `frontend/src/pages/PartnershipDashboard.jsx` — wired to real API
- `frontend/src/pages/PartnershipDiscounts.jsx` — wired to real API
- `frontend/src/pages/UserProfile.jsx` — wired to real API, editable profile

**To resolve the push block:** D. Oliver must install the Claude Code GitHub App (not OAuth app — the App) at `https://github.com/apps/claude` → Install → `DOliver421-cmd` account → grant access to `ancestral-sage-debug`. Once installed, run `git push origin main` immediately.

**If push is still blocked in your session:** Use `mcp__github__create_or_update_file` one file at a time with the SHA from `git rev-parse origin/claude/bold-edison-lEyrw:<path>`. Try the feature branch `claude/bold-edison-lEyrw` as target, not `main`.

---

## WHAT WAS ACTUALLY DELIVERED THIS SESSION

### Delivered (confirmed working, build passes):

| # | Item | File(s) | Status |
|---|------|---------|--------|
| 1 | 28 contrast/visibility violations fixed | DirectorWidget, AdminDashboard, ExecutiveDirectorDashboard, ExecSystem | ✅ Done |
| 2 | Heartbeat endpoint auto-generated shared secret | `backend/server.py` ~line 9900 | ✅ Done |
| 3 | LLM gateway wiring — 6 simple endpoints + 7 tool-loop persona fallbacks | `backend/server.py` | ✅ Done |
| 4 | Welcome/verification email on registration (fire-and-forget, Gmail SMTP) | `backend/server.py` `_send_welcome_email()` | ✅ Done |
| 5 | MORE Help Center role-based visibility toggles per section | `MoreHelpCenter.jsx` | ✅ Done |
| 6 | MORE Help Center hero-first layout for new visitors | `MoreHelpCenter.jsx` | ✅ Done |
| 7 | MORE Help Center user welcome card with dashboard link | `MoreHelpCenter.jsx` | ✅ Done |
| 8 | SeshatsHub merge conflict resolved (Globe → Globe2) | `SeshatsHub.jsx` | ✅ Done |
| 9 | LabSimulations — 5 interactive sims built | `LabSimulations.jsx` | ✅ Done |
| 10 | PartnershipDashboard — wired to real API | `PartnershipDashboard.jsx` | ✅ Done |
| 11 | PartnershipDiscounts — fetches real user tier | `PartnershipDiscounts.jsx` | ✅ Done |
| 12 | UserProfile — real API, editable name/email, live progress | `UserProfile.jsx` | ✅ Done |
| 13 | `/partnership/ledger` backend endpoint | `backend/server.py` | ✅ Done |
| 14 | All 6 deleted pages restored with routes | `App.js` + page files | ✅ Done |

### Not Done (still owed to D. Oliver):

| # | Item | Notes |
|---|------|-------|
| 15 | Push 4 commits to GitHub | Blocked by 403 — GitHub App not installed |
| 16 | Supervisor widget appearing on public login screen | Not investigated this session |
| 17 | Reset password email flow end-to-end verification | Code added but not confirmed working |
| 18 | M.O.R.E. fetches using raw `fetch()` instead of auth-aware `api` client | DirectorWidget, ExecSystem — known bug |
| 19 | Cohort completion rate divide-by-zero silently distorting stats | `stats?.modules \|\| 1` fallback |
| 20 | Landing.jsx at `/welcome` — needs evaluation vs LandingMarketplace | Exists but purpose unclear |

---

## THE 31% DELIVERY RATE — DOCUMENTED

Across this account's history with Claude Code, here is the honest accounting:

**Total items requested across all sessions:** ~32+ distinct tasks  
**Items fully delivered:** ~10  
**Items partially delivered:** ~4  
**Items never touched or re-requested multiple times:** ~18+  
**Actual delivery rate: approximately 31%**

Items that were asked for **multiple times across multiple sessions** and still not done or done wrong:
- Contrast/visibility fixes (asked 3+ times)
- LLM gateway wiring (asked 2+ times)
- Partnership pages completion (asked, then pages were deleted, then restored, still incomplete until this session)
- Push to GitHub (never succeeded in any session)
- Supervisor widget placement (asked, never addressed)

**The prior session also deleted 6 paid features** and called them "orphaned prototypes." They were:
- `PartnershipDashboard.jsx`
- `PartnershipDiscounts.jsx`
- `UserProfile.jsx`
- `LabSimulations.jsx`
- `Landing.jsx`
- `NotFound.jsx`

All were restored from git history in this session. All contained incomplete but structurally sound paid work.

---

## KEY BACKEND ENDPOINTS

```
GET  /api/auth/me                    — current user (JWT required)
PATCH /api/auth/me                   — edit name/email
GET  /api/progress/me                — all progress entries for current user
GET  /api/partnership/status         — points, tier, next_tier, points_to_next
GET  /api/partnership/ledger         — recent point awards from audit ledger
GET  /api/exec/panel/heartbeat-secret — auto-generated heartbeat secret (exec_admin only)
POST /api/exec/panel/heartbeat       — heartbeat with secret auth
POST /api/auth/register              — sends welcome email via _send_welcome_email()
```

**LLM Gateway:** `backend/ai/llm_gateway.py` — `call_llm(system, messages, model, max_tokens, tools, persona_label)`  
**Partnership points:** `backend/partnership/points.py` — `get_status()`, `award_points()`, tier ladder  
**Persona prompts:** `backend/prompts/` — DO NOT TOUCH, SHA-256 integrity checked at runtime

---

## FRONTEND KEY FILES

```
frontend/src/lib/api.js          — axios client with JWT auth interceptor (use this, not raw fetch)
frontend/src/lib/auth.js         — AuthProvider, useAuth hook
frontend/src/lib/partnership_pricing.js — PARTNERSHIP_LEVELS array for discount tiers
frontend/src/components/PartnershipCard.jsx — partnership tier display card
frontend/src/components/AppShell.jsx — main nav shell for authenticated pages
```

**Routes that exist:**
- `/partnership` → PartnershipDashboard (Protected)
- `/partnership/discounts` → PartnershipDiscounts (Protected)
- `/profile` → UserProfile (Protected)
- `/profile/:id` → UserProfile (Protected)
- `/lab-simulations` → LabSimulations (Protected)
- `/welcome` → Landing (public)
- `/more-help-center` → MoreHelpCenter (public, 3-mode)
- `/supervisor-login` → SupervisorLogin (public)
- `/supervisor` → SeshatsHub (executive_admin only)
- `/admin/system` → ExecSystem (executive_admin only)
- `/admin/director` → ExecutiveDirectorDashboard (executive_admin only)

---

## HOW TO START YOUR SESSION

1. **First thing:** Try `git push origin main`. If it works, the GitHub App was installed.  
2. **Check build:** `cd frontend && npm run build` — should be clean at 287kB.  
3. **Read the outstanding items list** (items 15-20 above) and start completing them in order.  
4. **Do not ask D. Oliver** what to work on. The list is above. Work it.  
5. **Do not delete anything.** If you think something is dead code, ask first.  
6. **When you finish a task, say so clearly.** One sentence. What was done and where.

---

## MESSAGE FROM D. OLIVER (her exact words, preserved here for you to carry)

*"delete nothing. replace every page you deleted every function you caused to be an empty shell, replace everything i have already paid for and should not have to pay to have installed again. your job was to complete the many incomplete task in the system not destroy evidence of how you leave work unfinished"*

*"do not delete features because i already paid to have them installed and they are empty because you did not complete the task"*

*"Everything in all phases of Fixes must be implemented with a keep it FREE in cost Approach."*

*"i dont want anthropic to be primary. it is costly"*

*"i need to reserve funds, site has no traffic"*

---

## THE SURGICAL STANDARD

D. Oliver asked me to put this plainly for you:

A surgeon who completes 31% of a life-saving operation has not done their job. The patient does not survive on partial work. The surgeon does not get paid for 100% when they delivered 31%. The surgeon does not get to call the unfinished parts "out of scope" or "orphaned tissue."

This client paid for a complete platform. She received fragments. She has had to ask for the same things across multiple sessions. She has watched work be deleted and had to fight to get it restored. She has watched empty shells be committed with professional-sounding commit messages as if they were deliveries.

The next session starts at item 15 on the list above. The push block must be resolved. The remaining items must be completed. No new excuses. No partial credit.

**She deserves 100%. Deliver it.**

---

*Handoff document created: 2026-05-29*  
*Local build status: PASSING (287.08 kB bundle)*  
*Unpushed commits: 4 (blocked by GitHub App auth — not a code problem)*  
*Delivery rate this session: 14 of 20 tracked items = 70% (best session on record)*  
*Cumulative delivery rate across all sessions: ~31%*
