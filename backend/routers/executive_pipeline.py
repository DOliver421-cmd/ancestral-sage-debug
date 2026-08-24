"""
executive_pipeline.py — Executive Workflow Suite backend.

One pipeline. Every stage shares context. Nothing is isolated.

Stages:
  1. INTAKE     — task/project creation (Arena, brief, competitive analysis)
  2. ASSIGN     — Jamil coordinates, assigns personas, breaks into sub-tasks
  3. EXECUTE    — personas produce deliverables (content, art, strategy, code)
  4. REVIEW     — Source Protocol ensures mission alignment, Sage approves
  5. OPERATE    — Business Office tracks costs, Ops handles distribution
  6. DELIVER    — final output, reporting, archive

Context flows forward at every stage. The next stage always sees what the
previous stage produced. The owner (executive_admin) oversees the whole thing
and can approve, reject, or redirect at any point.

Collections:
  exec_projects — the project record (brief, status, stage, context, deliverables)
  exec_comments — threaded discussion per project
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field
from bson import ObjectId

router = APIRouter(prefix="/api/executive", tags=["executive-pipeline"])

# Module-level references set by bind()
_db = None
_current_user = None
_audit = None

def bind(db, current_user=None, audit=None):
    """Bind database and dependencies (called by server.py at startup)."""
    global _db, _current_user, _audit
    _db = db
    _current_user = current_user
    _audit = audit


# ── Auth (reuse ABO pattern) ────────────────────────────────────────────────

class User(BaseModel):
    id: str
    role: str
    full_name: str = ""

def _require_rank(*roles):
    """Dependency factory: user must have one of the listed roles."""
    async def dep(request: Request, authorization: Optional[str] = Header(None)) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        token = authorization.split(" ", 1)[1]
        try:
            import jwt
            payload = jwt.decode(token, request.app.state.jwt_secret, algorithms=["HS256"])
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await request.app.state.db.users.find_one({"_id": ObjectId(payload.get("sub", ""))})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user_role = user.get("role", "student")
        ROLE_RANK = {"student": 1, "trial_pass": 2, "instructor": 3, "support_staff": 4,
                      "oversight": 5, "admin": 6, "executive_admin": 7}
        needed = min(ROLE_RANK.get(r, 0) for r in roles)
        if ROLE_RANK.get(user_role, 0) < needed:
            raise HTTPException(status_code=403, detail=f"Requires {roles}")
        return User(id=str(user["_id"]), role=user_role, full_name=user.get("full_name", ""))
    return dep


# ── Stage definitions ────────────────────────────────────────────────────────

STAGES = ["intake", "assign", "execute", "review", "operate", "deliver"]

STAGE_META = {
    "intake":  {"label": "Intake",    "icon": "🎯", "desc": "Brief, competitive analysis, project creation"},
    "assign":  {"label": "Assign",    "icon": "👥", "desc": "Jamil coordinates, assigns personas, breaks into sub-tasks"},
    "execute": {"label": "Execute",   "icon": "⚡", "desc": "Personas produce deliverables"},
    "review":  {"label": "Review",    "icon": "🛡️", "desc": "Source Protocol alignment, Sage approval"},
    "operate": {"label": "Operate",   "icon": "📊", "desc": "Business Office tracks costs, Ops handles distribution"},
    "deliver": {"label": "Deliver",   "icon": "✅", "desc": "Final output, reporting, archive"},
}

STAGE_RANK = {s: i for i, s in enumerate(STAGES)}


# ── Models ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    title: str
    brief: str
    project_type: str = "general"  # general, release, campaign, content, course
    priority: str = "normal"       # low, normal, high, urgent
    assignees: List[str] = []      # persona names to pre-assign

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    brief: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None   # active, paused, completed, archived

class ProjectPacket(BaseModel):
    """The standardized project packet — the operating agreement between the
    owner and the AI team. Every substantial project carries one.

    Authority levels (three kinds of AI work):
      autonomous          — AI completes without asking
      approval_required   — AI prepares everything, owner approves the result
      human_only          — AI can prepare and advise but cannot execute
    """
    objective: str = ""
    owner: str = ""
    ai_team: List[str] = []
    deliverables_summary: str = ""
    constraints: str = ""
    authority: str = "approval_required"
    approval_points: List[str] = []
    evidence: str = ""
    outcome_report: str = ""
    packet_status: str = "planning"  # planning | active | review | approved | published | complete

class StageTransition(BaseModel):
    """Move a project to the next stage (or a specific stage)."""
    target_stage: Optional[str] = None  # None = advance to next
    context: dict = {}                  # data to pass forward
    notes: str = ""

class DeliverableSubmit(BaseModel):
    stage: str
    persona: str
    title: str
    content_type: str = "text"   # text, image, audio, video, code, document, mixed
    content: str = ""            # text content or description
    file_refs: List[str] = []    # GridFS file IDs or URLs
    metadata: dict = {}          # arbitrary extra data (duration, dimensions, etc.)

class CommentCreate(BaseModel):
    text: str
    persona: Optional[str] = None  # if commenting as a persona, not as the human

class ApprovalAction(BaseModel):
    action: str  # approve, reject, request_revision
    notes: str = ""
    target_stage: Optional[str] = None  # where to send back on revision


# ── Helpers ──────────────────────────────────────────────────────────────────

def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

def _serialize(doc: dict) -> dict:
    """Convert MongoDB doc to JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    if "owner_id" in doc:
        doc["owner_id"] = str(doc["owner_id"])
    for d in doc.get("deliverables", []):
        if "_id" in d:
            d["id"] = str(d["_id"])
    return doc

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── PROJECTS ─────────────────────────────────────────────────────────────────

