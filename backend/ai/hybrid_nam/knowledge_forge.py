"""
knowledge_forge.py — Knowledge Forge
=====================================

Convert approved information into structured, attributable, queryable
knowledge that Hybrid NAM can use for leadership, strategy, coaching,
organizational memory, and mission alignment.

Architecture:
    KNOWLEDGE SOURCE
        ↓
    INGESTION SERVICE
        ↓
    FILE / DATA PARSER
        ↓
    NORMALIZATION
        ↓
    PRIVACY FILTER
        ↓
    CLASSIFICATION
        ↓
    KNOWLEDGE EXTRACTION
        ↓
    PROVENANCE
        ↓
    HUMAN/AI VALIDATION
        ↓
    NAM KNOWLEDGE BASE
"""

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any


# ── Knowledge Status Lifecycle ────────────────────────────────────────────────

class KnowledgeStatus(str, Enum):
    RAW = "raw"
    PARSED = "parsed"
    CLASSIFIED = "classified"
    CANDIDATE = "candidate"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


# ── Knowledge Types ───────────────────────────────────────────────────────────

class KnowledgeType(str, Enum):
    FACT = "fact"
    PRINCIPLE = "principle"
    VALUE = "value"
    BELIEF = "belief"
    MISSION = "mission"
    GOAL = "goal"
    STRATEGY = "strategy"
    POLICY = "policy"
    DECISION = "decision"
    LESSON = "lesson"
    EVENT = "event"
    PERSON = "person"
    PROJECT = "project"
    RELATIONSHIP = "relationship"
    PROCESS = "process"
    PROCEDURE = "procedure"
    CREATIVE_IDEA = "creative_idea"
    QUOTE = "quote"
    COMMUNICATION_PATTERN = "communication_pattern"
    LEADERSHIP_PATTERN = "leadership_pattern"
    HISTORICAL_EVENT = "historical_event"
    DREAM = "dream"
    ANCESTRAL_NARRATIVE = "ancestral_narrative"
    FUTURE_SCENARIO = "future_scenario"
    RISK = "risk"
    ASSUMPTION = "assumption"
    QUESTION = "question"


# ── Privacy Classifications ───────────────────────────────────────────────────

class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    PRIVATE = "private"
    THIRD_PARTY = "third_party"
    EXCLUDE = "exclude"


# ── Source Classifications ────────────────────────────────────────────────────

class SourceClassification(str, Enum):
    FOUNDING_ARCHIVE = "founding_archive"
    INSTITUTIONAL = "institutional"
    TEAM = "team"
    PROJECT = "project"
    TRAINING = "training"
    HISTORICAL = "historical"
    EXTERNAL = "external"
    PERSONAL = "personal"


# ── Knowledge Object ──────────────────────────────────────────────────────────

