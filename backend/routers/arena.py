"""
Arena router — The unified competition + synthesis workflow.

4 personas go through 5 graded rounds of self-competition on a project
assigned by a human or Hybrid NAM. A Commissioner scores each round.
2 of 4 personas can be swapped between rounds. The highest-scoring
output is handed to Hybrid NAM for mission alignment and plan creation.

MongoDB collections:
  arena_projects   — project definitions (title, scope, criteria)
  arena_sessions   — active sessions linking project → personas → rounds
  arena_rounds     — individual round outputs per persona
  arena_scores     — Commissioner + human + Hybrid NAM scores per round

Access: staff role OR patron+ tier (enforced here + server-side).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from roles import ROLE_RANK

logger = logging.getLogger("arena")

router = APIRouter(prefix="/api/arena", tags=["Arena"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
_current_user_dep = None
audit = None

MAX_ROUNDS = 5
MAX_PERSONAS = 4
SWAPPABLE_PERSONAS = 2  # 2 of 4 can be swapped


def bind(_current_user, _db=None, _audit=None):
    global db, _current_user_dep, audit
    _current_user_dep = _current_user
    db = _db
    audit = _audit


# ── Auth ──────────────────────────────────────────────────────────────────────

async def _get_user(authorization: str = Header(None)):
    if _current_user_dep is None:
        raise HTTPException(503, "Arena is not available right now.")
    return await _current_user_dep(authorization)


def _require_arena_access(user: Any):
    """Staff role OR patron+ tier required."""
    role = getattr(user, "role", "student")
    rank = ROLE_RANK.get(role, 0)
    # Staff: support_staff (2), oversight (3), admin (4), executive_admin (5)
    # Patron+ tier: checked via feature_tier
    is_staff = rank >= ROLE_RANK.get("instructor", 3)
    is_patron = _tier_rank(user) >= 4  # patron tier
    if not is_staff and not is_patron:
        raise HTTPException(
            403,
            "The Arena requires a staff role or Patron tier. "
            "Upgrade to Patron or contact an administrator.",
        )
    return user


def _tier_rank(user: Any) -> int:
    tier = getattr(user, "feature_tier", "free")
    tier_order = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6}
    return tier_order.get(tier, 0)


def _owner_or_staff(user: Any) -> bool:
    role = getattr(user, "role", "student")
    return ROLE_RANK.get(role, 0) >= ROLE_RANK.get("executive_admin", 5)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coll(name: str):
    if db is None:
        raise HTTPException(503, "Arena database not available.")
    return getattr(db, name)


async def _get_project(project_id: str) -> dict:
    doc = await _coll("arena_projects").find_one({"id": project_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Project not found.")
    return doc


async def _get_session(session_id: str) -> dict:
    doc = await _coll("arena_sessions").find_one({"id": session_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Session not found.")
    return doc


async def _own_session(session: dict, user: Any) -> dict:
    user_id = getattr(user, "id", "")
    if session.get("owner_id") != user_id and not _owner_or_staff(user):
        raise HTTPException(403, "That session does not belong to you.")
    return session


async def _save_session(doc: dict):
    doc["updated_at"] = _now_iso()
    await _coll("arena_sessions").replace_one({"id": doc["id"]}, doc, upsert=True)


def _persona_label(persona_id: str) -> str:
    return persona_id.replace("_", " ").title()


def _list_available_personas() -> List[dict]:
    """Return available personas from the persona loader (excluding unified/judge)."""
    try:
        from ai.persona_loader import load_personas
    except Exception:
        return [
            {"id": "ancestral_sage", "label": "Ancestral Sage"},
            {"id": "director", "label": "Director"},
            {"id": "assistant_director", "label": "Assistant Director"},
            {"id": "elder_council", "label": "Elder Council"},
        ]
    keys = sorted(k for k in load_personas().keys() if k not in ("unified", "hybrid_nam"))
    return [{"id": k, "label": _persona_label(k)} for k in keys]


async def _persona_reply(persona_id: str, system_prompt: str, user_message: str, user_id: str) -> str:
    """Real LLM call through the existing gateway."""
    from ai.llm_gateway import call_llm
    result = await call_llm(
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        persona_label=f"arena:{persona_id}",
        user_id=user_id or None,
        max_tokens=1500,
    )
    text = (result or {}).get("text") or ""
    if not text.strip():
        raise HTTPException(503, "The AI provider returned no response. Try again.")
    return text.strip()


def _persona_prompt(persona_id: str) -> str:
    try:
        from ai.persona_loader import get_persona_sync
        return get_persona_sync(persona_id)
    except Exception:
        return f"You are {_persona_label(persona_id)}. Provide thoughtful, detailed analysis."


def _commissioner_score(output: str, round_num: int, prev_output: Optional[str], project: dict) -> dict:
    """Commissioner auto-scoring: criteria alignment, improvement delta, clarity."""
    criteria = project.get("success_criteria", "")
    
    # Base scores (0-100)
    clarity_score = min(100, max(20, len(output.split()) * 2))  # length proxy
    criteria_score = 50  # baseline — real scoring would use LLM
    improvement_score = 0
    
    if prev_output:
        # Improvement: longer + more detailed = better
        prev_words = len(prev_output.split())
        curr_words = len(output.split())
        if curr_words > prev_words:
            improvement_score = min(80, 30 + (curr_words - prev_words) * 2)
        else:
            improvement_score = max(10, 40 - (prev_words - curr_words))
    else:
        improvement_score = 50  # first round baseline
    
    # Round progression bonus (later rounds should be better)
    round_bonus = round_num * 5
    
    total = int((clarity_score * 0.3 + criteria_score * 0.4 + improvement_score * 0.3) + round_bonus)
    total = min(100, max(0, total))
    
    return {
        "clarity": clarity_score,
        "criteria_alignment": criteria_score,
        "improvement": improvement_score,
        "round_bonus": round_bonus,
        "total": total,
        "commissioner_note": f"Round {round_num} auto-score. Clarity: {clarity_score}, Criteria: {criteria_score}, Improvement: {improvement_score}",
    }


# ── Request/Response Models ───────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    success_criteria: str = Field(default="", max_length=2000)
    assigned_by: str = Field(default="human", pattern="^(human|hybrid_nam)$")


class SessionCreate(BaseModel):
    project_id: str = Field(..., min_length=1)
    persona_ids: List[str] = Field(default_factory=list, max_length=MAX_PERSONAS)


class PersonaSwap(BaseModel):
    slot_index: int = Field(..., ge=0, lt=MAX_PERSONAS)
    new_persona_id: str = Field(..., min_length=1)


class RoundSubmit(BaseModel):
    persona_id: str = Field(..., min_length=1)
    output: str = Field(..., min_length=1, max_length=50000)


class ScoreSubmit(BaseModel):
    round_id: str = Field(..., min_length=1)
    score: int = Field(..., ge=0, le=100)
    note: str = Field(default="", max_length=2000)
    scorer: str = Field(default="human", pattern="^(human|hybrid_nam)$")


class HandoffRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    mission_alignment_notes: str = Field(default="", max_length=2000)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/personas")
async def list_personas(user=Depends(_get_user)):
    """List available personas for the Arena."""
    _require_arena_access(user)
    personas = _list_available_personas()
    return {"personas": personas, "max": MAX_PERSONAS, "swappable": SWAPPABLE_PERSONAS}


# ── Projects ──────────────────────────────────────────────────────────────────

@router.post("/projects", status_code=201)
async def create_project(payload: ProjectCreate, user=Depends(_get_user)):
    """Create a new Arena project (assigned by human or Hybrid NAM)."""
    _require_arena_access(user)
    project_id = uuid.uuid4().hex
    doc = {
        "id": project_id,
        "title": payload.title,
        "description": payload.description,
        "success_criteria": payload.success_criteria,
        "assigned_by": payload.assigned_by,
        "created_by": getattr(user, "id", ""),
        "created_at": _now_iso(),
    }
    await _coll("arena_projects").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/projects")
async def list_projects(user=Depends(_get_user)):
    """List projects the user created or has access to."""
    _require_arena_access(user)
    user_id = getattr(user, "id", "")
    cursor = _coll("arena_projects").find(
        {"$or": [{"created_by": user_id}, {"assigned_by": "hybrid_nam"}]},
        {"_id": 0},
    ).sort("created_at", -1).limit(50)
    return await cursor.to_list(length=50)


@router.get("/projects/{project_id}")
async def get_project(project_id: str, user=Depends(_get_user)):
    """Get a project by ID."""
    _require_arena_access(user)
    return await _get_project(project_id)


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.post("/sessions", status_code=201)
async def create_session(payload: SessionCreate, user=Depends(_get_user)):
    """Create an Arena session: 4 personas compete on a project through 5 rounds."""
    _require_arena_access(user)
    
    project = await _get_project(payload.project_id)
    
    # Default to 4 personas if none specified
    persona_ids = payload.persona_ids
    if not persona_ids:
        all_personas = _list_available_personas()
        persona_ids = [p["id"] for p in all_personas[:MAX_PERSONAS]]
    
    if len(persona_ids) > MAX_PERSONAS:
        raise HTTPException(400, f"Maximum {MAX_PERSONAS} personas allowed.")
    
    session_id = uuid.uuid4().hex
    doc = {
        "id": session_id,
        "project_id": payload.project_id,
        "project_title": project["title"],
        "owner_id": getattr(user, "id", ""),
        "personas": [
            {"persona_id": pid, "label": _persona_label(pid), "locked": i >= (MAX_PERSONAS - SWAPPABLE_PERSONAS)}
            for i, pid in enumerate(persona_ids)
        ],
        "current_round": 0,
        "max_rounds": MAX_ROUNDS,
        "status": "SETUP",  # SETUP → IN_PROGRESS → ROUND_COMPLETE → COMPLETED → HANDED_OFF
        "rounds_completed": 0,
        "best_output": None,
        "best_persona_id": None,
        "best_score": 0,
        "handoff_completed": False,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await _coll("arena_sessions").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/sessions")
async def list_sessions(user=Depends(_get_user)):
    """List the user's Arena sessions."""
    _require_arena_access(user)
    user_id = getattr(user, "id", "")
    cursor = _coll("arena_sessions").find(
        {"owner_id": user_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(50)
    return await cursor.to_list(length=50)


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user=Depends(_get_user)):
    """Get a session with all its rounds and scores."""
    _require_arena_access(user)
    session = await _get_session(session_id)
    await _own_session(session, user)
    
    # Attach rounds
    rounds_cursor = _coll("arena_rounds").find(
        {"session_id": session_id},
        {"_id": 0},
    ).sort("round_num", 1)
    session["rounds"] = await rounds_cursor.to_list(length=100)
    
    return session


# ── Persona Swap ──────────────────────────────────────────────────────────────

@router.patch("/sessions/{session_id}/swap")
async def swap_persona(session_id: str, payload: PersonaSwap, user=Depends(_get_user)):
    """Swap one of the 2 swappable personas. Locked personas (first 2) cannot be swapped."""
    _require_arena_access(user)
    session = await _get_session(session_id)
    await _own_session(session, user)
    
    if session["status"] not in ("SETUP", "IN_PROGRESS"):
        raise HTTPException(409, "Cannot swap personas after rounds are complete.")
    
    personas = session["personas"]
    idx = payload.slot_index
    if idx < 0 or idx >= len(personas):
        raise HTTPException(400, f"Slot index must be 0-{len(personas)-1}.")
    if personas[idx].get("locked"):
        raise HTTPException(403, "This persona slot is locked and cannot be swapped.")
    
    # Check the new persona isn't already in use
    existing_ids = {p["persona_id"] for p in personas}
    if payload.new_persona_id in existing_ids:
        raise HTTPException(409, "That persona is already in use in this session.")
    
    old_id = personas[idx]["persona_id"]
    personas[idx]["persona_id"] = payload.new_persona_id
    personas[idx]["label"] = _persona_label(payload.new_persona_id)
    
    await _save_session(session)
    return {
        "swapped": True,
        "old_persona": old_id,
        "new_persona": payload.new_persona_id,
        "personas": personas,
    }


# ── Rounds ────────────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/rounds", status_code=201)
async def start_round(session_id: str, user=Depends(_get_user)):
    """Start the next round. Each persona independently produces output for self-improvement."""
    _require_arena_access(user)
    session = await _get_session(session_id)
    await _own_session(session, user)
    
    if session["status"] in ("COMPLETED", "HANDED_OFF"):
        raise HTTPException(409, "All rounds are complete.")
    
    next_round = session["current_round"] + 1
    if next_round > MAX_ROUNDS:
        raise HTTPException(409, "All 5 rounds are complete.")
    
    project = await _get_session_project(session)
    
    # Generate output for each persona
    round_outputs = []
    for persona in session["personas"]:
        pid = persona["persona_id"]
        
        # Build context: project + previous round output (self-improvement)
        prev_round = await _get_previous_round(session_id, pid)
        context = _build_round_context(project, persona, next_round, prev_round)
        
        # Get persona's LLM output
        prompt = _persona_prompt(pid)
        try:
            output = await _persona_reply(pid, prompt, context, session["owner_id"])
        except Exception as e:
            logger.warning("Arena persona %s failed round %d: %s", pid, next_round, e)
            output = f"[Persona {pid} was unable to produce output for round {next_round}]"
        
        # Commissioner auto-score
        prev_output = prev_round.get("output") if prev_round else None
        commissioner = _commissioner_score(output, next_round, prev_output, project)
        
        # Create round document
        round_doc = {
            "id": uuid.uuid4().hex,
            "session_id": session_id,
            "round_num": next_round,
            "persona_id": pid,
            "persona_label": persona["label"],
            "output": output,
            "commissioner_score": commissioner,
            "human_score": None,
            "hybrid_nam_score": None,
            "final_score": commissioner["total"],
            "created_at": _now_iso(),
        }
        await _coll("arena_rounds").insert_one(round_doc)
        round_doc.pop("_id", None)
        round_outputs.append(round_doc)
        
        # Track best output across all personas
        if commissioner["total"] > session.get("best_score", 0):
            session["best_score"] = commissioner["total"]
            session["best_output"] = output
            session["best_persona_id"] = pid
    
    # Update session state
    session["current_round"] = next_round
    session["rounds_completed"] = next_round
    session["status"] = "IN_PROGRESS" if next_round < MAX_ROUNDS else "COMPLETED"
    await _save_session(session)
    
    return {
        "round": next_round,
        "status": session["status"],
        "rounds": round_outputs,
        "best_score": session["best_score"],
        "best_persona": session["best_persona_id"],
    }


@router.get("/sessions/{session_id}/rounds")
async def list_rounds(session_id: str, user=Depends(_get_user)):
    """List all rounds for a session."""
    _require_arena_access(user)
    session = await _get_session(session_id)
    await _own_session(session, user)
    
    cursor = _coll("arena_rounds").find(
        {"session_id": session_id},
        {"_id": 0},
    ).sort("round_num", 1)
    return await cursor.to_list(length=100)


# ── Scoring ───────────────────────────────────────────────────────────────────

@router.post("/scores")
async def submit_score(payload: ScoreSubmit, user=Depends(_get_user)):
    """Submit a human or Hybrid NAM score for a round."""
    _require_arena_access(user)
    
    # Find the round
    round_doc = await _coll("arena_rounds").find_one({"id": payload.round_id}, {"_id": 0})
    if not round_doc:
        raise HTTPException(404, "Round not found.")
    
    session = await _get_session(round_doc["session_id"])
    await _own_session(session, user)
    
    # Update the score
    score_field = f"{payload.scorer}_score"
    update = {
        "$set": {
            score_field: {"score": payload.score, "note": payload.note, "scored_at": _now_iso()},
        }
    }
    
    # Recalculate final_score: average of all available scores
    await _coll("arena_rounds").update_one({"id": payload.round_id}, update)
    
    # Re-fetch to get updated scores
    updated_round = await _coll("arena_rounds").find_one({"id": payload.round_id}, {"_id": 0})
    
    scores = []
    if updated_round.get("commissioner_score"):
        scores.append(updated_round["commissioner_score"]["total"])
    if updated_round.get("human_score"):
        scores.append(updated_round["human_score"]["score"])
    if updated_round.get("hybrid_nam_score"):
        scores.append(updated_round["hybrid_nam_score"]["score"])
    
    final_score = int(sum(scores) / len(scores)) if scores else 0
    await _coll("arena_rounds").update_one(
        {"id": payload.round_id},
        {"$set": {"final_score": final_score}},
    )
    
    # Update session best if this round is now the best
    if final_score > session.get("best_score", 0):
        session["best_score"] = final_score
        session["best_output"] = updated_round["output"]
        session["best_persona_id"] = updated_round["persona_id"]
        await _save_session(session)
    
    return {
        "round_id": payload.round_id,
        "final_score": final_score,
        "scores": {
            "commissioner": updated_round.get("commissioner_score"),
            "human": updated_round.get("human_score"),
            "hybrid_nam": updated_round.get("hybrid_nam_score"),
        },
    }


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/results")
async def get_results(session_id: str, user=Depends(_get_user)):
    """Get the ranked results after rounds are complete."""
    _require_arena_access(user)
    session = await _get_session(session_id)
    await _own_session(session, user)
    
    # Get all rounds grouped by persona, ranked by best final_score
    all_rounds = await _coll("arena_rounds").find(
        {"session_id": session_id},
        {"_id": 0},
    ).sort("final_score", -1).to_list(length=100)
    
    # Group by persona, find best round per persona
    persona_best = {}
    for r in all_rounds:
        pid = r["persona_id"]
        if pid not in persona_best or r["final_score"] > persona_best[pid]["final_score"]:
            persona_best[pid] = r
    
    # Rank personas by their best round score
    ranked = sorted(persona_best.values(), key=lambda x: x["final_score"], reverse=True)
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "total_rounds": session["rounds_completed"],
        "ranked_outputs": ranked,
        "best_output": session.get("best_output"),
        "best_persona_id": session.get("best_persona_id"),
        "best_score": session.get("best_score", 0),
        "can_handoff": session["status"] == "COMPLETED" and not session.get("handoff_completed"),
    }


