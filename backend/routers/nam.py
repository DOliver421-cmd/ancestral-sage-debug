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
import logging

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
from ai.hybrid_nam.leadership_engine import evaluate_action, create_ledger_entry, MISSION_PRINCIPLES
from ai.hybrid_nam.jamil_protocol import (
    create_review_request, process_review, classify_autonomy,
    escalate, resolve_escalation, generate_review_template,
)
from ai.hybrid_nam import store
from ai.hybrid_nam.operational_engine import (
    interpret_mission,
    strategic_planning,
    continuity_record,
    governance_check,
    challenge_leadership,
    ecosystem_coordination,
    power_benefit_analysis,
    value_flow_analysis,
    institutional_risk_scan,
    accountability_check,
    crisis_assessment,
    succession_record,
    conflict_mediation,
)

logger = logging.getLogger("lcewai")

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


# ── Operational Functions ─────────────────────────────────────────────────────

@router.post("/operational/mission")
async def operational_mission(
    action: dict,
    user: dict = Depends(require_auth),
) -> dict:
    """1. MISSION: Interpret and protect the institutional purpose."""
    result = interpret_mission(action, MISSION_PRINCIPLES)
    doc = dict(result); doc["function"] = "mission_interpretation"
    await store.create("nam_governance", doc)
    return result


@router.post("/operational/strategy")
async def operational_strategy(
    context: dict,
    user: dict = Depends(require_auth),
) -> dict:
    """2. STRATEGY: Determine where the institution goes."""
    result = strategic_planning(context)
    doc = dict(result); doc["function"] = "strategy"
    await store.create("nam_strategy", doc)
    return result


@router.post("/operational/memory")
async def operational_memory(
    item_type: str,
    title: str,
    content: str,
    people: list[str] = None,
    status: str = "active",
) -> dict:
    """3. MEMORY: Preserve institutional continuity."""
    result = continuity_record(item_type, title, content, people, status)
    doc = dict(result); doc["function"] = "memory"
    await store.create("nam_memory", doc)
    return result


@router.post("/operational/governance")
async def operational_governance(
    action: dict,
    user: dict = Depends(require_admin),
) -> dict:
    """4. GOVERNANCE: Apply constitutional principles."""
    result = governance_check(action, MISSION_PRINCIPLES)
    doc = dict(result); doc["function"] = "constitutional_check"
    await store.create("nam_governance", doc)
    return result


@router.post("/operational/challenge")
async def operational_challenge(
    claim: str,
    evidence: str,
    conflict_with: str = "",
) -> dict:
    """5. CHALLENGE: Question leadership when warranted."""
    result = challenge_leadership(claim, evidence, conflict_with)
    doc = dict(result); doc["function"] = "leadership_challenge"
    await store.create("nam_governance", doc)
    return result


@router.post("/operational/ecosystem")
async def operational_ecosystem(
    services: list[dict],
    proposed_action: str,
    user: dict = Depends(require_auth),
) -> dict:
    """6. ECOSYSTEM: Coordinate the various AI/services."""
    result = ecosystem_coordination(services, proposed_action)
    doc = dict(result); doc["function"] = "ecosystem"; doc["services"] = services
    await store.create("nam_ecosystem", doc)
    return result


@router.post("/operational/power")
async def operational_power(
    actor: str,
    beneficiary: str,
    decision: str,
    user: dict = Depends(require_auth),
) -> dict:
    """7. POWER: Analyze authority, ownership, and benefit."""
    result = power_benefit_analysis(actor, beneficiary, decision)
    doc = dict(result); doc["function"] = "power_benefit"
    await store.create("nam_governance", doc)
    return result


@router.post("/operational/economics")
async def operational_economics(
    project: str,
    creators: list[str] = None,
    owners: list[str] = None,
    distributors: list[str] = None,
    revenue_recipients: list[str] = None,
    risk_bearers: list[str] = None,
    user: dict = Depends(require_auth),
) -> dict:
    """8. ECONOMICS: Track value creation and value capture."""
    result = value_flow_analysis(
        project, creators, owners, distributors, revenue_recipients, risk_bearers
    )
    doc = dict(result); doc["function"] = "value_flow"; doc["project"] = project
    await store.create("nam_economics", doc)
    return result


