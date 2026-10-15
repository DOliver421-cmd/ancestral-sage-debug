# INTEGRATED PLAN — MoreHelp Center / WAI Homeschool Academy

**Single source of truth for delivery. Authored 2026-10-15 from executed evidence.**
This document is the consolidation of all 17 plan and audit documents in this repository. It preserves
every finding, corrects every claim that execution has disproved, and reduces the open work to a
sequence an agent can actually work through.

Supersedes (retained as history — do not work from them):

| Document | Status |
|---|---|
| `WORKING_PLAN.md` | superseded by this file |
| `MASTER_PLAN_2026-10-10.md` | self-declared SUPERSEDED |
| `PLAN_FROM_RUNTIME_AUDIT_2026-10-10.md` | self-declared SUPERSEDED |
| `API_KEY_GATEWAY_PLAN.md` | self-declared SUPERSEDED |
| `CONTINUATION_PLAN.md` | superseded by WORKING_PLAN, now by this file |
| `RUNTIME_AUDIT_2026-10-10.md` | findings integrated here; F1–F10 all resolved or re-stated |
| `SESSION_HANDOFF.md`, `HANDOFF_GUIDE_STEPS.md` | handoff records; standing rules integrated |
| `HOMESCHOOL_ACADEMY_ISSUES.md` | live defect ledger — keep appending, never edit out |
| `TIER_BASELINE.md`, `HYBRID_NAM_SPEC.md` | reference specs; verified against code here |
| `.kilo/plans/*.md` (4 files) | per-feature plans; status integrated here |

Method note: every "DONE" below was verified by reading the current tree. Nothing is claimed on the
strength of a document alone. Live-target probes were read-only GETs only.

---

## 1. Standing rules (violating these is the main failure mode)

Carried forward unchanged from `WORKING_PLAN.md` §1 and `CONTINUATION_PLAN.md` §6 — still binding:

1. **Check the branch before every edit:** `git rev-parse --abbrev-ref HEAD && git rev-list --count HEAD..origin/main`.
   If this checkout's branch is behind `origin/main`, or it is a `kilo/*` worktree branch, it is a stale
   trap — do not edit. Branch hygiene has already cost several wasted edits in this repo's history.
2. **AGENTS.md outranks every document here.** A claim recorded in a plan or handoff is *provenance*,
   not active approval. The owner's instruction in the current session is authoritative.
3. **Never create accounts on the live target.** Live probing is read-only GETs. Keep it light — manual
   probe traffic has tripped the login rate limiter mid-suite before and failed 44 tests for a
   state-pollution reason, not a code reason.
4. **No Anthropic anything** — not a reference, not a variable, not a dependency. See §4 item **O-** (a
   live violation was found on 2026-10-15).
5. **Smallest change that satisfies the verified requirement.** Never rewrite already-correct code
   because a stale document says to (this already nearly happened with the Resource Hub guides).
6. **"Done" means the user path executed.** A route that exists is not a feature. A page that renders
   is not a feature. Trace it or do not claim it.
7. **Dependency and infrastructure changes need the owner's approval in the active session** — including
   `pip install`, `npm install`, starting servers, and any provider/credential change.

---

## 2. Verified complete — do not redo

All of the following were re-verified against the current tree. Any document that lists them as open is
stale. Do not "fix" them.

### From the runtime audit (F1–F10) — all resolved

| ID | Defect | Fix evidence |
|---|---|---|
| F1 | Legal workflow sync dead (bare-array read + query-param POST 422) | `routers/resource_hub.py:128,383` body model; `LegalWorkflows.jsx:149,173,192` array read + visible `SyncWarning` |
| F2 | Concurrent enrolment lost writes while returning 200 | `routers/academy.py:641` `$addToSet` / `$pull` |
| F3 | Concurrent artifact save dropped/resurrected values | `routers/academy.py:1520` dot-path `$set`/`$unset` on `artifacts.<step>` |
| F4 | NAM knowledge seed failed 31/31 (truth-test on Motor objects) | `ai/hybrid_nam/persistence.py:40` `is not None` throughout; seed state + failure reasons on `/api/health` |
| F5 | PipelineManager boot failure (`No module named 'src'`) | `server.py:1666` import removed; honest 503 `Intent pipeline unavailable` |
| F6 | Resource Hub guides were inert catalogue rows behind a rejected badge | `resource_hub.py:550,568` verbatim 8-step guides; `ResourceHubPanel.jsx:429` "Workflow · N steps"; the string `Read-only guide` exists nowhere |
| F7 | Prod masked API 404/405 with SPA HTML | `server.py:11234` JSON 404 for unmatched `/api/*` |
| F8 | Tier drift on `ai_chat` / `courses` | both sides agree: `feature_control.py:237,245` == `tiers.js:41,47` |
| F9 | Prompt-guard / seed observability | `nam_knowledge_seed` exposed on `/api/health` |

### From the remediation plan — A1, A2, and two §C items

