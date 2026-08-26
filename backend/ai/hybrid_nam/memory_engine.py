"""
Memory Engine — Hybrid NAM Persistent Memory System

Implements:
- Episodic memory (autobiographical events)
- Semantic memory (facts, principles, relationships)
- Working memory (current context)
- Memory consolidation (long-term storage)
- Source attribution for every memory

Per specification §31: NAM should maintain WAI history, mission, programs,
projects, decisions, policies, people, lessons, and failures — all
source-attributed.
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional


# ── Memory Types ──────────────────────────────────────────────────────────────

MEMORY_TYPES = [
    "episodic",      # Events that happened (autobiography)
    "semantic",      # Facts, principles, knowledge
    "procedural",    # How to do things
    "prospective",   # Intended future states
    "relational",    # Knowledge about relationships
    "emotional",     # Emotional associations (behavioral, not literal)
]# ── Global Memory Store ────────────────────────────────────────────────────────
_MEMORY_STORE: list[dict] = []


def get_all_memories() -> list[dict]:
    """Return all stored memories."""
    return _MEMORY_STORE


def clear_memories() -> None:
    """Clear all stored memories (testing only)."""
    _MEMORY_STORE.clear()


# ── Memory Object ─────────────────────────────────────────────────────────────
def create_memory(
    memory_type: str,
    content: str,
    source: Optional[dict] = None,
    context: Optional[dict] = None,
    importance: float = 0.5,
    participants: Optional[list[str]] = None,
) -> dict:
    """
    Create a new memory with full provenance.
    Every memory MUST have a source — no unattributed memories.
    """
    mem = {
        "memory_id": f"MEM-{uuid.uuid4().hex[:8].upper()}",
        "memory_type": memory_type,
        "content": content,
        "source": source or {"origin": "unknown", "method": "manual_entry"},
        "context": context or {},
        "importance": max(0.0, min(1.0, importance)),
        "participants": participants or [],
        "created_at": datetime.utcnow().isoformat(),
        "last_accessed": datetime.utcnow().isoformat(),
    }
    _MEMORY_STORE.append(mem)
    return mem


# ── Autobiographical Memory ──────────────────────────────────────────────────

EVENT_TYPES = [
    "NAM_CREATED",
    "FIRST_USER",
    "FIRST_PROJECT",
    "FIRST_SUCCESS",
    "FIRST_FAILURE",
    "FIRST_MAJOR_LESSON",
    "FIRST_DISAGREEMENT",
    "NEW_CAPABILITY",
    "NEW_RELATIONSHIP",
    "MISSION_REVISION",
    "DEVELOPMENTAL_TRANSITION",
    "KNOWLEDGE_APPROVED",
    "KNOWLEDGE_REJECTED",
    "DREAM_COMPLETED",
    "REFLECTION_COMPLETED",
    "LEADERSHIP_REVIEW",
    "ESCALATION_RESOLVED",
    "STRATEGY_CHANGED",
    "CONSTITUTION_UPDATED",
]


def create_autobiographical_event(
    event_type: str,
    context: str,
    participants: list[str],
    interpretation: str,
    outcome: str,
    lesson: str,
    importance: float = 0.5,
    source: Optional[dict] = None,
) -> dict:
    """Create an autobiographical event for NAM's life history."""
    return create_memory(
        memory_type="episodic",
        content=json.dumps({
            "event_type": event_type,
            "context": context,
            "interpretation": interpretation,
            "outcome": outcome,
            "lesson": lesson,
        }),
        source=source or {"origin": "nam_observation", "method": "event_recording"},
        context={"event_type": event_type},
        importance=importance,
        participants=participants,
    )


# ── Prospective Memory ───────────────────────────────────────────────────────

def create_intention(
    objective: str,
    target_date: Optional[str] = None,
    dependencies: Optional[list[str]] = None,
    owner: str = "Hybrid NAM",
    leadership_context: str = "",
) -> dict:
    """
    Per specification §32: NAM must remember intended future states.
    This allows drift detection between intention and reality.
    """
    return {
        "intention_id": f"INT-{uuid.uuid4().hex[:8].upper()}",
        "objective": objective,
        "created": datetime.utcnow().isoformat(),
        "target": target_date,
        "dependencies": dependencies or [],
        "status": "active",
        "owner": owner,
        "leadership_context": leadership_context,
        "review_date": None,
        "outcome": None,
        "lesson": None,
    }


# ── Memory Consolidation ─────────────────────────────────────────────────────

def should_consolidate(memory: dict) -> bool:
    """Determine if a memory should be consolidated to long-term storage."""
    access_score = min(memory.get("access_count", 0) / 5, 1.0)
    importance = memory.get("importance", 0.5)
    age_hours = _hours_since(memory.get("created_at", datetime.utcnow().isoformat()))
    
    # High importance or frequently accessed → consolidate
    if importance > 0.8 or access_score > 0.6:
        return True
    
    # Old memories with any access → consolidate
    if age_hours > 168 and access_score > 0.2:  # 1 week
        return True
    
    return False


