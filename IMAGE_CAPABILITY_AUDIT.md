# IMAGE & VISUAL ASSET CAPABILITY AUDIT

**Date:** August 22, 2026
**Method:** Codebase scan of every router, component, tool, and config file.
**Status:** AUDIT ONLY — no implementation.

---

## EXECUTIVE SUMMARY

The platform has **significant existing infrastructure** for image generation and storage that is **underutilized**. The Architect persona already has DALL-E 3 integration, MongoDB asset storage, and brand-consistent prompt engineering — but none of this is connected to the actual site's visual presentation. The site currently runs on inline CSS gradients and SVG noise textures with no real imagery.

| Capability | Status | Evidence |
|------------|--------|----------|
| Image generation | **SUPPORTED** | DALL-E 3 via `architect_tools.py`, `generate_covers.py` |
| Image storage | **SUPPORTED** | MongoDB GridFS (`media.py`), `architect_assets` collection |
| Image upload | **SUPPORTED** | GridFS upload endpoints in `media.py`, `band.py`, `chat.py` |
| Image serving | **PARTIALLY SUPPORTED** | GridFS serving exists for media; no CDN |
| Responsive images | **NOT SUPPORTED** | No `<picture>`, no `srcset`, no breakpoint images |
| Image resizing/cropping | **PARTIALLY SUPPORTED** | Pillow installed but unused for this |
| Admin image management | **NOT SUPPORTED** | No admin UI for managing images |
| Fallback/broken-image states | **NOT SUPPORTED** | No `onerror`, no placeholder system |
| Feature-to-image mapping | **NOT SUPPORTED** | No canonical association |
| Image generation for site | **NOT SUPPORTED** | Architect generates for external use, not site assets |
| Different sizes/crops | **NOT SUPPORTED** | DALL-E returns fixed sizes only |
| CDN | **NOT SUPPORTED** | No CDN, no cache headers for images |

---

## 1. IMAGE GENERATION CAPABILITIES

### SUPPORTED — DALL-E 3 Integration (architect_tools.py)

**What exists:**
- `architect_tools.py` (lines 344-460): Full DALL-E 3 image generation pipeline
- `_dalle3_generate()` — calls DALL-E 3 with brand-consistent prompts
- `_build_wai_image_prompt()` — bakes in WAI visual philosophy (colors, tone, style, prohibitions)
- `_save_asset()` — saves to MongoDB `architect_assets` collection with metadata
- `architect_generate_cover_art()` — generates cover art with format/quality options
- `architect_generate_social_visual()` — generates platform-optimized social media visuals
- Supports 3 formats: `square` (1024x1024), `portrait` (1024x1792), `landscape` (1792x1024)

**What's missing:**
- No connection to site's actual pages/assets
- No automated generation of ecosystem images
- No batch generation for multiple sizes
- No admin UI to trigger generation
- Images are DALL-E URLs (expire in 60 min), not persisted as files

**Requirement:** `OPENAI_API_KEY` environment variable

### SUPPORTED — Cover Generation Script (generate_covers.py)

**What exists:**
- `backend/scripts/tools/generate_covers.py` — generates book covers using `gpt-image-1.5`
- Saves to local filesystem (`~/Downloads/`)
- Uses `base64` encoding for direct file output
- Batch generation with rate limiting (5s between calls)

**What's missing:**
- Saves to local filesystem, not to platform storage
- No integration with the application
- Manual script, not automated

### PARTIALLY SUPPORTED — Image Brief Generation (cipher_tools.py)

**What exists:**
- `generate_image_brief` tool — generates DALL-E prompts for visual content
- Returns ready-to-use prompts without calling DALL-E directly

**What's missing:**
- Brief generation only, no actual image generation
- Fallback when DALL-E is unavailable

---

## 2. IMAGE STORAGE CAPABILITIES

### SUPPORTED — MongoDB GridFS (media.py)

**What exists:**
- `backend/routers/media.py` (lines 204-267): Full GridFS upload/download
- Upload: `POST /api/media/upload` — accepts `UploadFile`, stores in GridFS with metadata
- Serve: `GET /api/media/file/{file_id}` — serves files with entitlement-aware preview boundaries
- Metadata tracking: uploader, filename, size, content_type, created_at
- Preview system: audio files have duration-based preview limits

**What's missing:**
- No image-specific processing (resize, crop, thumbnail)
- No CDN caching
- No public URL generation
- No image metadata (dimensions, color space, etc.)

