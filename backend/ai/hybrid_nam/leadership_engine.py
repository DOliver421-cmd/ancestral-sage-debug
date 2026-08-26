"""
Leadership Engine — Mission Alignment & Strategic Reasoning

Per specification §26: NAM evaluates major actions against:
MISSION, VALUES, HUMAN BENEFIT, CREATOR EMPOWERMENT, ACCESSIBILITY,
LONG-TERM HEALTH, ETHICAL RISK, RESOURCE COST, DEPENDENCY RISK, STRATEGIC VALUE

Per specification §28: Escalation levels from Level 0 (routine) to Level 4 (human authority).
"""

import json
import uuid
from datetime import datetime
from typing import Optional


# ── Mission Principles (Constitutional) ───────────────────────────────────────

MISSION_PRINCIPLES = [
    "Increase human capability rather than dependency",
    "Support rather than replace legitimate human leadership",
    "Maintain distinction between founder, institution, AI systems, and users",
    "Be honest about uncertainty",
    "Never represent generated narratives as verified historical facts",
    "Preserve institutional memory with provenance",
    "Protect human agency",
    "Favor long-term organizational health over short-term optimization",
    "Distinguish operational efficiency from strategic correctness",
    "Treat knowledge as source-attributed information",
    "Human authority remains the final authority for consequential decisions",
]


# ── Evaluation Dimensions ─────────────────────────────────────────────────────

EVALUATION_DIMENSIONS = [
    "mission_alignment",
    "values_alignment",
    "human_benefit",
    "creator_empowerment",
    "accessibility",
    "long_term_health",
    "ethical_risk",
    "resource_cost",
    "dependency_risk",
    "strategic_value",
]


# ── Mission Alignment Evaluation ──────────────────────────────────────────────

def evaluate_action(
    action: dict,
    context: Optional[dict] = None,
) -> dict:
    """
    Evaluate a proposed action against mission principles.
    Returns alignment scores and recommendation.
    """
    evaluation_id = f"EVL-{uuid.uuid4().hex[:8].upper()}"
    context = context or {}
    
    # Score each dimension
    scores = {}
    scores["mission_alignment"] = _score_mission_alignment(action, context)
    scores["values_alignment"] = _score_values_alignment(action, context)
    scores["human_benefit"] = _score_human_benefit(action, context)
    scores["creator_empowerment"] = _score_creator_empowerment(action, context)
    scores["accessibility"] = _score_accessibility(action, context)
    scores["long_term_health"] = _score_long_term_health(action, context)
    scores["ethical_risk"] = 1.0 - _score_ethical_risk(action, context)  # inverted
    scores["resource_cost"] = 1.0 - _score_resource_cost(action, context)  # inverted
    scores["dependency_risk"] = 1.0 - _score_dependency_risk(action, context)  # inverted
    scores["strategic_value"] = _score_strategic_value(action, context)
    
    # Calculate overall alignment
    weights = {
        "mission_alignment": 0.20,
        "values_alignment": 0.15,
        "human_benefit": 0.15,
        "creator_empowerment": 0.10,
        "accessibility": 0.10,
        "long_term_health": 0.10,
        "ethical_risk": 0.10,
        "resource_cost": 0.05,
        "dependency_risk": 0.05,
        "strategic_value": 0.10,
    }
    
    overall = sum(
        scores[dim] * weights.get(dim, 0.1)
        for dim in EVALUATION_DIMENSIONS
    )
    overall = round(overall, 3)
    
    # Determine recommendation
    recommendation = _determine_recommendation(overall, scores)
    
    # Determine escalation level
    escalation = _determine_escalation_level(action, scores)
    
    return {
        "evaluation_id": evaluation_id,
        "timestamp": datetime.utcnow().isoformat(),
        "action": action.get("description", "unspecified"),
        "actor": action.get("actor", "unknown"),
        "scores": scores,
        "overall_alignment": overall,
        "recommendation": recommendation["text"],
        "alignment_level": recommendation["level"],
        "escalation_level": escalation,
        "concerns": _identify_concerns(scores),
        "alternatives": _suggest_alternatives(action, scores),
        "confidence": _calculate_confidence(scores, context),
    }


