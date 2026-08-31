# WAI Platform — Launch Remediation Plan

**Rewritten:** 2026-08-31, from executed evidence in this checkout.
**Replaces:** the 2026-08-21 plan, which was stale (it described a 2,447-line
`server.py` and 41 routers; reality is **2,826 lines and 50 routers**).
**Audience:** Delon Oliver.

**How to read this.** Every claim below is labelled with how it was
established. `EXECUTED` means I ran it and captured the output. `SOURCE` means I
read the code and it is provable from the code. `BLOCKED` means this container
has no MongoDB so it could not be run. Nothing here is labelled "done" because
it was written down.

---

## Part 0 — Already fixed and verified this session

| # | Defect | Evidence |
|---|---|---|
| 1 | `backend/crm/routes.py:158` — `request: Request` after defaulted params. Module never imported; failure swallowed to a `logger.warning`; **zero** `/api/crm` endpoints existed at runtime. | `EXECUTED` — OpenAPI went 631 → 639 paths; 8 CRM paths / 11 operations now register; no `failed to load` warnings remain. |
| 2 | 9 of 11 CRM endpoints had **no auth dependency**; the other 2 depended on `request.state.user`, which nothing in the repo ever sets. The AccessGateway did **not** save them. | `EXECUTED` — traceback showed an unauthenticated request passing `gateway.py:579 → call_next` into `count_documents({})`. Now router-gated at oversight+; 6/6 unauthenticated calls return 401, forged token 401, rank logic correct across all 9 role values incl. legacy `steward`. |
| 3 | `GET /providers/usage-log` registered **3×**. Two of the three read collections (`provider_usage`, `api_key_usage_log`) that **nothing writes to**. | `EXECUTED` — 3 registrations → 1, owned by `provider_gateway.py:183`, now reading `ai_usage_log` (7 writers) and honoring `?limit=`. Duplicates 7 → 6. |

**Why #3 matters beyond the fix.** The "obvious" cleanup — delete the
duplicates, keep the newest — would have permanently blanked the Provider
Gateway Usage tab, because the accidental winner was the only handler reading a
collection with data. Static route-dedup tooling would have shipped that
regression. This is the pattern to distrust everywhere else.

---

## Part 1 — Your toggle idea, made real

### The idea
"Leave me a way to toggle off and on non-working features," so you can launch
with the working surface visible and everything else hidden.

### The reality (this is the important part)

You already have **two** toggle systems. One works. One is a placebo.

| | System A — **works** | System B — **placebo** |
|---|---|---|
| Store | `db.page_access` | `db.feature_configs` |
| Admin UI | `ExecControlPanel.jsx:198`, `ExecBusinessOffice.jsx:284` | `FeatureControlCenter.jsx:80,100,120` |
| Writes via | `POST /api/exec/control/access` | `PUT /api/features/{feature_id}` |
| Read for enforcement | `GET /api/exec/control/access/public` → `accessGates.js:71`, `useFeatureToggle.js:19` | **nothing** |
| Registry | ad-hoc page keys | **49 features** with roles, tiers, `cost_bearing`, `internal_only` |

`SOURCE` — grep for frontend consumers returns only `FeatureControlCenter.jsx`
touching `/features`, and it only ever **writes**. No enforcement path reads
`db.feature_configs`.

**Consequence: flipping a switch in the Feature Control Center changes nothing a
user sees.** Your nicer, richer, 49-feature control panel is disconnected from
enforcement. The crude page toggle is the one with real effect. That is a direct
instance of "features not functional as intended," and it is why the toggle you
reached for did not behave.

### Second problem: it fails **open** at three layers

For hiding *broken* features at launch, every default is backwards:

1. `frontend/src/lib/navAccess.js:44` — `if (!policy || typeof policy !== "object") return true;`
   → a page with **no policy is visible**.
2. `frontend/src/lib/accessGates.js:76-79` — on fetch failure, `gates = {}`
   → every page falls into case 1 → **everything visible**.
3. `frontend/src/components/AccessGate.jsx:26` — `if (!ready) return children;`
   → the page **renders before gates load**, so a disabled page flashes.

So if the gate request is slow or fails, your entire broken surface is exposed.

### How it becomes real in code

**Step 1.1 — Make System B enforceable without a migration or a frontend rewrite.**

Do *not* rewire the frontend and do *not* migrate collections. Change one
endpoint — `ec_access_public` at `backend/routers/exec_control.py:1049` — to
return a **merged, most-restrictive** view of both stores:

- read `db.page_access` (as today);
- read `db.feature_configs` and the 49-entry `FEATURE_REGISTRY` via the existing
  `get_feature_config_async()` (`backend/routers/features.py:997`);
- for each page key, `enabled = A.enabled AND B.enabled` — disabled in *either*
  store means disabled.