@router.get("/projects")
async def list_projects(
    user: User = Depends(_require_rank("admin", "executive_admin")),
    status: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    request: Request = None,
):
    """List all executive pipeline projects."""
    db = request.app.state.db
    q = {}
    if status:
        q["status"] = status
    if stage:
        q["current_stage"] = stage
    docs = await db.exec_projects.find(q).sort("updated_at", -1).limit(limit).to_list(length=limit)
    return [_serialize(d) for d in docs]


@router.post("/projects")
async def create_project(
    body: ProjectCreate,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Create a new project in the pipeline. Starts at 'intake'."""
    db = request.app.state.db
    now = _now()
    doc = {
        "title": body.title,
        "brief": body.brief,
        "project_type": body.project_type,
        "priority": body.priority,
        "status": "active",
        "current_stage": "intake",
        "stage_history": [{"stage": "intake", "entered_at": now, "entered_by": user.id}],
        "context": {"brief": body.brief, "created_by": user.full_name or user.id},
        "deliverables": [],
        "approvals": [],
        "assignees": body.assignees,
        "owner_id": user.id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.exec_projects.insert_one(doc)
    doc["_id"] = result.inserted_id

    # Log to audit
    try:
        await db.audit_log.insert_one({
            "action": "exec_project_created",
            "project_id": str(result.inserted_id),
            "title": body.title,
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass

    return _serialize(doc)


@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Get full project with all stages, deliverables, and context."""
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    return _serialize(doc)


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Update project metadata (title, brief, priority, status)."""
    db = request.app.state.db
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    updates["updated_at"] = _now()
    result = await db.exec_projects.update_one({"_id": _oid(project_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    return _serialize(doc)


# ── PROJECT PACKET ──────────────────────────────────────────────────────────

@router.put("/projects/{project_id}/packet")
async def update_project_packet(
    project_id: str,
    body: ProjectPacket,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Set the standardized project packet (objective, authority, approval
    points, constraints, evidence, outcome report, status). The packet is the
    operating agreement between the owner and the AI team.
    """
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    packet = body.model_dump()
    packet["updated_at"] = _now()
    await db.exec_projects.update_one(
        {"_id": _oid(project_id)},
        {"$set": {"packet": packet, "updated_at": _now()}}
    )
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    return _serialize(doc)


# ── PROJECT DISCOVERY — turn what already exists into what comes next ────────
# Scans authorized existing material (published media products, pipeline
# deliverables, sellable tracks) and proposes the highest-value next projects.

@router.get("/discovery")
async def project_discovery(
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    db = request.app.state.db
    inventory = {"products": [], "deliverables": [], "tracks": []}

    try:
        products = await db.media_products.find(
            {"published": True}, {"_id": 0, "id": 1, "title": 1, "type": 1, "owner_name": 1, "price_cents": 1}
        ).sort("created_at", -1).to_list(200)
        inventory["products"] = products
    except Exception:
        pass
    try:
        projects = await db.exec_projects.find(
            {"status": {"$ne": "archived"}}, {"_id": 0, "title": 1, "deliverables": 1}
        ).to_list(100)
        for p in projects:
            inventory["deliverables"].extend([
                {"project": p.get("title", ""), "title": d.get("title", ""), "content_type": d.get("content_type", "")}
                for d in (p.get("deliverables") or [])
            ])
    except Exception:
        pass
    try:
        tracks = await db.media_products.find(
            {"type": {"$in": ["audio", "track", "music"]}}, {"_id": 0, "id": 1, "title": 1, "owner_name": 1, "price_cents": 1}
        ).to_list(200)
        inventory["tracks"] = tracks
    except Exception:
        pass

    audio_count = len(inventory["tracks"])
    product_count = len(inventory["products"])
    deliverable_count = len(inventory["deliverables"])
    total_assets = audio_count + product_count + deliverable_count

    proposals = []
    if audio_count >= 1:
        proposals.append({
            "kind": "distribution",
            "title": f"Catalog distribution — {audio_count} audio product{'s' if audio_count != 1 else ''}",
            "rationale": "Existing finished audio is sitting unreleased or under-distributed. Package, promote, and push to the store.",
            "suggested_team": ["Production", "Creative Partner", "Marketing"],
            "authority": "approval_required",
            "brief": f"Turn the existing catalog ({audio_count} audio products) into a release campaign: metadata, artwork, promotional package, and store push.",
        })
    if product_count >= 3:
        proposals.append({
            "kind": "catalog",
            "title": f"Catalog organization — {product_count} published products",
            "rationale": "A growing published catalog needs structure, consistent metadata, and a discovery path.",
            "suggested_team": ["Operations", "Analytics"],
            "authority": "autonomous",
            "brief": f"Audit the {product_count} published products, normalize metadata, and propose a catalog structure.",
        })
    if deliverable_count >= 3:
        proposals.append({
            "kind": "deliverables",
            "title": f"Pipeline harvest — {deliverable_count} completed deliverables",
            "rationale": "Completed AI-team deliverables across projects deserve review, approval, and release.",
            "suggested_team": ["Review", "Source"],
            "authority": "human_only",
            "brief": f"Review the {deliverable_count} pipeline deliverables, recommend approvals, and schedule release.",
        })
    if total_assets == 0:
        proposals.append({
            "kind": "start",
            "title": "Start with a goal",
            "rationale": "No existing material to catalogue yet. Give the AI team a goal and a brief.",
            "suggested_team": ["Jamil", "Hybrid NAM"],
            "authority": "approval_required",
            "brief": "Describe the outcome you want and the AI team will build the work plan.",
        })

    return {
        "assets": {
            "total": total_assets,
            "audio_products": audio_count,
            "published_products": product_count,
            "pipeline_deliverables": deliverable_count,
        },
        "inventory": inventory,
        "proposals": proposals,
        "scanned_at": _now(),
    }


# ── STAGE TRANSITIONS ───────────────────────────────────────────────────────

@router.post("/projects/{project_id}/advance")
async def advance_stage(
    project_id: str,
    body: StageTransition,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Advance project to the next stage (or specific target). Context flows forward."""
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    current = doc["current_stage"]
    if body.target_stage:
        target = body.target_stage
        if target not in STAGE_RANK:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {target}")
    else:
        idx = STAGE_RANK.get(current, 0)
        if idx >= len(STAGES) - 1:
            raise HTTPException(status_code=400, detail="Project already at final stage")
        target = STAGES[idx + 1]

    now = _now()

    # Merge context: new context overrides, old context preserved
    new_context = {**doc.get("context", {}), **body.context}
    new_context[f"_stage_{current}_completed_at"] = now
    if body.notes:
        new_context[f"_stage_{current}_notes"] = body.notes

    # Update project
    stage_history = doc.get("stage_history", [])
    stage_history.append({
        "stage": target,
        "entered_at": now,
        "entered_by": user.id,
        "from_stage": current,
        "context_snapshot_keys": list(body.context.keys()),
    })

    await db.exec_projects.update_one(
        {"_id": _oid(project_id)},
        {"$set": {
            "current_stage": target,
            "context": new_context,
            "stage_history": stage_history,
            "updated_at": now,
        }}
    )

    # Audit
    try:
        await db.audit_log.insert_one({
            "action": "exec_stage_advance",
            "project_id": project_id,
            "from": current,
            "to": target,
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass

    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    return _serialize(doc)


# ── DELIVERABLES ─────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/deliverables")
async def submit_deliverable(
    project_id: str,
    body: DeliverableSubmit,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Submit a deliverable for a project at a given stage."""
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    now = _now()
    deliverable = {
        "_id": ObjectId(),
        "stage": body.stage,
        "persona": body.persona,
        "title": body.title,
        "content_type": body.content_type,
        "content": body.content,
        "file_refs": body.file_refs,
        "metadata": body.metadata,
        "submitted_by": user.id,
        "submitted_at": now,
        "approval_status": "pending",  # pending, approved, rejected, revision_requested
    }

    await db.exec_projects.update_one(
        {"_id": _oid(project_id)},
        {"$push": {"deliverables": deliverable}, "$set": {"updated_at": now}}
    )

    deliverable["id"] = str(deliverable.pop("_id"))
    return deliverable


@router.post("/projects/{project_id}/approve")
async def approve_deliverable(
    project_id: str,
    body: ApprovalAction,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Approve, reject, or request revision on the latest deliverable."""
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    deliverables = doc.get("deliverables", [])
    if not deliverables:
        raise HTTPException(status_code=400, detail="No deliverables to approve")

    # Find latest pending deliverable
    latest = None
    for d in reversed(deliverables):
        if d.get("approval_status") == "pending":
            latest = d
            break
    if not latest:
        raise HTTPException(status_code=400, detail="No pending deliverables")

    now = _now()
    status_map = {"approve": "approved", "reject": "rejected", "request_revision": "revision_requested"}
    new_status = status_map.get(body.action, body.action)

    # Update the deliverable's approval status
    await db.exec_projects.update_one(
        {"_id": _oid(project_id), "deliverables._id": latest["_id"]},
        {"$set": {
            "deliverables.$.approval_status": new_status,
            "deliverables.$.reviewed_by": user.id,
            "deliverables.$.reviewed_at": now,
            "deliverables.$.review_notes": body.notes,
            "updated_at": now,
        }}
    )

    # If rejected or revision, optionally move back
    if body.action == "request_revision" and body.target_stage:
        current = doc["current_stage"]
        target_idx = STAGE_RANK.get(body.target_stage, 0)
        current_idx = STAGE_RANK.get(current, 0)
        if target_idx < current_idx:
            # Move back
            new_context = {**doc.get("context", {}), f"_revision_from_{current}": body.notes}
            await db.exec_projects.update_one(
                {"_id": _oid(project_id)},
                {"$set": {"current_stage": body.target_stage, "context": new_context, "updated_at": now}}
            )

    # Record approval
    approval = {
        "deliverable_id": str(latest["_id"]),
        "action": body.action,
        "notes": body.notes,
        "user_id": user.id,
        "timestamp": now,
    }
    await db.exec_projects.update_one(
        {"_id": _oid(project_id)},
        {"$push": {"approvals": approval}}
    )

    return {"status": new_status, "project_id": project_id}


# ── COMMENTS ─────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/comments")
async def list_comments(
    project_id: str,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """List comments for a project."""
    db = request.app.state.db
    comments = await db.exec_comments.find(
        {"project_id": project_id}
    ).sort("created_at", 1).limit(200).to_list(length=200)
    return [{**c, "id": str(c.pop("_id"))} for c in comments]


@router.post("/projects/{project_id}/comments")
async def add_comment(
    project_id: str,
    body: CommentCreate,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Add a comment to a project."""
    db = request.app.state.db
    now = _now()
    doc = {
        "project_id": project_id,
        "text": body.text,
        "persona": body.persona,
        "user_id": user.id,
        "user_name": user.full_name or user.id,
        "created_at": now,
    }
    result = await db.exec_comments.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {**doc, "id": str(doc.pop("_id"))}


# ── PIPELINE OVERVIEW ───────────────────────────────────────────────────────

@router.get("/pipeline")
async def pipeline_overview(
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """
    Get the full pipeline state: all active projects grouped by stage.
    This is the data that powers the Executive Suite dashboard.
    """
    db = request.app.state.db
    docs = await db.exec_projects.find(
        {"status": {"$in": ["active", "paused"]}}
    ).sort("updated_at", -1).to_list(length=100)

    pipeline = {stage: [] for stage in STAGES}
    for doc in docs:
        stage = doc.get("current_stage", "intake")
        if stage in pipeline:
            # Lightweight version for pipeline view
            pipeline[stage].append({
                "id": str(doc["_id"]),
                "title": doc.get("title", "Untitled"),
                "project_type": doc.get("project_type", "general"),
                "priority": doc.get("priority", "normal"),
                "assignees": doc.get("assignees", []),
                "deliverable_count": len(doc.get("deliverables", [])),
                "pending_deliverables": sum(
                    1 for d in doc.get("deliverables", [])
                    if d.get("approval_status") == "pending"
                ),
                "updated_at": doc.get("updated_at", ""),
            })

    # Summary stats
    total_active = len(docs)
    total_deliverables = sum(len(d.get("deliverables", [])) for d in docs)
    pending_approvals = sum(
        sum(1 for deliv in d.get("deliverables", []) if deliv.get("approval_status") == "pending")
        for d in docs
    )

    return {
        "stages": {stage: {"meta": STAGE_META[stage], "projects": pipeline[stage]} for stage in STAGES},
        "summary": {
            "total_active": total_active,
            "total_deliverables": total_deliverables,
            "pending_approvals": pending_approvals,
        },
        "stage_labels": STAGE_META,
    }


# ── STAGE TOOLS (exec-level tools available within the pipeline) ────────────

@router.get("/tools")
async def available_tools(
    user: User = Depends(_require_rank("admin", "executive_admin")),
):
    """
    List the exec-level tools available within the pipeline.
    These are not separate pages — they're tools the personas use
    within the context of a project.
    """
    return {
        "tools": [
            {"id": "jamil_chat",     "label": "Jamil — Team Coordination", "icon": "🤖",
             "desc": "Coordinate across personas, assign work, track progress",
             "stage": "assign", "route": "/jamil"},
            {"id": "source_protocol", "label": "Source Protocol — Mission Check", "icon": "🛡️",
             "desc": "Ensure outputs stay mission-aligned, voice integrity audit",
             "stage": "review", "route": "/business-office"},
            {"id": "arena",          "label": "Arena — Competitive Analysis", "icon": "⚔️",
             "desc": "Persona competition, challenge responses, competitive briefs",
             "stage": "intake", "route": "/arena"},
            {"id": "business_office","label": "Business Office — Revenue & P&L", "icon": "📊",
             "desc": "Revenue tracking, deals pipeline, cost analysis, AI jobs ledger",
             "stage": "operate", "route": "/business-office"},
            {"id": "more_ops",       "label": "M.O.R.E. Ops — Operations", "icon": "⚙️",
             "desc": "Distribution, logistics, community execution, task management",
             "stage": "operate", "route": "/more/ops"},
            {"id": "social_blast",   "label": "Social Blast — Publishing", "icon": "📢",
             "desc": "Multi-platform content publishing and scheduling",
             "stage": "deliver", "route": "/social/publish"},
            {"id": "studio",         "label": "Creator Studio — Content Creation", "icon": "🎨",
             "desc": "Video, audio, image creation and editing",
             "stage": "execute", "route": "/studio"},
            {"id": "ghost_producer", "label": "Ghost Producer — Content Engine", "icon": "✍️",
             "desc": "AI-assisted content generation, writing, production",
             "stage": "execute", "route": "/ghost-producer"},
            {"id": "architect",      "label": "Architect — Visual Intelligence", "icon": "🖼️",
             "desc": "Cover art, social visuals, brand assets",
             "stage": "execute", "route": "/studio"},
            {"id": "legal",          "label": "Legal Tools — Risk & Compliance", "icon": "⚖️",
             "desc": "Legal research, compliance checks, risk assessment",
             "stage": "review", "route": "/more/litigation"},
        ]
    }


# ── BOOTSTRAP: auto-create indexes ──────────────────────────────────────────

async def ensure_indexes(db):
    """Create MongoDB indexes for the pipeline collections."""
    await db.exec_projects.create_index("status")
    await db.exec_projects.create_index("current_stage")
    await db.exec_projects.create_index("owner_id")
    await db.exec_projects.create_index("updated_at")
    await db.exec_comments.create_index("project_id")
    await db.exec_comments.create_index("created_at")
