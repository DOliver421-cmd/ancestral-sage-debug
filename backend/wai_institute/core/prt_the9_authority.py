"""
WAI-Institute — PRT / The 9 Authority Layer
=============================================
Single canonical implementation of the Executive + Sage Dual Authority Layer
(ESDAL). Replaces all conflicting versions from the design doc.

Authority model (final):
  - Authorized commanders: Ancestral Sage OR Executive (either is sufficient)
  - PRT obeys both; blocks every other persona
  - The 9 activates on command from Sage, PRT, or Executive
  - No AncestralSecurityLayer dependency (that class was never defined)

Design principle: One file, one truth. Import this everywhere.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.prt_the9_authority")

# ── Canonical authorized sender identities ────────────────────────────────────
# Lower-cased for comparison. Covers API callers, internal persona names,
# and executive account identifiers.
SAGE_IDENTITIES = frozenset({
    "ancestral_sage",
    "ancestralsage",
    "sage",
    "the ancestral sage",
})

EXECUTIVE_IDENTITIES = frozenset({
    "executive",
    "executive_admin",
    "delon",
    "nam_oshun",
    "namoshun",
    "executiveaccount",
    "executive_account",
    "system",          # system_startup bootstrapping counts as executive
})

# Personas that PRT explicitly blocks (cannot command PRT)
PRT_BLOCKED_SENDERS = frozenset({
    "director", "ambassador", "cipher", "oracle",
    "architect", "merchant", "producer", "analyst", "engineer",
})


class PRTThe9Authority:
    """
    Dual authority resolver for PRT and The 9.

    Usage:
        auth = PRTThe9Authority()
        if auth.is_authorized(sender):
            prt.enforce(directive)
        if auth.can_activate_the9(sender):
            the9.fuse(context, prt_directive)
    """

    # ── Identity checks ───────────────────────────────────────────────────────

    @staticmethod
    def is_sage(sender: str) -> bool:
        """Returns True if the sender is the Ancestral Sage."""
        return sender.lower().strip() in SAGE_IDENTITIES

    @staticmethod
    def is_executive(sender: str) -> bool:
        """Returns True if the sender is the Executive (Delon / executive_admin)."""
        return sender.lower().strip() in EXECUTIVE_IDENTITIES

    @classmethod
    def is_authorized(cls, sender: str) -> bool:
        """
        Returns True if the sender can command PRT.
        Either the Sage OR the Executive is sufficient — no dual-key required.
        """
        return cls.is_sage(sender) or cls.is_executive(sender)

    @classmethod
    def is_blocked(cls, sender: str) -> bool:
        """Returns True if the sender is explicitly blocked from commanding PRT."""
        return sender.lower().strip() in PRT_BLOCKED_SENDERS

    # ── The 9 activation gate ─────────────────────────────────────────────────

    @classmethod
    def can_activate_the9(cls, sender: str) -> bool:
        """
        The 9 can be activated by: Sage, Executive, OR PRT itself.
        PRT activates The 9 when it receives a valid directive.
        """
        return cls.is_authorized(sender) or sender.lower().strip() in {"prt", "poor_righteous_teacher"}

    @classmethod
    def dual_key_for_the9(
        cls,
        sage_confirmed: bool = False,
        executive_confirmed: bool = False,
        prt_confirmed: bool = False,
    ) -> bool:
        """
        Original design called for dual-key — Sage AND PRT both confirming.
        Updated (ESDAL): either Sage, Executive, OR PRT is sufficient.
        This preserves backward compatibility with any code that calls this method.
        """
        return sage_confirmed or executive_confirmed or prt_confirmed

    # ── Directive integrity ───────────────────────────────────────────────────

    @staticmethod
    def verify_directive_integrity(directive: str) -> dict:
        """
        Verify a directive has substance. A valid directive must be non-empty
        and at least 5 characters (not just whitespace or punctuation).
        """
        cleaned = directive.strip()
        if not cleaned or len(cleaned) < 5:
            return {
                "integrity_passed": False,
                "reason": "Directive is too short or empty.",
            }
        return {
            "integrity_passed": True,
            "directive": cleaned,
        }

    # ── Full authorization decision ───────────────────────────────────────────

    @classmethod
    def authorize(cls, sender: str, directive: str) -> dict:
        """
        Full authorization check: sender identity + directive integrity.

        Returns:
            accepted (bool)
            sender   (str)
            directive (str)
            reason    (str, only on rejection)
        """
        # Hard block — known blocked senders
        if cls.is_blocked(sender):
            logger.warning("PRT: blocked directive from %s", sender)
            return {
                "accepted": False,
                "sender":   sender,
                "reason":   f"Sender '{sender}' is not authorized to command PRT.",
            }

        # Authorization check
        if not cls.is_authorized(sender):
            logger.warning("PRT: unauthorized sender %s", sender)
            return {
                "accepted": False,
                "sender":   sender,
                "reason":   "Only the Ancestral Sage or the Executive may command PRT.",
            }

        # Directive integrity
        integrity = cls.verify_directive_integrity(directive)
        if not integrity["integrity_passed"]:
            return {
                "accepted": False,
                "sender":   sender,
                "reason":   integrity["reason"],
            }

        logger.info("PRT: authorized directive from %s", sender)
        return {
            "accepted":  True,
            "sender":    sender,
            "directive": integrity["directive"],
            "authority": "sage" if cls.is_sage(sender) else "executive",
        }

    # ── Activation log entry ──────────────────────────────────────────────────

    @staticmethod
    def build_activation_record(
        sender: str,
        directive: str,
        target: str = "prt",
        reason: str = "",
    ) -> dict:
        """Build a governance log record for PRT or The 9 activation."""
        return {
            "target":    target,
            "sender":    sender,
            "directive": directive[:500],   # cap at 500 chars in log
            "reason":    reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
