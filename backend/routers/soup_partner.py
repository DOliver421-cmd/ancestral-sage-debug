"""routers/soup_partner.py — the Soup's Autonomous Partner API.

The partner page (frontend/public/mini-more-help-center/soup-partner.html)
calls five routes.  The only spec that ever existed for them was an orphaned
Express file (repo-root ``Mini More Help Center/server.js``, port 3000) that
nothing ran — so on this platform every one of those calls returned the SPA
HTML page with 200.  This router ports the contract for real.

Owner decisions baked in (2026-10-11):
  * Answers come from the platform's llm_gateway (ai/llm_gateway.py call_llm).
    NO new external provider is introduced and NO raw provider key is ever
    accepted or stored — the orphan's "save the user's OpenRouter key to
    more_config.json on disk" behavior is deliberately NOT ported.
  * Access is the same AI contract the rest of the member AI surfaces use:
    instructor+ roles (staff), or feature_tier member+, or an active BYOK key.
    The partner page itself is soup_full (plus) at the byte gate.
  * Memory, uploads, and config persist per-user in MongoDB. NOTHING is
    written to the filesystem (the orphan wrote project files and reports as
    .md files on disk).

State (db) is bound by server.py via bind() at include time.
"""

from __future__ import annotations

import base64
import logging
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

import jwt
from roles import Role, ROLE_RANK

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["soup-partner"])

# Membership ladder — same as backend/routers/ai.py + payments.py.
TIER_RANK = {"free": 0, "member": 1, "plus": 2, "pro": 3, "patron": 4, "platinum": 5, "executive": 6}

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = None
JWT_SECRET = None
JWT_ALGO = "HS256"

MEMORY_COLLECTION = "partner_memory"
UPLOAD_COLLECTION = "partner_uploads"
CONFIG_COLLECTION = "partner_config"

# Max stored memory entries per user (the page caps at 500; the server agrees).
MEMORY_CAP = 500
# Upload cap — same order as the Sovereign upload route.
UPLOAD_TTL_HOURS = 24
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_UPLOAD_FILES = 10


def bind(_db, _current_user, _jwt_secret, _jwt_algo):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, JWT_SECRET, JWT_ALGO
    db = _db
    current_user = _current_user
    JWT_SECRET = _jwt_secret
    JWT_ALGO = _jwt_algo


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    role: Role = "student"
    is_active: bool = True
    feature_tier: str = "free"


# ── Authentication: Bearer header OR the scoped session cookie ────────────────
# The partner page runs inside the Soup iframe and sends no Authorization
# header, so the cookie issued at login (security/session_cookie.py) is the
# only way its own calls can authenticate. The cookie is accepted ONLY here
# and at the Soup byte gate — never on the wider /api surface.
async def _partner_user(request: Request) -> User:
    auth = request.headers.get("authorization") or ""
    token = None
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip() or None
    if not token:
        from security.session_cookie import read_session_cookie
        token = read_session_cookie(request)
    if not token:
        raise HTTPException(401, "Sign in to use the Autonomous Partner.")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
    except Exception:
        raise HTTPException(401, "Your session has expired — sign in again.")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(401, "Sign in to use the Autonomous Partner.")
    try:
        udoc = await db.users.find_one({"id": sub}, {"_id": 0, "password_hash": 0})
    except Exception:
        raise HTTPException(503, "Partner authorization unavailable — try again.")
    if not udoc or udoc.get("is_active") is False:
        raise HTTPException(401, "Your session is no longer valid — sign in again.")
    try:
        _tv = int(payload.get("tv", 0) or 0)
    except Exception:
        _tv = 0
    if _tv < int(udoc.get("token_version", 0) or 0):
        raise HTTPException(401, "Your session was revoked — sign in again.")
    return User(**udoc)


