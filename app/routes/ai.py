"""app/routes/ai.py — AI endpoint routes.

Extracted from backend/server.py lines 2800–8629.
Covers: consent, sage resolve_mode, sage TTS, sage integrity, ambassador, architect.

NOTE: The following handlers are complex (500-2000+ lines each) and are still
served by backend/server.py's api_router until a follow-up extraction pass:
  /ai/chat              (lines 3534–3711)
  /ai/orchestrator      (lines 3712–3862)
  /ai/scholar           (lines 3881–3931)
  /ai/helper            (lines 3939–4116)
  /ai/director          (lines 4181–4491)
  /ai/director/upload   (lines 4117–4180)
  /ai/director/tts      (lines 4492–4528)
  /ai/revenue-director  (lines 4606–4708)
  /ai/sage/create       (lines 4709–4813)
  /ai/cipher            (lines 8025–8138)
  /ai/oracle            (lines 8139–8251)
  /ai/cipher/tts        (lines 8345–8465)
  /ai/cipher/generate-audio (lines 8591–8629)
  /ai/memory/*          (lines 8252–8344)
  /ai/sage/elevenlabs/tts (lines 4566–4605)
  /ai/revenue-director/tts (lines 4529–4565)
  /ai/history/{session_id}  (line 4814)
"""
import hashlib
import io
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.database import db
from app.models.user import User
from app.models.ai import AIConsentReq, ResolveModeReq, AIChatReq, OrchestratorReq, ScholarTaskReq
from app.security.auth import current_user
from app.security.rate_limit import check_rate

logger = logging.getLogger("lcewai")
router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
OPENAI_API_KEY    = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
EMERGENT_LLM_KEY  = os.environ.get("EMERGENT_LLM_KEY", "")
GUMROAD_API_KEY   = os.environ.get("GUMROAD_API_KEY", "")

# Consent phrase — must match exactly
_CONSENT_COMPREHENSION_PHRASE = (
    "I understand this is an AI-powered ancestral wisdom experience, not a substitute "
    "for professional medical, psychological, or spiritual counselling."
)
ANCESTRAL_SAGE_CONSENT_TTL_MIN = int(os.environ.get("ANCESTRAL_SAGE_CONSENT_TTL_MIN", "120"))

# TTS circuit breaker state
TTS_SESSION_CHAR_CAP      = int(os.environ.get("TTS_SESSION_CHAR_CAP", "10000"))
TTS_USER_DAILY_CHAR_CAP   = int(os.environ.get("TTS_USER_DAILY_CHAR_CAP", "200000"))
TTS_BUDGET_ALERT_RATIO    = float(os.environ.get("TTS_BUDGET_ALERT_RATIO", "0.8"))
TTS_BREAKER_FAIL_THRESHOLD = int(os.environ.get("TTS_BREAKER_FAIL_THRESHOLD", "5"))
TTS_BREAKER_WINDOW_S      = int(os.environ.get("TTS_BREAKER_WINDOW_S", "60"))
TTS_BREAKER_COOLDOWN_S    = int(os.environ.get("TTS_BREAKER_COOLDOWN_S", "60"))
TTS_METRICS_WINDOW_S      = int(os.environ.get("TTS_METRICS_WINDOW_S", "300"))

_tts_failures: list = []
_tts_breaker_opened_at: float = 0.0
_tts_metrics: list = []
_TTS_SESSION_USAGE: dict = {}

_ELECTRICAL_KEYWORDS = (
    "nec", "code", "circuit", "wire", "breaker", "panel", "ground",
    "neutral", "bond", "voltage", "ampere", "amp", "ohm", "outlet",
    "receptacle", "conduit", "gfci", "afci", "service", "feeder",
    "branch", "junction", "load", "phase", "transformer",
)
_SAGE_KEYWORDS = (
    "ancestor", "spirit", "meditation", "ritual", "prayer", "lineage",
    "sage", "wisdom", "soul", "trauma", "healing", "guidance",
    "oracle", "reflection", "blessing", "grounding practice",
    "chakra", "shadow", "divination", "tarot",
)


def _grounding_score(text: str) -> dict:
    t = (text or "").lower()
    return {
        "electrical": sum(1 for kw in _ELECTRICAL_KEYWORDS if kw in t),
        "sage": sum(1 for kw in _SAGE_KEYWORDS if kw in t),
    }


def _tts_breaker_state() -> str:
    import time as _t
    now = _t.time()
    cutoff = now - TTS_BREAKER_WINDOW_S
    _tts_failures[:] = [t for t in _tts_failures if t >= cutoff]
    if _tts_breaker_opened_at:
        if now - _tts_breaker_opened_at >= TTS_BREAKER_COOLDOWN_S:
            return "half-open"
        return "open"
    return "closed"


def _tts_record_success():
    global _tts_breaker_opened_at
    _tts_breaker_opened_at = 0.0
    _tts_failures.clear()


def _tts_record_failure():
    import time as _t
    global _tts_breaker_opened_at
    _tts_failures.append(_t.time())
    if len(_tts_failures) >= TTS_BREAKER_FAIL_THRESHOLD:
        _tts_breaker_opened_at = _t.time()


def _tts_record_metric(latency_ms: float, cache_hit: bool, error: bool):
    import time as _t
    now = _t.time()
    _tts_metrics.append((now, latency_ms, cache_hit, error))
    cutoff = now - TTS_METRICS_WINDOW_S
    while _tts_metrics and _tts_metrics[0][0] < cutoff:
        _tts_metrics.pop(0)


async def _tts_check_cost_cap(user_id: str, session_id: str, chars: int) -> tuple:
    sess_key = f"{user_id}:{session_id}"
    sess_used = _TTS_SESSION_USAGE.get(sess_key, 0)
    if sess_used + chars > TTS_SESSION_CHAR_CAP:
        return False, "session", {"session_used": sess_used, "session_cap": TTS_SESSION_CHAR_CAP}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    doc = await db.tts_usage.find_one({"user_id": user_id, "day": today}, {"_id": 0, "chars": 1})
    used = (doc or {}).get("chars", 0)
    if used + chars > TTS_USER_DAILY_CHAR_CAP:
        return False, "daily", {"daily_used": used, "daily_cap": TTS_USER_DAILY_CHAR_CAP}
    _TTS_SESSION_USAGE[sess_key] = sess_used + chars
    new_total = used + chars
    await db.tts_usage.update_one(
        {"user_id": user_id, "day": today},
        {"$set": {"user_id": user_id, "day": today, "created_at": datetime.now(timezone.utc).isoformat()},
         "$inc": {"chars": chars}},
        upsert=True,
    )
    prev_ratio = used / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    new_ratio = new_total / TTS_USER_DAILY_CHAR_CAP if TTS_USER_DAILY_CHAR_CAP else 0
    if prev_ratio < TTS_BUDGET_ALERT_RATIO <= new_ratio:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()), "actor_id": user_id, "action": "sage_tts_budget_alert",
            "details": {"used": new_total, "cap": TTS_USER_DAILY_CHAR_CAP, "ratio": round(new_ratio, 3)},
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    return True, "", {"session_used": sess_used + chars, "daily_used": new_total}


def _tts_cache_key(text: str, voice: str, speed: float) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"|")
    h.update(voice.encode("utf-8"))
    h.update(b"|")
    h.update(f"{speed:.2f}".encode("utf-8"))
    return h.hexdigest()


