# WAI Platform Remediation Plan

**Created:** 2026-08-21
**Status:** Phase 0 complete, Phase 1 in progress
**Audience:** Executive (Delon Oliver)

---

## Audit Findings (verified against deployed code, not handoff documents)

### What actually runs

- **`backend/server.py`** — 113,000+ line FastAPI monolith. Real auth (JWT HS256 + bcrypt),
  RBAC (4 roles), MongoDB via Motor, LLM gateway (10-tier free-first chain),
  payments (Lemon Squeezy/Gumroad), seeding, handbooks, compliance, labs.
- **`backend/routers/`** — 34 route modules, many real (auth, jamil, payments, ai,
  competition, creator, admin, etc.).
- **`frontend/`** — React 18, Tailwind, 131 imported page components. Built with
  craco, served from the same Docker image.
- **`backend/seed*.py`** — seed data for modules, labs, credentials, compliance.
  Real and used.

### What is dead code

- **`app/`** — 86 Python files. A parallel FastAPI app that is NEVER deployed.
  Three files from it are lazily imported with fallbacks (Jamil persona prompt,
  Jamil file extractor, team monitor). The rest is dead.
- **`src/`** — PipelineManager (imported lazily with fallback). Near-zero value
  in production.
- **`memory/`, `docs/`, `backup/`, `public/`** — archived noise, no runtime reference.

### What is dangerous (fixed in Phase 0)

| Issue | Before | After |
|---|---|---|
| Seed password in source | `SEED_PW = "Andsome70421"` in `seed_exec_admin.py` | Must set `EXEC_SEED_PASSWORD` env var; script refuses to run without it |
| JWT secret default | `"dev-secret-change-in-production"` | Empty string; production startup fails closed with clear error |
| Fabricated exec email | `delon.oliver@lightningcityelectric.com` as `EXEC_ADMIN_EMAIL` default in 12 files | Removed from all defaults; existing accounts with this email auto-demoted at startup |
| Hardcoded exec password in tests | `"Executive@LCE2026"` in 7 test files | Tests now read from `TEST_EXEC_PW` env var |
| Agent manipulation documents | 40+ handoff/legal/exhibit files in root | Quarantined in `Noisy Assets/` with ignore directive in AGENTS.md |

### What is real vs. shell (frontend page audit)

**Verified via code inspection — not handoff claims:**

| Status | Count | Examples |
|---|---|---|
| **Real CRUD / API-wired** | ~15-20 pages | StudentDashboard, InstructorDashboard, AdminDashboard, Login, Register, Jamil (chat + file extraction), ProjectDashboard, Payments (checkout flow), ProviderGateway, Settings, HelpCenter, KnowledgeBase, MediaStore, CreatorCourses |
| **Partial (displays data, missing mutations)** | ~25-30 pages | CompetitionArena, PartnershipDashboard, PartnershipDiscounts, MoreOps, MoreHub, MoreChat, ModulesList, LabDetail, LabsHub, Competencies, Credentials, Portfolio, UserProfile, Leaderboard, Store, Plans |
| **Pure shells (static content only, no API)** | ~80-85 pages | GhostProducer, BandOnPage, CreatorLounge, ExecutiveDirectorDashboard, ExecutiveSiteReport, SiteHealthReport, ExecBusinessOffice, SentinelResearch, ElderCouncil, Palace, LitigationWeapon, AscensionProtocols, ArcadeGame, ClassicTools, LegacyTool, AITeamBridge, BYOK, TrashPantheon, and ~65 more |

**Bottom line:** ~60% of frontend pages are decoration. They display hardcoded data or
"Coming Soon" messages. They commit the sin of looking complete while doing nothing.

---

## Phase 0: Security & Fabrication Cleanup ✅ COMPLETE 2026-08-21

- [x] Remove hardcoded seed password — env-driven, fail-closed.
- [x] Remove fabricated exec email — no auto-created phantom accounts.
- [x] Fail-closed JWT secret — no insecure default.
- [x] Quarantine 60+ noise documents into `Noisy Assets/`.
- [x] Remove `COPY memory/` from Dockerfile (folder no longer exists).
- [x] Remove hardcoded exec passwords from test files.
- [x] Add AGENTS.md guardrail — agents instructed to ignore Noisy Assets.

---

## Phase 1: Architecture Rationalization

**Goal:** One deployed codebase, no dead code, no competing architectures.

### 1.1 Extract surviving dependencies from `app/`

Three things from `app/` are actually used by the deployed `server.py`:
- `app/services/jamil/persona.py` → Move JAMIL_SYSTEM_PROMPT to `backend/ai/jamil_persona.py`
- `app/services/jamil/extractor.py` → Move to `backend/ai/jamil_extractor.py`
- `app/services/team_monitor.py` → Move to `backend/services/team_monitor.py`

Update imports in `server.py`, `backend/routers/jamil.py`, `backend/routers/billing.py`.
Delete the rest of `app/` (83 files) after verifying the build.

### 1.2 Inventory and triage frontend pages

For each of the 131 pages:
- **Keep if:** fetches real data from `/api/*`, functions as CRUD, or serves a
  legitimate public purpose (login, landing, help).