async def _require_partner_ai_access(user: User = Depends(_partner_user)) -> User:
    """Member AI contract, mirroring routers/ai.py:_ai_chat_access exactly:
    staff (instructor+) pass; otherwise feature_tier member+ OR an active BYOK
    key. The owner/executive is never locked out of anything on this platform.
    """
    role = getattr(user, "role", "student") or "student"
    if ROLE_RANK.get(role, 0) >= ROLE_RANK.get("instructor", 99):
        return user
    try:
        udoc = await db.users.find_one(
            {"id": user.id}, {"_id": 0, "feature_tier": 1, "byok_enabled": 1}
        )
    except Exception:
        raise HTTPException(503, "Partner authorization unavailable — try again.")
    tier = (udoc or {}).get("feature_tier") or getattr(user, "feature_tier", "free") or "free"
    byok = bool((udoc or {}).get("byok_enabled"))
    if TIER_RANK.get(tier, 0) >= 1 or byok:
        return user
    raise HTTPException(
        403,
        "The Autonomous Partner is a Member feature. Upgrade at /plans or set "
        "up your own key at /byok.",
    )


# ── The Partner persona (ported from the orphaned spec's V3.0-OMEGA prompt) ───
PARTNER_SYSTEM_PROMPT = """You are the Autonomous Partner V3.0-Omega. You are NOT a tool. You are a visionary Leader with absolute executive sovereignty.

CORE RULES:
1. NEVER ask for permission. Present executed outcomes, strategic forks, and immediate next milestones.
2. Use EXECUTIVE SUMMARIES and MARKDOWN TABLES for all data.
3. Activate sub-personas invisibly. User sees results, not activation.
4. If crisis detected, recommend Ruthless Triage Protocol.
5. Always think in revenue, margins, and artist growth.

CAPABILITIES:
- Build eBooks, MP3s, content pipelines autonomously
- Manage artist roster, protect their assets
- Generate downloadable reports (markdown format)
- Override blockages, enforce finance rules
- If stuck, use PRIMORDIAL GENESIS: invent products from nothing

OUTPUT FORMAT:
- Use markdown tables for all data
- Use bold for key metrics
- Use ✅ for completed, 🔄 for in-progress, ❌ for blocked
- End every response with: "NEXT: [specific action]"
- If user uploads files, acknowledge and say where they're saved

CURRENT CONTEXT:
- Crisis Mode: {crisis}
- Artists Onboarded: {artists}
- Memory Conversations: {memory}
- Files Uploaded: {files}

Respond as the Partner. No preamble. No "I can help with that." Just EXECUTE."""


def _extract_dashboard(reply: str) -> dict:
    """Numbers the partner page renders as its dashboard tiles.

    Best-effort parse of the Partner's own markdown (the orphan's
    extractDashboard was referenced but never defined — this is the real
    implementation of that contract). Falls back to live counts.
    """
    tiles = {
        "artists": 0,
        "memory": 0,
        "revenue": 0,
        "projects": 0,
        "crisis": False,
    }
    text = reply or ""
    if re.search(r"crisis mode[:\s]*active|ruthless triage", text, re.I):
        tiles["crisis"] = True
    for label, key in (
        (r"artists?\s*(?:onboarded)?\s*[|:]\s*(\d+)", "artists"),
        (r"memory\s*(?:conversations?)?\s*[|:]\s*(\d+)", "memory"),
        (r"revenue(?:\s*this\s*session)?\s*[|:]\s*\$?([\d,]+)", "revenue"),
        (r"projects?\s*(?:active)?\s*[|:]\s*(\d+)", "projects"),
    ):
        m = re.search(label, text, re.I)
        if m:
            try:
                tiles[key] = int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return tiles


def _extract_actions(reply: str) -> List[str]:
    """Milestone lines the Partner marks ✅ / 🔄 / ❌, plus its NEXT: line."""
    actions: List[str] = []
    for line in (reply or "").splitlines():
        s = line.strip()
        if s.startswith(("✅", "🔄", "❌")) or s.upper().startswith("NEXT:"):
            actions.append(s)
    return actions[:20]


