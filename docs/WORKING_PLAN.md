> **SUPERSEDED (2026-10-15):** see `docs/INTEGRATED_PLAN.md`. This file is retained as history;
> its findings are consolidated there and its disproved claims are corrected.

# WORKING PLAN — MoreHelp Center / WAI Homeschool Academy

**Single source of truth for delivery. Authored 2026-10-10 from executed evidence.**
Supersedes and absorbs: `PLAN_FROM_RUNTIME_AUDIT_2026-10-10.md`, `API_KEY_GATEWAY_PLAN.md`,
`MASTER_PLAN_2026-10-10.md` (all retained as history), and carries forward everything still live in
`CONTINUATION_PLAN.md` (that document stays untouched as the prior session's authority; its rules, queue, and
open questions are integrated here with its disproved claims corrected by execution).
Evidence base: `docs/RUNTIME_AUDIT_2026-10-10.md` (runtime findings F1–F10) and the gateway verification
(D1–D21) summarized in §3. Defects are appended to `docs/HOMESCHOOL_ACADEMY_ISSUES.md`, never edited out.

---

## 1. Standing rules (violating these is the main failure mode)

**Before every edit, every time:**
```bash
cd /workspace/app && git rev-parse --abbrev-ref HEAD && git rev-list --count HEAD..origin/main
```
Branch `kilo/long-turtle-bvz` or count > 0 → stale trap branch; do not edit. Re-run the check mid-session if a
file's contents surprise you. Verify with `grep` against the actual tree before claiming anything is present.

1. **"Done" means executed, not inspected.** Every claim of working needs a run: server + DB, or a rendered
   component. Source-reading proves existence, never working.
2. **No "make it honest" as a substitute for building it.** If a feature is advertised but inert, build it or
   report it as **not delivered**. No relabelling as "by design" / "read-only" / "guide only".
3. **Zero-mock / live-wiring enforcement.** A control the owner cannot alter, verify, and push from the
   interface is a hardcoded mock, not a control. No decorative UI elements. No cosmetic metadata fixes.
4. **Zero architectural change, zero DB schema change, zero role changes, zero speculative refactoring** —
   constants and additive code only. Exceptions require the owner's decision *first*.
5. **The Homeschool Academy is free to every registered member.** The rest of the site keeps its paywalls.
6. **Live delivery on `main` + PR**, owner-reviewable. Never push straight to `main`; never force-push.
7. **Verify against the live target read-only** — never create accounts or write data on production; GET bodies
   must be verified as JSON (production masks unknown `/api/*` paths with the SPA catch-all, F9).
8. **Parent is legally responsible; the platform must not imply otherwise** (F.S. §1002.41, NoI, diplomas).
9. **No Anthropic — ever** (no key, dependency, or reference; platform policy, absolute).
10. **A bug found by your own tests is a finding, not an embarrassment** — report it and fix it.

---

## 2. Verified starting state (executed 2026-10-10 — do not re-derive)

