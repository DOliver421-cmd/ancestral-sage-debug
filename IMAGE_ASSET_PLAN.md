# IMAGE ASSET PLAN

**Date:** August 23, 2026
**Status:** PLAN ONLY — **no image generation executed** (awaiting approval per Phase 17 rule 18)

Stack facts (from IMAGE_CAPABILITY_AUDIT.md, verified 2026-08-23):
- DALL-E 3 generation exists in `backend/tools/architect_tools.py` (`client.images.generate`, model `dall-e-3`), reachable only through the AI handler (`routers/ai.py` dispatch) — already feature-gated.
- Storage: MongoDB GridFS exists (media uploads); static files served from `frontend/public/`.
- Pillow installed but unused for processing.
- No responsive-image component, no feature→image mapping, no admin asset manager yet.

**Cost policy:** static asset files = $0 per request. AI-generated images are COST-BEARING
and will only be produced after explicit approval, governed by the FCC (image generation
is an internal/exec-controlled capability; there is no user-facing generate button).

## Asset inventory — FEATURE → IMAGE ROLE → ASSET

Priorities: **P0** = landing + first impression (highest value), **P1** = primary product
sections, **P2** = polish/OG. Static recommended everywhere a bespoke brand image can be
produced once (or authored as SVG/CSS art — zero cost, infinitely scalable).

| # | Destination | Image role | Spec | Visual concept | Type | Priority |
|---|-------------|-----------|------|----------------|------|----------|
| 1 | Landing hero | hero | 1600×900 (16:9) | Afrocentric sage figure emerging from a cosmic knowledge grid — gold/indigo brand palette | static (SVG/CSS or one-time DALL-E) | P0 |
| 2 | Landing ecosystem strip | 6 ecosystem tiles | 800×450 each | AI / Learn / Create / Community / Music / Games — one consistent art direction per ecosystem | static | P0 |
| 3 | AI Console (/ai) | hero + feature card | 1600×900 + 800×450 | NAM as guiding light — neural constellation with a human silhouette | static | P1 |
| 4 | AI Console personas (Jamil, Council) | persona thumbnails | 400×400 | Internal personas stay INTERNAL — thumbnails only if page is customer-facing; otherwise admin-only assets | static | P2 |
| 5 | Learn (/modules) | hero + course card | 1600×900 + 800×450 | Open book + ascending staircase of knowledge | static | P1 |
| 6 | Community (/palace, /more) | hero | 1600×900 | Circle of figures around a shared fire/table — unity | static | P1 |
| 7 | Music (/band) | hero + album placeholder | 1600×900 + 800×800 | Vinyl + waveform, warm tones | static + dynamic placeholder (user upload) | P1 |
| 8 | Games (/arcade, /arena) | hero | 1600×900 | Arcade glow — public arcade only; **Arena gets NO public asset** (internal, exec-only) | static | P2 |
| 9 | Sanctuary (/sanctuary → /helper) | hero | 1600×900 | Calm water / candle — pending executive decision on Sanctuary's canonical home | static | P2 |
| 10 | BYOK (/byok) | feature card | 800×450 | Key + gateway lock, tech-illustration style | static | P2 |
| 11 | Global | empty states | 400×400 | Consistent "nothing here yet" art per section (no data → no stock-looking placeholder) | static SVG | P1 |
| 12 | Global | loading/skeleton | n/a | CSS shimmer on brand tokens — no asset needed | CSS | P1 |
| 13 | Global | OG/social share | 1200×630 | Brand mark + platform name; one per ecosystem | static | P2 |
| 14 | Global | favicon/app icon | 512×512 | Brand mark glyph | static SVG/PNG | P0 |

## Static-first rule

Preferred order (no recurring cost):
1. **CSS/SVG art** built on existing Tailwind tokens (hero shapes, gradients, patterns) — $0.
2. **One-time generated master** via the existing DALL-E path (exec-approved batch only) —
   ~$0.04/image at 1024×1024 (existing OpenAI budget, existing key), then stored as a
   static file in `frontend/public/images/` — subsequent serving is $0.
3. **User-uploaded** assets for user-owned content (band, portfolio) via existing GridFS.

## Dynamic generation (COST-BEARING — exec-controlled)

- Only through the existing AI handler / FCC-gated path; never a public button.
- Budget guard: existing `HOURLY_TOKEN_CAP` + per-user daily budget; per-feature image
  quota = CONFIGURATION REQUIRED.
- Any future batch: max N images per run, logged via `ai_cost_tracker`, generated
  into `frontend/public/images/<ecosystem>/` with a manifest.

## Roadmap (after approval — not started)

1. **Phase A (P0):** landing hero + ecosystem tiles — static SVG/CSS first; if exec
   approves, 7–9 one-time DALL-E images (~$0.30) as static files.
2. **Phase B (P1):** section heroes + empty states + ResponsiveImage component (lazy,
   fallback, alt text) — $0.
3. **Phase C (P2):** admin asset assignment in the Feature Control Center (Assets tab),
   feature→image mapping in the registry — $0, no new services.

**No external image provider will be added.** No new accounts. No recurring cost.
