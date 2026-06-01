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

v2 improvements:
  - _UNIFIED_SKILL_SET pre-computed at module load — fuse() no longer
    rebuilds the set union on every activation (was O(n) per call)
  - Persona capability values are tuples (immutable) — can't be mutated
    by callers accidentally corrupting the global capability map
  - FusionResult carries both activation_code (raw key) and activation_reason
    (human text) — makes MongoDB filtering on codes possible
  - The9FusionEngine exposes get_activation_conditions() static method
"""

import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from wai_institute.core.prt_the9_authority import PRTThe9Authority

logger = logging.getLogger("lcewai.the9_fusion_engine")

# ── The 9 persona capability map ──────────────────────────────────────────────
# Values are TUPLES — immutable so callers cannot accidentally mutate the
# global capability map (was mutable lists in v1).
# When fused, all capabilities are available as a unified skill set.

THE_9_PERSONA_CAPABILITIES: Dict[str, Tuple[str, ...]] = {
    "director":   ("governance", "risk_management", "strategy", "persona_oversight"),
    "ambassador": ("coordination", "execution", "timing", "campaign_orchestration"),
    "cipher":     ("creativity", "performance", "virality", "synthesis_protocol"),
    "oracle":     ("foresight", "sentiment_mapping", "cultural_timing", "trend_analysis"),
    "architect":  ("visual_intelligence", "brand_identity", "aesthetic_design"),
    "merchant":   ("revenue_logic", "offer_design", "pricing_strategy"),
    "producer":   ("distribution", "scheduling", "publishing_pipeline"),
    "analyst":    ("data_insights", "metrics_analysis", "pattern_recognition"),
    "engineer":   ("systems_integration", "technical_reasoning", "logic_architecture"),
}

# ── Pre-computed at module load — not rebuilt on every fuse() call ────────────
# v1 did `set(); for skills in THE_9...: set.update(skills)` inside fuse().
# That's O(n) work repeated on every activation. The capability map never
# changes at runtime, so computing this once is correct and faster.
_UNIFIED_SKILL_SET: List[str] = sorted({
    skill
    for skills in THE_9_PERSONA_CAPABILITIES.values()
    for skill in skills
})

# Activation condition codes
ACTIVATION_CONDITIONS: Dict[str, str] = {
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

    v2: activation_code stores the raw key ("prt_command") for DB filtering.
        activation_reason stores the human-readable expansion.
        Both are present so dashboards can display human text and queries
        can filter on stable codes.
    """
    status:            str                  # "fused" | "blocked"
    activated_by:      str                  # sender who triggered fusion
    activation_reason: str                  # human-readable reason text
    activation_code:   str                  = ""   # raw condition key (new in v2)
    unified_skill_set: List[str]            = field(default_factory=list)
    persona_map:       Dict[str, Any]       = field(default_factory=dict)
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
            skills = result.unified_skill_set   # pre-computed, not rebuilt
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
        verification: Optional[Dict[str, str]] = None,
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
        now = datetime.now(timezone.utc).isoformat()

        # Identity verification (optional but enforced when provided)
        if verification:
            expected_roles = {
                "sage": "ancestral_sage",
                "executive": "executive",
                "prt": "poor_righteous_teacher",
            }
            claimed_role = verification.get("sender_role", "").lower().strip()
            auth_token = verification.get("auth_token", "").strip()
            expected_sender = expected_roles.get(claimed_role, "")
            if not expected_sender:
                logger.warning("The 9: unknown sender_role '%s' in verification", claimed_role)
                return FusionResult(
                    status="blocked",
                    activated_by=sender,
                    activation_code=activation_reason,
                    activation_reason=ACTIVATION_CONDITIONS.get(activation_reason, activation_reason),
                    error=f"Unknown sender_role '{claimed_role}' in verification. Must be one of: sage, executive, prt.",
                    timestamp=now,
                )
            if sender.lower().strip() != expected_sender:
                logger.warning("The 9: sender '%s' does not match verification role '%s'", sender, claimed_role)
                return FusionResult(
                    status="blocked",
                    activated_by=sender,
                    activation_code=activation_reason,
                    activation_reason=ACTIVATION_CONDITIONS.get(activation_reason, activation_reason),
                    error=f"Sender '{sender}' does not match verified role '{claimed_role}'.",
                    timestamp=now,
                )

        # Authorization check
        if not self.auth.can_activate_the9(sender):
            logger.warning("The 9: blocked activation attempt from %s", sender)
            return FusionResult(
                status            = "blocked",
                activated_by      = sender,
                activation_code   = activation_reason,
                activation_reason = ACTIVATION_CONDITIONS.get(activation_reason, activation_reason),
                error             = f"Sender '{sender}' is not authorized to activate The 9.",
                timestamp         = now,
            )

        # Build synthesis brief from context
        synthesis = self._build_synthesis_brief(context, prt_directive, activation_reason)

        logger.info(
            "The 9 activated — sender=%s code=%s skills=%d",
            sender, activation_reason, len(_UNIFIED_SKILL_SET),
        )

        return FusionResult(
            status            = "fused",
            activated_by      = sender,
            activation_code   = activation_reason,
            # Human-readable text for display; activation_code used for filtering
            activation_reason = ACTIVATION_CONDITIONS.get(activation_reason, activation_reason),
            unified_skill_set = _UNIFIED_SKILL_SET,   # v2: pre-computed, not rebuilt
            persona_map       = {k: list(v) for k, v in THE_9_PERSONA_CAPABILITIES.items()},
            synthesis_brief   = synthesis,
            mode              = "unified_mind",
            timestamp         = now,
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
            verification      = request.get("verification"),
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
                parts.append(f"Mission brief: {str(brief)[:200]}")
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
        return list(THE_9_PERSONA_CAPABILITIES.get(persona_name.lower(), ()))

    @staticmethod
    def get_all_capabilities() -> List[str]:
        """
        Get the full unified skill set across all 9 personas.
        v2: Returns the pre-computed module-level list — no set rebuild.
        """
        return _UNIFIED_SKILL_SET[:]   # return a copy to prevent external mutation

    @staticmethod
    def get_activation_conditions() -> Dict[str, str]:
        """Return the full map of condition codes to human-readable descriptions."""
        return dict(ACTIVATION_CONDITIONS)
