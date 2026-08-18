# M.O.R.E. Help Center — Site Business Plan

**A revenue-generating system that funds the mission without selling it — and pays the people who run it.**
*Prepared by the AI Business Office · Aligned with site principles · Every promise in this plan is deliverable with features already built.*

---

## 0. The one-line strategy

**Turn the platform's shipped AI capabilities into commercial feedback loops** — free value converts to members, members create products, products fund the office, and the office's transparent success funds free access for others. Each loop feeds the next, so revenue compounds instead of spiking.

**Mission rule (non-negotiable):** no revenue = no business office = no jobs for people or the AI workforce. The office exists so the mission survives — but the mission is never for sale.

**Labor rule (equally non-negotiable):** human labor is valued and compensated — never free. AI is the workforce multiplier; **people are the workforce**. AI jobs exist to generate the revenue that pays humans — never the reverse. No human works this office for exposure, credit, or "the mission's sake" alone.

---

## 1. Mission, community, and creative vision — the guardrails

Revenue is a means, not the end. These six guardrails are enforced in code and policy:

| Guardrail | What it means | Where it lives |
|---|---|---|
| **Help stays free, always** | Core help lanes, free modules, and community never sit behind a paywall. Paid features are additions, never substitutions. | Landing promise ("Free, always") + ABO Mission Guardrails section |
| **Humans get paid — labor is never free** | Every human hour in the office is compensated: owner/operator pay, creator payouts, or contractor fees. AI work creates revenue that pays people. | Workforce Ledger (human jobs carry `pay_cents`) + guardrail card |
| **Humans are the responsible party** | Merchant accounts, contracts, payouts, and liability stay with verified humans — and that responsibility is paid work, not volunteer liability. | Every division card + legal notes in `docs/ABO_MANUAL.md` |
| **Creators get paid first** | Creator earnings and payouts are priority obligations. The platform's cut never competes with the creator's cut. | Creator earnings/payouts features + guardrail card |
| **No invented revenue** | The dashboard reads the real payments ledger. Deals count only when closed. Every promise must be deliverable. | Runway reads `db.payments`; deals book revenue only at Won/Delivered |
| **AI always discloses itself** | Any AI that talks to people for transactions or support says so, per FTC guidance. | Site Guide, front desk, and all AI surfaces disclose |