# ── Handoff to Hybrid NAM ─────────────────────────────────────────────────────

@router.post("/handoff")
async def handoff_to_nam(payload: HandoffRequest, user=Depends(_get_user)):
    """Hand the best output to Hybrid NAM for mission alignment and plan creation."""
    _require_arena_access(user)
    
    session = await _get_session(payload.session_id)
    await _own_session(session, user)
    
    if session["status"] != "COMPLETED":
        raise HTTPException(409, "Complete all 5 rounds before handing off.")
    if session.get("handoff_completed"):
        raise HTTPException(409, "This session has already been handed off.")
    
    project = await _get_session_project(session)
    best_output = session.get("best_output", "")
    best_persona = session.get("best_persona_id", "")
    
    if not best_output:
        raise HTTPException(400, "No output to hand off. Complete rounds first.")
    
    # Hybrid NAM evaluates mission alignment using the 12 pillars
    mission_context = (
        f"PROJECT: {project['title']}\n"
        f"DESCRIPTION: {project['description']}\n"
        f"SUCCESS CRITERIA: {project.get('success_criteria', 'None')}\n\n"
        f"BEST OUTPUT (from {best_persona}, score {session.get('best_score', 0)}):\n"
        f"{best_output}\n\n"
        f"MISSION ALIGNMENT NOTES: {payload.mission_alignment_notes}\n\n"
        f"Evaluate this output against the 12 institutional pillars: "
        f"Mission, Strategy, Memory, Governance, Challenge, Ecosystem, "
        f"Power, Economics, Risk, Accountability, Crisis, Succession. "
        f"Then modify the output for mission alignment and create an implementation plan."
    )
    
    # Call Hybrid NAM (unified persona) for mission alignment
    try:
        nam_prompt = _persona_prompt("unified")
        nam_output = await _persona_reply("unified", nam_prompt, mission_context, session["owner_id"])
    except Exception as e:
        logger.warning("Hybrid NAM handoff failed: %s", e)
        nam_output = f"[Hybrid NAM evaluation unavailable. Original output preserved.]\n\n{best_output}"
    
    # Create the handoff document
    handoff_doc = {
        "id": uuid.uuid4().hex,
        "session_id": session["id"],
        "project_id": session["project_id"],
        "project_title": session["project_title"],
        "owner_id": session["owner_id"],
        "best_persona_id": best_persona,
        "best_persona_label": _persona_label(best_persona),
        "best_score": session.get("best_score", 0),
        "original_output": best_output,
        "nam_mission_aligned_output": nam_output,
        "mission_alignment_notes": payload.mission_alignment_notes,
        "status": "HANDOFF_COMPLETE",
        "created_at": _now_iso(),
    }
    await _coll("arena_handoffs").insert_one(handoff_doc)
    handoff_doc.pop("_id", None)
    
    # Update session
    session["status"] = "HANDED_OFF"
    session["handoff_completed"] = True
    await _save_session(session)
    
    # Audit
    if audit:
        try:
            await audit(session["owner_id"], "arena_handoff", meta={
                "session_id": session["id"],
                "project_title": session["project_title"],
                "best_persona": best_persona,
                "best_score": session.get("best_score", 0),
            })
        except Exception:
            pass
    
    return handoff_doc