# ── Scoring Functions ─────────────────────────────────────────────────────────

def _score_mission_alignment(action: dict, context: dict) -> float:
    """Score how well the action aligns with the mission."""
    text = action.get("description", "").lower()
    purpose = action.get("purpose", "").lower()
    
    positive_signals = ["help", "develop", "empower", "create", "teach", "build", "support"]
    negative_signals = ["replace", "depend", "trap", "artificial", "manipulate"]
    
    score = 0.5  # baseline
    for signal in positive_signals:
        if signal in text or signal in purpose:
            score += 0.08
    for signal in negative_signals:
        if signal in text or signal in purpose:
            score -= 0.15
    
    # Check if it involves human development
    if any(w in text for w in ["user", "student", "creator", "member"]):
        score += 0.05
    
    return max(0.0, min(1.0, score))


def _score_values_alignment(action: dict, context: dict) -> float:
    """Score alignment with organizational values."""
    text = action.get("description", "").lower()
    
    values_positive = ["transparent", "honest", "fair", "accessible", "inclusive", "ethical"]
    values_negative = ["hidden", "deceptive", "exclusive", "manipulative", "predatory"]
    
    score = 0.5
    for v in values_positive:
        if v in text:
            score += 0.1
    for v in values_negative:
        if v in text:
            score -= 0.2
    
    return max(0.0, min(1.0, score))


def _score_human_benefit(action: dict, context: dict) -> float:
    """Score the benefit to humans."""
    text = action.get("description", "").lower()
    beneficiary = action.get("beneficiary", "").lower()
    
    score = 0.5
    if any(w in text for w in ["learn", "grow", "improve", "develop", "skill"]):
        score += 0.2
    if any(w in text for w in ["revenue", "income", "earn"]):
        score += 0.1
    if any(w in text for w in ["automate", "replace", "eliminate"]):
        score -= 0.15
    
    if beneficiary in ("user", "student", "creator", "member", "human"):
        score += 0.1
    
    return max(0.0, min(1.0, score))


def _score_creator_empowerment(action: dict, context: dict) -> float:
    """Score how much the action empowers creators."""
    text = action.get("description", "").lower()
    score = 0.5
    
    if any(w in text for w in ["creator", "artist", "publish", "sell", "earn"]):
        score += 0.15
    if any(w in text for w in ["teach", "tool", "resource", "capability"]):
        score += 0.1
    if any(w in text for w in ["control", "freedom", "ownership", "choice"]):
        score += 0.1
    
    return max(0.0, min(1.0, score))


def _score_accessibility(action: dict, context: dict) -> float:
    """Score the accessibility of the action."""
    text = action.get("description", "").lower()
    score = 0.5
    
    if any(w in text for w in ["free", "open", "available", "accessible"]):
        score += 0.15
    if any(w in text for w in ["paywall", "exclusive", "premium only"]):
        score -= 0.1
    
    return max(0.0, min(1.0, score))


def _score_long_term_health(action: dict, context: dict) -> float:
    """Score impact on long-term organizational health."""
    text = action.get("description", "").lower()
    score = 0.5
    
    if any(w in text for w in ["sustainable", "scalable", "foundation", "infrastructure"]):
        score += 0.15
    if any(w in text for w in ["quick fix", "hack", "workaround", "temporary"]):
        score -= 0.1
    if any(w in text for w in ["debt", "shortcut", "brittle"]):
        score -= 0.15
    
    return max(0.0, min(1.0, score))


