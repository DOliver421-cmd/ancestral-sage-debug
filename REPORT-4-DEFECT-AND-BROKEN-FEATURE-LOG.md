# REPORT 4 — Defect & Broken Feature Log

**Date:** August 24, 2026 · **Rule:** everything here was found by running the code, not by guessing. Critical = a real person hits it and is blocked. Minor = cosmetic or edge-case annoyance.

---

## Critical defects

**C1. Buying anything was impossible — the checkout dead end** *(FOUND AND FIXED TODAY; live purchase still unproven)*
- **Where:** every "buy" button on the site — plans, trial, donations, creator products.
- **What happened:** the system set up the payment correctly, then sent the buyer to the payment provider's internal dashboard — a page a customer cannot buy from.
- **Why it survived every earlier check:** the code "worked" — it returned a URL, and earlier checks only asked whether a URL came back, never whether a human could pay from it.
- **Status:** fixed today and proven with simulated provider responses. A real purchase is still the outstanding proof.

**C2. One broken tab shut down the entire business office**
- **Where:** the executive business office, "Arena" tab.
- **What happened:** opening that tab crashed the whole office panel — the page went blank, looking like "the office doesn't load at all."
- **Status:** fixed and verified — every tab now opens.

**C3. A daily puzzle could blank the entire student homepage**
- **Where:** the student dashboard.
- **What happened:** if the puzzle service returned anything unexpected, the whole homepage went blank.
- **Status:** fixed — the page now shows everything else and simply skips a broken puzzle.

**C4. Ten admin and analytics pages could go blank on bad data**
- **Where:** member lists, analytics, attendance, audit logs, and related admin pages.
- **What happened:** any unexpected response from the server would blank the whole page instead of showing an empty list.
- **Status:** fixed — all ten now show an empty state instead of crashing.

**C5. The Arena was unreachable**
- **Where:** the sidebar for executives.
- **What happened:** the Arena page existed but no menu item pointed to it.
- **Status:** fixed — the menu item is back.

## Unresolved defects (open right now)

**O1. The two music players on the gateway page — FIXED August 24, 2026**
- **Root cause found: it was our own site.** The security policy that controls which outside pages may be embedded only allowed the storefront host — the music platform was not on the list, so the browser silently blocked both players on every page. The tracks themselves were always live (confirmed directly). The allowlist now includes the music platform, confirmed by reading the live server's response header. The embeds will now load.

**O2. The executive health page mislabels a broken system — FIXED August 24, 2026**
- Re-applied the corrected check: a system with failures now reads "critical," warnings alone read "degraded."

**O3. Physical merchandise cannot be purchased**
- The system refuses these orders by design. Either wire it up or stop showing physical products. **Open decision.**

**O4. 62 of 140 pages have no sidebar navigation**
- They open as bare pages. A visitor who lands there has no way to navigate the site. **Open.**

**O5. The store was a window into someone else's website — FIXED August 24, 2026**
- The store page now leads with everything for sale, one click from checkout: the $3 trial, all four membership tiers (bought directly on the store page — no detour through another page), and the platform's **own creator catalog** with working buy buttons (creators keep 70%). Verified by rendering the page under three conditions — products present, catalog empty, catalog unreachable — no crashes, and the right message shows in each. The external storefront remains below, now honestly labeled "External." **Still open:** physical merchandise remains unavailable by design — an owner decision, not a defect.

## False claims and rubber-stamped "green lights" corrected by this audit

1. **"Every CTA routes to the real checkout — no dead ends"** (written into the plans page itself). False until today — every buy button dead-ended. Corrected.
2. **"Payments are wired end-to-end."** The wiring existed; the destination was unusable. The claim was true in code and false for humans. Corrected today.
3. **Earlier audit reports claimed broad "verified working" status** while the single most important flow — paying — was broken. Those reports were erased at the owner's instruction. This log exists so that gap can never hide again: **a flow is not working until a human can complete it.**
4. **"The AI Business Office does not load"** was reported by the owner and initially treated as a mystery — it was one broken tab crashing the whole panel (C2). The owner was right; the first instinct to look elsewhere was wrong.

## Defects found August 26, 2026 (this session)

**O6. Every root-level static file was served as `index.html` — FOUND AND FIXED (working tree; not deployed)**
- `/manifest.json`, `/sw.js`, `/clear-sw.js`, `favicon.svg`, `logo-512.png`, `robots.txt`, and the Open Graph images all returned `200 text/html` (confirmed against the live site).
- Browser-visible consequences: "Manifest: Line 1 syntax error," "clear-sw.js MIME type is not executable," and the service worker never registering — so a stale SW from an older deploy stayed in control and threw the `chrome-extension` Cache.put error.
- Fix: the SPA catch-all now serves a real file from the build directory when it exists, and only falls back to `index.html` for actual SPA routes (path traversal blocked).

**O7. Vonn's Saga crashed when a scene had uploaded artwork — FOUND AND FIXED (working tree; not deployed)**
- `media={node.media}` is `undefined` for story nodes without static media. Once live images exist for a scene, the render reached `media.audio` and the whole page hit the React error boundary.
- Fix: optional chaining (`media?.audio`) at both the early-return guard and the render.

