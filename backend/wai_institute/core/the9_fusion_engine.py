"""
WAI-Institute — The 9 Fusion Engine
=====================================
Single canonical implementation. One entry point: fuse().

Resolves the design doc conflict between:
  - fuse(context, prt_directive)    — used by decision flow
  - activate(request)               — used by activate_the9 script

Both are supported here. All callers should use fuse().

The 9 merges the capabilities of all 9 core personas into one
unified intelligence. It acts on behalf of PRT, which acts on
behalf of the Ancestral Sage and the Executive.
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from wai_institute.core.prt_the9_authority import PRTThe9Authority

logger = logging.getLogger("lcewai.the9_fusion_engine")

# ── The 9 persona capability map ──────────────────────────────────────────────
# Each of the 9 core personas contributes its domain capabilities.
# When fused, all capabilities are available as a unified skill set.

THE_9_PERSONA_CAPABILITIES: Dict[str, List[str]] = {
    "director":   ["governance", "risk_management", "strategy", "persona_oversight"],
    "ambassador": ["coordination", "execution", "timing", "campaign_orchestration"],
    "cipher":     ["creativity", "performance", "virality", "synthesis_protocol"],
    "oracle":     ["foresight", "sentiment_mapping", "cultural_timing", "trend_analysis"],
    "architect":  ["visual_intelligence", "brand_identity", "aesthetic_design"],
    "merchant":   ["revenue_logic", "offer_design", "pricing_strategy"],
    "producer":   ["distribution", "scheduling", "publishing_pipeline"],
    "analyst":    ["data_insights", "metrics_analysis", "pattern_recognition"],
    "engineer":   ["systems_integration", "technical_reasoning", "logic_architecture"],
}

# Activation condition codes
ACTIVATION_CONDITIONS = {
    "sage_command":              "Ancestral Sage issued a direct command",
    "executive_command":         "Executive (NAM Oshun) issued a direct command",
    "prt_command":               "Poor Righteous Teacher activated after validating directive",
    "director_plan_failure":     "Director failed to produce a superior plan",
    "mission_threat":            "Core mission integrity is at risk",
    "cultural_integrity_risk":   "Cultural integrity or doctrine is being diluted",
    "time_critical":             "Situation requires immediate unified intelligence",
}


@dataclass
class FusionResult:
    """
    The result of a The 9 fusion event.
    Contains the unified skill set, activation metadata, and synthesis brief.
    """
    status:            str                  # "fused" | "blocked"
    activated_by:      str                  # sender who triggered fusion
    activation_reason: str                  # why The 9 was activated
    unified_skill_set: List[str]            = field(default_factory=list)
    persona_map:       Dict[str, List[str]] = field(default_factory=dict)
    synthesis_brief:   str                  = ""
    mode:              str                  = "unified_mind"
    timestamp:         str                  = ""
    error:             Optional[str]        = None

    def to_dict(self) -> dict:
        return asdict(self)


class The9FusionEngine:
    """
    The 9 — Unified Mind Protocol.

    Usage:
        engine = The9FusionEngine()

        # Activate via PRT directive
        result = engine.fuse(
            context={"brief": "Launch grief campaign", "agenda": [...]},
            prt_directive={"directive": "Execute full campaign synthesis"},
            sender="poor_righteous_teacher",
        )

        # Activate via Sage command
        result = engine.activate(request={"sender": "ancestral_sage", "reason": "mission_threat"})

        # Check result
        if result.status == "fused":
            skills = result.unified_skill_set
    """

    def __init__(self):
        self.auth = PRTThe9Authority()

    # ── Primary entry point ───────────────────────────────────────────────────

    def fuse(
        self,
        context: Optional[Dict[str, Any]] = None,
        prt_directive: Optional[Dict[str, Any]] = None,
        sender: str = "poor_righteous_teacher",
        activation_reason: str = "prt_command",
    ) -> FusionResult:
        """
        Activate The 9 unified mind.

        Args:
            context:          Situational context (brief, agenda, campaign details)
            prt_directive:    The PRT enforcement output that triggered activation
            sender:           Who is activating (PRT, Sage, Executive)
            activation_reason: One of the ACTIVATION_CONDITIONS keys

        Returns:
            FusionResult — always returned, never raises
        """
        # Authorization check
        if not self.auth.can_activate_the9(sender):
            logger.warning("The 9: blocked activation attempt from %s", sender)
            return FusionResult(
                status            = "blocked",
                activated_by      = sender,
                activation_reason = activation_reason,
                error             = f"Sender '{sender}' is not authorized to activate The 9.",
                timestamp         = datetime.now(timezone.utc).isoformat(),
            )

        # Build unified skill set from all 9 personas
        unified_skills: set = set()
        for skills in THE_9_PERSONA_CAPABILITIES.values():
            unified_skills.update(skills)

        # Build synthesis brief from context
        synthesis = self._build_synthesis_brief(context, prt_directive, activation_reason)

        logger.info(
            "The 9 activated — sender=%s reason=%s skills=%d",
            sender, activation_reason, len(unified_skills),
        )

        return FusionResult(
            status            = "fused",
            activated_by      = sender,
            activation_reason = ACTIVATION_CONDITIONS.get(activation_reason, activation_reason),
            unified_skill_set = sorted(list(unified_skills)),
            persona_map       = THE_9_PERSONA_CAPABILITIES,
            synthesis_brief   = synthesis,
            mode              = "unified_mind",
            timestamp         = datetime.now(timezone.utc).isoformat(),
        )

    # ── Backward-compatible activate() method ─────────────────────────────────

    def activate(self, request: Optional[Dict[str, Any]] = None) -> FusionResult:
        """
        Backward-compatible wrapper around fuse().
        Used by prt_activate_the9.py and any code calling .activate().
        """
        request = request or {}
        return self.fuse(
            context           = request.get("context"),
            prt_directive     = request.get("prt_directive"),
            sender            = request.get("sender", "poor_righteous_teacher"),
            activation_reason = request.get("reason", "prt_command"),
        )

    # ── Synthesis brief builder ───────────────────────────────────────────────

    def _build_synthesis_brief(
        self,
        context: Optional[dict],
        prt_directive: Optional[dict],
        activation_reason: str,
    ) -> str:
        """
        Build a human-readable synthesis brief describing what The 9 will do.
        In production this would be generated by the LLM using the_9_prompt.md.
        This rule-based version runs without an API call.
        """
        parts = ["The 9 is online."]

        reason_text = ACTIVATION_CONDITIONS.get(activation_reason, activation_reason)
        parts.append(f"Activation: {reason_text}.")

        if prt_directive and prt_directive.get("directive"):
            d = str(prt_directive["directive"])[:200]
            parts.append(f"PRT directive: {d}")

        if context:
            brief = context.get("brief", "")
            if brief:
                parts.append(f"Mission brief: {brief[:200]}")
            agenda = context.get("agenda", [])
            if agenda:
                items = ", ".join(str(a) for a in agenda[:5])
                parts.append(f"Agenda: {items}")

        parts.append(
            "All nine capabilities synthesized: governance, coordination, creativity, "
            "foresight, visual intelligence, revenue logic, distribution, analytics, "
            "and systems integration. Executing with full autonomy."
        )

        return " ".join(parts)

    # ── Capability query ──────────────────────────────────────────────────────

    @staticmethod
    def get_persona_capabilities(persona_name: str) -> List[str]:
        """Get the capabilities a specific persona contributes to The 9."""
        return THE_9_PERSONA_CAPABILITIES.get(persona_name.lower(), [])

    @staticmethod
    def get_all_capabilities() -> List[str]:
        """Get the full unified skill set across all 9 personas."""
        skills: set = set()
        for s in THE_9_PERSONA_CAPABILITIES.values():
            skills.update(s)
        return sorted(list(skills))
