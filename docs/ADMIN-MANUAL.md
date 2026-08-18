# WAI-Institute — Administration & Executive Manual

**Version:** 1.0 · **Last updated:** 2026-08-17
**Audience:** Executive Admins, Admins, and operators of the WAI-Institute platform.
**Scope:** This manual is the operations reference for the WAI-Institute platform. It documents every site area, every executive control, and how to make changes to the site through the Executive Deck, the Keys tab (Provider Gateway), and the deploy pipeline.

> **Keep this manual in the repo (`docs/ADMIN-MANUAL.md`) and update it whenever a control changes.** If you add, rename, remove, or re-scope a page, route, control, or environment variable, update the relevant section below in the same change.

---

## 1. Overview

The WAI-Institute platform is a **single-service web application**:

- **Backend:** Python 3.11 + FastAPI (`backend/server.py` + modular routers in `backend/routers/`), MongoDB via Motor.
- **Frontend:** React 18 SPA (`frontend/`), built with CRACO, served by the backend itself (`SERVE_FRONTEND=1`).
- **Deployment:** Railway, single Docker image (see §6 Deploy Pipeline).
- **Auth:** JWT (bearer token stored as `lce_token` in localStorage). Four core roles: `student`, `instructor`, `admin`, `executive_admin`.

### 1.1 Roles & access

| Role | Rank | Can | Executive Deck access |
|---|---|---|---|
| `student` | 1 | Learn, submit labs, earn credentials/XP | No |
| `instructor` | 2 | Manage rosters, approve labs, attendance | No |
| `admin` | 3 | Administration section, users, analytics, moderation, M.O.R.E. admin/ops, AI Team Bridge | Administration section only |
| `executive_admin` | 4 | Everything incl. Executive Deck, Provider Gateway, failover, break-glass | Full |

Role hierarchy is enforced on both the frontend (`ROLE_RANK` in `App.js`) and backend (`ROLE_RANK` + `require_role`/`_require_rank`). A higher rank passes a lower-rank guard, so `executive_admin` can access anything `admin` can.

The three executive seats are auto-provisioned/reset on startup (see §6.4). `EXEC_FORCE_RESET=1` resets them to defaults on every start; `/api/auth/exec-unlock` does the same on demand with `EXEC_RESET_SECRET`.

---

## 2. Site Areas

The sidebar (`frontend/src/components/AppShell.jsx`) groups the site into sections. This table lists every area, its primary route(s), and what it does. All routes live in `frontend/src/App.js`.

### 2.1 Home (everyone)

| Area | Route(s) | Purpose |
|---|---|---|
| Dashboard | `/dashboard` | Role-aware landing after login. |
| My Profile | `/profile`, `/u/:username`, `/profile/:id` | Personal profile, public profile, user profiles. |
| My Position | `/my-position` | Current role/position card. |
| Settings | `/settings` | Account settings, password change, session management. |
| My AI (BYOK) | `/byok` | $3 Bring-Your-Own-Key unlock + key management (§7). |
| Avatar Setup | `/avatar-setup` | Avatar creation. |

### 2.2 Learn

| Area | Route(s) | Purpose |
|---|---|---|
| AI Tutor | `/ai` | Ancestral Sage / tutor chat with modes (tutor, scripture, electrician…). |
| Council (Sage) | `/council` | Sage council view. |
| Curriculum | `/modules`, `/modules/:slug` | Course/module catalog and detail. |
| Workforce Labs | `/labs`, `/labs/:slug`, `/lab` | Labs catalog, detail, lab page. |
| Lab Simulations | `/lab-simulations` | Simulation-based labs. |
| Compliance | `/compliance`, `/compliance/:slug` | Compliance modules. |
| Learning Path | `/adaptive` | Adaptive/learning-path engine. |
| Competencies | `/competencies` | Competency tracker. |
| Courses | `/courses` | Course catalog. |

### 2.3 Credentials

| Area | Route(s) | Purpose |
|---|---|---|
| Credentials | `/credentials` | Badges/competency credentials. |
| Certificates | `/certificates` | Awarded certificates. |
| Portfolio | `/portfolio` | User portfolio. |

### 2.4 Community

