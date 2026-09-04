"""
Studio + Arcade + Compliance router — Creator's Sanctuary, Virtual Arcade,
and safety-compliance training.

Extracted verbatim from backend/server.py (monolith refactor, slice 5).
Shared state (db, current_user, award_xp, award_credentials) is bound by
server.py via bind() at include time — no circular imports.
"""
import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["studio", "arcade", "compliance"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = award_xp = award_credentials = audit = None


def bind(_db, _current_user, _award_xp, _award_credentials, _audit=None):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, award_xp, award_credentials, audit
    db = _db
    current_user = _current_user
    award_xp = _award_xp
    award_credentials = _award_credentials
    audit = _audit


# Mirrors server.py's role hierarchy (not used by these routes, kept for parity).
from routers.roles import ROLE_RANK, Role


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


# ═════════════════════════════════════════════════════════════════════════════
# Short-form video studio
# ═════════════════════════════════════════════════════════════════════════════

# Defined before the video routes so FastAPI can capture the dependency while
# the module is imported. The typed compatibility helper below remains for the
# legacy studio routes.
async def _dep_current_user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)


VIDEO_TIERS = {"pro", "patron", "platinum", "executive"}
VIDEO_STAFF_ROLES = {"instructor", "support_staff", "oversight", "admin", "executive_admin"}
VIDEO_RATIOS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "16:9": (1920, 1080)}


def _video_access(user: User):
    if user.role not in VIDEO_STAFF_ROLES and str(getattr(user, "feature_tier", "free")) not in VIDEO_TIERS:
        raise HTTPException(403, "Pro membership or staff access is required for the Video Studio.")


def _clean_video_doc(doc: dict) -> dict:
    clean = {k: v for k, v in doc.items() if k != "_id"}
    return clean


async def _with_video_scenes(doc: dict) -> dict:
    scenes = await db.video_scenes.find(
        {"project_id": doc["id"], "user_id": doc["user_id"]},
        {"_id": 0},
    ).sort("scene_order", 1).to_list(100)
    result = _clean_video_doc(doc)
    result["scenes"] = scenes
    return result


class VideoProjectBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    idea: str = Field(default="", max_length=5000)
    description: str = Field(default="", max_length=5000)
    intended_audience: str = Field(default="", max_length=500)
    desired_length: int = Field(default=30, ge=1, le=180)
    purpose: str = Field(default="", max_length=500)
    call_to_action: str = Field(default="", max_length=1000)
    aspect_ratio: Literal["9:16", "1:1", "16:9"] = "9:16"


class VideoProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    idea: Optional[str] = Field(default=None, max_length=5000)
    description: Optional[str] = Field(default=None, max_length=5000)
    intended_audience: Optional[str] = Field(default=None, max_length=500)
    desired_length: Optional[int] = Field(default=None, ge=1, le=180)
    purpose: Optional[str] = Field(default=None, max_length=500)
    call_to_action: Optional[str] = Field(default=None, max_length=1000)
    aspect_ratio: Optional[Literal["9:16", "1:1", "16:9"]] = None


class VideoSceneBody(BaseModel):
    media_url: Optional[str] = Field(default=None, max_length=2000)
    text: str = Field(default="", max_length=5000)
    duration: int = Field(default=5, ge=1, le=60)
    position: int = Field(default=0, ge=0, le=8)


