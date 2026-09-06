"""
Vonns Saga API — the real media funnel.

Story nodes are static (frontend), but every asset behind the saga is real:

- Tracks   → audio bytes stored in MongoDB GridFS; each track is a
             `media_products` record (price $1, 33s preview) so the existing
             checkout / purchase / entitlement engine handles money. Playback
             goes through GET /api/media/file/{gfs_id} (preview-limited until
             purchased).
- Images   → GridFS; metadata in `saga_assets` (kind=image, node_id, caption)
             so story scenes can render the owner's artwork.
- Videos   → real mp4 rendered with ffmpeg (Ken Burns pan/zoom per image +
             xfade transitions + optional soundtrack) in a background task;
             result stored in GridFS with status ready / render_failed. A job
             never lies about being "processing" — if ffmpeg is missing the
             record is marked render_failed with the reason.
- Concerts → paid `media_products` records (type=video) tagged "vonn-live".
             Checkout is members-only (tier gate) + paid.

Every write is admin-gated. The old implementation stored metadata in module
memory, discarded the file bytes, and fabricated "processing" video records.
This replaces that facade.
"""

import asyncio
import logging
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

logger = logging.getLogger("lcewai")
router = APIRouter(prefix="/api/saga", tags=["saga"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
audit = None

MAX_PREVIEW_SECONDS = 33
TRACK_PRICE_CENTS = 100          # $1.00 per track
MAX_UPLOAD_MB = 100
CONCERT_TAG = "vonn-live"

# Roles that may upload/manage saga assets (mirrors the frontend admin gate).
_SAGA_STAFF = ("admin", "executive_admin", "support_staff", "oversight")


def bind(_db, _current_user, _audit):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Auth helpers (mirror routers/media.py) ───────────────────────────────────
from routers.media import _dep_current_user, _optional_current_user, _require_rank  # noqa: E402


# ── GridFS helpers ───────────────────────────────────────────────────────────

async def _store_file(filename: str, contents: bytes, content_type: str,
                      extra_meta: dict) -> str:
    """Store bytes in GridFS and return the serving URL (/api/media/file/<id>)."""
    bucket = AsyncIOMotorGridFSBucket(db)
    metadata = {"content_type": content_type or "application/octet-stream", **extra_meta}
    gfs_id = await bucket.upload_from_stream(filename, contents, metadata=metadata)
    return f"/api/media/file/{gfs_id}"


async def _delete_file(file_url: str) -> None:
    """Best-effort GridFS delete by file URL."""
    if not file_url:
        return
    fid = file_url.rsplit("/", 1)[-1]
    try:
        from bson import ObjectId
        bucket = AsyncIOMotorGridFSBucket(db)
        await bucket.delete(ObjectId(fid))
    except Exception as exc:  # never block a delete on file cleanup
        logger.warning("saga: file cleanup failed for %s: %s", file_url, exc)


# ── Tracks (sellable $1 audio) ───────────────────────────────────────────────

@router.post("/tracks")
async def upload_track(
    file: UploadFile = File(...),
    title: str = Form(...),
    price_cents: int = Form(TRACK_PRICE_CENTS),
    preview_start: float = Form(0),
    preview_duration: float = Form(MAX_PREVIEW_SECONDS),
    duration_seconds: float = Form(...),
    user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight")),
):
    """Upload a track for sale: GridFS + media_product ($1, 33s preview)."""
    if not file.content_type or not file.content_type.lower().startswith("audio/"):
        raise HTTPException(400, "File must be audio")
    if duration_seconds <= 0:
        raise HTTPException(400, "duration_seconds is required for audio uploads")

    # Read with cap — a hostile multi-GB upload must not land in memory first.
    contents = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD_MB}MB)")

    preview_sec = min(preview_duration, MAX_PREVIEW_SECONDS)
    preview_bytes = (
        len(contents)
        if duration_seconds <= MAX_PREVIEW_SECONDS
        else max(1, int(len(contents) * (MAX_PREVIEW_SECONDS / duration_seconds)))
    )

    file_url = await _store_file(
        file.filename or "track.mp3", contents, file.content_type,
        {
            "kind": "saga_track",
            "duration_seconds": duration_seconds,
            "preview_seconds": preview_sec,
            "preview_bytes": preview_bytes,
        },
    )

    pid = "saga_" + str(uuid.uuid4())[:8]
    product = {
        "id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": title.strip(),
        "description": "Vonns Saga track — 33-second preview, full download on purchase.",
        "price_cents": max(50, price_cents),
        "type": "track",
        "product_type": "track",
        "tags": ["saga", "vonn"],
        "file_url": file_url,
        "preview_seconds": preview_sec,
        "cover_url": "",
        "published": True,
        "saga": {"kind": "track", "preview_start": preview_start, "preview_duration": preview_sec},
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.media_products.insert_one(product)
    product.pop("_id", None)
    await audit(user.id, "saga.track_uploaded", target=pid,
                meta={"title": title, "size": len(contents)})
    return {"ok": True, "track": product,
            "message": f"Track '{title}' live — ${price_cents/100:.2f}, {preview_sec}s preview"}


@router.get("/tracks")
async def list_tracks(user=Depends(_optional_current_user)):
    """List published saga tracks (for the story page players)."""
    docs = await db.media_products.find(
        {"published": True, "type": "track", "tags": "saga"},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)
    return {"tracks": docs}


@router.delete("/tracks/{track_id}")
async def delete_track(track_id: str, user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight"))):
    doc = await db.media_products.find_one({"id": track_id, "type": "track"})
    if not doc:
        raise HTTPException(404, "Track not found")
    await db.media_products.delete_one({"id": track_id})
    await _delete_file(doc.get("file_url", ""))
    await audit(user.id, "saga.track_deleted", target=track_id)
    return {"ok": True, "message": "Track deleted"}


# ── Images (scene artwork) ───────────────────────────────────────────────────

@router.post("/images")
async def upload_image(
    file: UploadFile = File(...),
    node_id: str = Form("general"),
    caption: str = Form(""),
    user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight")),
):
    if not file.content_type or not file.content_type.lower().startswith("image/"):
        raise HTTPException(400, "File must be an image")
    # Read with cap — see the audio upload handler above.
    contents = await file.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {MAX_UPLOAD_MB}MB)")

    file_url = await _store_file(
        file.filename or "scene.png", contents, file.content_type, {"kind": "saga_image"}
    )
    doc = {
        "id": "sagi_" + str(uuid.uuid4())[:8],
        "kind": "image",
        "node_id": node_id,
        "caption": caption.strip(),
        "filename": file.filename,
        "content_type": file.content_type,
        "file_url": file_url,
        "created_at": _now(),
    }
    await db.saga_assets.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "saga.image_uploaded", target=doc["id"], meta={"node_id": node_id})
    return {"ok": True, "image": doc, "message": f"Image added to scene '{node_id}'"}


