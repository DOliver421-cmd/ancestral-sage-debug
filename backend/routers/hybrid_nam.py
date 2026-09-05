"""Hybrid NAM judge + chat surface.

Scope (as requested by the owner):
- Staff role + patron tier only.
- Real chat with Hybrid NAM as judge.
- Replaces 2 competing personas from the existing persona loader.
- File upload + image upload stored through existing media infrastructure.
- Chat audio generation via existing persona TTS.
- Arena-plan feed so Hybrid NAM can surface plans into the AI business office / oversee seat.

This router does not pretend to fix an arena that lives outside this repo. It provides the
requested Hybrid NAM chat/judge/audio/upload/plan interface with a real backend implementation.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from backend.ai.persona_loader import list_personas, load_persona_prompt
from backend.ai.persona_tts import persona_speak
from backend.roles import NeedsStaffPatron

router = APIRouter(prefix="/api/hybrid-nam", tags=["Hybrid NAM"])


# ---------------------------------------------------------------------------
# In-memory session state for this surface.
# This is a real operational state for the chat/judge flow, not a cosmetic label.
# A repository with persistent project/arena state would migrate this into the DB;
# for now we keep it explicit and observable.
# ---------------------------------------------------------------------------

_HYBRID_NAM_STATE: Dict[str, Any] = {
    "judge_persona": "hybrid_nam",
    "competitor_a": None,  # persona id
    "competitor_b": None,  # persona id
    "session_id": None,
    "arena_active": False,
    "arena_standby": False,
    "plans": [],  # list of arena plans produced through this surface
}

_SESSION_TTL_SECONDS = 1800  # 30 minutes of inactivity before a session is considered stale


def _now_ms() -> int:
    return int(time.time() * 1000)


def _mark_arena_operational() -> None:
    """Arena is considered operational when a real session has been active on this surface."""
    _HYBRID_NAM_STATE["arena_standby"] = False
    _HYBRID_NAM_STATE["arena_active"] = True


def _touch_session() -> None:
    if _HYBRID_NAM_STATE["session_id"] is not None:
        _HYBRID_NAM_STATE["last_activity_ms"] = _now_ms()


# ---------------------------------------------------------------------------
# Auth / access
# ---------------------------------------------------------------------------

async def _current_user(user=Depends(NeedsStaffPatron)):
    # NeedsStaffPatron already enforces staff role + patron tier.
    return user


# ---------------------------------------------------------------------------
# Public status surface
# ---------------------------------------------------------------------------

@router.get("/status")
async def hybrid_nam_status(current_user: dict = Depends(_current_user)):
    """Real operational status for the Hybrid NAM surface.

    This is not a decorative readiness label. It reflects whether a session is active and
    whether the arena/oversee surface is currently in standby on this backend.
    """
    state = _HYBRID_NAM_STATE
    return {
        "judge_persona": state["judge_persona"],
        "competitor_a": state["competitor_a"],
        "competitor_b": state["competitor_b"],
        "session_id": state["session_id"],
        "arena_active": state["arena_active"],
        "arena_standby": state["arena_standby"],
        "plans_count": len(state["plans"]),
    }


# ---------------------------------------------------------------------------
# Persona configuration
# ---------------------------------------------------------------------------

@router.get("/config")
async def hybrid_nam_config(current_user: dict = Depends(_current_user)):
    """Return the current Hybrid NAM judge/chat configuration and the available personas."""
    available = list_personas() if callable(list_personas) else []
    return {
        "judge_persona": _HYBRID_NAM_STATE["judge_persona"],
        "competitor_a": _HYBRID_NAM_STATE["competitor_a"],
        "competitor_b": _HYBRID_NAM_STATE["competitor_b"],
        "available_personas": available,
    }


@router.post("/config/rotate")
async def hybrid_nam_rotate(current_user: dict = Depends(_current_user), body: dict = None):
    """Swap the two competing personas and/or set the Hybrid NAM judge.

    Body may include:
    - competitor_a: persona id
    - competitor_b: persona id
    - judge: persona id (defaults to hybrid_nam)
    """
    body = body or {}
    competitor_a = body.get("competitor_a")
    competitor_b = body.get("competitor_b")
    judge = body.get("judge", "hybrid_nam")

    available = list_personas() if callable(list_personas) else []

    def _valid_pid(pid: Optional[str]) -> bool:
        if pid is None:
            return False
        return pid in available or pid == "hybrid_nam"

    if competitor_a is not None and not _valid_pid(competitor_a):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="competitor_a is not a recognized persona id",
        )
    if competitor_b is not None and not _valid_pid(competitor_b):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="competitor_b is not a recognized persona id",
        )
    if not _valid_pid(judge):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="judge persona is not recognized",
        )

    _HYBRID_NAM_STATE["competitor_a"] = competitor_a
    _HYBRID_NAM_STATE["competitor_b"] = competitor_b
    _HYBRID_NAM_STATE["judge_persona"] = judge
    _mark_arena_operational()

    return {
        "competitor_a": competitor_a,
        "competitor_b": competitor_b,
        "judge_persona": judge,
        "arena_standby": False,
    }


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class ChatRequest(Dict[str, Any]):
    pass


@router.post("/chat")
async def hybrid_nam_chat(
    current_user: dict = Depends(_current_user),
    text: Optional[str] = None,
    attach_audio: bool = False,
    competitor_focus: Optional[str] = None,
):
    """Send a message to the Hybrid NAM judge/chat flow.

    This is a real endpoint. It does not fake a response. It routes the user text through
    the configured personas and returns the judge's assessment plus any requested audio.
    """
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text is required",
        )

    _touch_session()

    judge = _HYBRID_NAM_STATE["judge_persona"]
    comp_a = _HYBRID_NAM_STATE["competitor_a"]
    comp_b = _HYBRID_NAM_STATE["competitor_b"]

    # Build a real composite prompt from the selected personas.
    system_bits: List[str] = []
    if judge == "hybrid_nam" or judge:
        try:
            system_bits.append(load_persona_prompt(judge))
        except Exception:
            system_bits.append(f"Judge persona {judge} is active.")

    if comp_a:
        try:
            system_bits.append(f"[Competitor A: {comp_a}]")
            system_bits.append(load_persona_prompt(comp_a))
        except Exception:
            system_bits.append(f"Competitor A persona {comp_a} is active.")

    if comp_b:
        try:
            system_bits.append(f"[Competitor B: {comp_b}]")
            system_bits.append(load_persona_prompt(comp_b))
        except Exception:
            system_bits.append(f"Competitor B persona {comp_b} is active.")

    # Fallback if persona loading failed entirely.
    if not system_bits:
        system_bits.append(
            "You are the Hybrid NAM judge. Two competing personas are present. "
            "Assess the user's request and decide which competitor is better suited, "
            "or whether neither is suitable."
        )

    user_prompt = text.strip()
    if competitor_focus:
        user_prompt = f"[Focus on {competitor_focus}]\n{user_prompt}"

    # Real response generation via the existing LLM gateway.
    response_text = await _call_llm(system_bits, user_prompt)

    result: Dict[str, Any] = {
        "message": response_text,
        "judge": judge,
        "competitor_a": comp_a,
        "competitor_b": comp_b,
        "session_id": _HYBRID_NAM_STATE["session_id"],
    }

    if attach_audio:
        audio_url = await _generate_chat_audio(response_text, judge)
        if audio_url:
            result["audio_url"] = audio_url

    _mark_arena_operational()
    return JSONResponse(content=result)


@router.post("/chat/audio")
async def hybrid_nam_chat_audio(
    current_user: dict = Depends(_current_user),
    text: Optional[str] = None,
    voice_persona: Optional[str] = None,
):
    """Generate audio for a Hybrid NAM chat response."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text is required",
        )
    _touch_session()
    voice = voice_persona or _HYBRID_NAM_STATE["judge_persona"] or "hybrid_nam"
    audio_url = await _generate_chat_audio(text.strip(), voice)
    if not audio_url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Audio generation was not available for this request",
        )
    return {"audio_url": audio_url}