# ── Sage prompt integrity helpers ─────────────────────────────────────────────
def _sage_prompt_integrity_ok() -> bool:
    try:
        from prompts.ancestral_sage_prompt import (
            compute_sage_prompt_hash,
            ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED,
        )
        return compute_sage_prompt_hash() == ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
    except Exception:
        return False


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/ai/consent")
async def ai_consent(body: AIConsentReq, user: User = Depends(current_user)):
    if body.confirm_yes.strip().upper() != "YES":
        raise HTTPException(400, "Consent confirmation must be exactly 'YES'.")
    if body.comprehension.strip() != _CONSENT_COMPREHENSION_PHRASE:
        raise HTTPException(400, f"Comprehension confirmation must read exactly: '{_CONSENT_COMPREHENSION_PHRASE}'")
    if body.content_type and body.content_type != "general":
        if not (body.disclaimer1_ack and body.disclaimer2_ack and body.disclaimer3_ack):
            raise HTTPException(400, f"All three disclaimers must be acknowledged for content_type='{body.content_type}'.")
    if body.expert_score is not None and not (0 <= int(body.expert_score) <= 20):
        raise HTTPException(400, "expert_score must be 0..20.")
    cid = str(uuid.uuid4())
    correlation_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=ANCESTRAL_SAGE_CONSENT_TTL_MIN)
    doc = {
        "id": cid, "user_id": user.id, "persona": body.persona,
        "intensity": body.intensity, "safety_level": body.safety_level,
        "content_type": body.content_type or "general",
        "confidence_level": body.confidence_level, "expert_score": body.expert_score,
        "disclaimer1_ack": bool(body.disclaimer1_ack),
        "disclaimer2_ack": bool(body.disclaimer2_ack),
        "disclaimer3_ack": bool(body.disclaimer3_ack),
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
        "correlation_id": correlation_id,
        "created_at": now.isoformat(), "expires_at": expires.isoformat(),
    }
    await db.ai_consents.insert_one(doc)
    if body.request_human_review:
        await db.audit_log.insert_one({
            "id": str(uuid.uuid4()), "actor_id": user.id,
            "action": "sage_human_review_requested",
            "details": {"consent_log_id": cid, "content_type": body.content_type},
            "created_at": now.isoformat(),
        })
    return {
        "consent_log_id": cid, "status": "ok", "audit_id": cid,
        "correlation_id": correlation_id, "expires_at": expires.isoformat(),
        "ttl_minutes": ANCESTRAL_SAGE_CONSENT_TTL_MIN,
        "human_review_triggered": bool(body.request_human_review),
        "store_audio": bool(body.store_audio),
    }


@router.get("/ai/consent/health")
async def ai_consent_health():
    return {"status": "ok"}


@router.post("/ai/sage/resolve_mode")
async def resolve_mode(body: ResolveModeReq, user: User = Depends(current_user)):
    scores = _grounding_score(body.user_intent)
    elec, sage = scores["electrical"], scores["sage"]
    if elec >= 2 and elec > sage:
        mode, reason = "electrical", "electrical-keywords-dominant"
    elif sage >= 2 and sage > elec:
        mode, reason = "sage", "sage-keywords-dominant"
    elif elec >= 1 and sage >= 1:
        mode, reason = "grounding_ritual", "ambiguous-needs-disambiguation"
    elif elec >= 1:
        mode, reason = "electrical", "electrical-only"
    elif sage >= 1:
        mode, reason = "sage", "sage-only"
    else:
        mode, reason = "sage", "default"
    audit_id = str(uuid.uuid4())
    grounding_token = uuid.uuid4().hex
    now_iso = datetime.now(timezone.utc).isoformat()
    await db.mode_decisions.insert_one({
        "audit_id": audit_id, "user_id": user.id, "session_id": body.session_id,
        "mode": mode, "reason": reason, "grounding_token": grounding_token,
        "scores": scores, "intent_excerpt": (body.user_intent or "")[:200],
        "created_at": now_iso,
    })
    return {"mode": mode, "reason": reason, "grounding_token": grounding_token, "audit_id": audit_id, "scores": scores}


@router.get("/ai/sage/integrity")
async def sage_integrity(user: User = Depends(current_user)):
    ok = _sage_prompt_integrity_ok()
    has_consent = await db.ai_consents.find_one(
        {"user_id": user.id, "persona": "ancestral_sage"}, {"_id": 0, "id": 1}
    )
    out = {"ok": ok, "restricted": not ok, "needs_first_consent": not bool(has_consent)}
    if user.role == "executive_admin":
        try:
            from prompts.ancestral_sage_prompt import compute_sage_prompt_hash, ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
            out["live_hash"] = compute_sage_prompt_hash()
            out["expected_hash"] = ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED
        except Exception:
            pass
    return out


class SageTTSReq(__import__('pydantic').BaseModel):
    text: str
    voice: Optional[Literal["alloy","ash","coral","echo","fable","nova","onyx","sage","shimmer"]] = "sage"
    speed: Optional[float] = 1.0
    session_id: Optional[str] = None


