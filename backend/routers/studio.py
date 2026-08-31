"""
Studio + Arcade + Compliance router — Creator's Sanctuary, Virtual Arcade,
and safety-compliance training.

Extracted verbatim from backend/server.py (monolith refactor, slice 5).
Shared state (db, current_user, award_xp, award_credentials) is bound by
server.py via bind() at include time — no circular imports.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, ConfigDict, Field
from roles import Role, ROLE_RANK, role_rank, LEGACY_ROLE_MAP, normalize_role, FREE_BYOK_ROLES

logger = logging.getLogger("lcewai")
router = APIRouter(tags=["studio", "arcade", "compliance"])

# ── Shared state, bound by server.py via bind() ──────────────────────────────
db = None
current_user = award_xp = award_credentials = None


def bind(_db, _current_user, _award_xp, _award_credentials):
    """Called by server.py at include time to inject shared dependencies."""
    global db, current_user, award_xp, award_credentials
    db = _db
    current_user = _current_user
    award_xp = _award_xp
    award_credentials = _award_credentials


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
        )
        return {"blueprint": result.get("text", "Sonic blueprint unavailable — try again.")}
    except Exception:
        raise HTTPException(503, "Sound blueprint unavailable")


_SOFT_ASSIST_LABEL = "AI assist unavailable. This is a creator-owned draft scaffold; fill, change, or discard it."


def _sovereign_scaffold(action: str, ctx: dict) -> tuple[str, str]:
    labels = {
        "generate_lyrics": "lyrics",
        "generate_metadata": "metadata",
        "visual_direction": "visual_direction",
        "polish_script": "polished_script",
        "sonic_blueprint": "sonic_blueprint",
    }
    return labels.get(action, "creator_prompt"), _SOFT_ASSIST_LABEL


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
    When AI is unavailable, we never fake it and never dead-end —
    we hand back a labeled structural scaffold the creator fills themselves.
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
            r = await call_llm(system="You are Sovereign, a master lyricist and poet. Write authentic, culturally resonant lyrics.", messages=[{"role": "user", "content": prompt}], persona_label="LyricForge")
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty lyric response")
            artifact = r.get("text", "")
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
            r = await call_llm(system="You are Sovereign, a music metadata and distribution specialist. Return accurate structured metadata.", messages=[{"role": "user", "content": prompt}], persona_label="PublishingGate")
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty metadata response")
            artifact = r.get("text", "{}")
            artifact_type = "metadata"
            response = "Metadata is locked in, Boss. Everything's structured for distribution — copy what you need."

        elif action == "visual_direction":
            prompt = (
                f"You are a visual creative director. "
                f"Descriptions: {ctx.get('descriptions', [])}. Palette: {ctx.get('colors', [])}. "
                f"Notes: {ctx.get('notes', '')}. "
                "Write a vivid 3-4 sentence visual direction — aesthetic, mood, and visual language."
            )
            r = await call_llm(system="You are Sovereign, a visual creative director. Describe aesthetic, mood, and visual language vividly.", messages=[{"role": "user", "content": prompt}], persona_label="VisualAltar")
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty visual response")
            artifact = r.get("text", "")
            artifact_type = "visual_direction"
            response = "Vision sealed, Creator. Your visual altar now has a direction — build from it."

        elif action == "polish_script":
            prompt = (
                f"Polish this {ctx.get('doc_type', 'script')} titled \"{ctx.get('title', '')}\"."
                " Improve clarity, flow, and impact while preserving the creator's voice."
                " Return ONLY the polished version.\n\n"
                f"{ctx.get('content', '')}"
            )
            r = await call_llm(system="You are Sovereign, a script editor. Polish for clarity, flow, and impact while preserving the creator voice.", messages=[{"role": "user", "content": prompt}], persona_label="ScriptScriptorium")
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty polish response")
            artifact = r.get("text", "")
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
            r = await call_llm(system="You are Sovereign, a music producer. Describe sonic blueprints with technical specificity.", messages=[{"role": "user", "content": prompt}], persona_label="SoundLab")
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty blueprint response")
            artifact = r.get("text", "")
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
            )
            if not (r.get("text") or "").strip():
                raise RuntimeError("empty chat response")
            response = r.get("text", "")

    except Exception:
        artifact_type, response = _sovereign_scaffold(action, ctx)
        artifact = _sovereign_scaffold_text(action, ctx)

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
