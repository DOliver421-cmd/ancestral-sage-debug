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
        mem = create_memory(
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
            mem = create_memory(
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
