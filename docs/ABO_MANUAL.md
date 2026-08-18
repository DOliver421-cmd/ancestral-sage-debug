# AI Business Office (ABO) — Operator's Manual

**Mission rule: no revenue = no business office = no jobs for people or the AI workforce = the platform gets evicted. The office exists to keep the mission funded.**

**Labor rule: human labor is valued and compensated — never free.** AI jobs create revenue (`value_cents`); human jobs are paid from it (`pay_cents`). Humans own the accounts, contracts, and liability — and are paid for that responsibility. AI work exists to pay people, never the reverse.

The AI Business Office is the revenue engine command center for M.O.R.E. Help Center. It does not invent new tools — it takes the capabilities the platform **already ships** (Social Blast, Creator Studio, Ghost Producer, BYOK, AAWAB, the Exec Site Report engine, the store, the membership ladder) and runs them as revenue lines, with the AI executing the work and a human always holding the responsibility.

---

## 1. Where it lives

| Area | Route | Access |
|---|---|---|
| AI Business Office dashboard | `/business-office` | Any signed-in user |
| Office Admin desk | `/admin/business-office` | Admin+ |
| Tools + divisions catalog | `GET /api/abo/tools` | Public |
| Revenue snapshot + runway | `GET /api/abo/overview` | Auth |
| Service deals | `GET/POST /api/abo/deals` · `PATCH /api/abo/deals/{id}` | Auth / admin |
| Workforce ledger (people & AI) | `GET /api/abo/jobs` · `POST /api/abo/jobs` · `PATCH /api/abo/jobs/{id}` | Auth / admin |
| Monthly goal | `GET/POST /api/abo/goals` | Auth / admin |
| Full office view | `GET /api/abo/admin/overview` | Admin |

All endpoints live in `backend/routers/abo.py` (mounted under `/api`), registered in `server.py` via the standard `bind(db, current_user, audit, check_rate)` pattern. Every write is audit-logged (`abo.*`).

---

## 2. Data model (MongoDB)

| Collection | Purpose |
|---|---|
| `abo_goals` | Singleton office doc: `monthly_goal_cents` (+ optional `note`). Default goal: **$1,000/mo** until an admin changes it. |
| `abo_deals` | B2B service pipeline. Fields: `id`, `user_id/user_name/user_email`, `service_key/service_name`, `org_name`, `description`, `budget_cents`, `value_cents`, `stage` (`lead → proposed → won → delivered` or `closed_lost`), `status` (`open` / `closed` / `closed_lost`), `human_approval` (bool), `notes[]` (audited), timestamps. |
| `abo_jobs` | AI workforce ledger. Fields: `id`, `title`, `persona`, `division`, `description`, `hours`, `value_cents`, `status` (`open` / `assigned` / `completed`), timestamps. Seeded with 5 starter jobs on first access so the board is never empty. |

Revenue numbers come from the **real** `payments` collection (the Lemon Squeezy / Gumroad webhook ledger) — the office never fakes the money. `paying_members` comes from `users.feature_tier`.

---

## 3. The divisions of labor — who does what

Every division follows the same legal skeleton:

- **AI (Autonomous Engine)** executes: drafts, publishes, audits, diagnoses, produces, answers customer chat.
- **Human (Oversight Desk)** owns: merchant accounts, EIN/LLC filings, supplier & client contracts, exception alerts, payout authorization, liability.

