"""app/routes/media_store.py — Upload-and-sell system for NAM Oshun.

GridFS-backed file storage + free-tier checkout (Lemon Squeezy → Gumroad)
for albums, tracks, PDFs, etc. Stripe was fully removed from this platform.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from pydantic import BaseModel

from app.database import db
from app.models.user import User
from app.security.auth import current_user

logger = logging.getLogger("lcewai")
router = APIRouter()

LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")
LEMON_SQUEEZY_STORE_ID = os.environ.get("LEMON_SQUEEZY_STORE_ID", "")
GUMROAD_API_KEY = os.environ.get("GUMROAD_API_KEY", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://morehelp.center")


def _gridfs_bucket():
    return AsyncIOMotorGridFSBucket(db, bucket_name="media")


async def _send_purchase_receipt(to_email: str, product_title: str, download_url: str):
    """Send a purchase confirmation email with download link via Gmail SMTP."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    gmail_user = os.environ.get("GMAIL_USER", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    if not gmail_user or not gmail_pass:
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Your purchase is ready — {product_title}"
    msg["From"] = f"NAM Oshun · M.O.R.E. <{gmail_user}>"
    msg["To"] = to_email
    html = f"""
    <div style="font-family:Georgia,serif;max-width:520px;margin:0 auto;padding:32px 24px;color:#1a1a1a;">
      <div style="font-size:22px;font-weight:900;color:#b5651d;margin-bottom:8px;">Thank you.</div>
      <p style="font-size:16px;line-height:1.7;margin-bottom:24px;">
        Your purchase of <strong>{product_title}</strong> is confirmed.
        Click below to access your download.
      </p>
      <a href="{download_url}"
         style="display:inline-block;background:#1a1a1a;color:#fff;padding:14px 28px;
                border-radius:8px;font-weight:700;text-decoration:none;font-size:15px;">
        Go to My Library →
      </a>
      <p style="font-size:12px;color:#9ca3af;margin-top:32px;line-height:1.6;">
        NAM Oshun · M.O.R.E. Help Center<br>
        This email confirms your purchase. Reply if you need anything.
      </p>
    </div>
    """
    msg.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_pass)
        server.sendmail(gmail_user, to_email, msg.as_string())


def _now():
    return datetime.now(timezone.utc)


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post("/media/upload")
async def upload_file(
    file: UploadFile,
    title: str = Form(...),
    description: str = Form(""),
    file_type: str = Form("other"),  # track/album/pdf/video/other
    is_public: bool = Form(False),
    user: User = Depends(current_user),
):
    bucket = _gridfs_bucket()
    file_id = str(uuid.uuid4())

    # Stream upload to GridFS
    content = await file.read()
    gridfs_id = await bucket.upload_from_stream(
        file.filename or "upload",
        content,
        metadata={
            "content_type": file.content_type,
            "uploaded_by": str(user.id),
        },
    )

    doc = {
        "id": file_id,
        "user_id": str(user.id),
        "title": title,
        "description": description,
        "file_type": file_type,
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(content),
        "gridfs_id": str(gridfs_id),
        "is_public": is_public,
        "created_at": _now(),
    }
    await db.media_files.insert_one(doc)
    doc.pop("_id", None)
    logger.info("media_upload: user=%s file=%s size=%d", user.id, file_id, len(content))
    return doc


# ── List my files ─────────────────────────────────────────────────────────────

@router.get("/media/files")
async def list_my_files(user: User = Depends(current_user)):
    files = await db.media_files.find(
        {"user_id": str(user.id)}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=200)
    return files


# ── Download / stream ─────────────────────────────────────────────────────────

