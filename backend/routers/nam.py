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

All endpoints require authentication via Bearer token.
Write endpoints (POST) additionally require executive_admin, oversight,
or support_staff role.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import sys
import os
import jwt

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.hybrid_nam.designation import HybridNAMDesignation
from ai.hybrid_nam.soul_kernel import SoulKernel
from ai.hybrid_nam.knowledge_forge import KnowledgeForge, KnowledgeObject
from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains
from ai.hybrid_nam.memory_engine import (
    create_memory as _create_memory,
    create_autobiographical_event,
    create_intention as _create_intention,
    retrieve_memories as _retrieve_memories,
    detect_drift,
    analyze_team_context,
)
from ai.hybrid_nam.dream_engine import assemble_dream_inputs, generate_dream
from ai.hybrid_nam.reflection_engine import create_reflection, generate_constitutional_tension
from ai.hybrid_nam.leadership_engine import evaluate_action, create_ledger_entry
from ai.hybrid_nam.jamil_protocol import (
    create_review_request, process_review, classify_autonomy,
    escalate, resolve_escalation, generate_review_template,
)
from ai.hybrid_nam import store

router = APIRouter(prefix="/api/nam", tags=["Hybrid NAM"])

# ── Singletons ──────────────────────────────────────────────────────────────
nam = HybridNAMDesignation()
soul = SoulKernel()
forge = KnowledgeForge()


# ── Auth ────────────────────────────────────────────────────────────────────

def _get_jwt_secret():
    """Read JWT_SECRET from server module to avoid circular import."""
    try:
        from server import JWT_SECRET, JWT_ALGO
        return JWT_SECRET, JWT_ALGO
    except ImportError:
        # Fallback for testing
        return os.environ.get("JWT_SECRET", ""), "HS256"


async def require_auth(authorization: Optional[str] = Header(None)) -> dict:
    """Validate JWT token, return user dict."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization.split(" ", 1)[1]
    secret, algo = _get_jwt_secret()
    if not secret:
        raise HTTPException(500, "JWT secret not configured")
    try:
        payload = jwt.decode(token, secret, algorithms=[algo])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role", "free"),
        "email": payload.get("email", ""),
    }


def require_admin(user: dict = Depends(require_auth)) -> dict:
    """Require executive_admin, oversight, or support_staff role."""
    admin_roles = {"executive_admin", "oversight", "support_staff"}
    if user.get("role") not in admin_roles:
        raise HTTPException(403, "Admin access required for this operation")
    return user


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
async def ingest_knowledge(body: KnowledgeIngest, user: dict = Depends(require_admin)):
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
    item_dict = item.to_dict() if hasattr(item, "to_dict") else item
    item_dict["ingested_by"] = user.get("user_id", "unknown")
    await store.create("nam_knowledge", item_dict)
    return {"status": "ingested", "item": item_dict}


@router.get("/knowledge/search")
async def search_knowledge(q: str = "", domains: str = "", include_synthetic: bool = False,
                           user: dict = Depends(require_auth)):
    """Search the Knowledge Forge with hybrid retrieval."""
    domain_list = [d.strip() for d in domains.split(",") if d.strip()] if domains else None
    knowledge_base = await store.find_many("nam_knowledge", limit=500)
    result = retrieve(
        query=q,
        knowledge_base=knowledge_base,
        domains=domain_list,
        include_synthetic=include_synthetic,
    )
    return result


@router.get("/knowledge/{knowledge_id}")
async def get_knowledge(knowledge_id: str, user: dict = Depends(require_auth)):
    """Get a specific knowledge item."""
    item = await store.find_one("nam_knowledge", {"knowledge_id": knowledge_id})
    if item:
        return item
    raise HTTPException(status_code=404, detail="Knowledge item not found")


@router.post("/knowledge/{knowledge_id}/approve")
async def approve_knowledge(knowledge_id: str, body: KnowledgeReview,
                            user: dict = Depends(require_admin)):
    """Approve or reject a knowledge item."""
    item = await store.find_one("nam_knowledge", {"knowledge_id": knowledge_id})
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    update = {
        "approved": body.approved,
        "status": "approved" if body.approved else "rejected",
        "reviewed_by": body.reviewer,
        "reviewed_at": datetime.utcnow().isoformat(),
    }
    await store.update_one("nam_knowledge", {"knowledge_id": knowledge_id}, update)
    item.update(update)
    return {"status": update["status"], "item": item}


@router.post("/knowledge/import")
async def import_knowledge(body: KnowledgeIngest, user: dict = Depends(require_admin)):
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
    item_dict = item.to_dict() if hasattr(item, "to_dict") else item
    item_dict["purpose"] = body.purpose
    item_dict["import_mode"] = "founding_archive"
    item_dict["ingested_by"] = user.get("user_id", "unknown")
    await store.create("nam_knowledge", item_dict)
    return {"status": "imported", "item": item_dict}


# ── Identity & State Endpoints ────────────────────────────────────────────────

@router.get("/identity")
async def get_identity(user: dict = Depends(require_auth)):
    """Get NAM's identity, designation, and organizational relationships."""
    return {
        "designation": nam.identity,
        "constitution": nam.constitution,
        "personality": nam.personality,
        "authority": {
            "is_human": nam.identity.get("is_human", False),
            "is_clone_of_founder": nam.identity.get("is_clone_of_founder", False),
            "is_legal_authority": nam.identity.get("is_legal_authority", False),
            "is_operational_director": nam.identity.get("is_operational_director", False),
            "primary_function": nam.identity.get("primary_function", ""),
        },
    }