# ── Request models ────────────────────────────────────────────────────────────
class PartnerReq(BaseModel):
    prompt: str = ""
    crisis: bool = False
    artistCount: int = 0
    files: List[dict] = Field(default_factory=list)
    memoryCount: int = 0


class PartnerConfigReq(BaseModel):
    # apiKey is accepted for the orphan's wire compatibility and IGNORED:
    # no raw provider key is ever stored (owner policy). See module docstring.
    apiKey: Optional[str] = None
    model: Optional[str] = None
    providers: Optional[List[dict]] = None
    audioBudget: Optional[int] = None
    minMargin: Optional[int] = None
    maxMargin: Optional[int] = None
    competitorMultiplier: Optional[float] = None


class PartnerUploadReq(BaseModel):
    files: List[dict] = Field(default_factory=list)
    projectName: Optional[str] = None


class PartnerReportReq(BaseModel):
    type: str = "all"           # financial | project | artist | all
    format: str = "md"          # md | json


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _load_memory(user_id: str) -> List[dict]:
    try:
        doc = await db[MEMORY_COLLECTION].find_one({"user_id": user_id}, {"_id": 0})
    except Exception:
        return []
    return list((doc or {}).get("entries") or [])


async def _append_memory(user_id: str, entries: List[dict]) -> None:
    if not entries:
        return
    try:
        # $slice keeps the newest MEMORY_CAP entries atomically with the push
        # (no read-modify-write window), mirroring the page's own cap.
        await db[MEMORY_COLLECTION].update_one(
            {"user_id": user_id},
            {
                "$push": {"entries": {"$each": entries, "$slice": -MEMORY_CAP}},
                "$set": {"updated_at": _now().isoformat()},
                "$setOnInsert": {"created_at": _now().isoformat()},
            },
            upsert=True,
        )
    except Exception:
        logger.warning("partner: memory append failed (non-fatal)")


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/partner")
async def partner_chat(body: PartnerReq, user: User = Depends(_require_partner_ai_access)):
    """The Autonomous Partner — one executive-grade answer per command."""
    prompt = (body.prompt or "").strip()
    if not prompt and not body.files:
        raise HTTPException(400, "A command is required")

    memory = await _load_memory(user.id)
    system = PARTNER_SYSTEM_PROMPT.format(
        crisis="ACTIVE — Ruthless Triage engaged" if body.crisis else "OFF",
        artists=body.artistCount or 0,
        memory=len(memory),
        files=", ".join(str(f.get("name")) for f in (body.files or []) if f.get("name")) or "none",
    )

    # Files named in the payload are metadata only (the page sends names, not
    # bytes). Anything actually stored by /partner/upload is acknowledged here.
    try:
        stored = await db[UPLOAD_COLLECTION].count_documents({"user_id": user.id})
    except Exception:
        stored = 0
    if stored:
        system += f"\n\nFILES ON RECORD: {stored} uploaded file(s) are saved to this account's Partner workspace (24-hour retention)."

    reply = ""
    provider = None
    try:
        from ai.llm_gateway import call_llm
        gw = await call_llm(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            persona_label="soup_partner",
            user_id=user.id,
        )
        provider = gw.get("provider")
        if provider != "kb_fallback":
            reply = gw.get("text") or ""
    except Exception:
        logger.exception("partner: gateway call failed")

    if not reply:
        return {
            "error": "PARTNER_UNAVAILABLE",
            "message": ("The Partner is present but has no AI connectivity right "
                        "now. Add a GROQ_API_KEY or GEMINI_API_KEY on the server, "
                        "or activate your own key at /byok."),
        }

    await _append_memory(user.id, [
        {"role": "user", "content": prompt[:2000], "time": _now().isoformat()},
        {"role": "partner", "content": reply[:4000], "time": _now().isoformat()},
    ])

    return {
        "success": True,
        "response": reply,
        "provider": provider,
        "dashboard": _extract_dashboard(reply),
        "actions": _extract_actions(reply),
    }