Effect: Feature Control Center toggles start working **immediately**, existing
page toggles keep working, no data moves, and `accessGates.js` needs no change
because it already honors `enabled: false`. This is roughly a 20-line change in
one function, and it is the highest leverage edit in this whole plan.

The registry already carries the key mapping surface you need
(`route`, `navigation_group`, `navigation_label`), so the merge can key on the
same page keys `accessGates.pathKey()` produces.

**Step 1.2 — One server-side switch that inverts the default to "hidden."**

Add a `launch_mode` flag to `db.platform_flags` (the collection
`enforce_platform_flags` already reads at `backend/server.py:230`). When
`launch_mode` is on, `ec_access_public` returns a policy for **every** registry
feature with `enabled: false` unless the feature is on an explicit launch
allowlist.

Why this shape: it inverts fail-open → fail-closed **centrally, on the server**,
using enforcement that already exists. The frontend needs no logic change. You
get one switch that means "show only what I have blessed," and you bless
features one at a time as they are proven. That is exactly the launch posture you
asked for, and it is reversible in one write.

**Step 1.3 — Stop the flash and the fail-open fetch.**

- `AccessGate.jsx:26` — return a neutral loading state, not `children`.
- `accessGates.js` catch block — set a `gatesFailed` flag; when set and
  `launch_mode` is on, treat unknown pages as **hidden** rather than visible.

Keep `home`, `login`, `register`, `forgot-password` always-visible (already
special-cased at `navAccess.js:40-42`) or you will lock yourself out.

**Step 1.4 — Back the toggle with real API enforcement.**

