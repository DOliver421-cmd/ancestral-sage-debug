"""
NAM API Routes — Hybrid NAM Leadership Intelligence Endpoints

Per specification §37, these endpoints expose:
- Knowledge Forge (ingest, search, approve/reject)
- Identity & State
- Memory & Autobiography
- Dreams
- Reflections
- Leadership reviews & ledger
- Jamil ↔ NAM protocol
- Mission alignment
- Development tracking
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.hybrid_nam.designation import HybridNAMDesignation
from ai.hybrid_nam.soul_kernel import SoulKernel
from ai.hybrid_nam.knowledge_forge import KnowledgeForge, KnowledgeObject
from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains
from ai.hybrid_nam.memory_engine import (
    create_memory, create_autobiographical_event, create_intention,
    retrieve_memories, detect_drift, analyze_team_context,
)
from ai.hybrid_nam.dream_engine import assemble_dream_inputs, generate_dream
from ai.hybrid_nam.reflection_engine import create_reflection, generate_constitutional_tension
from ai.hybrid_nam.leadership_engine import evaluate_action, create_ledger_entry
from ai.hybrid_nam.jamil_protocol import (
    create_review_request, process_review, classify_autonomy,
    escalate, resolve_escalation, generate_review_template,
)

router = APIRouter(prefix="/api/nam", tags=["Hybrid NAM"])

# ── Singletons (in-memory for proof of concept; DB-backed in production) ──────
nam = HybridNAMDesignation()
soul = SoulKernel()
forge = KnowledgeForge()

# In-memory stores (would be MongoDB in production)
_knowledge_base = []
_memories = []
_intentions = []
_dreams = []
_reflections = []
_ledger = []
_escalations = []


# ── Pydantic Models ───────────────────────────────────────────────────────────

class KnowledgeIngest(BaseModel):
    content: str
    source_type: str = "manual_entry"
    source_origin: str = "human"
    content_type: str = "fact"
    title: str = ""
    domains: List[str] = []
    keywords: List[str] = []
    purpose: str = "institutional"

class KnowledgeReview(BaseModel):
    approved: bool
    reviewer: str = "NAM Oshun"

class MemoryCreate(BaseModel):
    memory_type: str = "semantic"
    content: str
    importance: float = 0.5
    participants: List[str] = []

class IntentionCreate(BaseModel):
    objective: str
    target_date: Optional[str] = None
    dependencies: List[str] = []
    owner: str = "Hybrid NAM"
    leadership_context: str = ""

class DreamRequest(BaseModel):
    open_questions: List[str] = []
    creative_ideas: List[str] = []
    organizational_challenges: List[str] = []

class ReflectionCreate(BaseModel):
    event_type: str = "general"
    event_description: str
    expectation: str
    reality: str
    importance: float = 0.5

class ActionReview(BaseModel):
    description: str
    actor: str = "Jamil"
    purpose: str = ""
    beneficiary: str = "user"
    constraints: List[str] = []
    risks: List[str] = []
    expected_outcome: str = ""


# ── Knowledge Forge Endpoints ─────────────────────────────────────────────────

@router.post("/knowledge/ingest")
async def ingest_knowledge(body: KnowledgeIngest):
    """Ingest new knowledge into the Knowledge Forge."""
    item = forge.ingest(
        content=body.content,
        source_info={
            "origin": body.source_origin or "api",
            "type": body.source_type or "manual",
            "content_type": body.content_type or "fact",
            "title": body.title or "",
            "domains": body.domains or [],
            "keywords": body.keywords or [],
        },
    )
    _knowledge_base.append(item.to_dict() if hasattr(item, 'to_dict') else item)
    return {"status": "ingested", "item": item.to_dict() if hasattr(item, 'to_dict') else item}


@router.get("/knowledge/search")
async def search_knowledge(q: str = "", domains: str = "", include_synthetic: bool = False):
    """Search the Knowledge Forge with hybrid retrieval."""
    domain_list = [d.strip() for d in domains.split(",") if d.strip()] if domains else None
    result = retrieve(
        query=q,
        knowledge_base=_knowledge_base,
        domains=domain_list,
        include_synthetic=include_synthetic,
    )
    return result


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str):
    """Get a specific knowledge item."""
    for item in _knowledge_base:
        if item.get("knowledge_id") == knowledge_id:
            return item
    raise HTTPException(status_code=404, detail="Knowledge item not found")


@router.post("/knowledge/{knowledge_id}/approve")
async def approve_knowledge(knowledge_id: str, body: KnowledgeReview):
    """Approve or reject a knowledge item."""
    for item in _knowledge_base:
        if item.get("knowledge_id") == knowledge_id:
            item["approved"] = body.approved
            item["status"] = "approved" if body.approved else "rejected"
            item["reviewed_by"] = body.reviewer
            item["reviewed_at"] = datetime.utcnow().isoformat()
            return {"status": "approved" if body.approved else "rejected", "item": item}
    raise HTTPException(status_code=404, detail="Knowledge item not found")


@router.post("/knowledge/import")
async def import_knowledge(body: KnowledgeIngest):
    """Bulk import knowledge (founding archive mode)."""
    item = forge.ingest(
        content=body.content,
        source_info={
            "origin": body.source_origin or "founding_archive",
            "type": body.source_type or "founding_archive",
            "content_type": body.content_type or "principle",
            "title": body.title or "",
            "domains": body.domains or [],
            "keywords": body.keywords or [],
        },
    )
    item_dict = item.to_dict() if hasattr(item, 'to_dict') else item
    item_dict["purpose"] = body.purpose
    item_dict["import_mode"] = "founding_archive"
    _knowledge_base.append(item_dict)
    return {"status": "imported", "item": item}


# ── Identity & State Endpoints ────────────────────────────────────────────────

@router.get("/identity")
async def get_identity():
    """Get NAM's identity, designation, and organizational relationships."""
    return {
        "designation": nam.identity,
        "constitution": nam.constitution,
        "personality": nam.personality,
        "authority": {
            "is_human": nam.identity.get('is_human', False),
            "is_clone_of_founder": nam.identity.get('is_clone_of_founder', False),
            "is_legal_authority": nam.identity.get('is_legal_authority', False),
            "is_operational_director": nam.identity.get('is_operational_director', False),
            "primary_function": nam.identity.get('primary_function', ''),
        },
    }


