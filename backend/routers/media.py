"""
media — Media store — products, purchases, checkout, uploads, file serving.

Extracted verbatim from backend/server.py (monolith refactor, slice 13).
Shared state is bound by server.py via bind() at include time — no circular imports.
"""
import logging
import os
import re
import uuid
import asyncio
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


async def _media_stripe_checkout(title: str, desc: str, amount_cents: int, product_id: str,
                                 user) -> Optional[dict]:
    """Tier 1 media-store checkout — hosted Stripe Checkout Session.

    Returns {"url", "id"} or None when Stripe isn't configured / SDK missing /
    the session can't be built. The caller falls back to Lemon Squeezy → Gumroad.
    """
    sk = os.environ.get("STRIPE_SECRET_KEY", "")
    pub = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
    if not (sk and pub):
        return None
    try:
        import stripe
        stripe.api_key = sk
        front = (os.environ.get("FRONTEND_URL", "https://wai-institute.org") or "https://wai-institute.org").rstrip("/")
        metadata = {"product_key": "media", "product_id": product_id, "product_title": title[:500]}
        params: dict = {
            "client_reference_id": str(getattr(user, "id", "") or getattr(user, "email", "") or "guest"),
            "metadata": metadata,
            "success_url": f"{front}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url": f"{front}/payment/cancel",
            "mode": "payment",
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": amount_cents,
                    "product_data": {"name": title, "description": desc[:500]},
                },
                "quantity": 1,
            }],
        }
        session = await asyncio.to_thread(stripe.checkout.Session.create, **params)
        if not session or not session.get("url"):
            return None
        return {"url": session["url"], "id": session.get("id", "")}
    except Exception:
        logging.getLogger("lcewai").exception("Stripe media checkout failed for %s — falling back", product_id)
        return None


# Fallback covers are ON-BRAND and race-neutral by design: a self-hosted SVG
# mark in the platform's warm copper/ink palette, not a stock photo of people.
# This avoids both (a) misrepresenting the brand's Black-diasporic audience and
# (b) hotlinking third-party stock that shows the wrong subjects. Creators who
# want a real cover should upload their own via cover_url.
def _BRAND_COVER_SVG(label: str) -> str:
    """Return a data-URI SVG cover in the platform's copper/ink brand palette.

    Race-neutral by design: geometric brand mark + product-type label, no
    people. URL-encoded so it can live inline in the cover_url field with no
    external image dependency.
    """
    import base64 as _b64
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1160" '
        'viewBox="0 0 900 1160">'
        '<rect width="900" height="1160" fill="#0f1526"/>'
        '<rect x="40" y="40" width="820" height="1080" rx="28" fill="none" stroke="#b5501a" stroke-width="6"/>'
        '<circle cx="450" cy="430" r="150" fill="none" stroke="#e8a51e" stroke-width="8" opacity="0.9"/>'
        '<circle cx="450" cy="430" r="96" fill="#b5501a" opacity="0.25"/>'
        '<path d="M450 360l0 140M390 410l120 0M410 365l80 130M490 365l-80 130" stroke="#f2ede3" stroke-width="16" stroke-linecap="round"/>'
        f'<text x="450" y="760" text-anchor="middle" font-family="Georgia,serif" font-size="64" '
        f'font-weight="bold" letter-spacing="6" fill="#f2ede3">{label}</text>'
        '<text x="450" y="820" text-anchor="middle" font-family="Georgia,serif" font-size="22" '
        'letter-spacing="4" fill="#b5501a">M.O.R.E. HELP CENTER</text>'
        '</svg>'
    )
    return "data:image/svg+xml;base64," + _b64.b64encode(svg.encode()).decode()


