"""app/routes/exec.py — Executive pipeline routes.

Extracted from backend/server.py lines 8466–9524.
Covers: scout, audio, merch, personas, analytics, dashboard, products, staff meetings, pipeline.
"""
import io
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.database import db, _get_prt_engine, _get_the9_engine
from app.models.user import User
from app.security.auth import current_user, require_role

logger = logging.getLogger("lcewai")
router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))

_DOMAIN_ROLES = {
    "poor_righteous_teacher": "Cultural integrity and doctrinal alignment review.",
    "director":               "Operational security, threat assessment, and incident response.",
    "revenue_director":       "Financial modeling, revenue strategy, and sustainability analysis.",
    "ancestral_sage":         "Healing, wellness, community wellbeing, and cultural wisdom.",
    "ambassador":             "Community outreach, partnership building, and enrollment strategy.",
    "cipher":                 "Content creation, spoken word, viral strategy, and audience engagement.",
    "oracle":                 "Cultural intelligence, trend forecasting, and timing analysis.",
    "architect":              "Visual identity, brand design, and platform aesthetics.",
    "the_9":                  "Unified synthesis across all domains.",
}


# ── Cultural Scout ────────────────────────────────────────────────────────────

@router.post("/exec/scout/run")
async def scout_run(user: User = Depends(require_role("executive_admin"))):
    from app.security.rate_limit import check_rate
    from wai_institute.pipelines.cultural_scout import CulturalScout
    check_rate(f"exec_scout:{user.id}", max_calls=3, window_sec=300)
    scout = CulturalScout(db)
    result = await scout.run_full_scan(max_leads_per_source=20)
    return result


@router.get("/exec/scout/leads")
async def scout_leads(
    status: str = "unmatched",
    min_score: int = 0,
    limit: int = 50,
    user: User = Depends(require_role("executive_admin")),
):
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
async def scout_status(user: User = Depends(require_role("executive_admin"))):
    total = matched = actioned = 0
    last_scan = None
    try:
        total    = await db.scout_leads.count_documents({})
        matched  = await db.scout_leads.count_documents({"matched": True})
        actioned = await db.scout_leads.count_documents({"actioned": True})
        last_doc = await db.scout_scan_log.find_one({}, sort=[("started_at", -1)])
        if last_doc:
            last_scan = {"scan_id": last_doc.get("scan_id"), "started_at": last_doc.get("started_at"), "leads_found": last_doc.get("leads_found", {})}
    except Exception as _e:
        logger.warning("Swallowed exception: %s", _e)
    return {
        "scout_enabled": os.environ.get("SCOUT_ENABLED", "true").lower() != "false",
        "scan_interval_hours": int(os.environ.get("SCOUT_INTERVAL_HOURS", "6")),
        "platforms": {
            "reddit": True, "rss": True,
            "youtube": bool(os.environ.get("YOUTUBE_API_KEY")),
            "twitter": bool(os.environ.get("TWITTER_BEARER_TOKEN")),
        },
        "leads": {"total": total, "matched": matched, "actioned": actioned, "pending": total - actioned},
        "last_scan": last_scan,
    }


@router.post("/exec/scout/match-all")
async def scout_match_all(user: User = Depends(require_role("executive_admin"))):
    from app.security.rate_limit import check_rate
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
        "processed": len(results), "matched": matched_count,
        "unmatched": len(results) - matched_count,
        "match_rate": f"{matched_count / max(len(results), 1) * 100:.1f}%",
    }