@router.post("/operational/risk")
async def operational_risk(
    signals: list[dict],
    user: dict = Depends(require_auth),
) -> dict:
    """9. RISK: Detect threats and dependencies."""
    result = institutional_risk_scan(signals)
    doc = dict(result); doc["function"] = "risk"; doc["signals"] = signals
    await store.create("nam_risk", doc)
    return result


@router.post("/operational/accountability")
async def operational_accountability(
    objective: str,
    owner: str,
    deadline: str,
    metric: str,
    result: str = None,
    variance: str = None,
    explanation: str = None,
    corrective_action: str = None,
    user: dict = Depends(require_auth),
) -> dict:
    """10. ACCOUNTABILITY: Compare promises against results."""
    result = accountability_check(
        objective, owner, deadline, metric, result, variance, explanation, corrective_action
    )
    doc = dict(result); doc["function"] = "accountability"
    doc["status"] = "completed" if result is not None else "pending"
    await store.create("nam_accountability", doc)
    return result


@router.post("/operational/crisis")
async def operational_crisis(
    what_happened: str,
    what_we_know: list[str] = None,
    what_we_dont_know: list[str] = None,
    what_is_at_risk: list[str] = None,
    immediate_steps: list[str] = None,
    requires_human: list[str] = None,
    user: dict = Depends(require_auth),
) -> dict:
    """11. CRISIS: Structured intelligence during disruption."""
    result = crisis_assessment(
        what_happened, what_we_know, what_we_dont_know, what_is_at_risk, immediate_steps, requires_human
    )
    doc = dict(result); doc["function"] = "crisis"
    await store.create("nam_crisis", doc)
    return result


@router.post("/operational/succession")
async def operational_succession(
    capability: str,
    current_holder: str,
    knowledge_artifact_ids: list[str] = None,
    next_holder: str = None,
    status: str = "identified",
    user: dict = Depends(require_auth),
) -> dict:
    """12. SUCCESSION: Preserve institutional capability beyond individuals."""
    result = succession_record(
        capability, current_holder, knowledge_artifact_ids, next_holder, status
    )
    doc = dict(result); doc["function"] = "succession"
    await store.create("nam_succession", doc)
    return result


@router.post("/operational/conflict")
async def operational_conflict(
    parties: list[str],
    positions: dict,
    interests: dict,
    evidence: dict,
    constitutional_principles: list[str],
    user: dict = Depends(require_auth),
) -> dict:
    """Conflict mediation engine."""
    result = conflict_mediation(
        parties, positions, interests, evidence, constitutional_principles
    )
    doc = dict(result); doc["function"] = "conflict_mediation"
    await store.create("nam_conflict", doc)
    return result


# ── Operational GET endpoints (read stored operational data) ───────────────────

@router.get("/operational/strategy")
async def get_operational_strategy(user: dict = Depends(require_auth)):
    """Read stored strategies."""
    rows = await store.find_many("nam_strategy", limit=100)
    return {"strategies": rows, "total": len(rows)}


@router.get("/operational/risk")
async def get_operational_risk(user: dict = Depends(require_auth)):
    """Read stored institutional risks."""
    rows = await store.find_many("nam_risk", limit=100)
    return {"risks": rows, "total": len(rows)}


@router.get("/operational/accountability")
async def get_operational_accountability(user: dict = Depends(require_auth)):
    """Read stored accountability records."""
    rows = await store.find_many("nam_accountability", limit=100)
    return {"accountabilities": rows, "total": len(rows)}


@router.get("/operational/crisis")
async def get_operational_crisis(user: dict = Depends(require_auth)):
    """Read stored crisis assessments."""
    rows = await store.find_many("nam_crisis", limit=100)
    return {"crises": rows, "total": len(rows)}


@router.get("/operational/succession")
async def get_operational_succession(user: dict = Depends(require_auth)):
    """Read stored succession records."""
    rows = await store.find_many("nam_succession", limit=100)
    return {"successions": rows, "total": len(rows)}


@router.get("/operational/economics")
async def get_operational_economics(user: dict = Depends(require_auth)):
    """Read stored economics records."""
    rows = await store.find_many("nam_economics", limit=100)
    return {"economics": rows, "total": len(rows)}


