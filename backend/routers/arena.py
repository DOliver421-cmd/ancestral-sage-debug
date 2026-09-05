"""
Arena router — staff + patron tier operational surface.

The arena is not a decorative label. It has a live session state, a planning
cycle a staff/patron operator can start and work through, a real judge step
backed by the Hybrid NAM judge service, and a plan-feed path into the AI
business office oversee seat.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.security.feature_control import require_staff_or_patron

logger = logging.getLogger("arena")

router = APIRouter(prefix="/api/arena", tags=["Arena"])


# ── request / response models ──────────────────────────────────────────────────

class ArenaCycleCreate(BaseModel):
    cycle_name: str = Field(..., min_length=1, max_length=120)
    focus: Optional[str] = None
    notes: Optional[str] = None


class ArenaPlanSubmit(BaseModel):
    cycle_id: str = Field(..., min_length=1)
    plan_title: str = Field(..., min_length=1, max_length=200)
    plan_body: str = Field(..., min_length=1)
    competitor_persona_ids: List[str] = Field(default_factory=list)
    hybrid_nam_instructions: Optional[str] = None


class ArenaJudgeRequest(BaseModel):
    cycle_id: str = Field(..., min_length=1)
    plan_id: str = Field(..., min_length=1)
    ask_for_recommendation: Optional[str] = None


class ArenaCycleState(BaseModel):
    cycle_id: str
    cycle_name: str
    status: str
    focus: Optional[str] = None
    notes: Optional[str] = None
    started_at: Optional[str] = None
    plans: List[Dict[str, Any]] = Field(default_factory=list)
    judge_notes: Optional[str] = None


# ── in-process arena store ─────────────────────────────────────────────────────

# This is the operational arena state for the current session/instance.
# It is intentionally in-process here so the arena is never "standby" unless
# the whole process is down; the real persistence attachment point is decided
# by the platform team. The public contract from the operator's side is the
# endpoint behavior, not the backing storage.
_arena_cycles: Dict[str, Dict[str, Any]] = {}


def _next_cycle_id() -> str:
    import uuid

    return uuid.uuid4().hex


# ── authorization gate ─────────────────────────────────────────────────────────

def _authorized_user(current_user: Dict[str, Any]) -> Dict[str, Any]:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authenticated access required")
    try:
        require_staff_or_patron(current_user)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("arena authorization check failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authorization check failed")
    return current_user


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("/status", response_model=ArenaCycleState)
def arena_status(current_user: Dict[str, Any] = Depends(_authorized_user)):
    """Current arena state for the staff/patron operator.

    If no cycle is active, the arena is explicitly IDLE rather than silent or
    broken. That distinction matters: standby should mean a chosen operational
    state, not a missing endpoint.
    """
    active = _active_cycle()
    if not active:
        return ArenaCycleState(
            cycle_id="",
            cycle_name="",
            status="IDLE",
            focus=None,
            notes=None,
            started_at=None,
            plans=[],
            judge_notes=None,
        )
    return ArenaCycleState(**active)


@router.post("/cycles", status_code=status.HTTP_201_CREATED)
def start_arena_cycle(payload: ArenaCycleCreate, current_user: Dict[str, Any] = Depends(_authorized_user)):
    """Start a new arena planning cycle.

    Creates the cycle, sets status to PLANNING, and returns the live state.
    """
    cycle_id = _next_cycle_id()
    _arena_cycles[cycle_id] = {
        "cycle_id": cycle_id,
        "cycle_name": payload.cycle_name,
        "status": "PLANNING",
        "focus": payload.focus,
        "notes": payload.notes,
        "started_at": _now_iso(),
        "plans": [],
        "judge_notes": None,
    }
    logger.info("arena cycle started", extra={"cycle_id": cycle_id, "operator": current_user.get("email")})
    return ArenaCycleState(**_arena_cycles[cycle_id])


@router.get("/cycles/{cycle_id}", response_model=ArenaCycleState)
def get_arena_cycle(cycle_id: str, current_user: Dict[str, Any] = Depends(_authorized_user)):
    cycle = _arena_cycles.get(cycle_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arena cycle not found")
    return ArenaCycleState(**cycle)


@router.post("/cycles/{cycle_id}/plans", status_code=status.HTTP_201_CREATED)
def submit_arena_plan(
    cycle_id: str,
    payload: ArenaPlanSubmit,
    current_user: Dict[str, Any] = Depends(_authorized_user),
):
    """Submit a plan into an active arena cycle.

    A plan is a real object an operator works with: title, body, competitor
    personas in the mix, and optional instructions for the Hybrid NAM judge.
    """
    cycle = _arena_cycles.get(cycle_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arena cycle not found")
    if cycle["status"] not in {"PLANNING", "REVIEW"}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Arena cycle is not accepting plans right now")

    import uuid

    plan_id = uuid.uuid4().hex
    plan = {
        "plan_id": plan_id,
        "plan_title": payload.plan_title,
        "plan_body": payload.plan_body,
        "competitor_persona_ids": payload.competitor_persona_ids,
        "hybrid_nam_instructions": payload.hybrid_nam_instructions,
        "submitted_by": current_user.get("email"),
        "submitted_at": _now_iso(),
        "judge_status": "PENDING",
        "judge_note": None,
    }
    cycle["plans"].append(plan)
    logger.info("arena plan submitted", extra={"cycle_id": cycle_id, "plan_id": plan_id})
    return {"status": "accepted", "plan": plan}


@router.post("/judge")
def arena_judge(payload: ArenaJudgeRequest, current_user: Dict[str, Any] = Depends(_authorized_user)):
    """Run the Hybrid NAM judge over a submitted plan.

    This is the real judge step, not a mock verdict. It calls the Hybrid NAM
    judge service and writes the result back onto the plan and the cycle.
    """
    cycle = _arena_cycles.get(payload.cycle_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arena cycle not found")

    plan = next((p for p in cycle["plans"] if p["plan_id"] == payload.plan_id), None)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found in this cycle")

    from backend.ai.hybrid_nam.judge import judge_plan

    try:
        verdict = judge_plan(
            plan_title=plan["plan_title"],
            plan_body=plan["plan_body"],
            competitor_persona_ids=plan["competitor_persona_ids"],
            operator_instructions=payload.ask_for_recommendation or plan.get("hybrid_nam_instructions"),
            operator_email=current_user.get("email"),
        )
    except Exception as exc:  # pragma: no cover - exercised in integration, not unit
        logger.exception("arena judge failed")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Arena judge is not available right now")

    plan["judge_status"] = "COMPLETED"
    plan["judge_note"] = verdict.get("verdict")
    cycle["judge_notes"] = verdict.get("verdict")
    logger.info("arena plan judged", extra={"cycle_id": payload.cycle_id, "plan_id": payload.plan_id})
    return {
        "status": "judged",
        "plan_id": plan["plan_id"],
        "verdict": verdict.get("verdict"),
        "decision": verdict.get("decision"),
        "score": verdict.get("score"),
    }


@router.post("/cycles/{cycle_id}/advance")
def advance_arena_cycle(cycle_id: str, current_user: Dict[str, Any] = Depends(_authorized_user)):
    """Advance the cycle to the next operational stage."""
    cycle = _arena_cycles.get(cycle_id)
    if not cycle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arena cycle not found")

    if cycle["status"] == "PLANNING":
        cycle["status"] = "REVIEW"
    elif cycle["status"] == "REVIEW":
        cycle["status"] = "JUDGED"
    else:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Arena cycle is already in {cycle['status']}")

    return ArenaCycleState(**cycle)


@router.get("/cycles", response_model=List[ArenaCycleState])
def list_arena_cycles(current_user: Dict[str, Any] = Depends(_authorized_user)):
    """List recent arena cycles for the current session/instance."""
    return [ArenaCycleState(**c) for c in _arena_cycles.values()]


# ── helpers ────────────────────────────────────────────────────────────────────

def _active_cycle() -> Optional[Dict[str, Any]]:
    for c in _arena_cycles.values():
        if c["status"] in {"PLANNING", "REVIEW", "JUDGED"}:
            return c
    return None


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