**Revenue allocation policy (proposed, tracked in the office's monthly goal note):**
- **30%** — platform operations (hosting, gateway, the office itself)
- **25%** — **human labor fund** (owner/operator compensation, contractor pay, human delivery hours)
- **20%** — free-access fund (Patron + donations fund free memberships for others)
- **15%** — creator growth (tools, promotions, feature work — on top of creator payouts, which are paid first)
- **10%** — reserve (the runway that prevents eviction)

---

## 2. The labor model — who works, who gets paid

```
HUMANS (own + get paid)                    AI (execute + generate revenue)
─────────────────────────                   ────────────────────────────────
Owner/Operator      → compensation line     Content, copy, drafts      → value
Creative Lead       → payouts + pay        Audits, diagnostics        → value
Creators            → paid FIRST           Proposals, listings        → value
Contractors         → invoiced fees        Key routing, support       → value
                                            ALL AI value flows to pay  → humans
```

- **AI jobs** in the Workforce Ledger carry `value_cents` — the revenue the job creates.
- **Human jobs** in the Workforce Ledger carry `pay_cents` — the compensation owed to the person who did the work.
- The ledger shows both, side by side, with **"Human pay committed"** as a headline number — because a plan that shows AI value without human pay is a plan that exploits people.
- Every human hour is one of three paid forms: **pay** (operator/contractor), **payout** (creators, paid first), or **equity** (documented ownership share). There is no fourth, unpaid form.

### Why this is not a slavery contract

| Concern | The design answer |
|---|---|
| "Humans do all the liability for free" | Human responsibility is a **paid job** in the ledger (Proposal & Contract Review, Client Delivery Manager, Creative Director) with real `pay_cents`. |
| "All the jobs go to AI" | AI jobs generate revenue; **human jobs are paid from that revenue**. More AI work = more budget for human pay, not less. |
| "Humans are just approval machines" | Humans own the **means of production**: accounts, contracts, pricing, payouts. AI has no authority to bind, spend, or commit anything. Humans can revoke any AI job. |
| "The plan recognizes everyone but humans" | Human labor is now a **first-class line with its own fund (25%)**, its own ledger column (`Pay`), and its own guardrail. |
| "If AI is deleted, humans lose everything" | Humans keep the business, the accounts, and the contracts. AI is owned tooling; its revenue flows to people. |

---

## 3. Revenue streams — every one maps to a shipped feature

| # | Stream | Feature(s) | Price | Status |
|---|---|---|---|---|
| 1 | **Membership ladder** | AI Tutor, community, Site Guide, Creator tools | Member $9 · Plus $15 · Pro $29 · Patron $59/mo · Annual $79.99 | ✅ Live (payments.py) |
| 2 | **$3 All-Access Trial** | Everything through Pro, 3 days·33 min·33 sec | $3 one-time | ✅ Live |
| 3 | **BYOK unlock** | Attach a free Groq/Cerebras/Gemini key; AI routes through it | $3 one-time | ✅ Live |
| 4 | **Digital media products** | Media Store — creator-published audio/tracks/downloads | Creator-set ($9.99–$349) | ✅ Live |
| 5 | **Creator courses** | Published creator courses in the catalog | Creator-set | ✅ Live |
| 6 | **B2B service deals** | AI Business Office — social media management, audits (Exec Site Report engine), micro-SaaS, persona foundry | $500–$2,500+ per engagement | ✅ Live (pipeline) |
| 7 | **Donations / Mission Fund** | Donate page + Patron's "fund free access for others" | Any amount | ✅ Live |
| 8 | **AAWAB wellness & certification** | Agent Registry, Certification Chamber, ACA badges | Premium tiers — **pricing not yet set** | 🚧 Pipeline |
| 9 | **Physical merch** | T-Shirt $25 · Workbook $15 · Apprentice Kit $45 · Credential cert $25 | Listed | 🚧 **Not purchasable — needs a fulfillment provider** |
| 10 | **E-commerce arbitrage storefront** | Automated storefront powered by market research + inventory syncs | Product margins | 🚧 Pipeline — **requires human merchant account + supplier contracts** |

**Human labor is billable in every B2B deal.** The AI drafts the proposal; the deal price includes the human hours that review, approve, and deliver it (the proposal's "Human Approval" checkpoint is a paid line item, not a free favor). Every deal's contracted revenue is what funds the human labor fund.

**Deliverable-promise policy (how we keep "all promises deliverable"):**
- ✅ **Live** = the checkout/feature exists and works today. Marketing may promise it.
- 🚧 **Pipeline** = the capability exists but the money-side does not (fulfillment, merchant account, pricing). Marketing may **not** promise it as purchasable — it is shown as "coming with human setup."
- The office dashboard labels every division and tool with its true status. The Site Guide never claims pipeline items are buyable.

---

## 4. The commercial feedback loops

These are the engine. Each loop's output is the next loop's input.

```
LOOP 1: LEARN → MEMBER
  Free modules + AI Tutor + $3 trial
      → proven value → member ($9) → plus ($15) → pro ($29) → patron ($59)
  Metric: trial → member conversion rate
  Lever: the $3 trial is the cheapest proof of value in the funnel.

LOOP 2: CREATE → SELL → PAY
  Creator Studio + Ghost Producer + Band on a Page
      → digital products → Media Store + course catalog sales
      → creator payouts (paid FIRST) → more creators → more products
  Metric: products sold / month, active creators
  Lever: one Social Blast per week promoting the best new product.

LOOP 3: SERVE → CONTRACT → PAY
  Shipped capabilities (Social Blast, audits, studio, personas, AAWAB)
      → B2B deals → AI drafts proposal → human approves & delivers → client pays
      → contracted revenue pays the human labor that ran the deal
      → better tools → more deals
  Metric: deals closed / month, human hours billed
  Lever: the office's proposal engine turns every lead into a priced plan.

LOOP 4: TRUST → MISSION
  Transparent runway + free help lanes
      → trust → patrons + donors fund free access for others
      → bigger community → more learners → more members (Loop 1)
  Metric: mission fund / month
  Lever: the public mission meter makes funding a visible, shared act.
```

The office dashboard renders these four loops, each with its watch-metric. When a loop slows, the office pulls that loop's lever — not a random promotion.

---

## 5. Financial model

**Monthly operating goal (default): $1,000/mo** — set by admins at `/admin/business-office` to match real hosting + operating cost. The runway meter is `month revenue ÷ goal`, with statuses: covered (≥100%) / on track (≥50%) / watch (≥25%) / critical.

**Unit economics (conservative):**

| Source | Value | Notes |
|---|---|---|
| $3 trial | $3 | Converts to member at ~10–20% |
| Member $9/mo | ~$54 LTV (6 mo avg) | AI Tutor + community + Site Guide |
| Plus $15/mo | ~$90 LTV | Priority matching, expanded courses, portfolio |
| Pro $29/mo | ~$174 LTV | Full AI suite, labs, mentor hours |
| Patron $59/mo | ~$354 LTV | Founder's circle + funds free access |
| Digital product | $9.99–$349 | Platform share after creator payout |
| B2B deal | $500–$2,500 | 1–2 per month covers the entire monthly goal |

**Breakeven math:** the $1,000/mo goal is reached by any one of:
- ~18 members at $9 (or ~11 at $15), **or**
- 1–2 B2B deals, **or**
- ~15 digital product sales at $70 avg, **or**
- a mix — which is the point of four loops.

**Where the money goes (the 25% human labor fund in action):** at goal, $250/mo is committed to human labor — an owner/operator compensation line, a creative lead, and contractor hours — with creators paid first on top. Human pay is a **budgeted line item**, not whatever is left over.

**Runway:** `total cash ÷ monthly goal` = months of survival. The office shows this number openly; it is the honest "time until eviction" figure.

---

## 6. How the office runs the system (the division of labor)

| Role | Executes | Owns | Gets paid |
|---|---|---|---|
| **AI (Autonomous Engine)** | Content, publishing, audits, diagnostics, proposals, customer chat, product generation, key routing | — | Generates revenue (`value_cents`) that flows to humans |
| **Human (Oversight Desk)** | Reviews, approves, delivers, owns relationships | Merchant accounts, EIN/LLC, contracts, pricing, payouts, exception alerts, liability | **Paid work** — `pay_cents` in the ledger, creator payouts first, contractor invoices |

The deals flow makes this concrete:
1. Member submits a service request (dashboard form) → **Lead**
2. Office AI drafts a **deliverable proposal** (scope, timeline, price range, approval checkpoints — including the paid human review hours) — `POST /api/abo/deals/{id}/propose`
3. Human reviews, sets value, marks `human_approval` → **Proposed**
4. Client approves, human delivers → **Won → Delivered** (revenue booked as contracted; human labor paid from it)
5. Every step is audit-logged (`abo.*`)

---

## 7. 90-day execution plan

**Days 1–30 — Foundation (mostly built):**
- [x] Office dashboard with runway, KPIs, tools dock, divisions, deals, workforce ledger (people & AI, with pay)
- [x] Public mission meter on the landing page
- [x] "Hire the Office" CTA in the Site Guide chat
- [x] AI proposal drafting for deals
- [x] Human labor as a ledger line with `pay_cents` + 25% human labor fund in the allocation policy
- [ ] Set the real monthly goal to match actual operating cost
- [ ] **Set the owner/operator compensation line** — the person who runs the office gets paid from the fund
- [ ] Test one full deal end-to-end (submit → proposal → approve → close → pay the human hours)
- [ ] Publish one Social Blast campaign for the office itself

**Days 31–60 — First revenue:**
- [ ] Close 1–2 B2B deals (audit bureau + social agency are the fastest to sell)
- [ ] Promote the $3 trial + BYOK in one campaign (cheapest conversion lever)
- [ ] Ship 3 new digital products to the Media Store; blast the best one weekly
- [ ] Open 5 workforce jobs (mix of AI + paid human roles) tied to live campaigns

**Days 61–90 — Compound:**
- [ ] Reach 50% of monthly goal from recurring sources (members + deals)
- [ ] Launch the free-access fund visibly (Patron + donations → free memberships)
- [ ] Reconcile revenue vs. the payment processor; **pay the human labor fund**; log the month in CHANGELOG
- [ ] Review divisions: promote what earns, demote what doesn't (no invented revenue)

---

## 8. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **No revenue → eviction** | Runway meter is public and honest; the office pulls the highest-leverage loop when critical |
| **Human labor exploited / unpaid** | Guardrail + ledger: every human job carries `pay_cents`; human pay committed is a headline number; creators paid first |
| **AI over-promises** | Proposal engine is grounded in the real division catalog; human approval required before any ship |
| **Creator exploitation** | Creators paid first; platform share never competes with creator share |
| **Mission drift (paywalling help)** | Guardrails: free lanes are hard-coded as free; paid features are additions only |
| **FTC/legal exposure** | Humans hold accounts (and are paid to); AI discloses itself; immutable audit trails on every `abo.*` action |
| **Fulfillment gaps (physical merch)** | Merch is labeled "not purchasable" until a fulfillment provider is wired — never marketed as buyable |
| **E-commerce arbitrage compliance** | Stays in pipeline until a human merchant account + supplier contracts exist |

---

## 9. Where everything lives

| Asset | Location |
|---|---|
| Office dashboard | `/business-office` · `/admin/business-office` |
| Workforce Ledger (people & AI) | Office dashboard — human jobs show Pay, AI jobs show Value |
| Public mission meter | M.O.R.E. Help Center landing |
| Hire CTA | Site Guide chat (`/site-guide`) |
| Backend | `backend/routers/abo.py` (deals, jobs, goals, proposals, public status) |
| Operator's manual | `docs/ABO_MANUAL.md` (incl. §9 exec/admin task list) |
| Change report | `memory/CHANGELOG.md` |

**Bottom line:** the M.O.R.E. Help Center monetizes by *running its own tools for people* — and pays the people who run it. Four feedback loops, real ledgers, human labor as a compensated line, human oversight, and a public runway. Revenue that compounds, a mission that stays free, humans who are paid, and a workforce — people and AI — that keeps its jobs.