@router.get("/media/file/{file_id}")
async def download_file(file_id: str, user: User = Depends(current_user)):
    meta = await db.media_files.find_one({"id": file_id}, {"_id": 0})
    if not meta:
        raise HTTPException(404, "File not found")

    user_id_str = str(user.id)
    owner = meta["user_id"] == user_id_str

    if not meta.get("is_public") and not owner:
        # Check purchase record
        purchase = await db.media_purchases.find_one({
            "buyer_user_id": user_id_str,
            "file_id": file_id,
        })
        if not purchase:
            raise HTTPException(403, "Access denied — purchase required")

    bucket = _gridfs_bucket()
    try:
        grid_out = await bucket.open_download_stream(ObjectId(meta["gridfs_id"]))
    except Exception as exc:
        logger.error("GridFS download error: %s", exc)
        raise HTTPException(500, "File retrieval failed")

    async def iter_stream():
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    content_type = meta.get("content_type") or "application/octet-stream"
    filename = meta.get("original_filename") or "download"
    return StreamingResponse(
        iter_stream(),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Delete file ───────────────────────────────────────────────────────────────

@router.delete("/media/file/{file_id}")
async def delete_file(file_id: str, user: User = Depends(current_user)):
    meta = await db.media_files.find_one({"id": file_id})
    if not meta:
        raise HTTPException(404, "File not found")
    if meta["user_id"] != str(user.id):
        raise HTTPException(403, "Not your file")

    bucket = _gridfs_bucket()
    try:
        await bucket.delete(ObjectId(meta["gridfs_id"]))
    except Exception as exc:
        logger.warning("GridFS delete failed for %s: %s", file_id, exc)

    await db.media_files.delete_one({"id": file_id})
    return {"deleted": True}


# ── Products ──────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    title: str
    description: str = ""
    price_cents: int = 0
    file_id: Optional[str] = None
    cover_url: Optional[str] = None
    product_type: str = "track"  # track/album/bundle/pdf
    published: bool = False


@router.post("/media/products")
async def create_product(body: ProductCreate, user: User = Depends(current_user)):
    now = _now()
    doc = {
        "id": str(uuid.uuid4()),
        "seller_user_id": str(user.id),
        "title": body.title,
        "description": body.description,
        "price_cents": body.price_cents,
        "file_id": body.file_id,
        "cover_url": body.cover_url,
        "product_type": body.product_type,
        "published": body.published,
        "created_at": now,
        "updated_at": now,
        "sales_count": 0,
    }
    await db.media_products.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.get("/media/products")
async def list_products():
    """Public storefront — published products only."""
    products = await db.media_products.find(
        {"published": True}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=500)

    # Enrich with seller info
    seller_ids = list({p["seller_user_id"] for p in products})
    sellers = {}
    if seller_ids:
        cursor = db.users.find(
            {"$or": [{"id": sid} for sid in seller_ids]},
            {"id": 1, "display_name": 1, "avatar_url": 1, "_id": 0},
        )
        async for s in cursor:
            sellers[s["id"]] = s

    for p in products:
        seller = sellers.get(p["seller_user_id"], {})
        p["seller_display_name"] = seller.get("display_name", "Creator")
        p["seller_avatar"] = seller.get("avatar_url")

    return products


@router.get("/media/products/mine")
async def my_products(user: User = Depends(current_user)):
    products = await db.media_products.find(
        {"seller_user_id": str(user.id)}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=500)
    return products


@router.patch("/media/products/{product_id}")
async def update_product(
    product_id: str,
    body: dict,
    user: User = Depends(current_user),
):
    prod = await db.media_products.find_one({"id": product_id})
    if not prod:
        raise HTTPException(404, "Product not found")
    if prod["seller_user_id"] != str(user.id):
        raise HTTPException(403, "Not your product")

    allowed = {"title", "description", "price_cents", "file_id", "cover_url", "product_type", "published"}
    update = {k: v for k, v in body.items() if k in allowed}
    update["updated_at"] = _now()
    await db.media_products.update_one({"id": product_id}, {"$set": update})
    updated = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    return updated


@router.delete("/media/products/{product_id}")
async def delete_product(product_id: str, user: User = Depends(current_user)):
    prod = await db.media_products.find_one({"id": product_id})
    if not prod:
        raise HTTPException(404, "Product not found")
    if prod["seller_user_id"] != str(user.id):
        raise HTTPException(403, "Not your product")
    await db.media_products.delete_one({"id": product_id})
    return {"deleted": True}


# ── Checkout (Lemon Squeezy → Gumroad) ───────────────────────────────────────

@router.post("/media/products/{product_id}/checkout")
async def create_checkout(product_id: str, user: User = Depends(current_user)):
    prod = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not prod:
        raise HTTPException(404, "Product not found")
    if not prod.get("published"):
        raise HTTPException(400, "Product not published")
    if prod.get("price_cents", 0) <= 0:
        raise HTTPException(400, "Use free download for price=0 products")

    from ai.publishing import _publish_lemon_squeezy, _publish_gumroad

    # Tier 1 — Lemon Squeezy
    ls_result = await _publish_lemon_squeezy(
        name=prod["title"],
        description=prod.get("description") or "",
        price_cents=prod["price_cents"],
        persona="media",
        is_subscription=False,
    )
    if ls_result and ls_result.get("url"):
        await db.media_checkout_events.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "buyer_user_id": str(user.id),
            "buyer_email": user.email if hasattr(user, "email") else "",
            "provider": "lemon_squeezy",
            "created_at": _now(),
        })
        return {"checkout_url": ls_result["url"]}

    # Tier 2 — Gumroad (one-time digital purchases only)
    gr_result = await _publish_gumroad(prod["title"], prod.get("description") or "", prod["price_cents"])
    if gr_result and gr_result.get("url"):
        await db.media_checkout_events.insert_one({
            "id": str(uuid.uuid4()),
            "product_id": product_id,
            "buyer_user_id": str(user.id),
            "buyer_email": user.email if hasattr(user, "email") else "",
            "provider": "gumroad",
            "created_at": _now(),
        })
        return {"checkout_url": gr_result["url"]}

    raise HTTPException(
        501,
        "Payments are not configured yet. Add LEMON_SQUEEZY_API_KEY + LEMON_SQUEEZY_STORE_ID "
        "(free tier — payouts via PayPal or bank) or GUMROAD_API_KEY to enable checkout.",
    )


