"""
Dream Engine — Hybrid NAM Asynchronous Synthesis Layer

Per specification §23: Dreams occur asynchronously. They are the system's
controlled offline synthesis layer where unresolved questions, memories,
patterns, possibilities, and creative associations are processed without
directly changing production behavior.

Dreams MUST NEVER directly trigger consequential actions.
Dream output enters the strategic pipeline as:
  DREAM → IDEA → HYPOTHESIS → EVALUATION → EXPERIMENT

Not: DREAM → FACT
"""

import json
import uuid
from datetime import datetime
from typing import Optional


# ── Dream Schedule ────────────────────────────────────────────────────────────

DREAM_CONFIG = {
    "frequency": "daily",       # daily / weekly / on_demand
    "max_duration_seconds": 300,  # 5 minutes async
    "input_window_hours": 24,   # look back 24 hours
    "max_outputs_per_dream": 10,
    "min_confidence_for_action": 0.7,
}


# ── Dream Input Assembly ──────────────────────────────────────────────────────

def assemble_dream_inputs(
    memories: list[dict],
    open_questions: list[str],
    creative_ideas: list[str],
    organizational_challenges: list[str],
    goals: list[dict],
    recent_events: list[dict],
    ancestral_narratives: Optional[list[dict]] = None,
) -> dict:
    """
    Assemble the inputs for a dream cycle.
    Per specification §23, inputs include recent memories,
    unresolved questions, creative ideas, organizational challenges,
    future scenarios, and ancestral narratives.
    """
    # Prioritize memories by importance and recency
    sorted_memories = sorted(
        memories,
        key=lambda m: m.get("importance", 0) * 0.7 +
                       (1.0 / max(_hours_since(m.get("created_at", "")), 1)) * 0.3,
        reverse=True,
    )[:20]
    
    return {
        "recent_memories": sorted_memories,
        "open_questions": open_questions[:10],
        "creative_ideas": creative_ideas[:10],
        "organizational_challenges": organizational_challenges[:5],
        "current_goals": goals[:5],
        "recent_events": recent_events[:15],
        "ancestral_narratives": (ancestral_narratives or [])[:5],
        "assembled_at": datetime.utcnow().isoformat(),
    }


# ── Dream Generation ─────────────────────────────────────────────────────────

def generate_dream(inputs: dict) -> dict:
    """
    Generate a dream from assembled inputs.
    
    In production, this would call the LLM with a dream-specific prompt.
    For the proof of concept, we generate structured dream artifacts
    from the input patterns.
    """
    dream_id = f"DR-{uuid.uuid4().hex[:8].upper()}"
    
    # Extract themes from inputs
    themes = _extract_themes(inputs)
    
    # Generate symbols from patterns
    symbols = _generate_symbols(inputs, themes)
    
    # Find associations between memories and ideas
    associations = _find_associations(inputs)
    
    # Generate creative possibilities
    creative_candidates = _generate_possibilities(inputs, themes, associations)
    
    # Generate questions that emerged
    emergent_questions = _generate_questions(inputs, themes)
    
    # Generate candidate insights
    candidate_insights = _generate_insights(inputs, associations)
    
    # Generate action recommendations (non-binding)
    action_recommendations = _generate_recommendations(
        candidate_insights, inputs.get("current_goals", [])
    )
    
    return {
        "dream_id": dream_id,
        "ontology": "synthetic",  # ALWAYS synthetic
        "timestamp": datetime.utcnow().isoformat(),
        "theme": themes[0] if themes else "general_synthesis",
        "themes": themes,
        "symbols": symbols,
        "associated_memories": [m.get("memory_id") for m in inputs.get("recent_memories", [])[:5]],
        "associations": associations,
        "possible_interpretations": [],
        "creative_candidates": creative_candidates,
        "emergent_questions": emergent_questions,
        "candidate_insights": candidate_insights,
        "action_recommendations": action_recommendations,
        "inputs_summary": {
            "memory_count": len(inputs.get("recent_memories", [])),
            "question_count": len(inputs.get("open_questions", [])),
            "idea_count": len(inputs.get("creative_ideas", [])),
            "challenge_count": len(inputs.get("organizational_challenges", [])),
            "goal_count": len(inputs.get("current_goals", [])),
        },
    }