@router.get("/images")
async def list_images(node_id: Optional[str] = None, user=Depends(_optional_current_user)):
    q = {"kind": "image"}
    if node_id:
        q["node_id"] = node_id
    docs = await db.saga_assets.find(q, {"_id": 0}).sort("created_at", 1).to_list(100)
    return {"images": docs}


@router.delete("/images/{image_id}")
async def delete_image(image_id: str, user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight"))):
    doc = await db.saga_assets.find_one({"id": image_id, "kind": "image"})
    if not doc:
        raise HTTPException(404, "Image not found")
    await db.saga_assets.delete_one({"id": image_id})
    await _delete_file(doc.get("file_url", ""))
    await audit(user.id, "saga.image_deleted", target=image_id)
    return {"ok": True, "message": "Image deleted"}


# ── Video renderer (ffmpeg Ken Burns + xfade + soundtrack) ───────────────────

def build_segment_command(image: str, seg_duration: float, output: str,
                          size: str = "1080x1920", fps: int = 30,
                          zoom_in: bool = True) -> List[str]:
    """One image → a zoompan clip. Pure (unit-testable) command builder."""
    frames = max(1, int(round(seg_duration * fps)))
    if zoom_in:
        zexpr = "min(zoom+0.0015,1.5)"
    else:
        zexpr = "max(zoom-0.0015,1.0)"
    vf = (
        f"scale={size}:force_original_aspect_ratio=increase,"
        f"crop={size},"
        f"zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={size}:fps={fps}"
    )
    return [
        "ffmpeg", "-y", "-loop", "1", "-t", f"{seg_duration:.3f}",
        "-i", image, "-vf", vf,
        "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-r", str(fps), "-frames:v", str(frames), output,
    ]


def build_concat_command_explicit(segments: List[str], output: str,
                                  seg_duration: float,
                                  soundtrack: Optional[str] = None,
                                  fade: float = 0.4) -> List[str]:
    """xfade segments of known equal duration seg_duration into one mp4."""
    n = len(segments)
    if n == 0:
        raise ValueError("no segments to concat")
    fade = max(0.1, min(fade, seg_duration / 2 - 0.05))

    if n == 1:
        cmd = ["ffmpeg", "-y", "-i", segments[0]]
        if soundtrack:
            cmd += ["-i", soundtrack, "-c:v", "copy", "-c:a", "aac", "-shortest"]
        else:
            cmd += ["-c", "copy"]
        cmd += [output]
        return cmd

    cmd = ["ffmpeg", "-y"]
    for seg in segments:
        cmd += ["-i", seg]
    if soundtrack:
        cmd += ["-i", soundtrack]

    parts: List[str] = []
    prev = "[0:v]"
    offset = seg_duration - fade
    for i in range(1, n):
        out = f"[v{i}]" if i < n - 1 else "[vout]"
        parts.append(f"{prev}[{i}:v]xfade=transition=fade:duration={fade:.3f}:offset={offset:.3f}{out}")
        prev = out
        offset += seg_duration - fade
    fc = ";".join(parts)
    cmd += ["-filter_complex", fc, "-map", "[vout]"]
    if soundtrack:
        cmd += ["-map", f"{n}:a", "-c:v", "libx264", "-preset", "veryfast",
                "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest"]
    else:
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p"]
    cmd += [output]
    return cmd


async def _render_video(asset_id: str, images: List[bytes], image_names: List[str],
                        soundtrack: Optional[bytes], seg_duration: float,
                        size: str = "1080x1920", fps: int = 30) -> None:
    """Background render: images + optional soundtrack → mp4 → GridFS."""
    tmp = Path(tempfile.mkdtemp(prefix="saga_render_"))
    try:
        img_paths: List[Path] = []
        for i, (data, name) in enumerate(zip(images, image_names)):
            p = tmp / f"img_{i}{Path(name).suffix or '.png'}"
            p.write_bytes(data)
            img_paths.append(p)

        snd_path: Optional[Path] = None
        if soundtrack:
            snd_path = tmp / "soundtrack.bin"
            snd_path.write_bytes(soundtrack)

        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg is not installed in this environment — cannot render video")

        seg_out: List[str] = []
        zoom_in = True
        for i, p in enumerate(img_paths):
            seg = tmp / f"seg_{i}.mp4"
            cmd = build_segment_command(str(p), seg_duration, str(seg), size=size, fps=fps, zoom_in=zoom_in)
            zoom_in = not zoom_in
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"segment {i} render failed: {stderr.decode(errors='replace')[-400:]}")
            seg_out.append(str(seg))

        out = tmp / "final.mp4"
        cmd = build_concat_command_explicit(
            seg_out, str(out), seg_duration, str(snd_path) if snd_path else None
        )
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"concat render failed: {stderr.decode(errors='replace')[-400:]}")

        contents = out.read_bytes()
        file_url = await _store_file(
            f"vonns_{asset_id}.mp4", contents, "video/mp4", {"kind": "saga_video"}
        )
        await db.saga_assets.update_one(
            {"id": asset_id},
            {"$set": {"status": "ready", "file_url": file_url, "updated_at": _now()}},
        )
        await audit(None, "saga.video_rendered", target=asset_id,
                    meta={"size": len(contents), "segments": len(images)})
        logger.info("saga: video %s rendered (%d bytes)", asset_id, len(contents))
    except Exception as exc:
        logger.exception("saga: video render failed for %s", asset_id)
        try:
            await db.saga_assets.update_one(
                {"id": asset_id},
                {"$set": {"status": "render_failed", "error": str(exc)[:500], "updated_at": _now()}},
            )
        except Exception:
            pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@router.post("/videos")
