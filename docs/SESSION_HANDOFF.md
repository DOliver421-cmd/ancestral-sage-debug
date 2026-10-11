# SESSION HANDOFF — 2026-10-11

**State:** everything merged and live. No open PRs. `origin/main` = `badf35ed`.
**Live target:** https://charming-analysis-morehelpcenter.up.railway.app (auto-deploys from `main`; expect ~5 minutes between merge and deploy).
**Read this before touching anything.** The owner has been burned by agents that claimed delivery without executing, so every claim below is marked with how it was verified.

---

## 1. WHAT IS DONE AND VERIFIED LIVE

| # | Item | State | Verified by |
|---|---|---|---|
| 1 | Enrollment atomicity (R2 / defect #20) | Merged | 8-round × 3-writer loop: old code lost 8/8, fixed code 0/8 |
| 2 | Artifact save atomicity (R3 / #21) | Merged | same loop: old 6/6 loss, fixed 0/6 |
| 3 | NAM knowledge seed on real DBs (R4 / #22) | Merged + **live** | `/api/health` → `nam_knowledge_seed: {failed: 0, skipped: 31}` |
| 4 | Legal Workflow Engine account sync (R1 / #19) | Merged | JSON POST 201 (was 422), state round-trips, family isolation |
| 5 | In-product Resource Hub guides (R5 / #23) | Merged | guides return 8 verbatim steps; idempotent upsert upgrades existing rows |
| 6 | Creator Studio is paid: `studio: member`, Song+Publish `plus` | Merged | free 403 / member 200 base + 403 full / plus 200 both |
| 7 | Module content is Plus (`courses`) | Merged | free 403 / member 403 / plus 200; catalogue listing stays 200 for all |
| 8 | `DELETE /api/admin/users/{uid}` registered + typed | Merged | was 405 on four admin screens; the untyped `request` param was a 422 |
| 9 | Ancestral Sage prompt hash restored | Merged | `ok=false, restricted=true` → `ok=true, restricted=false` |
| 10 | Boot honesty (R9/R10) + route-policy 503 outage | Merged | loud WARNING with per-item reasons; PATCH /auth/me back to 200 |
| 11 | Test suite green | Merged | **691 passed, 0 failed** (see §5 for the fresh-DB caveat) |
| 12 | Anonymous `/media/file/` downloads closed | Merged | live anonymous → 401; owner → 200 with bytes |
| 13 | **The Soup is reachable and tier-gated** | Merged + **live** | live serves the real 30624-byte file (was the 2748-byte SPA page) |
| 14 | `docs/TIER_BASELINE.md` | Merged | tier table + plan-phase status + open items |

Live spot-check (run it yourself, it takes 10 seconds):

```bash
B=https://charming-analysis-morehelpcenter.up.railway.app
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' $B/mini-more-help-center/soup-index.html   # 200 30624
curl -s $B/api/health | head -c 200
```

---

## 2. THE TIER BASELINE — read `docs/TIER_BASELINE.md`, it is the source of truth

`free (0) → member (1, $9/mo) → plus (2, $15/mo) → pro (3) → patron (4) → executive (5)`

- **Free signed-in:** Academy (courses, projects, portfolio, compliance — the "$0 doorway" stays free), curriculum catalogue listing, and the Soup's **Confusion Engine + SEE Through Black**.
- **Member $9:** AI chat, posts, lounge, projects, **Creator Studio Beat + Keys**, and the Soup manual/pantheon/games/training/60-tactics/calendar.
- **Plus $15:** module content, progress, labs, credentials; **Song Arrangement + Publish** (the full studio); tracks, band, publisher, earnings, payouts; the Resource Hub; the Soup production suite (broadcast, distribution, publisher, media, partner, Suno, workshop).
- **Anonymous:** marketing pages, the catalogue listing, `/api/health`, and nothing else. No AI chat, no templates, no file bytes, no Soup.

Where the gates live (three places, all must agree):
1. `backend/security/feature_control.py` — `FEATURE_MIN_TIER` + `FEATURE_API_PATHS` (**API enforcement**).
2. `frontend/src/lib/tiers.js` — `TIER_FOR_FEATURE` (**what the UI reads**).
3. `frontend/src/App.js` — `<TierGate feature="...">` per route, and `originalTools.js` `feature:` per original tool.

---

## 3. OPEN ITEMS — the actual to-do list, in priority order

### 3.1 The Soup gate is UI-only, not server-side ⚠️ most important
The 16 Soup files are static assets under `frontend/public/mini-more-help-center/`, so **their raw URLs are reachable by anyone, logged in or not**:

```
curl -o /dev/null -w '%{http_code}\n' $B/mini-more-help-center/soup-broadcast.html   # 200 — no auth asked
```

The tier gate is enforced in `frontend/src/pages/LegacyTool.jsx` at `/classic/:slug` (verified by jsdom render: a member cannot open the Plus-only partner chat, no iframe is built). But the file itself has no server-side check. **This is not "done" until someone cannot fetch the bytes without entitlement.** Options: serve the Soup through an authenticated route instead of static assets, or add a server-side check on those prefixes. Flag this to the owner as a decision, not a silent choice.

### 3.2 `ai_chat` contradicts itself in the code
`frontend/src/lib/tiers.js` says `member`; `backend/security/feature_control.py` says `free`. The backend enforces the API call, so **an anonymous caller can reach AI chat today** while the UI implies Member. One decision needed; then change both maps.

### 3.3 The Sovereign engine is still `executive`
`FEATURE_MIN_TIER["sovereign"] = "executive"`, and `routers/auth.py:282` requires `executive_admin` on `/api/sovereign/chat`. Verified: `GET /api/puzzles/next` and `POST /api/sovereign/chat` → **403 "requires the Executive plan"** for free, member *and* plus. The owner's stated model puts paid game surfaces in the paid tiers, so this is likely wrong — **ask before changing it.**

### 3.4 `/api/*` unknown paths return 200 HTML
Verified live: `GET /api/definitely-not-a-route` → **200 `text/html`**, the SPA page. Owner-approved (decision #3, R8) to return JSON 404/405. **Not implemented.** Until it is, every endpoint probe lies — including any check of whether a Soup API exists.

### 3.5 The Soup partner chat has no backend
`mini-more-help-center/soup-partner.html` calls `/api/partner`, `/api/config`, `/api/memory`, `/api/upload`, `/api/report` — served live today by HTML, not JSON (consequence of 3.4). The spec for those routes exists in the orphaned `Mini More Help Center/server.js` (259 lines, Express, port 3000), which nothing runs. Port those five into `routers/` to make the partner real.

### 3.6 `rule_90211.mp3` does not exist
`mini-more-help-center/soup-suno.html` references it; it is nowhere in the repo. Pre-existing, the file was not modified. Needs the actual audio asset from the owner.

### 3.7 Remaining plan phases (from `docs/WORKING_PLAN.md`)
Phase 1 credential engine, Phase 2–3 API key gateway (G2–G7, design in `docs/API_KEY_GATEWAY_PLAN.md`), Phase 5 co-op schema/monetisation. Not started.

---

## 4. HOW TO WORK IN THIS REPO (learned the hard way)

**The sandbox resets and wipes `/home/netadmin/s` and `frontend/node_modules`.** Rebuild before verifying:

```bash
# mongod (needed by the tests and the app)
mkdir -p /home/netadmin/s && cd /home/netadmin/s && npm install mongodb-memory-server
/home/netadmin/s/node_modules/mongodb-memory-server/mongodb-binaries/mongod-x64-ubuntu-8.2.6 \
  --port 27017 --dbpath /home/netadmin/s/db --storageEngine wiredTiger --bind_ip 127.0.0.1 --noauth

# python deps (requirements now includes pytest + pytest-asyncio — don't install them by hand)
python3 -m venv --without-pip /home/netadmin/s/py
curl -s -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py && /home/netadmin/s/py/bin/python /tmp/get-pip.py -q
/home/netadmin/s/py/bin/pip install -r /workspace/app/backend/requirements.txt

# server — the test suite needs ALL of these
cd /workspace/app/backend && MONGO_URL=mongodb://127.0.0.1:27017 JWT_SECRET=test-secret-32-chars-minimum-ok!! \
  ENABLE_API_DOCS=1 DB_NAME=phase0_dev KEEP_TEST_DEMOS=1 DEV_RETURN_RESET_TOKEN=1 SERVE_FRONTEND=1 \
  /home/netadmin/s/py/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8001

# react render harness (for verifying real components)
mkdir -p /home/netadmin/rh && cd /home/netadmin/rh && npm install react@19 react-dom@19 jsdom \
  @babel/core @babel/plugin-transform-react-jsx @babel/plugin-transform-modules-commonjs
# run a harness with: NODE_PATH=/home/netadmin/rh/node_modules node /tmp/<harness>.js
```

**Starting the server with `background_process` works; `nohup ... &` gets killed when the bash call times out.** Use `background_process` with `ready.pattern: "Application startup complete"`.

**Verify against a *running* server after editing backend files** — Python won't reload a long-running uvicorn. Compare `ps -o lstart` with the file's `stat -c %y` before believing any probe result (this has already produced one false reading this session).

**To prove a fix is real, run the failing thing against the OLD code first.** Stash, restart the server, re-run, unstash, restart. The R2/R3 PRs did exactly this ("old 8/8 loss → fixed 0/8").

**Guard rails (dependency-free, always run before committing):**
```bash
cd /workspace/app
node frontend/scripts/academy-open-access.js   # Academy must never link to a paywalled route
node frontend/scripts/route-integrity.js       # every registered tool path must exist in public/
node frontend/scripts/nav-integrity.js
cd frontend && CI=false npx craco build
```

**Never disable or skip a check. The owner treats a skipped check as bad code.**

---

## 5. THE TEST SUITE — its honest state

`cd backend && REACT_APP_BACKEND_URL=http://127.0.0.1:8001 DB_NAME=phase0_dev python -m pytest tests/ -q`

- On a warm database: **691 passed, 4 skipped, 0 failed.** The 4 skips are TTS tests needing a live AI provider; they skip with a stated reason rather than failing.
- On a **fresh** database: ~23 failures, all cross-suite state/rate-limit artefacts. `python -m pytest tests/test_lcewai.py -q` passes 50/50 on the same fresh DB. This flakiness is **not fixed** — it is the next thing to harden if the owner wants a cold-start green run.
- Two suites fight over `MORE_ROLLBACK_WEBHOOK_SECRET` (module-level `setdefault`); both now set their own values per test via `monkeypatch`. If you add a suite that needs an env var, follow that pattern.
- `tests/conftest.py` contains: the login pacer (18 per 60s window, because the platform caps login at 20/min/IP), `ensure_lcewai_demo_accounts()` (a suite can delete a shared demo account mid-run), the cached `login_body`/`login_token` helpers, and the `pytest.ini` `asyncio_mode = auto`.

---

## 6. THINGS THAT WILL BITE YOU

1. **The owner's standing rules** (from `AGENTS.md`, read it):
   - Never claim done without executing the user path. "Implemented" is not "working".
   - Pre-existing is **not** a reason to leave something broken.
   - A new gate that blocks an intended workflow is a bug, not a feature.
   - No Anthropic, ever, in any form.
   - The Soup and its originals are **read-only content** — do not modify, condense, or "improve" the files. The Confusion Engine's design is intentional.
   - Merge via PR after the review check passes; never push straight to `main`.
2. **`frontend/package-lock.json`** shows up modified after every `npm install` — revert it before committing (`git checkout -- frontend/package-lock.json`).
3. **`pytest-randomly` is installed** — the suite runs in random order by default. If a test passes alone but fails in a run, it is an order/state dependency, and both rollback suites already hit this.
4. **`Mini More Help Center/` at the repo root is the Soup's source of truth**; `frontend/public/mini-more-help-center/` is the built copy. If you edit one, regenerate the other (and say so in the PR).
5. The **`server.js`** in that folder is an orphaned Express server — it is the spec for the partner API, not running code.

---

## 7. EXACT NEXT STEPS FOR THE NEW SESSION

1. Confirm `git log --oneline -1` is at or ahead of `badf35ed`, and that live `/api/health` is operational.
2. Ask the owner to rule on the three decisions in §3.1–§3.3: **the Soup gate's server-side enforcement**, the **`ai_chat`** boundary, and the **Sovereign engine's tier**.
3. On approval, implement **§3.2 + §3.3** first — both are one-line tier changes in two maps plus their guards, and both are verifiable in minutes with the tier probe pattern in §2.
4. Then **§3.4** (JSON 404/405 for `/api/*`) — approved already, unblocks §3.5, and stops endpoint probes from lying.
5. Then **§3.1** — the only way the Soup's tiers are actually enforced rather than decorative.
6. The `rule_90211.mp3` asset (§3.6) must come from the owner; do not synthesise it.
7. If the owner wants a cold-start green suite, tackle §5's flakiness before adding any new test.
