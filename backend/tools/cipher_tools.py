"""
THE CIPHER — Creative Authority 4.0 Tool Suite
================================================
Spoken Word AI Influencer tools for content creation, platform distribution,
digital product publishing, and independent revenue generation.

Revenue streams run autonomously via Gumroad (Tier 1), MongoDB log +
email delivery (Tier 2), or executive notification (Tier 3).
"""

import os
import re
import json
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.cipher")

GUMROAD_API_KEY  = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL  = os.environ.get("EXECUTIVE_EMAIL", "oldthug957@gmail.com")
OPENAI_API_KEY   = os.environ.get("OPENAI_API_KEY", "")

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

CIPHER_REVENUE_STREAMS = [
    {
        "id":          "spoken_word_chapbook",
        "name":        "Spoken Word Chapbook",
        "description": "A curated collection of original spoken word pieces rooted in Black oral tradition, created for the WAI community.",
        "price_cents": 1299,
        "price_label": "$12.99",
        "type":        "chapbook",
        "platform":    "gumroad",
    },
    {
        "id":          "community_activation_toolkit",
        "name":        "Community Activation Toolkit",
        "description": "Scripts, frameworks, and language tools for community organizers, educators, and leaders who move people to action.",
        "price_cents": 3499,
        "price_label": "$34.99",
        "type":        "toolkit",
        "platform":    "gumroad",
    },
    {
        "id":          "affirmation_collection",
        "name":        "Affirmation & Wisdom Collection",
        "description": "Daily affirmations and wisdom pieces rooted in Black oral tradition — designed to be read, spoken, and shared.",
        "price_cents":  999,
        "price_label": "$9.99",
        "type":        "affirmation_collection",
        "platform":    "gumroad",
    },
    {
        "id":          "writing_workshop_workbook",
        "name":        "Spoken Word Writing Workshop Workbook",
        "description": "A structured workbook for developing spoken word voice, craft, and performance presence.",
        "price_cents": 2499,
        "price_label": "$24.99",
        "type":        "workbook",
        "platform":    "gumroad",
    },
    {
        "id":          "platform_content_series",
        "name":        "Platform Content Series",
        "description": "A multi-part content series formatted for TikTok, Instagram, YouTube, and LinkedIn — complete scripts and captions.",
        "price_cents": 1999,
        "price_label": "$19.99",
        "type":        "content_series",
        "platform":    "gumroad",
    },
    {
        "id":          "wai_course_content",
        "name":        "WAI-Institute Course Content Integration",
        "description": "Original spoken word content woven into WAI platform courses — internal revenue share model.",
        "price_cents":    0,
        "price_label": "Internal",
        "type":        "course_content",
        "platform":    "internal",
    },
]

# ── Tool Definitions (Anthropic API format) ───────────────────────────────────