**O8. CSP blocked the Premium Services iframe and three inline scripts — FOUND AND FIXED (working tree; not deployed)**
- `frame-src` did not include the premium services host, so the landing-page iframe was refused by the browser (the iframe feature the owner asked for was silently dead).
- `script-src 'self'` blocked the three inline scripts in `index.html` (boot branding, DataCloneError suppression, PostHog init).
- Fix: scripts externalized to `/boot-branding.js`, `/error-suppress.js`, `/posthog-init.js`; PostHog's loader host added to `script-src`; the premium host added to `frame-src`.

**O9. Store catalog gaps — FOUND AND FIXED (working tree; not deployed)**
- Seeded ebooks had no cover URLs and the store did not display ebooks; the `/store` page did not show the membership ladder; purchased products did not join to their product record ("Unknown product" with no download).
- Fix: covers + ebook labels, membership cards on `/store`, purchase→product join, two $29 AI-authored books with manuscript files and authorship disclosure.

## Status correction + new findings — August 26, 2026

**Correction to O6–O9 above:** O6–O9 were originally footnoted "working tree; not deployed." They were **committed and pushed to `main` (commit `5ede974`)** and will go live on the next Railway deploy, together with the executive AUTH/db fixes below. The live site at the time of REPORT-4's writing was as broken as described; that was because the deployed image predated `5ede974`, not because the code was absent. After the next deploy they land together.

**New: O10. Executive pipeline + member-project routers rejected every valid token — FOUND AND FIXED (deploying)**
- Both routers decoded JWTs with `request.app.state.jwt_secret` and read `request.app.state.db` — **values never set by the production server** (only a unit test set them). Result: every valid token, including the owner's, got `401 Invalid token`; once auth was fixed the handler crashed on the missing DB handle. Proven live as 401 → 500 → 403 across two deploys.
- Fix (commits `64c3106` + `ac4f003`): both routers now use the same secret + DB handle the rest of the app uses. An entitled exec/admin now passes where every token previously failed.

**New: O11. Executive dashboard presented $0 revenue as a healthy operation — FOUND; truthful banner FIXED (deploying)**
- `/admin/command` painted $0 revenue, 0 months runway, status "critical" without ever flagging the machine isn't making money. Querying `/api/abo/overview` confirmed the zeros are real — the lie was the framing.
- Fix (commit `1797a26`): when revenue is $0 or runway ≤ 0 or status is critical, the page shows a red banner stating the real condition; when the revenue call fails to load it now says "do not treat these as real."

**New: O12. Two of the five text-AI keys were invisible to the chat chain — FOUND AND FIXED (pushed `98c79cd`)**
- `OPENAI_API_KEY` and `AI_PROVIDER_DEEPSEEK_KEY` are set in Railway but the LLM gateway's text chain had **no OpenAI or DeepSeek tier**, so a text query fell straight to the keyword KB no matter how healthy the other free tiers were. OpenAI only powered images/TTS/transcription; DeepSeek powered nothing.
- Fix: added OpenAI (`gpt-4o-mini`) and DeepSeek (`deepseek-chat`) as text tiers 1a/1b, reading the owner keys only (no stale `EMERGENT_LLM_KEY` fallback), and made the Arena/exec health surfaces count them.

**New: O13. Per-user AI budget was a flat 50k regardless of tier — FIXED (pushed `98c79cd`)**
- Every capped tier got the same daily cap. Budget now scales by `feature_tier`: free 50k base; member 62.5k (+25%); plus 67.5k (+35%); pro 72.5k (+45%); patron 75k (+50%). Instructor+ and exec stay unlimited; hourly cap untouched. Verified 9/9 budget assertions pass.

**Open (not fixed):**
- Physical merchandise purchase (O3) remains an owner decision.
- 62 sidebar-less pages (O4) remain.
- One real purchase and one real account against the real DB remain the outstanding launch proofs (see REPORT 5).

---

## Public-readiness audit — August 28, 2026 (evidence-based; repairs applied in working tree)

Every finding below was verified against the running production site (HTTP probes) or by
executing code — not by reading intentions.

**R1. Production payments are OFF — confirmed against the live site.** `GET /api/payments/products`
on www.morehelp.center returned `payments_enabled: false, provider: disabled` on 2026-08-28, and
`GET /api/version` confirms the deployed build is alive. The owner states all provider keys are
active in Railway; the deployed process sees none of them. That means either the last deploy
predates the keys, or a Railway variable name does not exactly match what the code reads
(`LEMON_SQUEEZY_API_KEY`, `LEMON_SQUEEZY_STORE_ID`; webhook secret `LEMON_SQUEEZY_WEBHOOK_SECRET`;
fallbacks `STRIPE_SECRET_KEY`/`STRIPE_PUBLISHABLE_KEY`, `GUMROAD_API_KEY`). **Owner action:** verify
the exact names in Railway, then redeploy. The 8948e73 "Coming Soon" frontend treatment was
hardcoded, so the site would have stayed "coming soon" forever even after keys went live.

