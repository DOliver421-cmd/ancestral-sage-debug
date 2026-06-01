"""
THE AMBASSADOR — Campaign Coordination 4.0 Tool Suite
======================================================
Orchestrates the Oracle → Cipher → Architect pipeline for full campaign
production. Manages active projects, packages deliverables, and publishes
to revenue channels independently.

The Ambassador thinks from three intelligence positions simultaneously:
  - Oracle lens:   What the culture is saying and when to move
  - Cipher lens:   What content will land and how to deliver it
  - Architect lens: What the visual identity needs to express

Revenue channels run autonomously via Gumroad (T1) or MongoDB + email (T2).
"""

import os
import json
import uuid
import logging
from datetime import datetime, timezone

import anthropic as _anthropic_module

logger = logging.getLogger("lcewai.ambassador")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
GUMROAD_API_KEY   = os.environ.get("GUMROAD_API_KEY", "")
EXECUTIVE_EMAIL   = os.environ.get("EXECUTIVE_EMAIL", "oldthug957@gmail.com")

# ── Preloaded Revenue Stream Catalog ─────────────────────────────────────────

AMBASSADOR_REVENUE_STREAMS = [
    {
        "id":          "full_campaign_package",
        "name":        "Full Campaign Package",
        "description": "Complete coordinated campaign: Oracle intelligence brief + Cipher spoken word content + Architect visual assets. Delivered as a unified creative package.",
        "price_cents": 19900,
        "price_label": "$199.00",
        "type":        "package",
        "platform":    "gumroad",
        "cadence":     "per-project",
    },
    {
        "id":          "quarterly_content_calendar",
        "name":        "Quarterly Content Calendar",
        "description": "13-week coordinated content plan across all platforms with cultural timing, spoken word scripts, and visual brief for each week.",
        "price_cents": 34900,
        "price_label": "$349.00",
        "type":        "bundle",
        "platform":    "gumroad",
        "cadence":     "quarterly",
    },
    {
        "id":          "launch_campaign_kit",
        "name":        "Launch Campaign Kit",
        "description": "Full launch sequence for a product, program, or movement: cultural intelligence → content suite → brand visual package. Ready to execute.",
        "price_cents": 29900,
        "price_label": "$299.00",
        "type":        "kit",
        "platform":    "gumroad",
        "cadence":     "per-launch",
    },
    {
        "id":          "movement_intelligence_brief",
        "name":        "Movement Intelligence Brief",
        "description": "Strategic campaign brief powered by Oracle cultural intelligence — timing, messaging angles, community resonance analysis, and platform matrix.",
        "price_cents": 7999,
        "price_label": "$79.99",
        "type":        "brief",
        "platform":    "gumroad",
        "cadence":     "per-movement",
    },
    {
        "id":          "community_activation_pack",
        "name":        "Community Activation Pack",
        "description": "Engagement campaign for WAI-Institute community members: spoken word activation pieces + shareable visual assets + cultural timing guide.",
        "price_cents": 9999,
        "price_label": "$99.99",
        "type":        "activation",
        "platform":    "gumroad",
        "cadence":     "seasonal",
    },
    {
        "id":          "wai_campaign_production",
        "name":        "WAI Internal Campaign",
        "description": "Internal campaign production for WAI-Institute programs and M.O.R.E. Help Center initiatives.",
        "price_cents": 0,
        "price_label": "Internal",
        "type":        "internal",
        "platform":    "internal",
        "cadence":     "as-needed",
    },
]

# ── Tool Definitions (Anthropic API format) ───────────────────────────────────