@router.get("/handoffs")
async def list_handoffs(user=Depends(_get_user)):
    """List handoffs the user has completed."""
    _require_arena_access(user)
    user_id = getattr(user, "id", "")
    cursor = _coll("arena_handoffs").find(
        {"owner_id": user_id},
        {"_id": 0},
    ).sort("created_at", -1).limit(50)
    return await cursor.to_list(length=50)


@router.get("/handoffs/{handoff_id}")
async def get_handoff(handoff_id: str, user=Depends(_get_user)):
    """Get a specific handoff."""
    _require_arena_access(user)
    doc = await _coll("arena_handoffs").find_one({"id": handoff_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Handoff not found.")
    return doc


# ── History ───────────────────────────────────────────────────────────────────

@router.get("/history")
async def arena_history(user=Depends(_get_user)):
    """Full history: projects, sessions, handoffs."""
    _require_arena_access(user)
    user_id = getattr(user, "id", "")
    
    projects = await _coll("arena_projects").find(
        {"created_by": user_id}, {"_id": 0},
    ).sort("created_at", -1).limit(20).to_list(20)
    
    sessions = await _coll("arena_sessions").find(
        {"owner_id": user_id}, {"_id": 0},
    ).sort("created_at", -1).limit(20).to_list(20)
    
    handoffs = await _coll("arena_handoffs").find(
        {"owner_id": user_id}, {"_id": 0},
    ).sort("created_at", -1).limit(20).to_list(20)
    
    return {
        "projects": projects,
        "sessions": sessions,
        "handoffs": handoffs,
    }


# ── Internal Helpers ──────────────────────────────────────────────────────────

async def _get_session_project(session: dict) -> dict:
    """Get the project for a session."""
    return await _get_project(session["project_id"])


async def _get_previous_round(session_id: str, persona_id: str) -> Optional[dict]:
    """Get the most recent round for a persona in this session."""
    cursor = _coll("arena_rounds").find(
        {"session_id": session_id, "persona_id": persona_id},
        {"_id": 0},
    ).sort("round_num", -1).limit(1)
    rounds = await cursor.to_list(1)
    return rounds[0] if rounds else None


def _build_round_context(project: dict, persona: dict, round_num: int, prev_round: Optional[dict]) -> str:
    """Build the prompt context for a persona's round."""
    lines = [
        f"PROJECT: {project['title']}",
        f"DESCRIPTION: {project['description']}",
    ]
    if project.get("success_criteria"):
        lines.append(f"SUCCESS CRITERIA: {project['success_criteria']}")
    
    lines.append(f"\nYOUR ROLE: {persona['label']}")
    lines.append(f"ROUND: {round_num} of {MAX_ROUNDS}")
    
    if prev_round:
        lines.append(f"\nYOUR PREVIOUS OUTPUT (Round {prev_round['round_num']}):")
        lines.append(prev_round["output"])
        lines.append(f"\nYOUR PREVIOUS SCORE: {prev_round.get('final_score', 'N/A')}")
        lines.append("\nIMPROVE on your previous output. Address weaknesses, add depth, refine clarity.")
    else:
        lines.append("\nThis is your FIRST PASS. Produce your best initial analysis/response.")
    
    lines.append("\nProvide your output below. Focus on quality, depth, and improvement over your previous work.")
    
    return "\n".join(lines)
