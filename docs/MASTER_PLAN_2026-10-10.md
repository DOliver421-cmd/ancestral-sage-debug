> **SUPERSEDED (2026-10-15):** see `docs/INTEGRATED_PLAN.md`. This file is retained as history;
> its findings are consolidated there and its disproved claims are corrected.

# MASTER PLAN — MoreHelp Center, 2026-10-10 — SUPERSEDED

> **Content integrated into `docs/WORKING_PLAN.md`.** Work from the working plan; this file is history.


**Supersedes the track-scoped sequencing.** This is the single delivery plan. The API Key Gateway
(`docs/API_KEY_GATEWAY_PLAN.md`) and the audit-derived queue (`docs/PLAN_FROM_RUNTIME_AUDIT_2026-10-10.md`)
are now **annexes** — engineering detail for Tracks B and A below. Nothing from the continuation plan is dropped;
§4 maps every continuation item to its place here.

---

## 0. The core goal (fixed, not re-litigated)

MoreHelp Center is a **commercial platform**. Revenue is the only engine that creates independence and satisfies
the institutional compliance parameters. The product strategy (continuation plan §8, owner-stated):

- **Tier 1 — the free Academy** buys trust and volume. It is the funnel. It must never lose a family's work and
  never lie about state.
- **Tier 2 — Creator & Builder** monetizes the individual: creator studio, course authoring, payouts,
  storefront, BYOK ($3 unlock).
- **Tier 3 — Enterprise & Resource Hub** monetizes the institution: the 16 `/api/hub/*` routes, the Legal
  Workflow Engine, grants, campaigns, and the future scholarship/co-op surfaces.
- **The substrate under all three tiers is the AI provider gateway** (Track B): the no-cost platform pool that
  keeps Tier 1 free, the BYOK line that monetizes Tier 2, and the policy-governed routing that protects margin.
  It is not a side feature; every tier's AI capability runs through it.
- The tiers coexist **only if** `FEATURE_API_PATHS` + `TIER_FOR_FEATURE` are truthful (continuation P1 — still
  the highest-leverage change, now executed-verified in Track A).
- Delivery: live on `main` through owner-reviewed PRs, executed verification, zero mock, human controls
  live-wired. Nothing counts as done until the owner-visible path runs.

---

## 1. Verified current state (executed 2026-10-10 — the numbers the plan starts from)

| Layer | State | Evidence |
|---|---|---|
| Tier 1 funnel | **WORKS end-to-end** | 52/52 Academy tests; guard rails 3/3; public course browse 200 anon; student create (K/adult), enrol, lesson attempt, records, compliance docs all executed |
| Tier 1 integrity | **LEAKING** | legal-engine account sync dead (F1); enrollment race loses courses 8/8 (F2); artifact race loses work 4/6 (F3); seeded guides inert (F8) |
| Tier 2 gates | **UNTRUTHFUL** | free member created a marketplace course via `POST /api/creator/courses` → 201 (F5); `ai_chat` frontend member / backend free (F6) |
| Tier 3 | **DEAD WHERE IT MATTERS** | Legal Workflow Engine sync never persists (F1); hub routes handler-gated only; scholarship/co-op surfaces don't exist |
| AI substrate | **HALF-REAL** | no-cost fallback chain + KB fallback real; `model:"auto"`, `/v1/chat/completions`, live model refresh, revocation, usage accounting, and both named limits missing (gateway audit D1–D21) |
| Boot hygiene | **FAILING SILENTLY** | NAM knowledge seed 31/31 fail on any real DB (F4); `PipelineManager` dead import (F7) |

---

## 2. The three tracks

- **Track A — fix what is broken now** (`docs/PLAN_FROM_RUNTIME_AUDIT_2026-10-10.md`, items R1–R17): silent
  data loss, dead sync, ungated money surface, cold-boot failures. User-trust and monetization-integrity work.
