"""
media — Media store — products, purchases, checkout, uploads, file serving.

Extracted verbatim from backend/server.py (monolith refactor, slice 13).
Shared state is bound by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Form
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['media'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None


def bind(_db, _current_user, _audit):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit
    
    db = _db
    current_user = _current_user
    audit = _audit


# Mirrors server.py's role hierarchy for runtime require_role checks.
from routers.roles import ROLE_RANK, Role


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


# ── MEDIA STORE (/media/*) ────────────────────────────────────────────────────

@router.get("/media/products")
async def list_media_products(user: User = Depends(_dep_current_user)):
    docs = await db.media_products.find({"published": True}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return docs

@router.get("/media/products/mine")
async def my_media_products(user: User = Depends(_dep_current_user)):
    docs = await db.media_products.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return docs

@router.post("/media/products")
async def create_media_product(body: dict, user: User = Depends(_dep_current_user)):
    import uuid
    pid = "mp_" + str(uuid.uuid4())[:8]
    doc = {
        "id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": (body.get("title") or "").strip(),
        "description": (body.get("description") or "").strip(),
        "price_cents": int(body.get("price_cents", 0)),
        "type": body.get("type", "file"),
        "tags": body.get("tags", []),
        "file_url": body.get("file_url", ""),
        "cover_url": body.get("cover_url", ""),
        "published": body.get("published", False),
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.media_products.insert_one(doc)
    doc.pop("_id", None)
    await audit(db, user.id, "media_product_created", {"id": pid, "title": doc["title"]})
    return doc

@router.patch("/media/products/{product_id}")
async def update_media_product(product_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "price_cents", "type", "tags", "file_url", "cover_url", "published"}
    updates = {k: v for k, v in body.items() if k in allowed}
    updates["updated_at"] = _now()
    await db.media_products.update_one({"id": product_id}, {"$set": updates})
    return {**{k: v for k, v in doc.items() if k != "_id"}, **updates}

@router.delete("/media/products/{product_id}")
async def delete_media_product(product_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can delete")
    await db.media_products.delete_one({"id": product_id})
    await audit(db, user.id, "media_product_deleted", {"id": product_id})
    return {"deleted": True}

@router.get("/media/purchases")
async def my_media_purchases(user: User = Depends(_dep_current_user)):
    docs = await db.media_purchases.find({"buyer_id": user.id}, {"_id": 0}).sort("purchased_at", -1).limit(100).to_list(100)
    return docs

@router.post("/media/products/{product_id}/checkout")
async def checkout_media_product(product_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    if not doc.get("published"):
        raise HTTPException(400, "Product not available")
    existing = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product_id})
    if existing:
        return {"already_purchased": True, "file_url": doc.get("file_url", "")}
    if doc.get("price_cents", 0) > 0:
        from ai.publishing import _publish_lemon_squeezy, _publish_gumroad
        amount = doc["price_cents"]
        title = doc.get("title", "Media product")
        desc = doc.get("description", "")[:500]
        ls_result = await _publish_lemon_squeezy(name=title, description=desc, price_cents=amount, persona="platform")
        if ls_result:
            await audit(db, user.id, "media.checkout_created", {"product_id": product_id, "provider": "lemon_squeezy"})
            return {"url": ls_result["url"]}
        gr_result = await _publish_gumroad(title, desc, amount)
        if gr_result:
            await audit(db, user.id, "media.checkout_created", {"product_id": product_id, "provider": "gumroad"})
            return {"url": gr_result["url"]}
        raise HTTPException(500, "Payment processing failed. Payment providers are configured but the request could not be completed.")
    import uuid
    purchase = {
        "id": str(uuid.uuid4())[:8],
        "buyer_id": user.id,
        "product_id": product_id,
        "title": doc.get("title", ""),
        "file_url": doc.get("file_url", ""),
        "purchased_at": _now(),
        "price_cents": 0,
    }
    await db.media_purchases.insert_one(purchase)
    purchase.pop("_id", None)
    return purchase

@router.get("/media/products/{product_id}/download")
async def download_media_product(product_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("price_cents", 0) > 0:
        existing = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product_id})
        if not existing and doc.get("owner_id") != user.id:
            raise HTTPException(403, "Purchase required")
    file_url = doc.get("file_url", "")
    if not file_url:
        raise HTTPException(404, "No file attached to this product")
    return {"file_url": file_url, "title": doc.get("title", "")}

@router.post("/media/upload")
async def upload_media_file(file: UploadFile = File(...), user: User = Depends(_dep_current_user)):
    max_mb = 50
    contents = await file.read()
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {max_mb}MB)")
    import gridfs
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    bucket = AsyncIOMotorGridFSBucket(db)
    gfs_id = await bucket.upload_from_stream(file.filename, contents, metadata={"uploader": user.id, "content_type": file.content_type})
    file_url = f"/api/media/file/{gfs_id}"
    await audit(db, user.id, "media_file_uploaded", {"filename": file.filename, "size": len(contents)})
    return {"file_url": file_url, "filename": file.filename, "size": len(contents)}

@router.get("/media/file/{file_id}")
async def get_media_file(file_id: str, user: User = Depends(_dep_current_user)):
    """Serve a GridFS file with fail-closed access control.

    This is the actual bytes-serving endpoint (uploads store file_url as
    /api/media/file/<gfs_id>). It must not be bypassable by calling the file
    endpoint directly:
      - Unauthenticated requests are rejected (401) by _dep_current_user.
      - If the file is referenced by a priced, published media_product, only
        the product owner, a purchaser holding a media_purchases row, or an
        admin/exec may stream it. No such reference => 403.
      - Files referenced only by free (price_cents == 0) products remain
        readable by any authenticated user.
    Admins/executives bypass the product gate for moderation/administration.
    """
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    from fastapi.responses import StreamingResponse

    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")

    # ── Fail-closed entitlement check on the serving path ────────────────────
    is_admin = (ROLE_RANK.get(user.role, 0) or 0) >= (ROLE_RANK.get("admin", 3) or 3)
    protected = False
    entitled = False
    try:
        products = await db.media_products.find(
            {"file_url": {"$regex": re.escape(str(oid)) + r"$"}},
            {"_id": 0, "id": 1, "owner_id": 1, "price_cents": 1, "published": 1},
        ).to_list(20)
    except Exception:
        products = []
    for p in products:
        if not p.get("published"):
            continue
        if (p.get("price_cents") or 0) > 0:
            protected = True
            if p.get("owner_id") == user.id:
                entitled = True
            else:
                purchaser = await db.media_purchases.find_one(
                    {"buyer_id": user.id, "product_id": p.get("id")},
                    {"_id": 0, "id": 1},
                )
                if purchaser:
                    entitled = True
        elif not protected and not entitled:
            # A free product referencing this file grants authenticated access.
            pass

    if protected and not entitled and not is_admin:
        raise HTTPException(403, "Purchase required to access this file.")

    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        stream = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")
    async def iter_file():
        while True:
            chunk = await stream.read(65536)
            if not chunk:
                break
            yield chunk
    return StreamingResponse(iter_file(), media_type=stream.metadata.get("content_type", "application/octet-stream"))