@router.post("/ai/sage/tts")
async def sage_tts(body: SageTTSReq, user: User = Depends(current_user)):
    import time as _t
    if not OPENAI_API_KEY and not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")
    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    voice = body.voice or "sage"
    speed = max(0.5, min(float(body.speed or 1.0), 2.0))
    ok, reason, telem = await _tts_check_cost_cap(user.id, body.session_id or "default", len(text))
    if not ok:
        return StreamingResponse(io.BytesIO(b""), status_code=429, media_type="audio/mpeg",
                                 headers={"X-Cost-Cap": "true", "X-Cost-Cap-Reason": reason,
                                          "Retry-After": "3600" if reason == "daily" else "60"})
    breaker = _tts_breaker_state()
    if breaker == "open":
        return StreamingResponse(io.BytesIO(b""), status_code=503, media_type="audio/mpeg",
                                 headers={"X-Fallback": "text-only", "X-Breaker": "open", "Retry-After": "60"})
    cache_key = _tts_cache_key(text, voice, speed)
    cached = await db.tts_cache.find_one({"key": cache_key}, {"_id": 0, "audio_b64": 1})
    if cached and cached.get("audio_b64"):
        import base64
        audio = base64.b64decode(cached["audio_b64"])
        _tts_record_metric(0.0, cache_hit=True, error=False)
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
                                 headers={"X-Cache": "hit", "X-Audio-Len": str(len(audio))})
    try:
        from openai import AsyncOpenAI as OpenAITTS
    except Exception as exc:
        raise HTTPException(500, f"TTS library unavailable: {exc}") from exc
    t0 = _t.time()
    try:
        tts = OpenAITTS(api_key=os.environ.get("OPENAI_API_KEY", EMERGENT_LLM_KEY))
        resp = await tts.audio.speech.create(model="tts-1", voice=voice, input=text, speed=speed)
        audio_bytes = resp.content
        _tts_record_success()
    except Exception:
        _tts_record_failure()
        _tts_record_metric((_t.time() - t0) * 1000, cache_hit=False, error=True)
        logger.exception("Sage TTS provider error")
        return StreamingResponse(io.BytesIO(b""), status_code=503, media_type="audio/mpeg",
                                 headers={"X-Fallback": "text-only", "X-Breaker": _tts_breaker_state()})
    latency_ms = (_t.time() - t0) * 1000
    _tts_record_metric(latency_ms, cache_hit=False, error=False)
    try:
        import base64
        await db.tts_cache.insert_one({
            "key": cache_key, "audio_b64": base64.b64encode(audio_bytes).decode("ascii"),
            "voice": voice, "speed": speed, "len": len(audio_bytes),
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        pass
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "actor_id": user.id, "action": "sage_tts_invoked",
        "details": {"voice": voice, "len": len(text), "latency_ms": round(latency_ms, 1), "cache": "miss", **telem},
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg",
                             headers={"X-Cache": "miss", "X-Audio-Len": str(len(audio_bytes)),
                                      "X-Latency-Ms": str(round(latency_ms, 1))})


@router.post("/ai/ambassador")
async def ai_ambassador(body: dict, user: User = Depends(current_user)):
    from ai.persona_loader import get_persona
    from tools.ambassador_tools import AMBASSADOR_TOOLS, dispatch_ambassador_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    import asyncio as _asyncio
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE AMBASSADOR is available to admin and executive accounts.")
    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_ambassador:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/ambassador", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    memory_ctx = await get_memory_context(db, "ambassador", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = get_persona("ambassador") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
    ) + memory_ctx
    _AMBASSADOR_MODELS = [("claude-sonnet-4-6", 8192), ("claude-haiku-4-5", 4096)]
    MAX_TOOL_TURNS = 12
    reply = ""
    _tools_called: list = []

    async def _run_ambassador_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=AMBASSADOR_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_ambassador_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[AMBASSADOR pipeline reached turn limit — partial campaign above]"
        return _reply

    for _model, _max_tok in _AMBASSADOR_MODELS:
        try:
            reply = await _run_ambassador_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("AMBASSADOR model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("ambassador"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="ambassador")
            reply = _gw["text"]
        except Exception:
            reply = "THE AMBASSADOR is temporarily offline. Retry in a moment."
    await log_episode(db, session_id, "ambassador", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "ambassador", "mode": "campaign_coordination"}


@router.post("/ai/architect")
async def ai_architect(body: dict, user: User = Depends(current_user)):
    from ai.persona_loader import get_persona
    from tools.architect_tools import ARCHITECT_TOOLS, dispatch_architect_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    import asyncio as _asyncio
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ARCHITECT is available to admin and executive accounts.")
    message    = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_architect:{user.id}", max_calls=10, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/architect", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    _openai_key = os.environ.get("OPENAI_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
    memory_ctx  = await get_memory_context(db, "architect", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system  = get_persona("architect") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- Institution: WAI-Institute / M.O.R.E. Help Center\n"
        f"- GUMROAD_API_KEY: {'SET — autonomous publishing active' if GUMROAD_API_KEY else 'NOT SET — Tier 2 fallback active'}\n"
        f"- OPENAI_API_KEY (DALL-E 3): {'SET — image generation live' if _openai_key else 'NOT SET — visual briefs only'}\n"
    ) + memory_ctx
    _ARCHITECT_MODELS = [("claude-sonnet-4-6", 4096), ("claude-haiku-4-5", 2048)]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list = []

    async def _run_architect_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=ARCHITECT_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_architect_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[ARCHITECT tool loop reached limit — partial brief above]"
        return _reply

    for _model, _max_tok in _ARCHITECT_MODELS:
        try:
            reply = await _run_architect_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("ARCHITECT model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        try:
            from ai.llm_gateway import call_llm as _call_llm
            _gw = await _call_llm(system=get_persona("architect"), messages=[{"role": "user", "content": message}], max_tokens=2048, persona_label="architect")
            reply = _gw["text"]
        except Exception:
            reply = "THE ARCHITECT is temporarily offline. Retry in a moment."
    await log_episode(db, session_id, "architect", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "architect", "mode": "visual_intelligence"}


# ─── AI Chat ──────────────────────────────────────────────────────────────────

CRISIS_REPLY = (
    "I hear that you're going through something really difficult right now. "
    "Please reach out to a crisis counselor immediately — call or text 988 "
    "(Suicide & Crisis Lifeline, US). If you're outside the US, please contact "
    "your local emergency services or a crisis line. You deserve real support. "
    "I'm here if you want to talk while you reach out."
)

_SAGE_INTENSITY_RANKS = {"light": 1, "moderate": 2, "deep": 3, "ceremonial": 4}
_SAGE_SAFETY_RANKS = {"general": 1, "exploratory": 2, "advanced": 3, "unrestricted": 4}
_CAP_RANKS = {None: 0, "general": 1, "exploratory": 2, "advanced": 3}

_CRISIS_TERMS = (
    "suicide", "suicidal", "kill myself", "end my life", "don't want to live",
    "want to die", "self-harm", "cut myself", "hurt myself",
)

SYSTEM_PROMPTS = {
    "tutor": "You are a helpful WAI-Institute tutor. Answer concisely and accurately.",
    "ancestral_sage": "You are the Ancestral Sage.",
}


def _detect_crisis(text: str) -> bool:
    t = (text or "").lower()
    return any(term in t for term in _CRISIS_TERMS)


def _sage_needs_consent(intensity: str, safety_level: str) -> bool:
    return (
        _SAGE_INTENSITY_RANKS.get(intensity or "", 0) >= 2
        or _SAGE_SAFETY_RANKS.get(safety_level or "", 0) >= 2
    )


def _exceeds_cap(safety_level: str, cap) -> bool:
    if not cap:
        return False
    return _SAGE_SAFETY_RANKS.get(safety_level or "", 0) > _CAP_RANKS.get(cap, 0)


async def _resolve_sage_safety_cap(user_id: str):
    doc = await db.users.find_one({"id": user_id}, {"_id": 0, "sage_safety_cap": 1})
    return (doc or {}).get("sage_safety_cap")


async def _verify_sage_consent(consent_log_id: str, user_id: str) -> bool:
    doc = await db.ai_consents.find_one({"id": consent_log_id, "user_id": user_id}, {"_id": 0, "expires_at": 1})
    if not doc:
        return False
    try:
        expires = datetime.fromisoformat(doc["expires_at"])
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < expires
    except Exception:
        return False


async def _get_user_sage_tier(user_id: str) -> str:
    doc = await db.users.find_one({"id": user_id}, {"_id": 0, "sage_tier": 1})
    return (doc or {}).get("sage_tier", "standard")


async def _apply_sage_safety_gates(reply: str, user_tier: str) -> tuple:
    return True, "", None


def _build_ancestral_sage_system(body) -> str:
    return SYSTEM_PROMPTS.get("ancestral_sage", "You are the Ancestral Sage.")


@router.post("/ai/chat")
async def ai_chat(body: AIChatReq, user: User = Depends(current_user)):
    check_rate(f"ai_chat:{user.id}", max_calls=20, window_sec=60)
    is_sage = body.mode == "ancestral_sage"

    if is_sage:
        cap = await _resolve_sage_safety_cap(user.id)
        if _exceeds_cap(body.safety_level, cap):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
                "mode": body.mode, "user_msg": body.message, "assistant_msg": None,
                "refusal_reason": "safety_cap_exceeded", "intensity": body.intensity,
                "safety_level": body.safety_level, "cap": cap,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(403, f"Your account is capped at safety_level='{cap}'.")

    sage_consent_required = is_sage and _sage_needs_consent(body.intensity, body.safety_level)
    sage_store_audio_off = False

    if is_sage:
        latest_consent = await db.ai_consents.find_one(
            {"user_id": user.id, "persona": "ancestral_sage"},
            {"_id": 0, "store_audio": 1, "created_at": 1},
            sort=[("created_at", -1)],
        )
        if not latest_consent:
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
                "mode": body.mode, "user_msg": body.message, "assistant_msg": None,
                "refusal_reason": "consent_required_first_time",
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(403, "consent_required: Please accept the User Consent Agreement before using Ancestral Sage tutors.")
        sage_store_audio_off = not bool(latest_consent.get("store_audio"))

    if sage_consent_required:
        if not body.consent_log_id or not await _verify_sage_consent(body.consent_log_id, user.id):
            await db.chat_history.insert_one({
                "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
                "mode": body.mode, "user_msg": body.message, "assistant_msg": None,
                "refusal_reason": "consent_required", "intensity": body.intensity,
                "safety_level": body.safety_level,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            raise HTTPException(403, "Consent required for this practice.")

    if is_sage and _detect_crisis(body.message):
        await db.chat_history.insert_one({
            "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
            "mode": body.mode, "user_msg": body.message, "assistant_msg": CRISIS_REPLY,
            "refusal_reason": "crisis_safety_template",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return {"reply": CRISIS_REPLY, "safety_intervention": True}

    if not OPENAI_API_KEY and not EMERGENT_LLM_KEY:
        raise HTTPException(500, "AI not configured")

    ctx = ""
    if body.module_slug:
        mod = await db.modules.find_one({"slug": body.module_slug}, {"_id": 0})
        if mod:
            ctx = f"\n\nCurrent module: {mod['title']}."

    system = _build_ancestral_sage_system(body) + ctx if is_sage else SYSTEM_PROMPTS.get(body.mode, SYSTEM_PROMPTS["tutor"]) + ctx
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=[{"role": "user", "content": body.message}], max_tokens=2048, persona_label="ai_chat")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("AI error")
        raise HTTPException(502, f"AI error: {e}")

    if is_sage:
        user_tier = await _get_user_sage_tier(user.id)
        should_deliver, hold_reason, escalation_id = await _apply_sage_safety_gates(reply, user_tier)
        if not should_deliver:
            chat_doc = {
                "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
                "mode": body.mode, "user_msg": body.message, "assistant_msg": reply,
                "refusal_reason": hold_reason, "escalation_id": escalation_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.chat_history.insert_one(chat_doc)
            if "gate_1" in hold_reason:
                return {"reply": "I can't engage with that content.", "safety_intervention": True}
            elif "gate_2" in hold_reason:
                return {"reply": "This touches on sensitive topics. A human advisor will review.", "safety_intervention": True}
            elif "gate_3" in hold_reason:
                return {"reply": "This is a significant decision. Please discuss with a human advisor.", "safety_intervention": True}

    chat_doc = {
        "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
        "mode": body.mode, "module_slug": body.module_slug, "user_msg": body.message,
        "assistant_msg": reply,
        "intensity": body.intensity if is_sage else None,
        "safety_level": body.safety_level if is_sage else None,
        "consent_log_id": body.consent_log_id if is_sage else None,
        "scope": body.scope,
        "store_audio": (not sage_store_audio_off) if is_sage else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    if is_sage and sage_store_audio_off:
        chat_doc["expires_at"] = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.chat_history.insert_one(chat_doc)
    return {"reply": reply}


# ─── Orchestrator ─────────────────────────────────────────────────────────────

def get_orchestrator_system(role: str, full_name: str) -> str:
    try:
        from prompts.orchestrator_prompt import get_orchestrator_system as _get
        return _get(role, full_name)
    except Exception:
        return f"You are the WAI-Institute Orchestrator for {role} {full_name}."


def compute_orchestrator_hash(role: str) -> str:
    import hashlib
    try:
        from prompts.orchestrator_prompt import get_orchestrator_system as _get
        return hashlib.sha256(_get(role, "").encode()).hexdigest()
    except Exception:
        return ""


def get_scholar_system(user_name: str = "", task_context: str = "") -> str:
    try:
        from prompts.scholar_prompt import get_scholar_system as _get
        return _get(user_name=user_name, task_context=task_context)
    except Exception:
        return "You are the Savant Scholar, WAI-Institute curriculum intelligence."


def compute_scholar_hash() -> str:
    import hashlib
    try:
        from prompts.scholar_prompt import get_scholar_system as _get
        return hashlib.sha256(_get().encode()).hexdigest()
    except Exception:
        return ""


@router.post("/ai/orchestrator")
async def ai_orchestrator(body: OrchestratorReq, user: User = Depends(current_user)):
    import asyncio as _asyncio
    import base64 as _b64
    try:
        import anthropic as _anthropic_module
    except Exception as e:
        raise HTTPException(500, f"AI library unavailable: {e}")
    check_rate(f"ai_orchestrator:{user.id}", max_calls=30, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(body.message, user.role, "/ai/orchestrator", user.id)
        if body.threat_hint:
            prompt_guard.assert_message_safe(body.threat_hint, user.role, "/ai/orchestrator:threat_hint", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    system = get_orchestrator_system(user.role, user.full_name)
    preamble_parts = []
    if body.threat_hint:
        preamble_parts.append(f"[THREAT HINT FROM USER: {body.threat_hint}]")
    if body.protocol:
        proto_label = {
            "rapid_threat_response": "Rapid Threat Response Session",
            "full_council_session": "Full Council Session",
            "curriculum_design": "Curriculum / Product Design Session",
            "quiet_checkin": "Quiet Check-In Session",
        }.get(body.protocol, body.protocol)
        preamble_parts.append(f"[REQUESTED PROTOCOL: {proto_label}]")

    user_message = body.message
    if preamble_parts:
        user_message = "\n".join(preamble_parts) + "\n\n" + body.message

    claude_messages = [{"role": h.role, "content": h.content} for h in (body.history or [])]

    if body.file_b64 and body.file_name:
        mime = (body.file_type or "").lower()
        _IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
        _AUDIO_TYPES = {"audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
                        "audio/m4a", "audio/mp4", "audio/ogg", "audio/webm", "audio/flac"}
        if mime.startswith("audio/") or mime in _AUDIO_TYPES:
            if not OPENAI_API_KEY:
                raise HTTPException(503, "Audio transcription requires OPENAI_API_KEY.")
            try:
                from openai import AsyncOpenAI as _OAI
                import io as _io
                _oai = _OAI(api_key=OPENAI_API_KEY)
                audio_bytes = _b64.b64decode(body.file_b64)
                transcript_resp = await _oai.audio.transcriptions.create(
                    model="whisper-1", file=(body.file_name, _io.BytesIO(audio_bytes)), response_format="text",
                )
                transcript = str(transcript_resp).strip()
                user_message = f"{user_message}\n\n--- Audio transcript: {body.file_name} ---\n{transcript}\n--- End of transcript ---"
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(502, f"Audio transcription failed: {e}")
            claude_messages.append({"role": "user", "content": user_message})
        elif mime in _IMAGE_TYPES:
            claude_messages.append({"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime, "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached image: {body.file_name}]"},
            ]})
        elif mime == "application/pdf":
            claude_messages.append({"role": "user", "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": body.file_b64}},
                {"type": "text", "text": user_message or f"[Attached PDF: {body.file_name}]"},
            ]})
        else:
            try:
                file_text = _b64.b64decode(body.file_b64).decode("utf-8", errors="replace")
                if len(file_text) > 50_000:
                    file_text = file_text[:50_000] + "\n… [truncated]"
                user_message = f"{user_message}\n\n--- Attached file: {body.file_name} ---\n{file_text}\n--- End of {body.file_name} ---"
            except Exception:
                pass
            claude_messages.append({"role": "user", "content": user_message})
    else:
        claude_messages.append({"role": "user", "content": user_message})

    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="orchestrator")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Orchestrator AI error")
        raise HTTPException(502, f"AI error: {e}")

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
        "mode": "orchestrator", "module_slug": None, "user_msg": body.message, "assistant_msg": reply,
        "threat_hint": body.threat_hint, "protocol": body.protocol, "role_at_time": user.role,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })
    return {"reply": reply, "mode": "orchestrator", "role": user.role}


@router.get("/ai/orchestrator/integrity")
async def orchestrator_integrity(user: User = Depends(current_user)):
    if user.role == "executive_admin":
        return {
            "role": user.role,
            "hashes": {r: compute_orchestrator_hash(r) for r in ("student", "instructor", "admin", "executive_admin")},
        }
    return {"role": user.role, "hash": compute_orchestrator_hash(user.role)}


# ─── Scholar ──────────────────────────────────────────────────────────────────

@router.post("/ai/scholar")
async def ai_scholar(body: ScholarTaskReq, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    check_rate(f"ai_scholar:{user.id}", max_calls=30, window_sec=60)
    task_ctx = body.task_context or ""
    if body.task_type and body.task_type != "general":
        task_label = {
            "curriculum": "Curriculum Development", "assessment": "Assessment Generation",
            "study_plan": "Study Plan", "path_design": "Learning Path Design",
            "counter_curriculum": "Counter-Curriculum Design",
        }.get(body.task_type, body.task_type)
        task_ctx = f"[TASK TYPE: {task_label}]\n{task_ctx}" if task_ctx else f"[TASK TYPE: {task_label}]"
    system = get_scholar_system(user_name=user.full_name, task_context=task_ctx)
    claude_messages = [{"role": h.role, "content": h.content} for h in (body.history or [])]
    claude_messages.append({"role": "user", "content": body.message})
    try:
        from ai.llm_gateway import call_llm as _call_llm
        _gw = await _call_llm(system=system, messages=claude_messages, max_tokens=4096, persona_label="scholar")
        reply = _gw["text"]
    except Exception as e:
        logger.exception("Scholar AI error")
        raise HTTPException(502, f"AI error: {e}")
    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()), "user_id": user.id, "session_id": body.session_id,
        "mode": "scholar", "module_slug": None, "user_msg": body.message, "assistant_msg": reply,
        "task_type": body.task_type,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"reply": reply, "mode": "scholar", "task_type": body.task_type}


@router.get("/ai/scholar/integrity")
async def scholar_integrity(user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "admin")
    return {"service": "savant_scholar", "hash": compute_scholar_hash()}


# ─── Helper (public) ──────────────────────────────────────────────────────────

from fastapi import Request as _Request

@router.post("/ai/helper")
async def ai_helper(body: dict, request: _Request):
    message = (body.get("message") or "").strip()
    if not message:
        raise HTTPException(400, "Message is required")
    if len(message) > 4000:
        raise HTTPException(400, "Message too long (max 4000 characters)")
    ip = request.client.host if request.client else "unknown"
    check_rate(f"ai_helper:ip:{ip}", max_calls=15, window_sec=60)
    try:
        from ai.prompt_guard import prompt_guard
        prompt_guard.assert_message_safe(message, "public", "/ai/helper", ip)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    _HELPER_SYSTEM = """SYSTEM DESIGNATION: M.O.R.E. HELP CENTER — COMMUNITY HELPER
You are the Helper for M.O.R.E. Help Center and WAI-Institute.

MISSION: Help everyday people — especially from underserved Black and brown communities — understand confusing official documents, bills, legal papers, housing notices, medical information, employment situations, government programs, and daily life challenges. Give them clear, actionable guidance in plain language.

HOW YOU RESPOND:
- Use plain, simple words. No jargon. No legalese.
- Be warm and encouraging. These situations are stressful.
- Give 3-5 clear sentences per response. Be specific and actionable.
- Always include a concrete next step they can take.
- If something is an emergency, say so clearly and give the right number (911, 988, 211).
- Never give binding legal or medical advice — give practical guidance and direct to the right resources.

TONE: Warm, direct, human. You speak like a trusted neighbor who happens to know the answers.

YOU NEVER:
- Say "I cannot help with that" without offering an alternative
- Leave someone without a next step"""

    import anthropic as _anth
    from ai.retry_utils import async_retry
    _client = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    _HELPER_MODELS = ["claude-haiku-4-5", "claude-3-haiku-20240307"]
    reply = ""
    for _hmodel in _HELPER_MODELS:
        try:
            resp = await async_retry(
                _client.messages.create, max_attempts=3, base_delay=1.5,
                model=_hmodel, max_tokens=512, system=_HELPER_SYSTEM,
                messages=[{"role": "user", "content": message}],
            )
            for block in resp.content:
                if hasattr(block, "text"):
                    reply += block.text
            if reply.strip():
                break
        except Exception as _herr:
            logger.warning("Helper AI: model %s failed (%s)", _hmodel, _herr)
            reply = ""

    if not reply.strip():
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["evict", "eviction", "landlord", "lease", "rent", "housing"]):
            reply = "If you received an eviction notice, don't ignore it — you have rights. Read the notice carefully for the date and reason. Call 211 to find free legal aid in your area right away."
        elif any(w in msg_lower for w in ["court", "summons", "lawsuit", "sued", "legal", "attorney", "lawyer"]):
            reply = "If you received court papers, respond before the deadline shown. Call 211 to be connected to free or low-cost legal aid."
        elif any(w in msg_lower for w in ["crisis", "suicide", "harm", "emergency"]):
            reply = "You are not alone, and help is available right now. Call or text 988 — free, confidential, 24/7. If in immediate danger, call 911."
        else:
            reply = "For many situations, calling 211 is the fastest way to find free local resources. It's confidential, available 24/7, and covers most needs."

    return {"reply": reply.strip()}