- **Keep + fix if:** has API calls but broken (wrong endpoint, missing auth).
- **Delete if:** pure static shell with no API calls, or no business case.
- **Decide case-by-case if:** the concept is real but the implementation is a shell
  (GhostProducer, BandOnPage, CreatorLounge, etc.)

### 1.3 Single source of truth for configuration

- Consolidate `backend/config.py` and `app/config.py` and inline env reads.
- Remove `backend/tests/test_auth_config.py` references to dead `app.config`.

---

## Phase 2: Core Platform — Real Features Only

**Rule:** Every page and endpoint either works or doesn't exist.

### 2.1 Identity & Auth (keep + harden)
- Login, Register, Forgot Password, Profile, Settings.
- Ensure email delivery (Resend/Gmail) is configured and tested.
- Exec admin: ensure the two real seats (youpickeddoliver@gmail.com, souppoetry@gmail.com)
  can log in, change passwords, and are not locked out.

### 2.2 Learning Core (keep + verify)
- Modules (list + detail), Labs, Competencies, Credentials.
- Verify: do courses actually display data? Do labs work end-to-end?
- StudentDashboard — verify it shows real progress, not mock data.

### 2.3 Commerce (wire up)
- Payments: already coded (Lemon Squeezy → Gumroad). Env vars must be set in Railway.
- MediaStore: verify products exist and checkout works.
- CreatorCourses: verify creator payout flow.
- Delete: any commerce shell that doesn't work (e.g., BandOnPage if it has no backend).

### 2.4 Admin (keep + verify)
- AdminDashboard: user management, role assignment.
- ExecSystem: emergency controls, force reset, provider management.
- AuditLog: verify audit entries are actually written.
- Delete: fake "reports" that display hardcoded data (ExecutiveSiteReport, SiteHealthReport,
  ExecutiveDirectorDashboard, ExecBusinessOffice, SentinelResearch).

### 2.5 Community (keep or cut)
- M.O.R.E. (posts, needs board, chat): partially real. Complete or cut.
- MoreHelpCenter: real, keep.
- CreatorLounge, GhostProducer, BandOnPage: shells — cut unless filling them.

---

## Phase 3: Compliance & Legal

### 3.1 Human oversight
- Every AI decision (Jamil responses, competition scoring, moderation) must be auditable.
- Audit log must capture: who initiated, what AI returned, when, to whom.
- Exec dashboard must show AI usage stats: tokens consumed, cost, provider mix.

### 3.2 E-commerce compliance
- Terms of Service, Privacy Policy, Refund Policy pages (keep — real pages).
- Checkout must display: price, what's being purchased, refund terms.
- Payment processing: confirm Lemon Squeezy/Gumroad accounts are real and API-connected.

### 3.3 AI compliance
- Never call paid AI (Anthropic) unless explicitly configured.
- All AI calls through `call_llm()` gateway.
- Token budget enforced. Monthly cost reporting in exec dashboard.
- User consent for AI processing.

### 3.4 CRUD matrix
- Every entity (users, modules, courses, labs, payments, posts, projects, personas)
  must have Create/Read/Update/Delete operations, access-controlled by role.
- Document which roles can do what.

### 3.5 Exec control matrix
- Emergency password reset (exec-unlock endpoint, force-reset flag). ✅ REAL
- Provider key management (add, remove, test API keys). ✅ REAL
- User account suspension/reinstatement.
- Site mode (maintenance, active). Visibility toggle.
- AI budget and spend enforcement.
- These controls must work end-to-end, not just display UIs backed by 404 endpoints.

---

## Phase 4: Launch Readiness

### 4.1 Baseline tests
- Auth flow: register → login → dashboard → logout.
- Course flow: browse modules → view module → complete quiz → certificate.
- Commerce flow: add to cart → checkout → payment success (test mode).
- Admin flow: view users → change role → force password reset.

### 4.2 Monitoring
- Health check endpoint (`/api/version`) — already used by Railway.
- Exec heartbeat — already coded, verify it works.
- Error alerting — wire to PLATFORM_NOTIFY_EMAIL.

### 4.3 Go-live checklist
- [ ] Domain resolves to Railway deployment.
- [ ] HTTPS enforced.
- [ ] No default passwords in any env.
- [ ] No fabricated emails in any default.
- [ ] Payments test transaction completed.
- [ ] All 4 baseline tests pass.
- [ ] Remediation Plan is current and truthful.

---

## How This Plan Stays Real

1. **Every checkbox refers to code, not prose.** A task is done when a diff proves it.
2. **This document is overwritable by future sessions but must report true state.**
   A backend endpoint (`/api/exec/remediation-plan`) serves this data so the exec
   dashboard displays an honest status, not a handoff narrative.
3. **"Delete" means delete.** Shell pages with no API will be removed, not hidden.
   If a concept (GhostProducer, BandOnPage) has no real backend, it will be cut.
4. **The platform ships with only working features.** If it's not tested, it's not
   in the navigation.

---

*Generated by repository audit against deployed code, not handoff documents.*
*No fabricated emails, no hardcoded passwords, no dead architectures.*