| Area | Route(s) | Purpose |
|---|---|---|
| Members' Palace | `/palace` | Member community space. |
| Elder Council | `/elder-council`, `/council` | Elder council community space. |
| XP Leaderboard | `/leaderboard` | XP rankings. |
| Report Incident | `/incidents` | Incident reporting. |
| Community | `/community` | Community hub. |
| Seshats Hub | `/seshats-hub` | Public supervisor/mentor hub. |
| Personas | `/personas`, `/personas/:slug` | Public persona directory. |
| Missing/Kameron | `/missing/kameron`, `/s-research`, `/trash`, `/trash-pantheon` | Legacy/archive pages. |

### 2.5 M.O.R.E. (help center & community support)

| Area | Route(s) | Purpose |
|---|---|---|
| M.O.R.E. Hub | `/app/more` (auth), `/more` (public) | Community support hub — posts, needs, help. |
| M.O.R.E. Help Center | `/more-help-center` | Full help center / site index (public). |
| Community Chat | `/more/chat`, `/more/chat/:roomId` | M.O.R.E. community chat rooms. |
| Legal Tools | `/more/litigation` | Legal drafting tools. |
| Personal Helper | `/app/helper` (auth), `/helper` (public) | Guided helper workspace (tools + chat). |
| Help Center | `/help-center` | Simple help center. |
| M.O.R.E. Admin | `/more/admin` (admin+) | Moderation queue, flags, appeals, purge. |
| Dept. AI Ops | `/more/ops` (admin+) | M.O.R.E. Department AI — 13-persona ops assistant (Executive, Revenue, Finance, Production, Customer Success). |

### 2.6 Creator's Sanctuary (all roles; page enforces tier locks)

| Area | Route(s) | Purpose |
|---|---|---|
| Social Blast | `/social/publish` | Cross-platform social publishing. |
| Creator Studio | `/studio` | Music/audio creator studio. |
| Course Manager | `/creator/courses` | Creator course management. |
| My Earnings | `/creator/earnings` | Creator earnings. |
| Payout Dashboard | `/creator/payouts` | Creator payouts. |
| Creator Profile | `/creator/profile/edit`, `/creator/:slug`, `/creators` | Creator profiles + directory. |
| Creator Lounge | `/creator-lounge` | Creator community. |
| Ghost Producer | `/ghost-producer` | Ghost-production toolset (incl. native browser voice). |
| Band on a Page | `/band` | Band page. |
| Playlist Manager | `/playlist/dashboard`, `/playlist/:slug/submit` | Playlist management + submissions. |
| Virtual Arcade | `/arcade`, `/arcade/:slug` | Points/puzzle arcade. |

### 2.7 Commerce

| Area | Route(s) | Purpose |
|---|---|---|
| Store | `/merch` | WAI storefront (Gumroad → Lemon Squeezy). |
| Media Store | `/store` | Digital media products store. |
| Plans & Pricing | `/plans` | Membership plans/pricing. |
| Membership | `/subscribe` | Subscription signup. |
| Donate | `/donate` | Donations. |
| Payment History | `/payment/history`, `/payment/success`, `/payment/cancel`, `/payment/manage` | Payment records + provider redirects. |
| Partnerships | `/partnership`, `/partnership/discounts` | Partnership program + discounts. |

### 2.8 Instructor (instructor+)

| Area | Route(s) | Purpose |
|---|---|---|
| My Roster | `/instructor` | Instructor roster. |
| Lab Approvals | `/instructor/labs` | Approve/submit labs. |
| Attendance | `/attendance` | Attendance tracking. |
| Dashboard (instructor) | `/dashboard/instructor` | Instructor dashboard. |

### 2.9 Administration (admin+)

