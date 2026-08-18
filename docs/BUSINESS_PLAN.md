# M.O.R.E. Help Center — Site Business Plan

**A revenue-generating system that funds the mission without selling it.**
*Prepared by the AI Business Office · Aligned with site principles · Every promise in this plan is deliverable with features already built.*

---

## 0. The one-line strategy

**Turn the platform's shipped AI capabilities into commercial feedback loops** — free value converts to members, members create products, products fund the office, and the office's transparent success funds free access for others. Each loop feeds the next, so revenue compounds instead of spiking.

**Mission rule (non-negotiable):** no revenue = no business office = no jobs for the AI workforce = the platform gets evicted. The office exists so the mission survives — but the mission is never for sale.

---

## 1. Mission, community, and creative vision — the guardrails

Revenue is a means, not the end. These five guardrails are enforced in code and policy:

| Guardrail | What it means | Where it lives |
|---|---|---|
| **Help stays free, always** | Core help lanes, free modules, and community never sit behind a paywall. Paid features are additions, never substitutions. | Landing promise ("Free, always") + ABO Mission Guardrails section |
| **Humans are the responsible party** | Merchant accounts, contracts, payouts, and liability stay with verified humans. AI executes; people approve. | Every division card in the office + legal notes in `docs/ABO_MANUAL.md` |
| **Creators get paid first** | Creator earnings and payouts are priority obligations. The platform's cut never competes with the creator's cut. | Creator earnings/payouts features + guardrail card |
| **No invented revenue** | The dashboard reads the real payments ledger. Deals count only when closed. Every promise must be deliverable. | Runway reads `db.payments`; deals book revenue only at Won/Delivered |
| **AI always discloses itself** | Any AI that talks to people for transactions or support says so, per FTC guidance. | Site Guide, front desk, and all AI surfaces disclose |

**Revenue allocation policy (proposed, tracked in the office's monthly goal note):**
- **50%** — platform operations (hosting, gateway, the office itself)
- **25%** — free-access fund (Patron + donations fund free memberships for others)
- **15%** — creator growth (tools, promotions, feature work)
- **10%** — reserve (the runway that prevents eviction)

---

## 2. Revenue streams — every one maps to a shipped feature

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

**Deliverable-promise policy (how we keep "all promises deliverable"):**
- ✅ **Live** = the checkout/feature exists and works today. Marketing may promise it.
- 🚧 **Pipeline** = the capability exists but the money-side does not (fulfillment, merchant account, pricing). Marketing may **not** promise it as purchasable — it is shown as "coming with human setup."
- The office dashboard labels every division and tool with its true status. The Site Guide never claims pipeline items are buyable.

---

## 3. The commercial feedback loops

These are the engine. Each loop's output is the next loop's input.

```
LOOP 1: LEARN → MEMBER
  Free modules + AI Tutor + $3 trial
      → proven value → member ($9) → plus ($15) → pro ($29) → patron ($59)
  Metric: trial → member conversion rate
  Lever: the $3 trial is the cheapest proof of value in the funnel.

LOOP 2: CREATE → SELL
  Creator Studio + Ghost Producer + Band on a Page
      → digital products → Media Store + course catalog sales
      → creator payouts (paid first) → more creators → more products
  Metric: products sold / month, active creators
  Lever: one Social Blast per week promoting the best new product.

LOOP 3: SERVE → CONTRACT
  Shipped capabilities (Social Blast, audits, studio, personas, AAWAB)
      → B2B deals → AI drafts proposal → human approves → client pays
      → contracted revenue → funds AI ops → better tools → more deals
  Metric: deals closed / month, contracted revenue
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

## 4. Financial model

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

**Runway:** `total cash ÷ monthly goal` = months of survival. The office shows this number openly; it is the honest "time until eviction" figure.

---

## 5. How the office runs the system (the division of labor)

| Role | Executes | Owns |
|---|---|---|
| **AI (Autonomous Engine)** | Content, publishing, audits, diagnostics, proposals, customer chat, product generation, key routing | — |
| **Human (Oversight Desk)** | — | Merchant accounts, EIN/LLC, contracts, pricing, payouts, exception alerts, liability |

The deals flow makes this concrete:
1. Member submits a service request (dashboard form) → **Lead**
2. Office AI drafts a **deliverable proposal** (scope, timeline, price range, approval checkpoints) — `POST /api/abo/deals/{id}/propose`
3. Human reviews, sets value, marks `human_approval` → **Proposed**
4. Client approves, work ships → **Won → Delivered** (revenue booked as contracted)
5. Every step is audit-logged (`abo.*`)

---

## 6. 90-day execution plan

**Days 1–30 — Foundation (already built):**
- [x] Office dashboard with runway, KPIs, tools dock, divisions, deals, jobs
- [x] Public mission meter on the landing page
- [x] "Hire the Office" CTA in the Site Guide chat
- [x] AI proposal drafting for deals
- [ ] Set the real monthly goal to match actual operating cost
- [ ] Test one full deal end-to-end (submit → proposal → approve → close)
- [ ] Publish one Social Blast campaign for the office itself

**Days 31–60 — First revenue:**
- [ ] Close 1–2 B2B deals (audit bureau + social agency are the fastest to sell)
- [ ] Promote the $3 trial + BYOK in one campaign (cheapest conversion lever)
- [ ] Ship 3 new digital products to the Media Store; blast the best one weekly
- [ ] Open 5 AI workforce jobs in the ledger tied to live campaigns

**Days 61–90 — Compound:**
- [ ] Reach 50% of monthly goal from recurring sources (members + deals)
- [ ] Launch the free-access fund visibly (Patron + donations → free memberships)
- [ ] Reconcile revenue vs. the payment processor; log the month in CHANGELOG
- [ ] Review divisions: promote what earns, demote what doesn't (no invented revenue)

---

## 7. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **No revenue → eviction** | Runway meter is public and honest; the office pulls the highest-leverage loop when critical |
| **AI over-promises** | Proposal engine is grounded in the real division catalog; human approval required before any ship |
| **Creator exploitation** | Creators paid first; platform share never competes with creator share |
| **Mission drift (paywalling help)** | Guardrails: free lanes are hard-coded as free; paid features are additions only |
| **FTC/legal exposure** | Humans hold accounts; AI discloses itself; immutable audit trails on every `abo.*` action |
| **Fulfillment gaps (physical merch)** | Merch is labeled "not purchasable" until a fulfillment provider is wired — never marketed as buyable |
| **E-commerce arbitrage compliance** | Stays in pipeline until a human merchant account + supplier contracts exist |

---

## 8. Where everything lives

| Asset | Location |
|---|---|
| Office dashboard | `/business-office` · `/admin/business-office` |
| Public mission meter | M.O.R.E. Help Center landing |
| Hire CTA | Site Guide chat (`/site-guide`) |
| Backend | `backend/routers/abo.py` (deals, jobs, goals, proposals, public status) |
| Operator's manual | `docs/ABO_MANUAL.md` (incl. §9 exec/admin task list) |
| Change report | `memory/CHANGELOG.md` |

**Bottom line:** the M.O.R.E. Help Center monetizes by *running its own tools for people*, not by selling its soul. Four feedback loops, real ledgers, human oversight, and a public runway — revenue that compounds, a mission that stays free, and a workforce that keeps its jobs.