@router.get("/state")
async def get_state(user: dict = Depends(require_auth)):
    """Get NAM's current soul kernel state."""
    return soul.export_state()


@router.get("/constitution")
async def get_constitution(user: dict = Depends(require_auth)):
    """Get NAM's foundational constitution."""
    return {
        "principles": nam.constitution,
        "constitutional_hash": nam.get_hash(),
    }


# ── Memory Endpoints ──────────────────────────────────────────────────────────

@router.get("/memory")
async def get_memories(memory_type: str = "", limit: int = 20,
                       user: dict = Depends(require_auth)):
    """Get NAM's memories, optionally filtered by type."""
    query = {"memory_type": memory_type} if memory_type else None
    memories = await store.find_many("nam_memory", query=query, limit=limit)
    total = await store.count("nam_memory")
    return {"memories": memories, "total": total}


@router.post("/memory")
async def create_new_memory(body: MemoryCreate, user: dict = Depends(require_admin)):
    """Create a new memory for NAM."""
    memory = _create_memory(
        memory_type=body.memory_type,
        content=body.content,
        importance=body.importance,
        participants=body.participants,
    )
    memory["created_by"] = user.get("user_id", "unknown")
    await store.create("nam_memory", memory)
    return {"status": "created", "memory": memory}


@router.get("/autobiography")
async def get_autobiography(user: dict = Depends(require_auth)):
    """Get NAM's autobiographical events."""
    events = await store.find_many("nam_memory", query={"memory_type": "episodic"}, limit=100)
    return {"events": events, "total": len(events)}


# ── Intention / Prospective Memory Endpoints ──────────────────────────────────

@router.get("/intentions")
async def get_intentions(user: dict = Depends(require_auth)):
    """Get NAM's active intentions (prospective memory)."""
    intentions = await store.find_many("nam_intentions", limit=100)
    return {"intentions": intentions, "total": len(intentions)}


@router.post("/intentions")
async def create_new_intention(body: IntentionCreate, user: dict = Depends(require_admin)):
    """Create a new intention."""
    intention = _create_intention(
        objective=body.objective,
        target_date=body.target_date,
        dependencies=body.dependencies,
        owner=body.owner,
        leadership_context=body.leadership_context,
    )
    intention["created_by"] = user.get("user_id", "unknown")
    await store.create("nam_intentions", intention)
    return {"status": "created", "intention": intention}


@router.get("/intentions/drift")
async def check_drift(user: dict = Depends(require_auth)):
    """Detect drift between intentions and reality."""
    intentions = await store.find_many("nam_intentions")
    memories = await store.find_many("nam_memory")
    drifts = detect_drift(intentions, memories)
    return {"drifts": drifts, "total": len(drifts)}


# ── Dream Endpoints ───────────────────────────────────────────────────────────

@router.get("/dreams")
async def get_dreams(limit: int = 10, user: dict = Depends(require_auth)):
    """Get recent dreams."""
    dreams = await store.find_many("nam_dreams", limit=limit)
    total = await store.count("nam_dreams")
    return {"dreams": dreams, "total": total}


@router.post("/dream")
async def generate_new_dream(body: DreamRequest, user: dict = Depends(require_admin)):
    """Generate a new dream (async synthesis)."""
    memories = await store.find_many("nam_memory", limit=100)
    intentions = await store.find_many("nam_intentions", limit=50)

    inputs = assemble_dream_inputs(
        memories=memories,
        open_questions=body.open_questions,
        creative_ideas=body.creative_ideas,
        organizational_challenges=body.organizational_challenges,
        goals=[i for i in intentions if i.get("status") == "active"],
        recent_events=[m for m in memories if m.get("memory_type") == "episodic"][-10:],
    )
    dream = generate_dream(inputs)
    dream["generated_by"] = user.get("user_id", "unknown")
    await store.create("nam_dreams", dream)
    return dream


# ── Reflection Endpoints ──────────────────────────────────────────────────────

@router.get("/reflections")
async def get_reflections(limit: int = 10, user: dict = Depends(require_auth)):
    """Get recent reflections."""
    reflections = await store.find_many("nam_reflections", limit=limit)
    total = await store.count("nam_reflections")
    return {"reflections": reflections, "total": total}


@router.post("/reflect")
async def create_new_reflection(body: ReflectionCreate, user: dict = Depends(require_admin)):
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
    reflection["created_by"] = user.get("user_id", "unknown")
    await store.create("nam_reflections", reflection)

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
    await store.create("nam_memory", memory)

    return reflection


