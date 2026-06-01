"""
routing.py - Director 4.0 (ADAPTED for string-based prompt system)
====================================================================
Role-based persona routing for WAI-Institute / M.O.R.E. Help Center.

ROUTING DEFAULTS (Director 4.0 chain of command):
  student / instructor  → assistant_director  (Tier 3 operations)
  admin / executive_admin → director          (Tier 2 executive authority)

OVERRIDE MECHANISM:
  Pass "force_persona" in context to bypass default routing.
  The Director can override routing when:
    - Specialized expertise is required
    - A threat is detected
    - A persona is out of mandate
    - Escalation is necessary

VALID PERSONA KEYS (as used throughout the string-based prompt system):
  director, assistant_director, ancestral_sage, savant_scholar,
  apprentice, revenue_director, wai_success_engine, product_designer,
  risk_officer, strategic_navigator, confidentiality_sentinel, elder_council

Usage:
  from ai.routing import route_request
  persona_key = route_request("student", {})
  # → "assistant_director"

  persona_key = route_request("admin", {"force_persona": "risk_officer"})
  # → "risk_officer"
"""

from typing import Dict

# All valid persona keys in the Director 4.0 ecosystem
VALID_PERSONAS = frozenset({
    "director",
    "assistant_director",
    "ancestral_sage",
    "savant_scholar",
    "apprentice",
    "revenue_director",
    "wai_success_engine",
    "product_designer",
    "risk_officer",
    "strategic_navigator",
    "confidentiality_sentinel",
    "elder_council",
})

# Role-based defaults (Director 4.0 chain of command)
ROLE_DEFAULTS: Dict[str, str] = {
    "student":         "assistant_director",
    "instructor":      "assistant_director",
    "admin":           "director",
    "executive_admin": "director",
}


def route_request(user_role: str, context: Dict) -> str:
    """
    Return the persona key that should handle this request.

    Args:
        user_role : User's assigned role string.
        context   : Dict that may contain:
                      "force_persona" — bypass default routing
                      "threat_detected" — bool; routes exec/admin to director
                      "specialist"    — specific domain needing specialist persona

    Returns:
        Persona key string (one of VALID_PERSONAS).
    """
    # Explicit Director override
    if "force_persona" in context:
        requested = context["force_persona"]
        if requested in VALID_PERSONAS:
            return requested
        # Unknown persona requested — fall through to defaults

    # Threat detected → escalate to Director regardless of role
    if context.get("threat_detected") and user_role in {"admin", "executive_admin"}:
        return "director"

    # Specialist routing (content-based)
    specialist = context.get("specialist")
    if specialist and specialist in VALID_PERSONAS:
        # Only allow specialist routing for admin+ users
        if user_role in {"admin", "executive_admin"}:
            return specialist

    # Role-based defaults
    return ROLE_DEFAULTS.get(user_role, "director")


def get_valid_personas() -> frozenset:
    """Return the complete set of valid persona keys."""
    return VALID_PERSONAS


def get_role_default(user_role: str) -> str:
    """Return the default persona key for a given role."""
    return ROLE_DEFAULTS.get(user_role, "director")