@router.get("/state")
async def get_state():
    """Get NAM's current soul kernel state."""
    return soul.export_state()


@router.get("/constitution")
async def get_constitution():
    """Get NAM's foundational constitution."""
    return {
        "principles": nam.constitution,
        "constitutional_hash": nam.get_hash(),
    }


# ── Memory Endpoints ──────────────────────────────────────────────────────────

@router.get("/memory")
async def get_memories(memory_type: str = "", limit: int = 20):
    """Get NAM's memories, optionally filtered by type."""
    results = retrieve_memories(
        memories=_memories,
        memory_type=memory_type if memory_type else None,
        limit=limit,
    )
    return {"memories": results, "total": len(_memories)}


@router.post("/memory")
async def create_new_memory(body: MemoryCreate):
    """Create a new memory for NAM."""
    memory = create_memory(
        memory_type=body.memory_type,
        content=body.content,
        importance=body.importance,
        participants=body.participants,
    )
    _memories.append(memory)
    return {"status": "created", "memory": memory}


@router.get("/autobiography")
async def get_autobiography():
    """Get NAM's autobiographical events."""
    events = [m for m in _memories if m.get("memory_type") == "episodic"]
    return {"events": events, "total": len(events)}


# ── Intention / Prospective Memory Endpoints ──────────────────────────────────

@router.get("/intentions")
async def get_intentions():
    """Get NAM's active intentions (prospective memory)."""
    return {"intentions": _intentions, "total": len(_intentions)}