async def create_video(
    request: Request,
    title: str = Form("Vonns Saga Video"),
    node_id: str = Form("general"),
    duration_seconds: int = Form(15),
    soundtrack: Optional[UploadFile] = File(None),
    user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight")),
):
    """Create a short-form video from scene images + optional soundtrack.

    The frontend sends image_0..image_N (UploadFile list). FastAPI cannot
    declare a dynamic field count, so we read the raw multipart body here.
    """
    form = await request.form()
    images: List[bytes] = []
    image_names: List[str] = []
    idx = 0
    while True:
        part = form.get(f"image_{idx}")
        if part is None:
            break
        if isinstance(part, UploadFile):
            data = await part.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
            if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
                raise HTTPException(413, f"Scene image too large (max {MAX_UPLOAD_MB}MB)")
            if data:
                images.append(data)
                image_names.append(part.filename or f"scene_{idx}.png")
        idx += 1

    snd_data = None
    if soundtrack is not None:
        snd_data = await soundtrack.read(MAX_UPLOAD_MB * 1024 * 1024 + 1)
        if len(snd_data) > MAX_UPLOAD_MB * 1024 * 1024:
            raise HTTPException(413, f"Soundtrack too large (max {MAX_UPLOAD_MB}MB)")

    if not images:
        raise HTTPException(400, "Add at least one image (image_0, image_1, ...)")
    duration_seconds = max(5, min(int(duration_seconds), 60))
    seg_duration = duration_seconds / len(images)

    doc = {
        "id": "sagv_" + str(uuid.uuid4())[:8],
        "kind": "video",
        "title": title.strip(),
        "node_id": node_id,
        "duration_seconds": duration_seconds,
        "segments": len(images),
        "status": "rendering",
        "effects": ["ken_burns_pan", "ken_burns_zoom", "xfade_transitions"],
        "ai_assisted": True,  # disclosure: rendered automatically by the platform
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.saga_assets.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "saga.video_queued", target=doc["id"],
                meta={"title": title, "segments": len(images), "duration": duration_seconds})
    asyncio.create_task(_render_video(doc["id"], images, image_names, snd_data, seg_duration))
    return {"ok": True, "video": doc,
            "message": f"Video '{title}' queued — {duration_seconds}s, {len(images)} scenes, Ken Burns + xfade"}