| Layer | State | Evidence |
|---|---|---|
| Tests / guard rails | 52/52 Academy suite · 3/3 guard rails · 193 routes resolve | executed |
| Tier 1 funnel | **WORKS end-to-end**: public browse 200 anon, student create (K/adult/grades), enrol, lesson attempt, records `{student,rows,summary,disclaimer}`, compliance docs, family isolation 403 | executed |
| Tier 1 integrity | **LEAKING**: legal-engine sync dead (F1); enrollment race 8/8 (F2); artifact race 4/6 (F3); seeded guides inert (F8) | executed |
| Auth | duplicate-registration race correct (1×200 + 3×409); bad token 401; profile edit persists (ledger #15) | executed |
| Tier 2 gates | **UNTRUTHFUL**: free member `POST /api/creator/courses` → **201** (F5); `ai_chat` fe-member/be-free (F6) | executed |
| Tier 3 | **DEAD WHERE IT MATTERS**: hub workflows bare-list + query-param contract (F1); hub handler-gated only; scholarship/co-op surfaces absent | executed |
| AI substrate | fallback chain + KB real; `model:"auto"`, `/v1/chat/completions` (404), live models, revocation, usage accounting, both named limits missing | executed |
| Boot | NAM knowledge seed 31/31 fail on any real DB (F4); `PipelineManager` dead import (F7); `run_monitor_loop()` never starts | executed |
| Vault | Fernet at rest real; masking real; no raw-key leakage found; **revocation has no effect until restart** (D1) | executed |
| Production | same version 4.0.1, identical router JSON (continuation's "routers not loaded" claim **disproved**); SPA catch-all masks 404/405 as 200 HTML (F9) | executed, read-only |

**Route surface (runtime-registered):** 820 paths / 944 operations. Frontend: 193 routes.
**Course catalogue:** 97 seeded, 96 published (91 curriculum + 5 handbooks), 9 tracks.
**Route correction:** guard rails live at `frontend/scripts/*.js` (continuation §5's paths were wrong).

---

## 3. Findings register (one line each; full evidence in the audit doc)

**Runtime audit (F):** F1 legal-engine account sync dead (bare-list GET + query-param POST, both swallowed) ·
F2 enrollment read-modify-write race · F3 artifact save race · F4 NAM seed fails on any real DB
(`if _db` truth-tests motor Database) · F5 creator money surface ungated · F6 tier drift (`ai_chat`,
`courses`, `resource_hub`) · F7 `PipelineManager` dead import · F8 guides inert behind the owner-rejected
badge · F9 production masks API errors with SPA HTML · F10 four continuation-plan statements disproved.

**Gateway (D):** D1 revocation not real (disable/delete leave key live until restart) · D2 multi-replica
amplification (import-time globals) · D3 `model:"auto"` ignored · D4 `/v1/chat/completions` missing ·
D5 ranking persisted but never read by the router · D6 usage log writes almost nothing and the UI reads two
fields no writer emits · D7 key save validates nothing · D8 model/tier strings disagree across four files ·
D9 9 UI cards of 15 statuses vs 27 expected · D10 Gemini 15 RPM / Mistral 1M-per-month unenforced ·
D11 token counts provider-reported only (HF 0/0) · D12 specialty keys env-only · D13 Exa / Cloudflare /
HF-image integrations have no code at all · D14 credit-grant model missing · D15 nav shows admins a link that
bounces · D16 `api_keys` schema collision · D17 legacy write-only collections · D18 missing indexes ·
D19 Anthropic remnants · D20 monitor loop dead · D21 Refresh doesn't refresh the open tab.

---

## 4. Owner decisions (ask once, decisively — each blocks named items)

| # | Decision | Blocks |
|---|---|---|
| 1 | Resource Hub tier — Plus (UI) or Member (handler)? | R7 |
| 2 | Creator Studio price — free (current) or Plus? | Phase 4 |
| 3 | Co-op / multi-seat — permitted new field/collection? | R15 |
| 4 | Legal Workflow Engine tier — stay Plus or join the free Academy? | Phase 5 pricing |
| 5 | K–8 deepening depth — same 2-lessons pattern as #474, or more? | R14 scope |
| 6 | Gateway routing policy defaults — confirm credit/aggregator/monetization/BYOK stay **excluded** from `model:"auto"` unless a policy flag authorizes (spec as written; default off) | G3 |
| 7 | May production return JSON 404/405 for `/api/*` instead of the SPA catch-all? (deployment behavior) | R8 |
| 8 | Legacy provider path — migrate into the vault or delete? | G7 |

---

## 5. THE TASK REGISTER — phases, dependencies, executed DoDs

One task per PR, branch from `origin/main` after the §1 check. Status column starts `OPEN` for everything.

### Phase 0 — Stop the bleeding (trust + cold boot)

| ID | Task | Problem | Change (minimal, root cause) | DoD (executed) | Deps |
|---|---|---|---|---|---|
| R1 | Legal Workflow Engine account sync | F1 | Backend: `WorkflowCreate` body model (`routers/resource_hub.py:369`). Frontend: read the array the API returns; surface sync failure once instead of swallowing | Plus member types → POST **201**; fresh browser with empty localStorage **restores from the account**; second family's list empty; guard rails + build clean | — |
| R2 | Enrollment atomicity | F2 | `$addToSet`/`$pull` on `course_slugs` (`routers/academy.py:614-629`), keep the `course_applies` 400 guard | 8-round × 3-writer loop: **0/8 rounds with loss**, codes 200/400 as appropriate; unenroll still works; `update_student` recompute passes; 52 tests green | — |
| R3 | Artifact save atomicity | F3 | Dot-path `$set` per `artifacts.<step>`, `$unset` on empty string, keep valid-step/length guards (`routers/academy.py:1471-1496`) | 6-round × 3-writer loop: **0/6 with loss**; #9 sequential-merge regression passes; off-pathway keys still dropped | — |
| R4 | NAM knowledge seed on real DBs | F4 | `if _db is not None` / `if col is not None` across `ai/hybrid_nam/persistence.py` | Cold boot on a fresh DB logs **31 seeded, 0 failed**; Mongo `nam_knowledge` count = 31; restart → 0 seeded / 31 skipped | — |
| R5 | In-product guides (continuation §4.1) | F8 | Backend: verbatim `docs/HANDOFF_GUIDE_STEPS.md` (`in_product` + 8 steps each, normal `seed_hub_resources` path). Frontend: delete the "Read-only guide" badge, add "Workflow · N steps" + "Open the workflow" checklist persisting through the **fixed** hub endpoints — no new endpoint, no schema change | `grep -c in_product` = 2; guides return `in_product=true` with 8 steps; render shows the workflow badge/button and **no** "Read-only guide" string; a checked box persists across re-fetch; another family's list empty | R1 |
| R9 | PipelineManager dead import | F7 | Restore `backend/src/agents/pipeline_manager.py` or remove the import and label the fallback honestly | Boot log shows "PipelineManager ready" **or** no init-failure line | — |
| R10 | Loud startup seeds | F4 companion | Log per-item failure reasons (the seed already returns them); expose seed state on `/api/health` | A forced seed failure appears in the boot log **with reasons** and in `/api/health.issues` | R4 |
| G0 | Structural hygiene | D15–D19 | Remove Anthropic references (policy); add indexes (`api_keys`, `api_providers`, `ai_usage_log.created_at`, `provider_rankings`); split `api_keys` (provider credentials vs customer API keys); move the sidebar link to the executive section; make Refresh refresh the open tab | `grep -ri anthropic backend/` clean; indexes exist; an `admin` never sees the bouncing link; each tab refreshes itself | — |
| G1 | Real revocation | D1, D2 | Call-time credential resolution from a short-TTL snapshot of the vault (DB authoritative; env fills gaps only); `KeyPool.evict` so rotation cannot resurrect a revoked key | Save → status available; **DELETE → next call fails over and status flips without restart**; a second server process (same DB) shows the same within the TTL; restart does not resurrect | — |

### Phase 1 — Truthful gates (monetization integrity)

| ID | Task | Problem | Change | DoD (executed) | Deps |
|---|---|---|---|---|---|
| R6 | Creator money surface gate | F5 | Add `/api/creator/courses`, `/api/creator/courses/{id}`, `/api/creator/payout-profile`, `/api/creator/enrollments/me` to `FEATURE_API_PATHS` (constants only) | Free member `POST /api/creator/courses` → **403**; plus member → 201; `academy-open-access.js` guard rail unchanged | Decision 2 (tier choice) |
| R7 | Tier drift alignment | F6 | Align `ai_chat` (fe member / be free), `courses` (fe plus / be free), `resource_hub` (fe plus / handler member) — pick one side as truth per feature | Free/member/plus probes return the intended codes for each; frontend copy matches behaviour | Decision 1 |
| R8 | Production error masking | F9 | JSON 404/405 for unmatched `/api/*` ahead of the SPA catch-all | Prod `GET /api/nam/chat` → **405 JSON** (matching local); anonymous probes unchanged | Decision 7 |

### Phase 2 — The AI substrate (Track B)

| ID | Task | Problem | Change | DoD (executed) | Deps |
|---|---|---|---|---|---|
| G2 | Registry + validated save + live models + full coverage | D7, D8, D9 | One DB-backed registry (`api_provider_registry`, owner-editable through the UI): rank, signup, routing class, cost class, limits, verification state; the four disagreeing model tables render from it; validate-on-save (live 1-token test before persisting); "Refresh live models" = real `GET /models` per provider; all 27 providers | Invalid key → 4xx with the provider's reason, `api_keys` unchanged, status unconfigured; valid key → stored, masked, `verified_at`; Refresh shows **real provider model IDs**; auto-pool equals exactly the verified set | G1 |
| G3 | Ranking routes + `model:"auto"` + `/v1/chat/completions` | D3, D4, D5 | Router reads the persisted ranking (TTL cache, DB authoritative) instead of the hardcoded tuple; `auto` selects only `verified` + no-cost-class (or policy-authorized) providers within limits; OpenAI-compatible route; explicit models route to their provider or 404 with the available list | Reorder via API → the **next** auto call follows the new order (proved with two configured keys); `auto` returns a real reply and the response + usage row name the serving provider and chain; `model:"nope"` → 404 + list | G2, Decision 6 |
| G4 | Usage log + enforced limits + credit accounting | D6, D10, D11, D14 | One writer at the `call_llm` choke point: `request_id, user_id, endpoint, model_requested, provider, model_served, result, reason, prompt/completion_tokens, latency_ms, cost_class, fallback_chain[], created_at`; the 7 ad-hoc writers become thin wrappers; Mongo rolling-window counters (Gemini requests/minute, Mistral tokens/month, credit grants) enforced pre-dispatch, values owner-editable; local token estimate where the provider reports none | 10 calls with the primary disabled mid-run → 10 rows with chains; counters equal direct Mongo counts; **16 Gemini requests in a minute → the 16th is served elsewhere and the row shows `limit reached`**; Mistral monthly cap enforced; a 1 000-token credit grant → overage shown and the provider leaves the auto-pool until reset | G2 |
| G5 | Specialty vault + missing integrations + tools | D12, D13 | All 11 specialty credentials (Exa, NASA, Pexels, Gumroad, Stripe, Resend, Gmail, Cloudflare Workers AI, HF Inference, ElevenLabs, Groq Audio) vaulted on the same Fernet path: masked, replaceable, testable, toggleable with G1 eviction; integrations read vault-then-env; build the three missing integrations (Exa search, Cloudflare Workers AI image/audio, HF image/music) against their real APIs; Specialty Tools panel executes through the vault | Pexels search returns **real photos**; Gmail test send **delivers**; Exa search returns real results; disable → the tool reports not-configured without restart | G1 |
| G6 | Console UI completion | D8, D9, D21 | Header actions (Test all providers / Refresh live models / Encrypt stored keys with legacy-scan + counts), filter, the full provider table (rank, signup, live model line, routing-class badge, status, masked credential + saved date, active toggle, connection latency + timestamp, limit badge, Test/Configure/Add-replace), routing-policy panel (ranked order that routes, editable limits, live budget, policy switches defaulting to exclusion), Payment/Credit Keys rows with `used this month` from real accounting, Specialty Keys vault, Specialty Tools, Usage Log with window counters and grouped fallback chains | Every element bound to registry/vault — **zero decorative elements**; the annex's 11-step acceptance walkthrough passes end to end | G2–G5 |
| G7 | Monitor loop live + legacy path resolution | D17, D20 | Start `run_monitor_loop()` (real per-provider health probe, auto-revoke on 401/403) with state visible in the console; migrate or delete the write-only legacy path | A failing key is auto-revoked and the console shows it; no write-only collections remain | G1, Decision 8 |

### Phase 3 — Tier 1 depth (the funnel)

| ID | Task | Change | DoD (executed) | Deps |
|---|---|---|---|---|
| R13 | Project review comments + artifacts cited in printed Records (continuation P7) | Additive UI over existing projects/records endpoints | Parent comments persist and render; the printed Records page cites project artifacts; executed end to end | — |
| R14 | K–8 cultural deepening, ~35 courses (continuation P6) | Same attach mechanism as #474 | Course pages show culture integrated per subject; content validation clean; suite green | Decision 5 |
| R17 | Weekly parent report + Afro-Latin / Portuguese-Spanish strands | Report generated from real progress data (no fabricated content) | A real family's report generates with real numbers; strands present in curriculum | — |

### Phase 4 — Tier 2 monetization

| ID | Task | Change | DoD (executed) | Deps |
|---|---|---|---|---|
| R11 | Digital-product commerce depth (continuation P3) | Additive UI over existing `/media/products/*`, no new collections | Purchase path executable end to end (local): buy → entitlement granted → product delivered | Phase 1 |
| — | Creator Studio price + Tier-2 marquee (continuation P2) | One constant per side + nav copy per the decision | Nav copy and gates match the decided price; if free, the Tier-2 proposal has a real marquee | Decision 2 |

### Phase 5 — Tier 3 monetization

| ID | Task | Change | DoD (executed) | Deps |
|---|---|---|---|---|
| R12 | PEP / FES-UA scholarship workflows (continuation P4) | New UI + content over existing `scholarship_funds` | Application → review → award workflow executable end to end | — |
| — | Price the Legal Workflow Engine | Tier decision applied to the (now real) engine | The tier gate matches the decision on both sides | R1, Decision 4 |
| R15 | Co-op / multi-seat (continuation P5) | **Blocked** — needs a field/collection decision | — | Decision 3 |

**Carried observations (no code change without a decision):** the revenue API-key stub
(`/api/revenue/api-keys*` issues keys that authenticate nothing; `verify_api_key` unused) — wire it real or
remove it; owner decision.

---

## 6. Dependency map

```
R1 ──► R5 (the guides' checklist persists through the fixed hub endpoints)
G1 ──► R6, G3 (gates and auto-routing need credentials that can actually be revoked)
G1 ──► G5 ──► G6
G2 ──► G3 ──► G4 ──► G6
R6, R7 ──► Phase 4 (nothing is sold against a lying gate)
R1 ──► Phase 5 (the Legal Engine becomes priceable only once its sync is real)
Decision 3 ──► R15 (co-op cannot start without the schema decision)
```

## 7. Environment recipe (rebuild every session — installs do not persist; ~6 min)

```bash
# 1. mongod (binary path resolved at runtime — do NOT hardcode)
mkdir -p /home/netadmin/s && cd /home/netadmin/s
npm install --prefix /home/netadmin/s --no-audit --no-fund mongodb-memory-server
MONGOD=$(find /home/netadmin/s/node_modules -name 'mongod-*' -type f ! -name '*.md5' | head -1)
mkdir -p /home/netadmin/s/db
"$MONGOD" --port 27097 --dbpath /home/netadmin/s/db --storageEngine wiredTiger --bind_ip 127.0.0.1 --noauth
#    ^ start with the background_process tool (persistent), never shell &

# 2. python deps
python3 -m venv --without-pip /home/netadmin/s/py
curl -s -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
/home/netadmin/s/py/bin/python /tmp/get-pip.py --quiet --no-warn-script-location
/home/netadmin/s/py/bin/pip install --no-cache-dir -r /workspace/app/backend/requirements.txt pytest

# 3. server (ENABLE_API_DOCS=1 exposes /api/openapi.json for route truth)
cd /workspace/app/backend
MONGO_URL="mongodb://127.0.0.1:27097" JWT_SECRET="test-secret-32-chars-minimum-ok!!" ENABLE_API_DOCS=1 \
  /home/netadmin/s/py/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8040
```

The app writes to database **`ancestral_sage`** (honours `DB_NAME`). Runtime-registered surface: **820 paths** —
diff against `/api/openapi.json`, not against source. Exec-account testing: register locally, then set
`role`/`feature_tier` on that row in the **local** DB only. Reusable probes from this session:
`/tmp/audit_probe.py`, `/tmp/audit_probe2.py`, `/tmp/audit_probe3.py`, `/tmp/audit_providers.py`,
`/tmp/render_harness*.js` (jsdom recipe: `react@19 react-dom@19 jsdom @babel/core @babel/plugin-transform-react-jsx
@babel/plugin-transform-modules-commonjs` in `/home/netadmin/rh`; transform only files under
`/workspace/app/frontend/src`).

**Academy suite (the meaningful signal):**
```bash
MONGO_URL="mongodb://127.0.0.1:27097" /home/netadmin/s/py/bin/python -m pytest \
  tests/test_academy_api.py tests/test_academy_projects.py tests/test_academy_content_coverage.py \
  tests/test_compliance_docs.py tests/test_dependency_compatibility.py -q        # 52 passed at plan time
```
**Guard rails (before every commit):** `node frontend/scripts/academy-open-access.js`,
`node frontend/scripts/route-integrity.js`, `node frontend/scripts/nav-integrity.js`, then
`cd frontend && npx craco build` (restore `package-lock.json` afterwards).
Many other `tests/*.py` fail with `Connection refused` against `localhost:8001` — environmental noise; state it,
don't chase it.

## 8. Delivery workflow and report format

1. Branch from `origin/main` after the §1 check. One task per PR.
2. PR body: what was asked vs what changed; **verification evidence** (commands + real output, never "passes");
   what is **not verified** and why; guard-rail results.
3. Never push straight to `main`; never force-push; never `rm -rf`; never reset --hard.
4. Append new defects to `docs/HOMESCHOOL_ACADEMY_ISSUES.md`; never delete entries.
5. Report format the owner accepts: **numbers, not adjectives**; asked vs delivered with PR numbers; what is NOT
   delivered listed explicitly and separately; verified-by-execution vs verified-by-reading vs unverified,
   labelled; own bugs reported as findings; environment-blocked work marked **UNVERIFIED / ENVIRONMENT BLOCKED**,
   never "done".

## 9. What done means (the end state, owner-visible)

1. **Tier 1**: the free Academy works end-to-end with zero silent data loss — no lost enrollments, no lost
   artifacts, the Legal Engine's state actually syncs to the account, the seeded guides are real 8-step
   workflows, and a cold deploy boots clean (NAM corpus seeded, no dead imports).
2. **Tier 2**: every creator/payout/BYOK surface is gated exactly as the tier table says, priced per the
   owner's decision, and its AI cost is real and capped.
3. **Tier 3**: the Resource Hub and Legal Workflow Engine are real, synced, and priced; scholarship and co-op
   surfaces exist or are explicitly deferred by owner decision.
4. **Substrate**: the gateway runs verified no-cost providers for `model:"auto"` with provider-aware failover,
   enforces Gemini 15 RPM and Mistral 1M tokens/month, revokes keys instantly across replicas, logs every
   attempt with its fallback chain, keeps every credential encrypted and masked, and gives the owner live
   control of ranking, limits, budgets, and routing policy through the interface.
5. **Revenue**: each monetization path — BYOK unlock, creator commerce, Tier 3 institutional access — is
   executable end-to-end by a real customer, proven by execution, not by build success.
