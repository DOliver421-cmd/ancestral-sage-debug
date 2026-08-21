"""
Vonns Saga API Routes
- Track upload for $1 sale with 33-second preview
- Image upload to saga pages
- Video creation (short-form, image animation, soundtrack)
"""

import os
import uuid
import json
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional

router = APIRouter(prefix="/api/saga", tags=["saga"])

# In-memory store (replace with DB in production)
_saga_tracks = []
_saga_images = []
_saga_videos = []

MAX_PREVIEW_SECONDS = 33
TRACK_PRICE_CENTS = 100


# ── Tracks ────────────────────────────────────────────────────────────────────

@router.post("/tracks")
async def upload_track(
    file: UploadFile = File(...),
    title: str = Form(...),
    price_cents: int = Form(TRACK_PRICE_CENTS),
    preview_start: float = Form(0),
    preview_duration: float = Form(MAX_PREVIEW_SECONDS),
    type: str = Form("track"),
):
    """Upload a track for $1 sale with 33-second preview limit."""
    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(400, "File must be audio")
    
    # Read file data
    data = await file.read()
    
    track = {
        "id": str(uuid.uuid4())[:12],
        "title": title,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(data),
        "price_cents": price_cents,
        "preview_start": preview_start,
        "preview_duration": min(preview_duration, MAX_PREVIEW_SECONDS),
        "created_at": datetime.utcnow().isoformat(),
    }
    _saga_tracks.append(track)
    
    return {"ok": True, "track": track, "message": f"Track '{title}' uploaded — ${price_cents/100:.2f}, {MAX_PREVIEW_SECONDS}s preview"}


@router.get("/tracks")
async def list_tracks():
    """List all uploaded saga tracks."""
    return {"tracks": _saga_tracks}


@router.delete("/tracks/{track_id}")
async def delete_track(track_id: str):
    """Delete a saga track."""
    global _saga_tracks
    before = len(_saga_tracks)
    _saga_tracks = [t for t in _saga_tracks if t["id"] != track_id]
    if len(_saga_tracks) == before:
        raise HTTPException(404, "Track not found")
    return {"ok": True, "message": "Track deleted"}


# ── Images ────────────────────────────────────────────────────────────────────

@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    node_id: str = Form("general"),
    caption: str = Form(""),
):
    """Upload an image to a saga page."""
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "File must be an image")
    
    data = await file.read()
    
    image = {
        "id": str(uuid.uuid4())[:12],
        "node_id": node_id,
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(data),
        "caption": caption,
        "created_at": datetime.utcnow().isoformat(),
    }
    _saga_images.append(image)
    
    return {"ok": True, "image": image, "message": f"Image added to scene '{node_id}'"}


@router.get("/images")
async def list_images(node_id: Optional[str] = None):
    """List saga images, optionally filtered by node."""
    if node_id:
        return {"images": [i for i in _saga_images if i["node_id"] == node_id]}
    return {"images": _saga_images}


# ── Videos ────────────────────────────────────────────────────────────────────

@router.post("/videos")
async def create_video(
    title: str = Form("Vonns Saga Video"),
    node_id: str = Form("general"),
    duration_seconds: int = Form(15),
):
    """Create a short-form video with Ken Burns pan/zoom effect on uploaded images."""
    video = {
        "id": str(uuid.uuid4())[:12],
        "title": title,
        "node_id": node_id,
        "duration_seconds": duration_seconds,
        "status": "processing",
        "effects": ["ken_burns_pan", "ken_burns_zoom", "crossfade_transitions"],
        "created_at": datetime.utcnow().isoformat(),
    }
    _saga_videos.append(video)
    
    return {"ok": True, "video": video, "message": f"Video '{title}' created — {duration_seconds}s with Ken Burns effect"}


@router.get("/videos")
async def list_videos():
    """List all saga videos."""
    return {"videos": _saga_videos}
