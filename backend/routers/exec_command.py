"""
exec_command.py — Executive Command Center backend
===================================================
Two endpoints that power the integrated exec surface:

  GET /api/exec/system   — RESTORED aggregate platform overview.
    The exec dashboard (ExecSystem.jsx) and the M.O.R.E. admin surface both
    call this endpoint, but it was lost during the router extraction refactor,
    leaving the exec dashboard showing "System endpoint unavailable". Restored
    here with the exact payload the frontends expect: role_counts, version,
    env key-presence flags, audit_log_total, collections, plus the full LLM
    gateway status (providers + hourly budget) for the Command Center's
    AI & Providers tab.

  GET /api/exec/manuals  — every operations manual & report in one call.
    Serves the repo's docs/*.md and backend/handbooks/*.md so reports and
    manuals are reachable from the exec interface without hunting through
    GitHub or copy/pasting between screens.
"""

import logging
import os
import pathlib
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import File, UploadFile
from fastapi.responses import Response
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")

router = APIRouter(tags=["exec_command"])# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = current_user = audit = None



def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db = _db
    current_user = _current_user
    audit = _audit


async def _dep_current_user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)


def _require_rank(*roles):
    needed_rank = min(ROLE_RANK[r] for r in roles)

    def dep(user: BaseModel = Depends(_dep_current_user)):
        if ROLE_RANK.get(getattr(user, "role", ""), 0) < needed_rank:
            raise HTTPException(403, "Insufficient permissions to access this resource.")
        return user

    return dep


# ─────────────────────────────────────────────────────────────────────────────
# /exec/system — aggregate platform overview
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/exec/system")
async def exec_system_overview(user: BaseModel = Depends(_require_rank("executive_admin"))):
    role_counts = {}
    try:
        cursor = db.users.aggregate([{"$group": {"_id": "$role", "n": {"$sum": 1}}}])
        async for d in cursor:
            role_counts[d.get("_id") or "unknown"] = d.get("n", 0)
    except Exception as e:
        logger.warning("exec/system: role count failed — %s", e)

    audit_log_total = 0
    try:
        audit_log_total = await db.audit_logs.count_documents({})
    except Exception:
        pass

    collections = []
    try:
        collections = await db.list_collection_names()
    except Exception:
        pass

    try:
        from server import APP_VERSION as _version, _DB_SOURCE as _db_source
    except Exception:
        _version = os.environ.get("APP_VERSION", "4.0.1")
        _db_source = os.environ.get("DB_SOURCE", "unknown")

    gateway = {}
    try:
        from ai.llm_gateway import gateway_status as _gateway_status
        gateway = _gateway_status()
    except Exception as e:
        logger.warning("exec/system: gateway status failed — %s", e)

    _prov = gateway.get("providers") or {}
    ls_ready = bool(os.environ.get("LEMON_SQUEEZY_API_KEY", "") and os.environ.get("LEMON_SQUEEZY_STORE_ID", ""))
    gr_ready = bool(os.environ.get("GUMROAD_API_KEY", ""))

    env_flags = {
        "db_name": os.environ.get("DB_NAME", "ancestral_sage"),
        "db_source": _db_source,
        "jwt_expire_hours": int(os.environ.get("JWT_EXPIRE_HOURS", "168")),
        "version": _version,
        "groq_key": bool(_prov.get("groq", {}).get("available")),
        "cerebras_key": bool(_prov.get("cerebras", {}).get("available")),
        "gemini_key": bool(_prov.get("gemini", {}).get("available")),
        "payments_enabled": bool(ls_ready or gr_ready),
        "lemon_squeezy": ls_ready,
        "gumroad": gr_ready,
        "active_free_providers": gateway.get("active_free_providers", 0),
        "active_providers": gateway.get("active_providers", gateway.get("active_free_providers", 0)),
    }

    return {
        "version": _version,
        "role_counts": role_counts,
        "audit_log_total": audit_log_total,
        "collections": collections,
        "env": env_flags,
        "gateway": gateway,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# /exec/manuals — operations manuals & reports
# ─────────────────────────────────────────────────────────────────────────────
_MANUAL_DIRS = None


def _manual_dirs():
    global _MANUAL_DIRS
    if _MANUAL_DIRS is not None:
        return _MANUAL_DIRS
    here = pathlib.Path(__file__).resolve()
    repo = here.parents[2]  # backend/routers/exec_command.py → repo root
    dirs = {
        "docs": [repo / "docs", repo.parent / "docs"],
        "handbook": [repo / "backend" / "handbooks", here.parents[1] / "handbooks"],
    }
    found = {}
    for group, candidates in dirs.items():
        for c in candidates:
            if c.is_dir():
                found[group] = c
                break
    _MANUAL_DIRS = found
    return found


@router.get("/exec/manuals")
async def exec_manuals(user: BaseModel = Depends(_require_rank("executive_admin"))):
    dirs = _manual_dirs()
    out = []
    for group, d in dirs.items():
        try:
            for f in sorted(d.glob("*.md")):
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                out.append({
                    "slug": f.stem,
                    "title": f.stem.replace("_", " ").title(),
                    "group": group,
                    "content": content[:120000],
                })
        except Exception as e:
            logger.warning("exec/manuals: reading %s failed — %s", group, e)
    out.sort(key=lambda m: (m["group"] != "docs", m["title"]))
    return {"manuals": out}


# ─────────────────────────────────────────────────────────────────────────────
# /exec/assets — site asset library over MongoDB GridFS (executive-managed)
# ---------------------------------------------------------------------------
# The owner uploads visual assets (hero imagery, gallery photos, course art)
# through the exec interface and assigns each a display role. The public
# landing page reads assigned roles via GET /api/site-assets (below) — no
# rebuilds, no code changes per image. Upload reuses the same GridFS bucket as
# POST /api/media/upload so both surfaces see one library.
# ─────────────────────────────────────────────────────────────────────────────

MAX_ASSET_MB = 50
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}