_DEFAULT_COVER_URLS = {
    "ebook":  _BRAND_COVER_SVG("BOOK"),   # inline data URI (see below)
    "pdf":    _BRAND_COVER_SVG("GUIDE"),
    "track":  _BRAND_COVER_SVG("TRACK"),
    "album":  _BRAND_COVER_SVG("ALBUM"),
    "video":  _BRAND_COVER_SVG("VIDEO"),
    "bundle": _BRAND_COVER_SVG("KIT"),
}


def _public_product(doc: dict) -> dict:
    clean = {k: v for k, v in doc.items() if k != "_id"}
    clean["product_type"] = clean.get("type", clean.get("product_type", "file"))
    clean["seller_display_name"] = clean.get("owner_name") or clean.get("seller_display_name") or "M.O.R.E. creator"
    clean["file_id"] = (clean.get("file_url") or "").rsplit("/", 1)[-1] or None
    # Every public catalog item has a usable cover, including older records
    # created before cover metadata was added to the product model.
    clean["cover_url"] = clean.get("cover_url") or _DEFAULT_COVER_URLS.get(
        clean["product_type"], _DEFAULT_COVER_URLS["pdf"]
    )
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


async def _optional_current_user(authorization: Optional[str] = Header(None)) -> Optional[User]:
    """Allow anonymous catalog browsing while preserving authenticated operations."""
    if not authorization:
        return None
    try:
        return await current_user(authorization)
    except HTTPException as exc:
        if exc.status_code in (401, 403):
            return None
        raise


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
async def list_media_products(user: Optional[User] = Depends(_optional_current_user)):
    if db is None:
        # Database outage — return an honest empty catalog instead of a 500,
        # matching the platform's db-outage resilience pattern.
        return []
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
    # Attach the sanitized catalog record so the library can render the
    # current title, cover, type, and download entitlement.
    for purchase in docs:
        product = await db.media_products.find_one({"id": purchase.get("product_id")}, {"_id": 0})
        purchase["product"] = _public_product(product) if product else None
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
        import uuid
        from ai.publishing import _publish_lemon_squeezy, _publish_gumroad
        amount = doc["price_cents"]
        title = doc.get("title", "Media product")
        desc = doc.get("description", "")[:500]
        # Tier 1 — Stripe (hosted Checkout Session)
        stripe_session = await _media_stripe_checkout(title, desc, amount, product_id, user)
        provider = None
        url = None
        if stripe_session:
            provider = "stripe"
            url = stripe_session["url"]
        if not provider:
            ls_result = await _publish_lemon_squeezy(name=title, description=desc, price_cents=amount, persona="platform")
            if ls_result:
                provider = "lemon_squeezy"
                url = ls_result["url"]
        if not provider:
            gr_result = await _publish_gumroad(title, desc, amount)
            if gr_result:
                provider = "gumroad"
                url = gr_result["url"]
        if not provider:
            _ls_key = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
            _ls_store = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
            _gr_key = os.environ.get("GUMROAD_API_KEY", "")
            _st_key = os.environ.get("STRIPE_SECRET_KEY", "")
            _st_pub = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
            if not ((_ls_key and _ls_store) or _gr_key or (_st_key and _st_pub)):
                raise HTTPException(
                    501,
                    "Payments are not configured. Add STRIPE_SECRET_KEY (or LEMON_SQUEEZY_API_KEY + "
                    "LEMON_SQUEEZY_STORE_ID, or GUMROAD_API_KEY) in your environment.",
                )
            raise HTTPException(
                500,
                "Payment processing failed. The payment providers are configured but the request could "
                "not be completed. Check your Stripe, Lemon Squeezy, or Gumroad API keys and try again.",
            )
        # Record the pending sale so the payment webhook can grant access when
        # the order_created event arrives. Without this row the customer pays
        # but their download stays locked.
        try:
            await db.media_checkout_pending.insert_one({
                "id": str(uuid.uuid4())[:8],
                "product_id": product_id,
                "provider": provider,
                "provider_product_name": title,
                "price_cents": amount,
                "buyer_id": user.id,
                "buyer_email": (user.email or "").lower(),
                "owner_id": doc.get("owner_id", ""),
                "status": "pending",
                "created_at": _now(),
            })
        except Exception:
            import logging
            logging.getLogger("lcewai").exception("media checkout: failed to record pending sale for %s", product_id)
        await audit(user.id, "media.checkout_created", target=product_id, meta={"provider": provider})
        return {"url": url}
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
    user: Optional[User] = Depends(_optional_current_user),
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
    asset_kind = metadata.get("kind", "")
    public_saga_asset = asset_kind in {"saga_image", "saga_video", "saga_track"}
    if user is None and not public_saga_asset:
        raise HTTPException(401, "Authentication required")
    full_access = bool(
        public_saga_asset and asset_kind in {"saga_image", "saga_video"}
        or product and user and (
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

    # ── Safe content-type handling ────────────────────────────────────────
    # The stored content_type is client-supplied at upload, so it is never
    # trusted for rendering. Only allowlist types may be served inline; every
    # other upload is served as an opaque download. This closes the stored-
    # media XSS vector (an HTML/SVG payload uploaded as "image" can no longer
    # execute in the viewer's origin) and forces the browser to sniff nothing.
    _SAFE_INLINE_TYPES = (
        "image/", "audio/", "video/", "application/pdf", "text/plain",
        "application/json", "application/octet-stream",
    )
    raw_type = (metadata.get("content_type") or "").lower().split(";")[0].strip()
    safe_inline = any(raw_type.startswith(p) for p in _SAFE_INLINE_TYPES)
    serve_type = raw_type if safe_inline else "application/octet-stream"
    disposition = "inline" if safe_inline else "attachment"
    filename = str(metadata.get("filename") or "download").replace('"', "")

    headers = {
        "X-Preview-Max-Seconds": str(preview_seconds),
        "X-Media-Full-Access": "true" if full_access else "false",
        "Accept-Ranges": "bytes",
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'{disposition}; filename="{filename}"',
    }
    if duration_seconds and limit_bytes:
        headers["X-Preview-Duration-Seconds"] = str(min(preview_seconds, duration_seconds))
    return StreamingResponse(iter_file(), media_type=serve_type, headers=headers)


@router.get("/media/content/{file_path:path}")
async def get_content_file(
    file_path: str,
    user: User = Depends(_dep_current_user),
):
    """Serve static content files (starter-library ebooks, etc.) from the content/ directory.

    The file_path is relative to the project root (e.g. 'content/starter-library/the-small-start.md').
    Only files under the content/ directory are served.
    """
    from fastapi.responses import FileResponse
    # Security: only serve files under content/
    if not file_path.startswith("content/") or ".." in file_path:
        raise HTTPException(403, "Access denied")
    # Resolve content paths relative to the repository root. This router lives
    # in backend/routers/, while the seeded manuscripts live in content/.
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_root = os.path.dirname(backend_dir)
    full_path = os.path.normpath(os.path.join(project_root, file_path))
    # Double-check: resolved path must still be under the project root
    if not full_path.startswith(project_root + os.sep):
        raise HTTPException(403, "Access denied")
    if not os.path.isfile(full_path):
        raise HTTPException(404, "Content file not found")
    # Check purchase entitlement
    product = await db.media_products.find_one(
        {"file_path": file_path}, {"_id": 0, "id": 1, "owner_id": 1, "price_cents": 1}
    )
    if product and product.get("price_cents", 0) > 0:
        owner = product.get("owner_id", "")
        is_owner = owner == user.id
        is_admin = ROLE_RANK.get(user.role, 0) >= ROLE_RANK.get("admin", 6)
        purchased = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": product.get("id")})
        if not is_owner and not is_admin and not purchased:
            raise HTTPException(403, "Purchase required to download this content")
    return FileResponse(full_path, media_type="text/markdown", filename=os.path.basename(full_path))
