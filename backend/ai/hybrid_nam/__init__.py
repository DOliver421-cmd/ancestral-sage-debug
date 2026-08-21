"""
hybrid_nam/ — WAI Institute AI Leadership Intelligence
======================================================

Hybrid NAM is a persistent AI leadership intelligence designed to operate
as Assistant Director within the WAI Institute ecosystem.

Architecture:
    THE SOURCE (immutable root)
        ↓
    HYBRID NAM (designation)
        ↓
    SOUL KERNEL (persistent state)
        ↓
    KNOWLEDGE FORGE (ingestion)
        ↓
    MEMORY ENGINE (temporal continuity)
        ↓
    DREAM ENGINE (async synthesis)
        ↓
    REFLECTION ENGINE (outcome learning)
        ↓
    LEADERSHIP ENGINE (mission evaluation)
        ↓
    LLM (replaceable reasoning engine)

The Source remains untouched. NAM is a designation above it.
"""

from ai.hybrid_nam.designation import HybridNAMDesignation
from ai.hybrid_nam.soul_kernel import SoulKernel
from ai.hybrid_nam.knowledge_forge import KnowledgeForge, KnowledgeItem
from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains, assemble_context
from ai.hybrid_nam.memory_engine import (
    create_memory, create_autobiographical_event, create_intention,
    retrieve_memories, detect_drift, analyze_team_context,
)
from ai.hybrid_nam.dream_engine import assemble_dream_inputs, generate_dream, evaluate_dream_outcome
from ai.hybrid_nam.reflection_engine import create_reflection, generate_constitutional_tension
from ai.hybrid_nam.leadership_engine import evaluate_action, create_ledger_entry
from ai.hybrid_nam.jamil_protocol import (
    create_review_request, process_review, classify_autonomy,
    escalate, resolve_escalation, generate_review_template,
)

__all__ = [
    "HybridNAMDesignation", "SoulKernel",
    "KnowledgeForge", "KnowledgeItem",
    "retrieve", "classify_domains", "assemble_context",
    "create_memory", "create_autobiographical_event", "create_intention",
    "retrieve_memories", "detect_drift", "analyze_team_context",
    "assemble_dream_inputs", "generate_dream", "evaluate_dream_outcome",
    "create_reflection", "generate_constitutional_tension",
    "evaluate_action", "create_ledger_entry",
    "create_review_request", "process_review", "classify_autonomy",
    "escalate", "resolve_escalation", "generate_review_template",
]