@router.post("/intentions")
async def create_new_intention(body: IntentionCreate):
    """Create a new intention."""
    intention = create_intention(
        objective=body.objective,
        target_date=body.target_date,
        dependencies=body.dependencies,
        owner=body.owner,
        leadership_context=body.leadership_context,
    )
    _intentions.append(intention)
    return {"status": "created", "intention": intention}


@router.get("/intentions/drift")
async def check_drift():
    """Detect drift between intentions and reality."""
    drifts = detect_drift(_intentions, _memories)
    return {"drifts": drifts, "total": len(drifts)}


# ── Dream Endpoints ───────────────────────────────────────────────────────────

@router.get("/dreams")
async def get_dreams(limit: int = 10):
    """Get recent dreams."""
    return {"dreams": _dreams[-limit:], "total": len(_dreams)}


@router.post("/dream")
async def generate_new_dream(body: DreamRequest):
    """Generate a new dream (async synthesis)."""
    inputs = assemble_dream_inputs(
        memories=_memories,
        open_questions=body.open_questions,
        creative_ideas=body.creative_ideas,
        organizational_challenges=body.organizational_challenges,
        goals=[i for i in _intentions if i.get("status") == "active"],
        recent_events=[m for m in _memories if m.get("memory_type") == "episodic"][-10:],
    )
    dream = generate_dream(inputs)
    _dreams.append(dream)
    return dream


# ── Reflection Endpoints ──────────────────────────────────────────────────────

@router.get("/reflections")
async def get_reflections(limit: int = 10):
    """Get recent reflections."""
    return {"reflections": _reflections[-limit:], "total": len(_reflections)}


@router.post("/reflect")
async def create_new_reflection(body: ReflectionCreate):
    """Create a new reflection after an event."""
    event = {
        "type": body.event_type,
        "description": body.event_description,
        "importance": body.importance,
    }
    reflection = create_reflection(
        event=event,
        expectation=body.expectation,
        reality=body.reality,
    )
    _reflections.append(reflection)
    
    # Also create an autobiographical memory
    memory = create_autobiographical_event(
        event_type="REFLECTION_COMPLETED",
        context=body.event_description,
        participants=["Hybrid NAM"],
        interpretation=body.expectation,
        outcome=body.reality,
        lesson=str(reflection.get("candidate_lessons", [])),
        importance=body.importance,
    )
    _memories.append(memory)
    
    return reflection


@router.get("/reflections/tensions")
async def check_constitutional_tensions():
    """Check for constitutional tensions across reflections."""
    tensions = generate_constitutional_tension(_reflections)
    return tensions


# ── Leadership Endpoints ──────────────────────────────────────────────────────

@router.post("/leadership/review")
async def review_action(body: ActionReview):
    """Evaluate an action against mission principles."""
    action = {
        "description": body.description,
        "actor": body.actor,
        "purpose": body.purpose,
        "beneficiary": body.beneficiary,
    }
    evaluation = evaluate_action(action)
    return evaluation


@router.get("/leadership/ledger")
async def get_ledger(limit: int = 20):
    """Get the leadership decision ledger."""
    return {"ledger": _ledger[-limit:], "total": len(_ledger)}


@router.post("/leadership/evaluate")
async def evaluate_and_log(body: ActionReview):
    """Evaluate an action and log it in the leadership ledger."""
    action = {
        "description": body.description,
        "actor": body.actor,
        "purpose": body.purpose,
        "beneficiary": body.beneficiary,
    }
    evaluation = evaluate_action(action)
    entry = create_ledger_entry(evaluation)
    _ledger.append(entry)
    return {"evaluation": evaluation, "ledger_entry": entry}


# ── Jamil ↔ NAM Protocol Endpoints ────────────────────────────────────────────

