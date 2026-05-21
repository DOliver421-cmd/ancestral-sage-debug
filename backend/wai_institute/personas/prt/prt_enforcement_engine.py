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
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from wai_institute.core.prt_the9_authority import PRTThe9Authority

logger = logging.getLogger("lcewai.prt_enforcement_engine")


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

    def filter_directive(self, sender: str, directive: str) -> Dict[str, Any]:
        """
        Gate all incoming directives.

        Only the Ancestral Sage or the Executive can command PRT.
        All other personas are blocked regardless of their tier.

        Returns:
            accepted (bool)
            directive (str)   — only present on acceptance
            sender (str)
            reason (str)      — only present on rejection
            authority (str)   — "sage" | "executive", only on acceptance
        """
        return self.auth.authorize(sender, directive)

    # ── Enforcement ───────────────────────────────────────────────────────────

    def enforce(self, directive: str) -> Dict[str, Any]:
        """
        Execute a validated directive through PRT's enforcement protocol.

        The three-stage enforcement process:
          1. interpret_doctrine  — align directive with WAI ancestral doctrine
          2. generate_action_plan — produce concrete, executable steps
          3. execute_without_hesitation — commit fully, no ambiguity

        Returns the enforcement record.
        """
        logger.info("PRT enforcing directive: %.80s...", directive)

        return {
            "status":    "enforcing",
            "directive": directive,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actions": [
                "interpret_doctrine",
                "generate_action_plan",
                "execute_without_hesitation",
            ],
            "authority": "poor_righteous_teacher",
            "alignment": "ancestral_sage",
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

        Returns a fusion request dict for The9FusionEngine.fuse().
        """
        from wai_institute.core.the9_fusion_engine import The9FusionEngine

        logger.warning("PRT activating The 9 — reason: %s", reason)

        engine = The9FusionEngine()
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
        filter_result = self.filter_directive(sender, directive)
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