| Division | Status | AI does | Human oversees | Revenue |
|---|---|---|---|---|
| M.O.R.E. Membership Ladder | live | Front desk, AI Tutor, Site Guide, support | Payment processor account, pricing, refunds | $9–$59/mo subs + $3 trial |
| Digital Products & Creator Marketplace | live | Course outlines, product copy, audio, buyer chat | Listing approval, pricing, creator payouts | Product sales + platform share |
| Social Media Management Co. | live | Writes copy, designs posts, schedules blasts | Approves before publish, holds accounts, signs contracts | Agency retainers (deals) |
| Custom Micro-SaaS & Utility Tools | live | Writes code, runs tests, answers tickets | Product vision, deploys, merchant account | Tool subs / one-time builds (deals) |
| AI-Key Brokerage & BYOK Optimization | live | Tests keys, routes traffic, tracks usage | Gateway policy, platform keys | $3 BYOK + optimization service |
| Compliance & Regulatory Audit Bureau | live | Runs multi-category audits | Signs reports, invoices clients | Per-audit fees (deals) |
| AI Persona & Workforce Foundry | live | Builds/hosts personas, tracks learners | Approves briefs, signs contracts | Build fees + retainers (deals) |
| AAWAB — Agent Wellness & Certification | live | Diagnostics, treatments, certification | Registry oversight, badge revocation | Wellness subs + cert fees |
| Autonomous E-Commerce Arbitrage & Fulfillment | **pipeline** | Supplier API monitoring, trend analysis, listings, buyer chat | **Merchant account + supplier contracts required first** | Product margins (not yet transacting) |

**E-commerce arbitrage stays in "pipeline" until a human holds a real merchant account and signs supplier contracts.** The office will not transact through an unverified identity — that is the compliance rule, not a limitation.

---

## 4. The tools dock — what AI can actually run

The dashboard's Tools section is the heart of the office: every card is a **real, shipped capability** with its revenue role spelled out.

| Tool | Route | What AI does | Revenue role |
|---|---|---|---|
| Social Blast | `/social/publish` | Writes/schedules/publishes campaigns | Agency retainers |
| Creator Studio | `/studio` | Builds sellable digital products | Product sales |
| Ghost Producer | `/ghost-producer` | Music production | Media store sales |
| BYOK Brokerage | `/byok` | Key testing + smart routing | $3 unlocks + service |
| AAWAB Bureau | `/aawab` | Vitals, treatments, certification | Wellness subs |
| Exec Site Report | `/admin/exec-report` | Deep automated audits | Per-audit B2B fees |
| Media Store | `/store` | Digital product listings | Direct sales |
| Membership Ladder | `/plans` | Front desk + conversion | Recurring subs |
| Mission Fund | `/donate` | Runway tracking | Direct support |
| Site Guide | `/site-guide` | Visitor → member conversion | Conversion for every lane |

---

## 5. The deals pipeline (B2B revenue)

1. **A member submits a request** (dashboard form): picks a division, names their organization, describes scope, optional budget. → `POST /api/abo/deals` creates a **Lead**.
2. **The office AI drafts the proposal** — `POST /api/abo/deals/{id}/propose` (admin) grounds the draft in the deal description + division catalog via `call_llm` (BYOK admins route through their own key). If the gateway is down, a deterministic template proposal is used — the office always delivers a proposal, never a dead end. The proposal includes the **paid human hours** (review, approval, delivery) as a line item — human labor is billable in every deal. The result is stored on the deal (`proposal`, `proposal_provider`, `proposal_drafted_at`) and audited (`abo.deal.proposal_drafted`).
3. **Human review** — admin sets `value_cents` and moves the deal to **Proposed**.
4. **Human approval** — the deal is only executable with `human_approval: true` (the AI never signs contracts). The human who approves is identified in the audit log.
5. **Won → Delivered** — work ships; the deal's `value_cents` books as **contracted revenue** (shown per-division and as a KPI; the runway itself only counts cash actually received).
6. **Closed lost** — logged for learning, never deleted (audit trail).

Every stage change is audited (`abo.deal.updated`) with the deal id, stage, and value.

---

## 5b. Commercial feedback loops & mission guardrails

The office runs four feedback loops — each loop's output feeds the next, which is what makes revenue consistent instead of one-off:

