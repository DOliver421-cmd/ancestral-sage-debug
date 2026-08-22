# VISUAL ASSET ARCHITECTURE — Proposed Plan

**Date:** August 22, 2026
**Status:** PROPOSAL — No implementation yet.

---

## CURRENT STATE

The site runs on inline CSS gradients and SVG noise textures. The only actual images are:
- Logo SVGs (brand assets)
- OG image for social sharing
- Favicon

**Zero hero images. Zero ecosystem illustrations. Zero feature screenshots. Zero social proof.**

Meanwhile, the platform has DALL-E 3 integration sitting unused in the Architect persona tools.

---

## PROPOSED ARCHITECTURE

### Layer 1: Brand Asset Store (static, no API cost)

**Location:** `frontend/public/images/`

Store pre-generated brand assets:
- Ecosystem hero images (AI, Create, Learn, Community, Marketplace, Sanctuary, Music, Games)
- Feature icons/illustrations
- Empty-state illustrations
- Social proof images
- Default avatars/persona images

**Generation:** Batch-generate once via `generate_covers.py`-style script, commit to repo.

**Cost:** One-time DALL-E generation (~$2-5 total for 20-30 images).

**Serving:** Standard React static file serving. No CDN needed.

---

### Layer 2: Dynamic Asset Store (GridFS, admin-managed)

**Location:** MongoDB GridFS via existing `media.py` upload endpoints.

For user-uploaded and admin-managed images:
- Product covers
- Course thumbnails
- Creator profile images
- User-uploaded content

**Admin UI:** Feature Control Center gets an "Asset Manager" tab.

---

### Layer 3: AI-Generated Assets (DALL-E, on-demand)

**Location:** `db.architect_assets` collection.

For on-demand generation:
- Admin triggers generation via Feature Control Center
- Persona generates assets via Architect tools
- Social Blast generates post images

**Flow:**
```
Admin/Persona request
    ↓
architect_generate_cover_art()
    ↓
DALL-E 3 API call
    ↓
Image URL (temporary) → download → store in GridFS
    ↓
Save metadata to architect_assets
    ↓
Associate with feature/page via feature registry
```

---

### Layer 4: Responsive Image Component

**New component:** `frontend/src/components/ResponsiveImage.jsx`

```jsx
// Props: src, alt, sizes, aspect, fallback, loading
// Behavior:
// - <picture> with srcset for mobile/desktop
// - loading="lazy" for below-fold
// - onerror fallback to placeholder
// - Skeleton loading state
// - aspect-ratio preservation
```

---

### Layer 5: Feature-Image Registry Extension

Extend `FEATURE_REGISTRY` in `backend/routers/features.py`:

```python
{
    "feature_id": "nam.chat",
    # ... existing fields ...
    "hero_image": "/images/ecosystems/ai-tutor-hero.webp",
    "thumbnail": "/images/ecosystems/ai-tutor-thumb.webp",
    "icon": "/images/icons/ai-tutor.svg",
    "empty_state": "/images/empty-states/ai-tutor.svg",
    "og_image": "/images/og/ai-tutor-1200x630.png",
}
```

---

## IMPLEMENTATION PLAN (Proposed)

### Phase A: Static Brand Assets (no code changes needed)

1. Generate 20-30 ecosystem/feature images via DALL-E batch script
2. Save to `frontend/public/images/`
3. Commit to repo
4. Reference in existing components

**Cost:** ~$1-3 one-time (DALL-E standard quality)
**Risk:** None — static files, no runtime impact
**Value:** Immediate visual upgrade to every page

### Phase B: ResponsiveImage Component

1. Create `ResponsiveImage.jsx` with lazy loading, fallback, skeleton
2. Add to landing page hero sections
3. Add to ecosystem cards
4. Add to feature showcases

**Cost:** $0 — pure frontend
**Risk:** Low — additive component
**Value:** Professional image handling across the site

### Phase C: Admin Asset Manager

1. Add "Assets" tab to Feature Control Center
2. Upload interface with GridFS backend
3. Image preview with crop/resize (Pillow)
4. Assign images to features/pages
5. Regenerate button (triggers DALL-E)

