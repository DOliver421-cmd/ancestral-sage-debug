# TASK LIST — Owner-Reported Live Failures

**Created:** August 28, 2026 — from Delon Oliver's report (verbatim complaints, not paraphrased into
cosmetic requests). **Updated:** same day, after code-level fixes and live-site probes.
**Rule:** an item is only DONE when the intended user path works on the live site — not when code
exists. Every line states the code reality, the live evidence, and what remains.

---

## 1. `/ascension-protocols` — video embeds do not show ✅ FIXED (code; pending deploy)

- **Root cause (proven):** page embeds YouTube on-site via iframes with real video IDs
  (`rkZlMgsNX-Q`, `dYjwlVkfxAs`, …). The site's CSP `frame-src` allowlist did not include
  `youtube.com` — confirmed in **live production headers** on 2026-08-28 (gumroad/bandcamp/
  premium/railway only, no youtube). Browser silently refused every embed.
- **Fix:** `backend/platform_services.py` `_FRAME_HOSTS` += `https://www.youtube.com` +
  `https://www.youtube-nocookie.com`. Verified: `7/7` platform-services unit tests pass.
- **Remaining:** deploy. Embeds stay on-site (that is already how they render).

## 2. `/dashboard` — "failure in code does not load" ✅ FIXED (code; pending deploy)

- **Root cause (proven against live API):** `GET /api/modules` on the live site returns **12
  modules with NO `competencies` field** (verified by parsing the live response). StudentDashboard
  rendered `m.competencies.length` → throws → **entire dashboard blanks**. This is the failure.
- **Fix:** `frontend/src/pages/StudentDashboard.jsx` now guards `competencies`, `tasks`, `order`,
  `hours` (`(m.competencies || [])`, `String(m.order ?? "")`, …). Same-class guards applied to
  `ModulesList.jsx` and `ModuleView.jsx` (identical landmines). Frontend builds clean.
- **Remaining:** deploy + load the dashboard logged in.

## 3. Personas locked away — "not accessible to human" ✅ FIXED (code; pending deploy)

- **Verified:** the persona directory API (`GET /api/personas`) is public, the `/personas` and
  `/personas/:slug` routes exist with no role gate, and all **20/20** personas have `PERSONA_META`
  (none dropped). The problem was **no nav entry anywhere** — the only path was typing the URL.
- **Fix:** added "AI Team" nav links (`/personas`) for anonymous visitors, customers, and staff in
  `frontend/src/components/AppShell.jsx`. Frontend builds clean.
- **Remaining:** deploy. Human can now reach the persona cards from the sidebar.

## 4. `/jamil` — "no api not working, should be integrated with business office" ⚠️ EXISTS; needs session check

- **Verified:** `POST /api/jamil/chat` is live (auth-gated, not 404). The **integration the owner
  asks for already exists**: the deployed bundle contains "Director Jamil" inside the AI Business
  Office — `frontend/src/pages/MoreOps.jsx` renders the full `<JamilChat embedded />` under
  Business Office → "More Ops" → "Director Jamil" (verified present in the live JS bundle:
  `main.ddb43fc8.js`). `frontend/src/pages/Jamil.jsx` is the full chat UI (files, voice, history).
- **What's left:** an actual logged-in session to confirm the office renders for the owner's
  account. If it doesn't load for them, the next step is capturing the console error from that
  session — code and API both check out.

## 5. `/settings` — "spreads out features to be non working stubs" ⚠️ VERIFIED REAL; UX request open

- **Verified:** all 5 tabs call live endpoints that exist and respond: `/auth/me` (GET/PATCH),
  `/auth/change-password`, `/auth/sessions` (GET/DELETE both), `/auth/account/export`,
  `/auth/account` (DELETE). Confirmed live with HTTP probes (401 = auth gate, not missing).
- **Open:** the consolidation decision — owner wants features on one page instead of tabs. That is
  a deliberate UI rebuild; doing it without being able to test would risk shipping a broken
  replacement. Awaiting owner's go-ahead on the single-page layout.

## 6. `/admin/command` — "working meant changing background and font" ⚠️ REAL PAGE; needs exec login

- **Verified:** page is a real integrated surface: 7 tabs, 9 live endpoint calls (`/exec/system`,
  `/admin/stats`, `/health`, `/abo/overview`, `/abo/agenda`, `/projects`, `/exec/manuals`,
  `/admin/control-panel`, `/admin/users`), briefing compiler, flag toggles, role/tier controls.
  All endpoints exist live (auth-gated). The $0-revenue truth banner fix is committed (`1797a26`).
- **Remaining:** one exec login to walk the panels. Not verifiable without the owner's credentials.

## 7. `/nam` — "total failure in code" ⚠️ REAL CONSOLE; needs session check

- **Verified:** `frontend/src/pages/HybridNam.jsx` is a full 6-tab console; `backend/routers/nam.py`
  implements every endpoint it calls (`identity`, `state`, `constitution`, `memory`, `intentions`,
  `dreams`, `reflections`, `leadership/ledger`, `leadership/review|evaluate`); live probe
  `/api/nam/identity` → 401 (auth gate by design). A dead ternary was corrected.
- **Remaining:** one logged-in visit to `/nam` to capture the real error the owner sees. Code and
  API both check out; the failure cannot be reproduced from here without an account.

## 8. `/social/publish` — "a shell… can not sign into anything via ui" ⚠️ PARTLY TRUE — genuine gap

- **Verified:** compose → AI format per platform (`/api/ai/social-blast`, live) → copy → open
  platform intent links all exist. **What does not exist is platform sign-in/publishing from the
  UI** — no OAuth connect, no server-side post. The owner is right; that part is genuinely absent.
- **Blocked on:** per-platform OAuth developer apps (X, Instagram/Facebook, TikTok, LinkedIn,
  Threads) and their credentials. This cannot be completed from the repo alone. **Needs owner
  decision:** which platform first, and the app credentials — then it is a buildable task.

---

## Environment note (why some items cannot be "verified" from here)

The Freebuff preview cannot complete a login: the app is a React (CRA) frontend + FastAPI backend
+ MongoDB, and the sandbox does not run that stack. Login-gated items (2–7) therefore cannot be
walked end-to-end in this workspace. That is why items 4, 5, 6, 7 remain marked "needs session"
instead of being claimed done — the code is present and the endpoints are live; the human-path
proof requires the owner's account on the real site.