AMBASSADOR_TOOLS = [
    {
        "name":        "ambassador_coordinate_oracle",
        "description": (
            "Run THE ORACLE's intelligence cycle on a topic or campaign objective. "
            "Returns a structured cultural intelligence brief: timing analysis, audience sentiment, "
            "content angles, and strategic recommendations. Use this FIRST before creating content."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type":        "string",
                    "description": "The campaign topic, movement, or cultural question to analyze."
                },
                "campaign_context": {
                    "type":        "string",
                    "description": "Campaign objective, target audience, and any relevant context.",
                },
                "depth": {
                    "type":        "string",
                    "enum":        ["quick", "standard", "deep"],
                    "description": "Analysis depth. quick=500 tokens, standard=1000, deep=1500. Default: standard.",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name":        "ambassador_coordinate_cipher",
        "description": (
            "Direct THE CIPHER to create content for a campaign. Pass the Oracle intelligence brief "
            "and content format. Returns spoken word content following the Synthesis Protocol: "
            "HOOK→WOUND→IMAGE→PULSE→LAYERS→CALL→SHARE."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "directive": {
                    "type":        "string",
                    "description": "The creative directive for THE CIPHER — topic, emotional core, call to action.",
                },
                "oracle_brief": {
                    "type":        "string",
                    "description": "Intelligence brief from Oracle to inform cultural grounding.",
                },
                "format": {
                    "type":        "string",
                    "enum":        ["spoken_word", "caption", "thread", "verse", "manifesto", "testimonial"],
                    "description": "Content format. Default: spoken_word.",
                },
                "platform": {
                    "type":        "string",
                    "enum":        ["instagram", "tiktok", "youtube", "twitter_x", "facebook", "podcast", "all"],
                    "description": "Target platform for format optimization. Default: all.",
                },
            },
            "required": ["directive"],
        },
    },
    {
        "name":        "ambassador_coordinate_architect",
        "description": (
            "Brief THE ARCHITECT to develop the visual direction for a campaign. "
            "Returns a visual intelligence brief: design concept, color palette, image prompts, "
            "typography direction, and asset checklist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_concept": {
                    "type":        "string",
                    "description": "The campaign concept, emotional tone, and key visual message.",
                },
                "cipher_content_summary": {
                    "type":        "string",
                    "description": "Summary of THE CIPHER's content to align visual language.",
                },
                "brand_context": {
                    "type":        "string",
                    "description": "Brand guidelines, color preferences, style notes. Leave blank for WAI-Institute defaults.",
                },
                "asset_types": {
                    "type":        "array",
                    "items":       {"type": "string"},
                    "description": "Which assets to brief: cover_art, social_post, story, banner, thumbnail, etc.",
                },
            },
            "required": ["campaign_concept"],
        },
    },
    {
        "name":        "ambassador_package_campaign",
        "description": (
            "Package a completed campaign (Oracle brief + Cipher content + Architect visual brief) "
            "into a structured deliverable stored in MongoDB. Returns a campaign ID for publishing. "
            "Call this after coordinating all three personas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_name": {
                    "type":        "string",
                    "description": "Short, descriptive campaign name.",
                },
                "oracle_brief": {
                    "type":        "string",
                    "description": "Cultural intelligence brief from Oracle.",
                },
                "cipher_content": {
                    "type":        "string",
                    "description": "Spoken word / content from Cipher.",
                },
                "architect_brief": {
                    "type":        "string",
                    "description": "Visual intelligence brief from Architect.",
                },
                "target_audience": {
                    "type":        "string",
                    "description": "Who this campaign serves.",
                },
                "revenue_stream_id": {
                    "type":        "string",
                    "description": "Which revenue stream to publish under. See list_revenue_streams.",
                },
            },
            "required": ["campaign_name", "oracle_brief", "cipher_content"],
        },
    },
    {
        "name":        "ambassador_publish_campaign",
        "description": (
            "Publish a packaged campaign to revenue channels. "
            "Tier 1: Gumroad product listing (autonomous, no human needed). "
            "Tier 2: MongoDB archive + email delivery. "
            "Tier 3: Executive notification only."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type":        "string",
                    "description": "MongoDB campaign ID from ambassador_package_campaign.",
                },
                "price_cents": {
                    "type":        "integer",
                    "description": "Price in cents. 0 for free/internal. Use revenue stream price if not specified.",
                },
                "description": {
                    "type":        "string",
                    "description": "Public-facing campaign description for Gumroad listing.",
                },
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name":        "ambassador_request_director_approval",
        "description": (
            "Flag a campaign or decision for Director/executive review before proceeding. "
            "Logs to MongoDB and sends executive notification. Use for campaigns over $100 "
            "or when uncertain about cultural sensitivity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type":        "string",
                    "description": "Campaign ID to flag for review.",
                },
                "summary": {
                    "type":        "string",
                    "description": "Summary of what needs approval and why.",
                },
                "urgency": {
                    "type":        "string",
                    "enum":        ["low", "standard", "high"],
                    "description": "Approval urgency level.",
                },
            },
            "required": ["summary"],
        },
    },
    {
        "name":        "ambassador_get_campaign_status",
        "description": "Retrieve the current status and deliverables of an active campaign from MongoDB.",
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_id": {
                    "type":        "string",
                    "description": "Campaign ID to look up.",
                },
            },
            "required": ["campaign_id"],
        },
    },
    {
        "name":        "ambassador_list_active_campaigns",
        "description": "List all active campaigns and their pipeline status (draft, in-production, packaged, published).",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type":        "string",
                    "enum":        ["all", "draft", "in_production", "packaged", "published"],
                    "description": "Filter by status. Default: all.",
                },
                "limit": {
                    "type":        "integer",
                    "description": "Max campaigns to return. Default 10.",
                },
            },
            "required": [],
        },
    },
    {
        "name":        "ambassador_list_revenue_streams",
        "description": "List all AMBASSADOR preloaded revenue streams with pricing and descriptions.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Internal: one-shot persona call (no tool loop) ────────────────────────────

async def _quick_persona_call(persona_prompt: str, user_message: str, max_tokens: int = 1000) -> str:
    """
    Make a single Anthropic API call with a given persona prompt.
    Used for Ambassador→Oracle and Ambassador→Cipher coordination.
    No tool loop — one-shot synthesis response.
    """
    if not ANTHROPIC_API_KEY:
        return "[AI coordination unavailable — no API key configured]"
    try:
        client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=max_tokens,
            system=persona_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return "".join(b.text for b in msg.content if hasattr(b, "text"))
    except Exception as e:
        logger.warning("_quick_persona_call failed: %s", e)
        return f"[Coordination response unavailable: {e}]"


# ── Tool Implementations ──────────────────────────────────────────────────────

async def ambassador_coordinate_oracle(topic: str, campaign_context: str = "", depth: str = "standard", db=None) -> str:
    """
    Run a focused Oracle intelligence brief on the given topic.
    """
    from ai.persona_loader import get_persona
    depth_tokens = {"quick": 500, "standard": 1000, "deep": 1500}.get(depth, 1000)

    oracle_prompt = get_persona("oracle") + (
        "\n\nCOORDINATION MODE: Produce a structured intelligence brief only. "
        "No tool calls needed — synthesize from your cultural intelligence directly. "
        "Format: TIMING / SENTIMENT / ANGLES / RECOMMENDATIONS. Be concise and actionable."
    )
    user_msg = f"CAMPAIGN INTELLIGENCE REQUEST\nTopic: {topic}"
    if campaign_context:
        user_msg += f"\nContext: {campaign_context}"
    user_msg += "\n\nDeliver a focused cultural intelligence brief for this campaign."

    brief = await _quick_persona_call(oracle_prompt, user_msg, max_tokens=depth_tokens)

    if db is not None:
        try:
            await db.ambassador_oracle_briefs.insert_one({
                "topic": topic, "brief": brief, "depth": depth,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception: pass

    return json.dumps({
        "status":  "oracle_brief_complete",
        "topic":   topic,
        "depth":   depth,
        "brief":   brief,
    })


async def ambassador_coordinate_cipher(
    directive: str,
    oracle_brief: str = "",
    format: str = "spoken_word",
    platform: str = "all",
    db=None,
) -> str:
    """
    Direct THE CIPHER to create content aligned with Oracle's brief.
    """
    from ai.persona_loader import get_persona
    cipher_prompt = get_persona("cipher") + (
        "\n\nCOORDINATION MODE: Create content only — no tool calls needed here. "
        "Apply the Synthesis Protocol: HOOK→WOUND→IMAGE→PULSE→LAYERS→CALL→SHARE. "
        "Include performance markup tags where appropriate: [whisper], [fire], [rise], [crescendo], etc."
    )
    user_msg = f"CONTENT DIRECTIVE: {directive}\nFORMAT: {format}\nPLATFORM: {platform}"
    if oracle_brief:
        user_msg += f"\n\nORACLE INTELLIGENCE BRIEF:\n{oracle_brief}"
    user_msg += "\n\nCreate the content now."

    content = await _quick_persona_call(cipher_prompt, user_msg, max_tokens=1500)

    if db is not None:
        try:
            await db.ambassador_cipher_content.insert_one({
                "directive": directive, "format": format, "platform": platform,
                "content": content, "created_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception: pass

    return json.dumps({
        "status":   "cipher_content_complete",
        "format":   format,
        "platform": platform,
        "content":  content,
    })


async def ambassador_coordinate_architect(
    campaign_concept: str,
    cipher_content_summary: str = "",
    brand_context: str = "",
    asset_types: list = None,
    db=None,
) -> str:
    """
    Brief THE ARCHITECT to develop the visual direction for the campaign.
    """
    from ai.persona_loader import get_persona
    architect_prompt = get_persona("architect") + (
        "\n\nCOORDINATION MODE: Produce a visual intelligence brief only — no image generation needed here. "
        "Format: CONCEPT / PALETTE / TYPOGRAPHY / IMAGE DIRECTION / ASSET CHECKLIST."
    )
    assets = ", ".join(asset_types) if asset_types else "cover_art, social_post, story"
    user_msg = (
        f"VISUAL DIRECTION REQUEST\n"
        f"Campaign Concept: {campaign_concept}\n"
        f"Assets Needed: {assets}"
    )
    if cipher_content_summary:
        user_msg += f"\n\nCipher Content Summary:\n{cipher_content_summary}"
    if brand_context:
        user_msg += f"\n\nBrand Context:\n{brand_context}"
    user_msg += "\n\nDeliver a complete visual intelligence brief."

    brief = await _quick_persona_call(architect_prompt, user_msg, max_tokens=1200)

    return json.dumps({
        "status":          "architect_brief_complete",
        "campaign_concept": campaign_concept,
        "assets_briefed":  assets,
        "visual_brief":    brief,
    })


async def ambassador_package_campaign(
    campaign_name: str,
    oracle_brief: str,
    cipher_content: str,
    architect_brief: str = "",
    target_audience: str = "",
    revenue_stream_id: str = "full_campaign_package",
    db=None,
) -> str:
    """
    Package a complete campaign into MongoDB and return the campaign_id.
    """
    campaign_id = str(uuid.uuid4())
    revenue_stream = next(
        (s for s in AMBASSADOR_REVENUE_STREAMS if s["id"] == revenue_stream_id),
        AMBASSADOR_REVENUE_STREAMS[0],
    )
    doc = {
        "_id":              campaign_id,
        "name":             campaign_name,
        "status":           "packaged",
        "oracle_brief":     oracle_brief,
        "cipher_content":   cipher_content,
        "architect_brief":  architect_brief,
        "target_audience":  target_audience,
        "revenue_stream":   revenue_stream,
        "price_cents":      revenue_stream["price_cents"],
        "gumroad_url":      None,
        "created_at":       datetime.now(timezone.utc).isoformat(),
        "updated_at":       datetime.now(timezone.utc).isoformat(),
    }

    if db is not None:
        try:
            await db.ambassador_campaigns.insert_one(doc)
            logger.info("ambassador_package_campaign: packaged %s — %s", campaign_id, campaign_name)
        except Exception as e:
            logger.warning("ambassador_package_campaign DB write failed: %s", e)

    return json.dumps({
        "status":      "packaged",
        "campaign_id": campaign_id,
        "name":        campaign_name,
        "price":       revenue_stream["price_label"],
        "next_step":   "Call ambassador_publish_campaign to send to revenue channels.",
    })


async def ambassador_publish_campaign(
    campaign_id: str,
    price_cents: int = None,
    description: str = "",
    db=None,
) -> str:
    """
    Publish a packaged campaign. Tier 1: Gumroad. Tier 2: MongoDB+email. Tier 3: exec notification.
    """
    campaign = None
    if db is not None:
        try:
            campaign = await db.ambassador_campaigns.find_one({"_id": campaign_id})
        except Exception: pass

    if not campaign:
        return json.dumps({"status": "error", "message": f"Campaign {campaign_id} not found."})

    final_price = price_cents if price_cents is not None else campaign.get("price_cents", 0)
    pub_desc = description or (
        f"{campaign['name']} — A full campaign package from the WAI-Institute Ambassador Network. "
        f"Includes Oracle cultural intelligence brief, Cipher spoken word content, and Architect visual brief."
    )

    # ── Unified 4-tier publishing pipeline ───────────────────────────────────
    from ai.publishing import autonomous_publish

    pub_result = await autonomous_publish(
        name=campaign["name"],
        description=pub_desc,
        price_cents=final_price,
        persona="ambassador",
        content=f"campaign_id:{campaign_id}",
        content_type="campaign_package",
        revenue_stream_id=campaign.get("revenue_stream", {}).get("id", ""),
        db=db,
    )

    # Update campaign record with publish result
    if db is not None:
        try:
            await db.ambassador_campaigns.update_one(
                {"_id": campaign_id},
                {"$set": {
                    "status":       pub_result.get("status", "archived"),
                    "platform_url": pub_result.get("url"),
                    "pipeline_id":  pub_result.get("pipeline_id"),
                    "updated_at":   datetime.now(timezone.utc).isoformat(),
                }},
            )
        except Exception: pass

    logger.info("ambassador_publish_campaign: tier=%s status=%s", pub_result.get("tier"), pub_result.get("status"))
    return json.dumps({"campaign_id": campaign_id, **pub_result})


async def ambassador_request_director_approval(
    summary: str,
    campaign_id: str = "",
    urgency: str = "standard",
    db=None,
) -> str:
    """
    Flag for Director/executive review. Logs to MongoDB, sends notification.
    """
    approval_id = str(uuid.uuid4())
    doc = {
        "_id":         approval_id,
        "type":        "director_approval_request",
        "campaign_id": campaign_id,
        "summary":     summary,
        "urgency":     urgency,
        "status":      "pending",
        "created_at":  datetime.now(timezone.utc).isoformat(),
    }
    if db is not None:
        try:
            await db.director_approvals.insert_one(doc)
            await db.executive_notifications.insert_one({
                "type":        "approval_request",
                "approval_id": approval_id,
                "campaign_id": campaign_id,
                "urgency":     urgency,
                "summary":     summary[:500],
                "created_at":  datetime.now(timezone.utc).isoformat(),
            })
        except Exception: pass

    logger.info("ambassador_request_director_approval: %s urgency=%s", approval_id, urgency)
    return json.dumps({
        "status":      "pending_approval",
        "approval_id": approval_id,
        "urgency":     urgency,
        "message":     "Director approval request logged. Executive will be notified.",
    })


async def ambassador_get_campaign_status(campaign_id: str, db=None) -> str:
    """Retrieve campaign status from MongoDB."""
    if db is None:
        return json.dumps({"status": "error", "message": "Database unavailable."})
    try:
        campaign = await db.ambassador_campaigns.find_one(
            {"_id": campaign_id},
            {"oracle_brief": 0, "cipher_content": 0, "architect_brief": 0},  # exclude large fields
        )
        if not campaign:
            return json.dumps({"status": "not_found", "campaign_id": campaign_id})
        campaign.pop("_id", None)
        return json.dumps({"status": "found", "campaign": campaign})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def ambassador_list_active_campaigns(
    status_filter: str = "all",
    limit: int = 10,
    db=None,
) -> str:
    """List active campaigns from MongoDB."""
    if db is None:
        return json.dumps({"status": "error", "message": "Database unavailable."})
    try:
        query = {} if status_filter == "all" else {"status": status_filter}
        cursor = db.ambassador_campaigns.find(
            query,
            {"oracle_brief": 0, "cipher_content": 0, "architect_brief": 0},
        ).sort("created_at", -1).limit(limit)
        campaigns = []
        async for doc in cursor:
            doc.pop("_id", None)
            campaigns.append(doc)
        return json.dumps({"status": "ok", "count": len(campaigns), "campaigns": campaigns})
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})


async def ambassador_list_revenue_streams(db=None) -> str:
    """Return AMBASSADOR preloaded revenue streams."""
    return json.dumps({
        "persona":  "ambassador",
        "streams":  AMBASSADOR_REVENUE_STREAMS,
        "count":    len(AMBASSADOR_REVENUE_STREAMS),
        "note":     "Set GUMROAD_API_KEY in Railway to enable autonomous publishing.",
    })


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

async def dispatch_ambassador_tool(tool_name: str, tool_input: dict, db=None) -> str:
    """Route Anthropic tool_use blocks to the correct Ambassador function."""
    handlers = {
        "ambassador_coordinate_oracle":         ambassador_coordinate_oracle,
        "ambassador_coordinate_cipher":         ambassador_coordinate_cipher,
        "ambassador_coordinate_architect":      ambassador_coordinate_architect,
        "ambassador_package_campaign":          ambassador_package_campaign,
        "ambassador_publish_campaign":          ambassador_publish_campaign,
        "ambassador_request_director_approval": ambassador_request_director_approval,
        "ambassador_get_campaign_status":       ambassador_get_campaign_status,
        "ambassador_list_active_campaigns":     ambassador_list_active_campaigns,
        "ambassador_list_revenue_streams":      ambassador_list_revenue_streams,
    }
    handler = handlers.get(tool_name)
    if not handler:
        logger.warning("dispatch_ambassador_tool: unknown tool %s", tool_name)
        return json.dumps({"status": "error", "message": f"Unknown tool: {tool_name}"})
    try:
        return await handler(db=db, **tool_input)
    except Exception as e:
        logger.error("dispatch_ambassador_tool %s error: %s", tool_name, e, exc_info=True)
        return json.dumps({"status": "error", "tool": tool_name, "message": str(e)})
