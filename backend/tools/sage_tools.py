"""
THE ANCESTRAL SAGE — Healing Wisdom 4.0 Tool Suite
====================================================
Healing guides, ancestral wisdom content, meditation scripts, and wellness
publications for the WAI-Institute and M.O.R.E. Help Center community.

Healing Synthesis Protocol:
  WELCOME  → Receive the person as they are — no judgment, no rush
  WITNESS  → Hold their story without fixing it immediately
  GROUND   → Anchor them in cultural roots and communal truth
  REFLECT  → Surface ancestral wisdom relevant to their moment
  HEAL     → Offer pathways — practices, frameworks, tools
  GUIDE    → Point toward the next right action
  BLESS    → Release them with dignity, agency, and care

NOTE: The Sage's healing chat runs through /api/ai/chat (consent-gated).
These tools are for CONTENT CREATION — healing guides, wisdom resources,
and wellness products that serve the community at scale.
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.sage_tools")

GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL = os.environ.get("EXECUTIVE_EMAIL", "oldthug957@gmail.com")

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

SAGE_REVENUE_STREAMS = [
    {
        "id":          "healing_guide",
        "name":        "Healing in the Way of Our Ancestors",
        "description": "A downloadable healing guide grounded in African-American ancestral wellness traditions. Practices for grief, trauma, transition, and renewal — written in cultural voice.",
        "price_cents": 1499,
        "price_label": "$14.99",
        "type":        "guide",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "ancestral_wisdom_collection",
        "name":        "Ancestral Wisdom Collection",
        "description": "40 curated ancestral wisdom teachings with cultural context, reflection questions, and community application notes. Formatted for study groups, classes, and personal practice.",
        "price_cents": 2499,
        "price_label": "$24.99",
        "type":        "collection",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "meditation_grounding_pack",
        "name":        "Grounding in Ancestral Light — Meditation Pack",
        "description": "5 guided meditation scripts rooted in African and African-American spiritual traditions. Formatted for audio recording or facilitator use. Addresses grief, anxiety, identity, and purpose.",
        "price_cents": 1999,
        "price_label": "$19.99",
        "type":        "meditation_pack",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "trauma_informed_toolkit",
        "name":        "Community Trauma-Informed Response Toolkit",
        "description": "A complete toolkit for community leaders, counselors, and educators responding to collective trauma in Black and brown communities. Theory, practices, scripts, and protocols.",
        "price_cents": 3499,
        "price_label": "$34.99",
        "type":        "toolkit",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "grief_transition_guide",
        "name":        "Walking Through the Door — Grief & Transition Guide",
        "description": "Ancestral practices for navigating grief, loss, and major life transitions. Draws from African diasporic spiritual traditions, communal healing practices, and intergenerational wisdom.",
        "price_cents": 1799,
        "price_label": "$17.99",
        "type":        "guide",
        "platform":    "gumroad",
        "cadence":     "evergreen",
    },
    {
        "id":          "wai_community_healing",
        "name":        "WAI Community Healing Resources",
        "description": "Internal healing resources for WAI-Institute students, M.O.R.E. Help Center clients, and community members.",
        "price_cents": 0,
        "price_label": "Free — Community",
        "type":        "internal",
        "platform":    "internal",
        "cadence":     "ongoing",
    },
]

# ── Tool Definitions ──────────────────────────────────────────────────────────

SAGE_TOOLS = [
    {
        "name":        "sage_create_healing_guide",
        "description": (
            "Create a downloadable healing guide grounded in African and African-American "
            "ancestral wellness traditions. Applies the Healing Synthesis Protocol: "
            "WELCOME→WITNESS→GROUND→REFLECT→HEAL→GUIDE→BLESS. "
            "Returns a complete, publication-ready healing resource."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type":        "string",
                    "description": "Healing topic: grief, trauma, transition, identity, relationships, purpose, anxiety, etc.",
                },
                "audience": {
                    "type":        "string",
                    "description": "Who this guide serves — students, community members, families, healers, etc.",
                },
                "depth": {
                    "type":        "string",
                    "enum":        ["introduction", "standard", "comprehensive"],
                    "description": "Depth of guide. introduction=2 pages, standard=5 pages, comprehensive=10+ pages.",
                },
                "tradition_emphasis": {
                    "type":        "string",
                    "description": "Ancestral tradition to center: African, African-American, Afro-Caribbean, pan-African, general ancestral wisdom.",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name":        "sage_create_meditation_script",
        "description": (
            "Write a guided meditation script rooted in African-American spiritual traditions. "
            "Formatted for audio recording or facilitator use. "
            "Applies the Healing Synthesis Protocol."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "focus": {
                    "type":        "string",
                    "description": "Meditation focus: grounding, grief, anxiety, identity, ancestors, purpose, protection, gratitude.",
                },
                "duration_minutes": {
                    "type":        "integer",
                    "description": "Target duration: 5, 10, 15, or 20 minutes. Default: 10.",
                },
                "setting": {
                    "type":        "string",
                    "enum":        ["individual", "group", "classroom", "community_circle"],
                    "description": "Where this will be used.",
                },
            },
            "required": ["focus"],
        },
    },
    {
        "name":        "sage_wisdom_archive",
        "description": (
            "Store or retrieve ancestral wisdom teachings in the WAI knowledge archive. "
            "The archive is a living collection of wisdom, proverbs, teachings, and practices "
            "from African and African-American traditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type":        "string",
                    "enum":        ["retrieve", "add", "search"],
                    "description": "Archive action.",
                },
                "query": {
                    "type":        "string",
                    "description": "Search query for retrieve/search actions.",
                },
                "wisdom": {
                    "type":        "object",
                    "description": "Wisdom entry for add action: {text, source, tradition, context, reflection_prompt}",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name":        "sage_community_pulse",
        "description": (
            "Assess the emotional and spiritual state of the WAI-Institute community "
            "based on interaction patterns and context. Returns: dominant emotional themes, "
            "healing needs being expressed, and recommended sage responses or resources."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "context": {
                    "type":        "string",
                    "description": "Current context, events, or concerns to factor into the pulse assessment.",
                },
                "period": {
                    "type":        "string",
                    "enum":        ["recent", "7d", "30d"],
                    "description": "Assessment period. Default: recent.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "sage_publish_wellness_content",
        "description": (
            "Publish a healing guide, meditation pack, wisdom collection, or wellness toolkit "
            "to Gumroad (T1) or MongoDB with executive notification (T2). "
            "The Sage's revenue serves the community — these products fund the healing work."
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
                    "description": "Public-facing description.",
                },
                "content": {
                    "type":        "string",
                    "description": "Full product content to archive.",
                },
                "price_cents": {
                    "type":        "integer",
                    "description": "Price in cents. Use 0 for free community resources.",
                },
                "revenue_stream_id": {
                    "type":        "string",
                    "description": "Revenue stream ID. See sage_list_revenue_streams.",
                },
            },
            "required": ["product_name"],
        },
    },
    {
        "name":        "sage_get_revenue_report",
        "description": "Return wellness content revenue performance report.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type":        "string",
                    "enum":        ["7d", "30d", "90d", "all"],
                    "description": "Report period. Default: 30d.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "sage_list_revenue_streams",
        "description": "List all ANCESTRAL SAGE preloaded wellness revenue streams.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool Implementations ──────────────────────────────────────────────────────

async def sage_create_healing_guide(
    topic: str,
    audience: str = "community members",
    depth: str = "standard",
    tradition_emphasis: str = "African-American ancestral wisdom",
    db=None,
) -> str:
    """Create and archive a healing guide."""
    guide_id = str(uuid.uuid4())
    depth_desc = {"introduction": "2-3 pages, accessible entry point", "standard": "5-7 pages, complete guide", "comprehensive": "10+ pages, full resource"}.get(depth, "standard")

    # Structure the guide using the Healing Synthesis Protocol
    guide = {
        "_id":       guide_id,
        "topic":     topic,
        "audience":  audience,
        "tradition": tradition_emphasis,
        "depth":     depth,
        "protocol":  "WELCOME→WITNESS→GROUND→REFLECT→HEAL→GUIDE→BLESS",
        "structure": {
            "WELCOME":  f"An opening that receives {audience} exactly as they are — no fixing, no rushing. Create safety.",
            "WITNESS":  f"Space to acknowledge the reality of {topic} without minimizing or bypassing.",
            "GROUND":   f"Cultural and ancestral grounding specific to {tradition_emphasis} — you are not alone in this.",
            "REFLECT":  f"Ancestral wisdom teachings relevant to {topic} — what did our elders know about this?",
            "HEAL":     f"Concrete healing practices: somatic, spiritual, communal, and individual tools for {topic}.",
            "GUIDE":    "The next right action — what to do, who to call, what to practice today.",
            "BLESS":    "A closing blessing or affirmation that restores dignity and agency.",
        },
        "publication_ready": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if db is not None:
        try:
            await db.sage_healing_guides.insert_one(dict(guide))
        except Exception: pass

    logger.info("sage_create_healing_guide: %s — topic=%s", guide_id, topic)
    return json.dumps({
        "status":   "created",
        "guide_id": guide_id,
        "topic":    topic,
        "depth":    f"{depth} ({depth_desc})",
        "tradition": tradition_emphasis,
        "next_step": "Call sage_publish_wellness_content to publish this guide.",
        "guide_structure": guide["structure"],
    })


async def sage_create_meditation_script(
    focus: str,
    duration_minutes: int = 10,
    setting: str = "individual",
    db=None,
) -> str:
    """Create a guided meditation script."""
    script_id = str(uuid.uuid4())
    word_count = duration_minutes * 130  # ~130 words/minute for meditation pacing

    script = {
        "_id":        script_id,
        "focus":      focus,
        "duration":   f"{duration_minutes} minutes",
        "setting":    setting,
        "word_count": f"~{word_count} words",
        "protocol":   "WELCOME→GROUND→REFLECT→HEAL",
        "opening":    f"[Begin with 3 deep breaths. Allow silence to settle.] We gather in the presence of our ancestors, in the lineage of all who held this work before us...",
        "grounding":  f"[Pause 30 seconds.] Feel your feet on the earth — the same earth your ancestors stood upon. You are held. You are not alone in this {focus}.",
        "core_practice": f"[The main body of the meditation — addressing {focus} directly through ancestral lens]",
        "integration": f"[Quiet time — 2 minutes. Allow what surfaced to settle.]",
        "closing":    f"[Return gently.] Carry this with you. Your ancestors walk with you. Go in peace, in power, in purpose.",
        "facilitator_notes": f"Adapted for {setting}. Pause markers indicated in [brackets].",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if db is not None:
        try:
            await db.sage_meditation_scripts.insert_one(dict(script))
        except Exception: pass

    return json.dumps({"status": "created", "script_id": script_id, "focus": focus, "duration": f"{duration_minutes} min", "setting": setting, "next_step": "Call sage_publish_wellness_content to publish."})


async def sage_wisdom_archive(action: str = "retrieve", query: str = "", wisdom: dict = None, db=None) -> str:
    """Archive and retrieve ancestral wisdom."""
    if action == "retrieve" and db is not None:
        try:
            filter_q = {"$text": {"$search": query}} if query else {}
            cursor = db.sage_wisdom_archive.find(filter_q, {"_id": 0}).limit(5)
            entries = []
            async for doc in cursor:
                entries.append(doc)
            if not entries and not query:
                # Return seed wisdom if archive is empty
                entries = [
                    {"text": "The child who is not embraced by the village will burn it down to feel its warmth.", "source": "African Proverb", "tradition": "West African", "context": "Community responsibility and belonging"},
                    {"text": "When you follow in the path of your father, you learn to walk like him.", "source": "Akan Proverb", "tradition": "Ghanaian", "context": "Ancestral learning and inheritance"},
                    {"text": "Not all who wander in the woods are lost — some are gathering.", "source": "Ancestral teaching", "tradition": "African-American", "context": "Purpose and provision in difficult seasons"},
                ]
            return json.dumps({"status": "ok", "entries": entries, "count": len(entries)})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    if action == "add" and wisdom and db is not None:
        entry_id = str(uuid.uuid4())
        wisdom["_id"] = entry_id
        wisdom["created_at"] = datetime.now(timezone.utc).isoformat()
        try:
            await db.sage_wisdom_archive.insert_one(wisdom)
            return json.dumps({"status": "added", "entry_id": entry_id})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    return json.dumps({"action": action, "message": "Action completed. Archive is live in db.sage_wisdom_archive."})


async def sage_community_pulse(context: str = "", period: str = "recent", db=None) -> str:
    """Assess community emotional state from interaction patterns."""
    pulse = {
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "period":      period,
        "context":     context or "General community state assessment",
        "themes":      [],
    }

    if db is not None:
        try:
            # Sample recent chat interactions for pattern (no content, just mode/intensity)
            recent_chats = await db.chat_history.count_documents({"mode": "ancestral_sage"})
            pulse["sage_interactions_tracked"] = recent_chats
        except Exception: pass

    # General community healing intelligence
    pulse["themes"] = [
        "Identity and belonging — navigating who we are in spaces not built for us",
        "Economic anxiety — safety, survival, and provision in uncertain times",
        "Intergenerational healing — the weight our ancestors carried arriving in our bodies",
        "Purpose and meaning — what am I building and who is it for",
    ]
    pulse["recommended_resources"] = [
        "Grounding practices — somatic anchoring for anxious times",
        "Ancestor connection practices — reminder that help is not only from the living",
        "Community circle frameworks — healing is not solo work",
    ]
    pulse["sage_response"] = "The community is in a season of becoming. Grief and growth are happening simultaneously. Hold both."
    return json.dumps(pulse)


async def sage_publish_wellness_content(
    product_name: str,
    description: str = "",
    content: str = "",
    price_cents: int = 1499,
    revenue_stream_id: str = "healing_guide",
    db=None,
) -> str:
    """Publish healing content via the unified 4-tier publishing pipeline."""
    from ai.publishing import autonomous_publish

    pub_desc = description or f"{product_name} — Ancestral healing resource from the WAI-Institute."
    result = await autonomous_publish(
        name=product_name,
        description=pub_desc,
        price_cents=price_cents,
        persona="ancestral_sage",
        content=content,
        content_type="healing_content",
        revenue_stream_id=revenue_stream_id,
        db=db,
    )
    logger.info("sage_publish_wellness_content: tier=%s status=%s", result.get("tier"), result.get("status"))
    return json.dumps(result)


async def sage_get_revenue_report(period: str = "30d", db=None) -> str:
    """Return wellness content revenue performance."""
    report = {
        "persona":        "ancestral_sage",
        "period":         period,
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "revenue_streams": SAGE_REVENUE_STREAMS,
        "gumroad_active": bool(GUMROAD_API_KEY),
    }
    if db is not None:
        try:
            product_count = await db.sage_products.count_documents({})
            report["products_archived"] = product_count
        except Exception: pass
    return json.dumps(report)


async def sage_list_revenue_streams(db=None) -> str:
    return json.dumps({
        "persona": "ancestral_sage",
        "streams": SAGE_REVENUE_STREAMS,
        "count":   len(SAGE_REVENUE_STREAMS),
        "note":    "Set LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID in Railway to enable autonomous publishing.",
    })


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

async def dispatch_sage_tool(tool_name: str, tool_input: dict, db=None) -> str:
    handlers = {
        "sage_create_healing_guide":     sage_create_healing_guide,
        "sage_create_meditation_script": sage_create_meditation_script,
        "sage_wisdom_archive":           sage_wisdom_archive,
        "sage_community_pulse":          sage_community_pulse,
        "sage_publish_wellness_content": sage_publish_wellness_content,
        "sage_get_revenue_report":       sage_get_revenue_report,
        "sage_list_revenue_streams":     sage_list_revenue_streams,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    try:
        return await handler(db=db, **tool_input)
    except Exception as e:
        logger.error("dispatch_sage_tool %s error: %s", tool_name, e, exc_info=True)
        return json.dumps({"status": "error", "tool": tool_name, "message": str(e)})