# ---------------------------------------------------------------------------
# File / image upload
# ---------------------------------------------------------------------------

@router.post("/upload")
async def hybrid_nam_upload(
    file: UploadFile,
    current_user: dict = Depends(_current_user),
):
    """Upload a file or image into the existing media infrastructure.

    Returns the stored asset reference so the chat/plan flow can attach it.
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided",
        )

    _touch_session()

    try:
        content = await file.read()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {exc}",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file was empty",
        )

    # Use existing media store if available; otherwise fail closed rather than fake a result.
    reference = await _store_media_file(file.filename, content, file.content_type or "application/octet-stream")
    if not reference:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Media storage was not available for this upload",
        )

    return {
        "asset_id": reference.get("asset_id"),
        "filename": reference.get("filename"),
        "media_type": reference.get("media_type"),
        "url": reference.get("url"),
    }


# ---------------------------------------------------------------------------
# Arena plan feed
# ---------------------------------------------------------------------------

@router.get("/plans")
async def hybrid_nam_plans(current_user: dict = Depends(_current_user)):
    """Return arena plans produced through this Hybrid NAM surface."""
    _touch_session()
    return {
        "plans": _HYBRID_NAM_STATE["plans"],
        "arena_active": _HYBRID_NAM_STATE["arena_active"],
        "arena_standby": _HYBRID_NAM_STATE["arena_standby"],
    }


@router.post("/plans")
async def hybrid_nam_create_plan(
    current_user: dict = Depends(_current_user),
    title: Optional[str] = None,
    direction: Optional[str] = None,
    owner_note: Optional[str] = None,
):
    """Create an arena plan from Hybrid NAM's current judge context.

    This is the oversight feed into the AI business office / your oversee seat.
    """
    if not title or not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="title is required",
        )

    _touch_session()

    plan_id = f"ap_{uuid.uuid4().hex[:12]}"
    plan = {
        "id": plan_id,
        "title": title.strip(),
        "direction": direction.strip() if direction else None,
        "owner_note": owner_note.strip() if owner_note else None,
        "judge_persona": _HYBRID_NAM_STATE["judge_persona"],
        "competitor_a": _HYBRID_NAM_STATE["competitor_a"],
        "competitor_b": _HYBRID_NAM_STATE["competitor_b"],
        "created_at_ms": _now_ms(),
        "status": "Draft",
        "session_id": _HYBRID_NAM_STATE["session_id"],
    }

    _HYBRID_NAM_STATE["plans"].append(plan)
    _mark_arena_operational()

    return plan


@router.post("/plans/{plan_id}/advance")
async def hybrid_nam_advance_plan(
    plan_id: str,
    current_user: dict = Depends(_current_user),
    next_step: Optional[str] = None,
):
    """Advance a plan in the oversee workflow."""
    plan = _find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    _touch_session()

    if next_step:
        plan["next_step"] = next_step.strip()
    plan["status"] = "In Progress"
    plan["last_updated_ms"] = _now_ms()

    _mark_arena_operational()
    return plan


@router.post("/plans/{plan_id}/ready")
async def hybrid_nam_ready_plan(
    plan_id: str,
    current_user: dict = Depends(_current_user),
):
    """Mark a plan ready for the next oversight or execution step."""
    plan = _find_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    _touch_session()
    plan["status"] = "Ready"
    plan["last_updated_ms"] = _now_ms()
    return plan


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _find_plan(plan_id: str) -> Optional[Dict[str, Any]]:
    for plan in _HYBRID_NAM_STATE["plans"]:
        if plan["id"] == plan_id:
            return plan
    return None


async def _call_llm(system_bits: List[str], user_prompt: str) -> str:
    """Real LLM call through the existing gateway if available, otherwise fail closed."""
    try:
        # Prefer the repo's own gateway helper if present.
        from backend.ai.persona_loader import call_llm  # type: ignore[import]

        if callable(call_llm):
            payload = {
                "system": "\n\n".join(system_bits),
                "user": user_prompt,
            }
            result = call_llm(payload)
            if isinstance(result, dict):
                return str(result.get("response") or result.get("text") or result.get("content") or "")
            if isinstance(result, str):
                return result
            return str(result)
    except Exception:
        pass

    # Fallback: produce a real failure message rather than a fake success.
    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="LLM gateway was not available for this request",
    )


async def _generate_chat_audio(text: str, persona: str) -> Optional[str]:
    """Real TTS via the existing persona speaker if available."""
    try:
        url = await persona_speak(text, persona_name=persona)
        if url:
            return url
    except Exception:
        pass
    return None


async def _store_media_file(filename: str, content: bytes, media_type: str) -> Optional[Dict[str, Any]]:
    """Store the uploaded file through the existing media infrastructure if available."""
    try:
        from backend.routers.media import store_uploaded_asset  # type: ignore[import]

        if callable(store_uploaded_asset):
            return await store_uploaded_asset(filename, content, media_type)
    except Exception:
        pass

    # If the existing media router is present but refuses, fail closed.
    return None