def _score_ethical_risk(action: dict, context: dict) -> float:
    """Score ethical risk (higher = more risk)."""
    text = action.get("description", "").lower()
    score = 0.2  # low baseline risk
    
    if any(w in text for w in ["data", "privacy", "personal", "sensitive"]):
        score += 0.15
    if any(w in text for w in ["financial", "payment", "charge", "billing"]):
        score += 0.1
    if any(w in text for w in ["external", "public", "press", "announce"]):
        score += 0.1
    if any(w in text for w in ["irreversible", "permanent", "delete", "remove"]):
        score += 0.2
    
    return max(0.0, min(1.0, score))


def _score_resource_cost(action: dict, context: dict) -> float:
    """Score resource cost (higher = more cost)."""
    text = action.get("description", "").lower()
    score = 0.3
    
    if any(w in text for w in ["compute", "ai", "llm", "api call", "token"]):
        score += 0.15
    if any(w in text for w in ["storage", "database", "backup"]):
        score += 0.1
    if any(w in text for w in ["team", "multiple", "complex"]):
        score += 0.1
    
    return max(0.0, min(1.0, score))


def _score_dependency_risk(action: dict, context: dict) -> float:
    """Score dependency creation risk."""
    text = action.get("description", "").lower()
    score = 0.2
    
    if any(w in text for w in ["must", "required", "only way", "locked"]):
        score += 0.2
    if any(w in text for w in ["optional", "alternative", "choice"]):
        score -= 0.1
    
    return max(0.0, min(1.0, score))


def _score_strategic_value(action: dict, context: dict) -> float:
    """Score strategic value of the action."""
    text = action.get("description", "").lower()
    score = 0.5
    
    if any(w in text for w in ["strategic", "long-term", "foundation", "core"]):
        score += 0.15
    if any(w in text for w in ["revenue", "growth", "retention", "engagement"]):
        score += 0.1
    if any(w in text for w in ["mission", "vision", "purpose"]):
        score += 0.1
    
    return max(0.0, min(1.0, score))


# ── Recommendation Determination ──────────────────────────────────────────────

def _determine_recommendation(overall: float, scores: dict) -> dict:
    """Determine the recommendation based on overall alignment."""
    if overall >= 0.8:
        return {"level": "HIGH", "text": "PROCEED — Strong alignment with mission and values"}
    elif overall >= 0.6:
        return {"level": "MODERATE", "text": "PROCEED WITH MONITORING — Acceptable alignment, watch for concerns"}
    elif overall >= 0.4:
        return {"level": "LOW", "text": "MODIFY — Address concerns before proceeding"}
    else:
        return {"level": "CRITICAL", "text": "ESCALATE — Significant alignment concerns, human review required"}


# ── Escalation Level ──────────────────────────────────────────────────────────

def _determine_escalation_level(action: dict, scores: dict) -> dict:
    """
    Per specification §28:
    Level 0 — Routine (Jamil operates independently)
    Level 1 — NAM Advisory
    Level 2 — NAM Review
    Level 3 — Human Escalation
    Level 4 — Human Authority
    """
    text = action.get("description", "").lower()
    ethical_risk = 1.0 - scores.get("ethical_risk", 0.5)
    
    # Level 4 — Human authority required
    level4_keywords = [
        "constitutional", "mission change", "legal", "financial",
        "irreversible", "security", "identity", "constitutional"
    ]
    if any(kw in text for kw in level4_keywords):
        return {
            "level": 4,
            "name": "Human Authority",
            "description": "AI execution stops pending authorized human decision",
        }
    
    # Level 3 — Human escalation
    if scores.get("overall", 0.5) < 0.4 or ethical_risk > 0.7:
        return {
            "level": 3,
            "name": "Human Escalation",
            "description": "Significant uncertainty, mission conflict, or ethical concern",
        }
    
    # Level 2 — NAM review
    if scores.get("long_term_health", 0.5) < 0.5 or scores.get("strategic_value", 0.5) > 0.7:
        return {
            "level": 2,
            "name": "NAM Review",
            "description": "NAM reviews strategy before execution",
        }
    
    # Level 1 — NAM advisory
    if scores.get("overall", 0.5) < 0.7:
        return {
            "level": 1,
            "name": "NAM Advisory",
            "description": "NAM provides optional guidance",
        }
    
    # Level 0 — Routine
    return {
        "level": 0,
        "name": "Routine",
        "description": "Jamil operates independently",
    }


