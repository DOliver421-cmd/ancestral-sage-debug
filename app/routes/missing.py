"""app/routes/missing.py — Missing persons tip submission + public photo upload."""
import logging
import os
import smtplib
import uuid
from email.mime.text import MIMEText
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.database import db

logger = logging.getLogger("lcewai")
router = APIRouter()

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
ALERT_EMAIL = os.environ.get("GMAIL_USER", "youpickeddoliver@gmail.com")

# Allowed MIME types for public photo upload
_ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_MAX_BYTES = 10 * 1024 * 1024  # 10 MB


class TipBody(BaseModel):
    name: str
    tip: str
    contact: Optional[str] = ""


@router.post("/missing/tip")
async def submit_tip(body: TipBody):
    msg_body = f"TIP FOR: {body.name}\n\n{body.tip}"
    if body.contact:
        msg_body += f"\n\nContact: {body.contact}"

    if GMAIL_USER and GMAIL_APP_PASSWORD:
        try:
            msg = MIMEText(msg_body)
            msg["Subject"] = f"MISSING PERSON TIP: {body.name}"
            msg["From"] = GMAIL_USER
            msg["To"] = ALERT_EMAIL
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
                s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
                s.send_message(msg)
        except Exception as e:
            logger.error("Tip email failed: %s", e)

    logger.info("Missing person tip received for %s", body.name)
    return {"received": True}


@router.post("/missing/photo")
async def upload_missing_photo(
    file: UploadFile = File(...),
    case_id: str = Form("kameron-mcmullen"),
):
    """Public endpoint — anyone can upload a photo for a missing persons case."""
    content_type = file.content_type or ""
    if content_type not in _ALLOWED:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are accepted.")

    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image must be under 10 MB.")

    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    try:
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        bucket = AsyncIOMotorGridFSBucket(db, bucket_name="missing_photos")
        file_id = str(uuid.uuid4())
        import io
        gridfs_id = await bucket.upload_from_stream(
            file.filename or "photo",
            io.BytesIO(content),
            metadata={
                "case_id": case_id,
                "file_id": file_id,
                "content_type": content_type,
            },
        )
        await db.missing_photos.insert_one({
            "file_id": file_id,
            "gridfs_id": str(gridfs_id),
            "case_id": case_id,
            "filename": file.filename or "photo",
            "content_type": content_type,
            "size": len(content),
        })
        logger.info("Missing photo uploaded: case=%s file=%s", case_id, file_id)
        return {"id": file_id, "case_id": case_id}
    except Exception as e:
        logger.error("Missing photo upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Upload failed.")


@router.get("/missing/photo/{file_id}")
async def get_missing_photo(file_id: str):
    """Serve a missing persons photo by file_id."""
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    doc = await db.missing_photos.find_one({"file_id": file_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Photo not found.")

    try:
        import bson
        from motor.motor_asyncio import AsyncIOMotorGridFSBucket
        from fastapi.responses import Response
        bucket = AsyncIOMotorGridFSBucket(db, bucket_name="missing_photos")
        gridfs_id = bson.ObjectId(doc["gridfs_id"])
        stream = await bucket.open_download_stream(gridfs_id)
        data = await stream.read()
        return Response(content=data, media_type=doc.get("content_type", "image/jpeg"))
    except Exception as e:
        logger.error("Missing photo serve failed: %s", e)
        raise HTTPException(status_code=500, detail="Could not retrieve photo.")


@router.get("/missing/photos/{case_id}")
async def list_missing_photos(case_id: str):
    """List all photo IDs for a case."""
    if db is None:
        return {"photos": []}
    docs = await db.missing_photos.find(
        {"case_id": case_id}, {"_id": 0, "file_id": 1}
    ).to_list(length=50)
    return {"photos": [d["file_id"] for d in docs]}