@router.get("/videos")
async def list_videos(user=Depends(_optional_current_user)):
    docs = await db.saga_assets.find({"kind": "video"}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"videos": docs}


# ── Virtual concerts (members-only + paid) ───────────────────────────────────

@router.post("/concerts")
async def create_concert(
    title: str = Form("Vonn Live — Virtual Concert"),
    price_cents: int = Form(2000),
    video_file_url: str = Form(""),
    description: str = Form("Members-only virtual concert. AI-assisted production, real Vonn."),
    user=Depends(_require_rank("admin", "executive_admin", "support_staff", "oversight")),
):
    """Create a members-only paid concert product (type=video, tag vonn-live)."""
    if not video_file_url:
        raise HTTPException(400, "video_file_url is required (point at a rendered saga video)")
    pid = "sagc_" + str(uuid.uuid4())[:8]
    doc = {
        "id": pid,
        "owner_id": user.id,
        "owner_name": user.full_name,
        "title": title.strip(),
        "description": description.strip(),
        "price_cents": max(0, price_cents),
        "type": "video",
        "product_type": "video",
        "tags": ["vonn-live", "saga", "concert"],
        "file_url": video_file_url,
        "preview_seconds": None,
        "cover_url": "",
        "published": True,
        "min_tier": "member",  # members-only + paid
        "saga": {"kind": "concert"},
        "created_at": _now(),
        "updated_at": _now(),
    }
    await db.media_products.insert_one(doc)
    doc.pop("_id", None)
    await audit(user.id, "saga.concert_created", target=pid, meta={"price_cents": price_cents})
    return {"ok": True, "concert": doc}


@router.get("/concerts")
async def list_concerts(user=Depends(_optional_current_user)):
    docs = await db.media_products.find(
        {"published": True, "tags": "vonn-live"}, {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    return {"concerts": docs}


@router.post("/concerts/{concert_id}/checkout")
async def checkout_concert(concert_id: str, user=Depends(_dep_current_user)):
    """Members-only + paid concert checkout (tier gate enforced server-side)."""
    doc = await db.media_products.find_one({"id": concert_id, "tags": "vonn-live"}, {"_id": 0})
    if not doc or not doc.get("published"):
        raise HTTPException(404, "Concert not found")

    from roles import TIER_RANK
    tier = getattr(user, "feature_tier", "free") or "free"
    min_tier = doc.get("min_tier", "member")
    if TIER_RANK.get(tier, 0) < TIER_RANK.get(min_tier, 1):
        raise HTTPException(403, f"This virtual concert is members-only (requires {min_tier} tier)")

    existing = await db.media_purchases.find_one({"buyer_id": user.id, "product_id": concert_id})
    if existing:
        return {"already_purchased": True, "file_url": doc.get("file_url", "")}

    if doc.get("price_cents", 0) > 0:
        from ai.publishing import _publish_lemon_squeezy, _publish_gumroad
        amount = doc["price_cents"]
        ls_result = await _publish_lemon_squeezy(
            name=doc.get("title", "Virtual Concert"), description=doc.get("description", "")[:500],
            price_cents=amount, persona="platform",
        )
        if ls_result:
            await audit(user.id, "saga.concert_checkout_created", target=concert_id,
                        meta={"provider": "lemon_squeezy"})
            return {"url": ls_result["url"]}
        gr_result = await _publish_gumroad(doc.get("title", "Virtual Concert"), doc.get("description", ""), amount)
        if gr_result:
            await audit(user.id, "saga.concert_checkout_created", target=concert_id,
                        meta={"provider": "gumroad"})
            return {"url": gr_result["url"]}
        raise HTTPException(500, "Payment processing failed. Payment providers are configured but the request could not be completed.")

    import uuid as _uuid
    purchase = {
        "id": str(_uuid.uuid4())[:8],
        "buyer_id": user.id,
        "product_id": concert_id,
        "title": doc.get("title", ""),
        "file_url": doc.get("file_url", ""),
        "purchased_at": _now(),
        "price_cents": 0,
    }
    await db.media_purchases.insert_one(purchase)
    return purchase
