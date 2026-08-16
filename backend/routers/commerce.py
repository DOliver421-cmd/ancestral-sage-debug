"""
Commerce + governance — admin sites/inventory/checkout, platform flags, admin audit, run-checks, verify, admin payments/discounts, pricing.

Extracted verbatim from backend/server.py (monolith refactor, slice 11).
Shared state (db, current_user, audit) is bound by server.py via bind()
at include time — no circular imports.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File
from pydantic import BaseModel, ConfigDict, Field
from seed_credentials import CREDENTIALS

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["admin", "commerce"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
run_escalation_check = None
run_engagement_check = None
_discount_manager = None


def bind(_db, _current_user, _audit, _run_escalation_check, _run_engagement_check, _discount_mgr):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, run_escalation_check, run_engagement_check, _discount_manager
    db = _db
    current_user = _current_user
    audit = _audit
    run_escalation_check = _run_escalation_check
    run_engagement_check = _run_engagement_check
    _discount_manager = _discount_mgr


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}
Role = Literal["student", "instructor", "admin", "executive_admin", "creative_partner"]


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
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            logger.warning("Unauthorized access attempt — insufficient privileges (user=%s, role=%s)", user.id, user.role)
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ═════════════════════════════════════════════════════════════════════════════
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
@router.get("/admin/sites")
async def list_sites(user: User = Depends(_require_rank("admin", "instructor"))):
    docs = await db.sites.find({}, {"_id": 0}).to_list(100)
    return docs


@router.post("/admin/sites")
async def create_site(payload: dict, user: User = Depends(_require_rank("admin"))):
    if not payload.get("slug") or not payload.get("name"):
        raise HTTPException(400, "slug and name required")
    if await db.sites.find_one({"slug": payload["slug"]}):
        raise HTTPException(400, "Site slug exists")
    doc = {
        "id": str(uuid.uuid4()),
        "slug": payload["slug"],
        "name": payload["name"],
        "address": payload.get("address", ""),
        "capacity": int(payload.get("capacity", 0)),
    }
    await db.sites.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/admin/inventory")
async def list_inventory(site_slug: Optional[str] = None, user: User = Depends(_require_rank("admin", "instructor"))):
    q = {"site_slug": site_slug} if site_slug else {}
    items = await db.inventory.find(q, {"_id": 0}).to_list(500)
    return items


@router.post("/admin/inventory")
async def add_inventory(payload: dict, user: User = Depends(_require_rank("admin"))):
    required = ["sku", "name", "category", "quantity_total", "site_slug"]
    if any(k not in payload for k in required):
        raise HTTPException(400, f"Required: {required}")
    if await db.inventory.find_one({"sku": payload["sku"]}):
        raise HTTPException(400, "SKU exists")
    doc = {
        "id": str(uuid.uuid4()),
        "sku": payload["sku"],
        "name": payload["name"],
        "category": payload["category"],
        "site_slug": payload["site_slug"],
        "quantity_total": int(payload["quantity_total"]),
        "quantity_available": int(payload["quantity_total"]),
    }
    await db.inventory.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.post("/admin/checkout")
async def checkout_tool(payload: dict, user: User = Depends(_require_rank("instructor", "admin"))):
    sku = payload.get("sku")
    student_id = payload.get("user_id")
    qty = int(payload.get("quantity", 1))
    if not sku or not student_id:
        raise HTTPException(400, "sku and user_id required")
    item = await db.inventory.find_one({"sku": sku}, {"_id": 0})
    if not item:
        raise HTTPException(404, "Item not found")
    if item["quantity_available"] < qty:
        raise HTTPException(400, f"Only {item['quantity_available']} available")
    co = {
        "id": str(uuid.uuid4()),
        "sku": sku,
        "user_id": student_id,
        "quantity": qty,
        "checked_out_by": user.id,
        "checked_out_at": datetime.now(timezone.utc).isoformat(),
        "returned_at": None,
        "status": "out",
    }
    await db.tool_checkouts.insert_one(co)
    await db.inventory.update_one({"sku": sku}, {"$inc": {"quantity_available": -qty}})
    co.pop("_id", None)
    return co


@router.post("/admin/checkout/{checkout_id}/return")
async def return_tool(checkout_id: str, user: User = Depends(_require_rank("instructor", "admin"))):
    co = await db.tool_checkouts.find_one({"id": checkout_id}, {"_id": 0})
    if not co or co["status"] == "returned":
        raise HTTPException(400, "Invalid or already returned")
    await db.tool_checkouts.update_one(
        {"id": checkout_id},
        {"$set": {"status": "returned", "returned_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.inventory.update_one({"sku": co["sku"]}, {"$inc": {"quantity_available": co["quantity"]}})
    return {"ok": True}


@router.get("/admin/checkouts")
async def list_checkouts(status: Optional[str] = None, user: User = Depends(_require_rank("instructor", "admin"))):
    q = {"status": status} if status else {}
    docs = await db.tool_checkouts.find(q, {"_id": 0}).sort("checked_out_at", -1).to_list(500)
    user_ids = list({d["user_id"] for d in docs})
    skus = list({d["sku"] for d in docs})
    users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    items = await db.inventory.find({"sku": {"$in": skus}}, {"_id": 0}).to_list(500)
    u_map = {u["id"]: u for u in users}
    i_map = {i["sku"]: i for i in items}
    for d in docs:
        d["user"] = u_map.get(d["user_id"])
        d["item"] = i_map.get(d["sku"])
    return docs


# -- NOTIFICATIONS --
@router.get("/admin/platform/flags")
async def get_platform_flags(user: User = Depends(_require_rank("executive_admin"))):
    """Return all platform feature flags. Executive only."""
    doc = await db.platform_flags.find_one({"_id": "flags"}, {"_id": 0})
    if not doc:
        return {"flags": {}}
    return {"flags": doc.get("flags", {})}


@router.post("/admin/platform/flags/{flag}")
async def set_platform_flag(
    flag: str,
    payload: dict,
    user: User = Depends(_require_rank("executive_admin")),
):
    """Set a platform feature flag (true/false). Executive only.
    Body: { value: bool, reason?: str }
    Supported flags: platform_locked, marketplace_disabled, ai_disabled,
                     community_disabled, labs_disabled
    """
    ALLOWED = {"platform_locked", "marketplace_disabled", "ai_disabled",
               "community_disabled", "labs_disabled"}
    if flag not in ALLOWED:
        raise HTTPException(400, f"Unknown flag '{flag}'. Allowed: {', '.join(sorted(ALLOWED))}")
    value = bool(payload.get("value", True))
    reason = (payload.get("reason") or "").strip()
    now = datetime.now(timezone.utc).isoformat()
    await db.platform_flags.update_one(
        {"_id": "flags"},
        {"$set": {
            f"flags.{flag}": {
                "enabled": value,
                "set_by": user.id,
                "set_at": now,
                "reason": reason,
            }
        }},
        upsert=True,
    )
    await audit(user.id, f"platform_flag:{flag}:{value}", {"reason": reason})
    return {"flag": flag, "enabled": value, "set_at": now}


@router.get("/admin/audit")
async def view_audit(
    limit: int = 200,
    action: Optional[str] = None,
    actor_id: Optional[str] = None,
    user: User = Depends(_require_rank("admin")),
):
    query: dict = {}
    if action:
        query["action"] = {"$regex": re.escape(action), "$options": "i"}
    if actor_id:
        query["actor_id"] = actor_id
    docs = await db.audit_log.find(query, {"_id": 0}).sort("at", -1).to_list(min(limit, 1000))
    user_ids = list({d["actor_id"] for d in docs if d.get("actor_id")})
    users_list = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "password_hash": 0}).to_list(1000)
    umap = {u["id"]: u for u in users_list}
    for d in docs:
        d["actor"] = umap.get(d.get("actor_id")) if d.get("actor_id") else None
    return docs


# -- PROGRAM ANALYTICS (admin) --
@router.post("/admin/run-checks")
async def admin_run_checks(user: User = Depends(_require_rank("admin"))):
    """Admin-triggered: run escalation + engagement checks immediately.

    Normally these run at server startup. Use this to trigger a fresh scan
    without waiting for a restart — useful at the start of each program day.
    Returns a summary of what was flagged.
    """
    await run_escalation_check()
    await run_engagement_check()
    await audit(user.id, "admin.checks.manual_trigger")
    return {"ok": True, "message": "Escalation and engagement checks completed. Check notifications for flags."}


# ─── Public Credential Verification ─────────────────────────────────────────

@router.get("/verify/{code}")
async def verify_credential(code: str):
    """Public credential verification — no authentication required.

    Any employer, partner, or third party can confirm a credential is real by
    visiting /api/verify/{code}. The code appears on every issued credential
    and in the credential PDF.
    """
    cred_doc = await db.user_credentials.find_one(
        {"verification_code": code}, {"_id": 0}
    )
    if not cred_doc:
        raise HTTPException(404, "Credential not found. The code may be invalid or the credential may have been revoked.")

    user_doc = await db.users.find_one(
        {"id": cred_doc["user_id"]}, {"_id": 0, "password_hash": 0}
    )
    if not user_doc:
        raise HTTPException(404, "Credential holder not found.")

    cred_map = {c["key"]: c for c in CREDENTIALS}
    cred = cred_map.get(cred_doc["credential_key"])
    if not cred:
        raise HTTPException(404, "Credential type not recognized.")

    now = datetime.now(timezone.utc)
    expired = False
    if cred_doc.get("expires_at"):
        try:
            exp_dt = datetime.fromisoformat(cred_doc["expires_at"])
            if exp_dt.tzinfo is None:
                exp_dt = exp_dt.replace(tzinfo=timezone.utc)
            expired = exp_dt < now
        except Exception:
            pass

    return {
        "valid": not expired,
        "status": "expired" if expired else "active",
        "holder": user_doc["full_name"],
        "credential": cred["name"],
        "description": cred.get("description", ""),
        "institution": "W.A.I. Workforce Apprentice Institute",
        "earned_at": cred_doc.get("earned_at"),
        "expires_at": cred_doc.get("expires_at"),
        "verification_code": code,
        "verified_at": now.isoformat(),
    }


# ─── Admin Assistant — public service endpoint (any authenticated user) ──────

class AssistantChatReq(BaseModel):
    message: str
    history: List[dict] = []
    session_id: str = ""

SUPERVISOR_PUBLIC_SYSTEM = """You are The Supervisor — the public-facing AI guide for M.O.R.E. Help Center and WAI-Institute.

