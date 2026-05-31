"""app/routes/supervisor_v2.py — Supervisor Console API (Phases 2–3 reconstruction).

Provides the real-authority Supervisor control routes:
  - Policies: CRUD on supervisor_policies
  - Feature flags: CRUD on feature_flags
  - Decisions: read supervisor_decisions
  - Governance log: read governance_log
  - Compliance dashboard: read compliance_events

These routes sit alongside the existing supervisor.py (moderation, greeter, sage sessions)
and are the new authoritative layer per SYSTEM_RECONSTRUCTION_BLUEPRINT.

All endpoints require executive_admin role.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Optional

from app.models.user import User
from app.security.auth import require_role
from app.utils.audit import audit

router = APIRouter()


class PolicyUpsertReq(BaseModel):
    key: str
    value: Any
    description: str = ""


class FeatureFlagUpsertReq(BaseModel):
    key: str
    value: Any
    description: str = ""


class DecisionOverrideReq(BaseModel):
    decision_id: str
    new_result: str
    rationale: str


# ── Policies ──────────────────────────────────────────────────────────────────

@router.get("/supervisor/v2/policies")
async def list_policies(
    include_inactive: bool = False,
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.supervisor_service import list_policies
    return {"policies": await list_policies(include_inactive=include_inactive)}


@router.put("/supervisor/v2/policies")
async def upsert_policy(body: PolicyUpsertReq, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import set_policy
    doc = await set_policy(body.key, body.value, body.description, actor_id=user.id)
    await audit(user.id, "supervisor.policy.set", meta={"key": body.key, "value": body.value})
    return doc


@router.get("/supervisor/v2/policies/{key}")
async def get_policy(key: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import get_policy as _get
    value = await _get(key)
    if value is None:
        raise HTTPException(404, f"Policy '{key}' not found or inactive")
    return {"key": key, "value": value}


@router.delete("/supervisor/v2/policies/{key}")
async def delete_policy(key: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import delete_policy
    ok = await delete_policy(key, actor_id=user.id)
    if not ok:
        raise HTTPException(404, f"Policy '{key}' not found")
    await audit(user.id, "supervisor.policy.deleted", meta={"key": key})
    return {"ok": True, "key": key}


# ── Feature Flags ─────────────────────────────────────────────────────────────

@router.get("/supervisor/v2/flags")
async def list_flags(
    include_inactive: bool = False,
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.supervisor_service import list_feature_flags
    return {"flags": await list_feature_flags(include_inactive=include_inactive)}


@router.put("/supervisor/v2/flags")
async def upsert_flag(body: FeatureFlagUpsertReq, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import set_feature_flag
    doc = await set_feature_flag(body.key, body.value, body.description, actor_id=user.id)
    await audit(user.id, "supervisor.flag.set", meta={"key": body.key, "value": body.value})
    return doc


@router.get("/supervisor/v2/flags/{key}")
async def get_flag(key: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import get_feature_flag
    value = await get_feature_flag(key)
    if value is None:
        raise HTTPException(404, f"Flag '{key}' not found or inactive")
    return {"key": key, "value": value}


@router.delete("/supervisor/v2/flags/{key}")
async def disable_flag(key: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import disable_feature_flag
    ok = await disable_feature_flag(key, actor_id=user.id)
    if not ok:
        raise HTTPException(404, f"Flag '{key}' not found")
    await audit(user.id, "supervisor.flag.disabled", meta={"key": key})
    return {"ok": True, "key": key}


# ── Decisions ─────────────────────────────────────────────────────────────────

@router.get("/supervisor/v2/decisions")
async def list_decisions(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, le=500),
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.supervisor_service import list_decisions
    decisions = await list_decisions(actor_id=actor_id, action=action, limit=limit)
    return {"decisions": decisions, "total": len(decisions)}


@router.get("/supervisor/v2/decisions/{decision_id}")
async def get_decision(decision_id: str, user: User = Depends(require_role("executive_admin"))):
    from app.services.supervisor_service import get_decision
    doc = await get_decision(decision_id)
    if not doc:
        raise HTTPException(404, "Decision not found")
    return doc


@router.post("/supervisor/v2/decisions/override")
async def override_decision(body: DecisionOverrideReq, user: User = Depends(require_role("executive_admin"))):
    """
    Record a Supervisor override of a prior decision.
    The original decision is immutable — this creates a new linked decision.
    """
    from app.services.supervisor_service import get_decision, record_decision
    original = await get_decision(body.decision_id)
    if not original:
        raise HTTPException(404, "Original decision not found")
    override = await record_decision(
        actor_type="supervisor",
        actor_id=user.id,
        action=f"override.{original['action']}",
        result=body.new_result,
        rationale={
            "original_decision_id": body.decision_id,
            "original_result": original["result"],
            "override_rationale": body.rationale,
        },
    )
    await audit(user.id, "supervisor.decision.overridden",
                meta={"original_id": body.decision_id, "new_result": body.new_result})
    return override


# ── Governance Log ────────────────────────────────────────────────────────────

@router.get("/supervisor/v2/governance-log")
async def governance_log(
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = Query(100, le=500),
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.supervisor_service import get_governance_log
    events = await get_governance_log(event_type=event_type, actor_id=actor_id, limit=limit)
    return {"events": events, "total": len(events)}


# ── Compliance Dashboard ──────────────────────────────────────────────────────

@router.get("/supervisor/v2/compliance")
async def compliance_dashboard(
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    verdict: Optional[str] = None,
    limit: int = Query(100, le=500),
    user: User = Depends(require_role("executive_admin")),
):
    from app.services.compliance_engine import list_compliance_events
    events = await list_compliance_events(action=action, actor_id=actor_id, verdict=verdict, limit=limit)
    return {"events": events, "total": len(events)}


@router.post("/supervisor/v2/compliance/evaluate")
async def evaluate_compliance(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Dry-run a compliance evaluation without executing any action.
    Returns the verdict, validator that triggered, log_key, and message.
    Useful for Supervisor to preview decisions before committing.
    """
    action = body.get("action", "")
    context = body.get("context", {})
    if not action:
        raise HTTPException(400, "action is required")
    from app.services.compliance_engine import ComplianceEngine
    result = await ComplianceEngine.evaluate(
        action, "supervisor", user.id, context, create_supervisor_decision=False
    )
    return {
        "verdict": result.verdict,
        "validator": result.validator,
        "log_key": result.log_key,
        "message": result.message,
        "passed": result.passed,
    }


# ── FallbackDecisionTree dry-run ──────────────────────────────────────────────

@router.post("/supervisor/v2/decision-tree/evaluate")
async def evaluate_decision_tree(
    body: dict,
    user: User = Depends(require_role("executive_admin")),
):
    """
    Run the FALLBACK_DECISION_TREE against a provided context.
    Returns verdict, log_key, and message without persisting anything.
    """
    from app.services.supervisor_service import evaluate_fallback_decision_tree
    result = await evaluate_fallback_decision_tree(body)
    return {
        "verdict": result.verdict,
        "log_key": result.log_key,
        "message": result.message,
    }