**Cost:** ~$0.04-0.08 per regeneration
**Risk:** Medium — new admin UI
**Value:** Admin can manage site visuals without code changes

### Phase D: AI-Generated Feature Images

1. Batch-generate hero images for all 10 ecosystems
2. Batch-generate feature thumbnails
3. Auto-generate social media visuals
4. Connect to Architect persona tools

**Cost:** ~$2-5 one-time for full set
**Risk:** Low — uses existing DALL-E integration
**Value:** Complete visual identity for every ecosystem

### Phase E: Social Media Image Pipeline

1. Auto-generate images for Social Blast posts
2. Resize for platform requirements (Instagram 1080x1080, Twitter 1200x675, etc.)
3. Image library for post creation
4. Template system for branded content

**Cost:** ~$0.04-0.08 per post image
**Risk:** Medium — social platform API integration
**Value:** Complete visual social media presence

---

## WHAT ALREADY EXISTS AND WORKS

| Component | File | Status |
|-----------|------|--------|
| DALL-E 3 generation | `backend/tools/architect_tools.py` | ✅ Works when OPENAI_API_KEY set |
| Brand prompt engineering | `architect_tools.py` _build_wai_image_prompt | ✅ Bakes in brand colors/tone |
| GridFS storage | `backend/routers/media.py` | ✅ Upload/download works |
| Asset metadata | `db.architect_assets` | ✅ Collection exists |
| Pillow | `backend/requirements.txt` | ✅ Installed, unused |
| AspectRatio component | `frontend/src/components/ui/aspect-ratio.jsx` | ✅ Available, unused |
| Cover generation script | `backend/scripts/tools/generate_covers.py` | ✅ Works with gpt-image-1.5 |

## WHAT NEEDS TO BE BUILT

| Component | Priority | Effort | Cost |
|-----------|----------|--------|------|
| Static brand assets (batch DALL-E) | P0 | 1 hour | ~$2 |
| ResponsiveImage component | P0 | 2 hours | $0 |
| Landing page hero images | P0 | 1 hour | $0 (use static) |
| Admin Asset Manager | P1 | 4 hours | $0 |
| Feature-Image registry extension | P1 | 1 hour | $0 |
| AI batch generation pipeline | P2 | 3 hours | ~$3 |
| Social media image pipeline | P2 | 4 hours | ~$1/post |
| Image versioning | P3 | 2 hours | $0 |

---

## CONSTRAINTS

1. **No new paid services** — Use existing DALL-E + MongoDB + Pillow
2. **No new signups** — Use existing OPENAI_API_KEY
3. **No CDN** — Static files + GridFS sufficient for current scale
4. **No external image hosting** — Everything stays in the platform
5. **Existing budget** — Image generation uses the same LLM gateway budget guard

---

## VISUAL IDENTITY GUIDELINES (from architect_tools.py)

The platform already defines its visual philosophy:

```python
WAI_BRAND_DEFAULTS = {
    "primary_colors": ["#1a1a1a", "#E8A51E", "#2D6A4F"],
    "visual_tone": "Bold, intentional, culturally grounded",
    "imagery_style": "Cinematic. High contrast. Intentional negative space. Black excellence expressed visually.",
    "prohibitions": [
        "No stereotypical imagery",
        "No passive or submissive poses",
        "No generic stock-photo aesthetics",
        "No cultural appropriation",
        "No derivative or模仿 Western corporate templates",
    ],
}
```

This should guide all generated assets.

---

## KEY DECISION NEEDED

**Question:** Should Phase A (static brand assets) proceed now?

This would:
- Generate ~20 ecosystem/feature images via DALL-E
- Cost ~$2 one-time
- Immediately improve every page's visual quality
- Require no code changes (just add images to public/ and reference them)

Or should we wait for the full Feature Control Center admin UI (Phase C) before generating anything?

**Recommendation:** Phase A first. It's low-risk, low-cost, high-impact. The admin UI can come later.
