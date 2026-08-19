"""
playlist.py — Playlist Curation router (Nova's playlist gateways + artist submissions).

Mounted at /api (via api_router in server.py), so routes below resolve to
/api/playlist/... — matching the frontend contract in PlaylistDashboard.jsx
and PlaylistSubmit.jsx.

Flow: curator creates gateways (admin) → artists submit songs (public) →
artists complete 5 gateway steps (public) → curator approves/rejects (admin).

Collections:
  playlist_gateways   — open/full/closed spot opportunities
  playlist_submissions — artist submissions with per-step completion
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["playlist"])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None


def bind(_db, _current_user):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user
    db = _db
    current_user = _current_user


# ROLE_RANK imported from roles.py


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: str = "student"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


async def _dep_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Resolve the real current_user at REQUEST time (bind() sets it after import)."""
    return await current_user(authorization)


def _require_rank(*roles):
    """Runtime equivalent of server.py's require_role() — used in Depends()."""
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: User = Depends(_dep_current_user)) -> User:
        if ROLE_RANK.get(user.role, 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions")
        return user

    return dep


# ── Constants (must match PlaylistSubmit.jsx STEPS) ──────────────────────────
GATEWAY_STEPS = ["save_playlist", "follow_playlist", "add_song", "follow_profile", "share"]
STEP_LABELS = {
    "save_playlist": "Save Playlist",
    "follow_playlist": "Follow Playlist",
    "add_song": "Add Required Song",
    "follow_profile": "Follow on Spotify",
    "share": "Share",
}


# ── Request models ────────────────────────────────────────────────────────────
class _GatewayCreateReq(BaseModel):
    playlist_name: str = Field(..., min_length=1, max_length=200)
    playlist_spotify_url: str = Field(..., min_length=5)
    curator_spotify_url: str = Field(..., min_length=5)
    target_song_name: str = Field(..., min_length=1, max_length=300)
    target_song_url: str = Field(..., min_length=5)
    max_slots: int = Field(2, ge=1, le=20)
    notes: Optional[str] = ""
    curator_slug: str = Field("nova-highborn", min_length=1, max_length=200)


class _SubmitReq(BaseModel):
    gateway_id: str
    artist_name: str = Field(..., min_length=1, max_length=200)
    artist_email: str = Field(..., max_length=300)
    artist_spotify_url: str = Field(..., min_length=5)
    song_title: str = Field(..., min_length=1, max_length=300)
    song_spotify_url: str = Field(..., min_length=5)
    genre: str = Field(..., min_length=1, max_length=100)


class _CompleteStepReq(BaseModel):
    submission_id: str
    step: str
    share_url: Optional[str] = ""


class _ReviewReq(BaseModel):
    submission_id: str
    note: Optional[str] = ""


async def _gateway_doc(gateway_id: str):
    try:
        return await db.playlist_gateways.find_one({"_id": ObjectId(gateway_id)})
    except Exception:
        return None


def _gw_out(gw) -> dict:
    """Public-facing gateway shape (no internal fields leaked)."""
    return {
        "_id": str(gw["_id"]),
        "playlist_name": gw.get("playlist_name", ""),
        "playlist_spotify_url": gw.get("playlist_spotify_url", ""),
        "curator_spotify_url": gw.get("curator_spotify_url", ""),
        "target_song_name": gw.get("target_song_name", ""),
        "target_song_url": gw.get("target_song_url", ""),
        "max_slots": gw.get("max_slots", 2),
        "notes": gw.get("notes", ""),
        "status": gw.get("status", "closed"),
        "filled_slots": gw.get("filled_slots", 0),
        "curator_slug": gw.get("curator_slug", "nova-highborn"),
    }


async def _count_filled(gateway_id: ObjectId) -> int:
    return await db.playlist_submissions.count_documents(
        {"gateway_id": gateway_id, "status": {"$in": ["approved", "live"]}})


async def _attach_counts(gateways) -> list:
    out = []
    for gw in gateways:
        d = dict(gw)
        d["filled_slots"] = await _count_filled(gw["_id"])
        out.append(d)
    return out


# ── Public: artist-facing ─────────────────────────────────────────────────────
@router.get("/playlist/gateways/{slug}")
async def playlist_public_gateways(slug: str):
    """Open gateways for a curator slug. Empty list => closed/paused."""
    gws = await db.playlist_gateways.find(
        {"curator_slug": slug, "status": "open"}
    ).sort("created_at", -1).to_list(50)
    gws = await _attach_counts(gws)
    # Hide gateways whose spots are full.
    open_gws = [gw for gw in gws if gw["filled_slots"] < gw.get("max_slots", 2)]
    return {"gateways": [_gw_out(gw) for gw in open_gws]}


@router.post("/playlist/submit")
async def playlist_submit(body: _SubmitReq):
    gw = await _gateway_doc(body.gateway_id)
    if not gw:
        raise HTTPException(404, "Gateway not found")
    if gw.get("status") != "open":
        raise HTTPException(400, "This playlist is not currently open for submissions.")
    filled = await _count_filled(gw["_id"])
    if filled >= gw.get("max_slots", 2):
        raise HTTPException(400, "This playlist is full — try another open playlist.")

    now = datetime.now(timezone.utc)
    submission = {
        "gateway_id": gw["_id"],
        "artist_name": body.artist_name.strip(),
        "artist_email": body.artist_email.strip(),
        "artist_spotify_url": body.artist_spotify_url.strip(),
        "song_title": body.song_title.strip(),
        "song_spotify_url": body.song_spotify_url.strip(),
        "genre": body.genre.strip(),
        "status": "pending",
        "steps_completed": {s: False for s in GATEWAY_STEPS},
        "share_url": "",
        "curator_note": "",
        "created_at": now,
        "updated_at": now,
    }
    res = await db.playlist_submissions.insert_one(submission)
    return {"submission_id": str(res.inserted_id), "gateway_id": str(gw["_id"])}


@router.post("/playlist/complete-step")
async def playlist_complete_step(body: _CompleteStepReq):
    if body.step not in GATEWAY_STEPS:
        raise HTTPException(400, f"Unknown step '{body.step}'. Valid: {GATEWAY_STEPS}")
    try:
        sub_id = ObjectId(body.submission_id)
    except Exception:
        raise HTTPException(404, "Submission not found")
    sub = await db.playlist_submissions.find_one({"_id": sub_id})
    if not sub:
        raise HTTPException(404, "Submission not found")

    steps = dict(sub.get("steps_completed") or {})
    steps[body.step] = True
    update = {"steps_completed": steps, "updated_at": datetime.now(timezone.utc)}
    if body.step == "share" and body.share_url:
        update["share_url"] = body.share_url.strip()
    await db.playlist_submissions.update_one({"_id": sub_id}, {"$set": update})

    all_done = all(steps.get(s) is True for s in GATEWAY_STEPS)
    return {"steps_completed": steps, "all_steps_complete": all_done}


# ── Admin: curator dashboard ──────────────────────────────────────────────────
@router.get("/playlist/dashboard")
async def playlist_dashboard(user: User = Depends(_require_rank("admin"))):
    gws = await db.playlist_gateways.find({}).sort("created_at", -1).to_list(100)
    gws = await _attach_counts(gws)

    out_gateways = []
    total_submissions = 0
    total_approved = 0
    open_count = 0
    for gw in gws:
        subs = await db.playlist_submissions.find(
            {"gateway_id": gw["_id"]}
        ).sort("created_at", -1).to_list(200)
        total_submissions += len(subs)
        pending = approved = 0
        sub_out = []
        for s in subs:
            st = s.get("status", "pending")
            if st == "pending":
                pending += 1
            elif st in ("approved", "live"):
                approved += 1
            sub_out.append({
                "_id": str(s["_id"]),
                "artist_name": s.get("artist_name", ""),
                "artist_email": s.get("artist_email", ""),
                "artist_spotify_url": s.get("artist_spotify_url", ""),
                "song_title": s.get("song_title", ""),
                "song_spotify_url": s.get("song_spotify_url", ""),
                "genre": s.get("genre", ""),
                "status": st,
                "steps_completed": s.get("steps_completed", {}),
                "share_url": s.get("share_url", ""),
                "curator_note": s.get("curator_note", ""),
                "created_at": s.get("created_at").isoformat() if hasattr(s.get("created_at"), "isoformat") else None,
            })
        total_approved += approved
        if gw.get("status") == "open" and gw["filled_slots"] < gw.get("max_slots", 2):
            open_count += 1
        out_gateways.append({
            "_id": str(gw["_id"]),
            "playlist_name": gw.get("playlist_name", ""),
            "playlist_spotify_url": gw.get("playlist_spotify_url", ""),
            "status": gw.get("status", "closed"),
            "filled_slots": gw["filled_slots"],
            "max_slots": gw.get("max_slots", 2),
            "notes": gw.get("notes", ""),
            "pending_count": pending,
            "approved_count": approved,
            "submissions": sub_out,
        })

    return {
        "gateways": out_gateways,
        "open_gateways": open_count,
        "total_submissions": total_submissions,
        "total_approved": total_approved,
    }


@router.post("/playlist/gateway/create")
async def playlist_gateway_create(body: _GatewayCreateReq,
                                  user: User = Depends(_require_rank("admin"))):
    now = datetime.now(timezone.utc)
    gw = {
        "playlist_name": body.playlist_name.strip(),
        "playlist_spotify_url": body.playlist_spotify_url.strip(),
        "curator_spotify_url": body.curator_spotify_url.strip(),
        "target_song_name": body.target_song_name.strip(),
        "target_song_url": body.target_song_url.strip(),
        "max_slots": body.max_slots,
        "notes": body.notes.strip() if body.notes else "",
        "curator_slug": body.curator_slug.strip(),
        "status": "open",
        "created_by": user.id,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.playlist_gateways.insert_one(gw)
    return {"ok": True, "gateway_id": str(res.inserted_id)}


@router.post("/playlist/approve")
async def playlist_approve(body: _ReviewReq, user: User = Depends(_require_rank("admin"))):
    try:
        sub_id = ObjectId(body.submission_id)
    except Exception:
        raise HTTPException(404, "Submission not found")
    sub = await db.playlist_submissions.find_one({"_id": sub_id})
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.playlist_submissions.update_one({"_id": sub_id}, {"$set": {
        "status": "approved",
        "curator_note": body.note or "",
        "reviewed_by": user.id,
        "reviewed_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }})
    return {"ok": True, "submission_id": body.submission_id, "status": "approved"}


@router.post("/playlist/reject")
async def playlist_reject(body: _ReviewReq, user: User = Depends(_require_rank("admin"))):
    try:
        sub_id = ObjectId(body.submission_id)
    except Exception:
        raise HTTPException(404, "Submission not found")
    sub = await db.playlist_submissions.find_one({"_id": sub_id})
    if not sub:
        raise HTTPException(404, "Submission not found")
    await db.playlist_submissions.update_one({"_id": sub_id}, {"$set": {
        "status": "rejected",
        "curator_note": body.note or "",
        "reviewed_by": user.id,
        "reviewed_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }})
    return {"ok": True, "submission_id": body.submission_id, "status": "rejected"}


@router.patch("/playlist/gateway/{gateway_id}/status")
async def playlist_toggle_gateway(gateway_id: str, user: User = Depends(_require_rank("admin"))):
    gw = await _gateway_doc(gateway_id)
    if not gw:
        raise HTTPException(404, "Gateway not found")
    new_status = "closed" if gw.get("status") == "open" else "open"
    await db.playlist_gateways.update_one({"_id": gw["_id"]}, {"$set": {
        "status": new_status,
        "updated_by": user.id,
        "updated_at": datetime.now(timezone.utc),
    }})
    return {"ok": True, "gateway_id": gateway_id, "status": new_status}
