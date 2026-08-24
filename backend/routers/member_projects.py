"""
member_projects.py — "Have your M.O.R.E. team work on it."

The member-facing half of the project pipeline. The executive pipeline
(/api/executive) is the internal AI staff's operating workspace; this router
is the customer product built on the same model:

    member defines the goal (title + brief + category)
        → Run stage → a persona reads the brief and produces work
        → the result lands PENDING — the member approves / rejects / asks
          for revision
        → advance → the next stage sees what was produced

The member is always the decision-maker. Nothing the AI produces is approved
or published without them. This is the same packet/authority model as the
executive pipeline, simplified for a member audience:

  - Authority is fixed at "approval_required" — the AI prepares, the member
    approves. Members never grant autonomous or human-only authority.
  - Personas are limited to the customer-facing team (no Jamil / Hybrid NAM /
    Source — those are internal staff per ROLE_ACCESS_ARCHITECTURE).
  - Platform-funded AI is bounded per member per day (MEMBER_PROJECT_DAILY_RUNS,
    default 5) and active projects are capped (default 5) so the feature can
    never be an unlimited cost sink.

Collection:
  member_projects — one doc per project, owner-scoped (owner_id = user uuid).
  Comments are embedded on the doc. Deliverables + approvals are embedded
  arrays, mirroring exec_projects.
"""

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel
from bson import ObjectId

router = APIRouter(prefix="/api/my-projects", tags=["member-projects"])

# ── Auth ──────────────────────────────────────────────────────────────────────

# Mirrors backend/roles.py ROLE_RANK (authority) and security/feature_control.py
# TIER_RANK (entitlement). Members = tier "member" and above. Staff roles pass
# the tier check the same way TIER_EXEMPT_ROLES does elsewhere.
_ROLE_RANK = {"student": 1, "trial_pass": 2, "instructor": 3, "support_staff": 4,
              "oversight": 5, "admin": 6, "executive_admin": 7}
_TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5}
_TIER_EXEMPT_ROLES = ("admin", "executive_admin")
MIN_MEMBER_TIER = "member"


class MemberUser(BaseModel):
    id: str
    role: str
    tier: str = "free"
    full_name: str = ""
    is_staff: bool = False


def _require_member():
    """Dependency: any authenticated user whose tier covers `member`.

    JWTs carry the user's uuid `id` field as `sub`; users are looked up by
    that field (see server.make_token / routers.auth). Staff roles bypass the
    tier gate, exactly like TIER_EXEMPT_ROLES in the FCC.
    """
    async def dep(request: Request, authorization: Optional[str] = Header(None)) -> MemberUser:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Authentication required")
        token = authorization.split(" ", 1)[1]
        try:
            import jwt
            payload = jwt.decode(token, request.app.state.jwt_secret, algorithms=["HS256"])
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await request.app.state.db.users.find_one({"id": payload.get("sub", "")})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.get("is_active") is False:
            raise HTTPException(status_code=403, detail="Account deactivated")
        role = user.get("role", "student")
        tier = user.get("feature_tier", "free")
        if role not in _TIER_EXEMPT_ROLES and _TIER_RANK.get(tier, 0) < _TIER_RANK[MIN_MEMBER_TIER]:
            raise HTTPException(
                status_code=403,
                detail="Member access required — this feature is part of Member membership and above.",
            )
        return MemberUser(
            id=str(user.get("id") or user.get("_id")),
            role=role,
            tier=tier,
            full_name=user.get("full_name", ""),
            is_staff=role in _TIER_EXEMPT_ROLES or _ROLE_RANK.get(role, 0) >= _ROLE_RANK["instructor"],
        )
    return dep


# ── Stages (same vocabulary as the executive pipeline) ───────────────────────

STAGES = ["intake", "assign", "execute", "review", "operate", "deliver"]

STAGE_META = {
    "intake":  {"label": "Intake",    "icon": "🎯", "desc": "The goal, the brief, and what success looks like."},
    "assign":  {"label": "Assign",    "icon": "👥", "desc": "The M.O.R.E. team breaks the goal into a work plan."},
    "execute": {"label": "Execute",   "icon": "⚡", "desc": "The team produces the work for this stage."},
    "review":  {"label": "Review",    "icon": "🛡️", "desc": "Quality and alignment check before you decide."},
    "operate": {"label": "Operate",   "icon": "📊", "desc": "Packaging, distribution, and next steps."},
    "deliver": {"label": "Deliver",   "icon": "✅", "desc": "The finished result, ready for you to use."},
}