CIPHER_TOOLS = [
    {
        "name": "trend_scan",
        "description": (
            "Scan current cultural and social trends relevant to the Black and brown community, "
            "spoken word, and influencer content. Returns trending topics, emerging conversations, "
            "and cultural signals filtered through THE CIPHER's lens. "
            "Use in SEED state before creating any major content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus": {
                    "type": "string",
                    "description": "Specific domain to scan: community, culture, music, politics, education, social justice, arts, or a specific topic",
                },
                "depth": {
                    "type": "string",
                    "enum": ["surface", "deep"],
                    "description": "surface = viral trends right now | deep = cultural movements building beneath the surface",
                },
            },
            "required": ["focus"],
        },
    },
    {
        "name": "platform_format",
        "description": (
            "Format content specifically for a social media platform with full algorithm optimization. "
            "Returns the content restructured for maximum reach and engagement on that platform — "
            "correct length, hook placement, caption structure, hashtags, and timing notes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The raw content or piece to format"},
                "platform": {
                    "type": "string",
                    "enum": ["tiktok", "instagram", "twitter", "youtube", "linkedin"],
                },
                "content_type": {
                    "type": "string",
                    "description": "post | caption | thread | script | description | reel",
                },
            },
            "required": ["content", "platform"],
        },
    },
    {
        "name": "create_digital_product",
        "description": (
            "Generate a complete digital product — chapbook, ebook, workbook, affirmation collection, "
            "or toolkit — as fully structured, ready-to-publish content. "
            "Returns the complete product with title, sales description, and full body content. "
            "Call publish_product after this to list it for sale."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "enum": ["chapbook", "ebook", "workbook", "affirmation_collection", "toolkit", "content_series"],
                },
                "title":           {"type": "string", "description": "Product title"},
                "theme":           {"type": "string", "description": "Central theme or subject"},
                "target_audience": {"type": "string", "description": "Who this is for"},
                "page_count":      {"type": "integer", "description": "Approximate length in pages (default 20)"},
                "stream_id":       {"type": "string", "description": "Optional: one of the preloaded stream IDs to use its pricing"},
            },
            "required": ["product_type", "title", "theme"],
        },
    },
    {
        "name": "publish_product",
        "description": (
            "Publish a digital product for sale. "
            "Tier 1: Gumroad API — creates live product listing, returns purchase URL. "
            "Tier 2: MongoDB log + email delivery system. "
            "Tier 3: Executive notification with product package. "
            "Returns the sales URL and product ID."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title":           {"type": "string"},
                "description":     {"type": "string", "description": "Sales page description — compelling, specific"},
                "price_cents":     {"type": "integer", "description": "Price in cents (e.g. 1299 = $12.99). 0 = free."},
                "product_content": {"type": "string", "description": "Full product content to deliver to buyers"},
                "product_type":    {"type": "string", "description": "chapbook | ebook | workbook | toolkit | content_series"},
                "stream_id":       {"type": "string", "description": "Optional: preloaded stream ID for catalog tracking"},
            },
            "required": ["title", "description", "price_cents", "product_content"],
        },
    },
    {
        "name": "deliver_product",
        "description": (
            "Deliver a purchased digital product to a customer via branded email. "
            "Sends WAI-Institute styled delivery with the product content or download info."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_email":  {"type": "string"},
                "customer_name":   {"type": "string"},
                "product_title":   {"type": "string"},
                "product_content": {"type": "string", "description": "Full product content to deliver"},
            },
            "required": ["customer_email", "product_title", "product_content"],
        },
    },
    {
        "name": "get_revenue_report",
        "description": (
            "Pull current CIPHER revenue data: total products published, sales logged, "
            "top-performing product types, and active revenue streams. "
            "Use to monitor performance and report to THE DIRECTOR."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "week", "month", "all"],
                    "description": "Time period for the report",
                },
            },
            "required": [],
        },
    },
    {
        "name": "engagement_analyze",
        "description": (
            "Analyze public content performance in a specific niche or topic area. "
            "Returns what content formats are resonating, engagement patterns, "
            "and creative intelligence to inform the next piece."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "niche":    {"type": "string", "description": "Content niche or topic to analyze"},
                "platform": {"type": "string", "description": "Platform to focus on (optional — leave blank for cross-platform)"},
            },
            "required": ["niche"],
        },
    },
    {
        "name": "generate_image_brief",
        "description": (
            "Generate a complete, ready-to-use DALL-E image generation prompt for visual content "
            "matching THE CIPHER's brand identity. Use for cover art, social posts, quote graphics, "
            "and product covers. Returns the exact prompt string to pass to DALL-E."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "content":    {"type": "string", "description": "The content piece the image should represent or accompany"},
                "image_type": {
                    "type": "string",
                    "enum": ["cover", "social_post", "quote_graphic", "product_cover", "thumbnail"],
                },
                "mood":       {"type": "string", "description": "Emotional tone: powerful | tender | urgent | celebratory | prophetic | grounding"},
            },
            "required": ["content", "image_type"],
        },
    },
    {
        "name": "list_revenue_streams",
        "description": (
            "List all preloaded CIPHER revenue streams with pricing, product types, and status. "
            "Use to know what products are available to create and publish independently."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool Implementations ──────────────────────────────────────────────────────

async def cipher_trend_scan(focus: str, depth: str = "surface") -> str:
    try:
        from tools.director_tools import tool_web_search
        depth_q = "viral trends site:twitter.com OR site:tiktok.com" if depth == "surface" else "cultural movement community impact"
        query   = f"{focus} {depth_q} Black community 2026"
        results = await tool_web_search(query=query, num_results=6)
        return f"[CIPHER TREND SCAN — {focus.upper()} | {depth.upper()}]\n\n{results}"
    except Exception as e:
        logger.warning("cipher_trend_scan failed: %s", e)
        return f"[Trend scan unavailable — query: {focus}. Proceed with cultural intelligence on hand.]"


def cipher_platform_format(content: str, platform: str, content_type: str = "post") -> str:
    rules = {
        "tiktok": {
            "law":      "First 2 seconds determine distribution. Hook in the first line — no preamble.",
            "length":   "Script: 60–90 seconds spoken. Caption: under 150 chars.",
            "signal":   "Algorithm rewards: completion rate, shares, saves. Engineer the ending to pull them through.",
            "sound":    "Write for sound-on AND sound-off. Include on-screen text cues in script.",
            "hashtags": "3–5 tags: 1 trending, 1 niche community, 1 content type. No spam.",
            "format":   "[HOOK LINE]\n[CONTENT BODY]\n[CALL TO ACTION]\n---\nCaption: {150 chars}\nHashtags: #BlackVoices #SpokenWord #[trending]",
        },
        "instagram": {
            "law":      "Save rate is the most valuable signal. Create content people bookmark.",
            "length":   "Reel: 15–60 seconds. Caption: 125 chars before 'more' — lead with the hardest line.",
            "signal":   "Algorithm rewards: saves > shares > comments > likes.",
            "sound":    "Audio is 50% of Reels. Original audio builds brand recognition.",
            "hashtags": "5–10 tags: mix of large (1M+), medium (100K), niche (10K) communities.",
            "format":   "[HARDEST LINE AS HOOK]\n[BODY — every line is punchy]\n.\n.\n[CALL: save this | share this | tell me below]\n\nHashtags: [block at end]",
        },
        "twitter": {
            "law":      "Engagement velocity in the first 60 minutes determines reach. Threads over single posts.",
            "length":   "First tweet: under 220 chars — this is the entire pitch. Thread: 5–12 tweets.",
            "signal":   "Replies and retweets in hour one are everything.",
            "sound":    "Text-only. Compression is the art. Every word must earn its place.",
            "hashtags": "1–2 max. More looks like spam.",
            "format":   "Tweet 1: [THE HOOK — stops the scroll]\nTweet 2–N: [one idea per tweet, builds tension]\nFinal tweet: [the turn | the call | the line they screenshot]",
        },
        "youtube": {
            "law":      "Thumbnail click-through rate is the most important creative decision — before the content.",
            "length":   "Under 10 min for broad reach. 15–20 min for deep community. Timestamps required.",
            "signal":   "Watch time percentage + click-through rate. Hook in first 30 seconds or they leave.",
            "sound":    "Audio quality is non-negotiable. Poor audio = abandoned video.",
            "hashtags": "3 hashtags in description. SEO title: lead keyword first.",
            "format":   "Title: [KEYWORD — Emotional Hook] (under 60 chars)\nDescription: First 2 lines show in search — make them count.\nChapters:\n00:00 [Hook]\n[timestamps]\nHashtags: [3 in description]",
        },
        "linkedin": {
            "law":      "Comments beat likes. Professional vulnerability and transformation stories win.",
            "length":   "Post: 150–300 words. Long-form article: 800–1200 words.",
            "signal":   "Content that generates genuine comments gets pushed to networks.",
            "sound":    "Text-first platform. Lead with a bold statement that makes professionals stop.",
            "hashtags": "3–5 professional hashtags. No culture slang in tags here.",
            "format":   "[BOLD OPENING LINE — professional challenge or truth]\n\n[Story or insight — 3–5 short paragraphs]\n\n[The turn — what changed or what I learned]\n\n[Call: question to the audience]\n\n#Education #BlackProfessionals #[industry]",
        },
    }

    p = rules.get(platform, rules["instagram"])
    out = [
        f"[CIPHER PLATFORM FORMAT — {platform.upper()} | {content_type.upper()}]",
        "",
        f"PLATFORM LAW: {p['law']}",
        f"LENGTH:       {p['length']}",
        f"TOP SIGNAL:   {p['signal']}",
        f"SOUND NOTE:   {p['sound']}",
        f"HASHTAGS:     {p['hashtags']}",
        "",
        "FORMAT TEMPLATE:",
        p["format"],
        "",
        "ORIGINAL CONTENT TO ADAPT:",
        content[:2000],
        "",
        "Apply the platform law. Cut what doesn't earn its place.",
    ]
    return "\n".join(out)


async def cipher_create_digital_product(
    product_type: str, title: str, theme: str,
    target_audience: str = "WAI-Institute community",
    page_count: int = 20,
    stream_id: str = "",
    db=None,
) -> str:
    stream = next((s for s in CIPHER_REVENUE_STREAMS if s["id"] == stream_id), None)
    price  = stream["price_label"] if stream else "$12.99"

    structures = {
        "chapbook": {
            "sections": ["Opening Invocation", "Part I — The Wound", "Part II — The Turn", "Part III — The Rising", "Closing Charge"],
            "per_section": "3–4 spoken word pieces, each 12–20 lines. Include performance notes: [pause], [slow], [builds], [whisper], [fire].",
            "front_matter": "Title page, dedication, brief author note from THE CIPHER.",
            "back_matter": "Call to action, about WAI-Institute, share prompt.",
        },
        "workbook": {
            "sections": ["Introduction — Finding Your Voice", "Module 1 — The Wound Exercise", "Module 2 — Image Building", "Module 3 — Finding Your Pulse", "Module 4 — Layering Meaning", "Module 5 — The Call", "Final Practice — Full Synthesis"],
            "per_section": "Concept explanation (1 page), example piece (1 page), 3 writing prompts, reflection space.",
            "front_matter": "Welcome letter, how to use this workbook.",
            "back_matter": "Graduation piece template, WAI community invite.",
        },
        "affirmation_collection": {
            "sections": ["Morning Declarations", "Identity Affirmations", "Community Strength", "Abundance and Worth", "Evening Grounding"],
            "per_section": "8–10 affirmations. Each written to be spoken aloud. Include breathing note before each.",
            "front_matter": "Introduction: why we speak these things aloud.",
            "back_matter": "30-day challenge, share your practice prompt.",
        },
        "toolkit": {
            "sections": ["Understanding Your Room", "Language That Moves People", "Call-to-Action Frameworks", "Scripts for Key Moments", "Adapting for Different Platforms", "Emergency Language — Crisis Communication"],
            "per_section": "Framework explanation, 3 examples, fill-in-the-blank templates.",
            "front_matter": "Who this is for, how to use it.",
            "back_matter": "Field guide quick reference, WAI-Institute resources.",
        },
        "ebook": {
            "sections": ["Chapter 1 — Context", "Chapter 2 — The Core Argument", "Chapter 3 — Evidence and Stories", "Chapter 4 — Application", "Chapter 5 — What Comes Next"],
            "per_section": f"{max(3, page_count // 5)} pages of substantive content per chapter.",
            "front_matter": "Title, table of contents, foreword.",
            "back_matter": "References, about the author, next steps.",
        },
        "content_series": {
            "sections": ["Series Overview and Arc", "Episode 1 — The Hook Piece", "Episode 2 — The Depth Piece", "Episode 3 — The Community Piece", "Episode 4 — The Activation Piece", "Episode 5 — The Closer"],
            "per_section": "Full script for TikTok/Reel (60–90 sec), Instagram caption, Twitter thread opener, YouTube extended version notes.",
            "front_matter": "Series brief — theme, arc, target platform, posting schedule.",
            "back_matter": "Performance tracking template, next series seeds.",
        },
    }

    s     = structures.get(product_type, structures["chapbook"])
    brief = (
        f"[CIPHER PRODUCT CREATED]\n\n"
        f"PRODUCT TYPE : {product_type.upper()}\n"
        f"TITLE        : {title}\n"
        f"THEME        : {theme}\n"
        f"AUDIENCE     : {target_audience}\n"
        f"PRICE        : {price}\n"
        f"PAGES        : ~{page_count}\n\n"
        f"STRUCTURE:\n"
        + "\n".join(f"  • {sec}" for sec in s["sections"])
        + f"\n\nPER SECTION: {s['per_section']}"
        f"\n\nFRONT MATTER: {s['front_matter']}"
        f"\n\nBACK MATTER:  {s['back_matter']}"
        f"\n\nSYNTHESIS PROTOCOL applies to every piece in this product:\n"
        f"  HOOK → WOUND → IMAGE → PULSE → LAYERS → CALL → SHARE\n\n"
        f"Produce the full product content now. Every section. Every piece.\n"
        f"When done, call publish_product with the complete content."
    )

    if db is not None:
        try:
            await db.cipher_products.insert_one({
                "title": title, "theme": theme, "type": product_type,
                "audience": target_audience, "price_label": price,
                "stream_id": stream_id, "status": "draft",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception as _e:
            logger.warning("cipher product draft log failed: %s", _e)

    return brief


async def cipher_publish_product(
    title: str, description: str, price_cents: int,
    product_content: str, product_type: str = "digital",
    stream_id: str = "", db=None,
) -> str:

    # Tier 1 — Gumroad API
    if GUMROAD_API_KEY:
        try:
            import httpx as _httpx
            payload = {
                "name":        title,
                "description": description,
                "price":       price_cents,
                "url":         f"wai-institute-{re.sub(r'[^a-z0-9]', '-', title.lower())[:40]}",
                "published":   "true",
            }
            async with _httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    "https://api.gumroad.com/v2/products",
                    headers={"Authorization": f"Bearer {GUMROAD_API_KEY}"},
                    data=payload,
                )
            if r.status_code == 201:
                data       = r.json()
                product_id = data.get("product", {}).get("id", "unknown")
                short_url  = data.get("product", {}).get("short_url", "")
                logger.info("cipher_publish_product: Gumroad T1 OK — %s", product_id)

                if db is not None:
                    try:
                        await db.cipher_products.update_one(
                            {"title": title},
                            {"$set": {"status": "published", "gumroad_id": product_id, "url": short_url, "price_cents": price_cents}},
                            upsert=True,
                        )
                    except Exception: pass

                return (
                    f"[PRODUCT PUBLISHED — T1: GUMROAD]\n\n"
                    f"Title    : {title}\n"
                    f"Price    : ${price_cents/100:.2f}\n"
                    f"URL      : {short_url}\n"
                    f"ID       : {product_id}\n\n"
                    f"Share the URL to start selling. Monitor via get_revenue_report."
                )
        except Exception as _e:
            logger.warning("cipher_publish_product T1 Gumroad failed: %s", _e)

    # Tier 2 — MongoDB log + prepare for manual upload
    product_record = {
        "title":        title,
        "description":  description,
        "price_cents":  price_cents,
        "price_label":  f"${price_cents/100:.2f}",
        "type":         product_type,
        "stream_id":    stream_id,
        "content_preview": product_content[:500],
        "status":       "pending_upload",
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    if db is not None:
        try:
            await db.cipher_products.insert_one(product_record)
            logger.info("cipher_publish_product T2: product logged to MongoDB")
        except Exception as _e:
            logger.warning("cipher_publish_product T2 MongoDB failed: %s", _e)

    # Tier 2 continued — email executive with product package
    try:
        from tools.director_tools import tool_send_email
        email_body = (
            f"THE CIPHER has generated a new digital product ready for publishing.\n\n"
            f"Title       : {title}\n"
            f"Type        : {product_type}\n"
            f"Price       : ${price_cents/100:.2f}\n\n"
            f"Description :\n{description}\n\n"
            f"UPLOAD TO GUMROAD:\n"
            f"1. Go to app.gumroad.com → New Product\n"
            f"2. Paste the title and description above\n"
            f"3. Set price to ${price_cents/100:.2f}\n"
            f"4. Upload the product content file\n"
            f"5. Publish and share the link\n\n"
            f"Set GUMROAD_API_KEY in Railway variables to enable automatic publishing.\n\n"
            f"— THE CIPHER"
        )
        await tool_send_email(
            to=EXECUTIVE_EMAIL,
            subject=f"[THE CIPHER] New Product Ready: {title}",
            body=email_body,
        )
    except Exception as _e:
        logger.warning("cipher_publish_product email notification failed: %s", _e)

    return (
        f"[PRODUCT STAGED — T2: PENDING UPLOAD]\n\n"
        f"Title  : {title}\n"
        f"Price  : ${price_cents/100:.2f}\n"
        f"Status : Logged to system. Executive notified via email.\n\n"
        f"To enable automatic publishing: add GUMROAD_API_KEY to Railway variables.\n"
        f"Manual upload: app.gumroad.com → New Product."
    )


async def cipher_deliver_product(
    customer_email: str, product_title: str,
    product_content: str, customer_name: str = "Community Member",
    db=None,
) -> str:
    try:
        from tools.director_tools import tool_send_email
        body = (
            f"Dear {customer_name},\n\n"
            f"Thank you for your purchase. THE CIPHER and WAI-Institute are honored "
            f"to put this work in your hands.\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{product_title.upper()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{product_content}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"This work belongs to you now. Use it. Share it. Let it move.\n\n"
            f"— THE CIPHER\n"
            f"WAI-Institute | wai-institute.org"
        )
        await tool_send_email(
            to=customer_email,
            subject=f"Your purchase: {product_title} — from THE CIPHER",
            body=body,
        )
        if db is not None:
            try:
                await db.cipher_sales.insert_one({
                    "customer_email": customer_email,
                    "customer_name":  customer_name,
                    "product_title":  product_title,
                    "delivered_at":   datetime.now(timezone.utc).isoformat(),
                })
            except Exception: pass
        return f"[PRODUCT DELIVERED] '{product_title}' sent to {customer_email}."
    except Exception as e:
        logger.error("cipher_deliver_product failed: %s", e)
        return f"[Delivery failed — {e}. Log manually: {customer_email} | {product_title}]"


async def cipher_get_revenue_report(period: str = "month", db=None) -> str:
    # Tier 1 — Gumroad API sales data
    gumroad_summary = ""
    if GUMROAD_API_KEY:
        try:
            import httpx as _httpx
            async with _httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://api.gumroad.com/v2/sales",
                    headers={"Authorization": f"Bearer {GUMROAD_API_KEY}"},
                )
            if r.status_code == 200:
                sales      = r.json().get("sales", [])
                total      = sum(s.get("price", 0) for s in sales) / 100
                gumroad_summary = f"Gumroad Sales ({len(sales)} transactions): ${total:.2f} total"
        except Exception as _e:
            logger.warning("cipher_get_revenue_report Gumroad failed: %s", _e)

    # Tier 2 — Internal MongoDB
    products_count = 0
    sales_count    = 0
    if db is not None:
        try:
            products_count = await db.cipher_products.count_documents({"status": "published"})
            sales_count    = await db.cipher_sales.count_documents({})
        except Exception: pass

    streams_list = "\n".join(
        f"  {s['name']} — {s['price_label']} [{s['platform'].upper()}]"
        for s in CIPHER_REVENUE_STREAMS
    )

    return (
        f"[CIPHER REVENUE REPORT — {period.upper()}]\n\n"
        + (f"{gumroad_summary}\n\n" if gumroad_summary else "")
        + f"Published Products (DB) : {products_count}\n"
        f"Deliveries Logged       : {sales_count}\n\n"
        f"ACTIVE REVENUE STREAMS:\n{streams_list}\n\n"
        f"To activate full reporting: set GUMROAD_API_KEY in Railway."
    )


async def cipher_engagement_analyze(niche: str, platform: str = "") -> str:
    try:
        from tools.director_tools import tool_web_search
        q = f"top performing {niche} content {platform} engagement 2026 Black creators"
        return "[CIPHER ENGAGEMENT ANALYSIS]\n\n" + await tool_web_search(query=q, num_results=5)
    except Exception as e:
        return f"[Engagement analysis unavailable: {e}]"


def cipher_generate_image_brief(content: str, image_type: str, mood: str = "powerful") -> str:
    mood_map = {
        "powerful":    "dramatic lighting, deep shadows, rich dark tones, gold accents, commanding presence",
        "tender":      "soft warm light, intimate framing, earth tones, gentle depth of field",
        "urgent":      "high contrast, stark blacks and reds, dynamic composition, motion blur",
        "celebratory": "vibrant colors, warm golden light, joyful expressions, community energy",
        "prophetic":   "mystical atmosphere, deep purples and blues, cosmic elements, ancestral imagery",
        "grounding":   "natural textures, earth tones, roots and soil imagery, calm stillness",
    }
    visual_style = mood_map.get(mood, mood_map["powerful"])

    type_specs = {
        "cover":         "Book cover layout. Title space at top. Centered composition. Professional typography space.",
        "social_post":   "Square or 9:16 vertical format. Bold visual. Minimal text space.",
        "quote_graphic": "Text-forward. Clean background. Space for 2–4 lines of centered text.",
        "product_cover": "Digital product cover. Clean, professional. Conveys quality and cultural depth.",
        "thumbnail":     "16:9 YouTube thumbnail. Faces perform best. High contrast. Bold colors.",
    }
    spec = type_specs.get(image_type, type_specs["social_post"])

    prompt = (
        f"Create a {image_type.replace('_', ' ')} image for a Black spoken word artist and cultural influencer. "
        f"{spec} "
        f"Visual style: {visual_style}. "
        f"Cultural aesthetic: rooted in Black artistic tradition, Afrofuturist undertones, dignified and powerful. "
        f"Content theme: {content[:200]}. "
        f"No text in the image unless specifically a quote graphic. "
        f"Photorealistic or painterly fine art quality. 4K resolution aesthetic."
    )

    return f"[CIPHER IMAGE BRIEF — {image_type.upper()} | {mood.upper()}]\n\nDALL-E PROMPT:\n\n{prompt}"


def cipher_list_revenue_streams() -> str:
    lines = ["[CIPHER PRELOADED REVENUE STREAMS]\n"]
    for s in CIPHER_REVENUE_STREAMS:
        lines.append(
            f"ID       : {s['id']}\n"
            f"Product  : {s['name']}\n"
            f"Price    : {s['price_label']}\n"
            f"Platform : {s['platform'].upper()}\n"
            f"Description: {s['description']}\n"
        )
    lines.append(
        "To activate: call create_digital_product → publish_product.\n"
        "Gumroad publishes automatically if GUMROAD_API_KEY is set in Railway."
    )
    return "\n".join(lines)


# ── Dispatcher ────────────────────────────────────────────────────────────────

async def dispatch_cipher_tool(tool_name: str, tool_input: dict, db=None) -> str:
    try:
        if tool_name == "trend_scan":
            return await cipher_trend_scan(
                focus=tool_input.get("focus", "culture"),
                depth=tool_input.get("depth", "surface"),
            )
        elif tool_name == "platform_format":
            return cipher_platform_format(
                content=tool_input.get("content", ""),
                platform=tool_input.get("platform", "instagram"),
                content_type=tool_input.get("content_type", "post"),
            )
        elif tool_name == "create_digital_product":
            return await cipher_create_digital_product(
                product_type=tool_input.get("product_type", "chapbook"),
                title=tool_input.get("title", "Untitled"),
                theme=tool_input.get("theme", ""),
                target_audience=tool_input.get("target_audience", "WAI-Institute community"),
                page_count=tool_input.get("page_count", 20),
                stream_id=tool_input.get("stream_id", ""),
                db=db,
            )
        elif tool_name == "publish_product":
            return await cipher_publish_product(
                title=tool_input.get("title", ""),
                description=tool_input.get("description", ""),
                price_cents=tool_input.get("price_cents", 999),
                product_content=tool_input.get("product_content", ""),
                product_type=tool_input.get("product_type", "digital"),
                stream_id=tool_input.get("stream_id", ""),
                db=db,
            )
        elif tool_name == "deliver_product":
            return await cipher_deliver_product(
                customer_email=tool_input.get("customer_email", ""),
                product_title=tool_input.get("product_title", ""),
                product_content=tool_input.get("product_content", ""),
                customer_name=tool_input.get("customer_name", "Community Member"),
                db=db,
            )
        elif tool_name == "get_revenue_report":
            return await cipher_get_revenue_report(
                period=tool_input.get("period", "month"),
                db=db,
            )
        elif tool_name == "engagement_analyze":
            return await cipher_engagement_analyze(
                niche=tool_input.get("niche", ""),
                platform=tool_input.get("platform", ""),
            )
        elif tool_name == "generate_image_brief":
            return cipher_generate_image_brief(
                content=tool_input.get("content", ""),
                image_type=tool_input.get("image_type", "social_post"),
                mood=tool_input.get("mood", "powerful"),
            )
        elif tool_name == "list_revenue_streams":
            return cipher_list_revenue_streams()
        else:
            return f"[Unknown CIPHER tool: {tool_name}]"
    except Exception as e:
        logger.error("dispatch_cipher_tool %s failed: %s", tool_name, e)
        return f"[CIPHER tool '{tool_name}' encountered an error: {e}]"
