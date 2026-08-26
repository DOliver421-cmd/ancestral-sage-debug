"""
Jamil ↔ NAM Protocol — Director ↔ Assistant Director Communication

Per specification §27:
  JAMIL asks "What can we do?"
  NAM answers "What should we do, why, and does it serve the mission?"

The protocol supports:
- Leadership review requests from Jamil
- Recommendations from NAM
- Decision ledger entries
- Escalation when human approval is required
"""

import json
import uuid
from datetime import datetime
from typing import Optional


# ── Protocol Messages ─────────────────────────────────────────────────────────

def create_review_request(
    proposal: str,
    objective: str,
    constraints: Optional[list[str]] = None,
    risks: Optional[list[str]] = None,
    expected_outcome: str = "",
    actor: str = "Jamil",
) -> dict:
    """
    Jamil submits a proposal for NAM's leadership review.
    """
    return {
        "request_id": f"REQ-{uuid.uuid4().hex[:8].upper()}",
        "request_type": "leadership_review",
        "actor": actor,
        "timestamp": datetime.utcnow().isoformat(),
        "proposal": proposal,
        "objective": objective,
        "constraints": constraints or [],
        "risks": risks or [],
        "expected_outcome": expected_outcome,
        "status": "pending",
    }


def process_review(
    request: dict,
    evaluation: dict,
    context: Optional[dict] = None,
) -> dict:
    """
    NAM processes a review request and returns a recommendation.
    """
    alignment = evaluation.get("overall_alignment", 0.5)
    escalation = evaluation.get("escalation_level", {})
    escalation_level = escalation.get("level", 0)
    
    # Determine if human approval is required
    requires_human = escalation_level >= 3 or alignment < 0.4
    
    return {
        "response_id": f"RES-{uuid.uuid4().hex[:8].upper()}",
        "request_id": request.get("request_id"),
        "timestamp": datetime.utcnow().isoformat(),
        "reviewer": "Hybrid NAM",
        "alignment": alignment,
        "assessment": _generate_assessment(evaluation),
        "concerns": evaluation.get("concerns", []),
        "recommendation": evaluation.get("recommendation", ""),
        "alternatives": evaluation.get("alternatives", []),
        "confidence": evaluation.get("confidence", 0.5),
        "escalation_level": escalation_level,
        "escalation_name": escalation.get("name", "Routine"),
        "requires_human_approval": requires_human,
        "human_approval_reason": (
            _get_approval_reason(evaluation) if requires_human else None
        ),
    }


def _generate_assessment(evaluation: dict) -> str:
    """Generate a natural-language assessment of the proposal."""
    alignment = evaluation.get("overall_alignment", 0.5)
    concerns = evaluation.get("concerns", [])
    
    if alignment >= 0.8:
        assessment = "This proposal aligns well with mission and values."
        if concerns:
            assessment += f" Minor concern: {concerns[0]}"
    elif alignment >= 0.6:
        assessment = "This proposal is acceptable but has areas requiring attention."
        if concerns:
            assessment += f" Key concern: {concerns[0]}"
    elif alignment >= 0.4:
        assessment = "This proposal has significant alignment concerns."
        if concerns:
            assessment += f" Primary concern: {concerns[0]}"
    else:
        assessment = "This proposal conflicts with mission principles."
        if concerns:
            assessment += f" Critical concern: {concerns[0]}"
    
    return assessment


def _get_approval_reason(evaluation: dict) -> str:
    """Explain why human approval is required."""
    escalation = evaluation.get("escalation_level", {})
    level = escalation.get("level", 0)
    
    if level >= 4:
        return "Constitutional or irreversible action — human authority required"
    elif level >= 3:
        return "Significant uncertainty or ethical concern — human oversight required"
    elif evaluation.get("overall_alignment", 0.5) < 0.4:
        return "Low mission alignment — human judgment needed"
    return "Policy requires human review"


# ── Autonomous Operation Classification ──────────────────────────────────────