@router.get("/exec/assets")
async def exec_list_assets(user: BaseModel = Depends(_require_rank("executive_admin"))):
    """List every uploaded asset (GridFS files + display-role assignments)."""
    fs_files = db.fs.files
    assignments = {a["file_id"]: a for a in await db.site_assets.find({}, {"_id": 0}).to_list(500)}
    cursor = fs_files.find({}, {"filename": 1, "contentType": 1, "length": 1, "uploadDate": 1, "metadata": 1})
    assets = []
    async for f in cursor:
        fid = str(f["_id"])
        a = assignments.get(fid, {})
        assets.append({
            "file_id": fid,
            "filename": f.get("filename", "upload"),
            "content_type": f.get("contentType", "application/octet-stream"),
            "size": f.get("length", 0),
            "uploaded_at": f.get("uploadDate").isoformat() if f.get("uploadDate") else None,
            "file_url": f"/api/media/file/{fid}",
            "role": a.get("role"),
            "label": a.get("label"),
        })
    assets.sort(key=lambda x: x["uploaded_at"] or "", reverse=True)
    return {"assets": assets}


@router.post("/exec/assets")
async def exec_upload_asset(
    file: UploadFile = File(...),
    role: Optional[str] = None,
    label: Optional[str] = None,
    user: BaseModel = Depends(_require_rank("executive_admin")),
):
    """Upload an image asset directly from the exec interface.

    Images only (jpg/png/webp/gif/svg), 50MB cap. Optionally assign the
    display role in the same call; the response's file_url is immediately
    usable anywhere on the site.
    """
    ctype = (file.content_type or "").lower().split(";")[0].strip()
    if ctype not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(415, f"Only image uploads are allowed here ({', '.join(sorted(_ALLOWED_IMAGE_TYPES))}); got {ctype or 'unknown'}")
    contents = await file.read(MAX_ASSET_MB * 1024 * 1024 + 1)
    if len(contents) > MAX_ASSET_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (max {MAX_ASSET_MB}MB)")
    if not contents:
        raise HTTPException(400, "Empty file")
    bucket = AsyncIOMotorGridFSBucket(db)
    gfs_id = await bucket.upload_from_stream(
        file.filename or "asset",
        contents,
        metadata={"uploader": user.id, "content_type": ctype, "source": "exec_assets"},
    )
    fid = str(gfs_id)
    if role:
        await db.site_assets.update_one(
            {"role": role},
            {"$set": {"role": role, "file_id": fid, "label": label or "", "assigned_at": datetime.now(timezone.utc).isoformat(), "assigned_by": user.id}},
            upsert=True,
        )
    await audit(user.id, "exec_asset_uploaded", target=fid, meta={"filename": file.filename, "role": role, "size": len(contents)})
    return {"file_id": fid, "file_url": f"/api/media/file/{fid}", "filename": file.filename, "role": role}


@router.put("/exec/assets/{file_id}/assign")
async def exec_assign_asset(file_id: str, body: dict, user: BaseModel = Depends(_require_rank("executive_admin"))):
    """Assign (or clear, with role=null) an asset's display role.

    Known roles: hero, landing_gallery, course:<slug>. Assigning a role moves
    it off any previous holder — one image per role, the last assignment wins.
    """
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    if not await db.fs.files.find_one({"_id": oid}, {"_id": 1}):
        raise HTTPException(404, "Asset not found")
    role = body.get("role")
    label = body.get("label", "")
    if role:
        await db.site_assets.update_one(
            {"file_id": file_id}, {"$unset": {"role": ""}}
        )  # clear any prior assignment of THIS file first
        await db.site_assets.update_one(
            {"role": role},
            {"$set": {"role": role, "file_id": file_id, "label": label, "assigned_at": datetime.now(timezone.utc).isoformat(), "assigned_by": user.id}},
            upsert=True,
        )
    else:
        await db.site_assets.delete_many({"file_id": file_id})
    await audit(user.id, "exec_asset_assigned", target=file_id, meta={"role": role, "label": label})
    return {"ok": True, "file_id": file_id, "role": role}


@router.delete("/exec/assets/{file_id}")
async def exec_delete_asset(file_id: str, user: BaseModel = Depends(_require_rank("executive_admin"))):
    """Delete an uploaded asset from GridFS and drop any role assignment."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(400, "Invalid file ID")
    bucket = AsyncIOMotorGridFSBucket(db)
    try:
        await bucket.delete(oid)
    except Exception:
        raise HTTPException(404, "Asset not found")
    await db.site_assets.delete_many({"file_id": file_id})
    await audit(user.id, "exec_asset_deleted", target=file_id)
    return {"ok": True}


@router.get("/site-assets")
async def public_site_assets():
    """Public read of assigned site assets for the landing page.

    Returns role -> {file_url, label}. No auth: the imagery is public site
    content by definition. Cached briefly at the browser (5 min) so page loads
    do not re-fetch the mapping on every navigation.
    """
    import json
    docs = await db.site_assets.find({}, {"_id": 0, "role": 1, "file_id": 1, "label": 1}).to_list(100)
    out = {}
    for d in docs:
        if d.get("role"):
            out[d["role"]] = {"file_url": f"/api/media/file/{d['file_id']}", "label": d.get("label", "")}
    return Response(
        content=json.dumps({"assets": out}),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=300"},
    )