1. **Learn → Member** — free modules + AI Tutor + $3 trial → members ($9–$59/mo). Watch: trial→member rate.
2. **Create → Sell** — Creator Studio / Ghost Producer / Band → Media Store + course sales → creator payouts → more creators. Watch: products sold/mo.
3. **Serve → Contract** — shipped capabilities → B2B deals → AI proposal → human approval → contracted revenue → funds AI ops. Watch: deals closed/mo.
4. **Trust → Mission** — transparent runway + free help lanes → patrons/donors fund free access → bigger community → more members. Watch: mission fund/mo.

**Guardrails (what revenue can never buy):** help stays free always · **humans get paid — labor is never free** (every human job carries `pay_cents`; creators paid first) · humans are the responsible party (paid responsibility, not volunteer liability) · no invented revenue (ledger-only) · AI always discloses itself. The dashboard renders both loops and guardrails under those names.

The full strategy, unit economics, and 90-day plan live in **`docs/BUSINESS_PLAN.md`** — every revenue stream there maps to a shipped feature, and anything not yet purchasable (physical merch, AAWAB pricing, e-commerce arbitrage) is explicitly labeled pipeline.

## 6. The workforce ledger — paid people & AI

The workforce board answers "who does what, for how much — and who gets paid." Every job has a `worker_type`:

- **AI jobs** (`worker_type: "ai"`) carry `value_cents` — the revenue the job creates. Pay is 0.
- **Human jobs** (`worker_type: "human"`) carry `pay_cents` — the compensation owed to the person. Value is 0; their labor is funded by AI-generated revenue.

Jobs are seeded on first access: 5 AI jobs (Campaign Copywriter → The Oracle, Course Architect → Product Designer, Audit Analyst → Confidentiality Sentinel, Front Desk Agent → Ambassador, Wellness Technician → Architect) **plus 3 paid human jobs** (Proposal & Contract Review — Owner/Operator $180, Creative Director — Listing Approvals $160, Client Delivery Manager $250) so the ledger demonstrates the labor model from day one.

Admins open new jobs with `POST /api/abo/jobs` (specify `worker_type`, `value_cents` for AI, `pay_cents` for humans) and update with `PATCH /api/abo/jobs/{id}`. The board shows **human pay committed** and **AI work value** side by side — a plan that shows AI value without human pay is a plan that exploits people.

---

## 7. Mission runway

`GET /api/abo/overview` returns:

```json
{
  "runway": {
    "monthly_goal_cents": 100000,
    "month_revenue_cents": 42000,
    "month_pct": 42.0,
    "status": "watch",            // covered | on_track | watch | critical
    "total_revenue_cents": 210000,
    "runway_months": 2.1
  },
  "revenue": { "total_revenue_cents": ..., "month_revenue_cents": ..., "order_count": ..., "paying_members": ..., "recurring_estimate_cents": ..., "by_product": {...}, "recent_orders": [...] },
  "divisions": [ ... ],
  "counts": { "deals": ..., "jobs": ... }
}
```

Status thresholds: `≥100%` covered · `≥50%` on_track · `≥25%` watch · below critical. `runway_months` = total cash ÷ monthly goal — the honest "how long until eviction" number.

---

## 8. Legal & compliance notes (read before selling)

1. **The human is the responsible party.** Bank accounts, LLC/Corp filings, payment processors, and tax registrations stay tied to a verified human identity and EIN/SSN. AI never holds merchant accounts.
2. **Transparent interactions.** If an AI chatbot talks to consumers to complete transactions or answer support, FTC guidelines require clear disclosure that they are interacting with an automated assistant. The Site Guide and front desk disclose themselves.
3. **Immutable audit trails.** Every `abo.*` action is audit-logged with actor, action, and metadata. If an automated outreach or content tool crosses a line, the audit trail protects the entity.
4. **No invented revenue.** The dashboard reads the real payments ledger. Deals only count when they close; divisions only claim revenue they recorded.
5. **E-commerce arbitrage requires a merchant account + supplier contracts** before it leaves "pipeline" status.