- **Track B — the API Key Gateway** (`docs/API_KEY_GATEWAY_PLAN.md`, items G0–G7): the substrate — verified
  no-cost auto-routing, `POST /v1/chat/completions`, real revocation, usage accounting, enforced limits
  (Gemini 15 RPM, Mistral 1M/mo), encrypted specialty vault, BYOK/monetization policy.
- **Track C — the continuation queue** (`docs/CONTINUATION_PLAN.md` §4): the §4.1 in-product guides and
  P1–P7 feature depth per tier.

## 3. Sequencing — phases, each a set of owner-reviewed PRs

### Phase 0 — Stop the bleeding (trust + cold boot)
**Why first:** these defects silently lose family work, fail on every fresh deploy, or break a live exec
control. Everything else is built on top of them.

| Item | Track | What |
|---|---|---|
| R1 | A | Legal Workflow Engine account sync — real contract both sides (bare-list read, JSON POST, surfaced failure) |
| R2 | A | Enrollment atomicity (`$addToSet`/`$pull`) — race loop must go 8/8 → 0/8 |
| R3 | A | Artifact saves atomic per step — race loop must go 4/6 → 0/6 |
| R4 | A | NAM knowledge seed — `if _db is not None`; cold boot must log 31 seeded |
| R5→needs R1 | A+C | §4.1 in-product guides (8 steps each, `in_product`, workflow checklist via the **fixed** hub endpoints) |
| G1 | B | Real revocation — call-time credential resolution + eviction (fixes the silent `MoreHelpCenter` toggle too) |
| G0 | B | Anthropic references removed (policy), missing indexes, `api_keys` split, nav defect, Refresh button |
| R9, R10 | A | `PipelineManager` dead import; startup seed failures logged with reasons |

### Phase 1 — Truthful gates (monetization integrity)
**Why second:** nothing may be sold or promised against a gate that lies. This is continuation P1, executed.

| Item | Track | What |
|---|---|---|
| R6 | A | Creator money surface into `FEATURE_API_PATHS` — free member must get 403 on create |
| R7 | A | Align `ai_chat` / `courses` / `resource_hub` between `lib/tiers.js` and `feature_control.py` |
| R8 | A | Production stops masking API 404/405 with SPA HTML **— owner decision (§5.7), deployment behavior** |

### Phase 2 — The substrate (Track B)
**Why third:** Tier 2 pricing, BYOK monetization, and Tier 3 AI features all run on this. Sequence G2→G3→G4→G5→G6→G7 per the gateway annex; policy defaults per the owner's spec (credit/aggregator/monetization/BYOK **excluded** from auto-routing unless authorized).

### Phase 3 — Tier 1 depth (funnel)
R13 project review comments + artifacts in printed Records; R14 K–8 cultural deepening (~35 courses);
R17 weekly parent report + Afro-Latin/Portuguese strands. Academy stays free for every registered member.

### Phase 4 — Tier 2 monetization
R11 digital-product commerce depth (additive over `/media/products/*`); P2 Creator Studio price + Tier-2
marquee **(owner decision §5.2)**; only after Phases 1–2 so the surface is gated truthfully and its AI cost is
real.

### Phase 5 — Tier 3 monetization
R12 PEP / FES-UA scholarship workflows (new UI + content over `scholarship_funds`); Legal Workflow Engine tier
decision **(owner decision §5.4)** — now priceable because R1 made it real; R15 co-op / multi-seat
**(blocked on owner schema decision §5.3)**.

## 4. Continuation-plan coverage check (nothing dropped)

| Continuation item | Where it lives |
|---|---|
| §4.1 two in-product guides | **R5**, Phase 0 (after R1) |
| §4.2 P1 tier gates truthful | **R6 + R7**, Phase 1 |
| §4.2 P2 Creator Studio price | Phase 4, owner decision §5.2 |
| §4.2 P3 digital-product commerce depth | **R11**, Phase 4 |
| §4.2 P4 PEP / FES-UA scholarship workflows | **R12**, Phase 5 |
| §4.2 P5 co-op & multi-seat | **R15**, Phase 5, blocked on §5.3 |
| §4.2 P6 K–8 cultural deepening | **R14**, Phase 3 |
| §4.2 P7 project review comments + artifacts in Records | **R13**, Phase 3 |
| §6 "routers not loaded on deploy" warning | **Disproved by execution** — prod serves identical router JSON; the SPA catch-all warning stands as R8 |
| §7 open questions | Consolidated in §5 below |