# ── Theme Extraction ─────────────────────────────────────────────────────────

THEME_SIGNALS = {
    "growth": ["learn", "develop", "improve", "grow", "skill", "progress"],
    "connection": ["team", "collaborate", "relationship", "community", "partner"],
    "creation": ["create", "build", "design", "write", "compose", "produce"],
    "mission": ["mission", "purpose", "vision", "goal", "impact"],
    "challenge": ["problem", "difficulty", "obstacle", "block", "fail"],
    "discovery": ["new", "discover", "explore", "investigate", "research"],
    "reflection": ["review", "evaluate", "assess", "reflect", "consider"],
    "transition": ["change", "evolve", "shift", "transform", "transition"],
}


def _extract_themes(inputs: dict) -> list[str]:
    """Extract dominant themes from dream inputs."""
    all_text = " ".join([
        m.get("content", "") for m in inputs.get("recent_memories", [])
    ] + inputs.get("open_questions", []) +
      inputs.get("creative_ideas", []) +
      inputs.get("organizational_challenges", []))
    
    all_text = all_text.lower()
    
    theme_scores = {}
    for theme, signals in THEME_SIGNALS.items():
        score = sum(1 for s in signals if s in all_text)
        if score > 0:
            theme_scores[theme] = score
    
    ranked = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
    return [t for t, _ in ranked[:3]]


# ── Symbol Generation ────────────────────────────────────────────────────────

SYMBOL_MAP = {
    "growth": ["seed", "root", "branch", "spring"],
    "connection": ["bridge", "thread", "circle", "weave"],
    "creation": ["forge", "canvas", "blueprint", "flame"],
    "mission": ["compass", "beacon", "path", "horizon"],
    "challenge": ["crucible", "threshold", "mountain", "current"],
    "discovery": ["key", "window", "map", "star"],
    "reflection": ["mirror", "pool", "echo", "shadow"],
    "transition": ["door", "river", "dawn", "chrysalis"],
}


def _generate_symbols(inputs: dict, themes: list[str]) -> list[dict]:
    """Generate symbolic imagery from themes and input patterns."""
    symbols = []
    for theme in themes:
        theme_symbols = SYMBOL_MAP.get(theme, [])
        if theme_symbols:
            symbols.append({
                "symbol": theme_symbols[0],
                "theme": theme,
                "ontology": "synthetic",
                "note": "Metaphorical — not literal",
            })
    return symbols


# ── Association Finding ───────────────────────────────────────────────────────

def _find_associations(inputs: dict) -> list[dict]:
    """Find non-obvious connections between memories, ideas, and challenges."""
    associations = []
    memories = inputs.get("recent_memories", [])
    ideas = inputs.get("creative_ideas", [])
    challenges = inputs.get("organizational_challenges", [])
    
    # Connect ideas to challenges
    for idea in ideas:
        for challenge in challenges:
            idea_words = set(idea.lower().split())
            challenge_words = set(challenge.lower().split())
            overlap = idea_words & challenge_words
            if overlap and len(overlap) >= 1:
                associations.append({
                    "type": "idea_to_challenge",
                    "from": idea,
                    "to": challenge,
                    "connection": list(overlap),
                    "strength": len(overlap) / max(len(idea_words), 1),
                })
    
    # Connect memories to goals
    for memory in memories[:5]:
        mem_content = memory.get("content", "").lower()
        for goal in inputs.get("current_goals", []):
            goal_text = goal.get("objective", "").lower()
            goal_words = set(goal_text.split()) - {"the", "a", "an", "to", "of", "and", "in"}
            if any(w in mem_content for w in goal_words if len(w) > 3):
                associations.append({
                    "type": "memory_to_goal",
                    "memory_id": memory.get("memory_id"),
                    "goal": goal.get("objective", ""),
                    "strength": 0.5,
                })
    
    return associations[:10]


# ── Possibility Generation ───────────────────────────────────────────────────

