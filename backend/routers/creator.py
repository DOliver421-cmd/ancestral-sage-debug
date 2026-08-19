"""
creator — Creator Course Publishing — course CRUD, checkout, enrollments, earnings, payouts, bank accounts, public profiles.

Extracted verbatim from backend/server.py (monolith refactor, slice 12).
Shared state (db, current_user, ...) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['creator', 'courses', 'payouts'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
notify = None
JWT_SECRET = None
JWT_ALGO = "HS256"


def bind(_db, _current_user, _audit, _notify, _jwt_secret, _jwt_algo):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, notify, JWT_SECRET, JWT_ALGO
    
    db = _db
    current_user = _current_user
    audit = _audit
    notify = _notify
    JWT_SECRET = _jwt_secret
    JWT_ALGO = _jwt_algo


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "priority_member": 2, "instructor": 2, "creative_partner": 2, "site_support": 3, "admin": 3, "executive_admin": 4}
Role = Literal["student", "priority_member", "instructor", "creative_partner", "site_support", "admin", "executive_admin"]


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    associate: Optional[str] = None
    is_active: bool = True
    must_change_password: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    avatar_url: Optional[str] = None
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()
    because require_role is bound after this module loads (no import-time call)."""
    def dep(user: User = Depends(_dep_current_user)) -> User:
        if not user or user.role not in ROLE_RANK or not any(
            ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get(r, 0) for r in roles
        ):
            raise HTTPException(403, "Insufficient permissions")
        return user
    return dep


import jwt
from routers.payments import PAYMENTS_ENABLED
# ── Creator Course Publishing ─────────────────────────────────────────────────
# Any authenticated user can be a creator. Courses live in db.creator_courses.
# Sections are text-based (title + content). Price in cents (0 = free).
# Status: "draft" (private, only creator sees) | "published" (public catalog).

class CourseSection(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=20000)

class CreateCourseReq(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = Field(default="", max_length=2000)
    category: str = Field(default="general", max_length=100)
    price_cents: int = Field(default=0, ge=0, le=99900)
    sections: List[CourseSection] = Field(default_factory=list)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)

class UpdateCourseReq(BaseModel):

    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    category: Optional[str] = Field(default=None, max_length=100)
    price_cents: Optional[int] = Field(default=None, ge=0, le=99900)
    sections: Optional[List[CourseSection]] = None
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    status: Optional[Literal["draft", "published"]] = None


@router.post("/creator/courses", status_code=201)
async def creator_create_course(body: CreateCourseReq, user: User = Depends(_dep_current_user)):
    """Create a new course draft. Any authenticated user can create."""
    course_id = str(uuid.uuid4())
    slug = re.sub(r"[^a-z0-9]+", "-", body.title.lower()).strip("-")[:60] + "-" + course_id[:8]
    doc = {
        "course_id": course_id,
        "creator_id": user.id,
        "creator_name": user.full_name,
        "title": body.title,
        "description": body.description,
        "category": body.category,
        "price_cents": body.price_cents,
        "sections": [s.model_dump() for s in body.sections],
        "thumbnail_url": body.thumbnail_url,
        "slug": slug,
        "status": "draft",
        "enrollment_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.creator_courses.insert_one(doc)
    await audit(user.id, "creator.course.created", meta={"course_id": course_id, "title": body.title})
    doc.pop("_id", None)
    return {"course": doc}


@router.get("/creator/courses")
async def creator_list_my_courses(user: User = Depends(_dep_current_user)):
    """List all courses owned by the current user."""
    courses = await db.creator_courses.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"courses": courses}


@router.get("/creator/courses/published")
async def creator_published_catalog(
    category: str = "",
    skip: int = 0,
    limit: int = 24,
):
    """Public catalog — published courses from all creators."""
    query: dict = {"status": "published"}
    if category:
        query["category"] = category
    courses = await db.creator_courses.find(
        query,
        {"_id": 0, "sections": 0},
    ).sort("created_at", -1).skip(skip).limit(min(limit, 50)).to_list(length=50)
    total = await db.creator_courses.count_documents(query)
    return {"courses": courses, "total": total}


@router.get("/creator/courses/{course_id}")
async def creator_get_course(course_id: str, user: User = Depends(_dep_current_user)):
    """Get full course detail. Drafts only visible to their creator."""
    course = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["status"] == "draft" and course["creator_id"] != user.id:
        raise HTTPException(403, "Not your draft")
    return {"course": course}


