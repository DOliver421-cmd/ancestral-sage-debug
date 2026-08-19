# HANDOFF — to the WAI Institute repo session ("new you")

**Paste this document at the start of the next session working on the WAI Institute side**
(Lovable app, source repo `DOliver421-cmd/ancestral-sage-debug` — this repo — Railway
projects `charming-analysis` (morehelp.center) and the WAI production build on
`wai-institute.org`).

**Written by:** previous session (Freebuff agent), 2026-08-19
**For:** the next AI coder working on the WAI deployment / repo — to know what exists,
what was delivered, and exactly what gaps are still open.

---

## 0. Read first — the human truth & the rules

- The owner paid for a complete platform and has been burned by sessions that deleted
  paid features, shipped empty shells, and claimed work was done when it wasn't.
- **Rules that are non-negotiable:** delete nothing (ask first). Keep solutions FREE-first
  (free LLM tiers, no paid calls without explicit consent). Never call Anthropic or any LLM
  directly — always `call_llm()` from `backend/ai/llm_gateway.py`. Do not modify
  `backend/prompts/` (SHA-256 integrity enforced at runtime). "No human interaction
  required" — automations must work without manual steps.
- **Honesty over agreeableness.** Do not affirm bad decisions. Do not claim a feature
  exists when it does not. If this document doesn't match what you find, say so in your report.