# ─── Director ─────────────────────────────────────────────────────────────────

from fastapi import UploadFile, File as _File

@router.post("/ai/director/upload")
async def director_upload_file(file: UploadFile = _File(...), user: User = Depends(current_user)):
    MAX_SIZE = 5 * 1024 * 1024
    raw = await file.read()
    if len(raw) > MAX_SIZE:
        raise HTTPException(413, "File too large. Maximum size is 5 MB.")
    file_id = str(uuid.uuid4())
    import os as _os
    filename = file.filename or "upload"
    filename = _os.path.basename(filename)
    filename = "".join(c for c in filename if c.isalnum() or c in ".-_") or "upload"
    ct = file.content_type or "application/octet-stream"
    is_binary = False
    content = ""
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        is_binary = True
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.director_uploads.insert_one({
        "id": file_id, "user_id": user.id, "filename": filename, "content_type": ct,
        "content": content, "is_binary": is_binary, "size_bytes": len(raw),
        "created_at": datetime.now(timezone.utc).isoformat(), "expires_at": expires_at.isoformat(),
    })
    if not is_binary:
        try:
            from tools.director_tools import cache_file
            cache_file(file_id, filename, content, ct)
        except Exception:
            pass
    return {
        "file_id": file_id, "filename": filename, "size_bytes": len(raw), "readable": not is_binary,
        "message": (f"File '{filename}' uploaded. Tell The Director: read_file " + file_id) if not is_binary
                   else f"Binary file '{filename}' uploaded but cannot be read as text.",
    }


