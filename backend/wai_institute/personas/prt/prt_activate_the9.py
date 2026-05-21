"""
WAI-Institute — PRT: Activate The 9
=======================================
Clean activation script. A thin wrapper around The9FusionEngine.fuse()
so callers don't need to import the engine directly.

Design doc had this as a standalone class — kept for interface compatibility.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("lcewai.prt_activate_the9")


class ActivateThe9:
    """
    PRT's activation trigger for The 9.

    Usage:
        activator = ActivateThe9()
        result = activator.run(
            reason="Director failed to produce superior plan",
            context={"brief": "healing campaign launch"},
        )
    """

    def __init__(self):
        self.status = "ready"

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
        """
        from wai_institute.core.the9_fusion_engine import The9FusionEngine

        logger.info("ActivateThe9.run — reason=%s sender=%s", reason, sender)

        engine = The9FusionEngine()
        result = engine.fuse(
            context           = context or {},
            prt_directive     = {"directive": reason, "authority": "poor_righteous_teacher"},
            sender            = sender,
            activation_reason = reason,
        )

        logger.info(
            "The 9 activation result: status=%s skills=%d",
            result.status,
            len(result.unified_skill_set),
        )

        return result.to_dict()
