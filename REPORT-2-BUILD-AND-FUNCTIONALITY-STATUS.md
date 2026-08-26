# REPORT 2 — Build & Functionality Status (Ground Truth)

**Date:** August 24, 2026 · **Method:** every item below was proven by actually running it this session — building the site, booting the server, loading pages, and sending requests. Nothing is marked "works" from reading code alone. Anything not proven says **UNPROVEN**.

---

## Overall build status

| Check | Result | How it was proven |
|---|---|---|
| Site builds for production | **PASS** | Full production build ran to completion this session |
| Server starts | **PASS** | Server booted and answered requests |
| All 47 server modules load | **PASS** | Each one imported successfully |
| All 45 main pages load without crashing | **PASS** | Each page was actually rendered, including with broken/incomplete data fed to it on purpose |
| Every link resolves | **PASS** | Automatic sweep of all 167 routes — zero dead links |
| Live test suite | **188+ passed** against a running server | The tests that need a filled-in database could NOT run here (no database in this workspace) — those are **UNPROVEN** |

## Core modules

**Store / Commerce — PARTLY WORKING, one critical fix applied today**
- Membership checkout was a **dead end until today**: the system set up the payment correctly and then sent the buyer to a page where purchase is impossible (the payment provider's internal dashboard). Fixed today and proven with simulated provider responses. **A real purchase has NOT yet been completed end-to-end — that is the final proof and it is still outstanding.**
- Donations use the same checkout path and get the same fix.
- The store page itself is an external storefront in a frame; it is not our own catalog.
- Physical merchandise orders are refused by design.

**User Management — WORKING (code-proven), live-data UNPROVEN**
- Sign-up, sign-in, password reset, roles, and account deletion all exist and are wired. The pages render. But no test here has created a real account against a real database — that proof is outstanding.

**Content Delivery — WORKING**
- Courses, lessons, knowledge base, help center, and media all load. Pages survive missing data instead of crashing (hardened today across 10 pages).

**Interactive / Engagement — WORKING**
- Community boards, chat, arcade games, daily puzzles, bands, and the creator studio all render and respond. The two music players on the gateway page are reported broken by the owner — unresolved.

**Admin Controls — WORKING**
- Admin dashboards, member management, audit logs, and system health pages all render. The executive site-report page pulls live system status.

## Core workflows — do they actually execute end-to-end?

| Workflow | Status |
|---|---|
| Click a plan → reach a real payment page | **Fixed today, proven with simulated responses; live purchase still unproven** |
| Pay → account upgraded automatically | **Wired** (payment confirmation updates the account), but never proven with a real payment |
| Sign up → account created → signed in | **UNPROVEN** — needs a real database, which this workspace doesn't have |
| Submit a post / comment | **UNPROVEN** — same reason |
| Buy a creator's digital product → receive it | **Wired** (delivery is automatic on payment), never proven live |

## Sandbox hacks, silent workarounds, and fake-working states — full disclosure

1. **The checkout fallback lie:** if checkout fails because payments aren't set up, the site shows *"Checkout is being set up — redirected to our live storefront"* and sends the buyer to the store page. That message overstates things — it papers over a failure instead of stating it.
2. **Silent AI downgrade:** when no AI keys are active, AI features answer from a built-in knowledge base without telling the user AI is off.
3. **Payments recorded without a person attached:** incoming payment records don't always link to the buyer's account directly; upgrades rely on matching the buyer's email afterward. The buyer's email is now pre-filled at checkout to make that matching reliable — but it is still a match-by-email design.
4. **The server runs without a database** in this workspace and serves empty-but-alive pages instead of saying "database down." A visitor could see a blank-looking site during a real database outage with no error message.
5. **A status-page bug was found and is currently unfixed:** the executive health page labels a system with failures as "degraded" instead of "critical" in one case (the logic reads backwards). It was fixed earlier today and reverted at the owner's instruction along with the rest of the report changes; it needs to be re-applied. *(Superseded: re-applied and verified — see Report 4, defect O2.)*

## Addendum — August 26, 2026 (this session)

This addendum updates the report in place rather than issuing a new file. Findings are split into **verified live** and **fixed in working tree, not deployed** — nothing below claims "works" when it has not shipped.

| Finding | Evidence | Status |
|---|---|---|
| The SPA catch-all returned `index.html` for **every** root path — `/manifest.json`, `/sw.js`, `/clear-sw.js`, `favicon.svg`, `logo-512.png`, `robots.txt`, og images all arrived as `text/html` | Confirmed against the live site: all three returned `200 text/html` with the HTML doctype | **Fixed in working tree; not deployed.** This is the source of the browser's "Manifest: syntax error," the clear-sw MIME refusal, and a service worker that could never register — leaving a stale SW from an older deploy in control (the `chrome-extension` Cache.put error in the console) |
| Vonn's Saga crashed on scene-image upload | The render dereferences `media.audio` while `media` is `undefined` for story nodes without static media; matches the live crash stack (`Cannot read properties of undefined (reading 'audio')`) | **Fixed in working tree; not deployed** (optional chaining at the guard and render) |
| CSP blocked the Premium Services iframe and three inline scripts | Live response header: `script-src 'self'` and `frame-src` without the premium host | **Fixed in working tree; not deployed** — the three inline scripts moved to external files; PostHog's loader host added to `script-src`; the premium host added to `frame-src` |
| Delegation-based IAM console | 18 `/api/iam/*` endpoints live and protected (401 unauthenticated); six screens present in the served bundle | **Live** |
| Premium Services links use the direct `/services` URL | Confirmed in the served bundle (`bolt.host/services` ×2, landing iframe unchanged) | **Live** |
| Store catalog: two $29 AI-authored books with covers, membership cards on `/store`, ebook covers/labels | Working tree only | **Not deployed** |
| Saga media: GridFS URL normalization, immediate post-upload refresh, track playback fix, NAM memory persistence fix | Working tree only | **Not deployed** |

### Deploy-status correction — August 26, 2026 (post-push, `98c79cd`)

The items above footnoted **"fixed in working tree; not deployed."** are now **committed and pushed to `main`** — the root-file serving fix, Saga crash fix, CSP fix, IAM console, Premium Services links, store catalog, and media fixes. They land together on the next Railway deploy. Two findings from earlier are corrected the same way: the executive pipeline/member-project auth+db fixes (`64c3106`, `ac4f003`) and the honest dashboard banner (`1797a26`) are on `main` and deploying.

Newly shipped in `98c79cd` (also deploying):
- **Text-AI provider wiring:** `OPENAI_API_KEY` (OpenAI `gpt-4o-mini`) and `AI_PROVIDER_DEEPSEEK_KEY` (DeepSeek `deepseek-chat`) are now text tiers 1a/1b. They were set in Railway but previously invisible to the chat chain, so text fell straight to keyword KB.
- **Per-tier daily budget:** free 50k base; member +25%, plus +35%, pro +45%, patron +50%. Instructor+ and exec unlimited. Hourly cap untouched. 9/9 budget assertions verified.

Both deploy with the next build. The live site's AI text path only reflects them once that deploy lands and a human confirms an entitled member gets a live answer (there is no prior live proof of that path).