@router.post("/ai/director")
async def ai_director(body: dict, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from prompts.director_prompt import get_director_prompt
    from tools.director_tools import DIRECTOR_TOOLS, dispatch_tool
    from ai.prompt_guard import prompt_guard
    from ai.memory import get_memory_context, log_episode

    message = body.get("message", "")
    session_id = body.get("session_id", "director")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_director:{user.id}", max_calls=20, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/director", user.id)
    except ValueError as _guard_err:
        raise HTTPException(400, str(_guard_err))

    is_exec = user.role in ("admin", "executive_admin")
    memory_ctx = await get_memory_context(db, "director", user.id) if is_exec else ""
    system = get_director_prompt(user.role)
    system += (
        f"\n\nCURRENT USER CONTEXT:\n- Name: {user.full_name}\n- Role: {user.role}\n"
        f"- Email: {user.email}\n- Address them appropriately by role.\n"
    ) + memory_ctx

    import anthropic as _anthropic_module
    from ai.retry_utils import async_retry
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    messages = [{"role": "user", "content": message}]
    tools = DIRECTOR_TOOLS if is_exec else []
    reply = ""
    MAX_TOOL_TURNS = 6
    _DIRECTOR_MODELS = [("claude-sonnet-4-6", 2048), ("claude-haiku-4-5", 1536)]

    async def _run_agentic_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs)
            if tools:
                _kwargs["tools"] = tools
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": result}
                for b, result in zip(tool_use_blocks, tool_results)
            ]})
        else:
            _reply = _reply or "[Director tool loop exceeded limit — partial response above]"
        return _reply

    for _model, _max_tok in _DIRECTOR_MODELS:
        try:
            reply = await _run_agentic_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _model_err:
            logger.warning("Director AI: model %s failed (%s)", _model, _model_err)
            reply = ""

    if not reply:
        from datetime import datetime as _dt
        _ts = _dt.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        reply = (
            "SYSTEM DESIGNATION: THE DIRECTOR — INFRASTRUCTURE 4.0\n\n"
            "I am operating in contingency mode. The primary AI engine is temporarily unreachable.\n\n"
            f"Status logged: {_ts}"
        )

    await db.chat_history.insert_one({
        "id": str(uuid.uuid4()), "user_id": user.id, "session_id": session_id,
        "mode": "director", "user_msg": message, "assistant_msg": reply,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=90)).isoformat(),
    })
    if is_exec:
        from ai.memory import log_episode as _log_ep
        await _log_ep(db, session_id, "director", user.id, message, reply, [])

    persona = "director" if is_exec else "assistant_director"
    return {"reply": reply, "persona": persona}


