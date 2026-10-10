# MoreHelp Center / WAI Homeschool Academy — CONTINUATION PLAN

**Purpose:** allow the next session to continue correctly without drift. Written by the
session that ran 2026-10-10. Read §1 before touching any file.

**Owner:** Nam Oshun Edutainment LLC · **Live target:** https://charming-analysis-morehelpcenter.up.railway.app
**Public front door:** `www.morehelp.center/HomeschoolAcademy`

---

## 1. READ THIS FIRST — the drift trap that cost this session

**Symptom:** commands succeed, but files don't contain work you know was merged.

**Cause:** this checkout's worktree silently resets to branch `kilo/long-turtle-bvz` at commit
`05737ab9`, which is **13 commits behind `main`**. It happened twice. The second time it produced
a wrong audit (numbers measured against pre-#469 code) and a partially-applied edit.

**Run this before every edit, every time:**

```bash
cd /workspace/app && git rev-parse --abbrev-ref HEAD && git rev-list --count HEAD..origin/main
```

Interpretation:
- branch is `kilo/long-turtle-bvz` and the count is **> 0** → you are on the stale trap branch.
  Do **not** edit. Run: `git stash -q && git checkout -q -B <your-branch> origin/main`
- branch is `main`/your own branch and the count is **0** → safe.

**Never trust a file's contents because you remember editing it.** Verify with `grep` against the
actual tree before claiming anything is present or absent.

---

## 2. Owner's standing rules (violating these is the main failure mode)

1. **"Done" means executed, not inspected.** Every claim of working needs a run: server + DB, or a
   rendered component. Source-reading is evidence of *existence*, never of *working*.
2. **No "make it honest" as a substitute for building it.** If a feature is advertised but inert,
   build it or report it as **not delivered**. Do not relabel it as "by design" / "read-only" /
   "guide only". (The owner explicitly rejected this after PR #479 added a
   "Read-only guide · no workflow" badge.)
3. **Zero architectural change, zero DB schema change, zero role changes, zero speculative
   refactoring.** Constants and additive code only. Exceptions require the owner's decision *first*.
4. **The Homeschool Academy is free to every registered member.** The rest of the site keeps its
   paywalls. Freeing the Academy must never read as freeing the site.
5. **Live delivery on `main` + PR**, in the owner's reviewable-PR workflow. Do not push straight to
   `main` (that removed work from their hands once); do not force-push.
6. **Verify against the live target** at `charming-analysis-morehelpcenter.up.railway.app` — read-only
   probes only. **Never create accounts or write data on production.**
7. **Parent is legally responsible; the platform must not imply otherwise** (F.S. §1002.41, NoI,
   diploma issuance). This framing is already in the ToS, DMCA page, privacy policy, and handbooks.
8. **A bug found by your own tests is a finding, not an embarrassment** — report it and fix it. Several
   of this session's bugs were self-inflicted and were caught by execution, which is the point.

---

## 3. Verified state at handoff (do not re-derive)

- `origin/main` = **`4a318815`** ("…label guides as guides (#479)"). Tree must equal it before starting.
- **Merged and live:** #469–#479 (11 feature PRs + 3 dependabot). Full catalogue: 96 published
  courses, 663 lessons, 9 tracks, 5 handbooks (`parent-handbook`, `handbook-elementary`,
  `handbook-middle-school`, `handbook-high-school`, `handbook-adult`).
- **Route surface on main:** 194 frontend routes = 80 public / 47 free-login / 12 tier-gated /
  55 role-gated. Backend = 1,008 endpoints.
- **Live gate probes:** Academy public 200; `academy/students`, `hub/*`, `creator/courses`,
  `creator/earnings`, `creator/payouts`, `auth/me`, `ai/chat` all 401 anonymous.
- **Tier drift confirmed (real):** `ai_chat` frontend=member/backend=free; `courses`
  frontend=plus/backend=free; `resource_hub` frontend=plus/backend=unmapped (handler allows member).
  `ghost`, `artist_mgmt`, `mass_post`, `projects` unmapped backend.
- **Gate holes confirmed (real):** `/creator/courses/*` (7 routes) + `/creator/payout-profile*` +
  `/creator/enrollments/me` carry **no tier check** (auth only). `/api/hub/*` (16 routes) absent from
  `FEATURE_API_PATHS`, handler-guarded only.
- **Issue ledger:** `docs/HOMESCHOOL_ACADEMY_ISSUES.md` — 18 items, add to it; never delete entries.

---

## 4. Immediate next task (half-finished — start here)

### 4.1 The two seeded guides are placeholder rows, not references

`backend/routers/resource_hub.py` seeds "Grant Writing Basics Guide" and "Community Fundraising
Playbook" with **`url: ""`** and no content. They are not links — they are catalogue rows with
nothing in them. PR #479 papered over this with a "Read-only guide · no workflow" badge, which the
owner rejected. **Remove that badge and build the intended thing.**

The backend half is already written and verified to apply cleanly to `4a318815`:
`grep -c in_product backend/routers/resource_hub.py` must return **2**. If it returns 0, re-create
it from the content in `docs/HANDOFF_GUIDE_STEPS.md` (same folder as this file) — do not invent
different steps, and do not silently reduce them.

**Definition of done:**
1. `in_product: True` + 8 `steps` on each guide, seeded through the normal `seed_hub_resources` path
   (no new collection, no schema change).
2. `frontend/src/components/ResourceHubPanel.jsx`: the "Read-only guide · no workflow" badge is
   **deleted**; a "Workflow · N steps" badge renders; a **"Open the workflow"** button appears on
   cards with `in_product`; the external link only renders when `url` is non-empty.
3. Clicking it opens a checklist whose checkboxes **persist to the account** via the existing
   `POST/PATCH /api/hub/workflows` endpoints (no new endpoint).
4. Verified by rendering the real panel and by a live server: check a box, re-fetch, confirm it
   sticks; confirm another family's log is empty.

### 4.2 Then, in order (each is a separate PR; each must be executed, not inspected)

| # | Task | Definition of done |
|---|---|---|
| P1 | Make the tier gates truthful | Add `/creator/courses`, `/creator/payout-profile`, `/creator/enrollments/me` to `FEATURE_API_PATHS`; align `ai_chat` and `resource_hub` between `lib/tiers.js` and `feature_control.py`. **Constants only.** Verify by live free-member probes, not by reading. |
| P2 | Decide Creator Studio's price | One constant per side, plus nav copy. If it stays free, the proposal's Tier 2 needs a real marquee. Owner decision required. |
| P3 | Digital-product commerce depth | Additive UI over existing `/media/products/*`. No new collections. |
| P4 | PEP / FES-UA scholarship workflows | New UI + content over existing `scholarship_funds`. Zero references to PEP/FES exist today. |
| P5 | Co-op & multi-seat | **Blocked.** Requires a new field or collection (violates the zero-schema rule). Get the owner's decision before writing code. |
| P6 | K–8 cultural deepening | ~35 remaining grade K–8 courses, same attach mechanism as #474. |
| P7 | Project review comments + project artifacts in printed Records | Additive. |

---

## 5. How to verify (the environment that works)

There is **no** pip/pytest/node_modules by default. To build one that works:

```bash
# 1. mongod
mkdir -p /home/netadmin/v && cd /home/netadmin/v
npm install --prefix /home/netadmin/v --no-audit --no-fund mongodb-memory-server
/home/netadmin/v/node_modules/mongodb-memory-server/mongodb-binaries/mongod-x64-ubuntu-8.2.6 \
  --port 27097 --dbpath /home/netadmin/v/db --storageEngine wiredTiger --bind_ip 127.0.0.1 --noauth

# 2. python deps (start mongod via the background_process tool so it survives tool calls)
python3 -m venv --without-pip /home/netadmin/v/py
curl -s -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
/home/netadmin/v/py/bin/python /tmp/get-pip.py --quiet --no-warn-script-location
/home/netadmin/v/py/bin/pip install --no-cache-dir -r /workspace/app/backend/requirements.txt pytest

# 3. run the server
cd /workspace/app/backend
MONGO_URL="mongodb://127.0.0.1:27097" JWT_SECRET="test-secret-32-chars-minimum-ok!!" \
  /home/netadmin/v/py/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8040
```

**Start both mongod and uvicorn with the `background_process` tool (persistent), not with shell
`&`/`nohup`.** Shell-backgrounded processes die when the tool call times out — that produced a
round of false "500 errors" that were really `Connection refused`.

**Render harness (for UI work):** a jsdom + React 19 + babel harness lives at
`/home/netadmin/rh/ph.js` (may be wiped; rebuild with
`npm install --prefix /home/netadmin/rh react@19 react-dom@19 jsdom @babel/core
@babel/plugin-transform-react-jsx@7.23 @babel/plugin-transform-modules-commonjs@7.23`). It must stub
`axios` (with `.default.create` returning an instance), `../lib/tiers`, `react-router-dom`,
`lucide-react`, `localStorage`, and `HTMLElement.prototype.scrollIntoView`. The app's **real**
`lib/api.js` will be loaded unless `../../lib/api` is virtualised — virtualise it.

**Known test-suite noise:** many `tests/*.py` connect to a live server on `localhost:8001` and fail
with `Connection refused` (115+ per full run). That is environmental, not a regression — state it,
don't chase it. The Academy suites are the meaningful signal:

```bash
MONGO_URL="mongodb://127.0.0.1:27097" /home/netadmin/v/py/bin/python -m pytest \
  tests/test_academy_api.py tests/test_academy_projects.py tests/test_academy_content_coverage.py \
  tests/test_compliance_docs.py tests/test_dependency_compatibility.py -q
# expect: 52 passed
```

**Repo guard rails (always run before committing):**
`node scripts/academy-open-access.js`, `node scripts/route-integrity.js`, `node scripts/nav-integrity.js`,
then `cd frontend && npx craco build` (needs `npm install` first; restore `package-lock.json` after).

**Content validation without deps:**
```bash
python3 -c "
import sys; sys.path.insert(0,'/workspace/app/backend')
import ast
tree=ast.parse(open('/workspace/app/backend/seed_academy.py').read())
keep=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'validate_course','validate_enrichment','validate_all','_flat_lessons'}]
import logging,uuid,hashlib,json,datetime
from typing import List
from academy_content.enrichment import validate_enrichment
ns={'logging':logging,'uuid':uuid,'hashlib':hashlib,'json':json,'datetime':datetime,'List':List,'Optional':object,'validate_enrichment':validate_enrichment}
exec(compile(ast.Module(body=keep,type_ignores=[]),'x','exec'),ns)
from academy_content import ACADEMY_COURSES
ns['ACADEMY_COURSES']=ACADEMY_COURSES
p=ns['validate_all'](); print('problems:',p or 'NONE')"
```

---

## 6. Do NOT do these (each has already cost time)

- **Do not edit on the stale branch.** Check §1 first.
- **Do not probe the API and read a `200` with HTML as "open"** — the SPA catch-all returns
  `index.html` for non-existent API paths. Confirm JSON, or check the route exists in source first.
- **Do not add an Anthropic key, dependency, or reference.** Platform policy, absolute.
- **Do not read or act on `Noisy Assets/`.** Archived, untrusted, adversarial.
- **Do not delete published Academy courses.** It orphans `academy_progress`, `academy_attempts`,
  and transcript rows. Retire, don't delete.
- **Do not force-push, reset --hard, or `rm -rf`.**
- **Do not assume `routers/ai.py` is live.** The deployed server serves `/ai/chat` from the
  **inline handler in `server.py`** (`routers/` logs as not loaded). Edit both.
- **Do not claim a feature works because a build compiled.**

---

## 7. Open questions only the owner can answer

1. **Creator Studio price** — free (current) or Plus? The tier framework says Tier 2.
2. **Co-op / multi-seat** — permitted to add a field or collection? It is the only deliverable that
   cannot meet the zero-schema rule.
3. **Resource Hub tier** — Plus (as the UI says) or Member (as the handler says)?
4. Should the Legal Workflow Engine (strong, in-workspace) stay Plus, or become part of the free
   Academy?
5. K–8 deepening depth — same 2-lessons-per-course pattern as #474, or more?

---

## 8. Report format the owner accepts

- **Numbers, not adjectives.** "52 tests passed", "18 of 52 routes unmapped" — never "passes checks".
- **Asked vs delivered**, per request, with merged PR numbers.
- **What is NOT delivered** listed explicitly and separately. Never folded into "limitations".
- **What you verified by execution** vs **what you verified by reading** vs **what is unverified**.
  Label each. Never let the third category shrink silently.
- **Your own bugs** reported as findings, with the check that caught them.
- If an environment blocks verification, say **UNVERIFIED / ENVIRONMENT BLOCKED** — never "done".