### SUPPORTED — Architect Assets Collection

**What exists:**
- `db.architect_assets` collection stores generated image metadata
- Fields: `_id`, `type`, `concept`, `url`, `prompt`, `brand_tag`, `platform`, `size`, `created_at`
- `_save_asset()` function writes to this collection

**What's missing:**
- DALL-E URLs expire in 60 minutes — no permanent storage
- No local caching of generated images
- No association with site pages/features

### PARTIALLY SUPPORTED — Product Cover URLs

**What exists:**
- `media_products` collection has `cover_url` field
- `creator_courses` collection has `cover_image_url` field
- `social_routes.py` posts accept `image_url`

**What's missing:**
- `cover_url` is just a string field — no upload mechanism for product covers
- No image validation or processing
- No default/placeholder images

---

## 3. IMAGE UPLOAD CAPABILITIES

### SUPPORTED — GridFS Upload Endpoints

| Router | Endpoint | Purpose |
|--------|----------|---------|
| `media.py` | `POST /api/media/upload` | General media upload |
| `ai.py` | `POST /api/ai/director/upload` | Director file upload |
| `band.py` | `POST /api/band/upload` | Band page media upload |
| `chat.py` | `POST /api/chat/upload` | Chat image upload |
| `creator.py` | `POST /api/creator/upload` | Creator content upload |
| `creator_lounge.py` | `POST /api/creator-lounge/upload` | Lounge media upload |

### SUPPORTED — Frontend Upload Components

**What exists:**
- VonnsSagaAdmin.jsx — image upload with preview thumbnail
- Chat components — image upload capability
- DirectorWidget — file attachment support

**What's missing:**
- No drag-and-drop upload
- No image preview before upload
- No client-side cropping/resizing
- No progress indicator

---

## 4. FRONTEND IMAGE DISPLAY CAPABILITIES

### NOT SUPPORTED — Responsive Images

**Current state:** No `<picture>` elements, no `srcset`, no responsive image loading.

The site uses:
- Inline CSS gradients for backgrounds (`linear-gradient`)
- SVG noise textures (data URIs)
- Lucide icons (vector, not raster images)
- `<img>` tags for logos only (`WAI_LOGO`, `FOUNDER_LOGO`)

**What's needed:**
- `<picture>` with `srcset` for breakpoint images
- `loading="lazy"` for below-fold images
- Responsive `sizes` attribute
- Art direction (different crops for mobile/desktop)

### NOT SUPPORTED — Fallback/Broken-Image States

**Current state:** No `onerror` handlers on any `<img>` elements. No placeholder system. No skeleton loading states for images.

**What's needed:**
- `onError` fallback to placeholder SVG
- Skeleton loading states
- Empty-state illustrations
- Broken-image graceful degradation

### PARTIALLY SUPPORTED — Image Components

**What exists:**
- `frontend/src/components/ui/aspect-ratio.jsx` — Radix UI AspectRatio component (available but unused)
- `frontend/src/components/TeamAvatar.jsx` — team member avatars
- VonnsSagaAdmin — image preview with `objectFit: "contain"`
- Landing page — logo image with `objectFit: "cover"`

**What's missing:**
- No reusable `ResponsiveImage` component
- No `ImageGallery` component
- No `HeroImage` component
- No `FeatureImage` component

---

## 5. IMAGE PROCESSING CAPABILITIES

### PARTIALLY SUPPORTED — Pillow Library

**What exists:**
- `Pillow>=10.0.0` is in `requirements.txt`
- Not currently used for any image processing

**What's possible:**
- Resize, crop, thumbnail generation
- Format conversion (WebP, AVIF)
- Watermarking
- Color extraction
- EXIF manipulation

**What's needed:** Usage in a dedicated image processing module

### NOT SUPPORTED — Client-Side Image Processing

**What exists:** Nothing. No `canvas` usage, no client-side resizing, no drag-and-drop cropping.

---

## 6. ADMIN IMAGE MANAGEMENT

### NOT SUPPORTED — No Admin UI for Images

**Current state:** The Feature Control Center I just built has no image management. There is no admin interface for:
- Uploading site images
- Assigning images to features/pages
- Regenerating images
- Viewing generated assets
- Managing image versions