@router.patch("/creator/courses/{course_id}")
async def creator_update_course(
    course_id: str,
    body: UpdateCourseReq,
    user: User = Depends(_dep_current_user),
):
    """Update a course. Only the creator can edit."""
    course = await db.creator_courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["creator_id"] != user.id:
        raise HTTPException(403, "Not your course")
    update: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if body.title is not None:
        update["title"] = body.title
        update["slug"] = re.sub(r"[^a-z0-9]+", "-", body.title.lower()).strip("-")[:60] + "-" + course_id[:8]
    if body.description is not None:
        update["description"] = body.description
    if body.category is not None:
        update["category"] = body.category
    if body.price_cents is not None:
        update["price_cents"] = body.price_cents
    if body.sections is not None:
        update["sections"] = [s.model_dump() for s in body.sections]
    if body.thumbnail_url is not None:
        update["thumbnail_url"] = body.thumbnail_url
    if body.status is not None:
        update["status"] = body.status
    await db.creator_courses.update_one({"course_id": course_id}, {"$set": update})
    await audit(user.id, "creator.course.updated", meta={"course_id": course_id, "fields": list(update.keys())})
    updated = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    return {"course": updated}


@router.delete("/creator/courses/{course_id}", status_code=204)
async def creator_delete_course(course_id: str, user: User = Depends(_dep_current_user)):
    """Soft-delete (archive) a course. Only the creator can delete."""
    course = await db.creator_courses.find_one({"course_id": course_id})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["creator_id"] != user.id:
        raise HTTPException(403, "Not your course")
    await db.creator_courses.update_one(
        {"course_id": course_id},
        {"$set": {"status": "archived", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await audit(user.id, "creator.course.deleted", meta={"course_id": course_id})


# ── Creator Course Checkout ───────────────────────────────────────────────────

@router.post("/creator/courses/{course_id}/checkout")
async def creator_course_checkout(course_id: str, user: User = Depends(_dep_current_user)):
    """Initiate Lemon Squeezy -> Gumroad checkout for a published creator course."""
    if not PAYMENTS_ENABLED:
        raise HTTPException(501, "Payments are not configured yet — add Lemon Squeezy or Gumroad keys.")
    course = await db.creator_courses.find_one({"course_id": course_id}, {"_id": 0})
    if not course:
        raise HTTPException(404, "Course not found")
    if course["status"] != "published":
        raise HTTPException(400, "Course is not available for purchase")
    if course["creator_id"] == user.id:
        raise HTTPException(400, "You cannot buy your own course")

    amount = course["price_cents"]
    if amount == 0:
        # Free course — enroll directly
        await db.creator_courses.update_one({"course_id": course_id}, {"$inc": {"enrollment_count": 1}})
        await db.creator_enrollments.update_one(

            {"course_id": course_id, "user_id": user.id},
            {"$setOnInsert": {"enrolled_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        return {"enrolled": True, "free": True}

    from ai.publishing import _publish_lemon_squeezy, _publish_gumroad

    ls_result = await _publish_lemon_squeezy(
        name=course["title"],
        description=course.get("description", "")[:500],
        price_cents=amount,
        persona="creator_course",
    )
    if ls_result:
        await audit(user.id, "creator.course.checkout", meta={"course_id": course_id, "amount": amount, "provider": "lemon_squeezy"})
        return {"url": ls_result["url"]}

    gr_result = await _publish_gumroad(course["title"], course.get("description", "")[:500], amount)
    if gr_result:
        await audit(user.id, "creator.course.checkout", meta={"course_id": course_id, "amount": amount, "provider": "gumroad"})
        return {"url": gr_result["url"]}

    raise HTTPException(
        501,
        "Payments are not configured yet. Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID "
        "(free tier) or GUMROAD_API_KEY to enable course sales.",
    )


@router.get("/creator/enrollments/me")
async def creator_enrollments_me(user: User = Depends(_dep_current_user)):
    """Return the list of course_ids the current user is enrolled in (free + paid)."""
    docs = await db.creator_enrollments.find(
        {"user_id": user.id},
        {"_id": 0, "course_id": 1},
    ).to_list(length=500)
    return {"enrolled_course_ids": [d["course_id"] for d in docs]}


# ── Creator Earnings & Payouts ────────────────────────────────────────────────
# Platform retains 30%; creator keeps 70%. Payouts accumulate monthly.
# "Pending" = earned but not yet disbursed. "paid" = payout sent.

class SaveBankAccountReq(BaseModel):
    account_holder_name: str = Field(..., min_length=2, max_length=200)
    routing_number: str = Field(..., min_length=9, max_length=9, pattern=r"^\d{9}$")
    account_number: str = Field(..., min_length=4, max_length=17, pattern=r"^\d+$")
    account_type: Literal["checking", "savings"] = "checking"


@router.get("/creator/earnings")
async def creator_earnings_summary(user: User = Depends(_dep_current_user)):
    """Monthly earnings summary for the current creator."""
    entries = await db.creator_earnings.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=500)

    # Group by period
    by_period: dict = {}
    for e in entries:
        p = e["period"]
        if p not in by_period:
            by_period[p] = {"period": p, "gross_cents": 0, "creator_share_cents": 0, "sales": 0, "payout_status": "pending"}
        by_period[p]["gross_cents"] += e["gross_cents"]
        by_period[p]["creator_share_cents"] += e["creator_share_cents"]
        by_period[p]["sales"] += 1
        if e.get("payout_status") == "paid":
            by_period[p]["payout_status"] = "paid"

    months = sorted(by_period.values(), key=lambda x: x["period"], reverse=True)
    total_earned = sum(e["creator_share_cents"] for e in entries)
    total_pending = sum(e["creator_share_cents"] for e in entries if e.get("payout_status") == "pending")
    total_paid = sum(e["creator_share_cents"] for e in entries if e.get("payout_status") == "paid")

    # Check if bank account on file
    bank = await db.creator_bank_accounts.find_one({"creator_id": user.id}, {"_id": 0, "account_number": 0, "routing_number": 0})

    return {
        "total_earned_cents": total_earned,
        "total_pending_cents": total_pending,
        "total_paid_cents": total_paid,
        "months": months,
        "bank_account_on_file": bank is not None,
        "bank_account_holder": (bank or {}).get("account_holder_name"),
        "bank_account_type": (bank or {}).get("account_type"),
    }


@router.get("/creator/payouts")
async def creator_payout_history(user: User = Depends(_dep_current_user)):
    """Payout disbursement history for the current creator."""
    payouts = await db.creator_payouts.find(
        {"creator_id": user.id},
        {"_id": 0},
    ).sort("created_at", -1).to_list(length=100)
    return {"payouts": payouts}


@router.post("/creator/bank-account", status_code=201)
async def creator_save_bank_account(body: SaveBankAccountReq, user: User = Depends(_dep_current_user)):
    """Save or update creator bank account for payouts.
    Account number stored masked (last 4 digits only after save)."""
    masked = "****" + body.account_number[-4:]
    await db.creator_bank_accounts.update_one(
        {"creator_id": user.id},
        {"$set": {
            "creator_id": user.id,
            "account_holder_name": body.account_holder_name,
            "routing_number": body.routing_number,  # stored for payout processing
            "account_number_masked": masked,
            "account_type": body.account_type,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }, "$setOnInsert": {"created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    await audit(user.id, "creator.bank_account.saved", meta={"masked": masked})
    return {"saved": True, "account_number_masked": masked}


@router.get("/creator/bank-account")
async def creator_get_bank_account(user: User = Depends(_dep_current_user)):
    """Get masked bank account info on file."""
    bank = await db.creator_bank_accounts.find_one(
        {"creator_id": user.id},
        {"_id": 0, "routing_number": 0},
    )
    if not bank:
        return {"bank_account": None}
    return {"bank_account": bank}


# Admin endpoint — process monthly payouts (executive_admin only)
@router.post("/admin/creator-payouts/process")
async def admin_process_creator_payouts(user: User = Depends(_require_rank("executive_admin"))):
    """Mark all pending earnings as paid and write payout records.
    In production this triggers ACH transfer; here it records the intent."""
    period = datetime.now(timezone.utc).strftime("%Y-%m")
    # Find all creators with pending earnings this period
    pipeline = [
        {"$match": {"payout_status": "pending", "period": {"$lt": period}}},
        {"$group": {"_id": "$creator_id", "total_cents": {"$sum": "$creator_share_cents"}, "count": {"$sum": 1}}},
    ]
    summaries = await db.creator_earnings.aggregate(pipeline).to_list(length=500)
    payouts_created = []
    for s in summaries:
        creator_id = s["_id"]
        amount = s["total_cents"]
        if amount < 100:
            continue  # below $1 minimum, roll over
        bank = await db.creator_bank_accounts.find_one({"creator_id": creator_id})
        payout_id = str(uuid.uuid4())
        await db.creator_payouts.insert_one({
            "payout_id": payout_id,
            "creator_id": creator_id,
            "amount_cents": amount,
            "sale_count": s["count"],
            "bank_on_file": bank is not None,
            "status": "processing",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        # Mark earnings as paid
        await db.creator_earnings.update_many(
            {"creator_id": creator_id, "payout_status": "pending", "period": {"$lt": period}},
            {"$set": {"payout_status": "paid", "payout_id": payout_id}},
        )
        await notify(creator_id, "Payout Initiated",
                     f"Your payout of ${amount/100:.2f} has been initiated. Allow 2-3 business days.",
                     link="/creator/earnings", kind="success")
        payouts_created.append({"creator_id": creator_id, "amount_cents": amount})
    await audit(user.id, "admin.creator_payouts.processed", meta={"count": len(payouts_created)})
    return {"payouts_initiated": len(payouts_created), "detail": payouts_created}


# ── Creator Public Profiles ───────────────────────────────────────────────────
# Creators claim a slug and edit their own profile. Public GET by slug.
# Hardcoded profiles in the frontend are the fallback when no DB record exists.

class CreatorSocialLink(BaseModel):
    platform: str = Field(..., max_length=100)
    handle: str = Field(default="", max_length=100)
    url: str = Field(..., max_length=500)
    note: str = Field(default="", max_length=300)

class CreatorOffering(BaseModel):
    icon: str = Field(default="✨", max_length=10)
    title: str = Field(..., max_length=200)
    desc: str = Field(default="", max_length=1000)

class CreatorCommerceItem(BaseModel):
    label: str = Field(..., max_length=200)
    desc: str = Field(default="", max_length=500)
    url: str = Field(..., max_length=500)

class UpsertCreatorProfileReq(BaseModel):
    slug: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-z0-9-]+$")
    display_name: str = Field(..., min_length=1, max_length=100)
    title: str = Field(default="", max_length=200)
    tagline: str = Field(default="", max_length=300)
    bio: str = Field(default="", max_length=5000)
    pronouns: str = Field(default="", max_length=50)
    location: str = Field(default="", max_length=100)
    avatar: str = Field(default="✨", max_length=10)
    socials: List[CreatorSocialLink] = Field(default_factory=list)
    more_offerings: List[CreatorOffering] = Field(default_factory=list)
    commerce: List[CreatorCommerceItem] = Field(default_factory=list)


@router.get("/creator/profile/me")
async def get_my_creator_profile(user: User = Depends(_dep_current_user)):
    """Get the current user's creator profile (if claimed)."""
    profile = await db.creator_profiles.find_one({"user_id": user.id}, {"_id": 0})
    return {"profile": profile}


@router.put("/creator/profile")
async def upsert_creator_profile(body: UpsertCreatorProfileReq, user: User = Depends(_dep_current_user)):
    """Create or update the current user's creator profile."""
    # Ensure slug is not already taken by someone else
    existing = await db.creator_profiles.find_one({"slug": body.slug})
    if existing and existing.get("user_id") != user.id:
        raise HTTPException(409, "That profile URL is already taken. Choose a different slug.")

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user.id,
        "slug": body.slug,
        "display_name": body.display_name,
        "title": body.title,
        "tagline": body.tagline,
        "bio": body.bio,
        "pronouns": body.pronouns,
        "location": body.location,
        "avatar": body.avatar,
        "socials": [s.model_dump() for s in body.socials],
        "more_offerings": [o.model_dump() for o in body.more_offerings],
        "commerce": [c.model_dump() for c in body.commerce],
        "updated_at": now,
    }
    await db.creator_profiles.update_one(
        {"user_id": user.id},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    await audit(user.id, "creator.profile.saved", meta={"slug": body.slug})
    saved = await db.creator_profiles.find_one({"user_id": user.id}, {"_id": 0})
    return {"profile": saved}


@router.get("/creator/profiles/public")
async def list_public_creator_profiles(limit: int = 50):
    """Public — list creator profiles for the Creators directory page."""
    profiles = await db.creator_profiles.find(
        {},
        {"_id": 0, "user_id": 0, "encrypted_key": 0},
    ).sort("created_at", -1).limit(min(limit, 100)).to_list(length=100)
    return {"profiles": profiles, "total": len(profiles)}


@router.get("/creator/profile/{slug}")
async def get_creator_profile_by_slug(slug: str, authorization: Optional[str] = Header(None)):
    """Public — get a creator profile by slug. Returns is_owner=True if the requester owns it."""
    profile = await db.creator_profiles.find_one({"slug": slug}, {"_id": 0})
    if not profile:
        raise HTTPException(404, "Creator profile not found")
    # Determine ownership without requiring auth (public endpoint)
    requester_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            payload = jwt.decode(authorization.split(" ", 1)[1], JWT_SECRET, algorithms=[JWT_ALGO])
            requester_id = payload.get("sub")
        except Exception:
            pass
    is_owner = requester_id is not None and profile.get("user_id") == requester_id
    profile_out = {k: v for k, v in profile.items() if k != "user_id"}
    profile_out["is_owner"] = is_owner
    return {"profile": profile_out}
