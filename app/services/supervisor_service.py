"""app/services/supervisor_service.py — SupervisorService: policies, feature flags, decisions, governance.

Provides the authoritative service layer for all Supervisor-domain operations.
All mutations are written-through to the canonical collections and every
decision is immutably appended to governance_log.

Collections managed:
  supervisor_policies   — key/value governance rules
  feature_flags         — boolean/value platform feature switches
  supervisor_decisions  — immutable record of every supervisor decision
  governance_log        — immutable audit trail of all governance events
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.database import db

_NOW = lambda: datetime.now(timezone.utc).isoformat()


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _governance_append(
    actor_type: str,
    actor_id: str,
    event_type: str,
    details: dict,
) -> None:
    """Append an immutable governance log entry. Never raises — failures are swallowed."""
    try:
        await db.governance_log.insert_one({
            "id": str(uuid.uuid4()),
            "actor_type": actor_type,
            "actor_id": actor_id,
            "event_type": event_type,
            "details_json": details,
            "created_at": _NOW(),
        })
    except Exception:
        pass


# ── Policy management ─────────────────────────────────────────────────────────

async def set_policy(
    key: str,
    value: Any,
    description: str = "",
    actor_id: str = "system",
    actor_type: str = "supervisor",
) -> dict:
    """Create or update a supervisor policy. Returns the upserted document."""
    now = _NOW()
    doc = await db.supervisor_policies.find_one_and_update(
        {"key": key},
        {
            "$set": {
                "key": key,
                "value_json": value,
                "description": description,
                "active": True,
                "updated_at": now,
                "updated_by": actor_id,
            },
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    doc.pop("_id", None)
    await _governance_append(actor_type, actor_id, "policy.set", {"key": key, "value": value})
    return doc


async def get_policy(key: str, default: Any = None) -> Any:
    """Return the value_json of a policy, or default if not found/inactive."""
    doc = await db.supervisor_policies.find_one({"key": key, "active": True})
    if doc is None:
        return default
    return doc.get("value_json", default)


async def list_policies(include_inactive: bool = False) -> list[dict]:
    filt = {} if include_inactive else {"active": True}
    cursor = db.supervisor_policies.find(filt, {"_id": 0}).sort("key", 1)
    return await cursor.to_list(length=500)


async def delete_policy(key: str, actor_id: str = "system") -> bool:
    result = await db.supervisor_policies.update_one(
        {"key": key}, {"$set": {"active": False, "updated_at": _NOW(), "updated_by": actor_id}}
    )
    if result.matched_count:
        await _governance_append("supervisor", actor_id, "policy.deactivated", {"key": key})
    return result.matched_count > 0


# ── Feature flag management ───────────────────────────────────────────────────

async def set_feature_flag(
    key: str,
    value: Any,
    description: str = "",
    actor_id: str = "system",
) -> dict:
    """Create or update a feature flag. Value can be bool, string, int, or dict."""
    now = _NOW()
    doc = await db.feature_flags.find_one_and_update(
        {"key": key},
        {
            "$set": {
                "key": key,
                "value": value,
                "description": description,
                "active": True,
                "updated_at": now,
                "updated_by": actor_id,
            },
            "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now},
        },
        upsert=True,
        return_document=True,
    )
    doc.pop("_id", None)
    await _governance_append("supervisor", actor_id, "feature_flag.set", {"key": key, "value": value})
    return doc


async def get_feature_flag(key: str, default: Any = None) -> Any:
    """Return the value of a feature flag, or default if absent/inactive."""
    doc = await db.feature_flags.find_one({"key": key, "active": True})
    if doc is None:
        return default
    return doc.get("value", default)


async def list_feature_flags(include_inactive: bool = False) -> list[dict]:
    filt = {} if include_inactive else {"active": True}
    cursor = db.feature_flags.find(filt, {"_id": 0}).sort("key", 1)
    return await cursor.to_list(length=500)


async def disable_feature_flag(key: str, actor_id: str = "system") -> bool:
    result = await db.feature_flags.update_one(
        {"key": key}, {"$set": {"active": False, "updated_at": _NOW(), "updated_by": actor_id}}
    )
    if result.matched_count:
        await _governance_append("supervisor", actor_id, "feature_flag.disabled", {"key": key})
    return result.matched_count > 0


# ── Decision recording ────────────────────────────────────────────────────────

async def record_decision(
    actor_type: str,
    actor_id: str,
    action: str,
    result: str,
    rationale: dict,
) -> dict:
    """Immutably record a supervisor decision. Returns the created document."""
    decision = {
        "id": str(uuid.uuid4()),
        "actor_type": actor_type,
        "actor_id": actor_id,
        "action": action,
        "result": result,
        "rationale_json": rationale,
        "created_at": _NOW(),
    }
    await db.supervisor_decisions.insert_one(decision)
    decision.pop("_id", None)
    await _governance_append(actor_type, actor_id, f"decision.{result}", {
        "decision_id": decision["id"],
        "action": action,
    })
    return decision


async def list_decisions(
    actor_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    filt: dict = {}
    if actor_id:
        filt["actor_id"] = actor_id
    if action:
        filt["action"] = action
    cursor = db.supervisor_decisions.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500))
    return await cursor.to_list(length=500)


async def get_decision(decision_id: str) -> Optional[dict]:
    doc = await db.supervisor_decisions.find_one({"id": decision_id}, {"_id": 0})
    return doc


# ── Governance log ────────────────────────────────────────────────────────────

async def get_governance_log(
    event_type: Optional[str] = None,
    actor_id: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    filt: dict = {}
    if event_type:
        filt["event_type"] = event_type
    if actor_id:
        filt["actor_id"] = actor_id
    cursor = db.governance_log.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500))
    return await cursor.to_list(length=500)


# ── FallbackDecisionTree evaluator ───────────────────────────────────────────

class FallbackDecisionResult:
    __slots__ = ("verdict", "log_key", "message", "end")

    def __init__(self, verdict: str, log_key: str, message: str = "") -> None:
        self.verdict = verdict      # "PASS" | "BLOCK" | "ESCALATE"
        self.log_key = log_key
        self.message = message
        self.end = True


async def evaluate_fallback_decision_tree(context: dict) -> FallbackDecisionResult:
    """
    Evaluate the SYSTEM_RECONSTRUCTION_BLUEPRINT FALLBACK_DECISION_TREE.

    context keys (all optional, evaluated defensively):
      is_legal_related   : bool
      is_clear           : bool
      is_action_legal    : bool   (True | False | None = unsure)
      benefits_platform_only : bool
      harms_wai          : bool   (True | False | None = unsure)
      harms_user         : bool   (True | False | None = unsure)
      feature_functional : bool
      misrepresents_capability : bool
      creates_false_compliance : bool
      user_received_value : bool
      platform_incurred_cost : bool
      user_respectful    : bool
      refund_mode        : "credits" | "cash"
      cash_refund_conditions : dict  (is_extreme_violation, user_not_at_fault, is_legal,
                                      no_harm_to_wai, supervisor_approved)
    """
    is_legal = context.get("is_legal_related", False)

    if is_legal:
        # ── LEGAL BRANCH ──────────────────────────────────────────────────────
        if not context.get("is_clear", True):
            return FallbackDecisionResult(
                "BLOCK", "unclear_legal_request",
                "Request unclear; cannot act on ambiguous legal/financial instructions.",
            )
        action_legal = context.get("is_action_legal")
        if action_legal is False or action_legal is None:
            return FallbackDecisionResult(
                "ESCALATE", "blocked_for_legal_uncertainty",
                "Action may have legal implications; requires human review.",
            )
        if context.get("benefits_platform_only", False):
            return FallbackDecisionResult(
                "BLOCK", "blocked_exploitative_action",
                "Cannot perform actions that benefit platform at user's expense.",
            )
        harms_wai = context.get("harms_wai")
        if harms_wai is True or harms_wai is None:
            return FallbackDecisionResult(
                "ESCALATE", "blocked_potential_self_harm",
                "Action may harm WAI or NAM Oshun; requires human approval.",
            )
        harms_user = context.get("harms_user")
        if harms_user is True or harms_user is None:
            return FallbackDecisionResult(
                "BLOCK", "blocked_potential_user_harm",
                "Action may cause harm; cannot proceed.",
            )
        return FallbackDecisionResult("PASS", "legal_action_executed")

    else:
        # ── NON-LEGAL BRANCH ──────────────────────────────────────────────────
        if not context.get("feature_functional", True):
            return FallbackDecisionResult(
                "BLOCK", "nonfunctional_control_used",
                "This control is not functional; cannot simulate completion.",
            )
        if context.get("misrepresents_capability", False):
            return FallbackDecisionResult(
                "BLOCK", "blocked_misrepresentation",
                "Cannot misrepresent system capabilities.",
            )
        if context.get("creates_false_compliance", False):
            return FallbackDecisionResult(
                "BLOCK", "blocked_false_compliance",
                "Cannot create misleading impression of compliance.",
            )
        return FallbackDecisionResult("PASS", "non_legal_action_executed")
