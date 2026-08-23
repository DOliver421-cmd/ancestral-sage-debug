# PUBLIC READINESS AUDIT (Phase 20)

**Method:** source inspection + automated route checks this session. No browser/production verification available.

## What an anonymous visitor can actually do (SRC)

1. Browse public pages (see inventory below).
2. Register / login / reset password.
3. Use the **public Helper** (`/helper` page + `POST /api/public/helper/ask`).
4. Use **`POST /api/helper/ask`** — documented as the "authenticated" variant but **requires no auth** (SRC).
5. Read Terms + Privacy, accept cookie consent.
6. View store/courses/creators/community discovery content.
7. **Cannot:** see Dashboard, reach admin/exec pages, use any other AI endpoint, purchase (checkout requires auth), or see premium nav items (Phase 19 nav verified + nav-integrity tests).

## Public page inventory (verified routes, frontend/src/App.js)

`/` · `/login` · `/register` · `/forgot-password` · `/factory-reset` · `/reset-password` · `/helper` · `/app/helper` (auth) · `/plans` · `/help-center` · `/knowledge-base` · `/seshats-hub` · `/more-help-center` · `/classic-tools` · `/classic/:slug` · `/search` · `/site-guide` · `/landing` · `/wai-institute` · `/vonns-saga` · `/supervisor-login` · `/terms` · `/privacy` · `/courses` · `/ascension-protocols` · `/community` · `/creators` · `/modules` · `/modules/:slug` · `/p/:slug` · `/leaderboard` · `/trash-pantheon` · `/internships` · `/store` · `/merch` · `/subscribe` · `/donate` · `/payment/success` · `/payment/cancel` · `/u/:username` · `/trash` · `/welcome` · `/more` · `/more/litigation`

## Anonymous helper teaser — deep dive (SRC)

`POST /api/public/helper/ask` and `POST /api/helper/ask` (routers/ai.py):
- KB-first: `_helper_kb()` returns first; **zero tokens** on a KB match.
- LLM only on no-match, max 512 tokens, persona "helper".
- IP rate limit: **15/min** (`check_rate(f"public_helper:ip:{ip}")` / `helper_ask:ip:`).
- IP budget: `budget_key=f"ip:{ip}"` — per-IP daily budget via `USER_DAILY_TOKEN_CAP` machinery.
- 4000-char question cap; `prompt_guard.assert_message_safe` before processing.
- Exhaustion/degradation: returns curated 211 guidance + generic KB — never a resource-draining dead end.
- **Can it invoke platform-funded AI?** Yes — on a KB miss the LLM call is platform-funded unless the caller has BYOK; it is bounded by the per-IP budget and rate limit, and budget exhaustion short-circuits to KB. That is the deliberate teaser design.

**Verdict: KEEP (as an explicitly bounded teaser) with the following noted for executive decision:** (a) `/api/helper/ask` requires no auth despite its name — either require auth or accept it as a second public surface; (b) confirm the per-IP budget value is appropriate for campaign traffic. **Not changed during this audit** — disposition is an executive decision (KEEP / MODIFY / REMOVE).

## Other findings

- **No dead links:** `scripts/route-integrity.js` → 161 routes, 428 link candidates, all resolve (TEST).
- **No placeholder content** in `src/` (SRC scan).
- SEO: robots.txt, sitemap.xml, description + OG meta present (SRC).
- `supervisor-login` and `/auth/cross-site` are public routes — verify they are intended to be (SRC flag).
- `/trash` and `/trash-pantheon` are public routes named "M.O.R.E. Pantheon" — an unusual public destination; confirm intended (SRC flag).
- Visual/mobile presentation: **BROWSER-BLOCKED**.