class KnowledgeObject:
    """
    A single knowledge item with full provenance.
    """
    
    def __init__(self, **kwargs):
        self.knowledge_id: str = kwargs.get("knowledge_id", f"KN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
        self.source_id: str = kwargs.get("source_id", "")
        self.source_type: str = kwargs.get("source_type", "")
        self.content_type: str = kwargs.get("content_type", "fact")
        self.title: str = kwargs.get("title", "")
        self.statement: str = kwargs.get("statement", "")
        self.confidence: float = kwargs.get("confidence", 0.5)
        self.status: str = kwargs.get("status", KnowledgeStatus.RAW)
        self.approved: bool = kwargs.get("approved", False)
        self.created_at: str = kwargs.get("created_at", datetime.now(timezone.utc).isoformat())
        self.source_timestamp: str = kwargs.get("source_timestamp", "")
        self.privacy: str = kwargs.get("privacy", PrivacyLevel.INTERNAL)
        self.provenance: Dict = kwargs.get("provenance", {})
        self.relationships: List[Dict] = kwargs.get("relationships", [])
        self.tags: List[str] = kwargs.get("tags", [])
        self.domains: List[str] = kwargs.get("domains", [])
        self.keywords: List[str] = kwargs.get("keywords", [])
        self.evidence: List[Dict] = kwargs.get("evidence", [])
    
    def to_dict(self) -> Dict:
        return {
            "knowledge_id": self.knowledge_id,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "content_type": self.content_type,
            "title": self.title,
            "statement": self.statement,
            "confidence": self.confidence,
            "status": self.status,
            "approved": self.approved,
            "created_at": self.created_at,
            "source_timestamp": self.source_timestamp,
            "privacy": self.privacy,
            "provenance": self.provenance,
            "relationships": self.relationships,
            "tags": self.tags,
            "domains": self.domains,
            "keywords": self.keywords,
            "evidence": self.evidence,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeObject':
        return cls(**data)


# ── Knowledge Forge ───────────────────────────────────────────────────────────

class KnowledgeForge:
    """
    The Knowledge Forge: ingestion, classification, and retrieval
    of institutional knowledge for Hybrid NAM.
    """
    
    def __init__(self):
        self.knowledge_base: List[KnowledgeObject] = []
        self.sources: List[Dict] = []
        self.conflicts: List[Dict] = []
    
    def ingest(self, content: str, source_info: Dict) -> KnowledgeObject:
        """
        Ingest raw content into the knowledge forge.
        
        Args:
            content: Raw text content
            source_info: Metadata about the source
        
        Returns:
            KnowledgeObject in RAW status
        """
        knowledge = KnowledgeObject(
            source_id=source_info.get("source_id", ""),
            source_type=source_info.get("source_type", SourceClassification.EXTERNAL),
            content_type=source_info.get("content_type", KnowledgeType.FACT),
            title=source_info.get("title", "Untitled"),
            statement=content,
            confidence=0.3,  # Low confidence until classified
            status=KnowledgeStatus.RAW,
            privacy=source_info.get("privacy", PrivacyLevel.INTERNAL),
            provenance={
                "origin": source_info.get("origin", "unknown"),
                "method": "ingestion",
                "evidence_count": 1,
            },
            tags=source_info.get("tags", []),
            # Retrieval fields: knowledge_graph.retrieve() scores items by
            # domain overlap and keyword hits. Dropping them at ingestion
            # (the historical behavior) made every API-ingested item
            # invisible to domain-scoped search — carry them through.
            domains=source_info.get("domains", []),
            keywords=source_info.get("keywords", []),
        )
        
        self.knowledge_base.append(knowledge)
        return knowledge
    
    def classify(self, knowledge_id: str, classification: Dict) -> KnowledgeObject:
        """
        Classify a knowledge object.
        
        Updates: content_type, confidence, status
        """
        knowledge = self._find(knowledge_id)
        if not knowledge:
            raise ValueError(f"Knowledge not found: {knowledge_id}")
        
        knowledge.content_type = classification.get("content_type", knowledge.content_type)
        knowledge.confidence = classification.get("confidence", knowledge.confidence)
        knowledge.status = KnowledgeStatus.CLASSIFIED
        knowledge.tags.extend(classification.get("tags", []))
        
        return knowledge
    
    def approve(self, knowledge_id: str, approver: str = "human") -> KnowledgeObject:
        """
        Approve a knowledge object for active use.
        """
        knowledge = self._find(knowledge_id)
        if not knowledge:
            raise ValueError(f"Knowledge not found: {knowledge_id}")
        
        knowledge.status = KnowledgeStatus.APPROVED
        knowledge.approved = True
        knowledge.provenance["approved_by"] = approver
        knowledge.provenance["approved_at"] = datetime.now(timezone.utc).isoformat()
        
        return knowledge
    
    def reject(self, knowledge_id: str, reason: str = "") -> KnowledgeObject:
        """
        Reject a knowledge object.
        """
        knowledge = self._find(knowledge_id)
        if not knowledge:
            raise ValueError(f"Knowledge not found: {knowledge_id}")
        
        knowledge.status = KnowledgeStatus.DEPRECATED
        knowledge.provenance["rejected_reason"] = reason
        
        return knowledge
    
    def search(self, query: str, limit: int = 10, 
               status_filter: Optional[str] = None,
               type_filter: Optional[str] = None) -> List[KnowledgeObject]:
        """
        Search the knowledge base.
        
        In production: vector similarity + graph traversal + structured query
        """
        results = []
        query_lower = query.lower()
        
        for k in self.knowledge_base:
            # Status filter
            if status_filter and k.status != status_filter:
                continue
            
            # Type filter
            if type_filter and k.content_type != type_filter:
                continue
            
            # Privacy check
            if k.privacy == PrivacyLevel.EXCLUDE:
                continue
            
            # Simple keyword matching (replace with vector search in production)
            if (query_lower in k.title.lower() or 
                query_lower in k.statement.lower() or
                any(query_lower in tag.lower() for tag in k.tags)):
                results.append(k)
        
        # Sort by confidence * approved status
        results.sort(key=lambda x: (
            1.0 if x.approved else 0.5,
            x.confidence,
        ), reverse=True)
        
        return results[:limit]
    
    def detect_conflicts(self) -> List[Dict]:
        """
        Detect conflicts in the knowledge base.
        
        When sources disagree, NAM should not silently choose one.
        """
        conflicts = []
        
        # Simple conflict detection (replace with semantic analysis in production)
        by_type = {}
        for k in self.knowledge_base:
            if k.status != KnowledgeStatus.ACTIVE:
                continue
            by_type.setdefault(k.content_type, []).append(k)
        
        # Check for contradictions within same type
        for k_type, items in by_type.items():
            for i, item_a in enumerate(items):
                for item_b in items[i+1:]:
                    # Simple: if tags overlap but statements differ significantly
                    shared_tags = set(item_a.tags) & set(item_b.tags)
                    if shared_tags and item_a.statement.lower() != item_b.statement.lower():
                        conflicts.append({
                            "conflict_type": "contradiction",
                            "knowledge_a": item_a.knowledge_id,
                            "knowledge_b": item_b.knowledge_id,
                            "shared_context": list(shared_tags),
                            "needs_human_review": True,
                        })
        
        self.conflicts = conflicts
        return conflicts
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        status_counts = {}
        type_counts = {}
        for k in self.knowledge_base:
            status_counts[k.status] = status_counts.get(k.status, 0) + 1
            type_counts[k.content_type] = type_counts.get(k.content_type, 0) + 1
        
        return {
            "total": len(self.knowledge_base),
            "by_status": status_counts,
            "by_type": type_counts,
            "approved": sum(1 for k in self.knowledge_base if k.approved),
            "conflicts": len(self.conflicts),
        }
    
    def _find(self, knowledge_id: str) -> Optional[KnowledgeObject]:
        """Find a knowledge object by ID."""
        for k in self.knowledge_base:
            if k.knowledge_id == knowledge_id:
                return k
        return None
    
    def to_dict(self) -> Dict:
        """Serialize knowledge forge state."""
        return {
            "knowledge_base": [k.to_dict() for k in self.knowledge_base],
            "sources": self.sources,
            "conflicts": self.conflicts,
            "stats": self.get_stats(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'KnowledgeForge':
        """Deserialize knowledge forge state."""
        forge = cls()
        forge.knowledge_base = [KnowledgeObject.from_dict(k) for k in data.get("knowledge_base", [])]
        forge.sources = data.get("sources", [])
        forge.conflicts = data.get("conflicts", [])
        return forge
