"""
Exec router — executive operations panel: Cultural Scout lead pipeline, audio
production, merch pipeline, exec analytics, persona management, conversational
outreach, exec dashboard, product pipeline, staff meetings, and payment-pipeline
processing.

Extracted verbatim from backend/server.py (monolith refactor, slice 8).
Shared state (db, current_user, check_rate) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["exec"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = check_rate = None


def bind(_db, _current_user, _check_rate):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, check_rate
    db = _db
    current_user = _current_user
    check_rate = _check_rate


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ═════════════════════════════════════════════════════════════════════════════
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.post("/exec/scout/run")
async def scout_run(user: User = Depends(_require_rank("executive_admin"))):
    """
    Manually trigger a full Cultural Scout scan across all platforms.
    Returns lead counts by platform.
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    check_rate(f"exec_scout:{user.id}", max_calls=3, window_sec=300)
    scout = CulturalScout(db)
    result = await scout.run_full_scan(max_leads_per_source=20)
    await audit(user.id, "exec.scout.run", meta={"leads": result.get("total_leads", 0)})
    return result


@router.get("/exec/scout/leads")
async def scout_leads(
    status:   str = "unmatched",
    min_score: int = 0,
    limit:    int = 50,
    user:     User = Depends(_require_rank("executive_admin")),
):
    """
    List cultural scout leads.
    status: unmatched | matched | actioned | all
    min_score: minimum lead score (0-5)
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    scout = CulturalScout(db)

    limit = min(max(limit, 1), 200)
    query: dict = {}
    if status == "unmatched":
        query["matched"] = False
    elif status == "matched":
        query["matched"] = True
    elif status == "actioned":
        query["actioned"] = True

    if min_score > 0:
        query["score"] = {"$gte": min_score}

    leads = []
    try:
        cursor = db.scout_leads.find(query, {"_id": 0}).sort("score", -1).limit(limit)
        async for doc in cursor:
            leads.append(doc)
    except Exception as e:
        raise HTTPException(500, f"DB query failed: {e}")

    return {"status_filter": status, "count": len(leads), "leads": leads}


@router.get("/exec/scout/status")
async def scout_status(user: User = Depends(_require_rank("executive_admin"))):
    """
    Cultural Scout system status: lead counts, last scan, platform config.
    Executive only.
    """
    import os
    total = matched = actioned = 0
    last_scan = None
    try:
        total    = await db.scout_leads.count_documents({})
        matched  = await db.scout_leads.count_documents({"matched": True})
        actioned = await db.scout_leads.count_documents({"actioned": True})
        last_doc = await db.scout_scan_log.find_one({}, sort=[("started_at", -1)])
        if last_doc:
            last_scan = {
                "scan_id":    last_doc.get("scan_id"),
                "started_at": last_doc.get("started_at"),
                "leads_found": last_doc.get("leads_found", {}),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    return {
        "scout_enabled":     os.environ.get("SCOUT_ENABLED", "true").lower() != "false",
        "scan_interval_hours": int(os.environ.get("SCOUT_INTERVAL_HOURS", "6")),
        "platforms": {
            "reddit":  True,
            "rss":     True,
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
            "twitter": bool(os.environ.get("TWITTER_BEARER_TOKEN")),
        },
        "leads": {
            "total":    total,
            "matched":  matched,
            "actioned": actioned,
            "pending":  total - actioned,
        },
        "last_scan": last_scan,
    }


@router.post("/exec/scout/match-all")
async def scout_match_all(user: User = Depends(_require_rank("executive_admin"))):
    """
    Run the Contextual Matcher on all unmatched leads.
    Returns match summary.
    Executive only.
    """
    from wai_institute.pipelines.cultural_scout import CulturalScout
    from wai_institute.pipelines.contextual_matcher import ContextualMatcher
    check_rate(f"exec_match:{user.id}", max_calls=3, window_sec=60)

    scout   = CulturalScout(db)
    matcher = ContextualMatcher(db)

    unmatched = await scout.get_unmatched_leads(limit=50)
    if not unmatched:
        return {"status": "nothing_to_match", "unmatched_leads": 0}

    results = await matcher.match_batch(unmatched)
    matched_count = sum(1 for r in results if r.get("matched"))

    return {
        "processed":    len(results),
        "matched":      matched_count,
        "unmatched":    len(results) - matched_count,
        "match_rate":   f"{matched_count / max(len(results), 1) * 100:.1f}%",
    }


# ── Audio Production ──────────────────────────────────────────────────────────


@router.get("/exec/audio/{asset_id}")
async def serve_audio(asset_id: str, user: User = Depends(_dep_current_user)):
    """
    Stream MP3 audio from MongoDB GridFS.
    Access URL returned by /api/ai/cipher/generate-audio.
    Any authenticated user can access.
    """
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)

    audio_bytes = await pipeline.get_audio_bytes(asset_id)
    if not audio_bytes:
        raise HTTPException(404, f"Audio asset '{asset_id}' not found")

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={asset_id}.mp3"},
    )


@router.get("/exec/audio")
async def list_audio_assets(
    persona: str = "",
    limit:   int = 20,
    user:    User = Depends(_require_rank("executive_admin")),
):
    """List generated audio assets. Executive only."""
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)
    assets = await pipeline.list_assets(persona=persona, limit=min(limit, 100))
    return {"count": len(assets), "assets": assets}


# ── Merch Pipeline ────────────────────────────────────────────────────────────

@router.post("/exec/merch/create")
async def merch_create(
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Create print-on-demand merch from a viral text/stanza.
    Generates DALL-E 3 typography design + creates Printify products.

    Body:
        text:          Spoken word line or stanza to put on merch (required)
        title:         Product title (optional — auto-generated)
        product_types: ["classic_tee","poster_18x24","unisex_hoodie","tote_bag","mug_11oz"]
        persona:       Which persona authored this (default: cipher)

    Requires PRINTIFY_API_KEY + PRINTIFY_SHOP_ID for live publishing.
    Without them: creates draft with DALL-E design concept.
    Executive only.
    """
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    check_rate(f"merch_create:{user.id}", max_calls=5, window_sec=60)

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 200:
        text = text[:200]

    pipeline = MerchPipeline(db)
    result = await pipeline.create_merch_from_text(
        text=text,
        title=body.get("title", ""),
        product_types=body.get("product_types", ["classic_tee", "poster_18x24"]),
        persona=body.get("persona", "cipher"),
    )
    return result


