"""
Knowledge Graph — Hybrid Retrieval Engine

Implements the dual-pathway retrieval described in the specification:
1. Vector similarity search (embeddings)
2. Graph traversal (relationships)
3. Structured queries (relational)
4. Source ranking & context assembly

Every retrieval passes through:
  Query → Classify → Domain ID → Vector + Graph + Structured
  → Source Ranking → Context Assembly → Reasoning Prompt
"""

import json
import uuid
from datetime import datetime
from typing import Any, Optional


# ── Relationship Types ────────────────────────────────────────────────────────

RELATIONSHIP_TYPES = [
    "supports",
    "contradicts",
    "derived_from",
    "caused_by",
    "learned_from",
    "related_to",
    "belongs_to",
    "created_by",
    "approved_by",
    "supersedes",
    "depends_on",
    "influences",
]


# ── Knowledge Domain Classification ──────────────────────────────────────────

DOMAIN_KEYWORDS = {
    "mission": ["mission", "purpose", "vision", "goal", "objective", "calling"],
    "identity": ["identity", "who", "personality", "character", "self"],
    "leadership": ["leadership", "lead", "guide", "direct", "govern", "authority"],
    "strategy": ["strategy", "plan", "approach", "direction", "decision"],
    "values": ["value", "principle", "belief", "ethic", "moral", "standard"],
    "history": ["history", "past", "founded", "origin", "began", "started"],
    "relationship": ["team", "people", "role", "skill", "collaborate", "member"],
    "creative": ["creative", "art", "music", "design", "expression", "story"],
    "technical": ["system", "architecture", "code", "build", "infrastructure"],
    "organizational": ["policy", "procedure", "protocol", "workflow", "process"],
    "developmental": ["learn", "grow", "develop", "improve", "skill", "capacity"],
    "dream": ["dream", "imagine", "envision", "possibility", "hypothetical"],
    "ancestral": ["ancestral", "heritage", "lineage", "legacy", "origin story"],
}


def classify_domains(text: str) -> list[str]:
    """Classify text into knowledge domains for retrieval scoping."""
    text_lower = text.lower()
    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[domain] = score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [d for d, _ in ranked[:3]]


# ── Source Ranking ────────────────────────────────────────────────────────────

# Priority ordering per the specification §15
SOURCE_RANKS = {
    "constitutional": 10,
    "policy": 9,
    "organizational_state": 8,
    "verified_fact": 7,
    "recent_decision": 6,
    "historical": 5,
    "inferred_principle": 4,
    "candidate_knowledge": 3,
    "synthetic_narrative": 2,
    "unverified": 1,
}


def rank_source(knowledge_item: dict) -> int:
    """Rank a knowledge item by source priority."""
    status = knowledge_item.get("status", "unverified")
    content_type = knowledge_item.get("content_type", "")
    
    if status == "constitutional":
        return SOURCE_RANKS["constitutional"]
    if content_type == "policy":
        return SOURCE_RANKS["policy"]
    if status == "approved" and content_type == "verified_fact":
        return SOURCE_RANKS["verified_fact"]
    if status == "approved" and content_type in ("principle", "value"):
        return SOURCE_RANKS["inferred_principle"]
    if status == "candidate":
        return SOURCE_RANKS["candidate_knowledge"]
    if content_type in ("dream", "ancestral_narrative"):
        return SOURCE_RANKS["synthetic_narrative"]
    return SOURCE_RANKS["unverified"]


def rank_sources(items: list[dict]) -> list[dict]:
    """Sort knowledge items by source priority."""
    return sorted(items, key=rank_source, reverse=True)


# ── Context Assembly ─────────────────────────────────────────────────────────

MAX_CONTEXT_TOKENS = 4000  # approximate budget per retrieval


def assemble_context(
    vector_results: list[dict],
    graph_results: list[dict],
    structured_results: list[dict],
    query: str,
) -> dict:
    """
    Merge and deduplicate retrieval results into a ranked context block.
    Returns a dict with 'context_items', 'conflicts', and 'confidence'.
    """
    # Merge all sources
    all_items = {}
    for item in vector_results + graph_results + structured_results:
        kid = item.get("knowledge_id", str(uuid.uuid4()))
        if kid not in all_items:
            all_items[kid] = item
        else:
            # Prefer the version with more metadata
            existing = all_items[kid]
            if len(item) > len(existing):
                all_items[kid] = item
    
    # Rank
    ranked = rank_sources(list(all_items.values()))
    
    # Detect conflicts
    conflicts = detect_conflicts(ranked)
    
    # Budget-aware selection
    selected = []
    token_count = 0
    for item in ranked:
        approx_tokens = len(json.dumps(item)) // 4
        if token_count + approx_tokens > MAX_CONTEXT_TOKENS:
            break
        selected.append(item)
        token_count += approx_tokens
    
    # Calculate confidence
    if not selected:
        confidence = 0.0
    else:
        avg_conf = sum(i.get("confidence", 0.5) for i in selected) / len(selected)
        rank_bonus = min(len(selected) / 5, 0.2)
        confidence = min(avg_conf + rank_bonus, 1.0)
    
    return {
        "context_items": selected,
        "conflicts": conflicts,
        "confidence": round(confidence, 3),
        "total_retrieved": len(ranked),
        "selected_count": len(selected),
    }