# ── Lemon Squeezy Webhook ─────────────────────────────────────────────────────

@router.post("/media/webhook")
async def media_webhook(request: Request):
    import json
    import hmac as _hmac
    import hashlib as _hashlib

    secret = os.environ.get("LEMON_SQUEEZY_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(404, "Payment webhook not configured")

    payload = await request.body()
    sig = request.headers.get("x-signature", "")
    if not sig or not _hmac.compare_digest(
        sig, _hmac.new(secret.encode(), payload, _hashlib.sha256).hexdigest()
    ):
        raise HTTPException(400, "Invalid webhook signature")

    try:
        event = json.loads(payload)
    except Exception:
        raise HTTPException(400, "Invalid JSON payload")

    event_name = (event.get("meta") or {}).get("event_name", "")
    if event_name == "order_created":
        data = (event.get("data") or {}).get("attributes") or {}
        first_item = data.get("first_order_item") or {}
        product_name = first_item.get("product_name", "")
        buyer_email = data.get("user_email", "")

        # Match the purchased product by title; grant download access to the
        # matching WAI account (buyer email).
        prod = await db.media_products.find_one({"title": product_name}, {"_id": 0})
        if prod:
            buyer = await db.users.find_one({"email": buyer_email}, {"id": 1}) if buyer_email else None
            now = _now()
            purchase_doc = {
                "id": str(uuid.uuid4()),
                "product_id": prod["id"],
                "buyer_user_id": buyer["id"] if buyer else None,
                "buyer_email": buyer_email,
                "file_id": prod.get("file_id"),
                "provider_order_id": str((event.get("data") or {}).get("id", "")),
                "amount_paid": int(float(data.get("total", 0) or 0) * 100),
                "created_at": now,
            }
            await db.media_purchases.insert_one(purchase_doc)
            await db.media_products.update_one(
                {"id": prod["id"]}, {"$inc": {"sales_count": 1}}
            )
            logger.info("media_purchase: product=%s buyer=%s", prod["id"], buyer_email)

            # Send purchase receipt email with download link
            try:
                if buyer_email and prod.get("file_id"):
                    download_url = f"{FRONTEND_URL}/store/library"
                    await _send_purchase_receipt(buyer_email, product_name, download_url)
            except Exception as _mail_err:
                logger.warning("Purchase receipt email failed (non-fatal): %s", _mail_err)

    return {"received": True}


# ── Download after purchase ───────────────────────────────────────────────────

@router.get("/media/products/{product_id}/download")
async def download_purchased(product_id: str, user: User = Depends(current_user)):
    prod = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not prod:
        raise HTTPException(404, "Product not found")

    user_id_str = str(user.id)
    is_owner = prod["seller_user_id"] == user_id_str

    if not is_owner:
        # Verify purchase
        if prod.get("price_cents", 0) > 0:
            purchase = await db.media_purchases.find_one({
                "product_id": product_id,
                "buyer_user_id": user_id_str,
            })
            if not purchase:
                raise HTTPException(403, "Purchase required to download")

    file_id = prod.get("file_id")
    if not file_id:
        raise HTTPException(400, "No file linked to this product")

    meta = await db.media_files.find_one({"id": file_id}, {"_id": 0})
    if not meta:
        raise HTTPException(404, "File not found")

    bucket = _gridfs_bucket()
    try:
        grid_out = await bucket.open_download_stream(ObjectId(meta["gridfs_id"]))
    except Exception as exc:
        logger.error("GridFS download error: %s", exc)
        raise HTTPException(500, "File retrieval failed")

    async def iter_stream():
        while True:
            chunk = await grid_out.readchunk()
            if not chunk:
                break
            yield chunk

    content_type = meta.get("content_type") or "application/octet-stream"
    filename = meta.get("original_filename") or "download"
    return StreamingResponse(
        iter_stream(),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── My purchases / library ────────────────────────────────────────────────────

@router.get("/media/purchases")
async def my_purchases(user: User = Depends(current_user)):
    purchases = await db.media_purchases.find(
        {"buyer_user_id": str(user.id)}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=500)

    # Enrich with product info
    product_ids = [p["product_id"] for p in purchases]
    products = {}
    if product_ids:
        async for prod in db.media_products.find(
            {"id": {"$in": product_ids}}, {"_id": 0}
        ):
            products[prod["id"]] = prod

    for p in purchases:
        p["product"] = products.get(p["product_id"])

    return purchases
