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

def _get_jwt_secret():
    """Resolve the JWT secret from the canonical server module (like nam.py).

    ``app.state.jwt_secret`` is never set at startup, so decoding with it
    rejected every valid token with 401 "Invalid token" — the Executive Suite
    pipeline could never load for anyone, including the owner.
    """
    try:
        from server import JWT_SECRET, JWT_ALGO
        return JWT_SECRET, JWT_ALGO
    except ImportError:
        return os.environ.get("JWT_SECRET", ""), "HS256"


def _require_rank(*roles):
    """Dependency factory: user must have one of the listed roles.

    JWTs carry the user's uuid `id` field as `sub` (see server.make_token),
    and every auth path on the platform looks users up by that field — so
    this lookup uses {"id": sub}, NOT the Mongo ObjectId `_id`. An `_id`
    lookup would 500 on every real token (ObjectId(uuid) raises).
    """
    async def dep(request: Request, authorization: Optional[str] = Header(None)) -> User:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        token = authorization.split(" ", 1)[1]
        secret, algo = _get_jwt_secret()
        if not secret:
            raise HTTPException(status_code=500, detail="JWT secret not configured")
        try:
            import jwt
            payload = jwt.decode(token, secret, algorithms=[algo])
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await request.app.state.db.users.find_one({"id": payload.get("sub", "")})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.get("is_active") is False:
            raise HTTPException(status_code=403, detail="Account deactivated")
        user_role = user.get("role", "student")
        ROLE_RANK = {"student": 1, "trial_pass": 2, "instructor": 3, "support_staff": 4,
                      "oversight": 5, "admin": 6, "executive_admin": 7}
        needed = min(ROLE_RANK.get(r, 0) for r in roles)
        if ROLE_RANK.get(user_role, 0) < needed:
            raise HTTPException(status_code=403, detail=f"Requires {roles}")
        return User(id=str(user["id"]), role=user_role, full_name=user.get("full_name", ""))
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


# ── Stage execution (AI runs the stage, human approves the result) ──────────
# The AI team "runs" a stage the same way a staff member would: it reads the
# project brief, the packet, and what earlier stages produced, does the work
# for this stage, and files the output as a pending deliverable. Nothing it
# produces is approved or published without the owner.

_PERSONA_ROLE = {
    "Jamil":          "The Director — coordinates the whole AI team and produces executive-grade work across all domains.",
    "Hybrid NAM":     "The Assistant Director — operations, guidance, and institutional continuity.",
    "Production":     "The creative production lead — content, copy, packaging, and creative assets.",
    "Creative Partner": "The creative development partner — concepts, writing, and project development.",
    "Marketing":      "The campaign lead — audience, positioning, and promotional plans.",
    "Review":         "The quality reviewer — mission alignment, clarity, and completeness checks.",
    "Source":         "The Source Protocol — mission and voice integrity review.",
    "Operations":     "The operations lead — logistics, distribution, and execution plans.",
    "Analytics":      "The measurement lead — metrics, tracking, and performance analysis.",
    "Architect":      "The visual intelligence lead — artwork, layouts, and brand assets.",
    "Ghost Producer": "The music production authority — beats, songwriting, and studio workflows.",
}


def _stage_system(persona: str, stage: str) -> str:
    """System prompt for a stage run: the persona's role + the stage's task."""
    role = _PERSONA_ROLE.get(persona, f"The specialist assigned to this task ({persona}).")
    task = STAGE_META.get(stage, {}).get("desc", f"Execute the {stage} stage of the project.")
    return (
        "You are a member of the M.O.R.E. AI team operating inside the executive pipeline. "
        f"Your role: {role}\n"
        f"Current stage: {task}\n"
        "You are working from the project's brief, its packet, and the context earlier stages produced. "
        "Produce a concrete deliverable FOR THIS STAGE — completed work, not a plan of work. "
        "Do not invent facts about the platform's live data; ground everything in the brief and context given. "
        "Be plain, direct, and useful. Flag anything that requires the owner's approval instead of deciding it."
    )