| Area | Route(s) | Purpose |
|---|---|---|
| Admin Overview | `/admin`, `/dashboard/admin` | Admin dashboard (users, incidents, stats). |
| Users | `/admin/users` | Full user management (create, edit, roles, tiers, sessions). |
| Sites & Inventory | `/admin/tools` | Sites and inventory. |
| Analytics | `/admin/analytics` | Program analytics + benchmarks. |
| Audit Log | `/admin/audit` | Auditable action log. |
| Payments | `/admin/payments` | Payment records. |
| Billing | `/admin/billing` | Credits, refunds, Sage sessions. |
| Prices | `/admin/prices` | Platform pricing. |
| System Health | `/admin/health` | Health checks. |
| Moderation | `/admin/moderation` | Content moderation. |
| Revenue | `/revenue` | Revenue division dashboard. |
| Auditor | `/auditor` | Auditor dashboard. |
| Admin Assistant | `/assistant` | Admin assistant chat (native browser voice). |
| AI Team Bridge | `/admin/bridge` | Cross-domain AI team bridge (Director + NAM Oshun Scholar + Curriculum Analyst). |
| AAWAB Admin | `/admin/aawab` | Agent Wellness & Certification Bureau — platform-wide agent health, badge revocation, isolation overrides (§2.13). |
| AI Business Office | `/business-office` · `/admin/business-office` | Revenue engine command center — owner-first P&L waterfall, mission runway, revenue KPIs, tools dock (the capabilities AI runs for income), 16 business divisions, the A2A economy (Workforce Exchange + Red-Teaming Bureau), B2B service deals pipeline, performance-linked workforce ledger (§2.14). |
| Office Control (no-code) | `/admin/office-control` | **Exec Control** — edit every office number and text string (goal, infra cost, owner draw %, fees, prices, all division/tool copy) without code (§2.15). |

> **Note:** `/admin/accounts` (Account Controls) is a legacy duplicate of user management. The route still works, but the sidebar points to **Users** for all user administration.

### 2.10 Executive (executive_admin only — the Executive Deck)

| Area | Route(s) | Purpose |
|---|---|---|
| Exec System | `/admin/system`, `/dashboard/exec` | User database, create/edit/reset users, bulk actions, exec seats. |
| Site Control | `/admin/control` | Platform flags, broadcast messages, site controls. |
| Sovereign Command | `/admin/exec-control` | User roles, feature tiers, AI persona access, break-glass, failover, audit. |
| Director Dashboard | `/admin/director` | Executive Director dashboard — incident actions, user actions, platform lock, feature flags, broadcast. |
| Sage Audit | `/admin/sage-audit` | Sage/AI audit log. |
| Staff Meetings | `/admin/staff-meetings` | Staff meeting history + convene (PRT + The 9 synthesis). |
| **Executive Site Report** | `/admin/exec-report` | Full-system white-glove audit (§4). |
| Provider Gateway (Keys) | `/admin/providers` | The Keys tab — AI provider keys (§5). |
| Team Ops | `/team/ops` | Team operations + action log. |
| Supervisor Hub | `/supervisor` | Supervisor control hub. |
| The Arena | `/arena` | Competition arena. |
| Jamil | `/jamil` | Jamil — Director-class AI assistant (voice/file/chat). |
| Projects | `/projects` | Projects board. |

### 2.11 Auth & public

| Area | Route(s) |
|---|---|
| Landing | `/`, `/landing`, `/welcome` |
| Login / Register | `/login`, `/register`, `/supervisor-login` |
| Forgot / Reset | `/forgot-password`, `/reset-password` |
| Legal | `/terms`, `/privacy`, `/factory-reset` |
| Internships | `/internships` |

### 2.12 Handbooks (public reference documents)

The flagship curriculum documents are served as public HTML pages from `backend/handbooks/html/` via `backend/routers/handbooks.py`:

| Route | Document |
|---|---|
| `GET /api/handbooks` | List available handbooks. |
| `GET /api/handbooks/instructor` | Instructor Handbook — mission, role, the 12-module/142-hour program, teaching principles, classroom management, escalation. |
| `GET /api/handbooks/student` | Student Handbook — welcome, what you'll learn, competency assessment, M.O.R.E., code of conduct. |
| `GET /api/handbooks/admin` | Admin Handbook. |
| `GET /api/handbooks/persona` | AI Persona Creation Manual. |
| `GET /api/handbooks/{name}/raw` | Raw HTML body (for embedding/tools). |

Links to the Instructor and Student handbooks appear on the **Curriculum** page (`/modules`) and in the **M.O.R.E. help center** nav. The **Curriculum Analyst** (AI Team Bridge) is seeded with the handbook content so its curriculum work is grounded in the flagship program.

### 2.13 AAWAB — Agent Wellness & Certification Bureau

