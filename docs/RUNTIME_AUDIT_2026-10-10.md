# RUNTIME AUDIT — MoreHelp Center / WAI Homeschool Academy

**Date:** 2026-10-10 · **Auditor:** successor session (continuation-plan §1 check passed: branch `kilo/focused-firefly-ikf`, 0 behind `origin/main` at `5430570c`)
**Method:** live execution against a real server, database, and rendered frontend. Nothing below is inferred
from file trees or route enumeration. Prior reports were treated as unverified until reproduced in code or at runtime.

---

## 1. What was actually executed

| # | Execution | Result |
|---|---|---|
| 1 | mongod 8.2.6 (memory-server binary) on 27097 + uvicorn `server:app` on 8040, real Mongo writes | server booted, "Application startup complete" |
| 2 | Academy test suites (`test_academy_api`, `test_academy_projects`, `test_academy_content_coverage`, `test_compliance_docs`, `test_dependency_compatibility`) | **52 passed** (matches plan's last-observed) |
| 3 | Guard rails `frontend/scripts/{academy-open-access,route-integrity,nav-integrity}.js` | **3/3 PASS** (193 routes, no dead paths) |
| 4 | ~77 authenticated HTTP probes across auth, academy, projects, hub, creator, AI chat, isolation, edge cases | see findings |
| 5 | Concurrency loops: 8 enrollment rounds × 3 writers; 6 artifact rounds × 3 writers; 4× duplicate register | see F2, F3 |
| 6 | jsdom render harness executing the **real** `ResourceHubPanel.jsx` and `LegalWorkflows.jsx` against the **real captured backend response shapes** | see F1, F8 |
| 7 | 12 read-only probes against the live target `charming-analysis-morehelpcenter.up.railway.app` | see F9, F10 |
| 8 | Fresh-DB cold boot (`DB_NAME=fresh_nam_probe4`) reproducing startup seeding | see F4 |

Runtime route surface captured from the live app: **820 paths / 944 operations** (GET 436, POST 407, PATCH 47, DELETE 39, PUT 15). The plan's "1,008 endpoints" is not the registered number.

---

## 2. Findings (all proven by execution)

| ID | Severity | Class | Finding |
|---|---|---|---|
| F1 | **Critical** | broken contract + swallowed async failure | Legal Workflow Engine "sync to account" is dead — every restore/sync fails silently |
| F2 | **Critical** | race condition (read-modify-write) | Concurrent course enrollment **loses enrollments** while returning 200 |
| F3 | **High** | race condition (read-modify-write) | Concurrent project artifact saves **silently drop earlier artifacts** |
| F4 | **High** | runtime failure, false pass | Hybrid NAM knowledge seed fails **31/31 on any real database**; `nam_knowledge` is empty in production |
| F5 | **High** | gate hole | The Creator **money surface** accepts writes from free accounts (course created, HTTP 201) |
| F6 | Medium | tier drift (frontend vs backend) | `ai_chat`, `courses`, `resource_hub` disagree between `lib/tiers.js` and `feature_control.py` |
| F7 | Medium | startup failure | `PipelineManager` init fails on every boot (`No module named 'src'`) — keyword fallback only |
| F8 | **High** | inert feature | Resource Hub "guides" are empty catalogue rows behind the badge the owner rejected |
| F9 | Medium | prod/local divergence | Production masks API 404/405 with the SPA catch-all (200 HTML) — probes and monitors are lied to |
| F10 | Process | prior-report defects | The continuation plan itself contains 4 statements disproved by this audit |

### F1 — Legal Workflow Engine account sync is dead code at runtime (Critical)

Two stacked contract defects, both reproduced:

1. **`GET /api/hub/workflows` returns a bare JSON array.** Probe as a plus member: `body_type=list`.
   The frontend reads `r.data?.workflows` (`frontend/src/pages/LegalWorkflows.jsx:155,174`) → `undefined` →
   `.find()` throws `TypeError` → swallowed by `.catch(() => {})` (lines 160, 178). Restore never happens.
2. **`POST /api/hub/workflows` declares `title`/`area`/`steps` as query parameters** (`backend/routers/resource_hub.py:369` — no `Body(...)`), while the frontend sends a JSON body. Executed result:
   ```
   422 {"detail":[{"type":"missing","loc":["query","title"]},{"type":"missing","loc":["query","area"]},{"type":"list_type","loc":["body"]}]}
   ```
   The query-param shape works (201) — no frontend caller uses it.

Render-harness proof (real component, real shapes): on mount the component fires `GET /api/hub/workflows`;
after each state change it fires `GET` then `POST /api/hub/workflows` with the JSON payload — every POST is the
422 above, swallowed. **User-visible consequence:** the comment at `LegalWorkflows.jsx:135-138` ("It now mirrors
to their account… one well-known workflow") is false. A member's case work exists only in that browser's
`localStorage`; change device and it is gone. This is the "unhandled asynchronous failure" class: the failure is
real, silent, and defeats an advertised feature.

### F2 — Concurrent enrollment silently loses courses (Critical)

`backend/routers/academy.py:614-629` reads `course_slugs`, mutates the set, and `$set`s the whole array.
Executed: 8 rounds × 3 concurrent enroll calls for one student:

```
every round: codes=[200, 200, ...]  but  1–2 of the 3 courses missing from the dashboard
round 0: missing={'visual-arts-foundations'}   round 3: missing={'parent-handbook'}
```
All responses are `200 OK`. A parent (or the auto-enroll path) enrolling two courses at once — two tabs, a
double-click, a slow network retry — loses one with no error. The API reports success for lost writes.

### F3 — Concurrent artifact saves silently drop earlier artifacts (High)

`backend/routers/academy.py:1471-1496` merges artifacts in Python (`safe = dict(p.get("artifacts"))`) then
`$set`s the whole map. The sequential merge (ledger #9's fix) works — executed: sequential saves keep all keys.
Under concurrency (6 rounds × 3 concurrent writers of different steps):

```
rounds_with_loss = 4/6
round 0: wanted {interview, records, tree} -> got {tree: 'r0s2'}
round 4: wanted {r4s0, r4s1, r4s2}        -> got {tree:'r4s2', interview:'r3s0', records:'r4s1'}   (stale step-1 value resurrected)
```
Scenario: a family filling the 6-step family-history pathway from two devices/tabs loses work and can even see
a **stale value resurrect** over a newer one.

### F4 — Hybrid NAM knowledge seed can never write to a real database (High)

Cold boot on a fresh DB logs: `STARTUP: Hybrid NAM knowledge seed done — 0 seeded, 0 skipped, 31 failed.`
Root cause, reproduced by calling the seed after the real startup: every item fails with
`Database objects do not implement truth value testing or bool(). Please compare with None instead: database is not None`.
Source: `backend/ai/hybrid_nam/persistence.py:35` — `return _db[name] if _db else None` truth-tests the motor
`Database` handle (the same pattern repeats for collections at lines 47, 59, 71, 85, 93). Verified in Mongo:
`nam_knowledge` count = **0** in every database touched by a server boot.

The "standalone seed works (31/31)" result is a **false pass**: with no DB bound, every write goes to the
in-memory `_FALLBACK` store. So on the live deployment the owner's 31-item Hybrid NAM corpus is absent, and the
only signal is one non-fatal startup line.

### F5 — The Creator money surface is ungated (High)

Executed as a **free** (`feature_tier: "free"`) registered member:

| Request | Result |
|---|---|
| `GET /api/creator/courses` | 200 OPEN |
| **`POST /api/creator/courses`** | **201 — course created** |
| `GET /api/creator/payout-profile` | 200 OPEN |
| `GET /api/creator/enrollments/me` | 200 OPEN |
| `GET /api/creator/earnings` | 403 GATED (Plus) |
| `GET /api/creator/payouts` | 403 GATED (Plus) |

`/api/creator/courses*` (7 routes) is absent from `FEATURE_API_PATHS` (`backend/security/feature_control.py:70-83`),
so the gateway never gates it. A free account can author, price, publish and delete marketplace courses — the
surface the continuation plan calls "the money surface and the least protected part" — confirmed by execution, not reading.

### F6 — Tier drift frontend vs backend (Medium)

| Feature | Frontend (`lib/tiers.js`) | Backend (`FEATURE_MIN_TIER`) | Executed evidence |
|---|---|---|---|
| `ai_chat` | member | **free** | plain student `POST /api/ai/chat` → 200 with a real reply |
| `courses` | plus | **free** | catalog detail served to any authenticated user |
| `resource_hub` | plus | member (handler) | free member → 403 "requires a **Member** subscription" |

`resource_hub` has **no** `FEATURE_API_PATHS` entry — it is handler-guarded only (`_require_member`).

### F7 — PipelineManager dead on every boot (Medium)

Startup log on every run: `STARTUP: PipelineManager init failed (non-fatal): No module named 'src'`
(`backend/server.py:1580` imports `src.agents.pipeline_manager`; there is no `backend/src/`). LLM intent routing
permanently runs the keyword fallback. Either restore the module or delete the import and the fallback label.

### F8 — Resource Hub guides are inert rows behind the rejected badge (High)

Executed against the live DB and the real component:

- `GET /api/hub/resources?category=templates` as plus: both guides return `in_product=None, steps=0, url=''`.
- Render of the real `ResourceHubPanel` with those exact rows: **"Read-only guide · no workflow" badge renders**,
  no "Workflow · N steps" badge, no "Open the workflow" button. (The `url` guard is correct — no empty-href link.)

So continuation-plan §4.1 is **not started** (`grep -c in_product backend/routers/resource_hub.py` = 0), and the
badge the owner rejected is still live in the UI.

### F9 — Production masks API errors with the SPA catch-all (Medium)

Read-only probes, prod vs local, same version (4.0.1):

| Path | Production | Local |
|---|---|---|
| `GET /api/nam/chat` (POST-only) | **200 text/html** (index.html) | 405 JSON |
| `GET /api/hub/grants` | 401 JSON (identical body) | 401 JSON |
| `GET /api/hybrid-nam/status` | 401 JSON (identical body) | 401 JSON |
| `GET /api/academy/courses` | 200 JSON (identical) | 200 JSON |
| `GET /api/health`, `/api/version` | 200 | 200 |

Consequence for every future audit: on production a `200` proves nothing — the body must be checked for JSON.
(Continues the plan's §6 warning, now with a side-by-side execution.)

### F10 — Statements in prior reports disproved by this audit (Process)

| Claim | Source | Reality (executed) |
|---|---|---|
| "routers/ is not loaded on the deployed server; /ai/chat comes from the inline handler" | continuation plan §6 | Routers **are** loaded in prod: `/api/academy/*`, `/api/nam/*`, `/api/hybrid-nam/*`, `/api/ai/personas`, `/api/hub/*`, `/api/creator/*` all answer with JSON identical to local. The inline `server.py` handler and `routers/ai.py` coexist; the deployed behaviour matches this checkout. |
| Guard rails live at `scripts/*.js` | plan §5 | They live at **`frontend/scripts/*.js`**; the plan's paths fail with MODULE_NOT_FOUND |
| "Backend = 1,008 endpoints" | plan §3 | Registered surface is **820 paths / 944 operations** |
| "194 frontend routes" | plan §3 | route-integrity reports **193** |

---

## 3. Verified working (executed, not read)

- Public Academy: `GET /api/academy/courses` 200 anonymous; course detail 200 anonymous with `content_visible=false`; unknown course → 404.
- Auth gates: bad token → 401 JSON; `POST /api/ai/chat` anonymous → 401. **Duplicate-registration race: 4 concurrent identical registrations → one 200 + three 409** (correct).
- Student lifecycle: create with `grade=K`, `grade=adult`, `grade=3` → 200 (ledger #8 fixed); invalid grade → 422; over-length grade → 422; auto-enrolment populated 7 recommended courses.
- Projects: create family-history project (6 steps) → 200; sequential artifact merge works (ledger #9 fixed); off-pathway artifact keys dropped.
- Academy: lesson attempt round-trip; records endpoint returns `{student, generated_at, rows, summary, disclaimer}`; compliance docs 200.
- Profile: `PATCH /api/auth/me` persists (ledger #15 fixed).
- AI chat: authenticated student gets a grounded knowledge-base reply (BYOK upsell) — 200.
- Isolation: family B reading family A's student → 403; workflow list isolated per account.
- Tests 52/52; guard rails 3/3.

## 4. Not verified (stated, not hidden)

- **Anything behind a production login** — no accounts were created and no data written on production (read-only probes only). Every tier/gate finding above is proven on a local server with a locally-promoted test account.
- Full-course completion → transcript GPA arithmetic: verified by source inspection (`academy.py:1196`) and the 52-test suite, **not** by executing a completed course.
- ~900 of 944 operations were not exercised; the audit spot-checked ~40 plus 3 concurrency loops.
- Frontend beyond the two rendered components (no full CRA build run — `node_modules` absent; `npx craco build` would need a ~3-minute install).

## 5. Environment notes for the next session (corrections to plan §5)

- Guard rails: `node frontend/scripts/{academy-open-access,route-integrity,nav-integrity}.js` from the repo root.
- `ENABLE_API_DOCS=1` is required to get `/api/openapi.json` (docs are env-gated off).
- App database is `ancestral_sage`; the app honours `DB_NAME` if set.
- mongod 8.2.6 binary resolves under `/home/netadmin/s/node_modules/mongodb-memory-server/mongodb-binaries/`.
- All probe scripts are reusable: `/tmp/audit_probe.py`, `/tmp/audit_probe2.py`, `/tmp/audit_probe3.py`, `/tmp/render_harness*.js`.