@router.get("/reflections/tensions")
async def check_constitutional_tensions(user: dict = Depends(require_auth)):
    """Check for constitutional tensions across reflections."""
    reflections = await store.find_many("nam_reflections", limit=100)
    tensions = generate_constitutional_tension(reflections)
    return tensions


# ── Leadership Endpoints ──────────────────────────────────────────────────────

@router.post("/leadership/review")
async def review_action(body: ActionReview, user: dict = Depends(require_auth)):
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
async def get_ledger(limit: int = 20, user: dict = Depends(require_auth)):
    """Get the leadership decision ledger."""
    ledger = await store.find_many("nam_ledger", limit=limit)
    total = await store.count("nam_ledger")
    return {"ledger": ledger, "total": total}


@router.post("/leadership/evaluate")
async def evaluate_and_log(body: ActionReview, user: dict = Depends(require_admin)):
    """Evaluate an action and log it in the leadership ledger."""
    action = {
        "description": body.description,
        "actor": body.actor,
        "purpose": body.purpose,
        "beneficiary": body.beneficiary,
    }
    evaluation = evaluate_action(action)
    entry = create_ledger_entry(evaluation)
    entry["evaluated_by"] = user.get("user_id", "unknown")
    await store.create("nam_ledger", entry)
    return {"evaluation": evaluation, "ledger_entry": entry}


# ── Jamil ↔ NAM Protocol Endpoints ────────────────────────────────────────────

@router.post("/jamil/review")
async def jamil_request_review(body: ActionReview, user: dict = Depends(require_auth)):
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
async def get_jamil_protocol(user: dict = Depends(require_auth)):
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
async def get_autonomy_level(action_type: str, user: dict = Depends(require_auth)):
    """Get the autonomy classification for an action type."""
    return classify_autonomy(action_type)


# ── Mission Alignment Endpoints ───────────────────────────────────────────────

@router.get("/mission/alignment")
async def get_mission_alignment(user: dict = Depends(require_auth)):
    """Get NAM's mission alignment criteria."""
    from ai.hybrid_nam.leadership_engine import MISSION_PRINCIPLES
    return {"principles": MISSION_PRINCIPLES}


@router.post("/mission/evaluate")
async def evaluate_mission_alignment(body: ActionReview, user: dict = Depends(require_auth)):
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
async def get_development(user: dict = Depends(require_auth)):
    """Get NAM's developmental status."""
    mem_count = await store.count("nam_memory")
    ref_count = await store.count("nam_reflections")
    dream_count = await store.count("nam_dreams")
    knowledge_count = await store.count("nam_knowledge")
    intention_count = await store.count("nam_intentions")
    ledger_count = await store.count("nam_ledger")

    return {
        "stage": soul.state.get("development_stage", {}),
        "event_count": mem_count,
        "reflection_count": ref_count,
        "dream_count": dream_count,
        "knowledge_count": knowledge_count,
        "intention_count": intention_count,
        "ledger_count": ledger_count,
    }


@router.post("/development/evaluate")
async def evaluate_development(user: dict = Depends(require_admin)):
    """Trigger a developmental self-assessment."""
    mem_count = await store.count("nam_memory")
    ref_count = await store.count("nam_reflections")
    knowledge_count = await store.count("nam_knowledge")
    dream_count = await store.count("nam_dreams")

    reflection = create_reflection(
        event={
            "type": "developmental_assessment",
            "description": "Periodic self-evaluation of NAM's developmental trajectory",
            "importance": 0.7,
        },
        expectation="NAM should show growth across knowledge, memory, and reflection",
        reality=f"NAM has {knowledge_count} knowledge items, {mem_count} memories, {ref_count} reflections, {dream_count} dreams",
    )
    reflection["created_by"] = user.get("user_id", "unknown")
    await store.create("nam_reflections", reflection)
    return reflection


# ── Escalation Endpoints ──────────────────────────────────────────────────────

@router.post("/escalate")
async def create_escalation(reason: str = "", severity: str = "advisory",
                            action: str = "", user: dict = Depends(require_auth)):
    """Create an escalation requiring human attention."""
    esc = escalate(reason=reason, severity=severity, context={}, original_action=action)
    esc["created_by"] = user.get("user_id", "unknown")
    await store.create("nam_escalations", esc)
    return esc


@router.get("/escalations")
async def get_escalations(user: dict = Depends(require_auth)):
    """Get open escalations."""
    escalations = await store.find_many("nam_escalations", query={"status": "open"})
    return {"escalations": escalations, "total": len(escalations)}


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_esc(escalation_id: str, resolved_by: str = "NAM Oshun",
                      resolution: str = "", approved: bool = True,
                      user: dict = Depends(require_admin)):
    """Resolve an escalation."""
    esc = await store.find_one("nam_escalations", {"escalation_id": escalation_id})
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    resolved = resolve_escalation(esc, resolved_by, resolution, approved)
    await store.update_one("nam_escalations", {"escalation_id": escalation_id}, resolved)
    return resolved