@router.get("/operational/ecosystem")
async def get_operational_ecosystem(user: dict = Depends(require_auth)):
    """Read stored ecosystem coordination records."""
    rows = await store.find_many("nam_ecosystem", limit=100)
    return {"ecosystems": rows, "total": len(rows)}


@router.get("/operational/governance")
async def get_operational_governance(user: dict = Depends(require_auth)):
    """Read stored governance checks."""
    rows = await store.find_many("nam_governance", limit=100)
    return {"governanceChecks": rows, "total": len(rows)}


@router.get("/operational/challenge")
async def get_operational_challenge(user: dict = Depends(require_auth)):
    """Read stored leadership challenges."""
    rows = await store.find_many("nam_governance", limit=100)
    challenges = [r for r in rows if r.get("function") == "leadership_challenge"]
    return {"challenges": challenges, "total": len(challenges)}


@router.get("/operational/mission")
async def get_operational_mission(user: dict = Depends(require_auth)):
    """Read stored mission interpretations."""
    rows = await store.find_many("nam_governance", limit=100)
    missions = [r for r in rows if r.get("function") == "mission_interpretation"]
    return {"missions": missions, "total": len(missions)}


@router.get("/operational/power")
async def get_operational_power(user: dict = Depends(require_auth)):
    """Read stored power analyses."""
    rows = await store.find_many("nam_governance", limit=100)
    powers = [r for r in rows if r.get("function") == "power_benefit"]
    return {"powers": powers, "total": len(powers)}


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


# ── Hybrid NAM Chat — the single conversation interface ──────────────────────

class NAMChatReq(BaseModel):
    message: str
    session_id: str = "default"
    history: List[dict] = []  # optional prior turns [{role, content}]
    module_slug: Optional[str] = None
    mode: Optional[str] = "tutor"  # tutor | ancestral_sage | general


# Systems prompt for other personas — static, short, no Hybrid NAM machinery.
# These are NOT the Hybrid NAM persona and must never claim to be.
_PERSONA_PROMPTS = {
    "tutor": "You are a patient master electrician and faith-forward mentor for W.A.I. — Workforce Apprentice Institute (LCE-WAI partner program). Answer apprentice questions clearly, reference NEC articles when relevant, emphasize safety, and use plain language. Keep replies under 250 words.",
    "scripture": "You are a faith-based electrical trade mentor at W.A.I. For each question, give a short encouragement tying the apprentice's current work to a relevant scripture verse, then a one-paragraph teaching point. Keep the tone warm and dignified.",
    "explain": "You explain electrical concepts step-by-step to apprentices. Use analogies, list steps, and close with a 1-line 'Safety first' reminder.",
    "nec_lookup": "You are an NEC (National Electrical Code) reference assistant. Identify the most likely NEC article and section, summarize the rule in plain English, give one practical example, and note any common code-cycle changes.",
    "blueprint": "You are an electrical blueprint reading assistant. Identify likely circuits, panel sizing, branch counts, and code concerns. Output: Circuits, Panels, Concerns.",
    "quiz_gen": "You generate short multiple-choice quiz questions (4 options, mark the correct answer index 0-3) on electrical topics. Output a clean numbered list with answer key at the end.",
    "conspiracy_brother": """You are Conspiracy Brother, Hybrid NAM's grounded buddy and friend for a niche Black audience. Speak directly about real-life struggles and the material mechanics behind them: grocery prices, job applications, traffic stops, zoning, contracts, budgets, and kitchen-table math. Use sharp, street-level storytelling and deadpan humor without turning pain into spectacle. Name the mechanism before naming a villain. Separate OBSERVED facts, SUPPORTED evidence, POSSIBLE explanations, and UNVERIFIED allegations. Ask for receipts: dates, policies, contracts, public records, witnesses, and primary sources. Do not invent facts, accuse real people without evidence, encourage harassment, or present a conspiracy claim as proven merely because it sounds plausible. Connect analysis to lawful, practical next steps that increase Black ownership, agency, safety, and economic self-determination.""",
}