- **Exec-only IP rule (owner's standing instruction):** internal documents, brainstorming,
  theories, exec features, admin/staff non-public-facing features, the Business Office page,
  and book manuscripts are **exec only**. Do not expose intellectual property to the public.
  Anything that renders on the public WAI door must be reviewed for leaks of internal docs.
- **Working tree discipline:** preserve pre-existing user changes, stage only files that
  belong to the current request. This repo's Changes panel (Freebuff) owns commits/pushes —
  only run git delivery commands when explicitly asked.

---

## 1. The one-screen picture (verified reality, not aspiration)

**Two doors, one house — but TODAY they are TWO deployments.**

| Door | Domain | Served by | Status (verified 2026-08-19) |
|---|---|---|---|
| WAI Institute | `www.wai-institute.org` | **A different build** — title "WAI Institute — Three Schools. One Path to Mastery.", not this repo's bundle | HTTP 200, live |
| M.O.R.E. Help Center | `www.morehelp.center` | **This repo's build** (`static/js/main.6fd4476b.js`), API v4.0.1 | HTTP 200, live |

Both domains resolve and answer. **The code in THIS repo is not what serves wai-institute.org.**
The WAI door code below is dormant here by design — it activates the moment DNS points
`wai-institute.org` at this deployment. That is a deployment/DNS decision, not a code fix.

---

## 2. What this session delivered (all committed, working tree clean)

Three commits on top of PR #201 (`main`):

| Commit | Files | Content |
|---|---|---|
| `458e4ef` (5 files) | `frontend/src/lib/domain.js`, `frontend/src/App.js`, `frontend/src/pages/WAIInstitute.jsx`, `frontend/src/components/AppShell.jsx`, `reset_exec_accounts.py` | **Phase A** — domain-aware front door |
| `20d2bf0` (8 files) | `App.js`, `AppShell.jsx`, `BugReportModal.jsx`, `lib/seo.js`, `HelpCenter.jsx`, `KnowledgeBase.jsx`, `Login.jsx`, `Register.jsx` | **Phase B** — support entry points re-targeted; **Phase C** — Knowledge Base + SEO |
| `5cb2b49` (1 file) | `frontend/public/index.html` | Boot-time domain branding snippet |

Canonical plan: `docs/morehelp-migration-blueprint.md` (Phase A–D sequencing).

### Phase A — domain-aware front door
- **`lib/domain.js`** (new): `isWaiDoor()` (hostname contains `wai-institute.org`) and `MORE_HOME = "https://www.morehelp.center"`.
- **`App.js`**: the old hard redirect of every wai-institute.org visitor to
  `https://www.morehelp.center/wai-institute` is **gone**. `/` renders `<WAIInstitute />`
  on the wai door, `<UnifiedGateway />` on the MORE door. `HelpGuide` (floating in-app help
  widget) is suppressed on the WAI door so support links OUT instead.
- **`WAIInstitute.jsx`**: focused institution landing (Classrooms, Administration, AI Tutor,
  Credentials portals). All support/billing/creative CTAs link OUT to morehelp.center.
  Header has a permanent "Help & Support → morehelp.center" link. Fixed a real bug: header
  logo was a router `Link` with an external URL; now an `<a href>`.
- **`AppShell.jsx`**: sidebar is hostname-aware — on the WAI door, core education items stay
  in-app (Home, Dashboard, Learn, AI Tutor, Council, Curriculum, Labs, Lab Sims, Compliance,
  Learning Path, Competencies, Credentials, AAWAB, Business Office, Social Blast, all
  Instructor/Admin/Exec staff sections); profile/position/settings/site-guide/BYOK,
  community, M.O.R.E. hub/chat/helper, classic tools, the creative suite, and ALL commerce
  become outbound links to morehelp.center with an external-link icon. The "M.O.R.E.
  Institute" card flips to an outbound "M.O.R.E. Hub" card.
- **`reset_exec_accounts.py`**: the 3 plaintext exec passwords were **removed** from the file.
  Passwords now come from env (`EXEC_PASSWORD_1/2/3` per seat, or `EXEC_RESET_PASSWORD` for
  all); script refuses to run when any are missing. ⚠️ **The old values are still in git
  history — rotate the passwords regardless.**

### Phase B — support entry points re-targeted (WAI door)
- **`BugReportModal.jsx`**: on the WAI door the floating button becomes **"Get Help —
  M.O.R.E."** linking out to `morehelp.center/help-center`; in-app bug-bounty flow untouched
  on the MORE door.
- **`Login.jsx`**: on the WAI door, "Forgot password?" → `morehelp.center/forgot-password`
  and "Help Center" → `morehelp.center/help-center` (new tab, external-link icon). Unchanged
  on MORE.
- **`Register.jsx`**: same treatment for its "Questions? Help Center" link.

### Phase C — Knowledge Base + per-domain SEO
- **`KnowledgeBase.jsx`** (new, `/knowledge-base`, public): the handbook hub — all 4
  handbooks render in-app as HTML (`/api/handbooks/{student|instructor|admin|persona}`) plus
  Site Guide and Help Center links, and 3 new quick-answer articles: **Browser & Device
  Requirements**, **Where is my certificate?**, **Refunds & Billing**.
- **`lib/seo.js`** (new): `useSeoManager()` — per-route, per-door title/description. WAI door
  targets high-intent technical terms (NFPA 70, NEC 2023, electrical curriculum, credentials);
  MORE door owns support/community/commerce terms. Longest-prefix matching so `/modules/:slug`
  inherits `/modules`. Wired once in `App.js` inside the router. Updates `document.title`,
  description, OG, and Twitter metas + `og:url`.
- **`HelpCenter.jsx`**: added an "Open Knowledge Base" card.
- **`AppShell.jsx`**: "Knowledge Base" added to the M.O.R.E. nav section (in-app on MORE,
  outbound on WAI).
- **`index.html`**: inline boot-time script — if hostname is `wai-institute.org`, rewrites
  title + description/OG/Twitter metas to WAI branding before React mounts (no MORE-branding
  flash; correct default for non-JS crawlers).

### Verification this session
- `npm run build` (craco, same as Dockerfile) — passes.
- Live probes: morehelp.center 200 + `/api/version` 200; wai-institute.org 200 (different build).

---

## 3. Inventory findings (so you don't re-audit)

- **Deployed backend:** FastAPI monolith `backend/server.py` (Dockerfile entrypoint
  `docker-entrypoint.sh` → `uvicorn backend.server:app`, port 8080). `HANDOFF.md` claims
  `app.main:app` — **stale**; the `app/` modular tree is NOT deployed.
- **Database:** MongoDB (Motor). **Not Supabase.** Zero references to project
  `phuymlvvxxvcejyfxwui` anywhere in this repo. The only Supabase code lives in the
  non-deployed `app/` tree (env-gated, in-memory fallback). The two platforms do **not**
  share a database today.
- **Conference-bridge embed:** absent from this repo (`frontend/public/index.html` has no
  `conference-bridge.js` tag). A different mechanism exists: `backend/routers/bridge.py` —
  a cross-domain **API** bridge, not the floating Team Conference panel.
- **Payments (MORE side):** real code — `POST /api/payments/checkout` (Lemon Squeezy tier 1 →
  Gumroad tier 2 → MongoDB archive tier 3; gated by `PAYMENTS_ENABLED` +
  `LEMON_SQUEEZY_API_KEY`+`STORE_ID` or `GUMROAD_API_KEY`). Frontend `/store` (MediaStore →
  `/media/products/:id/checkout`), `/subscribe`, `/donate`, `/plans`, `/sponsor`,
  `/payment/history`. Physical merch returns HTTP 501 (digital-only). **Live checkout depends
  on Railway env keys that cannot be verified from the repo.**
- **Auth:** JWT HS256, RBAC `student(1)/creative_partner/priority_member/instructor(2)/
  site_support(3)/admin(4)/executive_admin(5)` — mirrors `ROLE_RANK` in `App.js` and
  `backend/server.py`. `/business-office` and admin/exec routes are auth-protected. Good.

---

## 4. Gaps to fill — the actual job for the next session (prioritized)

1. **Port Phases A–C to the WAI-serving deployment.** The build serving wai-institute.org
   is NOT this repo. If it's a separate repo/deployment, port the changes above (section 2)
   faithfully — same behavior contract, same file patterns. **This is the single biggest gap.**
2. **Decide the deployment topology.** Two options: (a) point both domains at ONE deployment
   (then this repo's WAI door goes live and the WAI repo's build is retired), or (b) keep the
   split and ensure the WAI deployment carries identical Phase A–C behavior. Get the owner's
   call; don't guess.
3. **Verify payments end-to-end on morehelp.center.** Confirmed live checkout needs Railway
   env: `PAYMENTS_ENABLED=1`, `LEMON_SQUEEZY_API_KEY`, `LEMON_SQUEEZY_STORE_ID` (or
   `GUMROAD_API_KEY`). Run a real test purchase on a digital product. If keys are missing,
   name them — do not claim checkout works.
4. **Rotate the exec passwords.** Old plaintext values are in git history. Set new
   `EXEC_PASSWORD_1/2/3` (or `EXEC_RESET_PASSWORD`) in Railway env, run
   `python reset_exec_accounts.py` from this repo, then discard.
5. **Supabase seam decision.** The original handoff assumed a shared Supabase brain
   (`phuymlvvxxvcejyfxwui`) and a conference-bridge embed on morehelp.center. Neither exists
   in this build. If the WAI platform depends on them, this MORE build is not wired to it —
   confirm whether that's intended or a missing integration.
6. **Conference-bridge embed (if wanted):** add the script tag to `frontend/public/index.html`
   with `data-slug="wai-morehelp-bridge"`, `data-origin="morehelp"`,
   `data-site-url` = the actual deployment URL. Note: the script's src points at the WAI
   Railway host — only meaningful if that host still serves it.
7. **Phase D verification (full):** sign-in per domain (localStorage token is per-domain),
   cross-door help flows land on morehelp.center, CORS for both origins, no in-app support
   widget on the WAI door, commerce absent from WAI nav.
8. **Exec-only leak audit:** walk the public WAI door pages and confirm no internal docs,
   brainstorming, business-office content, or book manuscripts render publicly.
9. **SEO known limit:** title/meta are client-side (helps JS-rendering crawlers + link
   previews). Raw HTML always ships the MORE default until React mounts on morehelp.center —
   prerender/SSR would be needed for full static SEO on both doors. Not built; only if asked.
10. **Handbooks:** in-app HTML exists (`/api/handbooks/*`). Blueprint also calls for
    porting LMS access guides + a browser-requirements article (done in KB) + refunds article
    (done). Remaining content items: "LMS access guides" port and "certificate delivery FAQ"
    (done in KB). Check the WAI-side handbook HTML files for MORE rebranding consistency.

---

## 5. Key commands & file map

```bash
cd backend && python -m server                 # start API (port 8001 local)
cd backend && python -m pytest tests/ -v       # backend tests
cd frontend && npm run build                   # frontend build (craco, like Dockerfile)
python reset_exec_accounts.py                  # exec seat reset (env-driven passwords)
```

Key files (this repo):
- `frontend/src/lib/domain.js` — door detection + MORE_HOME
- `frontend/src/lib/seo.js` — per-route/per-door SEO map
- `frontend/src/App.js` — routes, `/` door split, SeoManager, HelpGuide suppression
- `frontend/src/components/AppShell.jsx` — hostname-aware sidebar (`nl()` in-app / `out()` outbound)
- `frontend/src/pages/WAIInstitute.jsx` — WAI landing
- `frontend/src/pages/KnowledgeBase.jsx` — KB hub
- `frontend/src/pages/HelpCenter.jsx`, `MoreHelpCenter.jsx` — MORE support surfaces
- `backend/server.py` — API monolith (payments, auth, handbooks mount)
- `backend/routers/handbooks.py` — `/api/handbooks/*` HTML
- `backend/routers/bridge.py` — cross-domain API bridge (not the embed)
- `docs/morehelp-migration-blueprint.md` — canonical plan
- `PROPRIETARY_ASSET_PROTECTION.md` — owner's IP stance; respect it

## 6. What NOT to do

- Don't delete/rename pages or features — ask first.
- Don't touch `backend/prompts/`.
- Don't call LLMs directly; use `call_llm()`.
- Don't expose exec-only content (section 0) publicly.
- Don't claim checkout/SEO/verification works without running it.
- Don't commit/push without explicit ask (Changes panel owns delivery).

---

*End of handoff. Deliver 100%, not 31% — and report honestly what matches and what doesn't.*