## 5. Owner decisions (each blocks a named item — ask once, decisively)

1. **Resource Hub tier** — Plus (UI) or Member (handler)? Blocks R7. *(still open from continuation §7.3)*
2. **Creator Studio price** — free (current) or Plus? Blocks Phase 4 marquee. *(§7.1)*
3. **Co-op / multi-seat schema** — permitted new field/collection? Blocks R15. *(§7.2)*
4. **Legal Workflow Engine tier** — stay Plus, or part of the free Academy? Blocks Phase 5 pricing. *(§7.4)*
5. **K–8 deepening depth** — same 2-lessons-per-course pattern as #474, or more? Scopes R14. *(§7.5)*
6. **Gateway routing policy defaults** — confirm credit/aggregator/monetization/BYOK stay **excluded** from
   `model:"auto"` unless a policy flag authorizes them (spec as written; default off). Blocks G3/B4.
7. **Production SPA catch-all** — may `/api/*` 404/405 return JSON instead of index.html? Blocks R8.

## 6. Dependency map (why the order is the order)

```
R1 ──► R5 (guides' checklist persists through the fixed hub endpoints)
G1 ──► R6/G3 (gates and auto-routing need credentials that can actually be revoked)
R6,R7 ──► Phase 4 (nothing sold against a lying gate)
G2 ──► G3 ──► G4 ──► G6 (registry → auto-routing → accounting → UI)
R1 ──► Phase 5 (the Legal Engine becomes priceable only once its sync is real)
§5.3 ──► R15 (co-op cannot start without the schema decision)
```

## 7. Verification and delivery standard (every PR, every track)

- **Executed DoD**: each item's definition-of-done is a run with real output pasted into the PR body. Race
  items re-run their concurrency loop; gate items re-run the free/member/plus probes; gateway items follow the
  annex's §7 walkthrough.
- **Guard rails**: `frontend/scripts/{academy-open-access,route-integrity,nav-integrity}.js` + Academy suite
  (52 tests) + `craco build`.
- **Live check**: read-only probes against the production target; GET bodies verified as JSON (R8); no
  accounts, no writes.
- **Report format**: asked vs delivered with PR numbers; what is NOT delivered listed separately; verified-by-
  execution vs verified-by-reading vs unverified, labelled; own bugs reported as findings.
- **Ledger**: every new defect is appended to `docs/HOMESCHOOL_ACADEMY_ISSUES.md` (never history-edited).
- **Delivery**: one task per PR on `main`; never push straight to `main`; never force-push.

## 8. What done means for the whole plan (the end state, in owner-visible terms)

1. **Tier 1**: the free Academy works end-to-end with zero silent data loss — no lost enrollments, no lost
   artifacts, the Legal Engine's state actually syncs to the account, the seeded guides are real 8-step
   workflows, and a cold deploy boots clean (NAM corpus seeded, no dead imports).
2. **Tier 2**: every creator/payout/BYOK surface is gated exactly as the tier table says, priced per the
   owner's decision, and its AI cost is real and capped.
3. **Tier 3**: the Resource Hub and Legal Workflow Engine are real, synced, and priced; scholarship and co-op
   surfaces exist or are explicitly deferred by owner decision.
4. **Substrate**: the gateway runs verified no-cost providers for `model:"auto"` with provider-aware failover,
   enforces Gemini 15 RPM and Mistral 1M tokens/month, revokes keys instantly, logs every attempt with its
   fallback chain, keeps every credential encrypted and masked, and gives the owner live control of ranking,
   limits, budgets, and routing policy through the interface.
5. **Revenue**: each monetization path — BYOK unlock, creator commerce, Tier 3 institutional access — is
   executable end-to-end by a real customer, proven by execution, not by build success.