def _stage_prompt(doc: dict, stage: str, packet: dict, ctx_lines: list, prior: str, instructions: str) -> str:
    """Build the user prompt handed to the persona for this stage run."""
    parts = [
        f"PROJECT: {doc.get('title')}",
        f"TYPE: {doc.get('project_type')}  ·  PRIORITY: {doc.get('priority')}",
        f"STAGE: {stage} — {STAGE_META.get(stage, {}).get('label', stage)}",
        f"BRIEF: {doc.get('brief')}",
    ]
    if packet.get("objective"):
        parts.append(f"OBJECTIVE: {packet['objective']}")
    if packet.get("constraints"):
        parts.append(f"CONSTRAINTS: {packet['constraints']}")
    if packet.get("deliverables_summary"):
        parts.append(f"REQUIRED DELIVERABLES: {packet['deliverables_summary']}")
    if packet.get("authority"):
        parts.append(
            f"AUTHORITY: {packet['authority']} "
            "(autonomous = complete without asking; approval_required = prepare for owner approval; "
            "human_only = advise only, never execute)"
        )
    if ctx_lines:
        parts.append("ACCUMULATED CONTEXT:\n" + "\n".join(ctx_lines))
    if prior:
        parts.append("PRIOR DELIVERABLES (most recent first):\n" + prior)
    if instructions:
        parts.append(f"OWNER'S INSTRUCTIONS FOR THIS RUN: {instructions}")
    parts.append("YOUR DELIVERABLE:")
    return "\n\n".join(parts)


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

class StageRun(BaseModel):
    """Run a stage: hand the project brief + accumulated context to a persona
    through the LLM gateway, then post the result back into the pipeline as a
    deliverable. The owner stays the decision-maker — the result lands as a
    pending deliverable awaiting review, never as an approved action.
    """
    persona: str = ""              # empty → packet ai_team[0] or Jamil
    instructions: str = ""         # optional owner's direction for this run
    max_tokens: int = 2000

class ArchiveAsset(BaseModel):
    """One item in the personal archive — material that already exists and
    deserves to become something next: album masters, manuscripts, photos,
    documents, video. Discovery scans this archive and proposes projects.
    """
    title: str
    kind: str = "other"     # audio, book, document, photo, video, other
    notes: str = ""         # what it is, what state it's in, what's missing
    file_ref: str = ""      # GridFS file ID or URL (optional)
    tags: List[str] = []

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


# ── PERSONAL ARCHIVE — turn what already exists into what comes next ─────────
# The owner's archive of existing material (album masters, manuscripts,
# photos, documents). Discovery scans this archive alongside the platform's
# own products and proposes the highest-value next projects from it.