`navAccess.js:20` says it plainly: "Navigation visibility is UX only — the
backend stays authoritative." Right now, for a disabled feature, that is not
true — hiding the nav item does not stop the API. And the AccessGateway is
**fail-open** for routes absent from its startup snapshot (`EXECUTED`, Part 0 #2).

So: add a FastAPI dependency that calls the existing
`get_feature_config_async(feature_id)` and returns 403 when the feature is
disabled, and attach it **at router level** (as I did for CRM) on the routers
backing toggleable features. Router-level is deliberate: per-endpoint
dependencies get forgotten, which is precisely how 9 CRM endpoints ended up
unguarded.

**Step 1.5 — Close the gateway's fail-open snapshot.**

`access_gateway.wrap(app)` (`backend/server.py:2783`) snapshots the route surface
at call time. Four routers register *after* it — `nam:2789`, `saga:2798`,
`executive_pipeline:2809`, `exec_tools:2818` — and are in neither the public list
nor the handler-requirement list. These are your highest-authority routers. Move
the `wrap()` call **after** all `include_router` calls, then re-verify the two
snapshot counts rise (they were 133 public / 541 with requirements).

---

## Part 2 — Make the AI real

`EXECUTED` — importing the app reports `/api/health` → `"issues": ["db_down",
"ai_providers_unconfigured"]`. The AI chain is not proven working in this
environment, only present.

- `backend/ai/llm_gateway.py` (46KB) is the single AI authority; providers pinned
  in `requirements.txt` are groq, openai, together, cohere, mistralai,
  huggingface_hub. Key resolution ladder: env → `keyvault` → BYOK → user budget.
- `backend/ai/persona_loader.py` — `_PERSONA_MAP` at `:1058`, plus a synthetic
  `"unified"` key at `:1157`. **Count the keys before quoting "17."**

**What to do, in order:**
1. Confirm at least one provider key is live via `GET /api/providers/quick-setup/status`
   (exec-only) and that `/api/health` stops reporting `ai_providers_unconfigured`.
2. Execute **one** persona round-trip through the real chat endpoint with a real
   token and capture the response body. Not a unit test. Not a health check.
3. Confirm the free-first fallback actually falls back: force the primary
   provider to fail and verify the next tier answers rather than the request 500ing.
4. Confirm `prompt_guard.py` and `sage_safety_gates.py` are on the live call path
   (grep call sites; a guard nothing imports is decoration).
5. Confirm per-user budget enforcement (`user_budget.py`, `ai_cost_tracker.py`)
   actually denies when exhausted — this is your **cost-saving** control, and an
   unenforced budget is an unbounded bill.

Item 5 is the cost-saving feature that must be real. Prove it by execution.

---

## Part 3 — Revenue must be real

Lemon Squeezy is merchant of record, Gumroad second (your directive; also recorded
at `backend/routers/payments.py:37-40`).

**3.1 — Gumroad sales are invisible. `SOURCE`, high severity.**
Gumroad has **outbound** publishing only (`ai/publishing.py:242`, plus persona
tools POSTing products). There is **no inbound Gumroad webhook** — the only two
webhook routes are `/api/payments/stripe-webhook` and `/api/payments/webhook`
(Lemon Squeezy). A Gumroad purchase records no order, grants no tier, fulfils
nothing.

Fix: add `POST /api/payments/gumroad-webhook` modelled exactly on the existing
Lemon Squeezy handler (`payments.py:815`) — verify authenticity, insert the event
id as `_id` into `db.webhook_events` for idempotency (catch duplicate-key
`11000`, return no-op), then reuse the existing `_grant_tier_by_email` and
pending-order reconciliation. Register it in the AccessGateway's public list, as
the two existing webhooks already are (`EXECUTED` — both confirmed present).

**3.2 — Failed renewals keep full access. `SOURCE`, high severity.**
Handled Lemon Squeezy events (`payments.py`): `order_created:870`,
`subscription_cancelled/expired/paused:994`, `order_refunded:1040`,
`subscription_resumed/unpaused:1089`, `subscription_created:1101`.
**Missing: `subscription_payment_failed`** — so a declined card revokes nothing.
Also missing `subscription_payment_success` (renewal) and `subscription_updated`
(plan change). Add them to the same dispatcher; the idempotency and
grant/revoke helpers already exist.

**3.3 — All four scheduled revenue jobs are no-ops. `EXECUTED`.**
`db_manager.db is None: True`. `backend/jobs.py` guards every job with
`if not db_manager.db: return` (`:91, 170, 221, 261, 293`), and
`start_revenue_operations(db)` (`revenue_operations_integration.py:97`) receives
the live database and **never passes it to `db_manager`**. `database.init_database()`
is called nowhere. So payouts, revenue recognition, renewal alerts, and dunning
have never run — while logging `✅ Revenue operations job scheduler started`.

Fix carefully, and **do not** call `init_database()`: it reads different
env vars and a different database name (`MONGODB_URI` / `wai_institute` at
`config.py:17-21`) than the live app (`MONGO_URL` / `ancestral_sage` at
`server.py:107`). That would connect the jobs to a second, empty database and
they would "succeed" against nothing. Instead assign the **live** handle into
`db_manager` inside `start_revenue_operations`.

Then, before enabling: keep `JOBS_ENABLED=false`, add a dry-run that reports what
the first payout run *would* do, and review it. `jobs.py:95` says payouts are
settled manually, and the job only snapshots balances into pending records — so
it does not move money by itself. Confirm that is still true before enabling.

**3.4 — Two dunning paths are stubs.** `check_renewal_deadlines` and
`check_failed_payments` end at `# TODO: Send actual email via SendGrid`
(`jobs.py`). SendGrid is not in this stack — email is Resend with Gmail SMTP
fallback (`server.py:657-735`). Wire to the real sender. Separately, note
`contracts` and `invoices` have **no writers anywhere in the repo**, so those two
jobs currently query collections nothing populates; fixing the email without
fixing the data source yields silence, not dunning.

---

## Part 4 — Launch blockers (do not go public with these open)

| Severity | Item | Evidence |
|---|---|---|
| **Critical** | `railway.toml` health-checks `/api/version`, which returns 200 with a dead database and never touches it. `/api/health` correctly reports `status:"critical"` but **nothing gates on it**. A container with no database is declared healthy and takes traffic. | `EXECUTED` — `/api/version → 200` three times while startup was still incomplete; `/api/health → 200 {"status":"critical","issues":["db_down",...]}`. |
| **Critical** | Startup is fire-and-forget: `asyncio.create_task(_on_startup_impl())` (`server.py:1350-1362`). Requests are served before `deps.set_db()`, `app.state.db`, keyvault, indexes, and seeds. The task handle is never stored (GC-eligible) and every step is `try/except → warning`. | `EXECUTED` — requests served with `startup_impl_complete=False`. |
| **Critical** | No exec seat email configured → **"On a fresh database the first registered user would become executive_admin."** | `EXECUTED` — logged at import. Set `EXEC_ADMIN_EMAIL` before the site is public. |
| **High** | `JWT_SECRET` unset prints `FATAL:` and **the app continues anyway**. Must be persistent in Railway or every deploy logs everyone out. | `EXECUTED` — logged at import. |
| **High** | `AUDIT_ENCRYPTION_KEY` unset → access-denial records stored **unencrypted**. | `EXECUTED` — logged at import. |
| **High** | `deps.bind()` is **never called anywhere**, so `deps.dep_current_user` / `require_rank` / `require_tier` raise 503 unconditionally. Currently harmless — the 47 routers use their own local copies — but it is a live landmine: the module documents itself as "the canonical target" for migration, so the next migration silently 503s a router. | `SOURCE` — zero call sites. |
| **High** | `deps.require_tier` looks broken-open: `deps.py:107` only computes a rank if `min_tier` is in a hardcoded tuple of **role** names, so real tier names (`free`, `basic`, `premium`, `staff`, `exec`) yield `needed = 0` and admit everyone. It never calls `tier_min_rank()`. | `SOURCE` — confirm by execution before relying on any tier gate. |
| **Medium** | CORS `allow_origins=['*']`. Auth is a bearer token from `localStorage`, so `allow_credentials=False` does not prevent replay from any origin. Pin to your two domains. | `EXECUTED` — observed middleware config. |
| **Medium** | Rate limiting is an in-process `defaultdict` (`server.py:310`, comment: "replace with redis in true HA prod"). Resets on restart, per-worker. | `SOURCE` |
| **Medium** | **6 duplicate `(method,path)` registrations remain**: `DELETE /admin/users/{uid}`, `DELETE|GET /admin/users/{uid}/sessions`, `GET /admin/users/{uid}/audit`, `GET /exec/control/route-access`, `GET /personas`. Shadowed admin-delete and session-revoke handlers are an authz hazard if the winner has the weaker gate. | `EXECUTED` — Recipe C. |
| **Medium** | Frontend stale-role window: `auth.jsx:22-32` seeds `user` from the `lce_user` cache and sets `loading=false` immediately, so `Protected` authorizes on a cached role while `/auth/me` is in flight. Server still enforces, so this is a UI-truth / exposure-window defect, not a confirmed bypass. | `SOURCE` |
| **Low** | **Zero frontend tests.** `package.json:62` defines `craco test`; no test file exists. All browser verification is manual — never cite a frontend test as evidence. | `EXECUTED` |

---

## Part 5 — Recommended order

Launch-blocking and cheap first.

1. **Part 1.1 + 1.2** — merged gate read + `launch_mode` flag. This is what lets
   you launch at all: hide everything unproven behind one switch.
2. **Part 4 criticals** — `EXEC_ADMIN_EMAIL`, persistent `JWT_SECRET`,
   `AUDIT_ENCRYPTION_KEY`, and move the Railway healthcheck to a readiness
   endpoint that fails when the database is down.
3. **Part 1.3 + 1.4** — stop the fail-open flash; enforce toggles on the API.
4. **Part 3.1 + 3.2** — Gumroad webhook and `subscription_payment_failed`. Direct
   revenue leaks; both reuse a proven idempotency pattern.
5. **Part 2** — prove one AI round-trip and budget enforcement end-to-end.
6. **Part 1.5** — move `access_gateway.wrap(app)` after all router includes.
7. **Part 3.3 + 3.4** — job scheduler wiring, dry-run first.
8. **Part 4 mediums** — CORS, duplicates, rate limiting.

---

## Part 6 — How to check my work

No claim in this plan needs to be taken on trust. Run these.

```bash
cd backend

# 1. What actually registered? Watch stderr — every "failed to load" is a
#    feature that does not exist at runtime.
JWT_SECRET=t python3 -c "
import logging; logging.disable(logging.CRITICAL)
import server; print(len(server.app.openapi()['paths']), 'paths')"

# 2. Duplicate/shadowed routes. app.routes is USELESS here (returns 7 lazy
#    _IncludedRouter wrappers) — you must recurse.
JWT_SECRET=t python3 -c "
import logging, collections; logging.disable(logging.CRITICAL)
import server
seen=collections.Counter()
def walk(rs):
    for r in rs:
        o=getattr(r,'original_router',None)
        if o is not None: walk(o.routes); continue
        p,ms=getattr(r,'path',None),getattr(r,'methods',None)
        if p and ms:
            for m in ms: seen[(m,p)]+=1
walk(server.app.routes)
print({k:v for k,v in seen.items() if v>1})"

# 3. Is a collection actually written, or only read? Run this before trusting
#    ANY read path. It is how the usage-log bug was found.
grep -rn "<collection_name>" --include=*.py . | grep -iE "insert|update"
```

Use `python3`, not `python` — `python` is not on PATH, so every `python -m ...`
command in `AGENTS.md` and `opencode.json` fails as written.

**No MongoDB in this container.** Persistence, seeding, indexes, and the full
RBAC matrix are `BLOCKED` here and must be proven in an environment that has one.

---

## Part 7 — Standing rule

The three bugs fixed today shared one shape: **each reported success while doing
nothing.** A swallowed import warning. A gate that let the request through. A
`✅ scheduler started` log in front of four no-op jobs.

That is why the plan above never accepts a log line, a 200, or a file's existence
as proof, and why `.claude/skills/_shared/REPO-REALITY.md` now anchors every audit
skill to executed evidence with a fixed vocabulary
(`route-registered`, `executed`, `persistence-verified`, `UNVERIFIED`,
`ENVIRONMENT BLOCKED`, `BROKEN`). `source-confirmed` is not sufficient to call an
endpoint real in this codebase.
