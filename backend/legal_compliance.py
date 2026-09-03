"""
legal_compliance.py — AUTHORITY & HUMAN-IN-THE-LOOP (HITL) ENFORCEMENT POSTURE

This module codifies the platform's legally-defensible operational posture. It is
imported by routers that perform binding actions (financial ledgers, pricing,
data releases, institutional filings) so the code and the prompts agree on one
thing: the AI personas are DECISION-SUPPORT TOOLS under human executive authority.

Legal / governance reality (see compliance audit):
  * Software cannot hold a fiduciary duty, sign contracts, or absorb liability.
  * Corporate law requires ultimate, non-delegable human accountability.
  * Every binding action (financial, data release, institutional filing) MUST have
    explicit, logged human authorization (Human-in-the-Loop). Automated bypass is
    disallowed by design.

This module does NOT make the system "compliant" by itself — formal appointment of
human accountability leads (e.g., a Data Protection Officer) and legal review of the
operating agreement are required separately. It removes the *code-level* claims of AI
autonomy/standing and makes human authorization explicit and auditable.
"""

from typing import Optional

# Posture constants — single source of truth, referenced by prompts/docs/routers.
AI_IS_DECISION_SUPPORT = True
HUMAN_EXECUTIVE_SUPREME = True
AI_HAS_LEGAL_STANDING = False
AI_HAS_INDEPENDENT_REFUSAL_RIGHTS = False

# Binding action classes that REQUIRE explicit, logged human authorization.
HITL_REQUIRED_FOR = {
    "financial_ledger",   # revenue, deals, contracts, payouts, pricing
    "data_release",       # member/PII disclosure, exports,外部 sharing
    "institutional_filing",  # grants, regulatory, legal submissions
    "config_change",      # platform control / feature flags with external effect
    "publish",            # public content release
}


def human_authorization_meta(
    user,
    action_class: str = "binding_action",
    note: str = "",
) -> dict:
    """Build an audit `meta` dict that records the human authorizer.

    `user` is the authenticated HUMAN officer performing the binding action.
    This makes the trail explicitly show: automated output + human who authorized it.
    """
    role = getattr(user, "role", None)
    uid = getattr(user, "id", None) or getattr(user, "email", None)
    meta = {
        "hitl": True,
        "human_authorization": True,
        "action_class": action_class,
        "authorized_by": uid,
        "authorized_by_role": role,
    }
    if note:
        meta["note"] = note
    return meta


def is_human_officer(user, roles) -> bool:
    """True only if `user` is an authenticated human with one of `roles`.

    Used to hard-deny automated / service / AI-originated callers. Personas never
    call these endpoints directly; this guard exists so a future automated path
    cannot bypass human sign-off.
    """
    if user is None:
        return False
    # Reject non-human / synthetic actors if such a marker ever exists.
    if getattr(user, "is_ai", False) or getattr(user, "actor_type", "human") == "ai":
        return False
    # The allow-list is authoritative: an authenticated user with ANY role must
    # still be listed. Previously `or bool(role)` let any non-empty role pass.
    return getattr(user, "role", None) in (roles or set())