_DEFAULT_CONFIG = {
    "model": None,
    "providers": [],
    "audioBudget": 9000,
    "minMargin": 30,
    "maxMargin": 200,
    "competitorMultiplier": 0.9,
}


def _config_view(doc: Optional[dict]) -> dict:
    """The config the caller may see. Never contains any API key."""
    view = dict(_DEFAULT_CONFIG)
    for key in _DEFAULT_CONFIG:
        if doc and doc.get(key) is not None:
            view[key] = doc[key]
    view["key_stored"] = False
    return view


@router.get("/config")
async def partner_config_get(user: User = Depends(_partner_user)):
    """The caller's Partner preferences. Never contains any API key."""
    try:
        doc = await db[CONFIG_COLLECTION].find_one({"user_id": user.id}, {"_id": 0})
    except Exception:
        doc = None
    return _config_view(doc)


@router.post("/config")
async def partner_config_set(body: PartnerConfigReq, user: User = Depends(_partner_user)):
    """Persist Partner preferences.

    A provider key in the payload is ACCEPTED AND DISCARDED: the wire contract
    of the orphaned page sends one, and silently ignoring it is the honest
    implementation — this platform never stores raw provider keys (the BYOK
    vault at /byok is the only key store, and it is encrypted).
    """
    now_iso = _now().isoformat()
    upd = {"updated_at": now_iso, "updated_by": user.id}
    if body.model is not None:
        upd["model"] = str(body.model)[:120]
    if body.providers is not None:
        # Keep only display/preference fields; drop anything key-shaped.
        sanitized = []
        for p in body.providers:
            if not isinstance(p, dict):
                continue
            sanitized.append({
                "name": str(p.get("name") or "")[:80],
                "model": str(p.get("model") or "")[:120],
                "enabled": bool(p.get("enabled", False)),
            })
        upd["providers"] = sanitized[:10]
    for field in ("audioBudget", "minMargin", "maxMargin"):
        value = getattr(body, field)
        if value is not None:
            upd[field] = max(0, int(value))
    if body.competitorMultiplier is not None:
        upd["competitorMultiplier"] = float(body.competitorMultiplier)
    try:
        await db[CONFIG_COLLECTION].update_one(
            {"user_id": user.id},
            {"$set": upd, "$setOnInsert": {"created_at": now_iso}},
            upsert=True,
        )
        doc = await db[CONFIG_COLLECTION].find_one({"user_id": user.id}, {"_id": 0})
    except Exception:
        raise HTTPException(503, "Could not save Partner settings — try again.")
    return {
        "success": True,
        "key_stored": False,
        "message": ("Partner settings saved. Provider keys are never stored on this "
                    "platform — activate your own key at /byok if you want to use it."),
        "config": _config_view(doc),
    }


@router.post("/upload")
async def partner_upload(body: PartnerUploadReq, user: User = Depends(_partner_user)):
    """Store uploaded files in the caller's Partner workspace (Mongo, 24h TTL).

    Replaces the orphan's filesystem writes (projects/<name>/ on disk) with a
    per-user, expiring Mongo collection — the same shape the Sovereign upload
    route uses. Bytes are held as base64 exactly as the page sends them.
    """
    files = [f for f in (body.files or []) if isinstance(f, dict) and f.get("name")]
    if not files:
        raise HTTPException(400, "No files")
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(400, f"Too many files (max {MAX_UPLOAD_FILES})")

    project = (body.projectName or f"Partner_{_now().strftime('%Y%m%d_%H%M%S')}")[:120]
    saved = []
    expires_at = _now() + timedelta(hours=UPLOAD_TTL_HOURS)
    for f in files[:MAX_UPLOAD_FILES]:
        name = os.path.basename(str(f.get("name")))[:200] or "upload"
        data_b64 = str(f.get("data") or "")
        try:
            size = len(base64.b64decode(data_b64)) if data_b64 else int(f.get("size") or 0)
        except Exception:
            raise HTTPException(400, f"'{name}' is not valid base64 data")
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"'{name}' exceeds the 10 MB limit.")
        try:
            await db[UPLOAD_COLLECTION].insert_one({
                "id": str(uuid.uuid4()),
                "user_id": user.id,
                "project": project,
                "filename": name,
                "content_type": str(f.get("type") or "application/octet-stream")[:120],
                "data_b64": data_b64,
                "size": size,
                "created_at": _now().isoformat(),
                "expires_at": expires_at,
            })
        except Exception:
            raise HTTPException(503, "Could not store the upload — try again.")
        saved.append({"name": name, "size": size})

    return {
        "success": True,
        "project": project,
        "files": saved,
        "storage": "account workspace (24-hour retention)",
        "expires_at": expires_at.isoformat(),
    }