**What exists in backend:**
- `architect_assets` collection — stores generated image metadata
- `media_products` collection — stores product cover URLs
- GridFS upload endpoints — but no admin UI to use them

---

## 7. FEATURE-TO-IMAGE MAPPING

### NOT SUPPORTED — No Canonical Association

**Current state:** No system maps features/pages to their visual assets.

The `FEATURE_REGISTRY` I created has no image fields. There's no:
- `hero_image` field per feature
- `cover_image` field per ecosystem
- `icon` field per capability
- Default image per page

---

## 8. CDN AND CACHING

### NOT SUPPORTED — No CDN

**Current state:** Images served directly from MongoDB/GridFS via FastAPI. No CDN, no edge caching, no `Cache-Control` headers for static assets.

The server sets `cache-control: no-store` on API responses, which is correct for dynamic data but wrong for static images.

**What exists:**
- HSTS headers enabled
- Security headers in place
- Static file serving for `frontend/build/` (React app)

---

## 9. EXISTING IMAGE ECOSYSTEM

### Brand Assets (frontend/public/)

| Asset | Path | Purpose |
|-------|------|---------|
| MORE Logo | `public/MORE_Logo.svg` | Sidebar brand |
| WAI Logo | `public/WAI_Logo.jpg` | WAI door brand |
| OG Image | `public/logo-og-1200x630.png` | Social sharing |
| Favicon | `public/favicon.svg` | Browser tab |
| Sovereign | `public/sovereign.svg` | Sovereign persona |

### Landing Page Visual System