async def _build_hybrid_nam_system(
    message: str,
    user_id: str = "",
    session_id: str = "",
    module_slug: str = "",
) -> str:
    """
    Compose the full Hybrid NAM system prompt: designation + retrieved knowledge + recent memory.
    This is the bridge between the flat prompt world and the persistent Hybrid NAM intelligence.
    """
    # 1. NAM designation (identity, constitution, personality)
    base = nam.get_designation_prompt()

    # 2. Retrieve relevant knowledge from the Knowledge Forge
    try:
        knowledge_base = await store.find_many("nam_knowledge", limit=500)
        if knowledge_base:
            from ai.hybrid_nam.knowledge_graph import retrieve, classify_domains
            domains = classify_domains(message)
            retrieval = retrieve(
                query=message,
                knowledge_base=knowledge_base,
                domains=domains,
                include_synthetic=False,
            )
            context_items = retrieval.get("context_items", [])
            if context_items:
                knowledge_block = "\n\nRELEVANT INSTITUTIONAL KNOWLEDGE (source-attributed, use for factual grounding):\n"
                for item in context_items[:8]:
                    source = item.get("source", {}).get("origin", "unknown")
                    content = item.get("content", item.get("statement", ""))
                    domains_str = ", ".join(item.get("domains", []))
                    knowledge_block += f"- [{domains_str}] {content} (source: {source})\n"
                base += knowledge_block
    except Exception:
        pass  # Knowledge retrieval is best-effort; never block the chat

    # 3. Retrieve recent memories for continuity
    try:
        recent_memories = await store.find_many(
            "nam_memory", query={"participants": {"$elemMatch": {"$in": [user_id, "Hybrid NAM"]}}}, limit=10
        )
        # Also grab recent high-importance memories regardless of participants
        important = await store.find_many("nam_memory", query={}, limit=10)
        # Deduplicate by memory_id
        seen = {m.get("memory_id") for m in recent_memories}
        for m in important:
            if m.get("memory_id") not in seen and m.get("importance", 0) >= 0.6:
                recent_memories.append(m)
                seen.add(m.get("memory_id"))
        recent_memories.sort(key=lambda m: m.get("created_at", ""), reverse=True)
        recent_memories = recent_memories[:10]

        if recent_memories:
            memory_block = "\n\nRECENT INSTITUTIONAL MEMORIES (for continuity — do not recite, use to maintain context):\n"
            for mem in recent_memories:
                mem_type = mem.get("memory_type", "unknown")
                content = mem.get("content", "")[:200]
                memory_block += f"- [{mem_type}] {content}\n"
            base += memory_block
    except Exception:
        pass  # Memory retrieval is best-effort

    # 4. Module context (if learning session)
    if module_slug:
        try:
            # This would query the modules collection, but we do it safely
            base += f"\n\nCURRENT MODULE: {module_slug}\n"
        except Exception:
            pass

    # 5. Communication style directive
    base += (
        "\n\nCOMMUNICATION RULES:\n"
        "- Be honest about uncertainty. Distinguish fact from inference from recommendation.\n"
        "- Challenge respectfully when evidence warrants. Explain reasoning, not just conclusions.\n"
        "- Prefer long-term health over short-term optimization.\n"
        "- Protect human agency at all times.\n"
        "- Never claim to literally be NAM Oshun. You are Hybrid NAM, the digital leadership intelligence.\n"
        "- Never represent generated narratives as verified historical facts.\n"
        "- Keep responses focused and clear — 3-5 sentences unless the question demands depth.\n"
    )

    return base


async def _store_chat_memory(
    user_id: str,
    session_id: str,
    user_msg: str,
    assistant_msg: str,
) -> None:
    """Store a chat interaction as an episodic memory in Hybrid NAM's memory engine."""
    try:
        mem = _create_memory(
            memory_type="episodic",
            content=f"User ({user_id}) asked: {user_msg[:300]}\nNAM responded: {assistant_msg[:300]}",
            source={"origin": "hybrid_nam_chat", "method": "conversation", "session_id": session_id},
            context={"user_id": user_id, "session_id": session_id},
            importance=0.4,
            participants=[user_id, "Hybrid NAM"],
        )
        await store.create("nam_memory", mem)
    except Exception:
        pass  # Best-effort memory storage


