"""app/services/compliance_engine.py — ComplianceEngine with five validators.

Validators (run in sequence on every critical action):
  1. LegalityValidator       — jurisdictional / legal constraint checks
  2. EthicsValidator         — uses FallbackDecisionTree; blocks scams, misrepresentation
  3. BillingValidator        — cost+10% rule, refund modality, no overcharging
  4. PersonaScopeValidator   — persona must stay within allowed providers/capabilities
  5. ProviderUsageValidator  — rate limits, quotas, provider status

Every compliance evaluation is persisted to db.compliance_events.
Critical actions that are blocked or escalated also create supervisor_decisions entries.

Usage:
    result = await ComplianceEngine.evaluate(action, context)
    if result.verdict != "PASS":
        raise HTTPException(403, result.message)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.database import db

_NOW = lambda: datetime.now(timezone.utc).isoformat()


# ── Verdict enum ──────────────────────────────────────────────────────────────

class Verdict(str, Enum):
    PASS     = "PASS"
    BLOCK    = "BLOCK"
    ESCALATE = "ESCALATE"


class ComplianceResult:
    __slots__ = ("verdict", "validator", "log_key", "message", "decision_id")

    def __init__(
        self,
        verdict: Verdict,
        validator: str,
        log_key: str,
        message: str = "",
        decision_id: Optional[str] = None,
    ) -> None:
        self.verdict     = verdict
        self.validator   = validator
        self.log_key     = log_key
        self.message     = message
        self.decision_id = decision_id

    @property
    def passed(self) -> bool:
        return self.verdict == Verdict.PASS


# ── Persistence helpers ───────────────────────────────────────────────────────

async def _log_compliance_event(
    action: str,
    actor_type: str,
    actor_id: str,
    verdict: Verdict,
    rationale: dict,
    linked_decision_id: Optional[str] = None,
) -> str:
    event_id = str(uuid.uuid4())
    try:
        await db.compliance_events.insert_one({
            "id": event_id,
            "action": action,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "decision": verdict.value,
            "rationale_json": rationale,
            "linked_supervisor_decision_id": linked_decision_id,
            "created_at": _NOW(),
        })
    except Exception:
        pass
    return event_id


async def _create_supervisor_decision(
    action: str,
    actor_type: str,
    actor_id: str,
    result: str,
    rationale: dict,
) -> str:
    from app.services.supervisor_service import record_decision
    doc = await record_decision(actor_type, actor_id, action, result, rationale)
    return doc["id"]


# ── Individual validators ─────────────────────────────────────────────────────

class LegalityValidator:
    """Check jurisdictional and legal constraints."""

    async def validate(self, action: str, context: dict) -> Optional[ComplianceResult]:
        # Sensitive action categories that require legality confirmation
        legal_sensitive = context.get("is_legal_related", False)
        if not legal_sensitive:
            return None  # not in scope

        if not context.get("is_clear", True):
            return ComplianceResult(
                Verdict.BLOCK, "LegalityValidator", "unclear_legal_request",
                "Action unclear; cannot act on ambiguous legal/financial instructions.",
            )
        action_legal = context.get("is_action_legal")
        if action_legal is False or action_legal is None:
            return ComplianceResult(
                Verdict.ESCALATE, "LegalityValidator", "blocked_for_legal_uncertainty",
                "Action may have legal implications; requires human review.",
            )
        return None  # PASS


class EthicsValidator:
    """Enforce ethical rules using the FallbackDecisionTree."""

    async def validate(self, action: str, context: dict) -> Optional[ComplianceResult]:
        from app.services.supervisor_service import evaluate_fallback_decision_tree
        result = await evaluate_fallback_decision_tree(context)
        if result.verdict == "PASS":
            return None
        verdict = Verdict.BLOCK if result.verdict == "BLOCK" else Verdict.ESCALATE
        return ComplianceResult(
            verdict, "EthicsValidator", result.log_key, result.message,
        )


class BillingValidator:
    """Enforce billing integrity: cost+10% rule, refund modality, no overcharging."""

    async def validate(self, action: str, context: dict) -> Optional[ComplianceResult]:
        billing_actions = {"charge", "refund", "credit", "invoice", "billing_event"}
        if not any(ba in action for ba in billing_actions):
            return None

        # Cash refund requires all five conditions
        if "cash" in context.get("refund_mode", ""):
            conditions = context.get("cash_refund_conditions", {})
            required = [
                "is_extreme_violation",
                "user_not_at_fault",
                "is_legal",
                "no_harm_to_wai",
                "supervisor_approved",
            ]
            missing = [k for k in required if not conditions.get(k, False)]
            if missing:
                return ComplianceResult(
                    Verdict.BLOCK, "BillingValidator", "cash_refund_conditions_not_met",
                    f"Cash refund blocked — conditions not met: {', '.join(missing)}. Issue site credits instead.",
                )

        # Charge cannot exceed cost + 10% when no value was delivered
        if not context.get("user_received_value", True):
            charge = context.get("charge_amount", 0)
            cost   = context.get("platform_cost", 0)
            max_allowed = cost * 1.10
            if charge > max_allowed:
                return ComplianceResult(
                    Verdict.BLOCK, "BillingValidator", "overcharge_no_value_delivered",
                    f"Cannot charge ${charge/100:.2f} — user received no value; maximum allowed is cost+10% (${max_allowed/100:.2f}).",
                )

        # Profit/markup prohibited when no value was delivered
        if not context.get("user_received_value", True) and context.get("includes_profit", False):
            return ComplianceResult(
                Verdict.BLOCK, "BillingValidator", "profit_blocked_no_value",
                "Cannot include profit margin when user received no value.",
            )

        return None  # PASS


class PersonaScopeValidator:
    """Ensure persona only acts within its allowed providers and capabilities."""

    async def validate(self, action: str, context: dict) -> Optional[ComplianceResult]:
        persona_id = context.get("persona_id")
        if not persona_id:
            return None  # not a persona-scoped action

        provider_id = context.get("provider_id")
        capability  = context.get("capability")

        if provider_id:
            allowed_scope = await db.persona_provider_scopes.find_one({
                "persona_id": persona_id,
                "provider_id": provider_id,
                "allowed": True,
            })
            if not allowed_scope:
                return ComplianceResult(
                    Verdict.BLOCK, "PersonaScopeValidator", "persona_provider_not_allowed",
                    f"Persona '{persona_id}' is not authorized to use provider '{provider_id}'.",
                )

        if capability:
            allowed_cap = await db.persona_capabilities.find_one({
                "persona_id": persona_id,
                "capability_key": capability,
                "allowed": True,
            })
            if not allowed_cap:
                return ComplianceResult(
                    Verdict.BLOCK, "PersonaScopeValidator", "persona_capability_not_allowed",
                    f"Persona '{persona_id}' does not have capability '{capability}'.",
                )

        # Check persona-specific policies
        policy_block = await db.persona_policies.find_one({
            "persona_id": persona_id,
            "key": {"$in": [f"block_{capability}", f"block_{action}", "block_all"]},
            "active": True,
        })
        if policy_block:
            return ComplianceResult(
                Verdict.BLOCK, "PersonaScopeValidator", "persona_policy_blocked",
                f"Persona '{persona_id}' is restricted by policy: {policy_block.get('key')}.",
            )

        return None  # PASS


class ProviderUsageValidator:
    """Check provider status, rate limits, and quotas before outbound calls."""

    async def validate(self, action: str, context: dict) -> Optional[ComplianceResult]:
        provider_id = context.get("provider_id")
        if not provider_id or "provider" not in action:
            return None

        provider_doc = await db.api_providers.find_one({"id": provider_id})
        if not provider_doc:
            return ComplianceResult(
                Verdict.BLOCK, "ProviderUsageValidator", "provider_not_found",
                f"Provider '{provider_id}' is not registered.",
            )
        if provider_doc.get("status") != "active":
            status = provider_doc.get("status", "unknown")
            return ComplianceResult(
                Verdict.BLOCK, "ProviderUsageValidator", "provider_not_active",
                f"Provider '{provider_id}' is currently {status} — cannot route calls.",
            )

        # Check global supervisor policy for this provider
        from app.services.supervisor_service import get_policy
        provider_enabled = await get_policy(f"provider.{provider_id}.enabled", default=True)
        if provider_enabled is False:
            return ComplianceResult(
                Verdict.BLOCK, "ProviderUsageValidator", "provider_disabled_by_policy",
                f"Provider '{provider_id}' has been disabled by Supervisor policy.",
            )

        return None  # PASS


# ── ComplianceEngine orchestrator ─────────────────────────────────────────────

_VALIDATORS = [
    LegalityValidator(),
    EthicsValidator(),
    BillingValidator(),
    PersonaScopeValidator(),
    ProviderUsageValidator(),
]


class ComplianceEngine:
    """
    Evaluate all validators in sequence against an action + context.

    Usage:
        result = await ComplianceEngine.evaluate(
            action="billing.refund",
            actor_type="user",
            actor_id=user.id,
            context={
                "is_legal_related": True,
                "refund_mode": "cash",
                "cash_refund_conditions": {...},
                ...
            },
        )
        if not result.passed:
            raise HTTPException(403, result.message)
    """

    @staticmethod
    async def evaluate(
        action: str,
        actor_type: str,
        actor_id: str,
        context: dict,
        create_supervisor_decision: bool = True,
    ) -> ComplianceResult:
        for validator in _VALIDATORS:
            try:
                finding = await validator.validate(action, context)
            except Exception as exc:
                # Validator crash = escalate, never crash the caller silently
                finding = ComplianceResult(
                    Verdict.ESCALATE,
                    type(validator).__name__,
                    "validator_exception",
                    f"Validator {type(validator).__name__} raised: {str(exc)[:200]}",
                )

            if finding is not None and not finding.passed:
                # Record compliance event
                decision_id: Optional[str] = None
                if create_supervisor_decision and finding.verdict in (Verdict.BLOCK, Verdict.ESCALATE):
                    decision_id = await _create_supervisor_decision(
                        action, actor_type, actor_id,
                        finding.verdict.value,
                        {
                            "validator": finding.validator,
                            "log_key": finding.log_key,
                            "message": finding.message,
                            "context_summary": {
                                k: v for k, v in context.items()
                                if k not in ("cash_refund_conditions",)
                            },
                        },
                    )
                await _log_compliance_event(
                    action, actor_type, actor_id,
                    finding.verdict,
                    {"validator": finding.validator, "log_key": finding.log_key, "message": finding.message},
                    linked_decision_id=decision_id,
                )
                finding.decision_id = decision_id
                return finding

        # All validators passed
        await _log_compliance_event(
            action, actor_type, actor_id,
            Verdict.PASS,
            {"validators_run": [type(v).__name__ for v in _VALIDATORS]},
        )
        return ComplianceResult(Verdict.PASS, "ComplianceEngine", "all_validators_passed")


async def list_compliance_events(
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    verdict: Optional[str] = None,
    limit: int = 100,
) -> list[dict]:
    filt: dict = {}
    if action:
        filt["action"] = {"$regex": action, "$options": "i"}
    if actor_id:
        filt["actor_id"] = actor_id
    if verdict:
        filt["decision"] = verdict.upper()
    cursor = db.compliance_events.find(filt, {"_id": 0}).sort("created_at", -1).limit(min(limit, 500))
    return await cursor.to_list(length=500)
