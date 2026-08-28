# TASK LIST — Owner-Reported Live Failures

**Created:** August 28, 2026 — from Delon Oliver's report (verbatim complaints, not paraphrased into
cosmetic requests).
**Rule:** an item is only DONE when the intended user path works on the live site — not when code
exists. Every line below states the code reality and the missing proof separately.

---

## 1. `/ascension-protocols` — video embeds do not show

- **Owner:** "video imbeds do not show. can this be fixed still keep user on site."
- **Root cause (FOUND + FIXED in code):** the page embeds YouTube players on-site via
  `frontend/src/pages/AscensionProtocols.jsx` (`https://www.youtube.com/embed/<id>` iframes), but
  the site's CSP `frame-src` allowlist in `backend/platform_services.py` did not include
  `youtube.com`, so the browser silently refused every embed. Confirmed against the live site's
  response headers on 2026-08-28: `frame-src` had gumroad/bandcamp/premium-services/railway but
  **no youtube**.
- **Fix (committed to working tree, NOT deployed):** added `https://www.youtube.com` +
  `https://www.youtube-nocookie.com` to `_FRAME_HOSTS`. Verified `7/7` unit tests pass.
- **Done when:** the fix deploys AND the embed visibly plays on the live page.

## 2. `/admin/command` — "working" was cosmetic

- **Owner:** "you clearly translated working to mean just change the background and font… then
  presenting failures to complete task as completed task."
- **Code reality:** `frontend/src/pages/ExecutiveCommandCenter.jsx` is a real page loading 9 live
  endpoints (`/exec/system`, `/admin/stats`, `/health`, `/abo/overview`, `/abo/agenda`,
  `/projects`, `/exec/manuals`, `/admin/control-panel`, `/admin/users`). The $0-revenue / critical
  runway banner fix is committed (`1797a26`) but the exec page has never been verified live with a
  working exec account.
- **Status:** UNVERIFIED. **Needs:** log in as exec on the live site; confirm every panel loads
  real data and the revenue/runway banner tells the truth.

## 3. `/nam` — "total failure in code"

- **Owner:** "total failure in code. need working."
- **Code reality:** `frontend/src/pages/HybridNam.jsx` is a complete console (Overview / Memory /
  Intentions / Dreams / Reflections / Leadership tabs) wired to real `/api/nam/*` endpoints;
  `backend/routers/nam.py` implements every endpoint (identity, state, constitution, memory,
  intentions, dreams, reflections, ledger, evaluate). Live probe: `/api/nam/identity` → 401
  (auth-gated read — by design). Nothing in the code points to a crash.
- **Status:** UNVERIFIED — cannot be judged from code alone. **Needs:** a logged-in user to load
  `/nam` on the live site and confirm each tab renders real state (and the exact error text if it
  doesn't).

## 4. `/settings` — "wasted page… non working stubs"

- **Owner:** "a wasted page that does nothing but spread out its features to be non working stubs
  instead of on same page."
- **Code reality:** `frontend/src/pages/Settings.jsx` has 5 tabs (Profile, Password, Privacy,
  Sessions, Social) all wired to real endpoints (`/auth/me` PATCH, `/auth/change-password`,
  `/auth/sessions`, `/auth/account/export`, `/auth/account` DELETE). Not stubs in code.
- **Status:** partially a live-verification item, partially a UX/consolidation request.
  **Needs:** (a) verify each tab works live with a real account; (b) owner decision on what
  "on same page" consolidation should look like — which features belong on one screen.

## 5. `/dashboard` — "failure in code does not load"

- **Owner:** "failure in code does not load should have features integrated into user profile."
- **Code reality:** `frontend/src/pages/StudentDashboard.jsx` is fully wired (`/modules`,
  `/progress/me`, `/certificates/me`, `/xp/me`, `/partnership/status`) and defensive — one failing
  API cannot blank the page (the C3 puzzle-blank fix). Route is public-to-authenticated at
  `/dashboard`.
- **Status:** UNVERIFIED. **Needs:** load `/dashboard` logged in on the live site; capture the
  actual error (console + network) if it fails, since code inspection shows a guarded page, not a
  guaranteed crash. The "integrate into user profile" part is a product decision.

## 6. `/jamil` — "no api not working"

- **Owner:** "no api not working, should be integrated with AI business office more ops chat
  interface not be a single featureless page with no work flow."
- **Code reality:** the API exists and is live — `POST /api/jamil/chat` returned the auth-gated
  error (not 404) on 2026-08-28. `frontend/src/pages/Jamil.jsx` is a full chat UI (files, voice
  in/out, history sync via `/jamil/history`). It is admin-gated (`/jamil` requires admin) and
  standalone.
- **Status:** API works for entitled users (unverified end-to-end without an admin login).
  **Open feature:** embedding Jamil as an ops-chat inside the AI Business Office
  (`/business-office`) with a workflow, per owner direction. This is a build task, not a bug fix.

## 7. `/social/publish` — "a shell… can not sign into anything via ui"

- **Owner:** "is a shell. its controlls are a shell, can not sign into anything via ui."
- **Code reality:** partial truth. `SocialPublish.jsx` really does: compose → AI format per
  platform (`/api/ai/social-blast`, live, auth-gated) → copy per-platform text → open platform
  web-intent links. What it does NOT do — and the owner is right — is **connect/publish to any
  platform account from the UI**. There is no OAuth connect and no direct post API integration.
- **Status:** PARTIALLY REAL / PARTIALLY SHELL, confirmed. **Needs:** a real social publishing
  integration (OAuth connect per platform + server-side post) — a significant build requiring
  per-platform developer apps, or an explicit owner decision to keep it as a compose-and-share
  tool and label it honestly.

## 8. Personas locked away / AI compliance

- **Owner:** "personas are locked away and not accesible to human. site meet 0 ai compliance in
  reality. if oversight features are mostly shells or failures, the persona cards in source
  protocols are not accessible human."
- **Code reality:** `GET /api/personas` is public and returns the roster; `/personas` +
  `/personas/:slug` routes exist (no role gate — `AdminPage` is layout only). But there is no
  obvious nav entry for regular users, and personas without a `PERSONA_META` entry in
  `backend/routers/ai.py` are silently dropped from the directory.
- **Status:** discoverability + completeness gap. **Needs:** a public persona directory entry in
  navigation, every loaded persona surfaced (or explicitly labeled), and a live walkthrough of the
  oversight surfaces so "human can access the AI team" is true on the site, not just in code.

---

## What is NOT done / cannot be done from this repo alone

- **Deploy:** several committed fixes (CSP YouTube fix above, O6–O16 from REPORT-4, R4–R8) reach
  the live site only after a Railway deploy. The live CSP header still predates this fix.
- **Live verification:** items 2, 3, 4, 5 need a real account on the live site. No credentials are
  available to this session; code inspection cannot substitute for the human path.
- **New integrations:** items 6 and 7 are feature builds (embed Jamil in Business Office; real
  social OAuth publishing) that need owner scope decisions before implementation.