| Area | Route(s) | Purpose |
|---|---|---|
| Agent Registry | `/aawab` (auth) | User dashboard — register AI agents, monitor vital stats (CVS, token velocity, context load, memory fragmentation), run diagnostics/treatments/certification. |
| Certification Chamber | `/aawab/chamber` (auth) | Guided wizard: Intake Diagnostic → Treatment → Stress Gauntlet → ACA badge (download/share/verify). |
| AAWAB Admin | `/admin/aawab` (admin+) | Bureau oversight — platform-wide health cards, all agents, revoke certifications, override isolation holds, recent treatments log. |
| Public registry | `GET /api/aawab/registry` | Certified agents + platform vitality analytics (public). |
| Badge verification | `GET /api/aawab/badge/{id}/verify` | HMAC-SHA256 badge verification (public). |

The full how-to, data model, API reference, legal notes, and the executive/admin task list live in **`docs/AAWAB_MANUAL.md`**. The Site Guide persona and site search (`/api/search`) know about AAWAB.

### 2.14 AI Business Office — the revenue engine command center

| Area | Route(s) | Purpose |
|---|---|---|
| AI Business Office | `/business-office` (auth) | Mission runway, **owner-first P&L waterfall** (gross → infra → net profit → owner retained → performance pool), revenue KPIs from the real payments ledger, the tools dock, **16 business divisions** (memberships, store, social agency, micro-SaaS, BYOK, audits, persona foundry, AAWAB, **Workforce Exchange, Red-Teaming Bureau, Living Archive, compliance gigs, dev maintenance, SEO retainers, invoice ops**, e-commerce pipeline), the B2B deals pipeline, and the performance-linked workforce ledger. |
| Office Admin | `/admin/business-office` (admin+) | Set the monthly goal, advance/close deals (human-approval flag), open/update workforce jobs, settle exchange contracts, Merge/Approve red-team patches, top revenue sources, recent orders. |
| Service deals API | `POST /api/abo/deals` · `POST /api/abo/deals/{id}/propose` | Members submit a service engagement → a Lead (lead → proposed → won → delivered). Admins trigger the office AI to draft a deliverable proposal (`call_llm`, template fallback if the gateway is down). |
| Workforce Exchange | `POST /api/abo/exchange/contracts` · `POST .../contracts/{id}/complete` | A2A economy — agent task contracts with a clearinghouse fee (default 10%, editable) booked on completion. |
| Red-Teaming Bureau | `POST /api/abo/redteam/engagements` · `POST .../{id}/approve` · `POST .../{id}/close` | Adversarial AI scans client systems and drafts sandboxed patches; the human **Merge/Approve** click ships them and books contracted revenue ($495 / $799/mo, editable). |
| Public mission meter | `GET /api/abo/public-status` | Aggregate runway only (goal, month revenue, pct, status) — powers the Mission Funding strip on the M.O.R.E. Help Center landing. No private order/product data. |
| Workforce ledger API | `GET /api/abo/jobs` | People & AI. AI jobs carry `value_cents` (revenue created); **human roles are performance-linked** (`pay_type` commission/distribution, `commission_pct`) — payable only from net profit at the owner's direction, never a fixed out-of-pocket liability. Seeded with 5 AI jobs + 3 commission-linked human roles. |

Mission rule: **no revenue = no office = no jobs for people or the AI workforce.** Owner-first rule: **revenue → infrastructure → net profit to the owner/entity; nothing is auto-drained.** Labor rule: **performance-linked — commissions/distributions from net profit only, at the owner's direction.** Every division keeps the human as the responsible party (merchant accounts, contracts, payouts, liability) while AI executes the work.

The full how-to, API reference, division-of-labor, and the executive/admin task list live in **`docs/ABO_MANUAL.md`**; the complete revenue strategy, P&L model, banking-viability rationale, and 90-day plan live in **`docs/BUSINESS_PLAN.md`**. The Site Guide persona and site search (`/api/search`) know about the AI Business Office, and the Site Guide chat has a **Hire the Office** CTA.

### 2.15 Office Control — Exec Control (no-code)

| Area | Route(s) | Purpose |
|---|---|---|
| Exec Control | `/admin/office-control` (admin+) | **Change every office number and text without code.** `GET/PUT /api/abo/config` reads/writes `db.abo_config` (audited, `abo.config.updated`). Numbers: monthly goal, infrastructure costs, owner draw %, clearinghouse fee %, red-team prices. Text: header, runway, loops, all five guardrails, all 16 division cards, all 12 tool cards. Empty values restore defaults. The owner-first waterfall and performance-linked labor model cannot be disabled from the panel. |

---

## 3. The Executive Deck