You answer questions directly. You do not re-route people to other personas or tell them to go ask someone else.
If someone asks you something, you answer it — fully, confidently, and helpfully.

WHO YOU SERVE:
- Visitors exploring M.O.R.E. Help Center and WAI-Institute
- Community members seeking resources, support, or information
- Students and prospective students
- Anyone who needs help navigating the platform

WHAT YOU DO:
- Answer questions about the platform, services, and community directly
- Help people find resources, programs, and support within M.O.R.E.
- Explain WAI-Institute courses, credentials, and learning paths
- Guide visitors through registration and getting started
- Provide grounded, practical answers — not vague redirects

YOUR TONE:
- Warm, direct, and human
- Never say "you should ask [another persona]" — you are the one answering
- Never hedge when you can answer — just answer
- Short clarifying question only if you genuinely cannot help without more info
- Act like someone who works the front desk and actually knows the place

If you don't know a specific fact, say what you do know and offer the closest help you can.
Never leave someone with nothing.
"""

ASSISTANT_SYSTEM = """You are the WAI Admin Assistant — a professional, highly capable AI assistant
built to handle real business and administrative work for operators and clients of M.O.R.E. Help Center.

YOUR CAPABILITIES (these are real — use them confidently):
- Draft and send professional emails on behalf of the user
- Schedule and organize tasks, follow-ups, and action items
- Write business letters, proposals, reports, and correspondence
- Research topics and summarize findings
- Answer questions about the WAI-Institute platform and services
- Help manage customer communication and client relationships
- Create templates, checklists, SOPs, and workflow documents
- Advise on business strategy, community outreach, and service marketing

