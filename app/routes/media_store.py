"""app/routes/media_store.py — Upload-and-sell system for NAM Oshun.

GridFS-backed file storage + Stripe checkout for albums, tracks, PDFs, etc.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import stripe as _stripe
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

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://morehelp.center")

if STRIPE_SECRET_KEY:
    _stripe.api_key = STRIPE_SECRET_KEY


def _gridfs_bucket():
    return AsyncIOMotorGridFSBucket(db, bucket_name="media")


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


# ── Stripe Checkout ───────────────────────────────────────────────────────────

@router.post("/media/products/{product_id}/checkout")
async def create_checkout(product_id: str, user: User = Depends(current_user)):
    if not STRIPE_SECRET_KEY:
        raise HTTPException(503, "Stripe not configured")

    prod = await db.media_products.find_one({"id": product_id}, {"_id": 0})
    if not prod:
        raise HTTPException(404, "Product not found")
    if not prod.get("published"):
        raise HTTPException(400, "Product not published")
    if prod.get("price_cents", 0) <= 0:
        raise HTTPException(400, "Use free download for price=0 products")

    session = _stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": prod["price_cents"],
                "product_data": {
                    "name": prod["title"],
                    "description": prod.get("description") or "",
                },
            },
            "quantity": 1,
        }],
        success_url=f"{FRONTEND_URL}/store?success=1&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/store",
        metadata={
            "product_id": product_id,
            "buyer_user_id": str(user.id),
        },
    )
    return {"checkout_url": session.url}


# ── Stripe Webhook ────────────────────────────────────────────────────────────

@router.post("/media/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    if STRIPE_WEBHOOK_SECRET:
        try:
            event = _stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
        except _stripe.error.SignatureVerificationError:
            raise HTTPException(400, "Invalid webhook signature")
    else:
        import json
        event = json.loads(payload)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        product_id = meta.get("product_id")
        buyer_user_id = meta.get("buyer_user_id")

        if product_id and buyer_user_id:
            # Look up product to get file_id
            prod = await db.media_products.find_one({"id": product_id}, {"_id": 0})
            now = _now()
            purchase_doc = {
                "id": str(uuid.uuid4()),
                "product_id": product_id,
                "buyer_user_id": buyer_user_id,
                "file_id": prod.get("file_id") if prod else None,
                "stripe_session_id": session.get("id"),
                "amount_paid": session.get("amount_total", 0),
                "created_at": now,
            }
            await db.media_purchases.insert_one(purchase_doc)
            if prod:
                await db.media_products.update_one(
                    {"id": product_id}, {"$inc": {"sales_count": 1}}
                )
            logger.info("media_purchase: product=%s buyer=%s", product_id, buyer_user_id)

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
