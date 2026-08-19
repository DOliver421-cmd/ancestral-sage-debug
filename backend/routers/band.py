"""
band — Band listings and bookings.

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

logger = logging.getLogger("lcewai")
router = APIRouter(tags=['band'])


# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None
notify = None


def bind(_db, _current_user, _audit, _notify):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit, notify
    
    db = _db
    current_user = _current_user
    audit = _audit
    notify = _notify


# Mirrors server.py's role hierarchy for runtime require_role checks.
ROLE_RANK = {"student": 1, "priority_member": 2, "instructor": 2, "creative_partner": 2, "site_support": 3, "admin": 3, "executive_admin": 4}
Role = Literal["student", "priority_member", "instructor", "creative_partner", "site_support", "admin", "executive_admin"]


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


# ═══════════════════════════════════════════════════════════════════════════════
#  BAND ON PAGE  —  /api/band/*
#  Live music booking: artist listings, venue inquiries, booking requests.
# ═══════════════════════════════════════════════════════════════════════════════

class _BandListingReq(BaseModel):
    artist_name: str  = Field(..., min_length=1, max_length=200)
    bio:         str  = Field("", max_length=3000)
    genres:      List[str] = []
    location:    str  = Field("", max_length=200)
    rate_min:    Optional[int] = None   # cents
    rate_max:    Optional[int] = None   # cents
    available:   bool = True
    social_links: dict = {}

class _BandBookingReq(BaseModel):
    listing_id:  str
    event_name:  str  = Field(..., min_length=1, max_length=200)
    event_date:  str  = Field(..., min_length=8, max_length=30)
    venue_name:  str  = Field(..., min_length=1, max_length=200)
    venue_city:  str  = Field("", max_length=100)
    offer_cents: Optional[int] = None
    message:     str  = Field("", max_length=1000)

@router.get("/band/listings")
async def band_list(
    genre: Optional[str] = None, location: Optional[str] = None,
    available_only: bool = True, limit: int = 30, offset: int = 0
):
    q: dict = {}
    if available_only: q["available"] = True
    if genre:    q["genres"]   = {"$regex": genre, "$options": "i"}
    if location: q["location"] = {"$regex": location, "$options": "i"}
    total  = await db.band_listings.count_documents(q)
    cursor = db.band_listings.find(q, {"_id": 0}).sort("created_at", -1).skip(offset).limit(min(limit, 50))
    return {"total": total, "listings": await cursor.to_list(min(limit, 50))}

@router.post("/band/listings")
async def band_create_listing(body: _BandListingReq, user: User = Depends(_dep_current_user)):
    existing = await db.band_listings.find_one({"owner_id": user.id}, {"_id": 0, "id": 1})
    doc = {
        "id":          existing["id"] if existing else str(uuid.uuid4()),
        "owner_id":    user.id,
        "artist_name": body.artist_name,
        "bio":         body.bio,
        "genres":      body.genres,
        "location":    body.location,
        "rate_min":    body.rate_min,
        "rate_max":    body.rate_max,
        "available":   body.available,
        "social_links":body.social_links,
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }
    if existing:
        await db.band_listings.update_one({"owner_id": user.id}, {"$set": doc})
    else:
        doc["created_at"] = datetime.now(timezone.utc).isoformat()
        await db.band_listings.insert_one({**doc, "_id": doc["id"]})
    await audit(user.id, "band.listing.upserted", target=doc["id"])
    return doc

@router.get("/band/my-listing")
async def band_my_listing(user: User = Depends(_dep_current_user)):
    doc = await db.band_listings.find_one({"owner_id": user.id}, {"_id": 0})
    return doc or {}

@router.post("/band/book")
async def band_request_booking(body: _BandBookingReq, user: User = Depends(_dep_current_user)):
    listing = await db.band_listings.find_one({"id": body.listing_id}, {"_id": 0, "owner_id": 1, "artist_name": 1, "available": 1})
    if not listing: raise HTTPException(404, "Artist listing not found")
    if not listing.get("available"): raise HTTPException(400, "This artist is not currently available")
    booking = {
        "id":           str(uuid.uuid4()),
        "listing_id":   body.listing_id,
        "artist_id":    listing["owner_id"],
        "artist_name":  listing["artist_name"],
        "requester_id": user.id,
        "requester_name": getattr(user, "full_name", None) or getattr(user, "email", ""),
        "event_name":   body.event_name,
        "event_date":   body.event_date,
        "venue_name":   body.venue_name,
        "venue_city":   body.venue_city,
        "offer_cents":  body.offer_cents,
        "message":      body.message,
        "status":       "pending",
        "created_at":   datetime.now(timezone.utc).isoformat(),
    }
    await db.band_bookings.insert_one({**booking, "_id": booking["id"]})
    await notify(listing["owner_id"], "New Booking Request",
        f"{booking['requester_name']} wants to book you for {body.event_name} on {body.event_date}.",
        link="/band/bookings", kind="info")
    await audit(user.id, "band.booking.requested", target=booking["id"])
    return {"ok": True, "booking_id": booking["id"]}

@router.get("/band/bookings")
async def band_my_bookings(user: User = Depends(_dep_current_user)):
    as_artist   = await db.band_bookings.find({"artist_id":    user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    as_requester= await db.band_bookings.find({"requester_id": user.id}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return {"as_artist": as_artist, "as_requester": as_requester}

@router.patch("/band/bookings/{booking_id}/status")
async def band_update_booking(booking_id: str, body: dict, user: User = Depends(_dep_current_user)):
    status = body.get("status")
    if status not in ("accepted", "declined", "cancelled"):
        raise HTTPException(400, "status must be accepted, declined, or cancelled")
    bk = await db.band_bookings.find_one({"id": booking_id}, {"_id": 0})
    if not bk: raise HTTPException(404, "Booking not found")
    if bk["artist_id"] != user.id and bk["requester_id"] != user.id:
        raise HTTPException(403, "Not your booking")
    await db.band_bookings.update_one({"id": booking_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    notify_uid = bk["requester_id"] if user.id == bk["artist_id"] else bk["artist_id"]
    await notify(notify_uid, f"Booking {status.title()}",
        f"Your booking for {bk['event_name']} has been {status}.", link="/band/bookings", kind="info")
    return {"ok": True, "booking_id": booking_id, "status": status}