STAGE_RANK = {s: i for i, s in enumerate(STAGES)}

# Customer-facing team only — internal staff personas stay internal.
_PUBLIC_PERSONAS = {
    "Helper":          "The research and answers lead — finds what you need, clearly explained.",
    "Creative Partner": "The creative development partner — concepts, writing, and project development.",
    "Production":      "The production lead — content, copy, packaging, and creative assets.",
    "Ghost Producer":  "The music authority — beats, songwriting, and studio workflows.",
    "Marketing":       "The audience lead — positioning, campaigns, and promotion.",
    "Review":          "The quality reviewer — clarity, completeness, and alignment checks.",
    "Operations":      "The operations lead — logistics, organization, and execution plans.",
    "Analytics":       "The measurement lead — metrics, tracking, and performance analysis.",
}

# Goal category → suggested team
_CATEGORY_TEAM = {
    "launch":   ["Production", "Marketing", "Operations"],
    "create":   ["Creative Partner", "Ghost Producer", "Production"],
    "organize": ["Operations", "Analytics"],
    "grow":     ["Marketing", "Production"],
    "learn":    ["Helper", "Review"],
}
_DEFAULT_TEAM = ["Production", "Review"]

# Abuse/cost caps
MAX_ACTIVE_PROJECTS = 5          # per member
MAX_PROJECTS_TOTAL = 25          # lifetime per member (archive old ones)
MEMBER_PROJECT_DAILY_RUNS = 5    # AI stage runs per member per day (env-overridable)


def _daily_run_limit() -> int:
    import os
    try:
        return max(1, int(os.environ.get("MEMBER_PROJECT_DAILY_RUNS", str(MEMBER_PROJECT_DAILY_RUNS))))
    except Exception:
        return MEMBER_PROJECT_DAILY_RUNS


# ── Models ────────────────────────────────────────────────────────────────────

class MemberProjectCreate(BaseModel):
    title: str
    brief: str
    category: str = "launch"      # launch | create | organize | grow | learn
    priority: str = "normal"      # low | normal | high
    desired_outcome: str = ""     # what "done" looks like to the member

class StageRun(BaseModel):
    persona: str = ""
    instructions: str = ""
    max_tokens: int = 1500

class StageTransition(BaseModel):
    target_stage: Optional[str] = None
    notes: str = ""

class DeliverableSubmit(BaseModel):
    title: str
    persona: str = "Member"
    content_type: str = "text"
    content: str = ""
    file_refs: List[str] = []
    metadata: dict = {}

class ApprovalAction(BaseModel):
    action: str  # approve | reject | request_revision
    notes: str = ""
    target_stage: Optional[str] = None

class CommentCreate(BaseModel):
    text: str
    persona: Optional[str] = None  # set when the AI team replies as a persona


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _today_start() -> datetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")


def _serialize(doc: dict) -> dict:
    """Mongo doc → JSON-safe dict with string ids on nested deliverables."""
    doc["id"] = str(doc.pop("_id"))
    for d in doc.get("deliverables", []):
        if "_id" in d:
            d["id"] = str(d["_id"])
    return doc


