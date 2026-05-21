"""
WAI-Institute HierarchyEnforcer
================================
Enforces the Director governance model:
  - Who can approve what
  - Which actions require escalation
  - Free-first policy on tools
  - Audio budget enforcement
  - Cultural alignment checks

Used by the autonomous pipeline before any publishing or major action.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.hierarchy_enforcer")

# Actions that ALWAYS require Director approval
DIRECTOR_APPROVAL_REQUIRED = {
    "system_changes",
    "persona_creation",
    "persona_retirement",
    "major_release",          # products > $99
    "budget_override",
    "new_paid_tool",
    "merge_personas",
}

# Actions Ambassador can approve without escalating
AMBASSADOR_APPROVAL_SCOPE = {
    "campaign_publish",       # products <= $99
    "persona_deployment",
    "tool_assignment",
    "content_release",
}

# Monthly audio character budget caps per persona
AUDIO_CAPS = {
    "cipher":           29_500,
    "director":         15_000,
    "ancestral_sage":   20_000,
    "revenue_director": 10_000,
    "ambassador":        5_000,
    "oracle":            3_000,
    "architect":         1_500,
}

AUDIO_SOFT_WARNING_PCT = 0.85   # warn at 85% of cap


class HierarchyEnforcer:
    """
    Governance gate for the autonomous pipeline.

    Usage:
        enforcer = HierarchyEnforcer(db)
        decision = await enforcer.check_action("cipher", "campaign_publish", {"price_cents": 1999})
        if decision["approved"]:
            ... proceed ...
    """

    def __init__(self, db=None):
        self.db = db

    # ── Action gate ───────────────────────────────────────────────────────────

    async def check_action(
        self,
        requesting_persona: str,
        action: str,
        context: dict = None,
    ) -> dict:
        """
        Check whether an action is approved.

        Returns:
            approved (bool)
            approver  ("autonomous" | "ambassador" | "director_required")
            reason    (str)
        """
        context = context or {}
        action = action.lower().strip()

        # Director-only actions
        if action in DIRECTOR_APPROVAL_REQUIRED:
            return {
                "approved":  False,
                "approver":  "director_required",
                "reason":    f"Action '{action}' requires Director approval.",
                "action":    action,
                "persona":   requesting_persona,
            }

        # High-value product publish → Director approval
        price = context.get("price_cents", 0)
        if action == "campaign_publish" and price > 9900:
            return {
                "approved":  False,
                "approver":  "director_required",
                "reason":    f"Products over $99 require Director approval. Price: ${price/100:.2f}",
                "action":    action,
                "price":     f"${price/100:.2f}",
            }

        # Ambassador-scope actions
        if action in AMBASSADOR_APPROVAL_SCOPE:
            return {
                "approved":  True,
                "approver":  "ambassador",
                "reason":    "Within Ambassador autonomous scope.",
                "action":    action,
            }

        # Default: autonomous
        return {
            "approved":  True,
            "approver":  "autonomous",
            "reason":    "Within autonomous operating parameters.",
            "action":    action,
        }

    # ── Audio budget ──────────────────────────────────────────────────────────

    async def check_audio_budget(
        self,
        persona: str,
        chars_requested: int,
    ) -> dict:
        """
        Check if a persona has budget for a TTS request.
        Reads actual usage from db.persona_tts_budgets.
        """
        cap = AUDIO_CAPS.get(persona.lower(), 5_000)
        used = 0

        if self.db is not None:
            try:
                bdoc = await self.db.persona_tts_budgets.find_one({"persona": persona})
                if bdoc:
                    used = bdoc.get("chars_used_this_month", 0)
            except Exception: pass

        remaining = cap - used
        will_exceed = (used + chars_requested) > cap
        warning = (used / max(cap, 1)) >= AUDIO_SOFT_WARNING_PCT

        return {
            "persona":          persona,
            "chars_requested":  chars_requested,
            "chars_used":       used,
            "monthly_cap":      cap,
            "remaining":        remaining,
            "approved":         not will_exceed,
            "warning":          warning,
            "pct_used":         round(used / max(cap, 1) * 100, 1),
            "status":           "HARD_CAP_REACHED" if will_exceed else ("SOFT_WARNING" if warning else "OK"),
        }

    # ── Free-first policy ─────────────────────────────────────────────────────

    def enforce_free_first(self, tool: dict) -> dict:
        """
        Check if a tool satisfies the free-first mandate.
        Returns approved=True for free tools, False for paid (requires director).
        """
        cost = tool.get("cost", 0)
        tool_name = tool.get("name", "unknown")

        if cost == 0:
            return {"approved": True, "tool": tool_name, "policy": "free_first_satisfied"}

        return {
            "approved": False,
            "tool":     tool_name,
            "cost":     cost,
            "policy":   "free_first_violated",
            "reason":   f"Tool '{tool_name}' costs ${cost}. Director approval required.",
        }

    # ── Cultural alignment check ──────────────────────────────────────────────

    def check_cultural_alignment(self, content: str, flags: list = None) -> dict:
        """
        Basic cultural alignment check.
        In production, this would call an LLM to assess content.
        For now: keyword-based flag check.
        """
        flags = flags or []
        content_lower = content.lower()

        # Hard blocks — content that violates WAI cultural values
        violations = []
        block_terms = [
            "poverty porn", "caricature", "stereotype",
            "mammy", "coon", "sambo",   # anti-Black tropes
        ]
        for term in block_terms:
            if term in content_lower:
                violations.append(term)

        if violations:
            return {
                "aligned":    False,
                "violations": violations,
                "action":     "block",
                "reason":     f"Content violates WAI cultural integrity standards: {violations}",
            }

        return {
            "aligned": True,
            "flags":   flags,
            "action":  "proceed",
        }

    # ── Revenue action approval ───────────────────────────────────────────────

    def approve_revenue_action(self, action: dict) -> dict:
        """
        Director's approval matrix for revenue actions.
        Requires: free_tool_used, revenue_potential, cultural_alignment, risk_clear
        """
        required = ["free_tool_used", "revenue_potential", "cultural_alignment", "risk_clear"]
        missing = [k for k in required if not action.get(k, False)]

        if missing:
            return {
                "approved": False,
                "missing":  missing,
                "reason":   f"Revenue action incomplete — missing: {missing}",
            }

        return {
            "approved": True,
            "reason":   "All governance requirements satisfied.",
            "action":   action,
        }

    # ── Log enforcement decision ──────────────────────────────────────────────

    async def log_decision(
        self,
        action: str,
        persona: str,
        decision: dict,
    ) -> None:
        """Persist enforcement decisions to db.governance_log for audit trail."""
        if self.db is None:
            return
        try:
            await self.db.governance_log.insert_one({
                "action":     action,
                "persona":    persona,
                "decision":   decision,
                "timestamp":  datetime.now(timezone.utc).isoformat(),
            })
        except Exception as e:
            logger.warning("HierarchyEnforcer.log_decision failed: %s", e)
