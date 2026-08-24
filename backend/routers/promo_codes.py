"""
Promo codes — grant a membership tier at signup.

A promo code is a row in the `promo_codes` collection:
    {
        code: "LEGACY704",          # normalized UPPERCASE, unique
        granted_tier: "member",     # free/member/plus/pro/patron
        label: "Legacy Student",    # short display name
        description: "...",         # why it exists
        max_uses: null,             # null = unlimited
        uses_count: 0,              # redeemed count (atomic $inc)
        expires_at: null,           # ISO datetime, null = never
        active: true,               # false = disabled
        created_by: "system",       # user id or "system"
        note: "...",                # admin note
        created_at: "...",
    }

Codes are redeemed ONLY at registration (POST /api/auth/register). They are
never shown in the frontend — the signup page just has an optional text field.
The platform-issued default code (Legacy704) is seeded at startup, idempotently.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["promo"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = audit = None


def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


# ── Tier ladder (mirror of payments.py / tiers.js) ───────────────────────────
TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "executive": 5}
TIER_LABEL = {"free": "Free", "member": "Member", "plus": "Plus", "pro": "Pro", "patron": "Patron", "executive": "Executive"}


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: str = "student"
    feature_tier: str = "free"


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    return await current_user(authorization)


def _require_admin():
    async def dep(user: User = Depends(_dep_current_user)) -> User:
        if user.role not in ("admin", "executive_admin"):
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user
    return dep


def normalize_code(code: str) -> str:
    return (code or "").strip().upper()


# ── Validation / redemption helpers (used by the auth register flow) ─────────
def _not_expired(doc: dict, now: datetime) -> bool:
    exp = doc.get("expires_at")
    if not exp:
        return True
    try:
        exp_dt = datetime.fromisoformat(exp)
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=timezone.utc)
        return exp_dt > now
    except Exception:
        return True  # malformed expiry treated as "no expiry set"


async def describe_promo(code: str) -> dict:
    """Validate WITHOUT redeeming. Returns {valid, ...} for the signup UI."""
    doc = await db.promo_codes.find_one({"code": normalize_code(code)}, {"_id": 0})
    if not doc:
        return {"valid": False, "message": "That promo code doesn't exist. Check the spelling and try again."}
    now = datetime.now(timezone.utc)
    if not doc.get("active"):
        return {"valid": False, "message": "That promo code has been deactivated."}
    if not _not_expired(doc, now):
        return {"valid": False, "message": "That promo code has expired."}
    max_uses = doc.get("max_uses")
    if max_uses is not None and doc.get("uses_count", 0) >= max_uses:
        return {"valid": False, "message": "That promo code has already been fully redeemed."}
    tier = doc.get("granted_tier", "free")
    return {
        "valid": True,
        "tier": tier,
        "tier_label": TIER_LABEL.get(tier, tier),
        "label": doc.get("label"),
        "message": f"Promo code applies: {TIER_LABEL.get(tier, tier)} account.",
    }


async def reserve_promo(code: str) -> Optional[dict]:
    """Atomically reserve one use of a valid code. Returns the code doc with
    uses_count already incremented, or None if invalid/exhausted. The caller
    must decrement (`release_promo`) if the account is then not created."""
    normalized = normalize_code(code)
    now = datetime.now(timezone.utc)
    doc = await db.promo_codes.find_one_and_update(
        {
            "code": normalized,
            "active": True,
            "$expr": {
                "$or": [
                    {"$eq": [{"$ifNull": ["$max_uses", None]}, None]},
                    {"$lt": ["$uses_count", "$max_uses"]},
                ]
            },
        },
        {"$inc": {"uses_count": 1}},
        return_document=True,
    )
    if not doc or not _not_expired(doc, now):
        if doc:
            await release_promo(normalized)
        return None
    return doc


async def release_promo(code: str):
    """Undo a reserved use (registration rolled back)."""
    try:
        await db.promo_codes.update_one({"code": normalize_code(code)}, {"$inc": {"uses_count": -1}})
    except Exception:
        logger.warning("promo: failed to release reserved use for %s", code)


def grant_fields_for(doc: dict) -> dict:
    """Build the user-doc tier fields a redeemed promo code grants."""
    now = datetime.now(timezone.utc)
    tier = doc.get("granted_tier", "free")
    duration_days = doc.get("duration_days")
    fields = {
        "feature_tier": tier,
        "feature_tier_source": "promo",
        "feature_tier_product": f"promo:{normalize_code(doc.get('code', ''))}",
        "feature_tier_updated_at": now.isoformat(),
        "promo_code_redeemed": normalize_code(doc.get("code", "")),
        "promo_redeemed_at": now.isoformat(),
    }
    if duration_days:
        fields["feature_tier_expires_at"] = (now.replace(microsecond=0) + timedelta(days=duration_days)).isoformat()
        fields["feature_tier_revert_to"] = "free"
    return fields


# ═════════════════════════════════════════════════════════════════════════════
# Default platform code — seeded idempotently at startup. The literal value is
# intentionally backend-only: it is never rendered or suggested in the frontend.
# ═════════════════════════════════════════════════════════════════════════════
DEFAULT_PROMO_SEEDS = [
    {
        "code": "LEGACY704",
        "granted_tier": "member",
        "label": "Legacy Student",
        "description": "Legacy code for NAM Oshun's former students — grants a Member account.",
        "max_uses": None,
        "expires_at": None,
        "active": True,
        "duration_days": None,  # permanent
        "created_by": "system",
        "note": "Legacy704 — adults who trained with NAM Oshun as youth. Testers of the member tier.",
    },
]


async def seed_default_promos():
    """Idempotent startup seed — inserts platform codes only if missing."""
    if db is None:
        return
    for seed in DEFAULT_PROMO_SEEDS:
        code = normalize_code(seed["code"])
        exists = await db.promo_codes.find_one({"code": code}, {"_id": 0})
        if exists:
            continue
        doc = {**seed, "code": code, "uses_count": 0, "created_at": datetime.now(timezone.utc).isoformat()}
        try:
            await db.promo_codes.insert_one(doc)
            logger.info("STARTUP: seeded promo code %s (grants %s).", code, seed["granted_tier"])
        except Exception:
            logger.warning("STARTUP: promo code %s already exists (race) — skipping.", code)


# ═════════════════════════════════════════════════════════════════════════════
# Endpoints
# ═════════════════════════════════════════════════════════════════════════════
class PromoCheckReq(BaseModel):
    code: str


@router.post("/promo/validate")
async def validate_promo(body: PromoCheckReq):
    """Public — used by the signup form to preview what a code grants."""
    return await describe_promo(body.code)


# ── Admin CRUD ───────────────────────────────────────────────────────────────
class PromoCreateReq(BaseModel):
    code: str
    granted_tier: str = "member"
    label: Optional[str] = None
    description: Optional[str] = None
    max_uses: Optional[int] = None
    duration_days: Optional[int] = None  # null = permanent
    expires_at: Optional[str] = None     # ISO datetime; overrides duration if set
    note: Optional[str] = None


class PromoUpdateReq(BaseModel):
    active: Optional[bool] = None
    max_uses: Optional[int] = None
    duration_days: Optional[int] = None
    expires_at: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    note: Optional[str] = None


@router.get("/admin/promo-codes")
async def list_promo_codes(user: User = Depends(_require_admin())):
    docs = await db.promo_codes.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return docs


@router.post("/admin/promo-codes")
async def create_promo_code(body: PromoCreateReq, user: User = Depends(_require_admin())):
    code = normalize_code(body.code)
    if not code or len(code) < 3:
        raise HTTPException(400, "Code must be at least 3 characters.")
    if body.granted_tier not in TIER_RANK:
        raise HTTPException(400, f"granted_tier must be one of: {', '.join(TIER_RANK)}.")
    if body.max_uses is not None and body.max_uses < 1:
        raise HTTPException(400, "max_uses must be at least 1 (or null for unlimited).")
    if body.duration_days is not None and body.duration_days < 1:
        raise HTTPException(400, "duration_days must be at least 1 (or null for permanent).")
    exists = await db.promo_codes.find_one({"code": code}, {"_id": 0})
    if exists:
        raise HTTPException(409, f"Promo code {code} already exists.")
    doc = {
        "code": code,
        "granted_tier": body.granted_tier,
        "label": body.label or code,
        "description": body.description or "",
        "max_uses": body.max_uses,
        "duration_days": body.duration_days,
        "expires_at": body.expires_at,
        "active": True,
        "uses_count": 0,
        "created_by": user.id,
        "note": body.note or "",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.promo_codes.insert_one(doc)
    await audit(user.id, "promo.created", target=code, meta={"tier": body.granted_tier})
    doc.pop("_id", None)
    return doc


@router.patch("/admin/promo-codes/{code}")
async def update_promo_code(code: str, body: PromoUpdateReq, user: User = Depends(_require_admin())):
    normalized = normalize_code(code)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "Nothing to update.")
    if "duration_days" in updates and updates["duration_days"] is not None and updates["duration_days"] < 1:
        raise HTTPException(400, "duration_days must be at least 1 (or null for permanent).")
    result = await db.promo_codes.update_one({"code": normalized}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(404, "Promo code not found.")
    await audit(user.id, "promo.updated", target=normalized, meta=updates)
    return await db.promo_codes.find_one({"code": normalized}, {"_id": 0})


@router.delete("/admin/promo-codes/{code}")
async def delete_promo_code(code: str, user: User = Depends(_require_admin())):
    normalized = normalize_code(code)
    result = await db.promo_codes.delete_one({"code": normalized})
    if result.deleted_count == 0:
        raise HTTPException(404, "Promo code not found.")
    await audit(user.id, "promo.deleted", target=normalized)
    return {"ok": True}