def _generate_possibilities(
    inputs: dict, themes: list[str], associations: list[dict]
) -> list[dict]:
    """Generate creative possibilities from dream synthesis."""
    possibilities = []
    
    # From associations
    for assoc in associations[:3]:
        if assoc["type"] == "idea_to_challenge":
            possibilities.append({
                "possibility": f"Apply '{assoc['from']}' to address '{assoc['to']}'",
                "source": "association",
                "confidence": 0.4,
                "ontology": "synthetic",
            })
    
    # From themes and goals
    for theme in themes[:2]:
        for goal in inputs.get("current_goals", [])[:2]:
            possibilities.append({
                "possibility": f"Explore {theme}-oriented approach to: {goal.get('objective', '')}",
                "source": "theme_goal_synthesis",
                "confidence": 0.3,
                "ontology": "synthetic",
            })
    
    return possibilities[:DREAM_CONFIG["max_outputs_per_dream"]]


# ── Question Generation ───────────────────────────────────────────────────────

def _generate_questions(inputs: dict, themes: list[str]) -> list[str]:
    """Generate emergent questions from dream synthesis."""
    questions = []
    
    for theme in themes:
        questions.append(f"What would happen if we prioritized {theme} more intentionally?")
    
    for challenge in inputs.get("organizational_challenges", [])[:2]:
        questions.append(f"What underlying assumption might be wrong about: {challenge}?")
    
    if inputs.get("open_questions"):
        # Connect open questions
        q1 = inputs["open_questions"][0]
        q2 = inputs["open_questions"][1] if len(inputs["open_questions"]) > 1 else ""
        if q2:
            questions.append(f"Are '{q1}' and '{q2}' actually the same question?")
    
    return questions[:5]


# ── Insight Generation ───────────────────────────────────────────────────────

def _generate_insights(inputs: dict, associations: list[dict]) -> list[dict]:
    """Generate candidate insights from dream synthesis."""
    insights = []
    
    # Pattern-based insights
    memories = inputs.get("recent_memories", [])
    if len(memories) > 5:
        insights.append({
            "insight": f"Recent activity spans {len(memories)} events — patterns may be emerging",
            "basis": "volume_analysis",
            "confidence": 0.5,
            "status": "candidate",
        })
    
    # Association-based insights
    for assoc in associations[:2]:
        insights.append({
            "insight": f"Connection detected: {assoc.get('type', '')}",
            "basis": "association_detection",
            "confidence": assoc.get("strength", 0.3),
            "status": "candidate",
        })
    
    return insights


# ── Recommendation Generation ────────────────────────────────────────────────

def _generate_recommendations(
    insights: list[dict], goals: list[dict]
) -> list[dict]:
    """Generate non-binding action recommendations from insights."""
    recommendations = []
    
    for insight in insights:
        if insight.get("confidence", 0) >= DREAM_CONFIG["min_confidence_for_action"]:
            recommendations.append({
                "recommendation": f"Investigate: {insight.get('insight', '')}",
                "basis": insight.get("basis", ""),
                "confidence": insight.get("confidence", 0),
                "requires_approval": True,
                "ontology": "synthetic",
            })
    
    return recommendations


# ── Dream Evaluation ──────────────────────────────────────────────────────────

def evaluate_dream_outcome(dream: dict, reality: dict) -> dict:
    """
    After a dream's recommendations are evaluated against reality,
    record the outcome for NAM's developmental learning.
    """
    predictions = dream.get("candidate_insights", [])
    actual = reality.get("actual_outcomes", [])
    
    accurate = 0
    total = max(len(predictions), 1)
    
    for pred in predictions:
        for outcome in actual:
            if any(
                word in outcome.lower()
                for word in pred.get("insight", "").lower().split()
                if len(word) > 3
            ):
                accurate += 1
                break
    
    return {
        "dream_id": dream.get("dream_id"),
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "predictions_made": len(predictions),
        "outcomes_observed": len(actual),
        "accuracy": round(accurate / total, 3),
        "lesson": (
            "Dream synthesis produced partially accurate predictions"
            if 0 < accurate < total
            else "Dream synthesis needs recalibration"
            if accurate == 0
            else "Dream synthesis aligned with reality"
        ),
    }


# ── Utility ───────────────────────────────────────────────────────────────────

def _hours_since(iso_timestamp: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return (datetime.utcnow() - dt).total_seconds() / 3600
    except (ValueError, TypeError):
        return 1.0