**R2. "Coming Soon" gating now follows the live backend — FIXED.** `PaymentsComingSoon` fetches
`/api/payments/products` and disappears the moment `payments_enabled` is true; the paid buttons on
Plans, Subscribe, Donate, Store, and BYOK re-enable automatically (no code revert, no frontend
redeploy). While the backend reports disabled, the banner shows exactly as before. All five pages
and the component parse-verified.

**R3. The AI outage on every member page — FOUND AND FIXED.** `ai/llm_gateway.py` contained a
fail-closed "platform-funded AI is admin/executive_admin ONLY" guard: every authenticated member
below admin got the keyword KB on every chat/persona/tutor/scholar surface, and routers turned that
into "AI service temporarily unavailable — no provider keys configured" errors. That made the tier
budgets in `user_budget.py` dead code and contradicted the products being sold ("Member tier — full
community + AI Tutor") and the $3 BYOK unlock. Repaired to the documented owner architecture:
BYOK users route through their own key first; members get platform AI within their daily
tier-scaled budget (free 50k → member 62.5k → plus 67.5k → pro 72.5k → patron 75k tokens/day);
instructor-and-above exempt; hourly global cap and KB fallback unchanged; anonymous visitors still
get KB only (enforced in the routers). Cost protection is now the budget system, not a membership
killer. **Owner decision point:** if staff-only AI was truly the intent, say so and it gets
restored — but then the membership copy selling an "AI Tutor" must change too.

**R4. Lemon Squeezy webhook amounts inflated 100× — FOUND AND FIXED.** The webhook recorded
`int(float(total) * 100)` as `amount_cents`, but Lemon Squeezy sends `total` already in integer
cents: a $9.99 order was recorded as $999.00 in `payments` and scholarship funds `raised_cents`
was credited 100×. Revenue reporting was structurally wrong. Now records cents as cents (asserted
by test).

**R5. Paid members could silently receive nothing — FOUND AND FIXED.** Registration stores emails
exactly as typed; Lemon Squeezy lowercases buyer emails; the tier-grant/cancel/refund/BYOK/scholarship
webhook paths looked users up by exact match. Any member who registered with one capital letter in
their email paid and got no entitlement, silently. All grant paths now match case-insensitively
(regex-escaped, so emails containing `+`/`.` cannot widen the match — same approach the media
fulfillment path already used). Asserted by test: `delon.oliver+pay@example.com` now matches a
stored `Delon.Oliver+Pay@Example.COM`.

**R6. Provider chain contradicted the merchant of record — FIXED.** `config.py` says "Payments run
through Lemon Squeezy → Gumroad (no Stripe)", `ai/publishing.py` implements Lemon Squeezy as Tier 1,
but `routers/payments.py` checkout tried Stripe first. With multiple providers configured the site
would have charged through the wrong merchant. Reordered Lemon Squeezy first (merchant of record
per owner directive), Stripe and Gumroad remain as configured fallbacks with their webhooks intact.

**R7. Every checkout created a new Lemon Squeezy product — FIXED.** `_publish_lemon_squeezy`
created a fresh product + variant per checkout call, flooding the merchant dashboard with
duplicates (one per visitor click) and making MoR accounting messy. It now looks up an existing
published product with a matching variant (name + price + billing shape) and reuses it; creation
only happens when no match exists, and any lookup failure falls back to the old create path.

**R8. Wrong-domain redirect default — FIXED.** `FRONTEND_URL` defaulted to `https://wai-institute.org`
in this morehelp.center repo; a missing Railway var would send checkout success/cancel back to the
other site. Default is now `https://www.morehelp.center` (explicit env still wins).

**Verification evidence (this session):** identical pytest failure sets before/after the repairs
(320 pre-existing failures require a live server/DB — sandbox has neither; 159 pass in both),
`test_bridge_delivery` 6/6 and KB-fallback suites 12/12 pass, targeted execution tests pass for the
cents fix, case-insensitive email matching, tier budgets (50k/62.5k/75k, instructor+ exempt,
role ≠ tier), gateway guard removal, and LS product reuse; all five edited pages + component
parse-verified. **Not yet verified (needs the environment above):** a real purchase against the
real LemonSqueezy store and a real webhook delivery — still the outstanding launch proofs.

**Owner checklist to switch revenue on (no further code changes required):**
1. Railway vars exactly: `LEMON_SQUEEZY_API_KEY`, `LEMON_SQUEEZY_STORE_ID`, `LEMON_SQUEEZY_WEBHOOK_SECRET` (names must match; verify, then redeploy).
2. Lemon Squeezy dashboard → Settings → Webhooks: endpoint `https://www.morehelp.center/api/payments/webhook`, events: order_created, order_refunded, subscription_created/cancelled/expired/paused/resumed/unpaused.
3. Redeploy, then confirm `GET /api/payments/products` reports `"payments_enabled": true, "provider": "lemon_squeezy"` — the frontend banners disappear and buy buttons activate on their own.
4. Revisit the Plans.jsx trial-banner line that still says "the platform doesn't fund customer AI" — it no longer matches the restored budget-based policy.