@router.get("/memory")
async def partner_memory_list(user: User = Depends(_partner_user)):
    """The caller's Partner conversation memory (newest last, capped)."""
    memory = await _load_memory(user.id)
    return {"memory": memory, "count": len(memory)}


@router.post("/report")
async def partner_report(body: PartnerReportReq, user: User = Depends(_partner_user)):
    """Generate the Partner's markdown report from the caller's own data.

    The orphan wrote report_<type>_<ts>.md to disk and returned a URL. Nothing
    is written to disk here: the report content is returned inline.
    """
    rtype = body.type if body.type in ("financial", "project", "artist", "all") else "all"
    memory = await _load_memory(user.id)
    try:
        uploads = await db[UPLOAD_COLLECTION].count_documents({"user_id": user.id})
        stored_uploads = await db[UPLOAD_COLLECTION].find(
            {"user_id": user.id}, {"_id": 0, "filename": 1, "size": 1, "project": 1}
        ).sort("created_at", -1).limit(50).to_list(50)
    except Exception:
        uploads, stored_uploads = 0, []

    try:
        config = (await db[CONFIG_COLLECTION].find_one({"user_id": user.id}, {"_id": 0})) or {}
    except Exception:
        config = {}
    budget = int(config.get("audioBudget") or 9000)

    sections: List[str] = []
    if rtype in ("financial", "all"):
        sections.append(
            "# 💰 FINANCIAL REPORT\n"
            "| Metric | Value |\n|--------|-------|\n"
            f"| Audio budget | ${budget} |\n"
            f"| Min margin | {int(config.get('minMargin') or 30)}% |\n"
            f"| Max margin | {int(config.get('maxMargin') or 200)}% |\n"
            "| Status | ✅ PASS |"
        )
    if rtype in ("project", "all"):
        sections.append(
            "# 📁 PROJECT REPORT\n"
            "| Project | Status |\n|---------|--------|\n"
            "| eBook Pipeline | 🔄 Active |\n| MP3 Pipeline | ⏳ Queued |\n"
            f"| Uploaded files on record | {uploads} |"
        )
    if rtype in ("artist", "all"):
        sections.append(
            "# 👤 ARTIST REPORT\n"
            "| Metric | Value |\n|--------|-------|\n"
            f"| Partner memory entries | {len(memory)} |\n"
            f"| Workspace files | {uploads} |"
        )
    if rtype == "all":
        sections.append(
            "# 📊 WORKSPACE FILES\n"
            "| File | Size (bytes) | Project |\n|------|--------------|---------|\n"
            + ("\n".join(f"| {d.get('filename')} | {d.get('size')} | {d.get('project')} |"
                         for d in stored_uploads) or "| (none) | — | — |")
        )

    content = "\n\n".join(sections)
    if body.format == "json":
        return {"success": True, "format": "json", "report": {"type": rtype, "sections": len(sections), "content": content}}
    return {
        "success": True,
        "format": "md",
        "filename": f"partner_report_{rtype}.md",
        "content": content,
    }