@router.post("/exec/scout/craft-response")
async def craft_outreach_response(body: dict, user: User = Depends(require_role("executive_admin"))):
    from app.security.rate_limit import check_rate
    from wai_institute.pipelines.contextual_matcher import ContextualMatcher
    from wai_institute.pipelines.conversational_engine import ConversationalEngine
    check_rate(f"craft_response:{user.id}", max_calls=10, window_sec=60)
    source_id = (body.get("source_id") or "").strip()
    if not source_id:
        raise HTTPException(400, "source_id is required")
    lead = await db.scout_leads.find_one({"source_id": source_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, f"Lead '{source_id}' not found")
    matcher = ContextualMatcher(db)
    match   = await matcher.match(lead)
    engine  = ConversationalEngine(db)
    response = await engine.craft_response(
        lead=lead, match_result=match,
        include_preview=body.get("include_preview", True),
        include_checkout=body.get("include_checkout", True),
    )
    return response


# ── Audio Pipeline ────────────────────────────────────────────────────────────

@router.post("/ai/cipher/generate-audio")
async def cipher_generate_audio(body: dict, user: User = Depends(require_role("executive_admin"))):
    from app.security.rate_limit import check_rate
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    check_rate(f"audio_gen:{user.id}", max_calls=10, window_sec=60)
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    pipeline = AudioPipeline(db)
    result = await pipeline.produce(
        text=text, persona=body.get("persona", "cipher"),
        title=body.get("title", ""), force_tier=body.get("force_tier", ""),
        preview_only=body.get("preview_only", False),
    )
    return result


@router.get("/exec/audio/{asset_id}")
async def serve_audio(asset_id: str, user: User = Depends(current_user)):
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)
    audio_bytes = await pipeline.get_audio_bytes(asset_id)
    if not audio_bytes:
        raise HTTPException(404, f"Audio asset '{asset_id}' not found")
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg",
        headers={"Content-Disposition": f"inline; filename={asset_id}.mp3"})