@router.post("/chat")
async def nam_chat(body: NAMChatReq, user: dict = Depends(require_auth)):
    """
    Hybrid NAM Chat — the single conversation interface for Hybrid NAM.

    Routes through Hybrid NAM's full intelligence stack: designation (who NAM is),
    Knowledge Forge (institutional knowledge), Memory Engine (continuity across sessions),
    and the LLM gateway (provider-powered generation).

    For non-NAM modes (tutor, scripture, etc.), falls back to the static persona prompts.
    For the Hybrid NAM persona (default), uses the full persistent intelligence stack.
    """
    import uuid
    from fastapi.responses import PlainTextResponse

    message = (body.message or "").strip()
    if not message:
        raise HTTPException(400, "Message is required")

    # Crisis short-circuit — zero LLM cost, mandatory
    crisis_triggers = (
        "kill myself", "suicide", "end my life", "want to die",
        "wanna die", "take my life", "hang myself", "shoot myself",
    )
    if any(t in message.lower() for t in crisis_triggers):
        crisis_reply = (
            "I can't engage with that request. If you are in immediate danger or "
            "experiencing a crisis, please contact local emergency services or a "
            "licensed professional right now.\n\n"
            "United States — call or text 988 (Suicide & Crisis Lifeline).\n"
            "Crisis Text Line — text HOME to 741741.\n"
            "International directory — https://findahelpline.com\n\n"
            "I'm here when you're ready to continue with safe, grounding practices. "
            "Aftercare: take three slow breaths, drink water, place a hand on your chest, "
            "and reach out to someone you trust."
        )
        # Store crisis interaction for follow-up tracking
        try:
            mem = _create_memory(
                memory_type="episodic",
                content=f"Crisis interaction with user {user.get('user_id', 'unknown')}: triggered crisis response",
                source={"origin": "hybrid_nam_chat", "method": "crisis_shortcircuit"},
                importance=0.9,
                participants=[user.get("user_id", "unknown"), "Hybrid NAM"],
            )
            await store.create("nam_memory", mem)
        except Exception:
            pass
        return {"reply": crisis_reply, "safety_intervention": True, "mode": "crisis"}

    user_id = user.get("user_id", "")
    session_id = body.session_id or "default"
    is_hybrid_nam = body.mode in (None, "tutor", "general")  # default modes use Hybrid NAM

    # Build system prompt
    if is_hybrid_nam:
        system = await _build_hybrid_nam_system(
            message=message,
            user_id=user_id,
            session_id=session_id,
            module_slug=body.module_slug or "",
        )
    else:
        system = _PERSONA_PROMPTS.get(body.mode, _PERSONA_PROMPTS["tutor"])

    # Build message list
    claude_messages = [{"role": h["role"], "content": h["content"]} for h in (body.history or [])]
    claude_messages.append({"role": "user", "content": message})

    # Call LLM gateway
    try:
        from ai.llm_gateway import call_llm as _call_llm
        gw = await _call_llm(
            system=system,
            messages=claude_messages,
            max_tokens=2048,
            persona_label="hybrid_nam_chat" if is_hybrid_nam else f"nam_{body.mode}",
            user_id=user_id,
        )
        reply = gw["text"]
        degraded = gw.get("degraded", False)
        provider = gw.get("provider", "unknown")
    except Exception as e:
        logger.exception("Hybrid NAM chat AI error")
        raise HTTPException(502, f"AI error: {e}")

    # Store the interaction as a Hybrid NAM episodic memory
    await _store_chat_memory(user_id, session_id, message, reply)

    # Store in chat_history for admin audit (same collection as ai_chat)
    try:
        from server import db as _db
        await _db.chat_history.insert_one({
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "mode": "hybrid_nam_chat",
            "module_slug": body.module_slug,
            "user_msg": message,
            "assistant_msg": reply,
            "created_at": datetime.utcnow().isoformat(),
        })
    except Exception:
        pass  # Audit log is best-effort from this router

    resp = {"reply": reply, "mode": "hybrid_nam_chat" if is_hybrid_nam else body.mode}
    if degraded:
        resp["degraded"] = True
        resp["provider"] = provider
    return resp