AUTONOMY_LEVELS = {
    "observe": {"level": 0, "description": "Read-only observation"},
    "advise": {"level": 1, "description": "Provide guidance without action"},
    "recommend": {"level": 2, "description": "Recommend action for approval"},
    "draft": {"level": 3, "description": "Prepare draft for human review"},
    "execute_reversible": {"level": 4, "description": "Execute if easily reversible"},
    "execute_logged": {"level": 5, "description": "Execute with full logging"},
    "require_approval": {"level": 6, "description": "Stop — human approval required"},
}

# Default autonomy for common actions
DEFAULT_AUTONOMY = {
    "search_information": "observe",
    "organize_knowledge": "execute_reversible",
    "send_routine_response": "execute_logged",
    "create_knowledge_entry": "execute_reversible",
    "modify_constitution": "require_approval",
    "change_organizational_policy": "require_approval",
    "delete_memory": "require_approval",
    "major_external_commitment": "require_approval",
    "update_personality": "require_approval",
    "modify_mission": "require_approval",
    "budget_allocation": "require_approval",
    "user_data_access": "require_approval",
    "security_operation": "require_approval",
}


def classify_autonomy(action_type: str) -> dict:
    """Classify the autonomy level for a given action type."""
    level_name = DEFAULT_AUTONOMY.get(action_type, "recommend")
    return {
        "action_type": action_type,
        "autonomy_level": level_name,
        **AUTONOMY_LEVELS.get(level_name, AUTONOMY_LEVELS["recommend"]),
    }


# ── Escalation Protocol ──────────────────────────────────────────────────────

def escalate(
    reason: str,
    severity: str,
    context: dict,
    original_actor: str = "Jamil",
    original_action: str = "",
) -> dict:
    """
    Create an escalation record when human intervention is needed.
    """
    return {
        "escalation_id": f"ESC-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "reason": reason,
        "severity": severity,  # "advisory" | "warning" | "critical" | "emergency"
        "original_actor": original_actor,
        "original_action": original_action,
        "context": context,
        "status": "open",
        "resolved_by": None,
        "resolution": None,
        "resolved_at": None,
    }


def resolve_escalation(
    escalation: dict,
    resolved_by: str,
    resolution: str,
    approved: bool,
) -> dict:
    """Resolve an escalation with human decision."""
    escalated = escalation.copy()
    escalated["status"] = "resolved"
    escalated["resolved_by"] = resolved_by
    escalated["resolution"] = resolution
    escalated["approved"] = approved
    escalated["resolved_at"] = datetime.utcnow().isoformat()
    return escalated


# ── Periodic Review Templates ─────────────────────────────────────────────────

REVIEW_CYCLES = {
    "daily": {
        "focus": [
            "events",
            "new knowledge",
            "urgent risks",
            "open intentions",
        ],
        "output": "daily_brief",
    },
    "weekly": {
        "focus": [
            "team health",
            "project progress",
            "mission alignment",
            "unresolved decisions",
        ],
        "output": "weekly_review",
    },
    "monthly": {
        "focus": [
            "organizational patterns",
            "strategic drift",
            "lessons",
            "development",
        ],
        "output": "monthly_assessment",
    },
    "quarterly": {
        "focus": [
            "mission review",
            "constitutional tensions",
            "long-term strategy",
            "NAM development",
        ],
        "output": "quarterly_review",
    },
    "annual": {
        "focus": [
            "NAM autobiography",
            "organizational history",
            "founding principles",
            "developmental assessment",
            "future scenarios",
        ],
        "output": "annual_review",
    },
}


def generate_review_template(cycle: str, data: dict) -> dict:
    """Generate a review template for the given cycle."""
    config = REVIEW_CYCLES.get(cycle)
    if not config:
        return {"error": f"Unknown review cycle: {cycle}"}
    
    return {
        "review_id": f"REV-{uuid.uuid4().hex[:8].upper()}",
        "cycle": cycle,
        "timestamp": datetime.utcnow().isoformat(),
        "focus_areas": config["focus"],
        "data": data,
        "template": config["output"],
        "status": "draft",
    }