async def _owned_project(db, project_id: str, user: MemberUser) -> dict:
    """Fetch a project, 404 when missing, 403 when not the owner.
    Only admin/exec may view another member's project (oversight)."""
    doc = await db.member_projects.find_one({"_id": _oid(project_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Project not found")
    if doc.get("owner_id") != user.id and user.role not in ("admin", "executive_admin"):
        raise HTTPException(status_code=403, detail="This is not your project")
    return doc


def _stage_system(persona: str, stage: str) -> str:
    role = _PUBLIC_PERSONAS.get(persona, f"The specialist assigned to this task ({persona}).")
    task = STAGE_META.get(stage, {}).get("desc", f"Execute the {stage} stage of the project.")
    return (
        "You are part of the M.O.R.E. AI team helping a member with their project. "
        f"Your role: {role}\n"
        f"Current stage: {task}\n"
        "Work from the member's goal, their brief, and what earlier stages produced. "
        "Produce a concrete deliverable FOR THIS STAGE — finished work, not a plan of work. "
        "Do not invent facts about the platform's live data; ground everything in the brief and context given. "
        "You serve the member, but you never decide for them: prepare everything, and clearly flag "
        "anything that needs their judgment or approval instead of deciding it. "
        "Be plain, direct, and useful. Never publish, spend, or commit on the member's behalf."
    )


def _stage_prompt(doc: dict, stage: str, ctx_lines: list, prior: str, instructions: str) -> str:
    parts = [
        f"PROJECT: {doc.get('title')}",
        f"CATEGORY: {doc.get('category')}  ·  PRIORITY: {doc.get('priority')}",
        f"STAGE: {stage} — {STAGE_META.get(stage, {}).get('label', stage)}",
        f"BRIEF: {doc.get('brief')}",
    ]
    if doc.get("desired_outcome"):
        parts.append(f"WHAT DONE LOOKS LIKE: {doc['desired_outcome']}")
    if ctx_lines:
        parts.append("CONTEXT FROM EARLIER STAGES:\n" + "\n".join(ctx_lines))
    if prior:
        parts.append("WORK ALREADY PRODUCED (most recent first):\n" + prior)
    if instructions:
        parts.append(f"MEMBER'S INSTRUCTIONS FOR THIS RUN: {instructions}")
    parts.append("YOUR DELIVERABLE:")
    return "\n\n".join(parts)


# ── LIST / CREATE ─────────────────────────────────────────────────────────────

@router.get("")
async def list_my_projects(
    user: MemberUser = Depends(_require_member()),
    status: Optional[str] = Query(None),
    request: Request = None,
):
    """List the member's projects, newest first, with summary counts."""
    db = request.app.state.db
    q = {"owner_id": user.id}
    if status:
        q["status"] = status
    docs = await db.member_projects.find(q).sort("updated_at", -1).limit(100).to_list(length=100)
    out = []
    for d in docs:
        s = _serialize(d)
        out.append(s)
    active = sum(1 for d in out if d.get("status") == "active")
    return {
        "projects": out,
        "summary": {
            "total": len(out),
            "active": active,
            "pending_reviews": sum(
                1 for d in out
                for dl in d.get("deliverables", [])
                if dl.get("approval_status") == "pending"
            ),
            "daily_runs_left": await _daily_runs_left(db, user),
            "daily_run_limit": _daily_run_limit(),
        },
    }


async def _daily_runs_left(db, user: MemberUser) -> int:
    """Count today's auto (AI) stage runs across the member's projects."""
    try:
        projects = await db.member_projects.find(
            {"owner_id": user.id},
            {"deliverables": 1},
        ).to_list(length=100)
        limit = _daily_run_limit()
        used = 0
        start = _today_start()
        for p in projects:
            for d in (p.get("deliverables") or []):
                if d.get("metadata", {}).get("auto") and d.get("submitted_at", "").startswith(start.strftime("%Y-%m-%d")):
                    used += 1
        return max(0, limit - used)
    except Exception:
        return _daily_run_limit()


@router.post("")
async def create_project(
    body: MemberProjectCreate,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Create a member project. Starts at intake with an approval-required packet."""
    db = request.app.state.db
    title = body.title.strip()
    brief = body.brief.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Give the project a title")
    if len(brief) < 10:
        raise HTTPException(status_code=400, detail="Tell the team a little more about the goal (at least 10 characters)")

    # Caps
    try:
        existing = await db.member_projects.count_documents({"owner_id": user.id})
        active = await db.member_projects.count_documents({"owner_id": user.id, "status": "active"})
    except Exception:
        existing, active = 0, 0
    if existing >= MAX_PROJECTS_TOTAL:
        raise HTTPException(status_code=403, detail="Project limit reached — complete or archive an old project first.")
    if active >= MAX_ACTIVE_PROJECTS:
        raise HTTPException(status_code=403, detail=f"Too many active projects — finish or archive one first (max {MAX_ACTIVE_PROJECTS}).")

    now = _now()
    category = body.category if body.category in _CATEGORY_TEAM else "launch"
    doc = {
        "title": title,
        "brief": brief,
        "category": category,
        "priority": body.priority if body.priority in ("low", "normal", "high") else "normal",
        "desired_outcome": body.desired_outcome.strip(),
        "status": "active",
        "current_stage": "intake",
        "stage_history": [{"stage": "intake", "entered_at": now}],
        "context": {"brief": brief, "category": category},
        "deliverables": [],
        "approvals": [],
        "comments": [],
        "packet": {
            "objective": body.desired_outcome.strip() or brief[:500],
            "owner": user.full_name or user.id,
            "ai_team": _CATEGORY_TEAM.get(category, _DEFAULT_TEAM),
            "authority": "approval_required",
            "approval_points": ["Approve every deliverable before it counts as done"],
        },
        "owner_id": user.id,
        "owner_name": user.full_name or user.id,
        "created_at": now,
        "updated_at": now,
    }
    result = await db.member_projects.insert_one(doc)
    doc["_id"] = result.inserted_id
    try:
        await db.audit_log.insert_one({
            "action": "member_project_created",
            "project_id": str(result.inserted_id),
            "title": title,
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass
    return _serialize(doc)


# ── DETAIL / TRANSITIONS ──────────────────────────────────────────────────────

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    return _serialize(doc)


@router.post("/{project_id}/advance")
async def advance_stage(
    project_id: str,
    body: StageTransition,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Move the project to the next stage (or a specific one). Context flows forward."""
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    current = doc["current_stage"]
    if body.target_stage:
        target = body.target_stage
        if target not in STAGE_RANK:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {target}")
    else:
        idx = STAGE_RANK.get(current, 0)
        if idx >= len(STAGES) - 1:
            raise HTTPException(status_code=400, detail="Project already at the final stage")
        target = STAGES[idx + 1]

    now = _now()
    new_context = {**doc.get("context", {}), f"_stage_{current}_completed_at": now}
    if body.notes:
        new_context[f"_stage_{current}_notes"] = body.notes
    stage_history = doc.get("stage_history", []) + [{"stage": target, "entered_at": now, "from_stage": current}]
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$set": {"current_stage": target, "context": new_context, "stage_history": stage_history, "updated_at": now}},
    )
    updated = await db.member_projects.find_one({"_id": doc["_id"]})
    return _serialize(updated)


@router.post("/{project_id}/run-stage")
async def run_stage(
    project_id: str,
    body: StageRun,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Run the current stage: a persona reads the brief + context and produces
    work, which lands as a PENDING deliverable the member reviews. Fail-closed:
    on any gateway error nothing is stored — no fabricated output ever lands.
    """
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    if doc.get("status") != "active":
        raise HTTPException(status_code=400, detail="Project is not active")

    # Per-member daily cost cap — the platform funds these runs.
    left = await _daily_runs_left(db, user)
    if left <= 0:
        raise HTTPException(
            status_code=429,
            detail=f"Daily AI run limit reached ({_daily_run_limit()}/day). Come back tomorrow — or review what's already produced.",
        )

    stage = doc.get("current_stage", "intake")
    persona = body.persona.strip()
    if not persona:
        persona = (doc.get("packet") or {}).get("ai_team", [""])[0] or "Production"
    if persona not in _PUBLIC_PERSONAS:
        raise HTTPException(status_code=400, detail=f"Pick a team member from: {', '.join(_PUBLIC_PERSONAS)}")

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
            messages=[{"role": "user", "content": _stage_prompt(doc, stage, ctx_lines, prior, body.instructions)}],
            max_tokens=body.max_tokens,
            persona_label="member_project",
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI stage execution unavailable: {e}")

    text = (result.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=503, detail="The team returned no output — nothing was saved. Try again.")

    now = _now()
    deliverable = {
        "_id": ObjectId(),
        "stage": stage,
        "persona": persona,
        "title": f"{STAGE_META.get(stage, {}).get('label', stage)} — {persona}",
        "content_type": "text",
        "content": text,
        "file_refs": [],
        "metadata": {"auto": True, "provider": result.get("provider", "unknown"), "instructions": body.instructions},
        "submitted_by": user.id,
        "submitted_at": now,
        "approval_status": "pending",
    }
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$push": {"deliverables": deliverable}, "$set": {"updated_at": now}},
    )
    deliverable["id"] = str(deliverable.pop("_id"))

    try:
        await db.audit_log.insert_one({
            "action": "member_stage_run",
            "project_id": project_id,
            "stage": stage,
            "persona": persona,
            "provider": result.get("provider", "unknown"),
            "user_id": user.id,
            "timestamp": now,
        })
    except Exception:
        pass

    updated = await db.member_projects.find_one({"_id": doc["_id"]})
    return {"status": "success", "deliverable": deliverable, "project": _serialize(updated)}


# ── DELIVERABLES & APPROVAL ───────────────────────────────────────────────────

@router.post("/{project_id}/deliverables")
async def submit_deliverable(
    project_id: str,
    body: DeliverableSubmit,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Member records their own work as a deliverable (a Studio export, a file,
    notes) — the same lane the AI team's output lands in."""
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    now = _now()
    deliverable = {
        "_id": ObjectId(),
        "stage": doc.get("current_stage", "intake"),
        "persona": body.persona or "Member",
        "title": body.title.strip() or "Deliverable",
        "content_type": body.content_type,
        "content": body.content,
        "file_refs": body.file_refs,
        "metadata": {"auto": False, **body.metadata},
        "submitted_by": user.id,
        "submitted_at": now,
        "approval_status": "pending",
    }
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$push": {"deliverables": deliverable}, "$set": {"updated_at": now}},
    )
    deliverable["id"] = str(deliverable.pop("_id"))
    return deliverable


@router.post("/{project_id}/approve")
async def approve_deliverable(
    project_id: str,
    body: ApprovalAction,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Approve, reject, or request revision on the latest pending deliverable.
    Approval is recorded and the member stays the decision-maker."""
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    deliverables = doc.get("deliverables", [])
    latest = next((d for d in reversed(deliverables) if d.get("approval_status") == "pending"), None)
    if not latest:
        raise HTTPException(status_code=400, detail="No pending work to review")

    now = _now()
    status_map = {"approve": "approved", "reject": "rejected", "request_revision": "revision_requested"}
    new_status = status_map.get(body.action, body.action)
    await db.member_projects.update_one(
        {"_id": doc["_id"], "deliverables._id": latest["_id"]},
        {"$set": {
            "deliverables.$.approval_status": new_status,
            "deliverables.$.reviewed_by": user.id,
            "deliverables.$.reviewed_at": now,
            "deliverables.$.review_notes": body.notes,
            "updated_at": now,
        }},
    )
    if body.action == "request_revision" and body.target_stage and body.target_stage in STAGE_RANK:
        if STAGE_RANK[body.target_stage] < STAGE_RANK.get(doc["current_stage"], 0):
            await db.member_projects.update_one(
                {"_id": doc["_id"]},
                {"$set": {"current_stage": body.target_stage, "updated_at": now}},
            )
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$push": {"approvals": {
            "deliverable_id": str(latest["_id"]),
            "action": body.action,
            "notes": body.notes,
            "user_id": user.id,
            "timestamp": now,
        }}},
    )
    return {"status": new_status, "project_id": project_id}


# ── COMMENTS (embedded, threaded by timestamp) ───────────────────────────────

@router.post("/{project_id}/comments")
async def add_comment(
    project_id: str,
    body: CommentCreate,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    now = _now()
    comment = {
        "id": str(ObjectId()),
        "text": body.text,
        "persona": body.persona,
        "user_id": user.id,
        "user_name": user.full_name or user.id,
        "created_at": now,
    }
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$push": {"comments": comment}, "$set": {"updated_at": now}},
    )
    return comment


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Archive a project (frees an active-project slot)."""
    db = request.app.state.db
    doc = await _owned_project(db, project_id, user)
    await db.member_projects.update_one(
        {"_id": doc["_id"]},
        {"$set": {"status": "archived", "updated_at": _now()}},
    )
    return {"status": "archived", "project_id": project_id}


# ── STAFF OVERSIGHT (admin/exec) ─────────────────────────────────────────────

@router.get("/admin/all")
async def admin_list_all(
    user: MemberUser = Depends(_require_member()),
    request: Request = None,
):
    """Admin/exec oversight list of every member project — the same feed the
    office KPIs will read in the next phase. Lightweight rows only."""
    if not user.is_staff or user.role not in ("admin", "executive_admin"):
        raise HTTPException(status_code=403, detail="Staff access required")
    db = request.app.state.db
    docs = await db.member_projects.find({}).sort("updated_at", -1).limit(300).to_list(length=300)
    rows = []
    for d in docs:
        rows.append({
            "id": str(d["_id"]),
            "title": d.get("title"),
            "owner_id": d.get("owner_id"),
            "owner_name": d.get("owner_name"),
            "category": d.get("category"),
            "status": d.get("status"),
            "current_stage": d.get("current_stage"),
            "deliverable_count": len(d.get("deliverables", [])),
            "pending_count": sum(1 for x in d.get("deliverables", []) if x.get("approval_status") == "pending"),
            "updated_at": d.get("updated_at"),
        })
    return {"projects": rows, "total": len(rows)}


# ── INDEXES ───────────────────────────────────────────────────────────────────

async def ensure_indexes(db):
    """Create MongoDB indexes for member projects."""
    await db.member_projects.create_index("owner_id")
    await db.member_projects.create_index([("owner_id", 1), ("status", 1)])
    await db.member_projects.create_index("updated_at")