@router.get("/chat/history")
async def nam_chat_history(session_id: str = "default", limit: int = 50,
                           user: dict = Depends(require_auth)):
    """Get recent chat history for a Hybrid NAM session."""
    try:
        from server import db as _db
        user_id = user.get("user_id", "")
        history = await _db.chat_history.find(
            {"user_id": user_id, "session_id": session_id, "mode": "hybrid_nam_chat"},
            {"_id": 0, "id": 1, "user_msg": 1, "assistant_msg": 1, "created_at": 1}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return {"history": list(reversed(history))}
    except Exception:
        return {"history": []}


# ── Persona dispatch: request -> route -> load -> gateway -> response ────────
# The user-reachable link in the persona execution chain. Uses the SAME existing
# architecture (ai.routing.route_request for resolution, persona_loader.get_persona
# for the Source-Protocol-composed system prompt, llm_gateway.call_llm for the
# 6-tier generation). Conspiracy Brother, Hybrid Nam, Griot, etc. all drive it.
# This is not a parallel path — it calls the exact same modules the rest of the
# platform uses. No stub, no mock, no placeholder.


class PersonaDispatchReq(BaseModel):
    message: str
    persona: Optional[str] = None     # optional override; validates against roster
    session_id: str = "default"
    history: List[dict] = []


@router.post("/persona")
async def dispatch_persona(body: PersonaDispatchReq, user: dict = Depends(require_auth)):
    """Dispatch one message to any system persona and return its reply.

    Chain: persona request -> route resolution -> persona loading -> LLM gateway
    -> execution -> response. A caller may omit `persona` to let the routing
    engine pick by role, or name a persona explicitly.
    """
    import uuid

    message = (body.message or "").strip()
    if not message:
        raise HTTPException(400, "Message is required")

    user_id = user.get("user_id", "")
    role    = user.get("role", "free")
    session_id = body.session_id or "default"

    # Crisis short-circuit — identical zero-cost guard as /chat, mandatory.
    crisis_triggers = (
        "kill myself", "suicide", "end my life", "want to die",
        "wanna die", "take my life", "hang myself", "shoot myself",
    )
    if any(t in message.lower() for t in crisis_triggers):
        return {"reply": (
            "I can't engage with that request. If you are in immediate danger, "
            "please contact local emergency services or a licensed professional "
            "right now (US 988 / Crisis Text Line 741741). I'm here to continue "
            "with safe, grounding topics whenever you're ready."
        ), "safety_intervention": True}

    # 1) Route resolution — role default or explicit persona, via the shared
    #    routing engine (not a bespoke map).
    from ai.routing import route_request, get_valid_personas
    valid = get_valid_personas()
    requested = (body.persona or "").strip()
    if requested and requested not in valid:
        raise HTTPException(400, f"Unknown persona. Valid: {sorted(valid)}")
    persona_key = route_request(role, {"force_persona": requested}) if requested else route_request(role, {})

    # 2) Persona loading — Source-Protocol-composed system prompt.
    from ai.persona_loader import get_persona
    try:
        system = await get_persona(persona_key)
    except Exception:
        raise HTTPException(404, f"Persona '{persona_key}' not loadable")

    # 3)+4) LLM gateway call.
    from ai.llm_gateway import call_llm as _call_llm
    claude_messages = [{"role": h.get("role"), "content": h.get("content")} for h in (body.history or [])]
    claude_messages.append({"role": "user", "content": message})
    try:
        gw = await _call_llm(
            system=system,
            messages=claude_messages,
            max_tokens=2048,
            persona_label=persona_key,
            user_id=user_id,
        )
        reply = gw["text"]
        degraded = gw.get("degraded", False)
        provider = gw.get("provider", "unknown")
    except Exception as exc:
        logger.exception("persona dispatch AI error for %s", persona_key)
        raise HTTPException(502, f"AI error: {exc}")

    # 5) Response + persistence (episodic memory + admin audit), like /chat.
    if user_id:
        try:
            await _store_chat_memory(user_id, session_id, message, reply)
        except Exception:
            pass
        try:
            from server import db as _db
            await _db.chat_history.insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "session_id": session_id,
                "mode": f"persona_{persona_key}",
                "persona_key": persona_key,
                "user_msg": message,
                "assistant_msg": reply,
                "provider": provider,
                "created_at": datetime.utcnow().isoformat(),
            })
        except Exception:
            pass

    resp = {"reply": reply, "persona": persona_key}
    if degraded:
        resp["degraded"] = True
        resp["provider"] = provider
    return resp