@router.get("/exec/audio")
async def list_audio_assets(persona: str = "", limit: int = 20, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.pipelines.audio_pipeline import AudioPipeline
    pipeline = AudioPipeline(db)
    assets = await pipeline.list_assets(persona=persona, limit=min(limit, 100))
    return {"count": len(assets), "assets": assets}


# ── Merch Pipeline ────────────────────────────────────────────────────────────

@router.post("/exec/merch/create")
async def merch_create(body: dict, user: User = Depends(require_role("executive_admin"))):
    from app.security.rate_limit import check_rate
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    check_rate(f"merch_create:{user.id}", max_calls=5, window_sec=60)
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 200:
        text = text[:200]
    pipeline = MerchPipeline(db)
    result = await pipeline.create_merch_from_text(
        text=text, title=body.get("title", ""),
        product_types=body.get("product_types", ["classic_tee", "poster_18x24"]),
        persona=body.get("persona", "cipher"),
    )
    return result


@router.get("/exec/merch")
async def list_merch(status: str = "all", limit: int = 20, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.pipelines.merch_pipeline import MerchPipeline
    pipeline = MerchPipeline(db)
    products = await pipeline.get_merch_products(status=status, limit=min(limit, 100))
    return {"status_filter": status, "count": len(products), "products": products}


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/exec/analytics")
async def pipeline_analytics(period_days: int = 30, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.pipelines.analytics_pipeline import AnalyticsPipeline
    analytics = AnalyticsPipeline(db)
    report = await analytics.generate_full_report(period_days=min(period_days, 365))
    return report


# ── Persona Management ────────────────────────────────────────────────────────

@router.get("/exec/personas")
async def list_personas(user: User = Depends(require_role("executive_admin"))):
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    active = await pm.list_active()
    from wai_institute.core.persona_registry import get_registry
    registry = get_registry()
    return {"registry": registry, "active_count": len(active), "active_personas": active}


@router.post("/exec/personas/{name}/evolve")
async def evolve_persona(name: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.evolve(
        name=name, add_capabilities=body.get("add_capabilities", []),
        remove_capabilities=body.get("remove_capabilities", []),
        update_mandate=body.get("update_mandate"), evolved_by=user.id,
    )
    return result


@router.post("/exec/personas/{name}/activate")
async def activate_persona(name: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.activate(name=name, config=body.get("config", {}), mode=body.get("mode", "active"), activated_by=user.id)
    return result


@router.post("/exec/personas/{name}/deactivate")
async def deactivate_persona(name: str, body: dict, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.core.persona_manager import PersonaManager
    pm = PersonaManager(db)
    result = await pm.deactivate(name=name, reason=body.get("reason", ""), deactivated_by=user.id)
    return result


# ── Checkout Conversion ────────────────────────────────────────────────────────

@router.post("/exec/checkout/conversion")
async def record_checkout_conversion(body: dict, user: User = Depends(require_role("executive_admin"))):
    from wai_institute.pipelines.transaction_node import TransactionNode
    checkout_id = (body.get("checkout_id") or "").strip()
    if not checkout_id:
        raise HTTPException(400, "checkout_id is required")
    tn = TransactionNode(db)
    result = await tn.record_conversion(checkout_id, body.get("order_data", {}))
    return result


# ── Executive Dashboard ────────────────────────────────────────────────────────

@router.get("/exec/dashboard")
async def exec_dashboard(user: User = Depends(require_role("executive_admin"))):
    from ai.publishing import LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, GUMROAD_API_KEY
    elevenlabs_key = bool(os.environ.get("ELEVENLABS_API_KEY", ""))
    openai_key     = bool(os.environ.get("OPENAI_API_KEY", ""))
    anthropic_key  = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    ls_ready       = bool(LEMON_SQUEEZY_API_KEY and LEMON_SQUEEZY_STORE_ID)
    gumroad_ready  = bool(GUMROAD_API_KEY)
    platform_status = {
        "anthropic_api": anthropic_key, "elevenlabs": elevenlabs_key, "openai_tts": openai_key,
        "lemon_squeezy": ls_ready, "lemon_squeezy_key_set": bool(LEMON_SQUEEZY_API_KEY),
        "lemon_squeezy_store_set": bool(LEMON_SQUEEZY_STORE_ID), "gumroad": gumroad_ready,
        "publishing_tier": "lemon_squeezy" if ls_ready else "gumroad" if gumroad_ready else "mongodb_archive",
    }
    personas = [
        {"id": "the_9",                  "name": "THE 9 — UNIFIED MIND",         "tools": 16, "voice": "elevenlabs", "tier": 0, "authority": "unified_mind"},
        {"id": "poor_righteous_teacher", "name": "THE POOR RIGHTEOUS TEACHER",   "tools": 6,  "voice": "elevenlabs", "tier": 1, "authority": "doctrinal_guardian"},
        {"id": "director",               "name": "THE DIRECTOR 4.0",             "tools": 8,  "voice": "elevenlabs", "tier": 2},
        {"id": "revenue_director",       "name": "THE REVENUE DIRECTOR 4.0",     "tools": 9,  "voice": "elevenlabs", "tier": 3},
        {"id": "ancestral_sage",         "name": "THE ANCESTRAL SAGE 4.0",       "tools": 7,  "voice": "elevenlabs", "tier": 3},
        {"id": "ambassador",             "name": "THE AMBASSADOR 4.0",           "tools": 9,  "voice": "openai",     "tier": 4},
        {"id": "cipher",                 "name": "THE CIPHER 4.0",               "tools": 8,  "voice": "elevenlabs", "tier": 4},
        {"id": "oracle",                 "name": "THE ORACLE 4.0",               "tools": 7,  "voice": "openai",     "tier": 4},
        {"id": "architect",              "name": "THE ARCHITECT 4.0",            "tools": 8,  "voice": "openai",     "tier": 4},
    ]
    pipeline_published = pipeline_pending = pipeline_total = 0
    pending_notifs = policy_count = episode_count = 0
    tts_budgets: dict = {}
    try:
        pipeline_published = await db.wai_product_pipeline.count_documents({"status": "published"})
        pipeline_pending   = await db.wai_product_pipeline.count_documents({"status": "pending_publish"})
        pipeline_total = pipeline_published + pipeline_pending
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
    try:
        async for bdoc in db.persona_tts_budgets.find({}, {"_id": 0}):
            p = bdoc.get("persona", "unknown")
            tts_budgets[p] = {
                "chars_used": bdoc.get("chars_used_this_month", 0),
                "monthly_cap": bdoc.get("monthly_cap", 0),
                "pct_used": round(bdoc.get("chars_used_this_month", 0) / max(bdoc.get("monthly_cap", 1), 1) * 100, 1),
            }
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)
    try:
        cbdoc = await db.cipher_audio_budget.find_one({}, {"_id": 0})
        if cbdoc:
            cap = cbdoc.get("monthly_cap", 29500)
            used = cbdoc.get("chars_used_this_month", 0)
            tts_budgets["cipher"] = {"chars_used": used, "monthly_cap": cap, "pct_used": round(used / max(cap, 1) * 100, 1)}
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)
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
    recent_notifs = []
    try:
        cursor = db.executive_notifications.find(
            {}, {"_id": 0, "type": 1, "persona": 1, "name": 1, "note": 1, "created_at": 1}
        ).sort("created_at", -1).limit(5)
        async for doc in cursor:
            recent_notifs.append(doc)
    except Exception as _e: logger.warning("Swallowed exception: %s", _e)
    return {
        "dashboard": "WAI-Institute Executive Dashboard",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_status": platform_status,
        "personas": personas,
        "product_pipeline": {
            "total": pipeline_total, "published": pipeline_published,
            "pending_publish": pipeline_pending, "pending_preview": pending_preview,
        },
        "memory_system": {"total_episodes": episode_count, "active_policy_orders": policy_count},
        "tts_budgets": tts_budgets,
        "notifications": {"total_pending": pending_notifs, "recent": recent_notifs},
        "setup_guidance": (
            None if ls_ready else
            "Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID to Railway to enable autonomous product publishing."
        ),
    }


# ── Products ──────────────────────────────────────────────────────────────────

@router.get("/exec/products")
async def exec_list_products(status: str = "all", limit: int = 50, user: User = Depends(require_role("executive_admin"))):
    limit = min(max(limit, 1), 200)
    query = {}
    if status in ("published", "pending_publish"):
        query["status"] = status
    products = []
    try:
        cursor = db.wai_product_pipeline.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        async for doc in cursor:
            doc["price"] = f"${doc.get('price_cents', 0) / 100:.2f}"
            products.append(doc)
    except Exception as e:
        raise HTTPException(500, f"Pipeline query failed: {e}")
    return {"status_filter": status, "count": len(products), "products": products}


@router.post("/exec/products/create")
async def exec_create_product(body: dict, user: User = Depends(require_role("executive_admin"))):
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
    try:
        result = await autonomous_publish(
            name=name, description=description, price_cents=price_cents,
            persona=body.get("persona", "ancestral_sage"), content=body.get("content", ""),
            content_type=body.get("content_type", "digital_product"),
            is_subscription=bool(body.get("is_subscription", False)),
            interval=body.get("interval", "month"), db=db,
        )
    except Exception as e:
        raise HTTPException(500, f"Publish failed: {e}")
    return result


@router.post("/exec/products/publish-all")
async def exec_publish_all(user: User = Depends(require_role("executive_admin"))):
    from ai.publishing import batch_publish_pending
    try:
        result = await batch_publish_pending(db)
    except Exception as e:
        raise HTTPException(500, f"Batch publish failed: {e}")
    return result


# ── Staff Meetings ────────────────────────────────────────────────────────────

@router.get("/exec/staff-meetings")
async def list_staff_meetings(limit: int = 20, user: User = Depends(require_role("executive_admin"))):
    cursor = db.staff_meetings.find({}, {"_id": 0}).sort("convened_at", -1).limit(min(limit, 100))
    meetings = await cursor.to_list(length=limit)
    return {"meetings": meetings}


class StaffMeetingRequest(BaseModel):
    brief:        str              = Field(..., min_length=1, max_length=2000)
    agenda:       List[str]        = Field(default_factory=list)
    participants: List[str]        = Field(default_factory=list)
    priority:     Literal["normal", "high"] = "normal"


@router.post("/exec/staff-meeting")
async def exec_staff_meeting(body: StaffMeetingRequest, user: User = Depends(require_role("executive_admin"))):
    import asyncio as _asyncio
    brief        = body.brief.strip()
    agenda       = [str(a)[:500] for a in body.agenda]
    participants = [str(p)[:100] for p in body.participants]
    priority     = body.priority

    prt = _get_prt_engine()
    filter_result = {"accepted": True, "authority": "bypassed"}
    enforcement   = None
    prt_cleared   = False

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
            logger.warning("staff_meeting: PRT validation error: %s", _prt_err)

    try:
        from wai_institute.core.hierarchy_enforcer import HierarchyEnforcer
        enforcer  = HierarchyEnforcer(db)
        alignment = enforcer.check_cultural_alignment(brief)
        if not alignment["aligned"]:
            raise HTTPException(422, f"Cultural integrity check failed: {alignment.get('violations')}")
    except (ImportError, HTTPException):
        raise
    except Exception:
        pass

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
        meeting_participants = [p for p in participants if p in active_ids]
    else:
        meeting_participants = sorted(active_ids)

    domain_briefs = {}
    for persona_id in meeting_participants:
        role_question = _DOMAIN_ROLES.get(persona_id, "Domain input for this brief.")
        domain_briefs[persona_id] = {
            "persona": persona_id, "question": role_question,
            "brief": brief[:300], "status": "awaiting_response",
        }

    async def _call_persona(persona_id: str, question: str) -> tuple:
        try:
            try:
                from ai.persona_loader import get_persona
                system_prompt = get_persona(persona_id)
            except (ImportError, KeyError):
                system_prompt = (
                    f"You are {persona_id.replace('_', ' ').title()}, a WAI-Institute council member. "
                    f"Your role: {question}. Respond concisely and actionably."
                )
            user_message = (
                f"STAFF MEETING BRIEF:\n{brief}\n\nAGENDA:\n" +
                "\n".join(f"- {a}" for a in agenda) +
                f"\n\nYOUR ROLE QUESTION: {question}\n\nProvide your assessment and action items."
            )
            try:
                from ai.llm_gateway import call_llm as _call_llm
                _gw = await _call_llm(system=system_prompt, messages=[{"role": "user", "content": user_message}], max_tokens=1024, persona_label=persona_id)
                response = _gw["text"].strip()
            except Exception:
                import anthropic as _anth
                _c = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
                _msg = await _c.messages.create(model="claude-haiku-4-5", max_tokens=1024, system=system_prompt, messages=[{"role": "user", "content": user_message}])
                response = _msg.content[0].text.strip()
            return persona_id, response
        except Exception as exc:
            logger.warning("staff_meeting: persona %s LLM call failed: %s", persona_id, exc)
            return persona_id, ""

    _llm_personas = [pid for pid in meeting_participants if pid not in ("the_9", "poor_righteous_teacher")]
    if _llm_personas and ANTHROPIC_API_KEY:
        _results = await _asyncio.gather(*[_call_persona(pid, domain_briefs[pid]["question"]) for pid in _llm_personas])
        for pid, resp in _results:
            if resp:
                domain_briefs[pid]["response"] = resp
                domain_briefs[pid]["status"] = "responded"

    synthesis = None
    if priority == "high" or "the_9" in body.participants:
        the9 = _get_the9_engine()
        if the9 is not None:
            try:
                _persona_responses = {pid: br.get("response", "") for pid, br in domain_briefs.items() if br.get("response")}
                prt_directive = enforcement or {"directive": brief, "authority": "bypassed"}
                fusion = the9.fuse(
                    context={"brief": brief, "agenda": agenda, "participants": meeting_participants, "persona_responses": _persona_responses},
                    prt_directive=prt_directive, sender="executive", activation_reason="executive_command",
                )
                synthesis = fusion.to_dict()
                if synthesis.get("status") == "fused" and ANTHROPIC_API_KEY:
                    try:
                        _responses_text = "\n\n".join(f"=== {pid} ===\n{resp}" for pid, resp in _persona_responses.items()) if _persona_responses else "(no responses)"
                        _the9_system = "You are THE 9 — the unified intelligence of the WAI-Institute. Synthesize all persona inputs into a unified strategic response."
                        _the9_user = f"BRIEF: {brief}\n\nAGENDA:\n" + "\n".join(f"- {a}" for a in agenda) + f"\n\nPERSONA RESPONSES:\n{_responses_text}\n\nProduce your unified synthesis."
                        from ai.llm_gateway import call_llm as _call_llm
                        _gw = await _call_llm(system=_the9_system, messages=[{"role": "user", "content": _the9_user}], max_tokens=2048, persona_label="the_9")
                        synthesis["synthesis_brief"] = _gw["text"].strip()
                    except Exception as _synth_err:
                        logger.warning("staff_meeting: The 9 LLM synthesis failed: %s", _synth_err)
            except Exception as _the9_err:
                logger.warning("staff_meeting: The 9 synthesis error: %s", _the9_err)
                synthesis = {"status": "unavailable", "error": "the9_init_failed"}
        else:
            synthesis = {"status": "unavailable", "error": "engine_not_loaded"}

    meeting_id  = str(uuid.uuid4())
    convened_at = datetime.now(timezone.utc).isoformat()
    meeting_record = {
        "meeting_id": meeting_id, "brief": brief, "agenda": agenda,
        "participants": meeting_participants, "priority": priority, "prt_cleared": prt_cleared,
        "domain_briefs": domain_briefs, "synthesis": synthesis, "convened_by": user.id, "convened_at": convened_at,
    }

    try:
        await db.staff_meetings.insert_one({**meeting_record, "_id": meeting_id})
    except Exception as _db_err:
        logger.warning("staff_meeting: staff_meetings write failed: %s", _db_err)

    try:
        await db.governance_log.insert_one({
            "action": "staff_meeting", "persona": "executive",
            "decision": {"meeting_id": meeting_id, "brief": brief[:200], "participants": meeting_participants, "prt_cleared": prt_cleared},
            "timestamp": convened_at,
        })
    except Exception as _db_err:
        logger.warning("staff_meeting: governance_log write failed: %s", _db_err)

    if prt is not None:
        try:
            from wai_institute.personas.prt.prt_enforcement_engine import PRTEnforcementEngine
            await db.prt_enforcement_log.insert_one(
                PRTEnforcementEngine.to_governance_dict(sender="executive", directive=brief, filter_result=filter_result, enforcement=enforcement)
            )
        except Exception as _db_err:
            logger.warning("staff_meeting: prt_enforcement_log write failed: %s", _db_err)

    if synthesis and synthesis.get("status") == "fused":
        try:
            await db.the9_activations.insert_one({
                "meeting_id": meeting_id, "activated_by": synthesis.get("activated_by", "executive"),
                "activation_code": synthesis.get("activation_code", "executive_command"),
                "activation_reason": synthesis.get("activation_reason", ""),
                "skill_count": len(synthesis.get("unified_skill_set", [])), "timestamp": convened_at,
            })
        except Exception as _db_err:
            logger.warning("staff_meeting: the9_activations write failed: %s", _db_err)

    return {
        "meeting_id": meeting_id, "status": "convened", "prt_cleared": prt_cleared,
        "participants": meeting_participants, "domain_briefs": domain_briefs,
        "synthesis": synthesis, "priority": priority, "convened_at": convened_at,
    }


# ── Pipeline Processing ────────────────────────────────────────────────────────

class PipelineProcessRequest(BaseModel):
    text:   str = Field(..., min_length=1, max_length=5000)
    source: str = Field(default="api", max_length=100)


class PipelineProcessBatchRequest(BaseModel):
    texts:  List[str] = Field(..., min_items=1, max_items=50)
    source: str       = Field(default="api", max_length=100)


@router.post("/exec/pipeline/process")
async def exec_pipeline_process(body: PipelineProcessRequest, user: User = Depends(require_role("admin"))):
    import app.database as _app_db
    if _app_db._pipeline_manager is None:
        raise HTTPException(503, "PipelineManager not initialized — check server logs")
    result = await _app_db._pipeline_manager.process(body.text.strip(), source=body.source.strip())
    return result.to_dict()


@router.post("/exec/pipeline/process-batch")
async def exec_pipeline_process_batch(body: PipelineProcessBatchRequest, user: User = Depends(require_role("admin"))):
    import app.database as _app_db
    if _app_db._pipeline_manager is None:
        raise HTTPException(503, "PipelineManager not initialized — check server logs")
    texts  = body.texts
    source = body.source.strip()
    if len(texts) == 0:
        raise HTTPException(400, "texts must be a non-empty list")
    if len(texts) > 50:
        raise HTTPException(400, "Maximum 50 texts per batch call")
    results = await _app_db._pipeline_manager.process_batch(texts, source=source)
    return [r.to_dict() for r in results]