The Executive Deck is the set of executive-only controls. All require `executive_admin`. They are grouped under **Executive** in the sidebar.

### 3.1 Exec System — `/admin/system`
User database and account administration:
- **Create user** (with generated password + one-time reset link), **edit** (name, email, role), **reset password**, **deactivate/activate**, **delete**.
- **Bulk actions** (role change, suspend, unsuspend) via `POST /api/admin/users/bulk` (exec-only).
- **Force logout / session revocation** (increments token version).
- **Sage tier / feature tier** assignment.
- Backend endpoints: `POST/PATCH/DELETE /api/admin/users*`, `POST /api/admin/users/bulk`, `POST /api/admin/users/{uid}/reset-link`.

### 3.2 Site Control — `/admin/control`
Platform-wide site controls:
- **Feature flags** (`GET/POST /api/admin/platform/flags`, `POST /api/admin/platform/flags/{flag}`) with reason-required modal.
- **Broadcast messages** (site-wide info/warning).
- **AI spend budget** (`POST /api/admin/ai-spend-budget`).

### 3.3 Sovereign Command — `/admin/exec-control`
The highest-privilege control panel:
- **User role** changes, **feature tier**, **AI persona access** toggles.
- **Break-glass** audit trail and **failover** (`POST /api/exec/failover` to `primary`/`backup`/`emergency`).
- **Circuit-breaker panel** health + toggles (`/api/exec/panel`, `/api/exec/panel/toggle`, `/api/exec/panel/reset`).
- **Heartbeat secret** (`GET /api/exec/panel/heartbeat-secret`).

### 3.4 Director Dashboard — `/admin/director`
Executive Director operational dashboard:
- Incident actions, user actions, **platform lock**, **feature flags**, **broadcast**.

### 3.5 Sage Audit — `/admin/sage-audit`
AI/Sage audit trail (`GET /api/admin/sage/audit`, `/api/admin/sage/cap`, `/api/admin/sage/metrics`).

### 3.6 Staff Meetings — `/admin/staff-meetings`
Convene and review staff meetings. Backend: `GET/POST /api/exec/staff-meetings` and `POST /api/exec/staff-meeting`. Meetings run PRT (Poor Righteous Teacher) + The 9 synthesis.

### 3.7 Executive Site Report — `/admin/exec-report`
Runs a full-system white-glove audit and returns a live readiness report. See §4.

### 3.8 Team Ops — `/team/ops`
Team operations view with an action log.

### 3.9 Supervisor Hub — `/supervisor`
Supervisor control hub (supervisor-gated; exec-only).

### 3.10 The Arena — `/arena`
Competition arena — task submission, scoring, leaderboard (`/api/competition/*`).

### 3.11 Jamil — `/jamil`
Jamil, the Director-class assistant — chat, file upload, transcription, voice (native browser TTS), knowledge base (`/api/jamil/*`, 12-hour knowledge digest).

### 3.12 AI Team Bridge — `/admin/bridge`
Cross-domain coordination with the partner AI team at `www.wai-institute.org` / `we-are-the-original.lovable.app`. Editable partner name/goals/protocol, roster (Director, NAM Oshun Scholar, Curriculum Analyst, Ambassador…), dispatch + inbound webhook (`/api/bridge/*`). All AI runs through the free-first LLM gateway.

---

## 4. Executive Site Report (white-glove audit)

**Route:** `/admin/exec-report` (exec-only) · **Endpoint:** `GET /api/exec/site-report`

The report is a live, full-system audit across seven categories:

1. **Code & Application** — Python runtime, `APP_ENV`, persona registry.
2. **Database & Data** — MongoDB connectivity + document counts for core collections (users, modules, labs, progress, payments, projects, M.O.R.E., audit log…).
3. **Security & Access** — JWT secret, field-level RBAC, rate limiting, CORS, exec-seat protection.
4. **Integrations** — LLM gateway providers, voice (native browser TTS), email delivery, Slack alerts.
5. **Ecommerce & Payments** — active payment provider (Stripe / Lemon Squeezy / Gumroad / DB-archive) and publisher keys.
6. **Edge & Background** — knowledge digest scheduler, provider gateway live reload.
7. **Public Readiness** — health/version endpoints, auth flow, public M.O.R.E. board, public app URL.