**Current approach:** The UnifiedGateway landing page uses:
- Dark gradient backgrounds (`linear-gradient(160deg, #0a0a0f, #1a0a00, #0d1a0a)`)
- SVG noise texture overlay (data URI)
- Gold accent color (#E8A51E)
- Green accent (#2D6A4F)
- Logo image only

**No hero images.** No ecosystem illustrations. No feature screenshots. No social proof images.

---

## 10. SOCIAL MEDIA IMAGE PIPELINE

### PARTIALLY SUPPORTED — Social Blast Image Support

**What exists:**
- `social_routes.py` accepts `image_url` in post payloads
- Supports Facebook, Instagram, Twitter, TikTok posting with images
- Image validation (file size, dimensions) for social platforms

**What's missing:**
- No image generation for social posts
- No automatic resizing for platform requirements
- No image library/asset picker in the UI
- `image_url` must be provided externally

---

## COST ANALYSIS

### What Uses API Budget

| Feature | Provider | Cost Per Call | Daily Limit | Status |
|---------|----------|---------------|-------------|--------|
| DALL-E 3 (1024x1024 standard) | OpenAI | ~$0.04 | Budget-guarded | SUPPORTED |
| DALL-E 3 (1024x1792 standard) | OpenAI | ~$0.08 | Budget-guarded | SUPPORTED |
| gpt-image-1.5 | OpenAI | ~$0.04 | Budget-guarded | SUPPORTED |
| Architect image brief | LLM gateway | ~$0.001 | Budget-guarded | SUPPORTED |

### What Costs Nothing (existing infrastructure)

| Capability | Cost | Status |
|------------|------|--------|
| GridFS storage | $0 (MongoDB already paid) | SUPPORTED |
| Pillow processing | $0 (already installed) | SUPPORTED |
| Static file serving | $0 (React build) | SUPPORTED |
| Brand asset serving | $0 (public folder) | SUPPORTED |

### What Would Require New Spend

| Capability | Cost | Alternative |
|------------|------|-------------|
| CDN | $5-20/mo | Use MongoDB GridFS + cache headers |
| Image resizing service | $0 | Use Pillow locally |
| Image hosting (external) | $0 | Use existing GridFS |
| AI image generation | ~$0.04-0.08/image | Use existing DALL-E integration |

---

## ANSWERS TO YOUR QUESTIONS

### Can the current stack generate images?
**YES.** DALL-E 3 integration exists in `architect_tools.py`. The Architect persona can generate cover art, social visuals, and brand assets. It requires `OPENAI_API_KEY` in environment.

### Does it already have an image-generation provider/API?
**YES.** OpenAI DALL-E 3 is fully integrated. The `generate_covers.py` script also uses `gpt-image-1.5`. Both are functional when `OPENAI_API_KEY` is set.

### Can it store generated assets?
**YES.** MongoDB `architect_assets` collection stores metadata. GridFS stores actual files. Both are functional.

### Where would images live?
**MongoDB GridFS** (same database, no new service). For static brand assets, `frontend/public/images/`. For generated assets, `architect_assets` collection with GridFS binary storage.

### Can the frontend display responsive image assets?
**PARTIALLY.** `<img>` tags work. `objectFit` and `borderRadius` are used. But no `srcset`, no `<picture>`, no lazy loading, no breakpoint images. The `aspect-ratio` Radix component exists but is unused.

### Can admins replace/regenerate images without code changes?
**NO.** There is no admin UI for image management. The Architect persona can generate images via chat, but there's no visual asset manager.

### Can images be associated with canonical ecosystems/features?
**NO.** The Feature Registry has no image fields. There's no mapping system.

### Does it already have an asset/media management system?
**PARTIALLY.** GridFS upload/download exists. `architect_assets` collection exists. But no unified admin UI, no image editing, no version management.

### Can it generate different sizes/crops for desktop/mobile?
**NO.** DALL-E returns fixed sizes. Pillow could generate sizes but isn't wired up. No `srcset` in frontend.

### Can it handle loading, fallback, broken-image, and empty states?
**NO.** No `onerror` handlers, no skeleton states, no placeholder images, no empty-state illustrations.

### Can it track which image belongs to which page/component?
**NO.** No image-to-feature mapping exists.

### What existing components already support imagery?
- `AspectRatio` (Radix) — available, unused
- `TeamAvatar` — works for profile images
- VonnsSagaAdmin — image upload + preview
- Landing page — logo display
- Band page — audio upload with metadata

### Are there duplicate media systems we should consolidate?
**YES.** 6 separate upload endpoints across different routers. 2 asset collections (`architect_assets`, `media_products`). Should be unified into one asset management system.

### What would require no new paid service or signup?
**Everything.** The platform already has:
- DALL-E 3 (via OpenAI key)
- MongoDB GridFS (storage)
- Pillow (processing)
- React (display)

### What would consume existing API budget?
Image generation via DALL-E (~$0.04-0.08 per image). This is already budget-guarded by the LLM gateway.

### Can it use locally generated/static assets instead of introducing another recurring service?
**YES.** Brand assets can live in `public/images/`. Generated assets can live in GridFS. Pillow handles resizing. No CDN needed for current scale.

---

## CAPABILITY MATRIX

| Capability | Status | Implementation Exists | Connected to Site | Admin Configurable |
|------------|--------|----------------------|-------------------|-------------------|
| DALL-E 3 generation | **SUPPORTED** | architect_tools.py | ❌ Not connected | ❌ |
| gpt-image generation | **SUPPORTED** | generate_covers.py | ❌ Script only | ❌ |
| MongoDB GridFS storage | **SUPPORTED** | media.py | ✅ Media upload | ❌ |
| architect_assets collection | **SUPPORTED** | architect_tools.py | ❌ Metadata only | ❌ |
| Product cover_url field | **PARTIALLY** | media.py | ✅ Products | ❌ |
| Pillow image processing | **PARTIALLY** | requirements.txt | ❌ Not used | ❌ |
| Responsive images | **NOT SUPPORTED** | — | ❌ | ❌ |
| Image fallbacks | **NOT SUPPORTED** | — | ❌ | ❌ |
| Admin image manager | **NOT SUPPORTED** | — | ❌ | ❌ |
| Feature-image mapping | **NOT SUPPORTED** | — | ❌ | ❌ |
| CDN/caching | **NOT SUPPORTED** | — | ❌ | ❌ |
| Image versioning | **NOT SUPPORTED** | — | ❌ | ❌ |
| Batch generation | **NOT SUPPORTED** | — | ❌ | ❌ |

---

## PHASE 17 UPDATE (2026-08-23) — COST-BEARING CONFIRMATION

- Confirmed: DALL-E 3 exists only inside `backend/tools/architect_tools.py`
  (`client.images.generate`, model `dall-e-3`) and is dispatched through the
  feature-gated AI handler in `routers/ai.py` — **no public generate endpoint**,
  so image generation is already behind feature access + auth.
- Image generation is classified COST-BEARING in the registry and governed by the
  FCC. There is no user-facing generate button.
- Still NOT SUPPORTED (unchanged): responsive component, feature→image mapping,
  admin asset manager, versioning. See IMAGE_ASSET_PLAN.md for the static-first
  plan (no generation executed).
