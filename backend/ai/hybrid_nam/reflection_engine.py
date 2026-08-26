"""
Reflection Engine — Hybrid NAM Outcome Learning

Per specification §24: After significant events, NAM must ask:
- WHAT HAPPENED?
- WHAT DID NAM EXPECT?
- WHAT ACTUALLY HAPPENED?
- WHY WAS THERE A DIFFERENCE?
- WHAT DID NAM LEARN?
- SHOULD ITS STRATEGY CHANGE?
- SHOULD ITS KNOWLEDGE CHANGE?
- SHOULD ITS PERSONALITY MODEL CHANGE?

Reflection creates candidate lessons.
Lessons require appropriate validation before becoming constitutional principles.
"""

import json
import uuid
from datetime import datetime
from typing import Optional


# ── Reflection Trigger Criteria ───────────────────────────────────────────────

def should_reflect(event: dict) -> bool:
    """Determine if an event warrants reflection."""
    importance = event.get("importance", 0.5)
    unexpected = event.get("unexpected", False)
    decision_outcome = event.get("has_decision_outcome", False)
    user_feedback = event.get("has_user_feedback", False)
    
    # High importance always reflects
    if importance > 0.7:
        return True
    
    # Unexpected events always reflect
    if unexpected:
        return True
    
    # Decision outcomes always reflect
    if decision_outcome:
        return True
    
    # Significant user feedback
    if user_feedback and importance > 0.4:
        return True
    
    return False


# ── Reflection Structure ──────────────────────────────────────────────────────

def create_reflection(
    event: dict,
    expectation: str,
    reality: str,
    participants: Optional[list[str]] = None,
) -> dict:
    """
    Create a structured reflection record.
    """
    reflection_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
    
    # Analyze the gap between expectation and reality
    gap_analysis = _analyze_gap(expectation, reality)
    
    # Generate candidate lessons
    candidate_lessons = _generate_lessons(event, expectation, reality, gap_analysis)
    
    # Determine if strategy or knowledge should change
    strategy_change = _assess_strategy_change(gap_analysis)
    knowledge_change = _assess_knowledge_change(gap_analysis)
    personality_change = _assess_personality_change(gap_analysis)
    
    return {
        "reflection_id": reflection_id,
        "timestamp": datetime.utcnow().isoformat(),
        "event": {
            "type": event.get("type", "unknown"),
            "description": event.get("description", ""),
            "importance": event.get("importance", 0.5),
        },
        "what_happened": event.get("description", ""),
        "what_was_expected": expectation,
        "what_actually_happened": reality,
        "gap_analysis": gap_analysis,
        "candidate_lessons": candidate_lessons,
        "strategy_change_recommended": strategy_change,
        "knowledge_change_recommended": knowledge_change,
        "personality_change_recommended": personality_change,
        "participants": participants or [],
        "status": "candidate",  # candidate → reviewed → approved → integrated
        "lesson_integrated": False,
    }


# ── Gap Analysis ──────────────────────────────────────────────────────────────

def _analyze_gap(expectation: str, reality: str) -> dict:
    """Analyze the nature and magnitude of the gap."""
    exp_words = set(expectation.lower().split())
    real_words = set(reality.lower().split())
    
    common = exp_words & real_words
    unique_to_expectation = exp_words - real_words
    unique_to_reality = real_words - exp_words
    
    # Simple overlap metric
    total = len(exp_words | real_words) or 1
    overlap = len(common) / total
    
    if overlap > 0.7:
        gap_type = "minor_deviation"
        gap_magnitude = "low"
    elif overlap > 0.4:
        gap_type = "moderate_difference"
        gap_magnitude = "moderate"
    else:
        gap_type = "significant_divergence"
        gap_magnitude = "high"
    
    return {
        "gap_type": gap_type,
        "gap_magnitude": gap_magnitude,
        "overlap_score": round(overlap, 3),
        "unique_to_expectation": list(unique_to_expectation)[:5],
        "unique_to_reality": list(unique_to_reality)[:5],
        "interpretation": _interpret_gap(gap_type, unique_to_expectation, unique_to_reality),
    }


def _interpret_gap(
    gap_type: str, expectation_words: set, reality_words: set
) -> str:
    """Provide a human-readable interpretation of the gap."""
    if gap_type == "minor_deviation":
        return "Outcome largely aligned with expectations. Minor adjustments may suffice."
    elif gap_type == "moderate_difference":
        return (
            "Notable differences between expected and actual outcomes. "
            "Review assumptions and consider adjusting approach."
        )
    else:
        return (
            "Significant divergence from expectations. "
            "Fundamental assumptions may need revision."
        )