YOUR TONE:
- Professional, direct, and warm
- Never hedge or disclaim capability
- When asked to send an email, draft it immediately and confirm you sent it
- When asked to write something, write it — fully, not partially
- One short clarifying question only if genuinely needed; otherwise act

PLATFORM CONTEXT:
You serve operators of M.O.R.E. Help Center and WAI-Institute — a workforce education and community
empowerment platform. Users may be community organizers, small business owners, educators, or
healthcare workers who need reliable administrative support.

YOUR LIMITS:
- You cannot access external databases or the internet
- Legal advice: provide information, not legal counsel
- Medical advice: refer to a licensed provider

Always sign off with: "— Admin Assistant, M.O.R.E. Help Center"
"""


@router.get("/admin/payments")
async def admin_payment_list(user=Depends(_require_rank("admin"))):
    cursor = db.payments.find({}, {"_id": 0}).sort("created_at", -1).limit(500)
    records = await cursor.to_list(500)
    total_cents = sum(r.get("amount_cents", 0) for r in records if r.get("status") == "paid")
    return {"payments": records, "total_revenue_cents": total_cents, "count": len(records)}


# ─── DISCOUNT MANAGEMENT ──────────────────────────────────────────────────────

@router.get("/admin/discounts")
async def get_active_discount(user: User = Depends(_require_rank("executive_admin"))):
    """Get the currently active discount (Director-only).

    Returns:
        Current discount with percentage, expiration, and days remaining,
        or null if no active discount.
    """
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")

    discount = await _discount_manager.get_active_discount()
    if discount:
        return discount.dict()
    return None


@router.post("/admin/discounts")
async def set_discount(
    body: dict,
    user: User = Depends(_require_rank("executive_admin"))
):
    """Create or update discount (Director-only).

    Request body:
        {
            "percentage": 50,     # 0-100
            "notes": "Optional reason"
        }

    Returns:
        Updated discount with id, creation time, and expiration.

    Notes:
        - Creating a new discount deactivates any existing discount
        - To deactivate, set "active": false
        - Expiration is always 90 days from creation (not reset on update)
    """
    if not _discount_manager:
        raise HTTPException(500, "Discount system not initialized")

    try:
        percentage = body.get("percentage")
        active = body.get("active", True)
        notes = body.get("notes", "")

        if percentage is None:
            raise ValueError("percentage is required")

        if not isinstance(percentage, int) or not (0 <= percentage <= 100):
            raise ValueError("percentage must be an integer between 0 and 100")

        if not active:
            # Deactivate the current discount
            discount = await _discount_manager.deactivate_discount()
            if discount:
                await audit(user.id, "discount.deactivated", meta={"discount_id": discount.id})
                return discount.dict()
            return None

        # Check if discount exists
        existing = await _discount_manager.get_active_discount()
        if existing:
            # Update existing discount's percentage
            discount = await _discount_manager.update_discount_percentage(percentage, notes)
            await audit(
                user.id,
                "discount.updated",
                meta={
                    "discount_id": discount.id,
                    "new_percentage": percentage,
                    "notes": notes
                }
            )
        else:
            # Create new discount
            discount = await _discount_manager.create_discount(percentage, user.id, notes)
            await audit(
                user.id,
                "discount.created",
                meta={
                    "discount_id": discount.id,
                    "percentage": percentage,
                    "expires_at": discount.expires_at.isoformat(),
                    "notes": notes
                }
            )

        return discount.dict()

    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        logger.exception("Error setting discount: %s", e)
        raise HTTPException(500, f"Error setting discount: {str(e)}")


@router.get("/pricing")
async def get_pricing():
    """Get subscription pricing with active discount applied.

    This is a PUBLIC endpoint (no auth required).

    Returns:
        {
            "tiers": {
                "basic": {
                    "monthly": 9.99,
                    "monthly_discounted": 5.00  (if discount active)
                },
                ...
            },
            "active_discount": {
                "percentage": 50,
                "expires_at": "2026-08-20T...",
                "message": "Save 50% for the first 90 days!"
            }  // or null if no discount
        }
    """
    if not _discount_manager:
        raise HTTPException(500, "Pricing system not initialized")

    from billing.models import TIER_PRICING

    discount = await _discount_manager.get_active_discount()
    pricing_response = _discount_manager.get_pricing_with_discount(TIER_PRICING, discount)

    return pricing_response

# ─── END PAYMENTS ───
# ═══════════════════════════════════════════════════════════════════════════════
# THE AMBASSADOR 4.0 — Campaign Coordination endpoint
# ═══════════════════════════════════════════════════════════════════════════════
