"""
Playlist Curation — Gateway Submission System

Curators (Nova Highborn, etc.) run Spotify playlist placement services.
Artists submit songs and complete gateway requirements for free placements.

Gateway steps (all 5 required):
  1. save_playlist   — save the curator's playlist to their Spotify library
  2. follow_playlist — follow the playlist on Spotify
  3. add_song        — add the curator's required song to their library
  4. follow_profile  — follow the curator on Spotify
  5. share           — share the playlist on social media (artist pastes post URL)

Each gateway has a max_slots (default 2). When approved submissions reach max_slots
the gateway automatically closes. Curators can reopen it at any time.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from bson import ObjectId

from deps import require_user, get_db

router = APIRouter(prefix="/api/playlist", tags=["playlist"])

GATEWAY_STEPS = ["save_playlist", "follow_playlist", "add_song", "follow_profile", "share"]


def _ser(doc):
    if doc and "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ── Request models ────────────────────────────────────────────────────────────

class GatewayCreateRequest(BaseModel):
    playlist_name: str
    playlist_spotify_url: str
    playlist_spotify_id: str = ""
    curator_spotify_url: str = ""
    target_song_name: str = ""
    target_song_url: str = ""
    max_slots: int = 2
    notes: str = ""
    curator_slug: str = ""


class SubmissionRequest(BaseModel):
    gateway_id: str
    artist_name: str
    artist_email: str
    artist_spotify_url: str
    song_title: str
    song_spotify_url: str
    genre: str = ""
    share_url: str = ""


class StepRequest(BaseModel):
    submission_id: str
    step: str
    share_url: str = ""


class ReviewRequest(BaseModel):
    submission_id: str
    note: str = ""


# ── Public endpoints ──────────────────────────────────────────────────────────

@router.get("/gateways/{curator_slug}")
async def get_active_gateways(curator_slug: str):
    """Public — list open gateways for a curator (used by submission form)."""
    db = get_db()
    gateways = await db.playlist_gateways.find(
        {"curator_slug": curator_slug, "status": "open"}
    ).sort("created_at", -1).to_list(None)
    return {
        "status": "success",
        "curator_slug": curator_slug,
        "gateways": [_ser(g) for g in gateways],
    }


@router.post("/submit")
async def submit_song(data: SubmissionRequest):
    """Public — artist submits a song to an open gateway."""
    db = get_db()

    try:
        gateway = await db.playlist_gateways.find_one({"_id": ObjectId(data.gateway_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid gateway ID")

    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")
    if gateway["status"] != "open":
        raise HTTPException(status_code=400, detail="This gateway is full or closed — check back soon.")

    existing = await db.playlist_submissions.find_one({
        "gateway_id": data.gateway_id,
        "artist_email": data.artist_email.lower().strip(),
    })
    if existing:
        raise HTTPException(status_code=400, detail="You've already submitted to this gateway. Check your email for updates.")

    doc = {
        "gateway_id": data.gateway_id,
        "curator_slug": gateway["curator_slug"],
        "curator_id": gateway["curator_id"],
        "playlist_name": gateway["playlist_name"],
        "artist_name": data.artist_name.strip(),
        "artist_email": data.artist_email.lower().strip(),
        "artist_spotify_url": data.artist_spotify_url.strip(),
        "song_title": data.song_title.strip(),
        "song_spotify_url": data.song_spotify_url.strip(),
        "genre": data.genre.strip(),
        "share_url": data.share_url.strip(),
        "steps_completed": {step: False for step in GATEWAY_STEPS},
        "all_steps_complete": False,
        "status": "pending",
        "submitted_at": datetime.utcnow(),
        "approved_at": None,
        "curator_note": "",
    }
    result = await db.playlist_submissions.insert_one(doc)
    return {
        "status": "success",
        "message": "Song submitted! Complete all 5 gateway steps so Nova can review your track.",
        "submission_id": str(result.inserted_id),
    }


@router.post("/complete-step")
async def complete_step(data: StepRequest):
    """Public — artist marks a gateway step as complete."""
    if data.step not in GATEWAY_STEPS:
        raise HTTPException(status_code=400, detail=f"Invalid step: {data.step}")

    db = get_db()
    try:
        sub = await db.playlist_submissions.find_one({"_id": ObjectId(data.submission_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid submission ID")

    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    steps = sub.get("steps_completed", {})
    steps[data.step] = True

    update = {"steps_completed": steps}
    if data.step == "share" and data.share_url:
        update["share_url"] = data.share_url.strip()

    all_complete = all(steps.get(s, False) for s in GATEWAY_STEPS)
    update["all_steps_complete"] = all_complete

    await db.playlist_submissions.update_one(
        {"_id": ObjectId(data.submission_id)},
        {"$set": update}
    )
    return {
        "status": "success",
        "steps_completed": steps,
        "all_steps_complete": all_complete,
        "steps_remaining": [s for s in GATEWAY_STEPS if not steps.get(s, False)],
    }


# ── Curator-authenticated endpoints ──────────────────────────────────────────

@router.post("/gateway/create")
async def create_gateway(
    data: GatewayCreateRequest,

    current_user: dict = Depends(require_user),
):
    """Authenticated — curator creates a new gateway slot."""
    db = get_db()
    curator_slug = data.curator_slug or current_user.get("creator_slug", str(current_user["_id"]))

    doc = {
        "curator_slug": curator_slug,
        "curator_id": str(current_user["_id"]),
        "curator_name": current_user.get("full_name", ""),
        "playlist_name": data.playlist_name,
        "playlist_spotify_url": data.playlist_spotify_url,
        "playlist_spotify_id": data.playlist_spotify_id,
        "curator_spotify_url": data.curator_spotify_url,
        "target_song_name": data.target_song_name,
        "target_song_url": data.target_song_url,
        "max_slots": data.max_slots,
        "filled_slots": 0,
        "status": "open",
        "notes": data.notes,
        "created_at": datetime.utcnow(),
    }
    result = await db.playlist_gateways.insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return {"status": "success", "gateway": doc}


@router.get("/dashboard")
async def get_dashboard(

    current_user: dict = Depends(require_user),
):
    """Authenticated — curator's full dashboard with all gateways and submissions."""
    db = get_db()
    curator_id = str(current_user["_id"])

    gateways = await db.playlist_gateways.find(
        {"curator_id": curator_id}
    ).sort("created_at", -1).to_list(None)

    gateway_data = []
    for gw in gateways:
        gw_id = str(gw["_id"])
        submissions = await db.playlist_submissions.find(
            {"gateway_id": gw_id}
        ).sort("submitted_at", -1).to_list(None)

        gateway_data.append({
            **_ser(gw),
            "submissions": [_ser(s) for s in submissions],
            "pending_count": sum(1 for s in submissions if s["status"] == "pending"),
            "approved_count": sum(1 for s in submissions if s["status"] in ("approved", "live")),
            "complete_steps_count": sum(1 for s in submissions if s.get("all_steps_complete")),
        })

    total_submissions = sum(len(g["submissions"]) for g in gateway_data)
    total_approved = sum(g["approved_count"] for g in gateway_data)

    return {
        "status": "success",
        "curator_name": current_user.get("full_name", ""),
        "gateways": gateway_data,
        "total_submissions": total_submissions,
        "total_approved": total_approved,
        "open_gateways": sum(1 for g in gateway_data if g["status"] == "open"),
    }