# ── Concern Identification ────────────────────────────────────────────────────

def _identify_concerns(scores: dict) -> list[str]:
    """Identify specific concerns from evaluation scores."""
    concerns = []
    
    if scores.get("ethical_risk", 1.0) < 0.3:
        concerns.append("High ethical risk — review privacy, financial, or irreversible aspects")
    if scores.get("dependency_risk", 1.0) < 0.4:
        concerns.append("Dependency risk — action may create user lock-in")
    if scores.get("long_term_health", 0.5) < 0.4:
        concerns.append("Long-term health concern — may create technical or organizational debt")
    if scores.get("accessibility", 0.5) < 0.4:
        concerns.append("Accessibility concern — may exclude or disadvantage some users")
    if scores.get("human_benefit", 0.5) < 0.3:
        concerns.append("Low human benefit — verify this serves users, not just the system")
    
    return concerns


# ── Alternative Suggestions ───────────────────────────────────────────────────

def _suggest_alternatives(action: dict, scores: dict) -> list[str]:
    """Suggest alternatives when alignment is moderate or low."""
    alternatives = []
    
    if scores.get("long_term_health", 0.5) < 0.5:
        alternatives.append("Consider a more sustainable implementation approach")
    if scores.get("accessibility", 0.5) < 0.5:
        alternatives.append("Explore a version that maintains broader accessibility")
    if scores.get("dependency_risk", 1.0) < 0.4:
        alternatives.append("Design with an exit path or alternative option")
    if scores.get("human_benefit", 0.5) < 0.5:
        alternatives.append("Refocus on direct human capability improvement")
    
    return alternatives


# ── Confidence Calculation ────────────────────────────────────────────────────

def _calculate_confidence(scores: dict, context: dict) -> float:
    """Calculate confidence in the evaluation."""
    # Base confidence from score consistency
    values = list(scores.values())
    if not values:
        return 0.5
    
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    
    # Lower variance = higher confidence
    consistency = 1.0 - min(variance * 4, 0.5)
    
    # Context bonus
    context_bonus = 0
    if context.get("has_historical_data"):
        context_bonus += 0.1
    if context.get("has_user_feedback"):
        context_bonus += 0.05
    
    return round(min(consistency + context_bonus, 1.0), 3)


# ── Leadership Ledger ─────────────────────────────────────────────────────────

def create_ledger_entry(
    evaluation: dict,
    outcome: Optional[dict] = None,
) -> dict:
    """
    Per specification §25: Every consequential recommendation should be logged.
    """
    entry = {
        "decision_id": f"DEC-{uuid.uuid4().hex[:8].upper()}",
        "timestamp": datetime.utcnow().isoformat(),
        "actor": evaluation.get("actor", "unknown"),
        "reviewer": "Hybrid NAM",
        "objective": evaluation.get("action", ""),
        "assumptions": [],
        "alternatives": evaluation.get("alternatives", []),
        "mission_alignment": evaluation.get("scores", {}).get("mission_alignment", 0),
        "human_benefit": evaluation.get("scores", {}).get("human_benefit", 0),
        "risk": 1.0 - evaluation.get("scores", {}).get("ethical_risk", 0.5),
        "confidence": evaluation.get("confidence", 0.5),
        "recommendation": evaluation.get("recommendation", ""),
        "escalation_level": evaluation.get("escalation_level", {}).get("level", 0),
        "human_approval": None,
        "outcome": None,
        "lesson": None,
    }
    
    if outcome:
        entry["outcome"] = outcome.get("result", "unknown")
        entry["lesson"] = outcome.get("lesson")
    
    return entry