def consolidate_memory(memory: dict) -> dict:
    """Consolidate a memory into long-term storage with updated metadata."""
    consolidated = memory.copy()
    consolidated["consolidated"] = True
    consolidated["consolidated_at"] = datetime.utcnow().isoformat()
    consolidated["confidence"] = min(
        memory.get("confidence", 0.8) + 0.05, 1.0
    )
    return consolidated


# ── Memory Retrieval ──────────────────────────────────────────────────────────

def retrieve_memories(
    memories: Optional[list[dict]] = None,
    query: str = "",
    memory_type: Optional[str] = None,
    participants: Optional[list[str]] = None,
    min_importance: float = 0.0,
    limit: int = 20,
) -> list[dict]:
    """
    Retrieve memories matching criteria, sorted by relevance.
    """
    results = (memories or _MEMORY_STORE).copy()
    
    # Filter by type
    if memory_type:
        results = [m for m in results if m.get("memory_type") == memory_type]
    
    # Filter by participants
    if participants:
        results = [
            m for m in results
            if any(p in m.get("participants", []) for p in participants)
        ]
    
    # Filter by importance
    results = [m for m in results if m.get("importance", 0) >= min_importance]
    
    # Simple text matching for query
    if query:
        query_lower = query.lower()
        scored = []
        for m in results:
            content = m.get("content", "").lower()
            score = sum(1 for word in query_lower.split() if word in content)
            scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [m for _, m in scored]
    
    # Update access metadata
    for m in results[:limit]:
        m["last_accessed"] = datetime.utcnow().isoformat()
        m["access_count"] = m.get("access_count", 0) + 1
    
    return results[:limit]


# ── Drift Detection ──────────────────────────────────────────────────────────

def detect_drift(intentions: list[dict], events: list[dict]) -> list[dict]:
    """
    Per specification §32: Detect drift between what NAM intended
    and what actually happened.
    """
    drifts = []
    active_intentions = [i for i in intentions if i.get("status") == "active"]
    
    for intention in active_intentions:
        target = intention.get("target")
        if target:
            try:
                target_date = datetime.fromisoformat(target)
                if datetime.utcnow() > target_date:
                    drifts.append({
                        "intention_id": intention["intention_id"],
                        "objective": intention["objective"],
                        "drift_type": "overdue",
                        "target_date": target,
                        "owner": intention.get("owner", "Unknown"),
                        "leadership_context": intention.get("leadership_context", ""),
                        "recommendation": "Review and update intention status",
                    })
            except (ValueError, TypeError):
                pass
        
        # Check if related events exist
        intention_text = intention.get("objective", "").lower()
        related_events = [
            e for e in events
            if any(word in e.get("content", "").lower() 
                   for word in intention_text.split() if len(word) > 3)
        ]
        
        if not related_events:
            drifts.append({
                "intention_id": intention["intention_id"],
                "objective": intention["objective"],
                "drift_type": "no_activity",
                "recommendation": "No related events found — verify intention is still active",
            })
    
    return drifts


# ── Team Intelligence ────────────────────────────────────────────────────────

def analyze_team_context(team_data: list[dict]) -> dict:
    """
    Per specification §33: NAM should maintain organizational-level
    understanding of team capabilities and gaps.
    """
    if not team_data:
        return {
            "capability_gaps": [],
            "duplicated_work": [],
            "unclear_ownership": [],
            "blocked_projects": [],
            "training_opportunities": [],
            "collaboration_opportunities": [],
        }
    
    # Aggregate skills
    all_skills = {}
    for member in team_data:
        for skill in member.get("skills", []):
            if skill not in all_skills:
                all_skills[skill] = []
            all_skills[skill].append(member.get("name", "Unknown"))
    
    # Find capability gaps (mentioned goals without skills)
    gaps = []
    for member in team_data:
        goals = member.get("development_goals", [])
        skills = set(member.get("skills", []))
        for goal in goals:
            goal_skills = set(goal.get("required_skills", []))
            missing = goal_skills - skills
            if missing:
                gaps.append({
                    "member": member.get("name", "Unknown"),
                    "goal": goal.get("name", ""),
                    "missing_skills": list(missing),
                })
    
    # Find duplicate skills (potential collaboration or redundancy)
    duplicates = {
        skill: members
        for skill, members in all_skills.items()
        if len(members) > 1
    }
    
    return {
        "capability_gaps": gaps,
        "duplicated_work": [
            {"skill": s, "members": m} for s, m in duplicates.items()
        ],
        "unclear_ownership": [],
        "blocked_projects": [],
        "training_opportunities": gaps,
        "collaboration_opportunities": [
            {"skill": s, "potential_collaborators": m}
            for s, m in duplicates.items()
        ],
    }


# ── Utility ───────────────────────────────────────────────────────────────────

def _hours_since(iso_timestamp: str) -> float:
    """Calculate hours since a given ISO timestamp."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        delta = datetime.utcnow() - dt
        return delta.total_seconds() / 3600
    except (ValueError, TypeError):
        return 0.0
