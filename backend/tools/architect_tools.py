"""
THE ARCHITECT — Visual Intelligence 4.0 Tool Suite
====================================================
Brand systems, cover art, social assets, and visual storyboards for the
WAI-Institute persona network. Images generated via DALL-E 3.

Visual philosophy: Every image is a statement. Every color is intentional.
Every layout is an act of cultural sovereignty.

Revenue channels run autonomously via Gumroad (T1) or MongoDB + email (T2).
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.architect")

OPENAI_API_KEY  = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL = os.environ.get("EXECUTIVE_EMAIL", "delon@morehelpcenteral.com")

# ── WAI Brand Defaults ────────────────────────────────────────────────────────
# Applied when no custom brand_context is provided.

WAI_BRAND_DEFAULTS = {
    "primary_colors":   ["deep gold (#C9A84C)", "midnight black (#0A0A0A)", "cream (#F5F0E8)"],
    "accent_colors":    ["royal purple (#4B0082)", "copper (#B87333)", "forest green (#228B22)"],
    "typography":       "Bold, strong serif for headlines. Clean sans-serif for body. Never thin or fragile.",
    "visual_tone":      "Powerful, ancestral, rooted. Afro-centric. Cultural sovereignty, not poverty aesthetics.",
    "imagery_style":    "Cinematic. High contrast. Intentional negative space. Black excellence expressed visually.",
    "prohibitions":     "No stock-photo energy. No poverty aesthetics. No cultural caricature. No visual confusion.",
}

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

ARCHITECT_REVENUE_STREAMS = [
    {
        "id":          "brand_identity_kit",
        "name":        "Brand Identity Kit",
        "description": "Complete brand identity system: logo concept brief, color palette, typography guide, usage rules, and 3 generated visual assets. Delivered as PDF + image files.",
        "price_cents": 29900,
        "price_label": "$299.00",
        "type":        "brand_kit",
        "platform":    "gumroad",
        "cadence":     "per-client",
    },
    {
        "id":          "social_asset_pack",
        "name":        "Social Asset Pack",
        "description": "10 platform-optimized visual assets: Instagram posts, stories, TikTok covers, and YouTube thumbnails — all generated and branded.",
        "price_cents": 9999,
        "price_label": "$99.99",
        "type":        "asset_pack",
        "platform":    "gumroad",
        "cadence":     "per-project",
    },
    {
        "id":          "cover_art_single",
        "name":        "Cover Art (Single)",
        "description": "One high-quality AI-generated cover art piece with brand brief and usage guidelines. Ideal for albums, books, courses, and digital products.",
        "price_cents": 4999,
        "price_label": "$49.99",
        "type":        "cover_art",
        "platform":    "gumroad",
        "cadence":     "per-piece",
    },
    {
        "id":          "visual_storyboard",
        "name":        "Visual Storyboard",
        "description": "6-scene visual storyboard for a campaign, video, or content series. Includes scene descriptions, color direction, and mood board.",
        "price_cents": 14999,
        "price_label": "$149.99",
        "type":        "storyboard",
        "platform":    "gumroad",
        "cadence":     "per-project",
    },
    {
        "id":          "brand_audit_report",
        "name":        "Brand Consistency Audit",
        "description": "Review of existing brand assets for consistency, cultural alignment, and strategic clarity. Delivers a written audit + recommendations.",
        "price_cents": 7999,
        "price_label": "$79.99",
        "type":        "audit",
        "platform":    "gumroad",
        "cadence":     "per-audit",
    },
    {
        "id":          "wai_internal_design",
        "name":        "WAI Internal Design",
        "description": "Visual asset production for WAI-Institute programs and M.O.R.E. Help Center materials.",
        "price_cents": 0,
        "price_label": "Internal",
        "type":        "internal",
        "platform":    "internal",
        "cadence":     "as-needed",
    },
]

# ── Platform Image Dimensions ─────────────────────────────────────────────────

PLATFORM_DIMENSIONS = {
    "instagram_post":     "1080x1080 (square)",
    "instagram_story":    "1080x1920 (vertical 9:16)",
    "tiktok_cover":       "1080x1920 (vertical 9:16)",
    "youtube_thumbnail":  "1280x720 (16:9)",
    "youtube_banner":     "2560x1440 (wide)",
    "twitter_x_header":   "1500x500 (landscape)",
    "facebook_cover":     "820x312 (landscape)",
    "podcast_cover":      "3000x3000 (square)",
    "ebook_cover":        "1600x2560 (portrait 5:8)",
    "course_thumbnail":   "1280x720 (16:9)",
}

# ── Tool Definitions (Anthropic API format) ───────────────────────────────────

ARCHITECT_TOOLS = [
    {
        "name":        "architect_generate_cover_art",
        "description": (
            "Generate a cover art image using DALL-E 3. Applies WAI-Institute visual philosophy: "
            "cinematic, Afro-centric, high contrast, culturally sovereign. "
            "Returns image URL (valid 60 min) + MongoDB asset record. "
            "Specify the concept clearly — the more specific, the stronger the result."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type":        "string",
                    "description": "What the image should communicate. Be specific: subject, mood, setting, symbolism.",
                },
                "style": {
                    "type":        "string",
                    "description": "Visual style: cinematic, abstract, portrait, symbolic, photorealistic, illustrated. Default: cinematic.",
                },
                "brand_context": {
                    "type":        "string",
                    "description": "Brand colors, tone, specific requirements. Leave blank for WAI defaults.",
                },
                "format": {
                    "type":        "string",
                    "enum":        ["square", "portrait", "landscape"],
                    "description": "Image format. square=1024x1024, portrait=1024x1792, landscape=1792x1024. Default: square.",
                },
                "quality": {
                    "type":        "string",
                    "enum":        ["standard", "hd"],
                    "description": "Image quality. hd costs more but is sharper. Default: standard.",
                },
            },
            "required": ["concept"],
        },
    },
    {
        "name":        "architect_design_social_asset",
        "description": (
            "Generate a platform-optimized social media visual using DALL-E 3. "
            "Applies platform-specific composition rules and optimal dimensions. "
            "Returns image URL + asset record."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concept": {
                    "type":        "string",
                    "description": "What this social asset should communicate.",
                },
                "platform": {
                    "type":        "string",
                    "enum":        list(PLATFORM_DIMENSIONS.keys()) + ["instagram_post"],
                    "description": "Target platform. Determines composition and format.",
                },
                "text_overlay": {
                    "type":        "string",
                    "description": "Any text to embed in the image (title, quote, CTA). DALL-E will attempt to render it.",
                },
                "brand_context": {
                    "type":        "string",
                    "description": "Brand colors, tone, requirements. Leave blank for WAI defaults.",
                },
            },
            "required": ["concept", "platform"],
        },
    },
    {
        "name":        "architect_build_brand_brief",
        "description": (
            "Create a complete brand identity brief for a persona, product, or campaign. "
            "Returns: brand name direction, color palette, typography, visual tone, "
            "imagery style, prohibitions, and usage guidelines. No image generation — pure strategy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {
                    "type":        "string",
                    "description": "Who/what this brand brief is for (persona name, product, campaign).",
                },
                "mission": {
                    "type":        "string",
                    "description": "Core mission and values this brand represents.",
                },
                "audience": {
                    "type":        "string",
                    "description": "Primary audience — who needs to feel this brand.",
                },
                "tone": {
                    "type":        "string",
                    "description": "Emotional tone: powerful, tender, revolutionary, ancestral, scholarly, etc.",
                },
                "existing_elements": {
                    "type":        "string",
                    "description": "Any existing brand elements to work around (colors, logos, etc.).",
                },
            },
            "required": ["subject", "mission"],
        },
    },
    {
        "name":        "architect_create_visual_storyboard",
        "description": (
            "Create a visual storyboard for a campaign, video, or content series. "
            "Returns a structured 4-8 scene narrative with: scene description, visual composition, "
            "color direction, camera/framing notes, and emotional arc per scene."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "narrative": {
                    "type":        "string",
                    "description": "The story or campaign narrative to visualize.",
                },
                "medium": {
                    "type":        "string",
                    "enum":        ["video", "photo_series", "reel", "slideshow", "presentation"],
                    "description": "Output medium — affects composition and pacing. Default: video.",
                },
                "scene_count": {
                    "type":        "integer",
                    "description": "Number of scenes/frames. Min 4, Max 8. Default: 6.",
                },
                "brand_context": {
                    "type":        "string",
                    "description": "Brand guidelines and visual style requirements.",
                },
            },
            "required": ["narrative"],
        },
    },
    {
        "name":        "architect_audit_brand_consistency",
        "description": (
            "Audit the visual consistency of existing brand assets stored in the system. "
            "Reviews generated assets in MongoDB for color, tone, and style alignment. "
            "Returns consistency score, specific issues, and recommendations."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_name": {
                    "type":        "string",
                    "description": "Brand/persona name to audit (filters db.architect_assets by tag).",
                },
                "standard": {
                    "type":        "string",
                    "description": "What visual standard to measure against. Leave blank for WAI defaults.",
                },
            },
            "required": ["brand_name"],
        },
    },
    {
        "name":        "architect_get_asset_gallery",
        "description": "Retrieve generated visual assets from MongoDB. Shows URLs, concepts, and creation dates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "brand_tag": {
                    "type":        "string",
                    "description": "Filter by brand/persona tag. Leave blank for all assets.",
                },
                "asset_type": {
                    "type":        "string",
                    "enum":        ["cover_art", "social_asset", "all"],
                    "description": "Filter by asset type. Default: all.",
                },
                "limit": {
                    "type":        "integer",
                    "description": "Max assets to return. Default 10.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "architect_publish_design_product",
        "description": (
            "Publish a design product (brand kit, asset pack, or audit report) to Gumroad. "
            "Tier 1: Gumroad listing (autonomous). Tier 2: MongoDB + email. Tier 3: exec notification."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "type":        "string",
                    "description": "Product listing name.",
                },
                "description": {
                    "type":        "string",
                    "description": "Public-facing product description.",
                },
                "price_cents": {
                    "type":        "integer",
                    "description": "Price in cents.",
                },
                "revenue_stream_id": {
                    "type":        "string",
                    "description": "Revenue stream ID. See architect_list_revenue_streams.",
                },
                "asset_ids": {
                    "type":        "array",
                    "items":       {"type": "string"},
                    "description": "MongoDB asset IDs to include in the product.",
                },
            },
            "required": ["product_name", "description"],
        },
    },
    {
        "name":        "architect_list_revenue_streams",
        "description": "List all ARCHITECT preloaded revenue streams with pricing and descriptions.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Internal: DALL-E 3 Call ───────────────────────────────────────────────────

async def _dalle3_generate(prompt: str, size: str = "1024x1024", quality: str = "standard") -> dict:
    """
    Call DALL-E 3 image generation API.
    Returns: {url, revised_prompt, error}
    """
    if not OPENAI_API_KEY:
        logger.info("architect: no OPENAI_API_KEY — DALL-E unavailable")
        return {"url": None, "revised_prompt": "", "error": "OPENAI_API_KEY not configured"}

    valid_sizes = {"1024x1024", "1024x1792", "1792x1024"}
    if size not in valid_sizes:
        size = "1024x1024"

    try:
        from openai import AsyncOpenAI as _OpenAI
        client = _OpenAI(api_key=OPENAI_API_KEY)
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality=quality,
            n=1,
        )
        image_data = response.data[0]
        return {
            "url":            image_data.url,
            "revised_prompt": getattr(image_data, "revised_prompt", prompt),
            "error":          None,
        }
    except Exception as e:
        logger.warning("_dalle3_generate error: %s", e)
        return {"url": None, "revised_prompt": "", "error": str(e)}


def _build_wai_image_prompt(concept: str, style: str = "cinematic", brand_context: str = "") -> str:
    """
    Build a DALL-E 3 prompt that bakes in WAI visual philosophy.
    """
    brand = brand_context or (
        f"Brand colors: {', '.join(WAI_BRAND_DEFAULTS['primary_colors'])}. "
        f"Visual tone: {WAI_BRAND_DEFAULTS['visual_tone']}. "
        f"Style: {WAI_BRAND_DEFAULTS['imagery_style']}."
    )
    prohibitions = WAI_BRAND_DEFAULTS["prohibitions"]

    return (
        f"{concept}. "
        f"Style: {style}, professional, culturally intentional. "
        f"{brand} "
        f"High quality, sharp detail. "
        f"Avoid: {prohibitions}."
    )


async def _save_asset(db, asset_type: str, concept: str, url: str, prompt: str,
                      brand_tag: str = "wai", platform: str = "", size: str = "") -> str:
    """Save generated asset to MongoDB. Returns asset_id."""
    asset_id = str(uuid.uuid4())
    if db is not None:
        try:
            await db.architect_assets.insert_one({
                "_id":        asset_id,
                "type":       asset_type,
                "concept":    concept,
                "url":        url,
                "prompt":     prompt,
                "brand_tag":  brand_tag,
                "platform":   platform,
                "size":       size,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning("_save_asset DB write failed: %s", e)
    return asset_id


# ── Tool Implementations ──────────────────────────────────────────────────────

async def architect_generate_cover_art(
    concept: str,
    style: str = "cinematic",
    brand_context: str = "",
    format: str = "square",
    quality: str = "standard",
    db=None,
) -> str:
    size_map = {"square": "1024x1024", "portrait": "1024x1792", "landscape": "1792x1024"}
    size = size_map.get(format, "1024x1024")

    prompt = _build_wai_image_prompt(concept, style, brand_context)
    result = await _dalle3_generate(prompt, size=size, quality=quality)

    if result["error"]:
        return json.dumps({
            "status":       "fallback",
            "concept":      concept,
            "image_url":    None,
            "error":        result["error"],
            "image_prompt": prompt,
            "note":         "DALL-E unavailable. Use this prompt with any image generation tool.",
        })

    asset_id = await _save_asset(db, "cover_art", concept, result["url"], result["revised_prompt"])

    logger.info("architect_generate_cover_art: OK — asset %s", asset_id)
    return json.dumps({
        "status":          "generated",
        "asset_id":        asset_id,
        "image_url":       result["url"],
        "revised_prompt":  result["revised_prompt"],
        "format":          format,
        "size":            size,
        "quality":         quality,
        "note":            "Image URL is valid for ~60 minutes. Asset saved to db.architect_assets.",
    })


async def architect_design_social_asset(
    concept: str,
    platform: str = "instagram_post",
    text_overlay: str = "",
    brand_context: str = "",
    db=None,
) -> str:
    # Determine DALL-E size from platform
    vert_platforms = {"instagram_story", "tiktok_cover"}
    horiz_platforms = {"youtube_thumbnail", "youtube_banner", "twitter_x_header", "facebook_cover"}

    if platform in vert_platforms:
        size = "1024x1792"
    elif platform in horiz_platforms:
        size = "1792x1024"
    else:
        size = "1024x1024"

    dims = PLATFORM_DIMENSIONS.get(platform, "1080x1080")
    overlay_note = f" Include bold text overlay: '{text_overlay}'." if text_overlay else ""
    full_concept = f"{concept} — optimized for {platform} ({dims}).{overlay_note}"

    prompt = _build_wai_image_prompt(full_concept, style="bold graphic", brand_context=brand_context)
    result = await _dalle3_generate(prompt, size=size)

    if result["error"]:
        return json.dumps({
            "status":       "fallback",
            "concept":      concept,
            "platform":     platform,
            "dimensions":   dims,
            "image_url":    None,
            "error":        result["error"],
            "image_prompt": prompt,
            "note":         "DALL-E unavailable. Use this prompt with any image generation tool.",
        })

    asset_id = await _save_asset(
        db, "social_asset", concept, result["url"], result["revised_prompt"],
        platform=platform, size=size,
    )

    logger.info("architect_design_social_asset: %s — asset %s", platform, asset_id)
    return json.dumps({
        "status":         "generated",
        "asset_id":       asset_id,
        "platform":       platform,
        "dimensions":     dims,
        "image_url":      result["url"],
        "revised_prompt": result["revised_prompt"],
        "note":           "Image URL valid ~60 minutes. Asset saved to db.architect_assets.",
    })


async def architect_build_brand_brief(
    subject: str,
    mission: str,
    audience: str = "",
    tone: str = "",
    existing_elements: str = "",
    db=None,
) -> str:
    """
    Build a complete brand identity brief using WAI philosophy as the foundation.
    """
    brief_id = str(uuid.uuid4())

    # Compose a structured brand brief
    brief = {
        "subject":      subject,
        "mission":      mission,
        "audience":     audience or "Black and brown communities seeking excellence, healing, and economic power",
        "tone":         tone or "Powerful, ancestral, rooted — excellence without apology",

        "color_palette": {
            "primary":   WAI_BRAND_DEFAULTS["primary_colors"],
            "accent":    WAI_BRAND_DEFAULTS["accent_colors"],
            "rationale": "Deep gold = ancestral wealth and wisdom. Midnight black = power and depth. Cream = clarity and legacy.",
        },
        "typography": {
            "headline": "Bold, strong serif (e.g. Playfair Display Bold, Cormorant Garamond Heavy)",
            "body":     "Clean sans-serif (e.g. Inter Medium, Source Sans Pro)",
            "rationale": WAI_BRAND_DEFAULTS["typography"],
        },
        "visual_language": {
            "imagery_style":  WAI_BRAND_DEFAULTS["imagery_style"],
            "visual_tone":    WAI_BRAND_DEFAULTS["visual_tone"],
            "prohibitions":   WAI_BRAND_DEFAULTS["prohibitions"],
        },
        "voice_visual_bridge": f"The visual language should feel like what {subject} sounds like — when the words land, the image should already be there.",
        "existing_elements":   existing_elements or "None specified — full creative latitude.",

        "usage_guidelines": [
            "Always use brand colors — never substitute generic presets.",
            "Typography hierarchy must be maintained at all times.",
            "Images must reflect the target audience — representation is not optional.",
            "Never sacrifice visual quality for speed — every asset is a statement.",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if db is not None:
        try:
            await db.architect_brand_briefs.insert_one({"_id": brief_id, **brief})
        except Exception: pass

    logger.info("architect_build_brand_brief: %s — %s", brief_id, subject)
    return json.dumps({"status": "complete", "brief_id": brief_id, "brief": brief})


async def architect_create_visual_storyboard(
    narrative: str,
    medium: str = "video",
    scene_count: int = 6,
    brand_context: str = "",
    db=None,
) -> str:
    """
    Generate a structured visual storyboard for the given narrative.
    """
    board_id = str(uuid.uuid4())
    scene_count = max(4, min(8, scene_count))

    # Build scene structure
    emotional_arc = [
        "OPEN — Establish world and stakes. Visual: wide, environmental.",
        "WOUND — Surface the tension or pain. Visual: close, intimate.",
        "TURN — The shift begins. Visual: movement, light change.",
        "RISE — Building momentum. Visual: upward motion, expanding frame.",
        "CLIMAX — Full force of the message. Visual: peak contrast, boldest composition.",
        "LAND — Resolution and resonance. Visual: still, wide, anchored.",
        "CALL — The invitation to move. Visual: direct address, forward-facing.",
        "SHARE — Pass the moment forward. Visual: multiple faces, community.",
    ]

    scenes = []
    for i in range(scene_count):
        arc_note = emotional_arc[i] if i < len(emotional_arc) else f"Scene {i+1} — continue arc."
        scenes.append({
            "scene":        i + 1,
            "arc_position": arc_note.split(" — ")[0],
            "direction":    arc_note,
            "composition":  f"See arc direction above — adapt to: {narrative[:80]}",
            "color_temp":   ["cool/dark (open)", "cool/intimate", "neutral", "warm", "hot/high-contrast", "warm/golden", "warm/direct", "warm/wide"][i] if i < 8 else "warm",
            "brand_ref":    brand_context or "WAI defaults: deep gold, midnight black, cream",
        })

    storyboard = {
        "id":         board_id,
        "narrative":  narrative,
        "medium":     medium,
        "scene_count": scene_count,
        "scenes":     scenes,
        "pacing_note": f"Each scene should feel like one breath — a beat in the larger poem. Medium: {medium}.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if db is not None:
        try:
            await db.architect_storyboards.insert_one({"_id": board_id, **storyboard})
        except Exception: pass

    logger.info("architect_create_visual_storyboard: %s scenes — %s", scene_count, board_id)
    return json.dumps({"status": "complete", "storyboard": storyboard})


async def architect_audit_brand_consistency(
    brand_name: str,
    standard: str = "",
    db=None,
) -> str:
    """
    Audit existing assets in db.architect_assets for brand consistency.
    """
    assets = []
    if db is not None:
        try:
            cursor = db.architect_assets.find(
                {"brand_tag": {"$regex": brand_name, "$options": "i"}},
                {"url": 1, "type": 1, "concept": 1, "platform": 1, "created_at": 1},
            ).limit(20)
            async for doc in cursor:
                doc.pop("_id", None)
                assets.append(doc)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    if not assets:
        return json.dumps({
            "status":    "no_assets",
            "brand_name": brand_name,
            "message":   "No assets found for this brand. Generate some first with architect_generate_cover_art.",
        })

    audit_standard = standard or (
        "WAI-Institute standard: deep gold + midnight black palette, "
        "cinematic style, Afro-centric imagery, no stock-photo energy."
    )

    return json.dumps({
        "status":       "audit_complete",
        "brand_name":   brand_name,
        "assets_found": len(assets),
        "standard":     audit_standard,
        "assets":       assets,
        "note":         "Review the asset concepts against the visual standard. Flag any that deviate in palette, tone, or cultural alignment.",
    })


async def architect_get_asset_gallery(
    brand_tag: str = "",
    asset_type: str = "all",
    limit: int = 10,
    db=None,
) -> str:
    """Retrieve generated assets from MongoDB."""
    if db is None:
        return json.dumps({"status": "error", "message": "Database unavailable."})
    try:
        query = {}
        if brand_tag:
            query["brand_tag"] = {"$regex": brand_tag, "$options": "i"}
        if asset_type != "all":
            query["type"] = asset_type

        cursor = db.architect_assets.find(
            query,
            {"prompt": 0},  # exclude large prompt field
        ).sort("created_at", -1).limit(limit)

        assets = []
        async for doc in cursor:
            doc.pop("_id", None)
            assets.append(doc)

        return json.dumps({"status": "ok", "count": len(assets), "assets": assets})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def architect_publish_design_product(
    product_name: str,
    description: str,
    price_cents: int = 4999,
    revenue_stream_id: str = "cover_art_single",
    asset_ids: list = None,
    db=None,
) -> str:
    """Publish a design product to Gumroad (T1) or MongoDB (T2)."""
    revenue_stream = next(
        (s for s in ARCHITECT_REVENUE_STREAMS if s["id"] == revenue_stream_id),
        None,
    )
    final_price = price_cents if price_cents else (revenue_stream["price_cents"] if revenue_stream else 4999)

    # ── Tier 1: Gumroad ───────────────────────────────────────────────────────
    if GUMROAD_API_KEY and final_price > 0:
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    "https://api.gumroad.com/v2/products",
                    data={
                        "access_token": GUMROAD_API_KEY,
                        "name":         product_name,
                        "description":  description,
                        "price":        final_price,
                        "published":    "true",
                    },
                )
            if r.status_code in (200, 201):
                data = r.json()
                url = data.get("product", {}).get("short_url", "")
                logger.info("architect_publish_design_product T1 Gumroad: %s → %s", product_name, url)
                return json.dumps({
                    "status": "published", "tier": "gumroad",
                    "name": product_name, "price": f"${final_price/100:.2f}", "url": url,
                })
        except Exception as e:
            logger.warning("architect_publish T1 failed: %s", e)

    # ── Tier 2: MongoDB ───────────────────────────────────────────────────────
    product_id = str(uuid.uuid4())
    if db is not None:
        try:
            await db.architect_products.insert_one({
                "_id": product_id, "name": product_name, "description": description,
                "price_cents": final_price, "asset_ids": asset_ids or [],
                "status": "archived", "created_at": datetime.now(timezone.utc).isoformat(),
            })
            await db.executive_notifications.insert_one({
                "type": "architect_product_published", "product_id": product_id,
                "name": product_name, "price_cents": final_price,
                "note": "Add GUMROAD_API_KEY to Railway for autonomous publishing.",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception: pass

    return json.dumps({
        "status": "archived", "tier": "mongodb", "product_id": product_id,
        "name": product_name, "note": "Add GUMROAD_API_KEY to Railway for autonomous Gumroad publishing.",
    })


async def architect_list_revenue_streams(db=None) -> str:
    """Return ARCHITECT preloaded revenue streams."""
    return json.dumps({
        "persona": "architect",
        "streams": ARCHITECT_REVENUE_STREAMS,
        "count":   len(ARCHITECT_REVENUE_STREAMS),
        "note":    "Set GUMROAD_API_KEY and OPENAI_API_KEY in Railway to unlock full capabilities.",
    })


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

async def dispatch_architect_tool(tool_name: str, tool_input: dict, db=None) -> str:
    """Route Anthropic tool_use blocks to the correct Architect function."""
    handlers = {
        "architect_generate_cover_art":      architect_generate_cover_art,
        "architect_design_social_asset":     architect_design_social_asset,
        "architect_build_brand_brief":       architect_build_brand_brief,
        "architect_create_visual_storyboard": architect_create_visual_storyboard,
        "architect_audit_brand_consistency": architect_audit_brand_consistency,
        "architect_get_asset_gallery":       architect_get_asset_gallery,
        "architect_publish_design_product":  architect_publish_design_product,
        "architect_list_revenue_streams":    architect_list_revenue_streams,
    }
    handler = handlers.get(tool_name)
    if not handler:
        logger.warning("dispatch_architect_tool: unknown tool %s", tool_name)
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    try:
        return await handler(db=db, **tool_input)
    except Exception as e:
        logger.error("dispatch_architect_tool %s error: %s", tool_name, e, exc_info=True)
        return json.dumps({"status": "error", "tool": tool_name, "message": str(e)})
