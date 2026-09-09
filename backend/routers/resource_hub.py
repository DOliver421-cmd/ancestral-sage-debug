"""
Resource Hub — unified workspace for Grants, Fundraising, Business Resources.

Combines existing scholarship/fundraising data with new grant tracking and
business resource management into one coherent workflow surface.

Access: member+ tier for browsing, staff for admin operations.
All data comes from real MongoDB collections.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field

from roles import ROLE_RANK

logger = logging.getLogger("resource_hub")

router = APIRouter(prefix="/api/hub", tags=["Resource Hub"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
_current_user_dep = None
audit = None


def bind(_current_user, _db=None, _audit=None):
    global db, _current_user_dep, audit
    _current_user_dep = _current_user
    db = _db
    audit = _audit


# ── Auth ──────────────────────────────────────────────────────────────────────

async def _get_user(authorization: str = Header(None)):
    if _current_user_dep is None:
        raise HTTPException(503, "Resource Hub is not available.")
    return await _current_user_dep(authorization)


def _require_member(user: Any):
    """Member+ tier required for browsing. Staff gets admin features."""
    tier = getattr(user, "feature_tier", "free")
    role = getattr(user, "role", "student")
    tier_order = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6}
    is_member = tier_order.get(tier, 0) >= 1
    is_staff = ROLE_RANK.get(role, 0) >= ROLE_RANK.get("instructor", 3)
    if not is_member and not is_staff:
        raise HTTPException(403, "This feature requires a Member subscription or staff access.")
    return user


def _require_staff(user: Any):
    role = getattr(user, "role", "student")
    if ROLE_RANK.get(role, 0) < ROLE_RANK.get("instructor", 3):
        raise HTTPException(403, "Staff access required.")
    return user


def _is_staff(user: Any) -> bool:
    role = getattr(user, "role", "student")
    return ROLE_RANK.get(role, 0) >= ROLE_RANK.get("instructor", 3)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coll(name: str):
    if db is None:
        raise HTTPException(503, "Database not available.")
    return getattr(db, name)


# ── Models ────────────────────────────────────────────────────────────────────

class GrantCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    source: str = Field(..., min_length=1, max_length=200)  # e.g. "SBA", "USDA", "Local Foundation"
    amount: str = Field(default="", max_length=100)  # e.g. "$5,000 - $25,000"
    deadline: str = Field(default="", max_length=50)
    description: str = Field(default="", max_length=5000)
    eligibility: str = Field(default="", max_length=2000)
    url: str = Field(default="", max_length=500)
    category: str = Field(default="general")  # general, education, tech, community, arts


class GrantApplication(BaseModel):
    grant_id: str = Field(..., min_length=1)
    project_title: str = Field(..., min_length=1, max_length=200)
    project_description: str = Field(..., min_length=1, max_length=5000)
    requested_amount: str = Field(default="", max_length=100)
    timeline: str = Field(default="", max_length=1000)


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    goal_amount: str = Field(..., min_length=1, max_length=100)  # e.g. "$10,000"
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = Field(default="general")  # education, community, arts, emergency
    deadline: str = Field(default="", max_length=50)


class ResourceCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    category: str = Field(..., pattern="^(legal|financial|marketing|technology|compliance|networking|templates)$")
    url: str = Field(default="", max_length=500)
    file_url: str = Field(default="", max_length=500)
    tags: List[str] = Field(default_factory=list)


class WorkflowStep(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    completed: bool = False


# ── Grants ────────────────────────────────────────────────────────────────────

@router.get("/grants")
async def list_grants(user=Depends(_get_user)):
    """Browse available grants. Real data from DB."""
    _require_member(user)
    cursor = _coll("hub_grants").find({}, {"_id": 0}).sort("created_at", -1).limit(100)
    return await cursor.to_list(100)


@router.post("/grants", status_code=201)
async def create_grant(payload: GrantCreate, user=Depends(_get_user)):
    """Create a grant listing (staff only)."""
    _require_staff(user)
    doc = {
        "id": uuid.uuid4().hex,
        "title": payload.title,
        "source": payload.source,
        "amount": payload.amount,
        "deadline": payload.deadline,
        "description": payload.description,
        "eligibility": payload.eligibility,
        "url": payload.url,
        "category": payload.category,
        "status": "open",
        "applications_count": 0,
        "created_by": getattr(user, "id", ""),
        "created_at": _now_iso(),
    }
    await _coll("hub_grants").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/grants/{grant_id}")
async def get_grant(grant_id: str, user=Depends(_get_user)):
    _require_member(user)
    doc = await _coll("hub_grants").find_one({"id": grant_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Grant not found.")
    return doc


@router.get("/grants/{grant_id}/applications")
async def list_grant_applications(grant_id: str, user=Depends(_get_user)):
    """List applications for a grant (staff sees all, member sees own)."""
    _require_member(user)
    query = {"grant_id": grant_id}
    if not _is_staff(user):
        query["user_id"] = getattr(user, "id", "")
    cursor = _coll("hub_grant_applications").find(query, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(50)


@router.post("/grants/applications", status_code=201)
async def apply_for_grant(payload: GrantApplication, user=Depends(_get_user)):
    """Submit a grant application with workflow tracking."""
    _require_member(user)
    grant = await _coll("hub_grants").find_one({"id": payload.grant_id}, {"_id": 0})
    if not grant:
        raise HTTPException(404, "Grant not found.")

    doc = {
        "id": uuid.uuid4().hex,
        "grant_id": payload.grant_id,
        "grant_title": grant["title"],
        "user_id": getattr(user, "id", ""),
        "project_title": payload.project_title,
        "project_description": payload.project_description,
        "requested_amount": payload.requested_amount,
        "timeline": payload.timeline,
        "status": "draft",  # draft → submitted → under_review → approved/declined
        "workflow_steps": [
            {"title": "Define project scope", "description": "Write a clear 1-page project summary", "completed": False},
            {"title": "Budget breakdown", "description": "Create a detailed budget with line items", "completed": False},
            {"title": "Impact statement", "description": "Describe community impact and measurable outcomes", "completed": False},
            {"title": "Letters of support", "description": "Gather 2-3 letters from community partners", "completed": False},
            {"title": "Final review", "description": "Review complete application package", "completed": False},
            {"title": "Submit", "description": "Submit before deadline", "completed": False},
        ],
        "notes": "",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await _coll("hub_grant_applications").insert_one(doc)

    # Update grant application count
    await _coll("hub_grants").update_one(
        {"id": payload.grant_id},
        {"$inc": {"applications_count": 1}},
    )

    doc.pop("_id", None)
    return doc


@router.patch("/grants/applications/{app_id}")
async def update_grant_application(app_id: str, updates: Dict[str, Any], user=Depends(_get_user)):
    """Update application status, workflow steps, or notes."""
    _require_member(user)
    doc = await _coll("hub_grant_applications").find_one({"id": app_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Application not found.")
    if doc["user_id"] != getattr(user, "id", "") and not _is_staff(user):
        raise HTTPException(403, "Not your application.")

    allowed = {"status", "workflow_steps", "notes", "project_title", "project_description", "requested_amount", "timeline"}
    update_fields = {k: v for k, v in updates.items() if k in allowed}
    update_fields["updated_at"] = _now_iso()

    await _coll("hub_grant_applications").update_one({"id": app_id}, {"$set": update_fields})
    return {**doc, **update_fields}


# ── Fundraising ───────────────────────────────────────────────────────────────

@router.get("/campaigns")
async def list_campaigns(user=Depends(_get_user)):
    """List fundraising campaigns. Integrates with existing scholarship funds."""
    _require_member(user)

    # Pull from both new campaigns and existing scholarship funds
    campaigns = await _coll("hub_campaigns").find({}, {"_id": 0}).sort("created_at", -1).limit(50).to_list(50)

    # Also pull existing scholarship funds as campaigns
    try:
        funds_cursor = _coll("scholarship_funds").find({}, {"_id": 0}).limit(50)
        funds = await funds_cursor.to_list(50)
        for f in funds:
            campaigns.append({
                "id": f.get("id", f.get("_id", "")),
                "title": f.get("name", "Scholarship Fund"),
                "goal_amount": f.get("target_amount", "$0"),
                "raised_amount": f.get("raised_amount", "$0"),
                "description": f.get("description", ""),
                "category": "education",
                "deadline": f.get("deadline", ""),
                "status": "active",
                "source": "scholarship",
                "donors_count": f.get("donors_count", 0),
                "created_at": f.get("created_at", ""),
            })
    except Exception:
        pass  # scholarships collection may not exist yet

    return campaigns


@router.post("/campaigns", status_code=201)
async def create_campaign(payload: CampaignCreate, user=Depends(_get_user)):
    """Create a fundraising campaign."""
    _require_member(user)
    doc = {
        "id": uuid.uuid4().hex,
        "title": payload.title,
        "goal_amount": payload.goal_amount,
        "raised_amount": "$0",
        "description": payload.description,
        "category": payload.category,
        "deadline": payload.deadline,
        "status": "active",
        "source": "hub",
        "donors_count": 0,
        "created_by": getattr(user, "id", ""),
        "created_at": _now_iso(),
    }
    await _coll("hub_campaigns").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str, user=Depends(_get_user)):
    _require_member(user)
    doc = await _coll("hub_campaigns").find_one({"id": campaign_id}, {"_id": 0})
    if not doc:
        # Try scholarship funds
        doc = await _coll("scholarship_funds").find_one({"id": campaign_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Campaign not found.")
    return doc


# ── Business Resources ────────────────────────────────────────────────────────

@router.get("/resources")
async def list_resources(category: str = "", user=Depends(_get_user)):
    """Browse business resources. Filterable by category."""
    _require_member(user)
    query = {}
    if category:
        query["category"] = category
    cursor = _coll("hub_resources").find(query, {"_id": 0}).sort("created_at", -1).limit(100)
    return await cursor.to_list(100)


@router.post("/resources", status_code=201)
async def create_resource(payload: ResourceCreate, user=Depends(_get_user)):
    """Add a business resource (staff only)."""
    _require_staff(user)
    doc = {
        "id": uuid.uuid4().hex,
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "url": payload.url,
        "file_url": payload.file_url,
        "tags": payload.tags,
        "downloads": 0,
        "created_by": getattr(user, "id", ""),
        "created_at": _now_iso(),
    }
    await _coll("hub_resources").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/resources/{resource_id}")
async def get_resource(resource_id: str, user=Depends(_get_user)):
    _require_member(user)
    doc = await _coll("hub_resources").find_one({"id": resource_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Resource not found.")
    return doc


# ── Workflows (cross-cutting) ────────────────────────────────────────────────

@router.get("/workflows")
async def list_workflows(user=Depends(_get_user)):
    """List active workflows across all areas."""
    _require_member(user)
    user_id = getattr(user, "id", "")
    cursor = _coll("hub_workflows").find(
        {"user_id": user_id, "status": {"$in": ["active", "paused"]}},
        {"_id": 0},
    ).sort("updated_at", -1).limit(20)
    return await cursor.to_list(20)


@router.post("/workflows", status_code=201)
async def create_workflow(title: str, area: str, steps: List[WorkflowStep], user=Depends(_get_user)):
    """Create a custom workflow across grant/fundraising/business areas."""
    _require_member(user)
    doc = {
        "id": uuid.uuid4().hex,
        "title": title,
        "area": area,  # grant, fundraising, business, custom
        "user_id": getattr(user, "id", ""),
        "steps": [s.model_dump() for s in steps],
        "current_step": 0,
        "status": "active",
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    await _coll("hub_workflows").insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.patch("/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, updates: Dict[str, Any], user=Depends(_get_user)):
    """Update workflow step completion or status."""
    _require_member(user)
    doc = await _coll("hub_workflows").find_one({"id": workflow_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Workflow not found.")
    if doc["user_id"] != getattr(user, "id", ""):
        raise HTTPException(403, "Not your workflow.")

    allowed = {"status", "current_step", "steps"}
    update_fields = {k: v for k, v in updates.items() if k in allowed}
    update_fields["updated_at"] = _now_iso()

    await _coll("hub_workflows").update_one({"id": workflow_id}, {"$set": update_fields})
    return {**doc, **update_fields}


# ── Dashboard (unified view) ─────────────────────────────────────────────────

@router.get("/dashboard")
async def hub_dashboard(user=Depends(_get_user)):
    """Unified dashboard: counts, recent activity, next steps across all areas."""
    _require_member(user)
    user_id = getattr(user, "id", "")

    # Grant stats
    grants_count = await _coll("hub_grants").count_documents({"status": "open"})
    my_apps = await _coll("hub_grant_applications").count_documents({"user_id": user_id})
    my_apps_active = await _coll("hub_grant_applications").count_documents({
        "user_id": user_id,
        "status": {"$in": ["draft", "submitted", "under_review"]},
    })

    # Campaign stats
    campaigns_count = await _coll("hub_campaigns").count_documents({"status": "active"})

    # Resource stats
    resources_count = await _coll("hub_resources").count_documents({})

    # Active workflows
    active_workflows = await _coll("hub_workflows").count_documents({
        "user_id": user_id,
        "status": "active",
    })

    # Next incomplete workflow step
    next_step = None
    workflow = await _coll("hub_workflows").find_one(
        {"user_id": user_id, "status": "active"},
        {"_id": 0},
    )
    if workflow and workflow.get("steps"):
        for i, step in enumerate(workflow["steps"]):
            if not step.get("completed"):
                next_step = {
                    "workflow": workflow["title"],
                    "step": step["title"],
                    "description": step.get("description", ""),
                    "step_index": i,
                    "total_steps": len(workflow["steps"]),
                }
                break

    return {
        "grants": {
            "open": grants_count,
            "my_applications": my_apps,
            "my_active": my_apps_active,
        },
        "fundraising": {
            "active_campaigns": campaigns_count,
        },
        "resources": {
            "total": resources_count,
        },
        "workflows": {
            "active": active_workflows,
            "next_step": next_step,
        },
    }


# ── Seed data (for initial population) ───────────────────────────────────────

SEED_RESOURCES = [
    {
        "title": "SBA Microloan Program",
        "description": "Loans up to $50,000 for small businesses and nonprofits. Ideal for startups, equipment purchases, and working capital.",
        "category": "financial",
        "url": "https://www.sba.gov/funding-programs/loans/microloans",
        "tags": ["sba", "loan", "startup", "small-business"],
    },
    {
        "title": "USDA Community Facilities Grant",
        "description": "Grants for essential community facilities in rural areas. Covers equipment, construction, and planning.",
        "category": "financial",
        "url": "https://www.rd.usda.gov/programs-services/community-facilities/community-facilities-grant-program",
        "tags": ["usda", "rural", "community", "grant"],
    },
    {
        "title": "SCORE Business Mentorship",
        "description": "Free business mentoring from experienced volunteers. Workshops, templates, and one-on-one coaching.",
        "category": "networking",
        "url": "https://www.score.org",
        "tags": ["mentorship", "free", "business", "coaching"],
    },
    {
        "title": "Florida SBDC Business Plan Templates",
        "description": "Free business plan templates and guides from the Florida Small Business Development Center.",
        "category": "templates",
        "url": "https://www.floridasbdc.org",
        "tags": ["florida", "template", "business-plan"],
    },
    {
        "title": "LegalZoom Nonprofit Formation",
        "description": "Step-by-step guide to forming a 501(c)(3) nonprofit, including required documents and filing procedures.",
        "category": "legal",
        "url": "https://www.legalzoom.com/articles/how-to-start-a-nonprofit",
        "tags": ["nonprofit", "legal", "501c3", "formation"],
    },
    {
        "title": "IRS Nonprofit Compliance Checklist",
        "description": "Annual compliance requirements for 501(c)(3) organizations: Form 990, state filings, board meeting minutes.",
        "category": "compliance",
        "url": "https://www.irs.gov/charities-non-profits",
        "tags": ["irs", "compliance", "nonprofit", "annual"],
    },
    {
        "title": "Canva for Nonprofits",
        "description": "Free Canva Pro account for registered nonprofits. Design marketing materials, social media, and presentations.",
        "category": "marketing",
        "url": "https://www.canva.com/canva-for-nonprofits/",
        "tags": ["design", "marketing", "free", "nonprofit"],
    },
    {
        "title": "Google Workspace for Nonprofits",
        "description": "Free Google Workspace (Gmail, Drive, Docs, Meet) for eligible nonprofits through Google for Nonprofits.",
        "category": "technology",
        "url": "https://www.google.com/nonprofits",
        "tags": ["google", "email", "free", "nonprofit", "technology"],
    },
    {
        "title": "Grant Writing Basics Guide",
        "description": "Step-by-step guide to writing effective grant proposals: problem statement, goals, budget, evaluation metrics.",
        "category": "templates",
        "url": "",
        "tags": ["grant-writing", "template", "guide"],
    },
    {
        "title": "Community Fundraising Playbook",
        "description": "Strategies for community-based fundraising: events, crowdfunding, social media campaigns, donor cultivation.",
        "category": "templates",
        "url": "",
        "tags": ["fundraising", "playbook", "community"],
    },
]


async def seed_hub_resources():
    """Seed initial business resources if collection is empty."""
    if db is None:
        return
    count = await _coll("hub_resources").count_documents({})
    if count > 0:
        return
    for r in SEED_RESOURCES:
        doc = {**r, "id": uuid.uuid4().hex, "downloads": 0, "created_by": "system", "created_at": _now_iso()}
        await _coll("hub_resources").insert_one(doc)
    logger.info("Seeded %d business resources into hub_resources", len(SEED_RESOURCES))