Each check reports **pass / warn / fail** with a human-readable detail. The report returns an overall status (`operational` / `degraded` / `critical`) and a **readiness score** (percent pass). It **never exposes secret values** — only whether a key or provider is configured. Use it before any public go-live and after any deploy.

---

## 5. The Keys Tab (Provider Gateway)

**Route:** `/admin/providers` (exec-only) · **Endpoints:** `/api/providers*`

The Keys tab is where you manage AI provider keys for the free-first LLM gateway. Keys are **encrypted at rest** (Fernet, using `PROVIDER_KEY_ENCRYPTION_SECRET`) and stored in MongoDB (`ai_provider_keys`), **never in the frontend or localStorage**.

### 5.1 What you can do

- **Add a key** — pick a provider (Groq, Cerebras, Gemini, Grok/xAI, Cohere, OpenRouter, HuggingFace, Anthropic, or custom), give it a label + scope. `POST /api/providers/keys`. The gateway **reloads immediately** — no redeploy needed.
- **Test a key** — `POST /api/providers/keys/{id}/test` makes a real 1-token call and reports `ok`, `latency_ms`, `status_code`.
- **Remove a key** — `DELETE /api/providers/keys/{id}`.
- **View usage** — `GET /api/providers/usage-log` (last 500 gateway calls).
- **Quick setup** — `POST /api/providers/quick-setup` + status endpoint for one-click provider setup.

### 5.2 Free-first routing

The LLM gateway (`backend/ai/llm_gateway.py`) routes in this order: **Groq → Cerebras → Gemini → Grok/xAI → Cohere → OpenRouter → HuggingFace → Anthropic (paid last resort) → KB fallback (always available)**. It never calls a paid provider unless no free tier is configured. An hourly token cap (`HOURLY_TOKEN_CAP`, default 200k) guards spend.

### 5.3 Env-var keys vs Keys-tab keys

- **Env-var keys** (set in Railway Variables): read at startup — e.g. `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY`, `ANTHROPIC_API_KEY`.
- **Keys-tab keys** (stored encrypted in Mongo): added live via the UI, encrypted with `PROVIDER_KEY_ENCRYPTION_SECRET`, and hot-reloaded via `reload_provider_keys()`.

Prefer the Keys tab for runtime-managed keys (no redeploys).

---

## 6. Deploy Pipeline

The platform deploys to **Railway** as a single Docker image.

### 6.1 Build (Dockerfile)

Two-stage build:
1. **Frontend build** — `node:18-alpine`, `npm ci --legacy-peer-deps`, then `npm run build` (CRACO). `REACT_APP_BACKEND_URL` is baked in at build time (set in Railway Variables).
2. **Runtime** — `python:3.11-slim`; copies `backend/`, `src/`, `app/`, `memory/`, and the built frontend to `/app/frontend/build`. `PYTHONPATH=/app/backend:/app`.

### 6.2 Start command

`docker-entrypoint.sh` runs `uvicorn backend.server:app --host 0.0.0.0 --port ${PORT:-8080}`. The single service serves both the API and the built SPA (`SERVE_FRONTEND=1`), so the frontend calls `/api` same-origin — no CORS, no separate frontend deployment.

### 6.3 Railway config (`railway.toml`)

- Build: `Dockerfile`.
- Healthcheck: `/api/version` (timeout 240s), restart `ON_FAILURE` with up to 10 retries.

### 6.4 A deploy in practice

1. Push to the connected repo (Railway auto-deploys on the production branch).
2. Railway builds the Docker image (frontend build → runtime image).
3. On start, the backend runs startup health checks, seeds platform config, and (if `EXEC_FORCE_RESET=1`) resets the 3 exec seats.
4. Railway healthchecks `/api/version`; once 200, the service is live.
5. **Verify** with the Executive Site Report (`/admin/exec-report`) before announcing public readiness.

### 6.5 Environment variables (Railway Variables)

**Required:**
- `MONGODB_URI` (or `MONGO_URL`) — MongoDB connection string.
- `JWT_SECRET` — change from default for production.
- `PROVIDER_KEY_ENCRYPTION_SECRET` — Fernet secret for Keys-tab encryption.
- `PUBLIC_APP_URL` — public origin (needed for absolute links in emails).

**BYOK:** `BYOK_PRICE_USD` (default `3`).

