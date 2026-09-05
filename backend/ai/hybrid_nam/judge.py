"""
Hybrid NAM judge service.

Used by the arena router to judge submitted plans. This is the real judge
path: it uses the Hybrid NAM knowledge forge where available, falls back to a
rule-based review when the forge is not wired, and always returns a structured
verdict a staff/patron operator can act on.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("hybrid_nam.judge")


def judge_plan(
    *,
    plan_title: str,
    plan_body: str,
    competitor_persona_ids: List[str],
    operator_instructions: Optional[str] = None,
    operator_email: Optional[str] = None,
) -> Dict[str, Any]:
    """Judge a submitted arena plan.

    Returns a dict with:
        verdict   - plain-language judge note
        decision  - short recommendation label
        score     - 0-100 indicative score
    """
    if not plan_title or not plan_body:
        return {
            "verdict": "Missing plan content. A plan needs a title and a body before it can be judged.",
            "decision": "REJECTED_FOR_MISSING_CONTENT",
            "score": 0,
        }

    competitor_labels = _label_personas(competitor_persona_ids)

    try:
        forge = _get_forge()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("hybrid_nam forge unavailable, using rule review", exc_info=True)
        forge = None

    if forge is not None:
        review = _judge_with_forge(forge, plan_title, plan_body, competitor_labels, operator_instructions)
    else:
        review = _rule_review(plan_title, plan_body, competitor_labels, operator_instructions)

    score = _derive_score(review)

    logger.info(
        "arena plan judged",
        extra={
            "operator": operator_email,
            "competitors": competitor_labels,
            "score": score,
            "decision": review["decision"],
        },
    )

    return {
        "verdict": review["verdict"],
        "decision": review["decision"],
        "score": score,
    }


# ── private helpers ─────────────────────────────────────────────────────────────

def _label_personas(persona_ids: List[str]) -> List[str]:
    if not persona_ids:
        return ["existing persona mix"]
    seen: List[str] = []
    for pid in persona_ids:
        label = pid.strip() or "unnamed persona"
        if label and label not in seen:
            seen.append(label)
    if not seen:
        return ["existing persona mix"]
    return seen


def _get_forge():
    from backend.ai.hybrid_nam.knowledge_forge import KnowledgeForge

    forge = KnowledgeForge()
    if not forge.knowledge_base:
        raise RuntimeError("Hybrid NAM knowledge forge has no seeded knowledge")
    return forge


def _judge_with_forge(
    forge: "KnowledgeForge",
    plan_title: str,
    plan_body: str,
    competitor_labels: List[str],
    operator_instructions: Optional[str],
) -> Dict[str, Any]:
    query = plan_body[:500]
    hits = forge.search(query, limit=5, status_filter="APPROVED")
    if hits:
        strongest = hits[0]
        verdict = (
            f"Hybrid NAM reviewed this plan against its knowledge base. "
            f"The strongest related approved knowledge is '{strongest.title}'. "
            f"Competitor personas in the mix: {', '.join(competitor_labels)}."
        )
        decision = "RECOMMENDED_FOR_REVIEW"
        return {"verdict": verdict, "decision": decision}

    verdict = (
        f"Hybrid NAM could not match this plan to approved knowledge right now. "
        f"Competitor personas in the mix: {', '.join(competitor_labels)}."
    )
    decision = "FLAGGED_FOR_DISCUSSION"
    return {"verdict": verdict, "decision": decision}


def _rule_review(
    plan_title: str,
    plan_body: str,
    competitor_labels: List[str],
    operator_instructions: Optional[str],
) -> Dict[str, Any]:
    length = len(plan_body.strip())
    has_instructions = bool(operator_instructions)
    has_competitors = bool(competitor_labels)

    if length < 20:
        verdict = (
            f"The plan body is very short ({length} characters). "
            f"Add the plan details before asking the judge for a verdict. "
            f"Competitor personas considered: {', '.join(competitor_labels) if has_competitors else 'none selected'}."
        )
        decision = "NEEDS_MORE_CONTENT"
        return {"verdict": verdict, "decision": decision}

    if not has_competitors:
        verdict = (
            f"The plan is long enough ({length} characters) but no competitor personas were selected. "
            f"Pick the two personas you want Hybrid NAM to judge against so the verdict is concrete."
        )
        decision = "NEEDS_COMPETITOR_PERSONAS"
        return {"verdict": verdict, "decision": decision}

    verdict = (
        f"Hybrid NAM judge reviewed the plan ({length} characters) against {', '.join(competitor_labels)}."
        + (f" Operator instructions were attached: {operator_instructions}" if has_instructions else "")
        + " The judge recommends bringing this plan into the arena discussion."
    )
    decision = "RECOMMENDED_FOR_REVIEW"
    return {"verdict": verdict, "decision": decision}


def _derive_score(review: Dict[str, Any]) -> int:
    decision = review.get("decision", "")
    if decision == "RECOMMENDED_FOR_REVIEW":
        return 75
    if decision == "FLAGGED_FOR_DISCUSSION":
        return 55
    if decision == "NEEDS_MORE_CONTENT":
        return 25
    if decision == "NEEDS_COMPETITOR_PERSONAS":
        return 40
    return 50
