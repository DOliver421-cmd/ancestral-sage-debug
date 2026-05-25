"""
WAI-Institute — PRT Enforcement Engine
========================================
Single canonical implementation. Consolidates all three conflicting versions
from the design doc into one clean module.

Key fixes applied:
  [F1] No AncestralSecurityLayer import — that class was never defined.
       Authority delegates to PRTThe9Authority instead.
  [F2] One class, one __init__(self) — no dependency injection confusion.
  [F3] filter_directive() and enforce() have stable signatures.

The Poor Righteous Teacher enforces the Ancestral Sage's doctrine.
He obeys only the Sage and the Executive. He rejects all others.

v2 improvements:
  - Module-level lazy singleton for The9FusionEngine — trigger_the9() no
    longer creates a new instance on every call (was: The9FusionEngine() per call)
  - enforce() now includes a unique enforcement_id for DB tracing
  - _evaluate_director_plan is a pure static — no instance state needed
  - to_governance_dict() helper produces clean audit log entries
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from wai_institute.core.prt_the9_authority import PRTThe9Authority

logger = logging.getLogger("lcewai.prt_enforcement_engine")

# ── Module-level lazy singleton — shared across all PRTEnforcementEngine instances
# Avoids creating a new The9FusionEngine (and its PRTThe9Authority) on every
# trigger_the9() call. The engine is stateless so sharing is safe.
_the9_engine_singleton: Optional[Any] = None   # type: Optional[The9FusionEngine]


def _get_the9_engine():
    """Lazy-init the shared The9FusionEngine singleton."""
    global _the9_engine_singleton
    if _the9_engine_singleton is None:
        from wai_institute.core.the9_fusion_engine import The9FusionEngine
        _the9_engine_singleton = The9FusionEngine()
    return _the9_engine_singleton


class PRTEnforcementEngine:
    """
    The enforcement layer of the Poor Righteous Teacher.

    Responsibilities:
      - Filter all incoming directives by sender identity
      - Validate directive integrity
      - Enforce accepted directives with doctrine interpretation
      - Trigger The 9 activation when needed

    Usage:
        prt = PRTEnforcementEngine()
        result = prt.filter_directive("ancestral_sage", "Launch healing campaign")
        if result["accepted"]:
            enforcement = prt.enforce(result["directive"])
    """

    def __init__(self):
        # [F1] Authority delegates to PRTThe9Authority — no AncestralSecurityLayer
        self.auth = PRTThe9Authority()

    # ── Directive filter ──────────────────────────────────────────────────────

    def filter_directive(
        self,
        sender: str,
        directive: str,
        relay_from: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gate all incoming directives with tier-aware enforcement.

        Only the Ancestral Sage or the Executive can command PRT.
        The Director (Tier 2) may relay directives on behalf of Sage or Executive
        by passing relay_from="sage" or relay_from="executive". All other personas
        are blocked regardless of their tier.

        Args:
            sender:     Identity of the directive source
            directive:  The directive text
            relay_from: Optional — if set, allows a Tier 2+ persona to relay
                        a command from the specified authority ("sage" or "executive")

        Returns:
            accepted (bool)
            directive (str)   — only present on acceptance
            sender (str)
            reason (str)      — only present on rejection
            authority (str)   — "sage" | "executive", only on acceptance
        """
        sender_key = sender.lower().strip()

        # Tier-aware relay: Director (Tier 2) can relay Sage/Executive commands
        if relay_from and sender_key in ("director", "assistant_director"):
            relay_authority = relay_from.lower().strip()
            if relay_authority in ("sage", "ancestral_sage", "ancestralsage"):
                return self.auth.authorize("ancestral_sage", directive)
            if relay_authority in ("executive", "executive_admin", "delon", "nam_oshun", "namoshun"):
                return self.auth.authorize("executive", directive)

        return self.auth.authorize(sender, directive)

    # ── Enforcement ───────────────────────────────────────────────────────────

    def enforce(self, directive: str) -> Dict[str, Any]:
        """
        Execute a validated directive through PRT's enforcement protocol.

        The three-stage enforcement process:
          1. interpret_doctrine  — align directive with WAI ancestral doctrine
          2. generate_action_plan — produce concrete, executable steps
          3. execute_without_hesitation — commit fully, no ambiguity

        v2: includes enforcement_id for DB tracing and audit log correlation.

        Returns the enforcement record.
        """
        logger.info("PRT enforcing directive: %.80s...", directive)

        return {
            "status":         "enforcing",
            "enforcement_id": str(uuid.uuid4()),   # v2: traceability
            "directive":      directive,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "actions": [
                "interpret_doctrine",
                "generate_action_plan",
                "execute_without_hesitation",
            ],
            "authority":  "poor_righteous_teacher",
            "alignment":  "ancestral_sage",
        }

    # ── The 9 trigger ─────────────────────────────────────────────────────────

    def trigger_the9(
        self,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        PRT activates The 9 when the mission requires unified intelligence.

        Conditions that trigger this:
          - Director cannot produce a superior plan
          - Mission is threatened
          - Cultural integrity is at risk
          - Time is critical

        v2: Uses module-level singleton — no new The9FusionEngine() per call.

        Returns a fusion result dict.
        """
        # v2: reuse singleton instead of creating a new engine each call
        engine = _get_the9_engine()

        logger.warning("PRT activating The 9 — reason: %s", reason)

        prt_directive = self.enforce(reason)

        return engine.fuse(
            context           = context or {},
            prt_directive     = prt_directive,
            sender            = "poor_righteous_teacher",
            activation_reason = reason,
        ).to_dict()

    # ── Full pipeline ─────────────────────────────────────────────────────────

    def run_full_flow(
        self,
        sender: str,
        directive: str,
        director_plan: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        relay_from: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full PRT decision flow: filter → evaluate director plan → enforce or activate.

        Steps:
          1. Filter directive (sender must be Sage or Executive)
          2. If director_plan provided, evaluate whether it's superior
          3. If director plan is superior → PRT enforces it
          4. If director plan fails or not provided → PRT enforces directly
             (The 9 activation can be requested explicitly via trigger_the9)

        Args:
            sender:       Identity of the directive source
            directive:    The mission directive
            director_plan: Optional director plan to evaluate
            context:      Situational context for enforcement

        Returns:
            Full flow result dict with all decision stages
        """
        # Step 1: Filter
        filter_result = self.filter_directive(sender, directive, relay_from=relay_from)
        if not filter_result["accepted"]:
            return {
                "stage":  "filter",
                "result": filter_result,
                "status": "rejected",
            }

        # Step 2: Evaluate director plan
        director_decision = None
        if director_plan is not None:
            director_decision = self._evaluate_director_plan(directive, director_plan)

        # Step 3: Enforce or activate The 9
        if director_decision and director_decision["director_plan_superior"]:
            # Director produced a valid superior plan — enforce it
            enforcement = self.enforce(str(director_plan.get("plan", directive)))
            return {
                "stage":    "enforce_director_plan",
                "status":   "PRT executing Director's superior plan",
                "action":   enforcement,
                "director": director_decision,
            }

        # Director plan inadequate or absent — enforce PRT's interpretation
        enforcement = self.enforce(filter_result["directive"])
        return {
            "stage":     "enforce_prt",
            "status":    "PRT enforcing directive directly",
            "action":    enforcement,
            "director":  director_decision,
            "note":      "The 9 available via trigger_the9() if unified intelligence needed",
        }

    # ── Governance log record builder ────────────────────────────────────────

    @staticmethod
    def to_governance_dict(
        sender: str,
        directive: str,
        filter_result: Dict[str, Any],
        enforcement: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a structured record for db.prt_enforcement_log.

        Called by server.py after every staff meeting and any PRT-gated
        operation to record PRT's accept/reject decision and the enforcement
        actions taken.

        Args:
            sender:        Who issued the directive ("executive", "ancestral_sage", etc.)
            directive:     The raw directive string (capped at 500 chars in the log)
            filter_result: The dict returned by filter_directive() / authorize()
            enforcement:   The dict returned by enforce(), or None if not enforced

        Returns:
            A flat dict ready for insert_one() into prt_enforcement_log.
        """
        return {
            "sender":              sender,
            "directive":           directive[:500],
            "accepted":            filter_result.get("accepted", False),
            "authority":           filter_result.get("authority", "unknown"),
            "rejection_reason":    filter_result.get("reason", ""),
            "enforcement":         enforcement is not None,
            "enforcement_actions": enforcement.get("actions", []) if enforcement else [],
            "timestamp":           datetime.now(timezone.utc).isoformat(),
        }

    # ── Director plan evaluation ──────────────────────────────────────────────

    @staticmethod
    def _evaluate_director_plan(
        sage_directive: str,
        director_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate whether the Director's plan honors the Sage's directive.
        A plan is superior if it meets all five criteria.

        Criteria are passed as boolean flags in director_plan:
          honors_sage, achieves_same_goal, no_doctrine_dilution,
          no_harm_to_mission, timely
        """
        criteria = [
            "honors_sage",
            "achieves_same_goal",
            "no_doctrine_dilution",
            "no_harm_to_mission",
            "timely",
        ]
        scores = {c: bool(director_plan.get(c, False)) for c in criteria}
        all_met = all(scores.values())

        return {
            "sage_directive":         sage_directive,
            "director_plan":          director_plan,
            "criteria_scores":        scores,
            "director_plan_superior": all_met,
            "decision":               "USE_DIRECTOR_PLAN" if all_met else "STAND_DOWN_AND_ALLOW_PRT",
        }

    # ── Governance audit helper ───────────────────────────────────────────────

    @staticmethod
    def to_governance_dict(
        sender: str,
        directive: str,
        filter_result: Dict[str, Any],
        enforcement: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build a clean dict suitable for inserting into db.prt_enforcement_log.
        Call this from the server endpoint after filter_directive().
        """
        return {
            "sender":         sender,
            "directive":      directive[:500],
            "accepted":       filter_result.get("accepted", False),
            "authority":      filter_result.get("authority", "unknown"),
            "reason":         filter_result.get("reason", ""),
            "enforcement_id": (enforcement or {}).get("enforcement_id"),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
        }