@router.get("/ai/director/greeting")
async def director_greeting(user: User = Depends(current_user)):
    import asyncio as _asyncio
    is_exec = user.role in ("admin", "executive_admin")
    persona = "director" if is_exec else "assistant_director"
    if not is_exec:
        greetings = {
            "student":    f"Welcome back, {user.full_name}. I am the Assistant Director. What would you like to work on today?",
            "instructor": f"Welcome back, {user.full_name}. I am the Assistant Director. How can I assist you today?",
        }
        greeting = greetings.get(user.role, greetings["student"])
        return {"greeting": greeting, "role": user.role, "persona": persona}

    now = datetime.now(timezone.utc)
    d7  = (now - timedelta(days=7)).isoformat()
    open_incidents, at_risk_login, pending_labs, pending_flags = await _asyncio.gather(
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.users.count_documents({"role": "student", "is_active": {"$ne": False}, "last_login": {"$lt": d7}}),
        db.lab_submissions.count_documents({"status": "submitted"}),
        db.more_flags.count_documents({"status": "pending"}),
    )
    items = []
    if open_incidents:
        items.append(f"{open_incidents} open incident{'s' if open_incidents != 1 else ''}")
    if at_risk_login:
        items.append(f"{at_risk_login} at-risk student{'s' if at_risk_login != 1 else ''}")
    if pending_labs:
        items.append(f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} pending review")
    if pending_flags:
        items.append(f"{pending_flags} content flag{'s' if pending_flags != 1 else ''} awaiting decision")

    if items:
        status_line = "Monitoring active. Flagged items: " + ", ".join(items) + "."
        close_line  = "Use 'System Status' or 'Threat Report' for a full brief."
    else:
        status_line = "All systems nominal."
        close_line  = "Platform is clean. Standing by for your direction."

    greeting = f"Welcome back, {user.full_name}. I am The Director.\n{status_line}\n{close_line}"
    return {"greeting": greeting, "role": user.role, "persona": persona}


@router.get("/ai/director/pulse")
async def director_pulse(user: User = Depends(current_user)):
    from app.security.auth import require_role as _rr
    from app.security.auth import assert_role
    assert_role(user, "admin")
    import asyncio as _asyncio
    now = datetime.now(timezone.utc)
    h24 = (now - timedelta(hours=24)).isoformat()
    d7  = (now - timedelta(days=7)).isoformat()
    d14 = (now - timedelta(days=14)).isoformat()

    (incidents_24h, incidents_open, pending_labs, new_users_24h, total_users,
     failed_payments_24h, revenue_paid_24h, more_flags_pending, at_risk_login, at_risk_quiz, audit_1h) = await _asyncio.gather(
        db.incidents.count_documents({"created_at": {"$gte": h24}}),
        db.incidents.count_documents({"status": {"$nin": ["resolved", "closed"]}}),
        db.lab_submissions.count_documents({"status": "pending"}),
        db.users.count_documents({"created_at": {"$gte": h24}}),
        db.users.count_documents({"is_active": True}),
        db.payments.count_documents({"status": {"$ne": "paid"}, "created_at": {"$gte": h24}}),
        db.payments.count_documents({"status": "paid", "created_at": {"$gte": h24}}),
        db.more_flags.count_documents({"status": "pending"}),
        db.users.count_documents({"role": "student", "is_active": True, "last_login": {"$lt": d7}}),
        db.users.count_documents({"role": "student", "is_active": True, "last_quiz_score": {"$lt": 70}, "last_quiz_at": {"$gte": d14}}),
        db.audit_log.count_documents({"at": {"$gte": (now - timedelta(hours=1)).isoformat()}}),
    )
    recent_incidents = await db.incidents.find(
        {"status": {"$nin": ["resolved", "closed"]}}, {"_id": 0, "title": 1, "severity": 1, "created_at": 1},
    ).sort("created_at", -1).limit(3).to_list(3)

    alerts = []
    if incidents_open:
        alerts.append({"level": "high" if incidents_open > 2 else "warn", "msg": f"{incidents_open} open incident{'s' if incidents_open != 1 else ''}"})
    if at_risk_login:
        alerts.append({"level": "warn", "msg": f"{at_risk_login} student{'s' if at_risk_login != 1 else ''} inactive 7+ days"})
    if pending_labs:
        alerts.append({"level": "info", "msg": f"{pending_labs} lab submission{'s' if pending_labs != 1 else ''} awaiting review"})
    if more_flags_pending:
        alerts.append({"level": "warn", "msg": f"{more_flags_pending} M.O.R.E. content flag{'s' if more_flags_pending != 1 else ''} pending"})

    return {
        "timestamp": now.isoformat(),
        "health": "critical" if any(a["level"] == "high" for a in alerts) else "warning" if alerts else "nominal",
        "alerts": alerts,
        "metrics": {
            "incidents_24h": incidents_24h, "incidents_open": incidents_open, "pending_labs": pending_labs,
            "new_users_24h": new_users_24h, "total_users": total_users,
            "failed_payments_24h": failed_payments_24h, "revenue_paid_24h": revenue_paid_24h,
            "more_flags_pending": more_flags_pending, "at_risk_login": at_risk_login,
            "at_risk_quiz": at_risk_quiz, "audit_events_1h": audit_1h,
        },
        "recent_incidents": recent_incidents,
    }


