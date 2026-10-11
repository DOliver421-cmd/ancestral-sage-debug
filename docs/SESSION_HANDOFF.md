# SESSION HANDOFF — 2026-10-11 (Soup enforcement session)

**Repo HEAD at handoff:** see `git log -1` (one commit ahead of `bfe42453` — the
previous session's handoff merge).
**Live target:** `https://charming-analysis-morehelpcenter.up.railway.app`
**Full suite at handoff:** 717 passed / 4 skipped, run twice clean
(`REACT_APP_BACKEND_URL=http://127.0.0.1:8001 DB_NAME=phase0_dev python -m pytest tests/ -q`)

---

## 1. WHAT THIS SESSION SHIPPED

Every item the previous handoff listed as open (its §3.1–§3.5) is now
**implemented, live-verified, and covered by tests**. The decisions were made
by the owner in-session; they are recorded here so nobody re-litigates them.

### 1.1 `ai_chat` is Member + BYOK (was: frontend/backend contradiction)
- `FEATURE_MIN_TIER["ai_chat"] = "member"` (`backend/security/feature_control.py`),
  now agreeing with `frontend/src/lib/tiers.js` **and** the handler's own guard
  (`routers/ai.py:_ai_chat_access`).
- Two carve-outs in `check_user_feature_access` keep the enforceable contract
  honest: an **active BYOK key** satisfies the member requirement, and the
  **keyword knowledge-base Helper** (`/api/ai/helper`) stays free for every
  signed-in account (its handler is documented to serve anonymous visitors too).
- **Verified live** (free demo account): `POST /api/ai/chat` → `403 "requires the
  Member plan"`, `POST /api/ai/helper` → `200` with a KB answer, `POST
  /api/ai/chat` as member → `200`. Anonymous callers never reached the LLM
  surfaces anyway (those handlers require a session).

### 1.2 The daily puzzle is free (was: 403 for every signed-in free account)
- `puzzles` is its own feature at `free`; `sovereign` keeps `executive` and its
  role gate. The puzzle card on the free StudentDashboard had been silently
  rendering nothing (`PuzzleCard.jsx` swallows the error and returns null).
- **Verified live:** `GET /api/puzzles/next` as free → `200` with the real
  puzzle payload; `POST /api/sovereign/chat` as free → `403`.

### 1.3 The Soup's bytes are gated server-side (was: UI-only, raw URLs open)
- `backend/security/soup_gate.py` middleware on `/mini-more-help-center/*`,
  driven by `SOUP_FILE_FEATURES` / `SOUP_MIN_TIER` in `security/feature_control.py`
  (mirroring `originalTools.js` one-for-one). 401 anonymous · 403 wrong tier ·
  404 file-not-in-the-map (never confirms what exists). admin/executive_admin
  bypass everything.
- **Authentication:** no cookie auth existed and the Soup's pages can't send a
  Bearer header (iframe document navigation + read-only original HTML whose
  `fetch()` calls send none). Login/register therefore also issue the same JWT in
  an httpOnly `lce_session` cookie (`security/session_cookie.py`) accepted
  **only** by the Soup gate and the five partner routes.
- **Verified live:** anonymous → `401 JSON`; free account → `403 JSON` on
  `soup-broadcast.html` **and** `hub_client.js`; cookie session → `200` with the
  real 37,687-byte `soup-confusion.html`; SPA routes unaffected.

### 1.4 Unknown `/api/*` answers JSON 404 (was: 200 + SPA HTML)
- `/api/{full_path:path}` registered after every real route; the SPA catch-all
  also refuses `/api` paths. **Verified live:** GET and POST on an unknown
  `/api` path both → `404 application/json {"detail":"Not Found"}`.

### 1.5 The Soup's partner API is real (was: five dead routes → SPA HTML)
- `backend/routers/soup_partner.py` — `POST /api/partner`, `GET|POST /api/config`,
  `POST /api/upload`, `GET /api/memory`, `POST /api/report`.
- Member AI contract (staff, or member+, or active BYOK); answers via the
  platform `llm_gateway`; memory/uploads/config persist per-user in Mongo;
  **no raw provider key is ever stored** (the orphaned Express spec wrote one to
  disk) and **nothing is written to the filesystem**.
- The access gateway accepts the scoped cookie on exactly those five paths
  (nothing else) so the unmodified partner page works.
- **Verified live** via the cookie: config GET/POST 200 (`key_stored: false`,
  the pasted key discarded), memory 200, free account → 403 member message,
  member account → the partner answers (honest `PARTNER_UNAVAILABLE` when the
  server has no AI key, which is the gateway's normal no-key behaviour).

### 1.6 Owner's standing rule, now structural
> "Not one part of the site should be locked away from owner/exec tier. Feature
> control, roles and tiers must be editable by exec control interface. Not a mock."

- Every enforced gate is now in the exec console's `AUTHZ_FEATURES` — the four
  that were missing (`curriculum`, `puzzles`, `studio_full`) plus the three Soup
  keys. `ec_get_authz_matrix` merges `load_soup_tier_requirements` so Soup edits
  show and save.
- `test_every_enforced_feature_is_exec_editable` (new) fails the build if any
  enforced gate is missing from that list. A gate nobody can edit is a lock
  nobody holds the key to.
- Role/tier edits were already real (`db.users` + `token_version` bump + session
  deletion + audit); verified by reading the endpoints, unchanged.

## 2. OWNER DECISIONS RECORDED THIS SESSION (do not re-litigate)

1. AI chat boundary: **member+ or active BYOK**; the keyword-KB helper stays free
   for everyone, including anonymous.
2. Sovereign: **split** — puzzles free, `/api/sovereign/*` executive.
3. Soup bytes: **server-side prefix gate**, authenticated by a **scoped session
   cookie** accepted only by the Soup gate + the five partner routes.
4. Partner API: **platform gateway + Mongo**, no filesystem writes, no stored
   provider keys, no new providers.
5. **If a feature/tier/role rule cannot be clearly defined, there is no policy to
   enforce** — the policy artifact is `docs/TIER_BASELINE.md` and the executable
   definition is `backend/tests/test_soup_and_tier_contracts.py`.

## 3. OPEN ITEMS FOR THE NEXT SESSION

1. **`rule_90211.mp3` is still missing from the repo.** `soup-suno.html`
   references it; it exists nowhere. The gate map includes the asset so it is
   protected the day it appears. **Supplying the file is the owner's — do not
   synthesize it.** (`docs/TIER_BASELINE.md` §5)
2. **Pre-existing broken frontend call sites** (found by
   `scripts/api_frontend_match.py`, NOT caused by this work, not fixed — scope
   discipline): `GET /academy/kinds` (frontend/src/pages/academy/AcademyProjects.jsx)
   and `GET /digital/purchases` (frontend/src/pages/OurLegacy.jsx).
3. **Cold-start flakiness:** one full-suite run in this session failed 44 tests
   purely from state pollution (manual probe traffic tripping the login rate
   limiter mid-suite). Two clean runs afterwards: 717 passed / 4 skipped.
   Re-run before trusting a red suite.
4. `scripts/api_inventory.json` was stale before this session (824 vs 960 actual
   routes); it is regenerated now and committed with this work.

## 4. HOW TO WORK IN THIS ENVIRONMENT (rebuilt 2026-10-11)

The sandbox resets `/home/netadmin/s` between sessions. Rebuild order that works:

```bash
# 1. Python venv with the repo's requirements
mkdir -p /home/netadmin/s && python3 -m venv --without-pip /home/netadmin/s/py
curl -s https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
/home/netadmin/s/py/bin/python /tmp/get-pip.py -q
/home/netadmin/s/py/bin/pip install -q -r backend/requirements.txt

# 2. mongod (use the background_process tool — nohup & gets killed)
cd /home/netadmin/s && npm install mongodb-memory-server
/home/netadmin/s/node_modules/mongodb-memory-server/mongodb-binaries/mongod-x64-ubuntu-8.2.6 \
  --port 27017 --dbpath /home/netadmin/s/db --storageEngine wiredTiger --bind_ip 127.0.0.1 --noauth

# 3. Backend on :8001 (background_process tool, NOT shell &)
cd backend && MONGO_URL=mongodb://127.0.0.1:27017 JWT_SECRET=test-secret-32-chars-minimum-ok!! \
  ENABLE_API_DOCS=1 DB_NAME=phase0_dev KEEP_TEST_DEMOS=1 DEV_RETURN_RESET_TOKEN=1 SERVE_FRONTEND=1 \
  /home/netadmin/s/py/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8001

# 4. Full suite
cd backend && REACT_APP_BACKEND_URL=http://127.0.0.1:8001 DB_NAME=phase0_dev \
  /home/netadmin/s/py/bin/python -m pytest tests/ -q

# 5. Frontend guards + build (craco is a declared devDependency but was absent
#    from node_modules this session — `npm i @craco/craco@^7.1.0` first)
cd frontend && npm run test:routes && npm run test:nav && npm run test:academy-access
cd frontend && CI=false GENERATE_SOURCEMAP=false npx craco build
```

**Version trap, learned the hard way this session:** do NOT "fix" the venv by
pinning `fastapi==0.115.x`/`starlette==0.41.x`. With that pair,
`include_router(prefix=...)` produces doubled prefixes and the whole surface
collapses under `/api`. The repo's code and the deployed Railway app both want
the newer FastAPI/Starlette that `requirements.txt` resolves today
(0.143.0 / 1.7.0). Leave it alone.

Demo accounts (KEEP_TEST_DEMOS=1): `student@lcewai.org` / `Learn@LCE2026`,
`instructor@lcewai.org` / `Teach@LCE2026`, owner seats per `server.py:448-460`.
Manual probe traffic can lock these out for 30 minutes — keep it light.

## 5. VERIFICATION EVIDENCE (this session, local server on :8001)

| Check | Result |
|---|---|
| Anonymous `GET /mini-more-help-center/soup-confusion.html` | 401 `SOUP_GATE_ENFORCED` |
| Free account + cookie, `soup-broadcast.html` / `hub_client.js` | 403 (plus tier) |
| Free account + cookie, `soup-confusion.html` | 200, 37,687 real bytes |
| Unknown file under the Soup prefix | 404 |
| `GET/POST /api/definitely-not-a-route` | 404 `application/json` |
| Free account `GET /api/puzzles/next` | 200, real puzzle |
| Free account `POST /api/sovereign/chat` | 403 |
| Free account `POST /api/ai/chat` / `POST /api/ai/helper` | 403 member / 200 KB |
| Member account `POST /api/ai/chat` (Bearer) | 200 |
| Cookie `GET/POST /api/config`, `GET /api/memory` | 200; `key_stored: false`, pasted key discarded |
| Cookie `POST /api/partner` free / member | 403 member message / partner answers |
| Login response | `Set-Cookie: lce_session=…; HttpOnly; SameSite=lax; Secure` |
| Backend suite (twice) | 717 passed / 4 skipped / 0 failed |
| New contract suite | 26 passed (`tests/test_soup_and_tier_contracts.py`) |
| Frontend guards | route / nav / academy-access all pass |
| CRA build | succeeds; soup assets present in `frontend/build/mini-more-help-center/` |

## 6. WHAT WAS NOT DONE (on purpose)

- The Soup's 16 files were not modified (read-only content; owner rule).
- No Anthropic anything.
- The two pre-existing broken frontend call sites were reported, not fixed.
- `docs/TIER_BASELINE.md` and `API_OPERATIONAL_LEDGER.md` were regenerated in
  the same commit as the code (their own instruction when the surface changes).