- **A1** password change did not end sessions — **FIXED** (`server.py:3102` bumps `token_version`, `:3104`
  deletes `auth_sessions`, re-issues the caller's own token). Test: `tests/test_remediation_a1_a2.py:47`.
- **A2** AI Coach parent switch was UI-only — **FIXED** (`server.py:4723`, labelled "REMEDIATION A2";
  403 when the learner has `coach_enabled is False`).
- **§C** `/digital/purchases` 404 and `/academy/kinds` 404 — **FIXED** (registered; live returns 401/200).

### From this session (PRs #504–#510, all merged 2026-10-15)

Verified on the live target after merge:
- `/api/ascension-protocols` → **200** (was 404; the Curriculum Explorer's Protocols section was permanently empty).
- `/api/digital/purchases` → **401** (registered, auth-gated; was 404).
- `/api/health` → operational, `ai_api` configured.

Also landed and verified: OurLegacy render crash (two stacked ReferenceErrors), MediaStore
"already purchased" → false *Checkout failed*, transcript mastery key, seed video hash, scholarship
grace-path reconciliation, profile edits silently dropped, session revocation self-logout, the false
"page offline" card for anonymous visitors, the 501 MB `.npm-cache` that was breaking every review's
workspace setup, and executed CI checks on every PR.

### IAM console — complete at source level

All 18 `routers/iam.py` routes registered, `IAMConsole.jsx` has all 9 tabs wired, `_ensure_human_identity`
strips `_id` (`iam.py:143`). Live browser+Mongo session not re-run.

### Hybrid NAM spec — all 12 pillars complete

`routers/nam.py` exposes GET+POST for all 12 pillars (mission, strategy, governance, challenge,
ecosystem, power, economics, risk, accountability, crisis, succession) plus `/nam/memory`;
`HybridNam.jsx` defines all 12 as tabs; feature gate and header asset present.

---

## 3. Still open — prioritised, with verified evidence

### Tier 0 — unblocked, cheap, high value. Do these first.

| # | Item | Evidence | Notes |
|---|---|---|---|
| **T0-1** | **Deduplicate `/ai/chat` and `/ai/helper`** | `server.py:4598` **and** `routers/ai.py:1104` both register `POST /api/ai/chat`; `server.py:5058` and `routers/ai.py:1728` both register `/ai/helper`. The router is included with `prefix="/api/ai"`, producing `/api/ai/ai/chat`. | Two sources of truth on the safety-critical AI surface — editing the shadow copy silently does nothing. Add a guard test asserting no duplicate path+method pair. |
| **T0-2** | **Remove the Anthropic violation** | `wai_institute/pipelines/conversational_engine.py:178` calls `client.messages.create(model="claude-haiku-4-5")` — and `client` is an **undefined name**, so this path NameErrors into `_template_response()` on every call. Reachable from `routers/exec.py:413` and `server.py:9533`. | Violates the absolute policy *and* is dead code that reports success via a template fallback. Also `ai/ai_cost_tracker.py:14` prices `claude-*`. |
| **T0-3** | **Gate the Creator money surface** | `FEATURE_API_PATHS` (`feature_control.py:67-96`) has no `/api/creator/courses`, `/payout-profile`, or `/enrollments/me`. A free member gets **201** from `POST /api/creator/courses` (`routers/creator.py:109`). | Constants only, no schema change. The plan's own stated reading is `plus`. Needs Decision 1 below — see the safe-intermediate note. |
| **T0-4** | **Resolve the `resource_hub` tier drift** | `tiers.js:67` says `plus`; `FEATURE_MIN_TIER` has **no** `resource_hub` key at all; the handler `_require_member` (`resource_hub.py:48`) enforces **member**. | One constant plus one side of truth. Needs Decision 2. |
| **T0-5** | **Regression tests for A1 and A2** | Both fixed, no named test asserts the behaviour. | A regression here re-opens a security hole. Cheap. |
| **T0-6** | **`/api/academy/enrollments` returns 404** | The `EnrollmentChange` model exists (`academy.py:151`) but no route serves that path; only `POST /academy/students/{id}/courses`. | Wire the route or drop the model. Auto-enrol means no user-visible break today. |

### Tier 1 — small, self-contained, still open

| # | Item | Evidence |
|---|---|---|
| **T1-1** | `KeyPool.evict` — rotation must not resurrect a revoked key | `ai/key_pool.py` has `acquire`/`mark_rate_limited`/`mark_failed` only. Call-time `db.api_keys` reads already make revocation live without restart. |
| **T1-2** | Start `run_monitor_loop()` | `ai/team_monitor.py:254` defines it, no caller. Auto-revoke on 401/403 is implemented inside it. |
| **T1-3** | Set `AUDIT_ENCRYPTION_KEY` in the deployment secret store | `security/access_control/gateway.py:296` still logs `OFF - AUDIT_ENCRYPTION_KEY missing`. **Owner action — needs the Railway secret store, cannot be done from code.** |
| **T1-4** | Two missing NAM routes: `GET /api/nam/status`, `GET /competition/context/{id}` | Both absent; the rest of the arena/NAM context integration exists (contextes CRUD, orchestrate, chat injection, unifier + competition linking, Active Work panel). |
| T1-5 | `verify_api_key` has zero callers; `/api/revenue/api-keys*` issues keys that authenticate nothing | `backend/api_keys.py:70`. Wire real or remove. |
| T1-6 | Missing indexes: `api_keys`, `api_providers`, `ai_usage_log.created_at`, `provider_rankings` | No `create_index` for any of them. |
| T1-7 | Provider Gateway: validate-on-save, live-model refresh, key encryption, per-row test | `provider_gateway.py:156` persists any non-empty string with no live test; refresh only toggles tabs. |
| T1-8 | Nav defect: Provider Gateway link in the `admin` section while the route requires `executive_admin` | `AppShell.jsx:216` vs `App.js:514`. |
| T1-9 | **User-account rollback / soft-delete** (`.kilo/plans/1788721677511-user-rollback-improvement.md`) | `RESTORE_CONFIG_COLLECTIONS` still config-only; `users.py:419,858` hard-delete. Accidental deletion is unrecoverable. |
| T1-10 | Link `routers/member_projects.py` and `routers/studio.py` to the arena work context | 0 matches for `work_context` in either file. |

### Tier 2 — needs an owner decision before any code

| # | Decision | Blocked items |
|---|---|---|
| **D1** | Creator money surface tier (plan reads `plus`) | T0-3 |
| **D2** | Resource Hub: Plus (UI) or Member (handler) | T0-4 |
| **D3** | Does the SPA JSON-404 change ship to production? | R8 |
| **D4** | Creator Studio price | continuation P2, nav copy |
| **D5** | Legal Workflow Engine price | WORKING_PLAN:153 |
| **D6** | Co-op / multi-seat data model (new field or collection) | continuation P5, WORKING_PLAN R15 |
| **D7** | K–8 cultural deepening scope | R14 (~35 courses) |
| **D8** | `rule_90211.mp3` — **owner supplies the file. Do not synthesize it.** | `soup-suno.html` references a missing asset |

**Safe intermediate for D1:** T0-3 can be landed at `plus` without a ruling — it is the plan's own
stated reading, it only *closes* a hole, and it never opens one. Flag it to the owner when the PR opens.

### Tier 3 — product depth, no code today

- **G3** `POST /v1/chat/completions` + ranking that actually routes. The route exists **nowhere**;
  `provider_rankings` is written by tests and read by nothing. Largest remaining revenue gap.
- **R13** project review comments + artifacts in printed Records — zero code.
- **R17** weekly parent report — zero code.
- **R11 depth** digital-product commerce (additive UI over existing `/media/products/*`).
- **R12 naming** PEP/FES labels.
- Call-time credential resolution, usage-log writer at the `call_llm` choke point, rolling-window RPM
  and monthly-token counters, the 11 specialty credentials (Exa, Pexels, Gmail, Cloudflare Workers AI,
  HF-inference absent), and the `api_keys` provider/customer split.

### Carried observation — do not work from these

- `MASTER_PLAN_2026-10-10.md`, `PLAN_FROM_RUNTIME_AUDIT_2026-10-10.md`, `API_KEY_GATEWAY_PLAN.md` are
  all self-declared SUPERSEDED.
- `CONTINUATION_PLAN.md` line 239 claims `routers/ai.py` is not loaded — **disproved by execution**.
- `CONTINUATION_PLAN.md` route counts (194 / 1,008) and `WORKING_PLAN.md` (820 / 944) are both stale;
  `scripts/api_inventory.json` now records **960** routes. Regenerate rather than re-derive.
- `HANDOFF_GUIDE_STEPS.md` says the Resource Hub frontend half is "not yet written" — **it is written
  and working**; following that instruction would delete working code.
- `SESSION_HANDOFF.md` lists `/digital/purchases` and `/academy/kinds` as broken — both resolve now.
- `HOMESCHOOL_ACADEMY_ISSUES.md` rows #19–#21 and #26 are still marked Open; they are Fixed.
- The venv at `/home/netadmin/s` is wiped. The current environment recipe is `SESSION_HANDOFF.md` §4.

---

## 4. Recommended sequence

1. **T0-1, T0-2** — remove the two sources of truth on the AI surface and the policy violation.
   Both are small, both are independently testable, both block safe work elsewhere.
2. **T0-3** — close the money-surface hole at `plus`, flagging D1 in the PR.
3. **T0-4, T0-5, T0-6** — the remaining Tier 0.
4. **T1** items in listed order.
5. Take D1–D8 to the owner as one batch rather than one at a time.
6. Tier 3 once the tier gates, the AI surface, and the rollback story are sound.

Merge order for anything already open: the artifact cleanup (#510) and the CI workflow (#507) are
prerequisites for every other PR being reviewable at all.
