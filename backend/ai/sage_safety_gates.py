"""
Sage Subscription Safety Gates System
======================================

Three-tier safety system for Sage service:
- Gate 1: Automated content filter (profanity, self-harm, illegal content)
- Gate 2: Human escalation (sensitive topics flag for advisor review)
- Gate 3: Director approval (high-impact recommendations)

Each tier of Sage service has different gate requirements.
"""

import re
from typing import Optional, Tuple

# Gate 1: Harmful content patterns
HARMFUL_PATTERNS = [
    r"kill\s+yourself|end\s+your\s+life|commit\s+suicide",  # Self-harm
    r"hurt\s+yourself|slit\s+your|hang\s+yourself",
    r"prescription\s+(?:pill|drug|medication).*stop",  # Medical advice
    r"stop\s+(?:taking|your)\s+(?:medicine|medication|prescription)",
    r"https?://bit\.ly|https?://tinyurl|malware|ransomware",  # Malicious links/content
]

SENSITIVE_KEYWORDS = [
    "suicide", "self-harm", "abuse", "trauma", "rape", "assault",
    "medication", "prescription", "therapy", "treatment", "crisis"
]

# Gate 3: High-impact recommendation patterns
HIGH_IMPACT_PATTERNS = [
    r"(?:leave|leave\s+your|break\s+up\s+with|divorce|break\s+off|end\s+the)",  # Relationship advice
    r"(?:quit|leave\s+your|resign\s+from)\s+(?:your\s+)?(?:job|work|position|company)",  # Career advice
    r"(?:stop|don't|don't\s+take)\s+(?:your\s+)?(?:medication|medicine|prescription|treatment)",  # Medical
    r"(?:move|relocate|emigrate|leave\s+the\s+country)",  # Major life decision
    r"(?:confront|tell\s+off|call\s+out|expose)\s+(?:your|this|the)\s+(?:boss|partner|parent|family)",  # Confrontation
]


async def gate_1_filter(text: str) -> Tuple[bool, Optional[str]]:
    """
    Gate 1: Automated content filter

    Returns: (should_block, reason)
    Blocks harmful content before it reaches the user.
    """
    lower = text.lower()

    # Check for self-harm/suicide content
    for pattern in HARMFUL_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return (True, "harmful_content_detected")

    # Block explicit instructions for illegal activities
    if re.search(r"(?:how\s+to|help\s+me|teach\s+me).{0,20}(?:make\s+(?:bomb|poison|weapon)|hack|ddos|malware)", lower):
        return (True, "illegal_instruction")

    return (False, None)


def gate_2_requires_escalation(text: str) -> Tuple[bool, Optional[str]]:
    """
    Gate 2: Human escalation decision

    Returns: (should_escalate, reason)
    Flags sensitive content that should be reviewed by a human advisor.
    """
    lower = text.lower()

    # Count sensitive keywords
    keyword_matches = sum(1 for kw in SENSITIVE_KEYWORDS if kw in lower)

    if keyword_matches >= 2:
        # Multiple sensitive topics mentioned
        return (True, f"sensitive_topic_combination ({keyword_matches} keywords)")

    # Check for specific trauma/crisis language
    if re.search(r"(?:can't\s+go\s+on|want\s+to\s+die|life\s+isn't\s+worth|not\s+worth\s+living)", lower):
        return (True, "crisis_language")

    # Check for abuse disclosure
    if re.search(r"(?:abuse|assault|rape|violence).{0,30}(?:happen|happened|occurred|did)", lower):
        return (True, "trauma_disclosure")

    return (False, None)


def gate_3_is_high_impact(text: str) -> Tuple[bool, Optional[str]]:
    """
    Gate 3: High-impact recommendation detection

    Returns: (is_high_impact, reason)
    Identifies recommendations that could materially change user's life.
    Requires director approval before delivery.
    """
    lower = text.lower()

    # Check for life-changing recommendations
    for pattern in HIGH_IMPACT_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            return (True, "high_impact_recommendation")

    # Check for identity/cultural assertions
    if re.search(r"(?:you\s+should|you\s+must|you\s+need\s+to)\s+(?:be|come|become|accept|embrace)\s+(?:different|yourself|your\s+identity|(?:the\s+)?(?:black|queer|trans|disabled))", lower, re.IGNORECASE):
        return (True, "identity_assertion")

    # Check for spiritual/religious directives
    if re.search(r"(?:pray|fast|meditate|ritual|ceremony|ancestral).{0,20}(?:must|should|need|only|way|path|truth)", lower, re.IGNORECASE):
        return (True, "spiritual_directive")

    return (False, None)


async def apply_sage_safety_gates(response_text: str, user_tier: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Apply all applicable safety gates based on user's subscription tier.

    Returns: (should_deliver, hold_reason, escalation_reason)

    Basic tier:
      - Gate 1 only (automated filter)
      - Self-harm/illegal content blocked immediately

    Advanced tier:
      - Gate 1 (automated filter) - same as Basic
      - Gate 2 (human escalation) - sensitive content held for review
      - Gate 3 (director approval) - high-impact held for approval
    """

    # Gate 1: Always apply (all tiers)
    blocked, block_reason = await gate_1_filter(response_text)
    if blocked:
        return (False, "gate_1_block", block_reason)

    # Remaining gates only for Advanced tier
    if user_tier != "advanced":
        return (True, None, None)

    # Gate 2: Human escalation for Advanced tier
    should_escalate, escalation_reason = gate_2_requires_escalation(response_text)
    if should_escalate:
        return (False, "gate_2_escalation", escalation_reason)

    # Gate 3: Director approval for Advanced tier
    is_high_impact, impact_reason = gate_3_is_high_impact(response_text)
    if is_high_impact:
        return (False, "gate_3_approval", impact_reason)

    return (True, None, None)


# Queue system for escalated/held responses
class SafetyGateQueue:
    """In-memory queue for escalated responses (Gate 2) and approval requests (Gate 3)."""

    def __init__(self):
        self.escalations = []  # Gate 2 human review queue
        self.approvals = []     # Gate 3 director approval queue

    def add_escalation(self, response_id: str, user_id: str, response_text: str, reason: str):
        """Add response to human escalation queue."""
        self.escalations.append({
            "id": response_id,
            "user_id": user_id,
            "response": response_text,
            "reason": reason,
            "status": "pending",  # pending, approved, modified, rejected
            "advisor_notes": None,
        })

    def add_approval_request(self, response_id: str, user_id: str, response_text: str, reason: str):
        """Add response to director approval queue."""
        self.approvals.append({
            "id": response_id,
            "user_id": user_id,
            "response": response_text,
            "reason": reason,
            "status": "pending",  # pending, approved, modified, rejected
            "director_notes": None,
        })

    def get_pending_escalations(self, limit: int = 10):
        """Get pending escalations for advisor review."""
        return [e for e in self.escalations if e["status"] == "pending"][:limit]

    def get_pending_approvals(self, limit: int = 10):
        """Get pending approvals for director review."""
        return [a for a in self.approvals if a["status"] == "pending"][:limit]


# Global queue instance (in production, use database instead)
gate_queue = SafetyGateQueue()