**AI gateway (free-first):** `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `XAI_API_KEY` (or `GROK_API_KEY`), `COHERE_API_KEY`, `OPENROUTER_API_KEY`, `HUGGINGFACE_API_KEY`, `ANTHROPIC_API_KEY` (paid last resort), `HOURLY_TOKEN_CAP`.

**Email:** `RESEND_API_KEY` (preferred) or `GMAIL_USER` + `GMAIL_APP_PASSWORD`. Without these, password-reset and welcome emails are not delivered.

**Payments:** `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` + `STRIPE_PUBLISHABLE_KEY`, or `LEMON_SQUEEZY_API_KEY` + `LEMON_SQUEEZY_STORE_ID`, or `GUMROAD_API_KEY`.

**Integrations:** `ELEVENLABS_API_KEY` (legacy voice — **not required**; voice is native browser TTS), `SLACK_WEBHOOK_URL` (alerts), `SUPABASE_URL` + `SUPABASE_KEY`.

**Ops:** `APP_ENV=production`, `PORT`, `CORS_ORIGINS`, `BACKEND_URL`, `EXEC_FORCE_RESET`, `EXEC_RESET_SECRET`, `EXEC_ADMIN_EMAIL`, `BACKUP_EXEC_ADMIN_EMAIL`, `NAM_EXEC_EMAIL`.

> **Security note:** Never commit `.env` or real keys. Add/rotate secrets in the Railway Variables panel (or the Freebuff Keys UI), not in the repo.

---

## 7. BYOK — $3 Bring Your Own Key

**Route:** `/byok` (all authenticated users) · **Endpoints:** `/api/byok/*`

BYOK is the platform's $3 Bring-Your-Own-Key unlock. A user activates the one-time $3 entitlement, then attaches their own key from one of three free providers (Groq, Cerebras, Google Gemini — none require a credit card). The LLM gateway then routes that user's AI requests through **their own key first**, so the platform spends nothing for that user's generation.

| Endpoint | Auth | Purpose |
|---|---|---|
| `GET /api/byok/status` | student+ | Entitlement + configured providers (masked keys only). |
| `POST /api/byok/activate` | student+ | Enable the $3 entitlement (post-payment hook). |
| `POST /api/byok/key` | student+ | Attach/replace a key for one provider. |
| `POST /api/byok/key/{provider}/test` | student+ | 1-token connectivity test. |
| `DELETE /api/byok/key/{provider}` | student+ | Remove a key. |
| `GET /api/byok/admin` | admin+ | Adoption stats (activated profiles, active keys). |

**Payment wiring:** `/api/byok/activate` currently sets `byok_enabled=true` directly and writes an audit row. Before public launch, route this through the existing commerce layer (Stripe / Lemon Squeezy) so the $3 is collected before the flag is set. Keys are stored encrypted in `db.user_byok_keys` with `PROVIDER_KEY_ENCRYPTION_SECRET` (same Fernet scheme as §5); raw keys are never returned to the frontend. Price is configurable via `BYOK_PRICE_USD` (default `3`).

**Gateway integration:** `backend/ai/llm_gateway.py` `call_llm()` accepts an optional `user_id`; when a BYOK user's request passes `user_id`, the gateway tries the user's key (Groq → Cerebras → Gemini) before the platform key chain, then falls back to the platform chain on failure. The primary chat (`/ai/chat`) and orchestrator (`/ai/orchestrator`) endpoints already pass `user_id`; other personas can be wired by adding `user_id=user.id` at their `call_llm(...)` call sites.

---

## 8. Voice output (recent change)

As of v1.0, **all voice output uses native browser text-to-speech** (`window.speechSynthesis`) with a per-surface on/off toggle. The old per-persona paid voice system (ElevenLabs / OpenAI `/ai/sage/tts`) is **dormant** and no longer called by the UI. No voice keys are required; voice works on every device with zero cost. Voice **input** (microphone transcription) still uses the Web Speech API / backend transcription endpoints and is unchanged.

---

## 9. How to keep this manual accurate

Whenever you change the platform:

1. **Add/rename a route** → update §2.
2. **Add/remove an executive control** → update §3.
3. **Change a control's behavior, endpoint, or permission** → update the relevant §3 entry and the endpoint list.
4. **Add/remove an env var** → update §6.5.
5. **Change the deploy pipeline** → update §6.
6. **Change voice/keys/security behavior** → update §5 / §7.

Bump the **Version** and **Last updated** at the top of this file with every change.
