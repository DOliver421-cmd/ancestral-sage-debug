"""app/routes/partnership.py — Partnership points, puzzle game, and Sovereign chat.

Ported from backend/server.py lines 10018–10100.
"""
import logging
import secrets as _secrets
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user, require_role
from app.utils.audit import audit

logger = logging.getLogger("lcewai")
router = APIRouter()


# ── Partnership Points & Tiers ────────────────────────────────────────────────

@router.get("/partnership/status")
async def partnership_status(user: User = Depends(current_user)):
    from app.services.partnership.points import get_status
    return await get_status(db, user.id)


@router.get("/partnership/ledger")
async def partnership_ledger(limit: int = 20, user: User = Depends(current_user)):
    from app.services.partnership.points import LEDGER_COLLECTION
    try:
        docs = await db[LEDGER_COLLECTION].find(
            {"user_id": user.id}, {"_id": 0, "user_id": 0}
        ).sort("ts", -1).limit(min(limit, 50)).to_list(50)
        for d in docs:
            if hasattr(d.get("ts"), "isoformat"):
                d["ts"] = d["ts"].isoformat()
        return docs
    except Exception:
        return []


# ── Puzzle Game ───────────────────────────────────────────────────────────────

async def _optional_user_id(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    try:
        from app.security.auth import decode_token
        token = authorization.replace("Bearer ", "").strip()
        payload = decode_token(token)
        return payload.get("sub")
    except Exception:
        return None


class _PuzzleAnswerBody(BaseModel):
    puzzle_id: str
    answer: str


@router.get("/puzzles/next")
async def puzzles_next(authorization: Optional[str] = Header(None)):
    from app.services.puzzles.engine import next_puzzle
    uid = await _optional_user_id(authorization)
    return await next_puzzle(db, uid)


@router.post("/puzzles/answer")
async def puzzles_answer(body: _PuzzleAnswerBody, authorization: Optional[str] = Header(None)):
    from app.services.puzzles.engine import submit_answer
    uid = await _optional_user_id(authorization)
    return await submit_answer(db, uid, body.puzzle_id, body.answer)


# ── Sovereign Chat (executive only) ──────────────────────────────────────────

class _SovereignChatBody(BaseModel):
    message: str

class _SovereignMemoryBody(BaseModel):
    content: str
    kind: Optional[str] = "fact"


async def _build_sovereign_prompt(db, user_id: str) -> str:
    try:
        from app.services.sovereign.sovereign_memory import load_memory_block
        memory = await load_memory_block(db, user_id)
    except Exception:
        memory = ""
    try:
        from app.services.sovereign.sovereign_persona import SOVEREIGN_PERSONA
        base = SOVEREIGN_PERSONA
    except Exception:
        base = "You are The Sovereign — NAM Oshun's booking, revenue, and business-development engine."
    memory_block = f"\n\n=== PERSISTENT MEMORY (current session context) ===\n{memory}" if memory else ""
    return base + memory_block


@router.post("/sovereign/chat")
async def sovereign_chat(body: _SovereignChatBody, user: User = Depends(require_role("executive_admin"))):
    from datetime import date as _date
    system = await _build_sovereign_prompt(db, user.id)
    today = _date.today().strftime("%A, %B %d, %Y")
    system = f"TODAY'S DATE: {today}\n\n" + system

    # Route report requests to a structured template
    lowered = body.message.lower()
    is_report = any(kw in lowered for kw in [
        "morning report", "progress report", "weekly report", "pipeline report",
        "weekly update", "report", "update me", "what's happening", "what happened",
        "status update", "what's going on", "what do we have",
    ])
    user_message = body.message
    if is_report:
        # Inject live pipeline data
        try:
            from datetime import date as _date2
            from app.routes.sovereign_pipeline import COLLECTION, STAGE_PROBABILITY, CLOSED_STAGES, STAGE_ORDER
            pipeline_docs = await db[COLLECTION].find({"user_id": user.id}, {"_id": 0}).to_list(1000)
            if pipeline_docs:
                confirmed_rev = sum(
                    (d.get("fee_offered") or 0) for d in pipeline_docs
                    if d.get("stage") in CLOSED_STAGES
                )
                weighted = sum(
                    (d.get("fee_offered") or 0) * (d.get("close_probability") or STAGE_PROBABILITY.get(d.get("stage", "Prospecting"), 0.0))
                    for d in pipeline_docs
                    if d.get("stage") not in CLOSED_STAGES
                )
                by_stage: dict = {}
                for d in pipeline_docs:
                    s = d.get("stage", "Prospecting")
                    by_stage.setdefault(s, []).append(d)
                stage_lines = []
                for s in STAGE_ORDER:
                    recs = by_stage.get(s, [])
                    if not recs:
                        continue
                    items = ", ".join(
                        f"{r['institution']} (${(r.get('fee_offered') or 0) / 100:,.0f})" for r in recs
                    )
                    stage_lines.append(f"  {s} ({len(recs)}): {items}")
                _today_str = _date2.today().isoformat()
                pipeline_prefix = (
                    f"LIVE PIPELINE DATA (as of {_today_str}):\n"
                    f"Confirmed: {sum(1 for d in pipeline_docs if d.get('stage') in CLOSED_STAGES)} booking(s) — ${confirmed_rev / 100:,.0f} total\n"
                    f"Active pipeline weighted value: ${weighted / 100:,.0f}\n"
                    "By stage:\n"
                    + "\n".join(stage_lines)
                    + "\n\n"
                )
            else:
                pipeline_prefix = "LIVE PIPELINE DATA: No institutions in pipeline yet.\n\n"
            user_message = pipeline_prefix + user_message
        except Exception:
            logger.exception("Pipeline data injection failed")
        user_message = (
            f"{user_message}\n\n"
            f"Generate a structured Morning Report for {today} in this exact format:\n\n"
            "**SOVEREIGN MORNING REPORT**\n\n"
            "**CONFIRMED BOOKINGS**\n"
            "[List confirmed bookings with dates, venues, fees. If none in memory: No confirmed bookings on record yet.]\n\n"
            "**ACTIVE PIPELINE**\n"
            "[Stage → Institution → Weighted Value. If none: Pipeline is empty — ready to begin first 50-institution batch.]\n\n"
            "**THIS WEEK: NEW / ADVANCED / LOST**\n"
            "[What moved. If no data: No movement logged this week.]\n\n"
            "**UPCOMING MILESTONE WINDOWS**\n"
            "[Next 2-3 booking-season windows with outreach deadlines based on today's date.]\n\n"
            "**ACTION ITEMS FOR NAM OSHUN'S REVIEW**\n"
            "[3-5 specific next steps. If pipeline is empty, first action: Authorize The Sovereign to begin the first 50-institution outreach batch.]\n\n"
            "Be direct. Use real data from memory. State plainly when data is absent. No padding."
        )
    try:
        import os, httpx
        key = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
        if not key:
            raise HTTPException(503, "No AI key configured")
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": "claude-sonnet-4-6", "max_tokens": 2048,
                      "system": system, "messages": [{"role": "user", "content": user_message}]},
            )
            r.raise_for_status()
            reply = r.json()["content"][0]["text"]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Sovereign AI error")
        raise HTTPException(502, f"Sovereign AI error: {e}")
    try:
        from app.services.sovereign.sovereign_memory import save_memory
        await save_memory(db, user.id, f"Asked: {body.message[:200]}", kind="note")
    except Exception:
        pass

    # ── NL pipeline command detection ─────────────────────────────────────────
    _pipeline_keywords = [
        "add ", " to pipeline", " to prospecting", " to outreach", " to conversation",
        " to proposal", " to negotiation", " confirmed", " lost", "move ", "mark ",
        "set fee for", "remove ", " from pipeline", "drop ",
    ]
    msg_lower = body.message.lower()
    if any(kw in msg_lower for kw in _pipeline_keywords):
        try:
            from app.routes.sovereign_pipeline import parse_pipeline_command, ParseCommandBody
            parse_body = ParseCommandBody(message=body.message)
            parse_result = await parse_pipeline_command(parse_body, user=user)
            if parse_result.get("executed"):
                action = parse_result.get("action", "updated")
                institution = parse_result.get("institution", "")
                stage = parse_result.get("stage", "")
                confirmation = f"\n\n---\n*Pipeline {action}: **{institution}**"
                if stage:
                    confirmation += f" → {stage}"
                confirmation += ".*"
                reply = reply + confirmation
        except Exception:
            logger.exception("Pipeline NL command execution failed")

    return {"reply": reply}


@router.get("/sovereign/memory")
async def sovereign_memory_list(user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import load_memory_block
    return {"memory": await load_memory_block(db, user.id)}


@router.post("/sovereign/memory")
async def sovereign_memory_add(body: _SovereignMemoryBody, user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import save_memory
    return {"saved": await save_memory(db, user.id, body.content, kind=body.kind or "fact")}


@router.delete("/sovereign/memory")
async def sovereign_memory_clear(user: User = Depends(require_role("executive_admin"))):
    from app.services.sovereign.sovereign_memory import clear_memory
    return {"cleared": await clear_memory(db, user.id)}
