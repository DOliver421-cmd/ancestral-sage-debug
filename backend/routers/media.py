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

from fastapi import APIRouter, Depends, HTTPException, Header, Request, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _public_product(doc: dict) -> dict:
    clean = {k: v for k, v in doc.items() if k != "_id"}
    clean["product_type"] = clean.get("type", clean.get("product_type", "file"))
    clean["file_id"] = (clean.get("file_url") or "").rsplit("/", 1)[-1] or None
    return clean


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
    return [_public_product(d) for d in docs]

@router.get("/media/products/mine")
async def my_media_products(user: User = Depends(_dep_current_user)):
    docs = await db.media_products.find({"owner_id": user.id}, {"_id": 0}).sort("created_at", -1).limit(100).to_list(100)
    return [_public_product(d) for d in docs]

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
        "type": body.get("type", body.get("product_type", "file")),
        "tags": body.get("tags", []),
        "file_url": body.get("file_url") or body.get("file_url", ""),
        # Uploaded audio is always preview-limited until a purchase, owner, or
        # executive entitlement is verified by the stream endpoint.
        "preview_seconds": 33 if body.get("type", body.get("product_type")) in {"audio", "track", "music"} else None,
        "cover_url": body.get("cover_url", ""),
        "published": body.get("published", False),
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.media_products.insert_one(doc)
    doc = _public_product(doc)
    await audit(user.id, "media_product_created", target=pid, meta={"title": doc["title"]})
    return doc

@router.patch("/media/products/{product_id}")
async def update_media_product(product_id: str, body: dict, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can update")
    allowed = {"title", "description", "price_cents", "type", "product_type", "tags", "file_url", "cover_url", "published"}
    updates = {k: v for k, v in body.items() if k in allowed}
    updates["updated_at"] = _now()
    await db.media_products.update_one({"id": product_id}, {"$set": updates})
    return _public_product({**{k: v for k, v in doc.items() if k != "_id"}, **updates})

@router.delete("/media/products/{product_id}")
async def delete_media_product(product_id: str, user: User = Depends(_dep_current_user)):
    doc = await db.media_products.find_one({"id": product_id})
    if not doc:
        raise HTTPException(404, "Product not found")
    if doc.get("owner_id") != user.id and ROLE_RANK.get(user.role, 0) < ROLE_RANK.get("admin", 3):
        raise HTTPException(403, "Only owner can delete")
    await db.media_products.delete_one({"id": product_id})
    await audit(user.id, "media_product_deleted", target=product_id)
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
            await audit(user.id, "media.checkout_created", target=product_id, meta={"provider": "lemon_squeezy"})
            return {"url": ls_result["url"]}
        gr_result = await _publish_gumroad(title, desc, amount)
        if gr_result:
            await audit(user.id, "media.checkout_created", target=product_id, meta={"provider": "gumroad"})
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
async def upload_media_file(
    file: UploadFile = File(...),
    duration_seconds: Optional[float] = Form(None),
    user: User = Depends(_dep_current_user),
):
    """Upload a media asset and persist its preview entitlement metadata.

    Audio uploads must provide their measured duration. This lets the server
    cap preview bytes for a 33-second response and lets the player enforce the
    exact time boundary. Full playback is never granted by the upload itself.
    """
    max_mb = 50
    contents = await file.read()
    if len(contents) > max_mb * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {max_mb}MB)")
    is_audio = (file.content_type or "").lower().startswith("audio/")
    if is_audio and (duration_seconds is None or duration_seconds <= 0):
        raise HTTPException(400, "duration_seconds is required for uploaded audio")
    preview_seconds = 33 if is_audio else None
    preview_bytes = None
    if is_audio:
        preview_bytes = len(contents) if duration_seconds <= 33 else max(1, int(len(contents) * (33 / duration_seconds)))
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    bucket = AsyncIOMotorGridFSBucket(db)
    metadata = {
        "uploader": user.id,
        "content_type": file.content_type or "application/octet-stream",
        "duration_seconds": duration_seconds,
        "preview_seconds": preview_seconds,
        "preview_bytes": preview_bytes,
    }
    gfs_id = await bucket.upload_from_stream(file.filename, contents, metadata=metadata)
    file_url = f"/api/media/file/{gfs_id}"
    await audit(user.id, "media_file_uploaded", meta={"filename": file.filename, "size": len(contents), "preview_seconds": preview_seconds})
    return {
        "file_url": file_url,
        "filename": file.filename,
        "size": len(contents),
        "preview_seconds": preview_seconds,
        "duration_seconds": duration_seconds,
        "preview_bytes": preview_bytes,
    }

@router.get("/media/file/{file_id}")
async def get_media_file(
    file_id: str,
    preview: bool = Query(True),
    user: User = Depends(_dep_current_user),
):
    """Serve uploaded media with an entitlement-aware preview boundary.

    Uploaded audio is preview-only by default. Paid purchases, the owner, and
    executive staff receive the full stream. Preview requests are byte-limited
    using the duration supplied at upload; the browser also enforces the exact
    33-second playback stop for variable-bitrate formats.
    """
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        stream = await bucket.open_download_stream(oid)
    except Exception:
        raise HTTPException(404, "File not found")

    metadata = stream.metadata or {}
    product = await db.media_products.find_one(
        {"file_url": {"$regex": f"/media/file/{file_id}$"}},
        {"_id": 0, "id": 1, "owner_id": 1, "price_cents": 1, "type": 1, "preview_seconds": 1},
    )
    full_access = bool(
        product and (
            product.get("owner_id") == user.id
            or ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get("admin", 6)
            or await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product.get("id")})
        )
    )
    preview_seconds = int(product.get("preview_seconds") or metadata.get("preview_seconds") or 33) if product else int(metadata.get("preview_seconds") or 33)
    duration_seconds = float(metadata.get("duration_seconds") or 0)
    preview_bytes = int(metadata.get("preview_bytes") or 0)
    # The query flag is not an entitlement.  It only expresses the caller's
    # requested mode; an unentitled listener must remain preview-limited even
    # when it asks for `preview=false` directly.
    content_type = (metadata.get("content_type") or "").lower()
    if not full_access and content_type.startswith("audio/") and preview_bytes <= 0:
        # Legacy uploads without measured preview metadata cannot be safely
        # time-bounded, so fail closed instead of returning the full track.
        raise HTTPException(503, "Preview metadata is unavailable for this audio asset.")
    limit_bytes = None if full_access or not content_type.startswith("audio/") else preview_bytes

    async def iter_file():
        remaining = limit_bytes
        while True:
            size = 65536 if remaining is None else min(65536, remaining)
            if size <= 0:
                break
            chunk = await stream.read(size)
            if not chunk:
                break
            yield chunk
            if remaining is not None:
                remaining -= len(chunk)

    headers = {
        "X-Preview-Max-Seconds": str(preview_seconds),
        "X-Media-Full-Access": "true" if full_access else "false",
        "Accept-Ranges": "bytes",
    }
    if duration_seconds and limit_bytes:
        headers["X-Preview-Duration-Seconds"] = str(min(preview_seconds, duration_seconds))
    return StreamingResponse(iter_file(), media_type=metadata.get("content_type", "application/octet-stream"), headers=headers)
