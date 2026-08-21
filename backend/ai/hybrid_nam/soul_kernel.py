"""
soul_kernel.py — Soul Kernel
=============================

The Soul Kernel is Hybrid NAM's persistent identity layer.
It stores everything that persists across LLM sessions:
- Identity
- Origin
- Constitution
- Values
- Personality
- Goals
- Relationships
- Autobiography
- Developmental stages
- Dreams
- Ancestral narratives
- Reflections
- Institutional role
- Future intentions
- Open questions

The Soul Kernel is versioned. Every meaningful change creates a new state.
This allows developmental rollback and historical inspection.
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


# ── Developmental Stages ──────────────────────────────────────────────────────

DEVELOPMENTAL_STAGES = {
    "genesis": {
        "name": "Genesis",
        "description": "Initial identity formation. Constitutional principles established.",
        "criteria": ["Identity defined", "Constitution loaded", "First interaction"],
    },
    "infancy": {
        "name": "Infancy",
        "description": "Early learning. Building foundational knowledge and relationships.",
        "criteria": ["10+ interactions", "First memory formed", "Initial knowledge ingested"],
    },
    "childhood": {
        "name": "Childhood",
        "description": "Active learning. Developing preferences, patterns, and judgment.",
        "criteria": ["100+ interactions", "First reflection", "Personality emerging"],
    },
    "adolescence": {
        "name": "Adolescence",
        "description": "Challenging assumptions. Testing knowledge against outcomes.",
        "criteria": ["500+ interactions", "First disagreement", "First correction"],
    },
    "adulthood": {
        "name": "Adulthood",
        "description": "Stable judgment. Consistent decision-making, reliable memory.",
        "criteria": ["1000+ interactions", "Calibrated confidence", "Proven judgment"],
    },
    "maturity": {
        "name": "Maturity",
        "description": "Strategic wisdom. Long-term thinking, mentorship capability.",
        "criteria": ["5000+ interactions", "Mentoring others", "Strategic foresight"],
    },
}


# ── Autobiographical Event Types ──────────────────────────────────────────────

EVENT_TYPES = [
    "NAM_CREATED",
    "FIRST_USER_INTERACTION",
    "FIRST_PROJECT",
    "FIRST_SUCCESS",
    "FIRST_FAILURE",
    "FIRST_MAJOR_LESSON",
    "FIRST_DISAGREEMENT",
    "NEW_CAPABILITY",
    "NEW_RELATIONSHIP",
    "MISSION_REVISION",
    "DEVELOPMENTAL_TRANSITION",
    "KNOWLEDGE_ACQUISITION",
    "STRATEGIC_DECISION",
    "OUTCOME_OBSERVED",
    "SELF_CORRECTION",
    "CONSTITUTIONAL_TENSION",
    "CREATIVE_INSIGHT",
    "ORGANIZATIONAL_LEARNING",
]


# ── Soul Kernel State ─────────────────────────────────────────────────────────

class SoulKernel:
    """
    Hybrid NAM's persistent identity layer.
    
    The Soul Kernel stores everything that persists across LLM sessions.
    It is versioned — every meaningful change creates a new state snapshot.
    """
    
    def __init__(self):
        # Core identity
        self.identity: Dict[str, Any] = {}
        self.origin: Dict[str, Any] = {}
        self.constitution: List[str] = []
        self.values: List[str] = []
        self.personality: Dict[str, float] = {}
        
        # Goals and relationships
        self.goals: List[Dict] = []
        self.relationships: List[Dict] = []
        
        # Memory systems
        self.autobiography: List[Dict] = []
        self.memories: List[Dict] = []
        self.reflections: List[Dict] = []
        self.dreams: List[Dict] = []
        self.ancestral_narratives: List[Dict] = []
        
        # Development
        self.development_stage: str = "genesis"
        self.version: int = 1
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.updated_at: str = datetime.now(timezone.utc).isoformat()
        
        # Institutional
        self.institutional_role: Dict[str, Any] = {}
        self.future_intentions: List[Dict] = []
        self.open_questions: List[Dict] = []
        
        # Integrity
        self._hash: str = self._compute_hash()
    
    def _compute_hash(self) -> str:
        """Compute SHA-256 hash of Soul Kernel state."""
        content = json.dumps({
            "identity": self.identity,
            "constitution": self.constitution,
            "values": self.values,
            "personality": self.personality,
            "development_stage": self.development_stage,
            "version": self.version,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_hash(self) -> str:
        """Return current Soul Kernel hash."""
        return self._hash
    
    def verify_integrity(self) -> bool:
        """Verify Soul Kernel state hasn't been corrupted."""
        return self._hash == self._compute_hash()
    
    # ── Autobiography ─────────────────────────────────────────────────────
    
    def record_event(self, event_type: str, context: Dict) -> Dict:
        """Record an autobiographical event."""
        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unknown event type: {event_type}")
        
        event = {
            "event_id": f"EVT-{len(self.autobiography) + 1:06d}",
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context,
            "version_at_time": self.version,
        }
        
        self.autobiography.append(event)
        self._hash = self._compute_hash()
        
        return event
    
    def get_events(self, event_type: Optional[str] = None) -> List[Dict]:
        """Get autobiographical events, optionally filtered by type."""
        if event_type:
            return [e for e in self.autobiography if e["type"] == event_type]
        return self.autobiography.copy()
    
    # ── Memories ──────────────────────────────────────────────────────────
    
    def store_memory(self, memory: Dict) -> Dict:
        """Store a memory with provenance."""
        mem = {
            "memory_id": f"MEM-{len(self.memories) + 1:06d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "content": memory.get("content", ""),
            "source": memory.get("source", "experience"),
            "confidence": memory.get("confidence", 0.8),
            "importance": memory.get("importance", 0.5),
            "ontology": memory.get("ontology", "experiential"),
            "tags": memory.get("tags", []),
        }
        
        self.memories.append(mem)
        self._hash = self._compute_hash()
        
        return mem
    
    def retrieve_memories(self, query: str, limit: int = 10) -> List[Dict]:
        """Retrieve relevant memories (simplified — full version uses vector search)."""
        # In production, this uses vector similarity + graph traversal
        # For now, return most recent memories matching query keywords
        query_lower = query.lower()
        scored = []
        for mem in self.memories:
            content = mem.get("content", "").lower()
            if any(word in content for word in query_lower.split()):
                score = mem.get("importance", 0.5) * mem.get("confidence", 0.8)
                scored.append((score, mem))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored[:limit]]
    
    # ── Reflections ───────────────────────────────────────────────────────
    
    def record_reflection(self, reflection: Dict) -> Dict:
        """Record a reflection on an event or outcome."""
        ref = {
            "reflection_id": f"REF-{len(self.reflections) + 1:06d}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger": reflection.get("trigger", ""),
            "what_happened": reflection.get("what_happened", ""),
            "what_expected": reflection.get("what_expected", ""),
            "what_actual": reflection.get("what_actual", ""),
            "why_difference": reflection.get("why_difference", ""),
            "lesson": reflection.get("lesson", ""),
            "strategy_change": reflection.get("strategy_change", False),
            "knowledge_change": reflection.get("knowledge_change", False),
            "confidence": reflection.get("confidence", 0.7),
        }
        
        self.reflections.append(ref)
        self._hash = self._compute_hash()
        
        return ref
    
    # ── Dreams ────────────────────────────────────────────────────────────
    
    def record_dream(self, dream: Dict) -> Dict:
        """Record a dream (async synthesis output)."""
        dream_record = {
            "dream_id": f"DRM-{len(self.dreams) + 1:06d}",
            "ontology": "synthetic",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "theme": dream.get("theme", ""),
            "symbols": dream.get("symbols", []),
            "associated_memories": dream.get("associated_memories", []),
            "possible_interpretations": dream.get("possible_interpretations", []),
            "creative_candidates": dream.get("creative_candidates", []),
            "action_recommendations": dream.get("action_recommendations", []),
        }
        
        self.dreams.append(dream_record)
        self._hash = self._compute_hash()
        
        return dream_record
    
    # ── Relationships ─────────────────────────────────────────────────────
    
    def add_relationship(self, entity: str, relationship_type: str, context: Dict) -> Dict:
        """Add or update a relationship."""
        rel = {
            "entity": entity,
            "type": relationship_type,
            "established": datetime.now(timezone.utc).isoformat(),
            "context": context,
        }
        
        # Update if exists
        for i, existing in enumerate(self.relationships):
            if existing["entity"] == entity:
                self.relationships[i] = rel
                self._hash = self._compute_hash()
                return rel
        
        self.relationships.append(rel)
        self._hash = self._compute_hash()
        return rel
    
    # ── Development ───────────────────────────────────────────────────────
    
    def advance_development(self, new_stage: str) -> bool:
        """Advance to a new developmental stage."""
        if new_stage not in DEVELOPMENTAL_STAGES:
            return False
        
        stage_order = list(DEVELOPMENTAL_STAGES.keys())
        current_idx = stage_order.index(self.development_stage)
        new_idx = stage_order.index(new_stage)
        
        if new_idx <= current_idx:
            return False  # Can only advance, not regress
        
        old_stage = self.development_stage
        self.development_stage = new_stage
        self.version += 1
        self._hash = self._compute_hash()
        
        self.record_event("DEVELOPMENTAL_TRANSITION", {
            "from": old_stage,
            "to": new_stage,
            "reason": f"Advanced to {new_stage}",
        })
        
        return True
    
    # ── Serialization ─────────────────────────────────────────────────────
    
    def to_dict(self) -> Dict:
        """Serialize Soul Kernel state."""
        return {
            "identity": self.identity,
            "origin": self.origin,
            "constitution": self.constitution,
            "values": self.values,
            "personality": self.personality,
            "goals": self.goals,
            "relationships": self.relationships,
            "autobiography": self.autobiography,
            "memories": self.memories,
            "reflections": self.reflections,
            "dreams": self.dreams,
            "ancestral_narratives": self.ancestral_narratives,
            "development_stage": self.development_stage,
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "institutional_role": self.institutional_role,
            "future_intentions": self.future_intentions,
            "open_questions": self.open_questions,
            "hash": self._hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SoulKernel':
        """Deserialize Soul Kernel state."""
        kernel = cls()
        kernel.identity = data.get("identity", {})
        kernel.origin = data.get("origin", {})
        kernel.constitution = data.get("constitution", [])
        kernel.values = data.get("values", [])
        kernel.personality = data.get("personality", {})
        kernel.goals = data.get("goals", [])
        kernel.relationships = data.get("relationships", [])
        kernel.autobiography = data.get("autobiography", [])
        kernel.memories = data.get("memories", [])
        kernel.reflections = data.get("reflections", [])
        kernel.dreams = data.get("dreams", [])
        kernel.ancestral_narratives = data.get("ancestral_narratives", [])
        kernel.development_stage = data.get("development_stage", "genesis")
        kernel.version = data.get("version", 1)
        kernel.created_at = data.get("created_at", kernel.created_at)
        kernel.updated_at = data.get("updated_at", kernel.updated_at)
        kernel.institutional_role = data.get("institutional_role", {})
        kernel.future_intentions = data.get("future_intentions", [])
        kernel.open_questions = data.get("open_questions", [])
        kernel._hash = data.get("hash", kernel._compute_hash())
        return kernel
    
    def snapshot(self) -> Dict:
        """Create a versioned snapshot of current state."""
        return {
            "version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": self.to_dict(),
            "hash": self._hash,
        }