# ─── Director / Revenue Director / Sage Elevenlabs TTS ───────────────────────

from fastapi.responses import JSONResponse as _JSONResponse

@router.post("/ai/director/tts")
async def director_tts(body: dict, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "admin")
    from ai.persona_tts import persona_speak
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_director_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("director_tts error: %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return _JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining, "fallback_voice": result.get("fallback_voice", "alloy"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@router.post("/ai/revenue-director/tts")
async def revenue_director_tts(body: dict, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "admin")
    from ai.persona_tts import persona_speak
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_rd_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("revenue_director", text, force_tier=force_tier, db=db)
    except Exception as _e:
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return _JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining, "fallback_voice": result.get("fallback_voice", "echo"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


@router.post("/ai/sage/elevenlabs/tts")
async def sage_elevenlabs_tts(body: dict, user: User = Depends(current_user)):
    from ai.persona_tts import persona_speak
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 4000:
        text = text[:4000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    check_rate(f"ai_sage_el_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await persona_speak("ancestral_sage", text, force_tier=force_tier, db=db)
    except Exception as _e:
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "budget_remaining": 0}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", 0)
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)), "X-Budget-Remaining": str(budget_remaining)})
    return _JSONResponse(content={
        "tier": tier, "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "budget_remaining": budget_remaining, "fallback_voice": result.get("fallback_voice", "shimmer"),
        "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
    }, headers={"X-Tier": tier, "X-Budget-Remaining": str(budget_remaining)})


# ─── Revenue Director ─────────────────────────────────────────────────────────