# ── Conflict Detection ───────────────────────────────────────────────────────

def detect_conflicts(items: list[dict]) -> list[dict]:
    """
    Identify knowledge items that contradict each other.
    Per specification §16: NAM must not silently choose one side.
    """
    conflicts = []
    approved = [i for i in items if i.get("status") == "approved"]
    
    for i, item_a in enumerate(approved):
        for item_b in approved[i + 1:]:
            # Check if they share domains but differ on key dimensions
            domains_a = set(item_a.get("domains", []))
            domains_b = set(item_b.get("domains", []))
            shared = domains_a & domains_b
            
            if shared:
                # Check for conflicting values
                val_a = item_a.get("statement", "").lower()
                val_b = item_b.get("statement", "").lower()
                
                # Simple negation detection
                negations = ["not", "never", "should not", "must not", "should not"]
                has_neg_a = any(neg in val_a for neg in negations)
                has_neg_b = any(neg in val_b for neg in negations)
                
                if has_neg_a != has_neg_b:
                    conflicts.append({
                        "conflict_type": "strategic_priority",
                        "source_a": {
                            "knowledge_id": item_a.get("knowledge_id"),
                            "statement": item_a.get("statement", ""),
                            "domains": list(shared),
                        },
                        "source_b": {
                            "knowledge_id": item_b.get("knowledge_id"),
                            "statement": item_b.get("statement", ""),
                            "domains": list(shared),
                        },
                        "recommendation": "Human review required",
                    })
    
    return conflicts


# ── Retrieval Interface ──────────────────────────────────────────────────────

def retrieve(
    query: str,
    knowledge_base: list[dict],
    domains: Optional[list[str]] = None,
    include_synthetic: bool = False,
    max_results: int = 10,
) -> dict:
    """
    Main retrieval function. In production this would use vector embeddings
    and graph traversal. This implements the logical pipeline with
    in-memory structures for the proof-of-concept.
    """
    if domains is None:
        domains = classify_domains(query)
    
    query_lower = query.lower()
    
    # Simulate vector retrieval (keyword matching for proof of concept)
    vector_results = []
    for item in knowledge_base:
        statement = item.get("statement", "").lower()
        title = item.get("title", "").lower()
        keywords = item.get("keywords", [])
        
        relevance = 0
        for word in query_lower.split():
            if word in statement or word in title:
                relevance += 1
            if word in [k.lower() for k in keywords]:
                relevance += 2
        
        # Filter by domain overlap
        item_domains = set(item.get("domains", []))
        domain_overlap = len(item_domains & set(domains))
        
        if relevance > 0 or domain_overlap > 0:
            vector_results.append({
                **item,
                "_relevance": relevance + domain_overlap,
            })
    
    vector_results.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
    vector_results = vector_results[:max_results]
    
    # Simulate graph traversal — find related items
    graph_results = []
    retrieved_ids = {i.get("knowledge_id") for i in vector_results}
    relationships = [
        r for item in vector_results
        for r in item.get("relationships", [])
    ]
    
    for rel in relationships:
        target_id = rel.get("target_id")
        if target_id and target_id not in retrieved_ids:
            target = next(
                (i for i in knowledge_base if i.get("knowledge_id") == target_id),
                None
            )
            if target:
                graph_results.append({
                    **target,
                    "_relevance": rel.get("strength", 0.5),
                    "_via_relationship": rel.get("type", "related_to"),
                })
                retrieved_ids.add(target_id)
    
    # Filter synthetic narratives if not requested
    if not include_synthetic:
        vector_results = [
            i for i in vector_results
            if i.get("content_type") not in ("dream", "ancestral_narrative")
        ]
        graph_results = [
            i for i in graph_results
            if i.get("content_type") not in ("dream", "ancestral_narrative")
        ]
    
    # Assemble context
    context = assemble_context(vector_results, graph_results, [], query)
    
    return {
        "query": query,
        "domains": domains,
        "context": context,
        "timestamp": datetime.utcnow().isoformat(),
    }