---

## 9. Executive & Admin task list

### Launch checklist (once, after deploy)
- [ ] Open `/admin/business-office` and set the **monthly operating goal** (default $1,000/mo — adjust to real hosting + operating cost).
- [ ] Verify the office loads for a normal member: `/business-office` shows runway, tools, divisions, empty deals, seeded jobs.
- [ ] Test the deal flow end-to-end: submit a deal as a member → **draft the AI proposal** (`abo.deal.proposal_drafted`) → advance it as admin → confirm the audit log (`/admin/audit`) has `abo.deal.created` and `abo.deal.updated`.
- [ ] Confirm the **public mission meter** on the landing page shows the aggregate monthly funding (no private detail).
- [ ] Confirm payments are wired: a paid order in Lemon Squeezy/Gumroad appears in "Recent orders" and moves the runway.
- [ ] Confirm the Site Guide knows the office: ask `/site-guide` "how does the site make money?" — it should answer with the office and its real tools.
- [ ] Confirm search finds it: `GET /api/search?q=business office` returns the office pages.

### Daily (5 minutes)
- [ ] Check the runway status. If `watch` or `critical`, the next lever is below.
- [ ] Review new **deals** (leads) — respond the same day; a lead older than 48h is a lost sale.
- [ ] Check the jobs board — are all jobs `assigned`/`completed`? Idle workforce = idle revenue.

### Weekly
- [ ] Advance/close deals in the pipeline; set `value_cents` and `human_approval` on anything that ships.
- [ ] Open 1–2 new jobs for the workforce tied to a live campaign (Social Blast week, new course, audit offer) — mix of AI jobs (value) and paid human jobs (pay).
- [ ] Confirm the **human labor fund** is tracked: human pay committed is visible on the ledger and funded from contracted + product revenue.
- [ ] Review top revenue sources (`admin overview`) — double down on the top two.
- [ ] Post one Social Blast campaign promoting the office itself (plans, store, deals).

### Monthly
- [ ] Reconcile the runway against the real payment processor payout.
- [ ] Review the division board: demote anything that made $0 to "pipeline" or kill it; promote what works.
- [ ] Update the monthly goal if operating costs changed.
- [ ] **Pay the human labor fund** — owner/operator compensation, contractor invoices, and creator payouts reconciled against the ledger.
- [ ] Log a CHANGELOG entry with the month's revenue and what the office ran.

### Revenue levers (when runway is critical)
1. Push the **$3 All-Access Trial** and BYOK — lowest friction, converts to members.
2. Run a **Social Blast** campaign to `/plans` and `/store`.
3. Open **deals** — the B2B pipeline is the highest-value line per hour.
4. Announce the **AAWAB** bureau and audit bureau to outside audiences (B2B services).
5. Promote the **Mission Fund** (`/donate`) — direct support keeps the lights on while the engine ramps.

---

## 10. Files

| File | Role |
|---|---|
| `backend/routers/abo.py` | All ABO endpoints + catalog data (`DIVISIONS`, `_TOOLS`, `SEED_JOBS`). |
| `frontend/src/pages/BusinessOffice.jsx` | The office dashboard (runway, KPIs, tools dock, divisions, deals, jobs, admin desk). |
| `frontend/src/App.js` | Routes `/business-office` + `/admin/business-office`. |
| `frontend/src/components/AppShell.jsx` | "Business Office" sidebar section + admin link. |
| `backend/routers/site_guide.py` | Site Guide knowledge + search index entries for the office. |
| `docs/ADMIN-MANUAL.md` | §2.14 summary. |
| `docs/BUSINESS_PLAN.md` | The full site business plan — revenue streams mapped to shipped features, the four feedback loops, guardrails, unit economics, 90-day execution, deliverable-promise policy. |
| `memory/CHANGELOG.md` | Change report. |