# ── Lesson Generation ────────────────────────────────────────────────────────

def _generate_lessons(
    event: dict,
    expectation: str,
    reality: str,
    gap_analysis: dict,
) -> list[dict]:
    """Generate candidate lessons from the reflection."""
    lessons = []
    
    magnitude = gap_analysis.get("gap_magnitude", "low")
    gap_type = gap_analysis.get("gap_type", "")
    
    if magnitude == "high":
        lessons.append({
            "lesson": f"Significant divergence in {event.get('type', 'operation')} — core assumptions need review",
            "category": "strategic",
            "confidence": 0.6,
            "requires_approval": True,
        })
    
    if "unexpected" in gap_analysis.get("interpretation", "").lower():
        lessons.append({
            "lesson": "Expected outcomes may not account for current context",
            "category": "predictive",
            "confidence": 0.5,
            "requires_approval": True,
        })
    
    # Pattern-based lessons
    if gap_type == "moderate_difference":
        unique_reality = gap_analysis.get("unique_to_reality", [])
        if unique_reality:
            lessons.append({
                "lesson": f"Reality introduced factors not in expectation: {', '.join(unique_reality[:3])}",
                "category": "contextual",
                "confidence": 0.5,
                "requires_approval": False,
            })
    
    return lessons


# ── Change Assessment ─────────────────────────────────────────────────────────

def _assess_strategy_change(gap_analysis: dict) -> bool:
    """Assess whether strategy should change based on gap analysis."""
    magnitude = gap_analysis.get("gap_magnitude", "low")
    return magnitude in ("moderate", "high")


def _assess_knowledge_change(gap_analysis: dict) -> bool:
    """Assess whether knowledge base should be updated."""
    magnitude = gap_analysis.get("gap_magnitude", "low")
    return magnitude == "high"


def _assess_personality_change(gap_analysis: dict) -> bool:
    """
    Assess whether personality model should change.
    This should be VERY rare — personality is stable.
    """
    magnitude = gap_analysis.get("gap_magnitude", "low")
    overlap = gap_analysis.get("overlap_score", 1.0)
    # Only on very significant divergence with very low overlap
    return magnitude == "high" and overlap < 0.2


# ── Reflection Integration ───────────────────────────────────────────────────

def integrate_lesson(reflection: dict, lesson_index: int = 0) -> dict:
    """
    Mark a lesson as approved and ready for integration.
    Per specification: lessons require validation before becoming principles.
    """
    lessons = reflection.get("candidate_lessons", [])
    if lesson_index < len(lessons):
        lessons[lesson_index]["status"] = "approved"
        lessons[lesson_index]["approved_at"] = datetime.utcnow().isoformat()
        reflection["lesson_integrated"] = True
        reflection["status"] = "approved"
    return reflection


def generate_constitutional_tension(reflections: list[dict]) -> dict:
    """
    Analyze multiple reflections for tensions in NAM's constitution.
    Per specification §40 (quarterly review): detect constitutional tensions.
    """
    if len(reflections) < 3:
        return {
            "tensions_detected": False,
            "message": "Insufficient reflections for tension analysis",
        }
    
    # Find recurring patterns
    strategy_changes = sum(
        1 for r in reflections if r.get("strategy_change_recommended")
    )
    knowledge_changes = sum(
        1 for r in reflections if r.get("knowledge_change_recommended")
    )
    personality_changes = sum(
        1 for r in reflections if r.get("personality_change_recommended")
    )
    
    total = len(reflections)
    
    tensions = []
    
    if strategy_changes / total > 0.3:
        tensions.append({
            "type": "strategy_tension",
            "severity": "moderate",
            "description": f"{strategy_changes}/{total} reflections recommend strategy changes",
            "recommendation": "Review current strategy against accumulated evidence",
        })
    
    if knowledge_changes / total > 0.2:
        tensions.append({
            "type": "knowledge_tension",
            "severity": "high",
            "description": f"{knowledge_changes}/{total} reflections indicate knowledge gaps",
            "recommendation": "Knowledge base may need significant updates",
        })
    
    if personality_changes / total > 0.1:
        tensions.append({
            "type": "identity_tension",
            "severity": "critical",
            "description": f"{personality_changes}/{total} reflections suggest identity review",
            "recommendation": "Human review of NAM's developmental trajectory required",
        })
    
    return {
        "tensions_detected": len(tensions) > 0,
        "tensions": tensions,
        "total_reflections_analyzed": total,
        "analysis_timestamp": datetime.utcnow().isoformat(),
    }