@router.post("/approve")
async def approve_submission(
    data: ReviewRequest,

    current_user: dict = Depends(require_user),
):
    """Authenticated — curator approves an artist's submission."""
    db = get_db()
    try:
        sub = await db.playlist_submissions.find_one({"_id": ObjectId(data.submission_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid submission ID")

    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub["curator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your submission")

    await db.playlist_submissions.update_one(
        {"_id": ObjectId(data.submission_id)},
        {"$set": {
            "status": "approved",
            "curator_note": data.note,
            "approved_at": datetime.utcnow(),
        }}
    )

    # Auto-close gateway if max_slots reached
    try:
        approved_count = await db.playlist_submissions.count_documents({
            "gateway_id": sub["gateway_id"],
            "status": {"$in": ["approved", "live"]},
        })
        gateway = await db.playlist_gateways.find_one({"_id": ObjectId(sub["gateway_id"])})
        if gateway:
            update = {"filled_slots": approved_count}
            if approved_count >= gateway.get("max_slots", 2):
                update["status"] = "full"
            await db.playlist_gateways.update_one(
                {"_id": ObjectId(sub["gateway_id"])},
                {"$set": update}
            )
    except Exception:
        pass

    return {"status": "success", "message": "Artist approved — add their song to your playlist!"}


@router.post("/reject")
async def reject_submission(
    data: ReviewRequest,

    current_user: dict = Depends(require_user),
):
    """Authenticated — curator rejects a submission."""
    db = get_db()
    try:
        sub = await db.playlist_submissions.find_one({"_id": ObjectId(data.submission_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid submission ID")

    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub["curator_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not your submission")

    await db.playlist_submissions.update_one(
        {"_id": ObjectId(data.submission_id)},
        {"$set": {"status": "rejected", "curator_note": data.note}}
    )
    return {"status": "success", "message": "Submission rejected"}


@router.patch("/gateway/{gateway_id}/status")
async def set_gateway_status(
    gateway_id: str,

    current_user: dict = Depends(require_user),
):
    """Authenticated — toggle gateway open/closed."""
    db = get_db()
    gateway = await db.playlist_gateways.find_one({
        "_id": ObjectId(gateway_id),
        "curator_id": str(current_user["_id"]),
    })
    if not gateway:
        raise HTTPException(status_code=404, detail="Gateway not found")

    new_status = "open" if gateway["status"] != "open" else "closed"
    await db.playlist_gateways.update_one(
        {"_id": ObjectId(gateway_id)},
        {"$set": {"status": new_status}}
    )
    return {"status": "success", "gateway_status": new_status}