@router.post("/jamil/review")
async def jamil_request_review(body: ActionReview):
    """Jamil submits a proposal for NAM's leadership review."""
    request = create_review_request(
        proposal=body.description,
        objective=body.purpose,
        constraints=body.constraints,
        risks=body.risks,
        expected_outcome=body.expected_outcome,
        actor=body.actor,
    )
    
    action = {
        "description": body.description,
        "actor": body.actor,
        "purpose": body.purpose,
        "beneficiary": body.beneficiary,
    }
    evaluation = evaluate_action(action)
    response = process_review(request, evaluation)
    
    return {"request": request, "response": response}


@router.get("/jamil/protocol")
async def get_jamil_protocol():
    """Get the Jamil ↔ NAM communication protocol."""
    return {
        "protocol": "Jamil proposes → NAM reviews → Human approves (if needed) → Jamil executes",
        "escalation_levels": [
            {"level": 0, "name": "Routine", "description": "Jamil operates independently"},
            {"level": 1, "name": "NAM Advisory", "description": "NAM provides optional guidance"},
            {"level": 2, "name": "NAM Review", "description": "NAM reviews strategy before execution"},
            {"level": 3, "name": "Human Escalation", "description": "Significant uncertainty or concern"},
            {"level": 4, "name": "Human Authority", "description": "AI execution stops pending human decision"},
        ],
    }


@router.get("/jamil/autonomy/{action_type}")
async def get_autonomy_level(action_type: str):
    """Get the autonomy classification for an action type."""
    return classify_autonomy(action_type)


# ── Mission Alignment Endpoints ───────────────────────────────────────────────

@router.get("/mission/alignment")
async def get_mission_alignment():
    """Get NAM's mission alignment criteria."""
    from ai.hybrid_nam.leadership_engine import MISSION_PRINCIPLES
    return {"principles": MISSION_PRINCIPLES}


@router.post("/mission/evaluate")
async def evaluate_mission_alignment(body: ActionReview):
    """Evaluate a proposed action against mission alignment."""
    action = {
        "description": body.description,
        "actor": body.actor,
        "purpose": body.purpose,
        "beneficiary": body.beneficiary,
    }
    return evaluate_action(action)


# ── Development Endpoints ─────────────────────────────────────────────────────

@router.get("/development")
async def get_development():
    """Get NAM's developmental status."""
    return {
        "stage": soul.state.get("development_stage", {}),
        "event_count": len([m for m in _memories if m.get("memory_type") == "episodic"]),
        "reflection_count": len(_reflections),
        "dream_count": len(_dreams),
        "knowledge_count": len(_knowledge_base),
        "intention_count": len(_intentions),
        "ledger_count": len(_ledger),
    }


@router.post("/development/evaluate")
async def evaluate_development():
    """Trigger a developmental self-assessment."""
    # Create a developmental reflection
    reflection = create_reflection(
        event={
            "type": "developmental_assessment",
            "description": "Periodic self-evaluation of NAM's developmental trajectory",
            "importance": 0.7,
        },
        expectation="NAM should show growth across knowledge, memory, and reflection",
        reality=f"NAM has {len(_knowledge_base)} knowledge items, {len(_memories)} memories, {len(_reflections)} reflections, {len(_dreams)} dreams",
    )
    _reflections.append(reflection)
    return reflection


# ── Escalation Endpoints ──────────────────────────────────────────────────────

@router.post("/escalate")
async def create_escalation(reason: str = "", severity: str = "advisory", action: str = ""):
    """Create an escalation requiring human attention."""
    esc = escalate(reason=reason, severity=severity, context={}, original_action=action)
    _escalations.append(esc)
    return esc


@router.get("/escalations")
async def get_escalations():
    """Get open escalations."""
    open_escs = [e for e in _escalations if e.get("status") == "open"]
    return {"escalations": open_escs, "total": len(open_escs)}


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_esc(escalation_id: str, resolved_by: str = "NAM Oshun", resolution: str = "", approved: bool = True):
    """Resolve an escalation."""
    for esc in _escalations:
        if esc.get("escalation_id") == escalation_id:
            resolved = resolve_escalation(esc, resolved_by, resolution, approved)
            return resolved
    raise HTTPException(status_code=404, detail="Escalation not found")
