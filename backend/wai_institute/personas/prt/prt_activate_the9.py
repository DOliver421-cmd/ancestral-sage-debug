"""
WAI-Institute — PRT: Activate The 9
=======================================
Clean activation script. A thin wrapper around The9FusionEngine.fuse()
so callers don't need to import the engine directly.

Design doc had this as a standalone class — kept for interface compatibility.

v2 improvements:
  - self.status tracks actual state ("ready" → "fused" | "blocked") instead
    of being permanently "ready" regardless of outcome (v1 was useless)
  - self.last_result stores the most recent activation result for inspection
  - Empty reason guard — prevents activating The 9 with no reason at all
  - Uses the module-level singleton from prt_enforcement_engine so we don't
    create yet another The9FusionEngine instance
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("lcewai.prt_activate_the9")

# Minimum reason length — prevents "activate the 9" with empty or trivial reason
_MIN_REASON_LENGTH = 3


class ActivateThe9:
    """
    PRT's activation trigger for The 9.

    Usage:
        activator = ActivateThe9()
        result = activator.run(
            reason="Director failed to produce superior plan",
            context={"brief": "healing campaign launch"},
        )
        print(activator.status)      # "fused" or "blocked"
        print(activator.last_result) # full FusionResult dict
    """

    def __init__(self):
        self.status:      str                    = "ready"
        self.last_result: Optional[Dict[str, Any]] = None

    def run(
        self,
        reason: str,
        context: Optional[Dict[str, Any]] = None,
        sender: str = "poor_righteous_teacher",
    ) -> Dict[str, Any]:
        """
        Activate The 9. Delegates to The9FusionEngine.fuse().

        Args:
            reason:  Why The 9 is being activated (activation condition key or description)
            context: Situational context dict
            sender:  Who is calling (default: PRT)

        Returns:
            FusionResult as dict — always returned, never raises

        v2: Updates self.status and self.last_result after each run.
        """
        # Input guard — don't activate with empty or trivial reason
        reason_clean = (reason or "").strip()
        if len(reason_clean) < _MIN_REASON_LENGTH:
            logger.warning("ActivateThe9: reason too short — using fallback 'prt_command'")
            reason_clean = "prt_command"

        # Use the module-level singleton — no new engine instantiation
        from wai_institute.personas.prt.prt_enforcement_engine import _get_the9_engine
        engine = _get_the9_engine()

        logger.info("ActivateThe9.run — reason=%s sender=%s", reason_clean, sender)

        result = engine.fuse(
            context           = context or {},
            prt_directive     = {"directive": reason_clean, "authority": "poor_righteous_teacher"},
            sender            = sender,
            activation_reason = reason_clean,
        )

        result_dict = result.to_dict()

        # v2: track state so callers can inspect outcome without re-running
        self.status      = result.status          # "fused" | "blocked"
        self.last_result = result_dict

        logger.info(
            "The 9 activation result: status=%s skills=%d",
            result.status,
            len(result.unified_skill_set),
        )

        return result_dict