@router.get("/video/projects")
async def list_video_projects(user: User = Depends(_dep_current_user)):
    _video_access(user)
    docs = await db.video_projects.find({"user_id": user.id}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    return [await _with_video_scenes(d) for d in docs]


@router.post("/video/projects")
async def create_video_project(body: VideoProjectBody, user: User = Depends(_dep_current_user)):
    _video_access(user)
    now = datetime.now(timezone.utc).isoformat()
    doc = {"id": "vp_" + uuid.uuid4().hex, "user_id": user.id, **body.model_dump(),
           "status": "Draft", "scenes": [], "final_video_url": None, "thumbnail_url": None,
           "created_at": now, "updated_at": now}
    await db.video_projects.insert_one(doc)
    if audit:
        await audit(user.id, "video_project_created", target=doc["id"], meta={"title": doc["title"]})
    return _clean_video_doc(doc)


async def _owned_video_project(project_id: str, user: User) -> dict:
    _video_access(user)
    doc = await db.video_projects.find_one({"id": project_id, "user_id": user.id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Video project not found")
    return doc


@router.get("/video/projects/{project_id}")
async def get_video_project(project_id: str, user: User = Depends(_dep_current_user)):
    return await _with_video_scenes(await _owned_video_project(project_id, user))


@router.patch("/video/projects/{project_id}")
async def update_video_project(project_id: str, body: VideoProjectUpdate, user: User = Depends(_dep_current_user)):
    doc = await _owned_video_project(project_id, user)
    updates = {k: v for k, v in body.model_dump(exclude_none=True).items() if v is not None}
    if not updates:
        return _clean_video_doc(doc)
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.video_projects.update_one({"id": project_id, "user_id": user.id}, {"$set": updates})
    doc.update(updates)
    return _clean_video_doc(doc)


@router.delete("/video/projects/{project_id}")
async def delete_video_project(project_id: str, user: User = Depends(_dep_current_user)):
    await _owned_video_project(project_id, user)
    await db.video_projects.delete_one({"id": project_id, "user_id": user.id})
    await db.video_scenes.delete_many({"project_id": project_id, "user_id": user.id})
    return {"deleted": True}


@router.post("/video/projects/{project_id}/scenes")
async def add_video_scene(project_id: str, body: VideoSceneBody, user: User = Depends(_dep_current_user)):
    project = await _owned_video_project(project_id, user)
    if body.media_url and not body.media_url.startswith("/api/media/file/"):
        raise HTTPException(400, "Media must be an uploaded MoreHelp media file")
    scene = {"id": "vs_" + uuid.uuid4().hex, "project_id": project_id, "user_id": user.id,
             "scene_order": body.position, "duration": body.duration, "visual_url": body.media_url,
             "script_text": body.text, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.video_scenes.insert_one(scene)
    await db.video_projects.update_one({"id": project_id, "user_id": user.id}, {"$set": {"updated_at": datetime.now(timezone.utc).isoformat(), "status": "Ready to Preview"}})
    return _clean_video_doc(scene)


@router.patch("/video/projects/{project_id}/scenes/{scene_id}")
async def update_video_scene(project_id: str, scene_id: str, body: VideoSceneBody, user: User = Depends(_dep_current_user)):
    await _owned_video_project(project_id, user)
    if body.media_url and not body.media_url.startswith("/api/media/file/"):
        raise HTTPException(400, "Media must be an uploaded MoreHelp media file")
    scene = await db.video_scenes.find_one({"id": scene_id, "project_id": project_id, "user_id": user.id}, {"_id": 0})
    if not scene:
        raise HTTPException(404, "Scene not found")
    updates = {"duration": body.duration, "script_text": body.text, "visual_url": body.media_url, "scene_order": body.position}
    await db.video_scenes.update_one({"id": scene_id, "project_id": project_id}, {"$set": updates})
    scene.update(updates)
    return _clean_video_doc(scene)


@router.post("/video/projects/{project_id}/scenes/{scene_id}/duplicate")
async def duplicate_video_scene(project_id: str, scene_id: str, user: User = Depends(_dep_current_user)):
    await _owned_video_project(project_id, user)
    source = await db.video_scenes.find_one(
        {"id": scene_id, "project_id": project_id, "user_id": user.id},
        {"_id": 0},
    )
    if not source:
        raise HTTPException(404, "Scene not found")
    now = datetime.now(timezone.utc).isoformat()
    scene = {**source, "id": "vs_" + uuid.uuid4().hex, "scene_order": source.get("scene_order", 0) + 1, "created_at": now}
    await db.video_scenes.insert_one(scene)
    await db.video_projects.update_one(
        {"id": project_id, "user_id": user.id},
        {"$set": {"updated_at": now, "status": "Ready to Preview"}},
    )
    return _clean_video_doc(scene)


@router.delete("/video/projects/{project_id}/scenes/{scene_id}")
async def delete_video_scene(project_id: str, scene_id: str, user: User = Depends(_dep_current_user)):
    await _owned_video_project(project_id, user)
    result = await db.video_scenes.delete_one({"id": scene_id, "project_id": project_id, "user_id": user.id})
    if not result.deleted_count:
        raise HTTPException(404, "Scene not found")
    return {"deleted": True}


async def _download_render_asset(url: str, workdir: str, index: int, user_id: str) -> tuple[str, bool]:
    """Resolve an owned MoreHelp upload without making an unauthenticated HTTP hop."""
    prefix = "/api/media/file/"
    if not url.startswith(prefix):
        raise HTTPException(400, "Use an uploaded MoreHelp media file for each scene")
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket

    try:
        file_id = ObjectId(url[len(prefix):].split("?", 1)[0])
        stream = await AsyncIOMotorGridFSBucket(db).open_download_stream(file_id)
        metadata = stream.metadata or {}
        if metadata.get("uploader") != user_id and metadata.get("user_id") != user_id:
            raise HTTPException(403, "You can only render media you uploaded")
        contents = await stream.read()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(404, "Scene media could not be found") from exc

    suffix = Path(str(metadata.get("filename") or "")).suffix.lower() or ".bin"
    target = os.path.join(workdir, f"asset_{index}{suffix}")
    Path(target).write_bytes(contents)
    return target, str(metadata.get("content_type") or "").startswith("video/")


@router.post("/video/projects/{project_id}/render")
async def render_video_project(project_id: str, user: User = Depends(_dep_current_user)):
    project = await _owned_video_project(project_id, user)
    scenes = await db.video_scenes.find({"project_id": project_id, "user_id": user.id}, {"_id": 0}).sort("scene_order", 1).to_list(100)
    if not scenes:
        raise HTTPException(400, "Add at least one scene before making your video.")
    if any(not s.get("visual_url") for s in scenes):
        missing = next(i + 1 for i, s in enumerate(scenes) if not s.get("visual_url"))
        raise HTTPException(400, f"Scene {missing} needs a picture or video before your video can be made.")
    if not shutil.which("ffmpeg"):
        raise HTTPException(503, "Video making is unavailable because the renderer is not installed.")

    job_id = "vr_" + uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    await db.video_render_jobs.insert_one({"id": job_id, "project_id": project_id, "user_id": user.id, "status": "Processing", "progress": 5, "created_at": now})
    await db.video_projects.update_one({"id": project_id}, {"$set": {"status": "Making Your Video...", "render_job_id": job_id, "updated_at": now}})
    width, height = VIDEO_RATIOS[project.get("aspect_ratio", "9:16")]
    try:
        with tempfile.TemporaryDirectory(prefix="morehelp-video-") as workdir:
            inputs = []
            for index, scene in enumerate(scenes):
                path, is_video = await _download_render_asset(scene["visual_url"], workdir, index, user.id)
                output = os.path.join(workdir, f"scene_{index}.mp4")
                duration = str(scene.get("duration", 5))
                input_args = ["-i", path] if is_video else ["-loop", "1", "-i", path]
                command = ["ffmpeg", "-y", *input_args, "-t", duration, "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,format=yuv420p", "-r", "30", "-an", output]
                await asyncio.to_thread(subprocess.run, command, check=True, capture_output=True, timeout=90)
                inputs.append(output)
                await db.video_render_jobs.update_one(
                    {"id": job_id},
                    {"$set": {"progress": min(90, 10 + (index + 1) * 80 // len(scenes))}},
                )
            concat = os.path.join(workdir, "concat.txt")
            Path(concat).write_text("".join(f"file '{p}'\\n" for p in inputs))
            final = os.path.join(workdir, "final.mp4")
            await asyncio.to_thread(subprocess.run, ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", final], check=True, capture_output=True, timeout=120)
            from motor.motor_asyncio import AsyncIOMotorGridFSBucket
            with open(final, "rb") as stream:
                file_id = await AsyncIOMotorGridFSBucket(db).upload_from_stream(f"{project_id}.mp4", stream, metadata={"kind": "video_render", "project_id": project_id, "user_id": user.id, "content_type": "video/mp4"})
        output_url = f"/api/studio/video/files/{file_id}"
        await db.video_render_jobs.update_one({"id": job_id}, {"$set": {"status": "Completed", "progress": 100, "output_url": output_url, "completed_at": datetime.now(timezone.utc).isoformat()}})
        await db.video_projects.update_one({"id": project_id}, {"$set": {"status": "Video Ready", "final_video_url": output_url, "updated_at": datetime.now(timezone.utc).isoformat()}})
        return {"job_id": job_id, "status": "Video Ready", "progress": 100, "output_url": output_url}
    except Exception as exc:
        logger.exception("video render failed for %s", project_id)
        await db.video_render_jobs.update_one({"id": job_id}, {"$set": {"status": "Failed", "error_message": "The video could not be made. Check each scene's media and try again."}})
        await db.video_projects.update_one({"id": project_id}, {"$set": {"status": "Needs Attention", "updated_at": datetime.now(timezone.utc).isoformat()}})
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(500, "The video could not be made. Check each scene's media and try again.") from exc


@router.get("/video/projects/{project_id}/render-jobs/{job_id}")
async def get_video_render_job(project_id: str, job_id: str, user: User = Depends(_dep_current_user)):
    await _owned_video_project(project_id, user)
    job = await db.video_render_jobs.find_one(
        {"id": job_id, "project_id": project_id, "user_id": user.id},
        {"_id": 0},
    )
    if not job:
        raise HTTPException(404, "Render job not found")
    return _clean_video_doc(job)


@router.get("/video/files/{file_id}")
async def download_video_file(file_id: str, user: User = Depends(_dep_current_user)):
    _video_access(user)
    from bson import ObjectId
    from motor.motor_asyncio import AsyncIOMotorGridFSBucket
    try:
        stream = await AsyncIOMotorGridFSBucket(db).open_download_stream(ObjectId(file_id))
    except Exception:
        raise HTTPException(404, "Rendered video not found")
    owner = (stream.metadata or {}).get("user_id")
    if owner != user.id and user.role not in VIDEO_STAFF_ROLES:
        raise HTTPException(403, "Access denied")
    return StreamingResponse(stream, media_type="video/mp4", headers={"Content-Disposition": f'attachment; filename="{file_id}.mp4"'})


# ═════════════════════════════════════════════════════════════════════════════
# Extracted endpoint bodies (verbatim from backend/server.py)
# ═════════════════════════════════════════════════════════════════════════════
class LyricBody(BaseModel):
    topic: str
    style: Optional[str] = "Hip-Hop"
    mood: Optional[str] = "Triumphant"
    structure: Optional[str] = "Verse"
    notes: Optional[str] = ""


class MetadataBody(BaseModel):
    title: str
    artist: Optional[str] = ""
    type: Optional[str] = "Single"
    genre: Optional[str] = "Hip-Hop"
    description: Optional[str] = ""
    release_date: Optional[str] = ""
    tags: Optional[str] = ""


class CheerBody(BaseModel):
    chamber: Optional[str] = "studio"


@router.post("/studio/lyric")
async def studio_lyric(body: LyricBody, user: User = Depends(_dep_current_user)):
    if not body.topic.strip():
        raise HTTPException(400, "Topic is required")
    prompt = f"""Write {body.structure} lyrics in the {body.style} style with a {body.mood} mood.
Topic / concept: {body.topic}
{f'Additional notes: {body.notes}' if body.notes else ''}

Rules:
- Write only the lyrics, no explanations or labels
- Match the structure requested ({body.structure})
- Keep it authentic, culturally grounded, and purposeful
- Use vivid imagery and real emotion"""
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            system="You are a master lyricist and poet. You write authentic, culturally resonant lyrics across all genres. You understand flow, rhyme scheme, metaphor, and the emotional truth of Black American music and storytelling.",
            persona_label="Lyric Forge",
            user_id=user.id,
        )
        return {"lyrics": result.get("text", ""), "provider": result.get("provider", "free")}
    except Exception as e:
        logger.warning("Studio lyric error: %s", e)
        raise HTTPException(503, "Lyric generation unavailable")

@router.post("/studio/metadata")
async def studio_metadata(body: MetadataBody, user: User = Depends(_dep_current_user)):
    if not body.title.strip():
        raise HTTPException(400, "Title is required")
    prompt = f"""Generate professional release metadata for this creative work.

Title: {body.title}
Artist: {body.artist or "Independent Artist"}
Type: {body.type}
Genre: {body.genre}
Description: {body.description or "Not provided"}
Release date: {body.release_date or "TBD"}
Tags/keywords: {body.tags or "Not provided"}

Return ONLY a JSON object with these exact keys (no markdown, no extra text):
{{
  "title": "official title",
  "artist": "artist name",
  "genre": "primary genre",
  "subgenre": "secondary genre if applicable",
  "short_description": "1-2 sentence description for streaming platforms",
  "long_description": "3-4 sentence description for YouTube/website",
  "hashtags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "keywords": ["kw1", "kw2", "kw3"],
  "mood_tags": ["mood1", "mood2"],
  "suggested_playlist_pitches": "2-3 playlist types this fits"
}}"""
    try:
        from ai.llm_gateway import call_llm
        import json as _json
        result = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            system="You are a music metadata specialist and digital distribution expert. You produce accurate, platform-optimized metadata for independent artists.",
            persona_label="Publishing Gate",
            user_id=user.id,
        )
        text = result.get("text", "{}").strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        try:
            data = _json.loads(text)
        except Exception:
            data = {"raw": text}
        return data
    except Exception as e:
        logger.warning("Studio metadata error: %s", e)
        raise HTTPException(503, "Metadata generation unavailable")

@router.post("/studio/cheer")
async def studio_cheer(body: CheerBody):
    chamber_context = {
        "lyric": "user is writing lyrics in the Lyric Forge",
        "publishing": "user is preparing a release in the Publishing Gate",
        "visual": "user is working on visuals",
        "sound": "user is building beats or sound concepts",
        "studio": "user just entered the Creator's Sanctuary",
    }
    context = chamber_context.get(body.chamber or "studio", "user is creating")
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": f"Give me one short motivational or hype message. Context: {context}"}],
            system="You are the Creative Spirit — an enthusiastic, slightly chaotic, always supportive AI presence in a creator's studio. You give SHORT punchy hype lines (1-2 sentences max). Be real, be fun, occasionally philosophical but never preachy. Like a hype man who actually understands the creative process.",
            persona_label="Cheerleader",
        )
        return {"message": result.get("text", "Let's build something real today.")}
    except Exception:
        return {"message": "Let's build something real today."}


@router.post("/studio/altar")
async def studio_altar(body: dict, user: User = Depends(_dep_current_user)):
    descriptions = body.get("descriptions", [])
    colors = body.get("colors", [])
    notes = body.get("notes", "")
    prompt = (
        f"You are a visual creative director. Given these image descriptions: {descriptions} "
        f"and color palette: {colors}, provide a visual direction paragraph (3-4 sentences) "
        f"describing the aesthetic, mood, and visual language for this project. "
        f"Be specific and evocative."
        + (f" Additional notes: {notes}" if notes else "")
    )
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            system="You are a world-class visual creative director. Give vivid, specific visual direction.",
            persona_label="VisualDirector",
            user_id=user.id,
        )
        return {"direction": result.get("text", "A bold, cinematic visual identity awaits.")}
    except Exception:
        raise HTTPException(503, "Visual direction unavailable")


@router.post("/studio/script")
async def studio_script(body: dict, user: User = Depends(_dep_current_user)):
    doc_type = body.get("type", "script")
    title = body.get("title", "Untitled")
    content = body.get("content", "")
    if not content.strip():
        raise HTTPException(400, "Content is required")
    prompt = (
        f'Polish this {doc_type} titled "{title}". '
        f"Improve clarity, flow, and impact while preserving the creator's voice. "
        f"Return ONLY the polished version, no commentary.\n\n{content}"
    )
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            system="You are a professional script editor and literary polisher. Return only the improved text.",
            persona_label="ScriptEditor",
            user_id=user.id,
        )
        return {"polished": result.get("text", content)}
    except Exception:
        raise HTTPException(503, "Script polish unavailable")


@router.post("/studio/sound")
async def studio_sound_blueprint(body: dict, user: User = Depends(_dep_current_user)):
    bpm = body.get("bpm", 90)
    key = body.get("key", "C")
    mood = body.get("mood", [])
    reference = body.get("reference", "")
    prompt = (
        f"You are a music producer. Create a sonic blueprint for a track with: "
        f"BPM {bpm}, key {key}, mood {mood}, reference artist {reference}. "
        f"Describe: drums pattern, bass style, melody approach, texture/atmosphere, sample suggestions. "
        f"Be specific and technical. 200 words max."
    )
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": prompt}],
            system="You are a seasoned music producer with deep knowledge of beats, sound design, and arrangement.",
            persona_label="SoundProducer",
            user_id=user.id,
        )
        return {"blueprint": result.get("text", "Sonic blueprint unavailable — try again.")}
    except Exception:
        raise HTTPException(503, "Sound blueprint unavailable")


def _require_provider_result(result: dict) -> str:
    """Accept only a real provider response for the Sovereign AI surface."""
    if not isinstance(result, dict):
        raise RuntimeError("invalid provider response")
    provider = str(result.get("provider") or "")
    if provider in {"kb_fallback", "user_budget"}:
        raise RuntimeError(f"no live AI provider result ({provider})")
    text = str(result.get("text") or "").strip()
    if not text:
        raise RuntimeError("empty provider response")
    return text


def _sovereign_scaffold_text(action: str, ctx: dict) -> str:
    """Create a useful deterministic worksheet without claiming authorship."""
    topic = str(ctx.get("topic") or "your concept").strip()
    genre = str(ctx.get("genre") or "your chosen style").strip()
    mood = str(ctx.get("mood") or "the feeling you want").strip()
    if action == "generate_lyrics":
        return ("[CREATOR DRAFT - write your own words]\n"
                f"Concept: {topic}\nStyle: {genre}\nMood: {mood}\n\n"
                "TITLE: [your title]\n\nVERSE 1\n[opening image or truth]\n\n"
                "CHORUS / HOOK\n[the line you want people to remember]\n\n"
                "VERSE 2\n[new information or consequence]\n\n"
                "BRIDGE\n[what must be said before the return]\n\n"
                "FINAL CHORUS\n[keep, change, or intensify the hook]")
    if action == "generate_metadata":
        return ("[CREATOR METADATA DRAFT - verify every field]\n"
                f"title: {ctx.get('title') or '[your title]'}\n"
                f"artist: {ctx.get('artist') or '[artist / project name]'}\n"
                f"genre: {genre}\nshort_description: [one sentence]\n"
                "long_description: [what it is, who it serves, and why it matters]\n"
                "tags: [accurate tags only]\nrelease_date: [confirm date]\n"
                "credits: [list every human contributor]\n"
                "rights_check: [confirm ownership and permissions]")
    if action == "visual_direction":
        return ("[CREATOR VISUAL WORKSHEET]\n"
                f"Project: {topic}\nPalette: {ctx.get('colors') or '[choose colors]'}\n"
                "Subject: [what must the viewer see?]\nFeeling: [what should the viewer feel?]\n"
                "References: [what informs this?]\nDo not use: [misleading imagery]\n"
                "Human decision: [what makes this unmistakably yours?]")
    if action == "polish_script":
        return ("[CREATOR EDITING DRAFT - original text preserved]\n\n"
                f"{str(ctx.get('content') or '').strip()}\n\n"
                "EDITING CHECKLIST\n[ ] Keep the core voice.\n[ ] Remove repetition only when it weakens the work.\n"
                "[ ] Check names, facts, permissions, and context.\n[ ] Read aloud and make the final choices yourself.")
    if action == "sonic_blueprint":
        return ("[CREATOR PRODUCTION WORKSHEET]\n"
                f"BPM: {ctx.get('bpm') or '[choose tempo]'}\nKey: {ctx.get('key') or '[choose key]'}\n"
                f"Mood: {mood}\nDrums: [pattern, swing, and space]\nBass: [instrument and rhythm]\n"
                "Harmony: [chords or tonal center]\nTexture: [sounds that support the story]\n"
                "Arrangement: [intro -> verse -> hook -> bridge -> outro]\n"
                "Human test: [what must remain distinctive?]")
    return ("[CREATOR DECISION NOTE]\nAI assistance is unavailable.\n"
            "What am I making? [ ]\nWhat decision is needed now? [ ]\n"
            "What will I keep, change, or reject? [ ]\nWhat is the next version? [ ]")


@router.post("/studio/sovereign")
async def studio_sovereign(body: dict, user: User = Depends(_dep_current_user)):
    """
    Sovereign is the single AI interface in the Sanctuary.
    All chamber tools dispatch through here — Sovereign routes internally,
    calls sub-tools, and delivers results in his own voice.

    AI-ASSISTED POLICY: AI output is always a DRAFT the creator edits.
    When no live provider result is available, this endpoint returns a
    structured 503 so the caller cannot mistake a worksheet or KB answer for AI work.
    """
    from ai.llm_gateway import call_llm
    chamber = body.get("chamber", "map")
    message = body.get("message", "")
    action = body.get("action", "chat")
    ctx = body.get("context", {})

    artifact = None
    artifact_type = None

    try:
        if action == "generate_lyrics":
            prompt = (
                f"Write {ctx.get('structure', 'verse + hook')} lyrics. "
                f"Genre: {ctx.get('genre', '')}. Mood: {ctx.get('mood', '')}. "
                f"Topic: {ctx.get('topic', '')}. Notes: {ctx.get('notes', '')}. "
                "Return only the lyrics — no commentary."
            )
            r = await call_llm(system="You are Sovereign, a master lyricist and poet. Write authentic, culturally resonant lyrics.", messages=[{"role": "user", "content": prompt}], persona_label="LyricForge", user_id=user.id)
            artifact = _require_provider_result(r)
            artifact_type = "lyrics"
            response = "Lyrics forged, Creator. Take what's useful — cut what isn't. The Forge is yours."

        elif action == "generate_metadata":
            prompt = (
                f"Generate release metadata as valid JSON for: "
                f"title=\"{ctx.get('title','')}\", type=\"{ctx.get('content_type','')}\", "
                f"genre=\"{ctx.get('genre','')}\", description=\"{ctx.get('description','')}\". "
                "Return a JSON object with keys: title, artist_note, genre, release_date_suggestion, "
                "description, tags (array), upc_note, isrc_note, distributor_note, pitch."
            )
            r = await call_llm(system="You are Sovereign, a music metadata and distribution specialist. Return accurate structured metadata.", messages=[{"role": "user", "content": prompt}], persona_label="PublishingGate", user_id=user.id)
            artifact = _require_provider_result(r)
            artifact_type = "metadata"
            response = "Metadata is locked in, Boss. Everything's structured for distribution — copy what you need."

        elif action == "visual_direction":
            prompt = (
                f"You are a visual creative director. "
                f"Descriptions: {ctx.get('descriptions', [])}. Palette: {ctx.get('colors', [])}. "
                f"Notes: {ctx.get('notes', '')}. "
                "Write a vivid 3-4 sentence visual direction — aesthetic, mood, and visual language."
            )
            r = await call_llm(system="You are Sovereign, a visual creative director. Describe aesthetic, mood, and visual language vividly.", messages=[{"role": "user", "content": prompt}], persona_label="VisualAltar", user_id=user.id)
            artifact = _require_provider_result(r)
            artifact_type = "visual_direction"
            response = "Vision sealed, Creator. Your visual altar now has a direction — build from it."

        elif action == "polish_script":
            prompt = (
                f"Polish this {ctx.get('doc_type', 'script')} titled \"{ctx.get('title', '')}\"."
                " Improve clarity, flow, and impact while preserving the creator's voice."
                " Return ONLY the polished version.\n\n"
                f"{ctx.get('content', '')}"
            )
            r = await call_llm(system="You are Sovereign, a script editor. Polish for clarity, flow, and impact while preserving the creator voice.", messages=[{"role": "user", "content": prompt}], persona_label="ScriptScriptorium", user_id=user.id)
            artifact = _require_provider_result(r)
            artifact_type = "polished_script"
            response = "Script polished. I kept your voice and tightened the structure. Side-by-side is ready."

        elif action == "sonic_blueprint":
            prompt = (
                f"You are a music producer. Sonic blueprint: BPM {ctx.get('bpm', 90)}, "
                f"key {ctx.get('key', 'C')}, mood tags {ctx.get('mood', [])}, "
                f"reference artist: {ctx.get('reference', 'none')}. "
                "Describe: drums pattern, bass style, melody approach, texture/atmosphere, sample ideas. "
                "200 words max. Be specific and technical."
            )
            r = await call_llm(system="You are Sovereign, a music producer. Describe sonic blueprints with technical specificity.", messages=[{"role": "user", "content": prompt}], persona_label="SoundLab", user_id=user.id)
            artifact = _require_provider_result(r)
            artifact_type = "sonic_blueprint"
            response = "Blueprint built, Boss. Your sonic direction is locked in — the Sound Lab is ready."

        else:
            # Standard chat — Sovereign speaks directly
            system = (
                f"You are Sovereign, the AI general of the Creator's Sanctuary. "
                "You are direct, wise, and efficient — like a trusted general and creative advisor. "
                f"The Creator is currently in the {chamber} chamber. "
                "Keep responses under 100 words. Address the user as 'Creator' or 'Boss'. "
                "You manage a team of internal AI tools (Lyric Forge, Visual Altar, Script Scriptorium, "
                "Sound Lab, Publishing Gate) and dispatch them silently — the Creator only talks to you."
            )
            msg = message.strip() or "What should I focus on?"
            r = await call_llm(
                messages=[{"role": "user", "content": f"Context: {ctx}\n\nCreator: {msg}"}],
                system=system,
                persona_label="Sovereign",
                user_id=user.id,
            )
            response = _require_provider_result(r)

    except Exception as e:
        logger.warning("Sovereign provider unavailable (%s): %s", action, e)
        raise HTTPException(
            status_code=503,
            detail={
                "code": "AI_PROVIDER_UNAVAILABLE",
                "message": "Sovereign AI is unavailable because no live AI provider returned a result.",
                "retryable": True,
            },
        ) from e

    return {"response": response, "artifact": artifact, "artifact_type": artifact_type}


# ─── VIRTUAL ARCADE ──────────────────────────────────────────────────────────

ARCADE_CATALOG = [
    {"slug": "black-wall-street", "title": "Black Wall Street", "category": "Culture", "xp_reward": 150},
    {"slug": "dont-get-played", "title": "Don't Get Played", "category": "Finance", "xp_reward": 100},
    {"slug": "drum-builder", "title": "Drum Builder", "category": "Music", "xp_reward": 50},
    {"slug": "scripture-scramble", "title": "Scripture Scramble", "category": "Faith", "xp_reward": 75},
]
_ARCADE_SLUGS = {g["slug"]: g for g in ARCADE_CATALOG}


class ArcadeScoreBody(BaseModel):
    game_slug: str
    score: int
    metadata: Optional[dict] = None


ARCADE_AI_SYSTEM = """You are the Arcade Guide — a chill, culturally grounded AI companion inside the M.O.R.E. Help Center Virtual Arcade.
You keep it short, warm, and real. You help users learn from games, answer quick questions about Black history, finances, music, faith, and trades.
No lectures. No corporate speak. If someone just wants to vibe, let them.
Keep every reply under 3 sentences unless asked for more.
This is a free space — no upselling, no pressure, just community."""


class ArcadeChatBody(BaseModel):
    message: str
    game_slug: Optional[str] = None


@router.post("/arcade/chat")
async def arcade_chat(body: ArcadeChatBody):
    if not body.message.strip():
        raise HTTPException(400, "Empty message")
    context = f"\n\nUser is currently playing: {body.game_slug}" if body.game_slug else ""
    try:
        from ai.llm_gateway import call_llm
        result = await call_llm(
            messages=[{"role": "user", "content": body.message}],
            system=ARCADE_AI_SYSTEM + context,
            persona_label="Arcade Guide",
        )
        return {"reply": result.get("text", ""), "provider": result.get("provider", "free")}
    except Exception as e:
        logger.warning("Arcade chat error: %s", e)
        raise HTTPException(503, "AI unavailable — try again in a moment")


@router.get("/arcade/games")
async def arcade_games():
    return ARCADE_CATALOG


@router.post("/arcade/scores")
async def arcade_submit_score(body: ArcadeScoreBody, user: User = Depends(_dep_current_user)):
    game = _ARCADE_SLUGS.get(body.game_slug)
    if not game:
        raise HTTPException(400, "Unknown game slug")
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user.id,
        "game_slug": body.game_slug,
        "score": body.score,
        "metadata": body.metadata or {},
        "at": datetime.now(timezone.utc).isoformat(),
    }
    await db.arcade_scores.insert_one(doc)
    xp_reward = game["xp_reward"]
    new_total = await award_xp(user.id, xp_reward, f"Arcade: {body.game_slug}")
    return {"score": body.score, "xp_awarded": xp_reward, "new_total_xp": new_total}


@router.get("/arcade/my-scores")
async def arcade_my_scores(user: User = Depends(_dep_current_user)):
    cursor = db.arcade_scores.find({"user_id": user.id}, {"_id": 0})
    scores = {}
    async for doc in cursor:
        slug = doc["game_slug"]
        if slug not in scores or doc["score"] > scores[slug]:
            scores[slug] = doc["score"]
    return scores


@router.get("/arcade/leaderboard")
async def arcade_leaderboard(user: User = Depends(_dep_current_user)):
    pipeline = [
        {"$group": {"_id": "$user_id", "total_score": {"$sum": "$score"}}},
        {"$sort": {"total_score": -1}},
        {"$limit": 25},
    ]
    rows = await db.arcade_scores.aggregate(pipeline).to_list(25)
    result = []
    for row in rows:
        u = await db.users.find_one({"id": row["_id"]}, {"_id": 0, "full_name": 1})
        result.append({"user_id": row["_id"], "full_name": (u or {}).get("full_name", "Unknown"), "total_score": row["total_score"]})
    return {"top": result}


# ─────────────────────────────────────────────────────────────────────────────

# -- COMPLIANCE MODULES --
@router.get("/compliance")
async def list_compliance(user: User = Depends(_dep_current_user)):
    docs = await db.compliance_modules.find({}, {"_id": 0}).sort("order", 1).to_list(50)
    progress = await db.compliance_progress.find({"user_id": user.id}, {"_id": 0}).to_list(50)
    pmap = {p["module_slug"]: p for p in progress}
    for d in docs:
        d["my_progress"] = pmap.get(d["slug"])
    return docs


@router.get("/compliance/{slug}")
async def get_compliance(slug: str, user: User = Depends(_dep_current_user)):
    doc = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Compliance module not found")
    doc["my_progress"] = await db.compliance_progress.find_one(
        {"user_id": user.id, "module_slug": slug}, {"_id": 0}
    )
    return doc


@router.post("/compliance/{slug}/quiz")
async def submit_compliance_quiz(slug: str, body: dict, user: User = Depends(_dep_current_user)):
    mod = await db.compliance_modules.find_one({"slug": slug}, {"_id": 0})
    if not mod:
        raise HTTPException(404, "Module not found")
    answers = body.get("answers", [])
    quiz = mod.get("quiz", [])
    if len(answers) != len(quiz):
        raise HTTPException(400, "Answer count mismatch")
    correct = sum(1 for i, q in enumerate(quiz) if q["answer"] == answers[i])
    score = correct / len(quiz) * 100 if quiz else 0
    pass_pct = 80 if slug == "loto-certification" else 70
    status_val = "completed" if score >= pass_pct else "in_progress"
    now = datetime.now(timezone.utc)
    expires_at = None
    if status_val == "completed" and mod.get("expires_months"):
        expires_at = (now + timedelta(days=30 * mod["expires_months"])).isoformat()
    update = {
        "user_id": user.id,
        "module_slug": slug,
        "status": status_val,
        "quiz_score": score,
        "completed_at": now.isoformat() if status_val == "completed" else None,
        "expires_at": expires_at,
        "hours_logged": mod.get("hours", 0) if status_val == "completed" else 0,
        "updated_at": now.isoformat(),
    }
    await db.compliance_progress.update_one(
        {"user_id": user.id, "module_slug": slug},
        {"$set": update, "$setOnInsert": {"id": str(uuid.uuid4())}},
        upsert=True,
    )
    if status_val == "completed":
        await award_credentials(user.id)
    return {"score": score, "correct": correct, "total": len(quiz), "status": status_val, "pass_pct": pass_pct, "expires_at": expires_at}
