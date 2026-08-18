# Original Tools — Inventory & Restoration Map

**Purpose:** The platform shipped full-featured standalone HTML applications before (and alongside) the React pages. Some React pages were later built as thin shells that lost the original experience. **The originals are never abandoned or deleted.** This document inventories every original HTML file, maps it to its module, and records how it is preserved and launched today.

**Policy:** If a modern page feels thin, the original is one click away. All originals ship inside the frontend build (from `/tools/*` and `/originals/*`) and are launchable in-app at `/classic/{slug}` or full-screen from the hub at `/classic-tools`. Inventory code: `frontend/src/lib/originalTools.js`.

---

## 1. The inventory

| Original file | Module / what it is | Size | Current React route (if any) | Restored at |
|---|---|---|---|---|
| `frontend/public/tools/creators-sanctuary.html` | **Creator's Sanctuary** — the original sanctuary hub linking all Kemetic Digital Empire tools | 105 KB | `/creator-lounge` (React lounge) | `/classic/creators-sanctuary` |
| `frontend/public/tools/djedi-oracle.html` | **WA DJEDI — Kemetic AI Oracle** | 42 KB | — | `/classic/djedi-oracle` |
| `frontend/public/tools/electrical-courses.html` | **Electrical Courses** — circuit design, wiring, solar, safety | 33 KB | `/modules` (course catalog) | `/classic/electrical-courses` |
| `frontend/public/tools/media-strategist.html` | **Media Strategist** — planning & publishing workbench | 42 KB | — | `/classic/media-strategist` |
| `frontend/public/tools/publisher-prime.html` | **Publisher — Book & Content Publishing Empire** | 43 KB | — | `/classic/publisher-prime` |
| `frontend/public/tools/litigation-weapon.html` | **Universal Litigation Weapon** — rights, checklists, damages, templates | 62 KB | `/more/litigation` (gateway page) | `/classic/litigation-weapon` |
| `public/🇺🇸 UNIVERSAL LITIGATION WEAPON v1.html` | **Case Weapon System v3.0** — the original full self-advocacy law toolkit | 63 KB | `/more/litigation` | `/classic/litigation-weapon-v1` |
| `more_help_center.html` | **Original M.O.R.E. Help Center** — ambient audio, chat drawer, mic, persona grid, supervisor tools | 100 KB | `/more-help-center` (React edition) | `/classic/more-help-center` |
| `app/helper/index.html` | **Helper — Authenticated Workspace (original)** | 30 KB | `/app/helper` (React Helper) | `/classic/helper` |
| `public/helper/index.html` | **Helper — Public Edition (original)** | 32 KB | `/helper` | `/classic/helper-public` |
| `backend/sovereign/ui.html` (dup: `app/services/sovereign/ui.html`) | **The Sovereign** — puzzle/points engine & persona home | 13 KB | — | `/classic/sovereign` |
| `backup/supervisor.html` | **The Supervisor** — AI governance, hybrid intelligence | 32 KB | `/supervisor` (Seshats Hub) | `/classic/supervisor` |
| `backup/index.html` | **The Supervisor — WAI Institute (admin dashboard)** | 84 KB | `/admin` (React admin) | `/classic/supervisor-admin` |
| `frontend/public/ancestral-sage-resurrected.html` | **Ancestral Sage — Resurrected** (founding AI persona's original home) | 16 KB | `/ai` (AI Tutor) | `/classic/ancestral-sage` |
| `public/free_tier_index.html` | **Free Sandbox & Resource Hub** | 3 KB | — | `/classic/free-tier-hub` |

## 2. How restoration works

1. **Preserved:** the original files remain in the repo at their original locations (nothing moved, nothing deleted).
2. **Served:** copies ship in the frontend build —
   - already-served originals stay where they are: `/tools/*.html` and `/ancestral-sage-resurrected.html`;
   - stranded originals (repo-root `more_help_center.html`, `backup/*`, `app/helper/`, `backend/sovereign/`, `public/*`) were copied into **`frontend/public/originals/`** so the build serves them at `/originals/*`.
3. **Launched:**
   - **Hub** — `/classic-tools` lists all 15 originals grouped by suite (Creator's Sanctuary, Legal Tools, M.O.R.E. Help Center, Governance, AI).
   - **In-app** — `/classic/{slug}` renders the original full-page inside the platform shell (`frontend/src/pages/LegacyTool.jsx`): title bar, back link, and an **Open full screen** escape hatch. Same proven pattern as the Litigation Weapon gateway.
   - **Full-screen** — every card on the hub also has a direct full-screen link to the raw file.
4. **Discoverable** — the sidebar gains a **Classic Tools** section (hub + key tools); the Site Guide persona and site search know the originals by name.

## 3. Shell pages that now point to their originals

| React page | Status | Original available at |
|---|---|---|
| `Store.jsx` (merch) | Gumroad iframe + membership/donation CTAs; physical merch honestly labeled pending fulfillment | n/a (no original store HTML) |
| `LitigationWeapon.jsx` | Gateway → **embeds the original** via iframe | `/classic/litigation-weapon` + v1 |
| `MoreHelpCenter.jsx` | Modern React edition (search, mission meter, guide) | original preserved at `/classic/more-help-center` |
| `Helper.jsx` | Modern React workspace | originals at `/classic/helper` · `/classic/helper-public` |
| `SeshatsHub.jsx` | Modern supervisor hub | originals at `/classic/supervisor` · `/classic/supervisor-admin` |
| Creator's Sanctuary suite (React) | Modern creator features (lounge, studio, ghost producer) | **all 5 original tools** at `/classic/*` |

## 4. Guardrails

- **Never delete an original HTML file.** If a React page replaces one, the original stays launchable.
- **Never "clean up" `frontend/public/originals/` or `frontend/public/tools/`.** They are part of the shipped product.
- When adding a new original, add it to `frontend/src/lib/originalTools.js` (catalog) and this inventory.
- The originals are standalone apps — they may use CDN fonts/icons and their own styling. They are intentionally not rewritten into React; they are served as-is, which is what preserves their full function.