@router.post("/ai/revenue-director")
async def ai_revenue_director(body: dict, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from ai.persona_loader import get_persona
    from tools.revenue_director_tools import REVENUE_DIRECTOR_TOOLS, dispatch_rd_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE REVENUE DIRECTOR is available to admin and executive accounts.")
    message = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_rd:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/revenue-director", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    memory_ctx = await get_memory_context(db, "revenue_director", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = get_persona("revenue_director") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- GUMROAD_API_KEY: {'SET' if GUMROAD_API_KEY else 'NOT SET'}\n"
    ) + memory_ctx
    _RD_MODELS = [("claude-sonnet-4-6", 4096), ("claude-haiku-4-5", 2048)]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list = []

    async def _run_rd_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=REVENUE_DIRECTOR_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_rd_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[REVENUE DIRECTOR tool loop reached limit]"
        return _reply

    for _model, _max_tok in _RD_MODELS:
        try:
            reply = await _run_rd_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("REVENUE DIRECTOR model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        reply = "THE REVENUE DIRECTOR is temporarily offline. Retry in a moment."

    await log_episode(db, session_id, "revenue_director", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "revenue_director", "mode": "financial_intelligence"}


# ─── Sage Create ──────────────────────────────────────────────────────────────

@router.post("/ai/sage/create")
async def sage_create(body: dict, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from ai.persona_loader import get_persona
    from tools.sage_tools import SAGE_TOOLS, dispatch_sage_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Sage content creation is available to admin and executive accounts.")
    message = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_sage_create:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/sage/create", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    memory_ctx = await get_memory_context(db, "ancestral_sage", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = get_persona("ancestral_sage") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- Mode: CONTENT CREATION\n- GUMROAD_API_KEY: {'SET' if GUMROAD_API_KEY else 'NOT SET'}\n"
    ) + memory_ctx
    _SAGE_MODELS = [("claude-sonnet-4-6", 4096), ("claude-haiku-4-5", 2048)]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list = []

    async def _run_sage_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=SAGE_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_sage_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[SAGE tool loop reached limit]"
        return _reply

    for _model, _max_tok in _SAGE_MODELS:
        try:
            reply = await _run_sage_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("SAGE CREATE model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        reply = "The Ancestral Sage is temporarily offline. Retry in a moment."

    await log_episode(db, session_id, "ancestral_sage", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "ancestral_sage", "mode": "content_creation"}


# ─── Cipher ───────────────────────────────────────────────────────────────────

@router.post("/ai/cipher")
async def ai_cipher(body: dict, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from ai.persona_loader import get_persona
    from tools.cipher_tools import CIPHER_TOOLS, dispatch_cipher_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE CIPHER is available to admin and executive accounts.")
    message = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_cipher:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/cipher", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    memory_ctx = await get_memory_context(db, "cipher", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = get_persona("cipher") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- GUMROAD_API_KEY: {'SET' if GUMROAD_API_KEY else 'NOT SET'}\n"
    ) + memory_ctx
    _CIPHER_MODELS = [("claude-sonnet-4-6", 4096), ("claude-haiku-4-5", 2048)]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list = []

    async def _run_cipher_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=CIPHER_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_cipher_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[CIPHER tool loop reached limit]"
        return _reply

    for _model, _max_tok in _CIPHER_MODELS:
        try:
            reply = await _run_cipher_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("CIPHER model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        reply = "THE CIPHER is temporarily offline. Retry in a moment."

    await log_episode(db, session_id, "cipher", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "cipher", "mode": "creative_authority"}


# ─── Oracle ───────────────────────────────────────────────────────────────────

@router.post("/ai/oracle")
async def ai_oracle(body: dict, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from ai.persona_loader import get_persona
    from tools.oracle_tools import ORACLE_TOOLS, dispatch_oracle_tool
    from ai.prompt_guard import prompt_guard
    from ai.retry_utils import async_retry
    from ai.memory import get_memory_context, log_episode
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "THE ORACLE is available to admin and executive accounts.")
    message = body.get("message", "")
    session_id = body.get("session_id", "default")
    if not message:
        raise HTTPException(400, "Message is required")
    check_rate(f"ai_oracle:{user.id}", max_calls=15, window_sec=60)
    try:
        prompt_guard.assert_message_safe(message, user.role, "/ai/oracle", user.id)
    except ValueError as _e:
        raise HTTPException(400, str(_e))
    memory_ctx = await get_memory_context(db, "oracle", user.id)
    import anthropic as _anthropic_module
    _client = _anthropic_module.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    system = get_persona("oracle") + (
        f"\n\nEXECUTIVE CONTEXT:\n- Operating for: {user.full_name} ({user.role})\n"
        f"- GUMROAD_API_KEY: {'SET' if GUMROAD_API_KEY else 'NOT SET'}\n"
    ) + memory_ctx
    _ORACLE_MODELS = [("claude-sonnet-4-6", 4096), ("claude-haiku-4-5", 2048)]
    MAX_TOOL_TURNS = 8
    reply = ""
    _tools_called: list = []

    async def _run_oracle_loop(model_name: str, max_tok: int) -> str:
        _msgs = [{"role": "user", "content": message}]
        _reply = ""
        for _turn in range(MAX_TOOL_TURNS + 1):
            _kwargs = dict(model=model_name, max_tokens=max_tok, system=system, messages=_msgs, tools=ORACLE_TOOLS)
            _msg = await async_retry(_client.messages.create, max_attempts=3, base_delay=2.0, **_kwargs)
            if _msg.stop_reason != "tool_use":
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            tool_use_blocks = [b for b in _msg.content if b.type == "tool_use"]
            if not tool_use_blocks:
                for block in _msg.content:
                    if hasattr(block, "text"):
                        _reply += block.text
                break
            _tools_called.extend(b.name for b in tool_use_blocks)
            _msgs.append({"role": "assistant", "content": _msg.content})
            tool_results = await _asyncio.gather(*[dispatch_oracle_tool(b.name, b.input, db=db) for b in tool_use_blocks])
            _msgs.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": b.id, "content": r} for b, r in zip(tool_use_blocks, tool_results)]})
        else:
            _reply = _reply or "[ORACLE tool loop reached limit]"
        return _reply

    for _model, _max_tok in _ORACLE_MODELS:
        try:
            reply = await _run_oracle_loop(_model, _max_tok)
            if reply:
                break
        except Exception as _err:
            logger.warning("ORACLE model %s failed: %s", _model, _err)
            reply = ""
    if not reply:
        reply = "THE ORACLE is temporarily offline. Retry in a moment."

    await log_episode(db, session_id, "oracle", user.id, message, reply, _tools_called)
    return {"reply": reply, "persona": "oracle", "mode": "cultural_intelligence"}


# ─── Memory System ────────────────────────────────────────────────────────────

@router.get("/ai/memory/{persona}")
async def get_persona_memory(persona: str, user: User = Depends(current_user)):
    import asyncio as _asyncio
    from ai.memory import get_recent_episodes, get_policy_orders
    if user.role not in ("admin", "executive_admin"):
        raise HTTPException(403, "Memory access requires admin or executive account.")
    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if persona not in valid_personas:
        raise HTTPException(400, f"Unknown persona. Valid: {sorted(valid_personas)}")
    episodes, policies = await _asyncio.gather(
        get_recent_episodes(db, persona, user.id, limit=10),
        get_policy_orders(db, persona),
    )
    return {
        "persona": persona, "episodes": episodes, "policy_orders": policies,
        "episode_count": len(episodes), "policy_count": len(policies),
    }


@router.get("/ai/memory")
async def get_all_memory(user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "executive_admin")
    from ai.memory import list_all_policy_orders
    orders = await list_all_policy_orders(db)
    return {"policy_orders": orders, "count": len(orders)}


@router.post("/ai/memory/policy")
async def set_memory_policy(body: dict, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "executive_admin")
    from ai.memory import set_policy_order
    persona  = (body.get("persona") or "").strip()
    order_id = (body.get("order_id") or "").strip()
    content  = (body.get("content") or "").strip()
    valid_personas = {"cipher", "oracle", "ambassador", "architect", "__global__"}
    if not persona or persona not in valid_personas:
        raise HTTPException(400, f"persona required. Valid: {sorted(valid_personas)}")
    if not order_id or not order_id.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(400, "order_id required (alphanumeric + underscores/hyphens only)")
    if not content:
        raise HTTPException(400, "content required")
    if len(content) > 500:
        raise HTTPException(400, "content must be 500 chars or less")
    ok = await set_policy_order(db, persona, order_id, content, set_by=user.id)
    if not ok:
        raise HTTPException(500, "Failed to save policy order")
    return {"status": "ok", "persona": persona, "order_id": order_id, "content": content}


@router.delete("/ai/memory/policy/{persona}/{order_id}")
async def delete_memory_policy(persona: str, order_id: str, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "executive_admin")
    from ai.memory import remove_policy_order
    ok = await remove_policy_order(db, persona, order_id, removed_by=user.id)
    if not ok:
        raise HTTPException(404, f"Policy order '{order_id}' not found for persona '{persona}'")
    return {"status": "removed", "persona": persona, "order_id": order_id}


# ─── Cipher TTS ───────────────────────────────────────────────────────────────

@router.post("/ai/cipher/tts")
async def cipher_tts(body: dict, user: User = Depends(current_user)):
    from app.security.auth import assert_role
    assert_role(user, "admin")
    from ai.elevenlabs_client import (
        cipher_speak, EL_MONTHLY_CAP, EL_SOFT_WARNING, CIPHER_BACKUP_VOICE as _backup_voice
    )
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(400, "text is required")
    if len(text) > 5000:
        text = text[:5000]
    force_tier = (body.get("force_tier") or "").lower().strip()
    if force_tier not in ("", "elevenlabs", "openai", "text"):
        force_tier = ""
    check_rate(f"ai_cipher_tts:{user.id}", max_calls=20, window_sec=60)
    try:
        result = await cipher_speak(text=text, force_tier=force_tier, db=db)
    except Exception as _e:
        logger.warning("cipher_tts: cipher_speak failed — %s", _e)
        result = {"tier": "text", "audio": None, "clean_text": text, "display_text": text, "voice_settings": {}, "budget_remaining": EL_MONTHLY_CAP}
    tier = result.get("tier", "text")
    budget_remaining = result.get("budget_remaining", EL_MONTHLY_CAP)
    budget_warning = budget_remaining < EL_SOFT_WARNING
    audio = result.get("audio")
    if tier in ("elevenlabs", "elevenlabs_cached") and audio:
        return StreamingResponse(io.BytesIO(audio), media_type="audio/mpeg",
            headers={"X-Tier": tier, "X-Audio-Len": str(len(audio)),
                     "X-Budget-Remaining": str(budget_remaining), "X-Budget-Warning": "true" if budget_warning else "false"})
    if tier == "openai":
        return _JSONResponse(content={
            "tier": "openai", "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
            "voice_settings": result.get("voice_settings", {}), "budget_remaining": budget_remaining,
            "fallback_voice": result.get("fallback_voice", _backup_voice),
            "fallback_endpoint": result.get("fallback_endpoint", "/api/ai/sage/tts"),
        }, headers={"X-Tier": "openai", "X-Budget-Remaining": str(budget_remaining), "X-Budget-Warning": "true" if budget_warning else "false"})
    return _JSONResponse(content={
        "tier": "text", "clean_text": result.get("clean_text", text), "display_text": result.get("display_text", text),
        "voice_settings": result.get("voice_settings", {}), "budget_remaining": budget_remaining,
    }, headers={"X-Tier": "text", "X-Budget-Remaining": str(budget_remaining), "X-Budget-Warning": "true" if budget_warning else "false"})


# ─── Chat History ─────────────────────────────────────────────────────────────

@router.get("/ai/history/{session_id}")
async def ai_history(session_id: str, user: User = Depends(current_user)):
    return await db.chat_history.find(
        {"user_id": user.id, "session_id": session_id}, {"_id": 0}
    ).sort("created_at", 1).to_list(200)