@router.get("/archive")
async def list_archive(
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """List every asset in the personal archive, newest first."""
    db = request.app.state.db
    docs = await db.exec_archive.find({}).sort("created_at", -1).limit(200).to_list(length=200)
    out = []
    for d in docs:
        d["id"] = str(d.pop("_id"))
        out.append(d)
    return out


@router.post("/archive")
async def add_archive_asset(
    body: ArchiveAsset,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Add an asset to the personal archive."""
    db = request.app.state.db
    now = _now()
    doc = {
        "title": body.title.strip(),
        "kind": body.kind,
        "notes": body.notes.strip(),
        "file_ref": body.file_ref.strip(),
        "tags": body.tags,
        "created_by": user.id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.exec_archive.insert_one(doc)
    doc["_id"] = result.inserted_id
    doc["id"] = str(doc.pop("_id"))
    try:
        await db.audit_log.insert_one({
            "action": "exec_archive_add",
            "asset_title": doc["title"],
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass
    return doc


@router.delete("/archive/{asset_id}")
async def delete_archive_asset(
    asset_id: str,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """Remove an asset from the personal archive."""
    db = request.app.state.db
    result = await db.exec_archive.delete_one({"_id": _oid(asset_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"status": "success", "deleted": asset_id}


# ── PROJECT DISCOVERY — turn what already exists into what comes next ────────
# Scans authorized existing material (personal archive, published media
# products, pipeline deliverables, sellable tracks) and proposes the
# highest-value next projects.

@router.get("/discovery")
async def project_discovery(
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    db = request.app.state.db
    inventory = {"products": [], "deliverables": [], "tracks": [], "archive": []}
    archive_docs = []

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
    try:
        archive_docs = await db.exec_archive.find({}).sort("created_at", -1).to_list(200)
        inventory["archive"] = [
            {"id": str(a.pop("_id")), "title": a.get("title", ""), "kind": a.get("kind", "other"),
             "notes": a.get("notes", "")}
            for a in archive_docs
        ]
    except Exception:
        pass

    audio_count = len(inventory["tracks"])
    product_count = len(inventory["products"])
    deliverable_count = len(inventory["deliverables"])
    archive_total = len(archive_docs)
    archive_audio = sum(1 for a in archive_docs if a.get("kind") == "audio")
    archive_books = sum(1 for a in archive_docs if a.get("kind") == "book")
    total_assets = audio_count + product_count + deliverable_count + archive_total

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
    if archive_audio >= 1:
        audio_titles = ", ".join(a.get("title", "") for a in archive_docs if a.get("kind") == "audio")[:180]
        proposals.append({
            "kind": "album_distribution",
            "title": f"Album — Distribution Project ({archive_audio} archived audio asset{'s' if archive_audio != 1 else ''})",
            "rationale": "Finished audio is sitting in the archive unreleased. Inventory the assets, fill the gaps, and build a release campaign.",
            "suggested_team": ["Production", "Creative Partner", "Marketing"],
            "authority": "approval_required",
            "brief": f"Turn the archived audio ({audio_titles}) into a distribution project: asset inventory, metadata, artwork, promotional package, and store push.",
        })
    if archive_books >= 1:
        book_titles = ", ".join(a.get("title", "") for a in archive_docs if a.get("kind") == "book")[:180]
        proposals.append({
            "kind": "book_publishing",
            "title": f"Book — Publishing Project ({archive_books} archived book/doc asset{'s' if archive_books != 1 else ''})",
            "rationale": "A manuscript deserves a full publishing path: edit, cover, interior, metadata, distribution, promotion.",
            "suggested_team": ["Creative Partner", "Production", "Marketing"],
            "authority": "approval_required",
            "brief": f"Take the archived manuscript(s) ({book_titles}) through the publishing pipeline: edit, cover, interior, metadata, distribution plan.",
        })
    if archive_total >= 3:
        proposals.append({
            "kind": "archive_org",
            "title": f"Archive — Organization & Discovery ({archive_total} assets)",
            "rationale": "More material than projects yet. Catalog everything, group related assets, identify gaps, and propose the highest-value next projects.",
            "suggested_team": ["Operations", "Analytics"],
            "authority": "autonomous",
            "brief": f"Catalog the {archive_total} archived assets, group them into projects, identify what is missing, and propose the highest-value next work.",
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
            "archive_assets": archive_total,
            "archive_audio": archive_audio,
            "archive_books": archive_books,
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


# ── STAGE EXECUTION ──────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/run-stage")
async def run_stage(
    project_id: str,
    body: StageRun,
    user: User = Depends(_require_rank("admin", "executive_admin")),
    request: Request = None,
):
    """
    Run the current stage: hand the brief + accumulated context to a persona
    through the LLM gateway, and post the result back as a pending deliverable.

    This is the difference between recording work and the AI team doing work:
    the persona actually executes the stage. The output lands pending review —
    the owner approves, rejects, or requests revision exactly as with any other
    deliverable. On any gateway failure the stage is NOT executed and no fake
    output is stored.
    """
    db = request.app.state.db
    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")

    stage = doc.get("current_stage", "intake")
    packet = doc.get("packet") or {}

    # Resolve persona: explicit choice → packet ai_team → Jamil
    persona = body.persona.strip()
    if not persona:
        team = packet.get("ai_team") or []
        persona = team[0] if team else "Jamil"

    # Assemble the context earlier stages produced
    ctx_lines = [
        f"{k}: {v}" for k, v in (doc.get("context") or {}).items()
        if isinstance(v, str) and not k.startswith("_stage_")
    ]
    deliverables = doc.get("deliverables", [])
    prior = "\n".join(
        f"- [{d.get('stage')}] {d.get('persona')}: {d.get('title')} — {(d.get('content') or '')[:600]}"
        for d in deliverables[-8:]
    )

    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            system=_stage_system(persona, stage),
            messages=[{"role": "user", "content": _stage_prompt(doc, stage, packet, ctx_lines, prior, body.instructions)}],
            max_tokens=body.max_tokens,
            persona_label="exec_pipeline",
            user_id=user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI stage execution unavailable: {e}")

    text = (result.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=503, detail="AI returned no output — stage not executed.")

    now = _now()
    deliverable = {
        "_id": ObjectId(),
        "stage": stage,
        "persona": persona,
        "title": f"{STAGE_META.get(stage, {}).get('label', stage)} — {persona} run",
        "content_type": "text",
        "content": text,
        "file_refs": [],
        "metadata": {
            "auto": True,
            "provider": result.get("provider", "unknown"),
            "instructions": body.instructions,
        },
        "submitted_by": user.id,
        "submitted_at": now,
        "approval_status": "pending",
    }

    await db.exec_projects.update_one(
        {"_id": _oid(project_id)},
        {"$push": {"deliverables": deliverable}, "$set": {"updated_at": now}}
    )
    deliverable["id"] = str(deliverable.pop("_id"))

    try:
        await db.audit_log.insert_one({
            "action": "exec_stage_run",
            "project_id": project_id,
            "stage": stage,
            "persona": persona,
            "provider": result.get("provider", "unknown"),
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass

    doc = await db.exec_projects.find_one({"_id": _oid(project_id)})
    return {"status": "success", "deliverable": deliverable, "project": _serialize(doc)}


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
    await db.exec_archive.create_index("created_at")
    await db.exec_archive.create_index("kind")
