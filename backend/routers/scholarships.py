"""
scholarships.py — Sponsor a Scholarship initiative
===================================================
Transparent, milestone-based scholarships for the M.O.R.E. Help Center.

Three-sided flow:
  SPONSOR  → picks a fund + tier (Full / Partial / Collective) → pledge →
             existing Lemon Squeezy → Gumroad checkout → webhook marks paid.
  APPLICANT → applies to a fund (financial need + community contribution).
  COMMITTEE → reviews applications (admin / Elder Council) → approval
             auto-matches the oldest un-assigned paid pledge → award created
             with milestones the committee verifies, so funds are only
             released against real progress.

Integrity rules (owner directive: every promise must be deliverable):
  - If payments are not configured yet, pledges are recorded with an explicit
    `grace` audit trail instead of a dead-end — the office can follow up and
    nothing is silently dropped.
  - Awards are milestone-based; milestone verification is audited.
  - All transitions are written to the audit log (sponsor + committee).
"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("lcewai")

router = APIRouter(prefix="/scholarships", tags=["scholarships"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = audit = notify = current_user = check_rate = None


def bind(_db, _audit, _notify, _current_user, _check_rate):
    global db, audit, notify, current_user, check_rate
    db, audit, notify, current_user, check_rate = _db, _audit, _notify, _current_user, _check_rate


async def _dep_current_user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)


PRODUCT_NAME = "Sponsor a Scholarship — M.O.R.E. Help Center"

# Default funds seeded the first time /funds is called with an empty collection.
DEFAULT_FUNDS = [
    {
        "id": "workforce-arts",
        "title": "Workforce & Arts Initiative Scholarship",
        "category": "workforce-arts",
        "description": "Covers certification fees, technical tools, software licenses, and trade or arts program costs for learners in the M.O.R.E. network.",
        "goal_cents": 50000,
        "status": "open",
    },
    {
        "id": "elder-caregiver",
        "title": "Elder & Caregiver Fund",
        "category": "elder-caregiver",
        "description": "Sponsors elders and caregivers — digital literacy, accessibility tools, and essential device or connectivity support.",
        "goal_cents": 35000,
        "status": "open",
    },
    {
        "id": "creator-tools",
        "title": "Creator Tools & Studio Fund",
        "category": "creator",
        "description": "Grants creators the equipment, software, and course access they need to turn their craft into income.",
        "goal_cents": 45000,
        "status": "open",
    },
]

# Standard milestone track for every award (verified by the committee).
DEFAULT_MILESTONES = [
    {"id": "enrolled", "title": "Enrollment confirmed — recipient begins the program", "status": "pending"},
    {"id": "m1", "title": "Milestone 1 — course/project progress verified", "status": "pending"},
    {"id": "complete", "title": "Completion verified — certificate or final deliverable", "status": "pending"},
]

TIER_LABELS = {"full": "Full Scholarship", "partial": "Partial Scholarship", "collective": "Collective (Multiple Recipients)"}


class PledgeReq(BaseModel):
    tier: str
    amount_cents: int
    dedication: Optional[str] = ""
    fund_id: Optional[str] = ""


class ApplyReq(BaseModel):
    fund_id: str
    need_statement: str
    contribution: str
    goal: str


class ReviewReq(BaseModel):
    status: str  # under_review | approved | denied
    note: Optional[str] = ""


class MilestoneReq(BaseModel):
    milestone_id: str
    verified: bool = True


class FundReq(BaseModel):
    title: str
    category: str
    description: str
    goal_cents: int


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _ensure_funds():
    try:
        if await db.scholarship_funds.count_documents({}) == 0:
            for f in DEFAULT_FUNDS:
                f = dict(f)
                f["raised_cents"] = 0
                f["created_at"] = _now()
                await db.scholarship_funds.insert_one(f)
    except Exception as e:
        logger.warning("scholarships: fund seed failed — %s", e)


async def _fund_or_404(fund_id: str) -> dict:
    fund = await db.scholarship_funds.find_one({"id": fund_id}, {"_id": 0})
    if not fund:
        raise HTTPException(404, "Fund not found")
    return fund


# ── Public: funds catalog ────────────────────────────────────────────────────
@router.get("/funds")
async def list_funds():
    """Public list of open scholarship funds with live progress."""
    await _ensure_funds()
    funds = await db.scholarship_funds.find({"status": "open"}, {"_id": 0}).sort("created_at", 1).to_list(50)
    for f in funds:
        f["progress_pct"] = round(f.get("raised_cents", 0) / max(f.get("goal_cents", 1), 1) * 100, 1)
    return {"funds": funds}


# ── Sponsor: pledge → checkout ───────────────────────────────────────────────
@router.post("/pledge")
async def create_pledge(req: PledgeReq, user=Depends(_dep_current_user)):
    """Record a sponsorship pledge and open the existing checkout pipeline.

    Returns {"url": ...} when payments are configured (redirect to pay), or a
    confirmation with grace=True when they are not — the pledge is still
    recorded and audited so the office can follow up. Nothing is dropped.
    """
    check_rate(f"scholarship_pledge:{user.id}", max_calls=10, window_sec=300)

    if req.tier not in TIER_LABELS:
        raise HTTPException(400, "tier must be full, partial, or collective")
    amount = int(req.amount_cents or 0)
    if amount < 500:
        raise HTTPException(400, "Minimum sponsorship is $5.00")

    if req.fund_id:
        await _fund_or_404(req.fund_id)

    pledge_id = str(uuid.uuid4())
    pledge = {
        "id": pledge_id,
        "user_id": user.id,
        "sponsor_name": getattr(user, "full_name", "") or user.id,
        "sponsor_email": getattr(user, "email", ""),
        "tier": req.tier,
        "amount_cents": amount,
        "dedication": (req.dedication or "").strip(),
        "fund_id": req.fund_id or "",
        "status": "pending",  # pending → paid (webhook) → matched (award)
        "provider_order_id": "",
        "created_at": _now(),
        "paid_at": None,
    }
    await db.scholarship_pledges.insert_one(pledge)
    await audit(user.id, "scholarship.pledge_created", target=pledge_id,
                meta={"tier": req.tier, "amount_cents": amount, "fund_id": req.fund_id or ""})

    # Reuse the exact same free-tier publishing pipeline as memberships/BYOK.
    from ai.publishing import _publish_lemon_squeezy, _publish_gumroad
    ls_key = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
    ls_store = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
    gr_key = os.environ.get("GUMROAD_API_KEY", "")

    if ls_key and ls_store:
        try:
            ls_result = await _publish_lemon_squeezy(
                name=PRODUCT_NAME,
                amount=amount,
                description=f"Sponsor a Scholarship ({TIER_LABELS[req.tier]}) — thank you for opening doors.",
            )
            url = ls_result.get("url") or ls_result.get("checkout_url")
            if url:
                await db.scholarship_pledges.update_one({"id": pledge_id}, {"$set": {"provider": "lemon_squeezy"}})
                await audit(user.id, "scholarship.checkout_created", target=pledge_id,
                            meta={"provider": "lemon_squeezy", "amount_cents": amount})
                return {"url": url, "pledge_id": pledge_id, "grace": False, "tier": req.tier}
        except Exception as e:
            logger.warning("scholarships: Lemon Squeezy checkout failed (%s) — falling through", e)

    if gr_key:
        try:
            gr_result = await _publish_gumroad(PRODUCT_NAME, "Sponsor a Scholarship — milestone-based giving.", amount)
            url = gr_result.get("url") or gr_result.get("checkout_url")
            if url:
                await db.scholarship_pledges.update_one({"id": pledge_id}, {"$set": {"provider": "gumroad"}})
                await audit(user.id, "scholarship.checkout_created", target=pledge_id,
                            meta={"provider": "gumroad", "amount_cents": amount})
                return {"url": url, "pledge_id": pledge_id, "grace": False, "tier": req.tier}
        except Exception as e:
            logger.warning("scholarships: Gumroad checkout failed (%s)", e)

    # Grace path — payments not configured: the pledge is real and audited.
    await db.scholarship_pledges.update_one({"id": pledge_id}, {"$set": {"status": "committed", "provider": "grace"}})
    await audit(user.id, "scholarship.pledge_committed_grace", target=pledge_id,
                meta={"tier": req.tier, "amount_cents": amount, "note": "payments not configured — office follow-up"})
    return {
        "url": None,
        "pledge_id": pledge_id,
        "grace": True,
        "tier": req.tier,
        "message": "Your sponsorship pledge is recorded. You'll hear from the office to complete payment — thank you for opening doors.",
    }


@router.get("/sponsor/mine")
async def my_pledges(user=Depends(_dep_current_user)):
    """A sponsor's pledges and their matched awards with recipient progress."""
    pledges = await db.scholarship_pledges.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    awards = await db.scholarship_awards.find({"pledge_user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    for a in awards:
        if a.get("application_id"):
            app = await db.scholarship_applications.find_one({"id": a["application_id"]}, {"_id": 0, "goal": 1, "status": 1})
            if app:
                a["recipient_goal"] = app.get("goal", "")
    return {"pledges": pledges, "awards": awards}


# ── Applicant: apply + track ─────────────────────────────────────────────────
@router.post("/apply")
async def apply_for_scholarship(req: ApplyReq, user=Depends(_dep_current_user)):
    """Submit a scholarship application. One active application per fund."""
    await _fund_or_404(req.fund_id)
    if len(req.need_statement.strip()) < 40:
        raise HTTPException(400, "Please describe your need in at least a few sentences.")
    if len(req.contribution.strip()) < 20:
        raise HTTPException(400, "Please tell us how you give back to your community.")

    existing = await db.scholarship_applications.find_one(
        {"user_id": user.id, "fund_id": req.fund_id, "status": {"$in": ["submitted", "under_review", "approved", "matched"]}},
        {"_id": 0, "id": 1},
    )
    if existing:
        raise HTTPException(409, "You already have an active application for this fund.")

    app_id = str(uuid.uuid4())
    app = {
        "id": app_id,
        "user_id": user.id,
        "applicant_name": getattr(user, "full_name", "") or user.id,
        "applicant_email": getattr(user, "email", ""),
        "fund_id": req.fund_id,
        "need_statement": req.need_statement.strip(),
        "contribution": req.contribution.strip(),
        "goal": req.goal.strip(),
        "status": "submitted",  # submitted → under_review → approved|denied → matched
        "review_note": "",
        "reviewed_by": "",
        "reviewed_at": None,
        "created_at": _now(),
    }
    await db.scholarship_applications.insert_one(app)
    await audit(user.id, "scholarship.applied", target=app_id, meta={"fund_id": req.fund_id})
    await notify(user.id, "Application Received",
                 "Your scholarship application is in the review queue. The committee reviews applications in the order they arrive.",
                 link="/scholarships/apply", kind="info")
    return {"application_id": app_id, "status": "submitted"}


@router.get("/applications/me")
async def my_applications(user=Depends(_dep_current_user)):
    apps = await db.scholarship_applications.find({"user_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    funds = {f["id"]: f["title"] for f in await db.scholarship_funds.find({}, {"_id": 0, "id": 1, "title": 1}).to_list(50)}
    for a in apps:
        a["fund_title"] = funds.get(a.get("fund_id", ""), "")
    return {"applications": apps}


# ── Committee / admin ────────────────────────────────────────────────────────
def _require_admin(user):
    if getattr(user, "role", "") not in ("admin", "executive_admin"):
        raise HTTPException(403, "Committee access required")


@router.get("/admin/applications")
async def admin_applications(status: str = "submitted", user=Depends(_dep_current_user)):
    _require_admin(user)
    q = {"status": status} if status != "all" else {}
    apps = await db.scholarship_applications.find(q, {"_id": 0}).sort("created_at", 1).to_list(100)
    funds = {f["id"]: f["title"] for f in await db.scholarship_funds.find({}, {"_id": 0, "id": 1, "title": 1}).to_list(50)}
    for a in apps:
        a["fund_title"] = funds.get(a.get("fund_id", ""), "")
    return {"applications": apps}


@router.patch("/admin/applications/{app_id}")
async def review_application(app_id: str, req: ReviewReq, user=Depends(_dep_current_user)):
    """Committee review. Approving auto-matches the oldest paid pledge to the
    application (same fund first) and creates a milestone-tracked award."""
    _require_admin(user)
    if req.status not in ("under_review", "approved", "denied"):
        raise HTTPException(400, "status must be under_review, approved, or denied")

    app = await db.scholarship_applications.find_one({"id": app_id}, {"_id": 0})
    if not app:
        raise HTTPException(404, "Application not found")

    update = {
        "status": req.status,
        "review_note": (req.note or "").strip(),
        "reviewed_by": user.id,
        "reviewed_at": _now(),
    }
    await db.scholarship_applications.update_one({"id": app_id}, {"$set": update})
    await audit(user.id, f"scholarship.{req.status}", target=app_id, meta={"note": req.note or ""})
    await notify(app["user_id"], "Scholarship Update",
                 f"Your application was {req.status}." if req.status != "under_review" else "Your application is under review.",
                 link="/scholarships/apply", kind="info" if req.status == "under_review" else "success" if req.status == "approved" else "error")

    if req.status == "approved":
        # Match the oldest paid, un-assigned pledge (same fund preferred).
        q = {"status": "paid"}
        if app.get("fund_id"):
            q["$or"] = [{"fund_id": app["fund_id"]}, {"fund_id": ""}]
        pledge = await db.scholarship_pledges.find_one(q, {"_id": 0}, sort=[("paid_at", 1), ("created_at", 1)])
        if not pledge:
            # No funded pledge yet — the award waits for one (status: reserved).
            award_id = str(uuid.uuid4())
            await db.scholarship_awards.insert_one({
                "id": award_id,
                "application_id": app_id,
                "pledge_id": "",
                "pledge_user_id": "",
                "amount_cents": 0,
                "status": "reserved",
                "milestones": [dict(m) for m in DEFAULT_MILESTONES],
                "created_at": _now(),
            })
            await audit(user.id, "scholarship.award_reserved", target=award_id, meta={"application_id": app_id})
            return {"application_id": app_id, "status": "approved", "award_status": "reserved",
                    "message": "Approved — waiting for a funded pledge to be matched."}

        award_id = str(uuid.uuid4())
        await db.scholarship_awards.insert_one({
            "id": award_id,
            "application_id": app_id,
            "pledge_id": pledge["id"],
            "pledge_user_id": pledge["user_id"],
            "amount_cents": pledge["amount_cents"],
            "status": "active",
            "milestones": [dict(m) for m in DEFAULT_MILESTONES],
            "created_at": _now(),
        })
        await db.scholarship_pledges.update_one({"id": pledge["id"]}, {"$set": {"status": "matched"}})
        await db.scholarship_applications.update_one({"id": app_id}, {"$set": {"status": "matched"}})
        await audit(user.id, "scholarship.matched", target=award_id,
                    meta={"application_id": app_id, "pledge_id": pledge["id"], "amount_cents": pledge["amount_cents"]})
        await notify(pledge["user_id"], "Your Sponsorship Is Matched",
                     "Your sponsorship has been matched to a scholar. Track their milestones in your sponsor view.",
                     link="/sponsor", kind="success")
        return {"application_id": app_id, "status": "matched", "award_status": "active", "award_id": award_id}

    return {"application_id": app_id, "status": req.status}


@router.get("/admin/awards")
async def admin_awards(user=Depends(_dep_current_user)):
    _require_admin(user)
    awards = await db.scholarship_awards.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    apps = {a["id"]: a for a in await db.scholarship_applications.find({}, {"_id": 0, "id": 1, "applicant_name": 1, "goal": 1, "fund_id": 1}).to_list(200)}
    for a in awards:
        app = apps.get(a.get("application_id", ""))
        if app:
            a["applicant_name"] = app.get("applicant_name", "")
            a["recipient_goal"] = app.get("goal", "")
    return {"awards": awards}


@router.patch("/admin/awards/{award_id}/milestones/{milestone_id}")
async def verify_milestone(award_id: str, milestone_id: str, req: MilestoneReq, user=Depends(_dep_current_user)):
    """Committee verifies a recipient milestone — funds release against progress."""
    _require_admin(user)
    award = await db.scholarship_awards.find_one({"id": award_id}, {"_id": 0})
    if not award:
        raise HTTPException(404, "Award not found")
    new_milestones = []
    for m in award.get("milestones", []):
        if m.get("id") == milestone_id:
            m["status"] = "verified" if req.verified else "pending"
            m["verified_at"] = _now() if req.verified else None
            m["verified_by"] = user.id if req.verified else ""
        new_milestones.append(m)
    await db.scholarship_awards.update_one({"id": award_id}, {"$set": {"milestones": new_milestones}})
    await audit(user.id, "scholarship.milestone_verified", target=award_id, meta={"milestone_id": milestone_id})
    return {"award_id": award_id, "milestones": new_milestones}


@router.get("/admin/pledges")
async def admin_pledges(user=Depends(_dep_current_user)):
    _require_admin(user)
    pledges = await db.scholarship_pledges.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"pledges": pledges}


@router.post("/admin/funds")
async def create_fund(req: FundReq, user=Depends(_dep_current_user)):
    _require_admin(user)
    if req.goal_cents < 1000:
        raise HTTPException(400, "Fund goal must be at least $10.00")
    fund_id = str(uuid.uuid4())[:12]
    await db.scholarship_funds.insert_one({
        "id": fund_id,
        "title": req.title.strip(),
        "category": req.category.strip(),
        "description": req.description.strip(),
        "goal_cents": req.goal_cents,
        "raised_cents": 0,
        "status": "open",
        "created_at": _now(),
    })
    await audit(user.id, "scholarship.fund_created", target=fund_id, meta={"title": req.title})
    return {"fund_id": fund_id}