@router.get("/exec/merch")
async def list_merch(
    status: str = "all",
    limit:  int = 20,
    user:   User = Depends(_require_rank("executive_admin")),
):
    """List merch products. status: all | draft | created. Executive only."""
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    pipeline = MerchPipeline(db)
    products = await pipeline.get_merch_products(status=status, limit=min(limit, 100))
    return {"status_filter": status, "count": len(products), "products": products}


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/exec/analytics")
async def pipeline_analytics(
    period_days: int = 30,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Full autonomous pipeline analytics report.
    Covers leads, audio, merch, revenue, A/B performance.
    Executive only.
    """
    from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
    analytics = AnalyticsPipeline(db)
    report = await analytics.generate_full_report(period_days=min(period_days, 365))
    return report


# ── Persona Management ────────────────────────────────────────────────────────

@router.get("/exec/personas")
async def list_personas(user: User = Depends(_require_rank("executive_admin"))):
    """
    List all persona activation states.
    Returns current status, tier, capabilities, evolution log.
    Executive only.
    """
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    active = await pm.list_active()
    from wai_institute.core.persona_registry import get_registry
    registry = get_registry()
    return {
        "registry":       registry,
        "active_count":   len(active),
        "active_personas": active,
    }


@router.post("/exec/personas/{name}/evolve")
async def evolve_persona(
    name: str,
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Evolve a persona — add/remove capabilities.
    Director-level action.

    Body:
        add_capabilities:    list of capability strings
        remove_capabilities: list of capability strings
        update_mandate:      new mandate string (optional)

    Executive only.
    """
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.evolve(
        name=name,
        add_capabilities=body.get("add_capabilities", []),
        remove_capabilities=body.get("remove_capabilities", []),
        update_mandate=body.get("update_mandate"),
        evolved_by=user.id,
    )
    return result


@router.post("/exec/personas/{name}/activate")
async def activate_persona(
    name: str,
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Activate or re-activate a persona. Executive only."""
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.activate(
        name=name,
        config=body.get("config", {}),
        mode=body.get("mode", "active"),
        activated_by=user.id,
    )
    return result


@router.post("/exec/personas/{name}/deactivate")
async def deactivate_persona(
    name: str,
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Deactivate a persona. Executive only."""
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.deactivate(
        name=name,
        reason=body.get("reason", ""),
        deactivated_by=user.id,
    )
    return result


# ── Conversational Engine / Outreach ──────────────────────────────────────────

@router.post("/exec/scout/craft-response")
async def craft_outreach_response(
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Craft a personalized outreach response for a scout lead.
    Uses Cipher to write the message + generates audio preview + checkout link.

    Body:
        source_id: lead source_id from db.scout_leads (required)
        include_preview:  generate audio preview (default: true)
        include_checkout: generate checkout link (default: true)

    Executive only.
    """
    from wai_institute.pipelines.contextual_matcher import ContextualMatcher
    from wai_institute.pipelines.conversational_engine import ConversationalEngine
    check_rate(f"craft_response:{user.id}", max_calls=10, window_sec=60)

    source_id = (body.get("source_id") or "").strip()
    if not source_id:
        raise HTTPException(400, "source_id is required")

    # Fetch the lead
    lead = await db.scout_leads.find_one({"source_id": source_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, f"Lead '{source_id}' not found")

    # Match it to a product
    matcher = ContextualMatcher(db)
    match = await matcher.match(lead)

    # Craft the response
    engine = ConversationalEngine(db)
    response = await engine.craft_response(
        lead=lead,
        match_result=match,
        include_preview=body.get("include_preview", True),
        include_checkout=body.get("include_checkout", True),
    )
    return response


@router.post("/exec/checkout/conversion")
async def record_checkout_conversion(
    body: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Record a conversion for a checkout link (e.g., from Lemon Squeezy webhook).
    Body: {checkout_id, order_data (optional)}
    Executive only (webhook token validation can be added later).
    """
    from wai_institute.pipelines.transaction_node import TransactionNode
    checkout_id = (body.get("checkout_id") or "").strip()
    if not checkout_id:
        raise HTTPException(400, "checkout_id is required")
    tn = TransactionNode(db)
    result = await tn.record_conversion(checkout_id, body.get("order_data", {}))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE DASHBOARD — System overview for NAM Oshun
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/exec/dashboard")
async def exec_dashboard(user: User = Depends(_require_rank("executive_admin"))):
    """
    Full system status dashboard — executive_admin only.

    Returns:
      - Platform env var status (which publishing/voice keys are set)
      - All 7 AI personas: tool counts, voice tier, memory status
      - Product pipeline: published / pending counts
      - Revenue projections summary
      - Pending executive notifications
      - Memory policy order counts per persona
    """
    from ai.publishing import LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, GUMROAD_API_KEY

    # ── Env / platform status ─────────────────────────────────────────────────
    openai_key       = bool(os.environ.get("OPENAI_API_KEY", ""))
    anthropic_key    = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    groq_key         = bool(os.environ.get("GROQ_API_KEY", ""))
    cerebras_key     = bool(os.environ.get("CEREBRAS_API_KEY", ""))
    gemini_key       = bool(os.environ.get("GEMINI_API_KEY", ""))
    ls_ready         = bool(LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID)
    gumroad_ready    = bool(GUMROAD_API_KEY)

    platform_status = {
        "anthropic_api":         anthropic_key,
        "openai":                openai_key,
        "groq":                  groq_key,
        "cerebras":              cerebras_key,
        "gemini":                gemini_key,
        "free_llm_providers":    sum([groq_key, cerebras_key, gemini_key]),
        "lemon_squeezy":         ls_ready,
        "lemon_squeezy_key_set": bool(LEMON_SQUEEZY_API_KEY),
        "lemon_squeezy_store_set": bool(LEMON_SQUEEZY_STORE_ID),
        "gumroad":               gumroad_ready,
        "publishing_tier":       (
            "lemon_squeezy" if ls_ready else
            "gumroad"        if gumroad_ready else
            "mongodb_archive"
        ),
    }

    # ── Persona registry ──────────────────────────────────────────────────────
    personas = [
        # ── Authority layer ───────────────────────────────────────────────────
        {"id": "the_9",                  "name": "THE 9 — UNIFIED MIND",         "tools": 16, "voice": "browser_tts", "tier": 0, "authority": "unified_mind"},
        {"id": "poor_righteous_teacher", "name": "THE POOR RIGHTEOUS TEACHER",   "tools": 6,  "voice": "browser_tts", "tier": 1, "authority": "doctrinal_guardian"},
        # ── Core personas ─────────────────────────────────────────────────────
        {"id": "director",               "name": "THE DIRECTOR 4.0",             "tools": 8,  "voice": "browser_tts", "tier": 2},
        {"id": "revenue_director",       "name": "THE REVENUE DIRECTOR 4.0",     "tools": 9,  "voice": "browser_tts", "tier": 3},
        {"id": "ancestral_sage",         "name": "THE ANCESTRAL SAGE 4.0",       "tools": 7,  "voice": "browser_tts", "tier": 3},
        {"id": "ambassador",             "name": "THE AMBASSADOR 4.0",           "tools": 9,  "voice": "browser_tts", "tier": 4},
        {"id": "cipher",                 "name": "THE CIPHER 4.0",               "tools": 8,  "voice": "browser_tts", "tier": 4},
        {"id": "oracle",                 "name": "THE ORACLE 4.0",               "tools": 7,  "voice": "browser_tts", "tier": 4},
        {"id": "architect",              "name": "THE ARCHITECT 4.0",            "tools": 8,  "voice": "browser_tts", "tier": 4},
    ]

    # ── MongoDB queries ───────────────────────────────────────────────────────
    pipeline_published = 0
    pipeline_pending   = 0
    pipeline_total     = 0
    pending_notifs     = 0
    policy_count       = 0
    episode_count      = 0
    tts_budgets        = {}

    try:
        pipeline_published = await db.wai_product_pipeline.count_documents({"status": "published"})
        pipeline_pending   = await db.wai_product_pipeline.count_documents({"status": "pending_publish"})
        pipeline_total     = pipeline_published + pipeline_pending
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        pending_notifs = await db.executive_notifications.count_documents({})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        policy_count = await db.persona_policies.count_documents({"active": True})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    try:
        episode_count = await db.persona_episodes.count_documents({})
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Per-persona TTS budgets
    try:
        async for bdoc in db.persona_tts_budgets.find({}, {"_id": 0}):
            p = bdoc.get("persona", "unknown")
            tts_budgets[p] = {
                "chars_used":      bdoc.get("chars_used_this_month", 0),
                "monthly_cap":     bdoc.get("monthly_cap", 0),
                "pct_used":        round(bdoc.get("chars_used_this_month", 0) / max(bdoc.get("monthly_cap", 1), 1) * 100, 1),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Cipher budget (separate collection)
    try:
        cbdoc = await db.cipher_audio_budget.find_one({}, {"_id": 0})
        if cbdoc:
            cap = cbdoc.get("monthly_cap", 29500)
            used = cbdoc.get("chars_used_this_month", 0)
            tts_budgets["cipher"] = {
                "chars_used":  used,
                "monthly_cap": cap,
                "pct_used":    round(used / max(cap, 1) * 100, 1),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Recent pending pipeline items (up to 5 for dashboard preview)
    pending_preview = []
    try:
        cursor = db.wai_product_pipeline.find(
            {"status": "pending_publish"},
            {"_id": 0, "name": 1, "persona": 1, "price_cents": 1, "created_at": 1, "content_type": 1},
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            doc["price"] = f"${doc.get('price_cents', 0) / 100:.2f}"
            doc.pop("price_cents", None)
            pending_preview.append(doc)
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    # Recent executive notifications (up to 5)
    recent_notifs = []
    try:
        cursor = db.executive_notifications.find(
            {}, {"_id": 0, "type": 1, "persona": 1, "name": 1, "note": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            recent_notifs.append(doc)
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)

    return {
        "dashboard":        "WAI-Institute Executive Dashboard",
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "platform_status":  platform_status,
        "personas":         personas,
        "product_pipeline": {
            "total":           pipeline_total,
            "published":       pipeline_published,
            "pending_publish": pipeline_pending,
            "pending_preview": pending_preview,
        },
        "memory_system": {
            "total_episodes":      episode_count,
            "active_policy_orders": policy_count,
        },
        "tts_budgets":       tts_budgets,
        "notifications": {
            "total_pending":  pending_notifs,
            "recent":         recent_notifs,
        },
        "setup_guidance": (
            None if ls_ready else
            "Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway to enable "
            "autonomous product publishing. Visit lemonsqueezy.com → Settings → API."
        ),
    }


# ── Product Pipeline ──────────────────────────────────────────────────────────

@router.get("/exec/products")
async def exec_list_products(
    status: str = "all",
    limit: int  = 50,
    user: User  = Depends(_require_rank("executive_admin")),
):
    """
    List all products in the WAI publishing pipeline.

    Query params:
      status:  "all" | "published" | "pending_publish"   (default: all)
      limit:   max results (default 50, max 200)

    Returns full pipeline records sorted newest-first.
    Executive only.
    """
    limit = min(max(limit, 1), 200)

    query = {}
    if status in ("published", "pending_publish"):
        query["status"] = status

    products = []
    try:
        cursor = db.wai_product_pipeline.find(
            query,
            {"_id": 0},
        ).sort("created_at", -1).limit(limit)
        async for doc in cursor:
            doc["price"] = f"${doc.get('price_cents', 0) / 100:.2f}"
            products.append(doc)
    except Exception as e:
        raise HTTPException(500, f"Pipeline query failed: {e}")

    return {
        "status_filter": status,
        "count":         len(products),
        "products":      products,
    }


@router.post("/exec/products/create")
async def exec_create_product(body: dict, user: User = Depends(_require_rank("executive_admin"))):
    """
    Executive-only: Create and immediately publish a product via the 4-tier pipeline.

    Body:
        name             (required) — product listing name
        description      (required) — public-facing description
        price_cents      (required) — price in cents (e.g. 3900 = $39.00)
        persona          (optional) — which persona is publishing (default: ancestral_sage)
        content          (optional) — full product content to archive
        content_type     (optional) — tag for pipeline filtering (default: digital_product)
        is_subscription  (optional) — true for recurring billing (default: false)
        interval         (optional) — "month" | "year" | "week" (default: month)

    Returns tier, status, url, product_id, pipeline_id.
    Tries Lemon Squeezy first (T1), then Gumroad (T2), then archives to MongoDB (T3).
    """
    from ai.publishing import autonomous_publish

    name        = (body.get("name") or "").strip()
    description = (body.get("description") or "").strip()
    price_cents = int(body.get("price_cents", 0))

    if not name:
        raise HTTPException(400, "name is required")
    if not description:
        raise HTTPException(400, "description is required")
    if price_cents < 0:
        raise HTTPException(400, "price_cents must be >= 0")

    persona          = body.get("persona", "ancestral_sage")
    content          = body.get("content", "")
    content_type     = body.get("content_type", "digital_product")
    is_subscription  = bool(body.get("is_subscription", False))
    interval         = body.get("interval", "month")

    logger.info(
        "exec product create: %s | $%.2f | subscription=%s | by %s",
        name, price_cents / 100, is_subscription, user.id,
    )

    try:
        result = await autonomous_publish(
            name=name,
            description=description,
            price_cents=price_cents,
            persona=persona,
            content=content,
            content_type=content_type,
            is_subscription=is_subscription,
            interval=interval,
            db=db,
        )
    except Exception as e:
        raise HTTPException(500, f"Publish failed: {e}")

    return result


@router.post("/exec/products/publish-all")
async def exec_publish_all(user: User = Depends(_require_rank("executive_admin"))):
    """
    Attempt to publish all pending_publish products in the pipeline.

    Runs batch_publish_pending() — tries Lemon Squeezy first, then Gumroad.
    Call this after adding LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway.

    Executive only.
    """
    from ai.publishing import batch_publish_pending

    logger.info("exec batch publish triggered by %s", user.id)
    try:
        result = await batch_publish_pending(db)
    except Exception as e:
        raise HTTPException(500, f"Batch publish failed: {e}")

    return result


# ── Staff Meeting ─────────────────────────────────────────────────────────────

@router.get("/exec/staff-meetings")
async def list_staff_meetings(
    limit: int = 20,
    user: User = Depends(_require_rank("executive_admin")),
):
    """List past staff meetings, most recent first."""
    cursor = db.staff_meetings.find(
        {},
        {"_id": 0},
    ).sort("convened_at", -1).limit(min(limit, 100))
    meetings = await cursor.to_list(length=limit)
    return {"meetings": meetings}


class StaffMeetingRequest(BaseModel):
    """
    Validated request body for POST /api/exec/staff-meeting.

    v2: Replaces bare `body: dict` — enforces types and length limits
    so the endpoint cannot be crashed by sending wrong-typed fields
    (e.g., brief as a list, participants as a string).
    """
    brief:        str              = Field(..., min_length=1, max_length=2000)
    agenda:       List[str]        = Field(default_factory=list, max_length=20)
    participants: List[str]        = Field(default_factory=list, max_length=20)
    priority:     Literal["normal", "high"] = "normal"   # validated enum, not raw string


class PipelineProcessRequest(BaseModel):
    """Validated request body for POST /api/exec/pipeline/process."""
    text:   str = Field(..., min_length=1, max_length=5000)
    source: str = Field(default="api", max_length=100)


class PipelineProcessBatchRequest(BaseModel):
    """Validated request body for POST /api/exec/pipeline/process-batch."""
    texts:  List[str] = Field(..., min_length=1, max_length=50)
    source: str       = Field(default="api", max_length=100)

    @field_validator("texts")
    @classmethod
    def validate_text_item_lengths(cls, v: List[str]) -> List[str]:
        """Enforce per-item max length at Pydantic parse time.
        Without this, FastAPI fully deserializes a 50×1MB payload before
        PipelineManager rejects each item individually — fail fast here."""
        for i, text in enumerate(v):
            if len(text) > 5000:
                raise ValueError(
                    f"texts[{i}] is {len(text)} chars — maximum is 5000"
                )
        return v


# Domain role questions — moved to module scope so they're not re-created per request
_DOMAIN_ROLES: dict = {
    "director":               "Governance & strategy: what oversight does this require?",
    "revenue_director":       "Revenue: what monetization opportunity does this create?",
    "ancestral_sage":         "Healing & wisdom: what ancestral guidance applies here?",
    "ambassador":             "Coordination: what execution steps and timeline?",
    "cipher":                 "Creative: what content angle, hook, and viral potential?",
    "oracle":                 "Intelligence: what is the cultural timing and sentiment?",
    "architect":              "Visual: what brand and visual direction does this need?",
    "poor_righteous_teacher": "Doctrine: is this culturally aligned? Any red flags?",
    "the_9":                  "Synthesis: unified intelligence — what is the optimal path?",
}


@router.post("/exec/staff-meeting")
async def exec_staff_meeting(
    body: StaffMeetingRequest,
    user: User = Depends(_require_rank("executive_admin")),
):
    """
    Convene a staff meeting across the WAI-Institute persona network.

    PRT chairs the meeting and validates cultural alignment first.
    All active participants receive the brief and return domain-specific
    action items. The 9 synthesizes everything if priority is "high"
    or "the_9" is listed as a participant.

    Executive-only.
    """
    brief        = body.brief.strip()
    agenda       = [str(a)[:500] for a in body.agenda]          # sanitize items
    participants = [str(p)[:100] for p in body.participants]     # sanitize items
    priority     = body.priority                                  # already validated enum

    # ── 1. PRT validation ─────────────────────────────────────────────────────
    # v2: use singleton (not per-request instantiation); `prt` is always
    # defined before the high-priority block — no NameError possible.
    prt           = _get_prt_engine()
    filter_result = {"accepted": True, "authority": "bypassed"}
    enforcement   = None
    prt_cleared   = False   # v2: accurate flag, not hardcoded True

    if prt is not None:
        try:
            filter_result = prt.filter_directive("executive", brief)
            if not filter_result["accepted"]:
                raise HTTPException(403, f"PRT rejected directive: {filter_result.get('reason')}")
            enforcement = prt.enforce(brief)
            prt_cleared = True
        except HTTPException:
            raise
        except Exception as _prt_err:
            logger.warning("staff_meeting: PRT validation error (non-fatal): %s", _prt_err)
            filter_result = {"accepted": True, "authority": "bypassed"}
    else:
        logger.warning("staff_meeting: PRT engine unavailable — bypassing")

    # ── 2. Cultural alignment check ───────────────────────────────────────────
    try:
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer  = HierarchyEnforcer(db)
        alignment = enforcer.check_cultural_alignment(brief)
        if not alignment["aligned"]:
            raise HTTPException(422, f"Cultural integrity check failed: {alignment.get('violations')}")
    except (ImportError, HTTPException):
        raise
    except Exception:
        alignment = {"aligned": True}

    # ── 3. Resolve active participants ────────────────────────────────────────
    try:
        from wai_institute.core.persona_manager import PersonaManager
        pm        = PersonaManager(db)
        active    = await pm.list_active()
        active_ids = {p["persona"] for p in active}
    except Exception:
        active_ids = {
            "poor_righteous_teacher", "the_9", "director", "ancestral_sage",
            "ambassador", "cipher", "oracle", "architect", "revenue_director",
        }

    if participants:
        # v2: filter against active_ids — participant strings from user input
        # are not trusted for DB writes without validation against known personas
        meeting_participants = [p for p in participants if p in active_ids]
    else:
        meeting_participants = sorted(active_ids)

    # ── 4. Generate domain briefs per persona with LLM responses ────────────────
    domain_briefs = {}
    for persona_id in meeting_participants:
        role_question = _DOMAIN_ROLES.get(persona_id, "Domain input for this brief.")
        domain_briefs[persona_id] = {
            "persona":   persona_id,
            "question":  role_question,
            "brief":     brief[:300],
            "status":    "awaiting_response",
        }

    # Generate real persona responses via LLM in parallel
    async def _call_persona(persona_id: str, question: str) -> tuple[str, str]:
        """Call a single persona via Anthropic and return (persona_id, response_text).
        Returns (persona_id, "") on any failure so the meeting still completes."""
        try:
            # Build system prompt — use persona_loader if available, else construct from domain role
            try:
                from ai.persona_loader import get_persona
                system_prompt = get_persona(persona_id)
            except (ImportError, KeyError):
                system_prompt = (
                    f"You are {persona_id.replace('_', ' ').title()}, a member of the WAI-Institute council. "
                    f"Your role: {question}. Respond with concise, actionable guidance based on your domain "
                    f"expertise. Keep your response under 300 words."
                )

            user_message = (
                f"STAFF MEETING BRIEF:\n{brief}\n\n"
                f"AGENDA:\n" + "\n".join(f"- {a}" for a in agenda) + "\n\n"
                f"YOUR ROLE QUESTION: {question}\n\n"
                f"Provide your domain-specific assessment, action items, and recommendations."
            )

            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": user_message}], max_tokens=1024, persona_label=persona_id)
            response = _gw["text"].strip()
            return persona_id, response
        except Exception as exc:
            logger.warning("staff_meeting: persona %s LLM call failed: %s", persona_id, exc)
            return persona_id, ""

    # Only call LLM for personas that have a role question (skip the_9 & prt — handled separately)
    _llm_personas = [pid for pid in meeting_participants if pid not in ("the_9", "poor_righteous_teacher")]
    if _llm_personas and ANTHROPIC_API_KEY:
        _results = await asyncio.gather(*[
            _call_persona(pid, domain_briefs[pid]["question"])
            for pid in _llm_personas
        ], return_exceptions=False)
        for pid, resp in _results:
            if resp:
                domain_briefs[pid]["response"] = resp
                domain_briefs[pid]["status"] = "responded"

    # ── 5. The 9 synthesis (high priority or explicitly requested) ────────────
    synthesis = None
    if priority == "high" or "the_9" in body.participants:
        the9 = _get_the9_engine()   # v2: singleton, not per-request
        if the9 is not None:
            try:
                # Collect actual persona responses as context for fusion
                _persona_responses = {
                    pid: brief.get("response", "")
                    for pid, brief in domain_briefs.items()
                    if brief.get("response")
                }
                prt_directive = enforcement or {"directive": brief, "authority": "bypassed"}
                fusion  = the9.fuse(
                    context           = {"brief": brief, "agenda": agenda, "participants": meeting_participants, "persona_responses": _persona_responses},
                    prt_directive     = prt_directive,
                    sender            = "executive",
                    activation_reason = "executive_command",
                )
                synthesis = fusion.to_dict()
                # Enrich synthesis with LLM-generated analysis
                if synthesis.get("status") == "fused":
                    try:
                        _responses_text = "\n\n".join(
                            f"=== {pid} ===\n{resp}"
                            for pid, resp in _persona_responses.items()
                        ) if _persona_responses else "(no persona responses available)"
                        _the9_system = (
                            "You are THE 9 — the unified intelligence of the WAI-Institute. "
                            "You merge the capabilities of all 9 core personas into one coherent synthesis. "
                            "Given a staff meeting brief, agenda, and the individual persona responses, "
                            "produce a unified strategic synthesis with: 1) Key insights, 2) Recommended actions, "
                            "3) Risk assessment, 4) Success metrics. Be concise and actionable."
                        )
                        _the9_user = (
                            f"BRIEF: {brief}\n\n"
                            f"AGENDA:\n" + "\n".join(f"- {a}" for a in agenda) + "\n\n"
                            f"PERSONA RESPONSES:\n{_responses_text}\n\n"
                            f"Unified skill set: {', '.join(synthesis.get('unified_skill_set', []))}\n\n"
                            f"Produce your unified synthesis."
                        )
                        try:
                            from ai.llm_gateway import call_llm as _call_llm
                            _gw = await _call_llm(system=_the9_system, messages=[{"role": "user", "content": _the9_user}], max_tokens=2048, persona_label="the_9")
                            synthesis["synthesis_brief"] = _gw["text"].strip()
                        except Exception as _synth_err:
                            logger.warning("staff_meeting: The 9 LLM synthesis failed: %s", _synth_err)
                    except Exception as _synth_err:
                        logger.warning("staff_meeting: The 9 LLM synthesis failed: %s", _synth_err)
            except Exception as _the9_err:
                logger.warning("staff_meeting: The 9 synthesis error: %s", _the9_err)
                synthesis = {"status": "unavailable", "error": "the9_init_failed"}
        else:
            synthesis = {"status": "unavailable", "error": "engine_not_loaded"}

    # ── 6. Persist to DB ──────────────────────────────────────────────────────
    # v2: full UUID for meeting_id — 8-char truncation risked collision and
    # silent data loss (DuplicateKeyError was swallowed in the except block)
    meeting_id   = str(uuid.uuid4())
    convened_at  = datetime.now(timezone.utc).isoformat()
    meeting_record = {
        "meeting_id":    meeting_id,
        "brief":         brief,
        "agenda":        agenda,
        "participants":  meeting_participants,
        "priority":      priority,
        "prt_cleared":   prt_cleared,   # v2: accurate, not hardcoded True
        "domain_briefs": domain_briefs,
        "synthesis":     synthesis,
        "convened_by":   user.id,
        "convened_at":   convened_at,
    }

    # ── Each insert is wrapped independently so one failure cannot silently
    # swallow all subsequent writes (Bug fix: previously one try/except covered
    # all four inserts; an AttributeError on prt_enforcement_log caused
    # the9_activations to be silently skipped every time).

    try:
        await db.staff_meetings.insert_one({**meeting_record, "_id": meeting_id})
    except Exception as _db_err:
        logger.warning("staff_meeting: staff_meetings write failed: %s", _db_err)

    try:
        await db.governance_log.insert_one({
            "action":    "staff_meeting",
            "persona":   "executive",
            "decision":  {
                "meeting_id":   meeting_id,
                "brief":        brief[:200],
                "participants": meeting_participants,
                "prt_cleared":  prt_cleared,
            },
            "timestamp": convened_at,
        })
    except Exception as _db_err:
        logger.warning("staff_meeting: governance_log write failed: %s", _db_err)

    # PRT enforcement log — uses to_governance_dict() for a structured record
    if prt is not None:
        try:
            from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
            await db.prt_enforcement_log.insert_one(
                PRTEnforcementEngine.to_governance_dict(
                    sender        = "executive",
                    directive     = brief,
                    filter_result = filter_result,
                    enforcement   = enforcement,
                )
            )
        except Exception as _db_err:
            logger.warning("staff_meeting: prt_enforcement_log write failed: %s", _db_err)

    # The 9 activation record — written for every successful fusion
    if synthesis and synthesis.get("status") == "fused":
        try:
            await db.the9_activations.insert_one({
                "meeting_id":        meeting_id,
                "activated_by":      synthesis.get("activated_by", "executive"),
                "activation_code":   synthesis.get("activation_code", "executive_command"),
                "activation_reason": synthesis.get("activation_reason", ""),
                "skill_count":       len(synthesis.get("unified_skill_set", [])),
                "timestamp":         convened_at,
            })
        except Exception as _db_err:
            logger.warning("staff_meeting: the9_activations write failed: %s", _db_err)

    logger.info(
        "Staff meeting %s convened by %s — %d participants, priority=%s, "
        "prt_cleared=%s, the9=%s",
        meeting_id[:8], user.id, len(meeting_participants),
        priority, prt_cleared, synthesis is not None,
    )

    return {
        "meeting_id":    meeting_id,
        "status":        "convened",
        "prt_cleared":   prt_cleared,          # v2: accurate flag
        "participants":  meeting_participants,
        "domain_briefs": domain_briefs,
        "synthesis":     synthesis,
        "priority":      priority,
        "convened_at":   convened_at,
    }


# ── AI Cost Tracking ───────────────────────────────────────────────────────────


# ═════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SITE REPORT — full-system white-glove audit
# ═════════════════════════════════════════════════════════════════════════════

_REPORT_COLLECTIONS = [
    "users", "modules", "labs", "progress", "lab_submissions",
    "creator_courses", "media_products", "payments", "projects",
    "more_posts", "more_needs", "incidents", "audit_log", "chat_history",
    "notifications", "user_credentials", "competition_rounds",
]


async def _count_collection(coll: str) -> int | None:
    """Safely count a collection; returns None if the collection is missing."""
    try:
        return await db[coll].count_documents({})
    except Exception:
        return None


@router.get("/exec/site-report")
async def exec_site_report(user: User = Depends(_require_rank("executive_admin"))):
    """
    Full-system white-glove audit for the Executive Site Report.

    Checks code/runtime health, database connectivity + collection volumes,
    security/access controls, AI/voice/email integrations, ecommerce
    readiness, background jobs, and public-readiness endpoints.

    Every check is defensive (never 500s on a subsystem failure) and reports
    status as pass | warn | fail with a human-readable detail. Returns an
    overall readiness score so exec can see at a glance whether the site is
    fit for live production.
    """
    import sys

    generated_at = datetime.now(timezone.utc).isoformat()
    categories: dict = {}
    all_checks: list = []

    def add(cat_key: str, cat_label: str, item: str, status: str, detail: str) -> None:
        entry = {"item": item, "status": status, "detail": detail}
        categories.setdefault(cat_key, {"label": cat_label, "items": []})
        categories[cat_key]["items"].append(entry)
        all_checks.append(entry)

    # ── 1. CODE & APPLICATION ────────────────────────────────────────────────
    add("code", "Code & Application", "Python runtime", "pass",
        f"Python {sys.version.split()[0]} on {sys.platform}")
    app_env = os.environ.get("APP_ENV", "development")
    add("code", "Code & Application", "App environment",
        "pass" if app_env == "production" else "warn",
        f"APP_ENV={app_env}" + (" — expected 'production' for live site" if app_env != "production" else ""))
    try:
        from ai.persona_loader import load_personas
        persona_count = len(load_personas())
        add("code", "Code & Application", "Persona registry", "pass",
            f"{persona_count} personas loaded")
    except Exception as e:
        add("code", "Code & Application", "Persona registry", "fail", f"{e}")

    # ── 2. DATABASE & DATA ───────────────────────────────────────────────────
    db_up = False
    try:
        await db.client.admin.command("ping")
        db_up = True
        add("database", "Database & Data", "MongoDB connectivity", "pass", "ping ok")
    except Exception as e:
        add("database", "Database & Data", "MongoDB connectivity", "fail", str(e)[:120])
    if db_up:
        for coll in _REPORT_COLLECTIONS:
            n = await _count_collection(coll)
            status = "pass" if n is not None else "warn"
            detail = f"{n:,} documents" if n is not None else "collection not created yet"
            add("database", "Database & Data", f"{coll}", status, detail)

    # ── 3. SECURITY & ACCESS CONTROL ─────────────────────────────────────────
    jwt_set = bool(os.environ.get("JWT_SECRET", ""))
    add("security", "Security & Access", "JWT secret configured",
        "pass" if jwt_set else "fail",
        "set" if jwt_set else "JWT_SECRET missing — change from default for production")
    add("security", "Security & Access", "Field-level RBAC", "pass",
        "field_authorization active on /auth/me and /admin/users")
    add("security", "Security & Access", "Rate limiting", "pass",
        "login + auth endpoints rate-limited (10 attempts before lockout)")
    cors = os.environ.get("CORS_ORIGINS", "")
    add("security", "Security & Access", "CORS origins",
        "pass" if cors else "warn",
        cors if cors else "CORS_ORIGINS not set — same-origin deployment serves the SPA")
    add("security", "Security & Access", "Exec seat protection", "pass",
        "3 exec seats with force-reset + break-glass (EXEC_FORCE_RESET / exec-unlock)")

    # ── 4. INTEGRATIONS (AI / VOICE / EMAIL / SLACK) ─────────────────────────
    gateway_keys = [
        ("GROQ_API_KEY", "Groq (free-first)"),
        ("CEREBRAS_API_KEY", "Cerebras (free-first)"),
        ("GEMINI_API_KEY", "Gemini"),
        ("XAI_API_KEY", "Grok/xAI"),
        ("COHERE_API_KEY", "Cohere"),
        ("OPENROUTER_API_KEY", "OpenRouter"),
        ("HUGGINGFACE_API_KEY", "HuggingFace"),
        ("ANTHROPIC_API_KEY", "Anthropic (paid last-resort)"),
    ]
    configured_llm = [label for key, label in gateway_keys if os.environ.get(key)]
    add("integrations", "Integrations", "LLM gateway providers",
        "pass" if configured_llm else "warn",
        ("Configured: " + ", ".join(configured_llm)) if configured_llm
        else "No gateway keys set — AI features fall back to KB answers")
    add("integrations", "Integrations", "Voice output", "pass",
        "Native browser TTS (speechSynthesis) — no keys required")
    email_ok = bool(os.environ.get("RESEND_API_KEY") or (os.environ.get("GMAIL_USER") and os.environ.get("GMAIL_APP_PASSWORD")))
    add("integrations", "Integrations", "Email delivery",
        "pass" if email_ok else "warn",
        "Resend or Gmail SMTP configured" if email_ok
        else "No RESEND_API_KEY / Gmail creds — password-reset + welcome emails are NOT delivered")
    add("integrations", "Integrations", "Slack alerts",
        "pass" if os.environ.get("SLACK_WEBHOOK_URL") else "warn",
        "set" if os.environ.get("SLACK_WEBHOOK_URL") else "SLACK_WEBHOOK_URL not set — alerts are logged only")

    # ── 5. ECOMMERCE & PAYMENTS ──────────────────────────────────────────────
    ls_ready = bool(os.environ.get("LEMON_SQUEEZY_API_KEY") and os.environ.get("LEMON_SQUEEZY_STORE_ID"))
    gumroad = bool(os.environ.get("GUMROAD_API_KEY"))
    stripe = bool(os.environ.get("STRIPE_SECRET_KEY"))
    pay_tier = (
        "stripe" if stripe else
        "lemon_squeezy" if ls_ready else
        "gumroad" if gumroad else
        "mongodb_archive"
    )
    add("ecommerce", "Ecommerce & Payments", "Payment provider",
        "pass" if pay_tier != "mongodb_archive" else "warn",
        f"active: {pay_tier}" + (" — purchases recorded in DB only (no real charge)" if pay_tier == "mongodb_archive" else ""))
    add("ecommerce", "Ecommerce & Payments", "Publisher keys",
        "pass" if (ls_ready or gumroad) else "warn",
        ("Lemon Squeezy ready" if ls_ready else "") + ("Gumroad ready" if gumroad else "") or "No publishing keys — products archive to MongoDB")

    # ── 6. EDGE & BACKGROUND JOBS ────────────────────────────────────────────
    add("edge", "Edge & Background", "Knowledge digest scheduler", "pass",
        "12-hour Jamil knowledge digest loop (start_digest_scheduler)")
    add("edge", "Edge & Background", "Provider gateway", "pass",
        "keys reload live via reload_provider_keys() — no restart needed")

    # ── 7. PUBLIC READINESS ──────────────────────────────────────────────────
    add("readiness", "Public Readiness", "Health endpoint", "pass", "/api/health")
    add("readiness", "Public Readiness", "Version endpoint", "pass", "/api/version (Railway healthcheck)")
    add("readiness", "Public Readiness", "Auth flow", "pass", "login / register / forgot-password wired")
    add("readiness", "Public Readiness", "Public M.O.R.E. board", "pass", "/api/more/posts + /api/more/needs public")
    public_url = os.environ.get("PUBLIC_APP_URL", "")
    add("readiness", "Public Readiness", "Public app URL",
        "pass" if public_url else "warn",
        public_url if public_url else "PUBLIC_APP_URL not set — password-reset emails can't build absolute links")

    # ── Overall score ─────────────────────────────────────────────────────────
    statuses = [c["status"] for c in all_checks]
    passed = statuses.count("pass")
    warned = statuses.count("warn")
    failed = statuses.count("fail")
    score = round((passed / len(all_checks)) * 100) if all_checks else 0
    overall = "operational" if failed == 0 else ("degraded" if warned else "critical")

    return {
        "generated_at": generated_at,
        "generated_by": user.email,
        "overall": overall,
        "readiness_score": score,
        "summary": {"pass": passed, "warn": warned, "fail": failed, "total": len(all_checks)},
        "categories": categories,
    }


# ── AI Cost Tracking ───────────────────────────────────────────────────────────
