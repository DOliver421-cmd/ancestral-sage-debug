"""
ElevenLabs Client — THE CIPHER Audio System
=============================================
3-tier voice system for THE CIPHER:

  Tier 1: ElevenLabs — performance-grade spoken word voice
           Budget: 30,000 chars/month ($5 Starter plan)
           Soft warning at 25,000 chars
           Hard cap at 29,500 chars (500 char buffer)

  Tier 2: OpenAI TTS — backup voice (existing /ai/sage/tts infrastructure)
           Voice: "onyx" — deep, clear, always available
           Budget: unlimited within existing TTS cost caps

  Tier 3: Text Performance Mode — markup preserved, no audio
           Always available. Zero cost.

Audio budget tracked in MongoDB: db.cipher_audio_budget
Resets on the 1st of each month.
"""

import os
import io
import re
import logging
import hashlib
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.elevenlabs")

ELEVENLABS_API_KEY  = os.environ.get("ELEVENLABS_API_KEY", "")
CIPHER_VOICE_ID     = os.environ.get("CIPHER_VOICE_ID", "")
CIPHER_BACKUP_VOICE = os.environ.get("CIPHER_BACKUP_VOICE", "onyx")

# Budget constants — $5/month Starter = 30,000 chars/month
EL_MONTHLY_CAP   = 29_500   # hard cap (500 char safety buffer)
EL_SOFT_WARNING  = 25_000   # soft warning threshold
EL_BUDGET_DOC_ID = "cipher_elevenlabs_budget"

# ── Performance Markup Tags ───────────────────────────────────────────────────
# These tags shape the ElevenLabs voice settings and are stripped before TTS.
# Format: [tag] or [tag:value]

MARKUP_PATTERNS = {
    # Intensity down → whisper
    r"\[whisper\]":     {"stability": 0.85, "similarity_boost": 0.4, "style": 0.0, "speed": 0.85},
    r"\[soft\]":        {"stability": 0.75, "similarity_boost": 0.5, "style": 0.1, "speed": 0.9},
    r"\[tender\]":      {"stability": 0.8,  "similarity_boost": 0.5, "style": 0.1, "speed": 0.88},

    # Intensity up → performance / activation
    r"\[shout\]":       {"stability": 0.3,  "similarity_boost": 0.8, "style": 0.9, "speed": 1.1},
    r"\[hard\]":        {"stability": 0.4,  "similarity_boost": 0.7, "style": 0.7, "speed": 1.05},
    r"\[fire\]":        {"stability": 0.25, "similarity_boost": 0.8, "style": 1.0, "speed": 1.15},

    # Movement
    r"\[rise\]":        {"stability": 0.45, "similarity_boost": 0.65, "style": 0.6, "speed": 1.0},
    r"\[fall\]":        {"stability": 0.6,  "similarity_boost": 0.55, "style": 0.3, "speed": 0.92},
    r"\[crescendo\]":   {"stability": 0.3,  "similarity_boost": 0.75, "style": 0.85, "speed": 1.08},
    r"\[drop\]":        {"stability": 0.7,  "similarity_boost": 0.5, "style": 0.2, "speed": 0.88},

    # Default / neutral
    r"\[steady\]":      {"stability": 0.6,  "similarity_boost": 0.7, "style": 0.4, "speed": 1.0},
    r"\[testimony\]":   {"stability": 0.55, "similarity_boost": 0.7, "style": 0.5, "speed": 0.95},
}

# Default voice settings (balanced spoken word)
DEFAULT_VOICE_SETTINGS = {
    "stability":        0.5,
    "similarity_boost": 0.75,
    "style":            0.4,
    "use_speaker_boost": True,
    "speed":            1.0,
}


# ── Performance Markup Engine ─────────────────────────────────────────────────

def parse_performance_markup(text: str) -> tuple[str, dict]:
    """
    Parse performance markup tags from text.
    Returns:
        clean_text: text with all markup tags removed
        voice_settings: ElevenLabs voice_settings dict derived from dominant tag
    """
    found_settings = []

    # Find all markup tags and collect their voice settings
    for pattern, settings in MARKUP_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            found_settings.append(settings)

    # Remove all known markup tags
    clean = text
    for pattern in MARKUP_PATTERNS:
        clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

    # Remove pause tags (handled as natural pauses via punctuation)
    # [pause:0.8] → convert to "..." for natural TTS pause
    clean = re.sub(r"\[pause:\d+\.?\d*\]", "...", clean)
    clean = re.sub(r"\[pause\]", "...", clean)

    # Remove breath markers
    clean = re.sub(r"\[breath://?\]", "", clean)
    clean = re.sub(r"\[breath\]", "", clean)

    # Clean up any remaining unknown tags
    clean = re.sub(r"\[[^\]]*\]", "", clean)

    # Clean up extra whitespace
    clean = re.sub(r" {2,}", " ", clean).strip()
    clean = re.sub(r"\n{3,}", "\n\n", clean)

    # Derive voice settings — average if multiple tags, use dominant intensity
    if not found_settings:
        voice_settings = DEFAULT_VOICE_SETTINGS.copy()
    elif len(found_settings) == 1:
        voice_settings = {**DEFAULT_VOICE_SETTINGS, **found_settings[0]}
    else:
        # Average all found settings
        keys = ["stability", "similarity_boost", "style", "speed"]
        averaged = {
            k: round(sum(s.get(k, DEFAULT_VOICE_SETTINGS[k]) for s in found_settings) / len(found_settings), 3)
            for k in keys
        }
        voice_settings = {**DEFAULT_VOICE_SETTINGS, **averaged}

    voice_settings["use_speaker_boost"] = True
    return clean, voice_settings


def preserve_performance_markup(text: str) -> str:
    """
    Format text with markup tags preserved for display in Text Performance Mode.
    Makes the markup human-readable as stage directions.
    """
    display = text

    # Convert tags to readable stage directions
    replacements = {
        r"\[whisper\]":   "\n  ‹whisper›\n",
        r"\[soft\]":      "\n  ‹softly›\n",
        r"\[tender\]":    "\n  ‹tenderly›\n",
        r"\[shout\]":     "\n  ‹FULL VOICE›\n",
        r"\[hard\]":      "\n  ‹with force›\n",
        r"\[fire\]":      "\n  ‹FIRE›\n",
        r"\[rise\]":      "\n  ‹rising›\n",
        r"\[fall\]":      "\n  ‹falling›\n",
        r"\[crescendo\]": "\n  ‹building›\n",
        r"\[drop\]":      "\n  ‹drop›\n",
        r"\[steady\]":    "\n  ‹steady›\n",
        r"\[testimony\]": "\n  ‹testimony›\n",
        r"\[pause:(\d+\.?\d*)\]": r"\n  ‹pause \1s›\n",
        r"\[pause\]":     "\n  ‹pause›\n",
        r"\[breath://?\]": "\n  ‹breathe›\n",
        r"\[breath\]":    "\n  ‹breathe›\n",
    }
    for pattern, replacement in replacements.items():
        display = re.sub(pattern, replacement, display, flags=re.IGNORECASE)

    # Clean remaining unknown tags
    display = re.sub(r"\[[^\]]*\]", "", display)
    return display.strip()


# ── Audio Budget Manager ──────────────────────────────────────────────────────

async def get_budget_status(db) -> dict:
    """
    Returns current ElevenLabs character budget status for this month.
    Creates the budget document if it doesn't exist.
    """
    now    = datetime.now(timezone.utc)
    month  = now.strftime("%Y-%m")

    try:
        doc = await db.cipher_audio_budget.find_one({"_id": EL_BUDGET_DOC_ID})

        if not doc or doc.get("month") != month:
            # New month — reset
            new_doc = {
                "_id":        EL_BUDGET_DOC_ID,
                "month":      month,
                "chars_used": 0,
                "chars_cap":  EL_MONTHLY_CAP,
                "soft_warning": EL_SOFT_WARNING,
                "resets_on":  f"{now.year}-{now.month + 1 if now.month < 12 else 1:02d}-01",
                "updated_at": now.isoformat(),
            }
            await db.cipher_audio_budget.replace_one(
                {"_id": EL_BUDGET_DOC_ID}, new_doc, upsert=True
            )
            return new_doc

        return doc
    except Exception as e:
        logger.warning("get_budget_status failed: %s", e)
        return {"chars_used": 0, "chars_cap": EL_MONTHLY_CAP, "month": month}


async def charge_budget(db, chars: int) -> bool:
    """
    Attempt to charge chars against the monthly budget.
    Returns True if charge succeeded, False if over cap.
    """
    try:
        now   = datetime.now(timezone.utc)
        month = now.strftime("%Y-%m")
        status = await get_budget_status(db)

        if status.get("month") != month:
            used = 0
        else:
            used = status.get("chars_used", 0)

        if used + chars > EL_MONTHLY_CAP:
            logger.info("ElevenLabs budget cap reached: %d used + %d requested > %d cap", used, chars, EL_MONTHLY_CAP)
            return False

        await db.cipher_audio_budget.update_one(
            {"_id": EL_BUDGET_DOC_ID},
            {"$inc": {"chars_used": chars}, "$set": {"updated_at": now.isoformat()}},
            upsert=True,
        )

        new_used = used + chars
        if new_used >= EL_SOFT_WARNING:
            logger.warning("ElevenLabs soft warning: %d / %d chars used this month", new_used, EL_MONTHLY_CAP)

        return True
    except Exception as e:
        logger.warning("charge_budget failed: %s — allowing request", e)
        return True  # Fail open so audio doesn't break on DB hiccup


async def get_remaining_chars(db) -> int:
    """Returns remaining ElevenLabs character budget for this month."""
    try:
        status = await get_budget_status(db)
        return max(0, EL_MONTHLY_CAP - status.get("chars_used", 0))
    except Exception:
        return EL_MONTHLY_CAP


# ── ElevenLabs API Call ───────────────────────────────────────────────────────

async def elevenlabs_tts(
    text: str,
    voice_id: str = "",
    voice_settings: dict = None,
    db=None,
) -> bytes | None:
    """
    Call ElevenLabs TTS API.
    Returns audio bytes on success, None on failure.
    Charges the monthly budget on success.
    """
    if not ELEVENLABS_API_KEY:
        logger.info("ElevenLabs: no API key configured — skipping T1")
        return None

    vid = voice_id or CIPHER_VOICE_ID
    if not vid:
        logger.info("ElevenLabs: no voice ID configured — skipping T1")
        return None

    chars = len(text)

    # Budget check
    if db is not None:
        budget_ok = await charge_budget(db, chars)
        if not budget_ok:
            logger.info("ElevenLabs: budget exhausted — falling to T2")
            return None

    settings = voice_settings or DEFAULT_VOICE_SETTINGS.copy()
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability":        settings.get("stability", 0.5),
            "similarity_boost": settings.get("similarity_boost", 0.75),
            "style":            settings.get("style", 0.4),
            "use_speaker_boost": settings.get("use_speaker_boost", True),
            "speed":            settings.get("speed", 1.0),
        },
    }

    try:
        import httpx as _httpx
        async with _httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{vid}",
                headers={
                    "xi-api-key":   ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                    "Accept":       "audio/mpeg",
                },
                json=payload,
            )

        if r.status_code == 200:
            logger.info("ElevenLabs T1 OK — %d chars, voice %s", chars, vid)
            return r.content
        else:
            logger.warning("ElevenLabs T1 failed: HTTP %d — %s", r.status_code, r.text[:200])
            # Refund budget on failure
            if db is not None:
                try:
                    await db.cipher_audio_budget.update_one(
                        {"_id": EL_BUDGET_DOC_ID},
                        {"$inc": {"chars_used": -chars}},
                    )
                except Exception: pass
            return None
    except Exception as e:
        logger.warning("ElevenLabs T1 exception: %s", e)
        if db is not None:
            try:
                await db.cipher_audio_budget.update_one(
                    {"_id": EL_BUDGET_DOC_ID},
                    {"$inc": {"chars_used": -chars}},
                )
            except Exception: pass
        return None


# ── Audio Cache ───────────────────────────────────────────────────────────────

def _el_cache_key(text: str, voice_id: str, settings: dict) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    h.update(b"|")
    h.update(voice_id.encode("utf-8"))
    h.update(b"|")
    h.update(str(sorted(settings.items())).encode("utf-8"))
    return "el_" + h.hexdigest()[:32]


async def get_cached_audio(db, cache_key: str) -> bytes | None:
    try:
        import base64
        doc = await db.cipher_tts_cache.find_one({"key": cache_key}, {"_id": 0, "audio_b64": 1})
        if doc and doc.get("audio_b64"):
            return base64.b64decode(doc["audio_b64"])
    except Exception as e:
        logger.warning("cipher TTS cache read failed: %s", e)
    return None


async def cache_audio(db, cache_key: str, audio: bytes) -> None:
    try:
        import base64
        await db.cipher_tts_cache.update_one(
            {"key": cache_key},
            {"$set": {
                "key":        cache_key,
                "audio_b64":  base64.b64encode(audio).decode(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "size_bytes": len(audio),
                "source":     "elevenlabs",
            }},
            upsert=True,
        )
    except Exception as e:
        logger.warning("cipher TTS cache write failed: %s", e)


# ── Main Entry Point ──────────────────────────────────────────────────────────

async def cipher_speak(
    text: str,
    voice_id: str = "",
    force_tier: str = "",
    db=None,
) -> dict:
    """
    THE CIPHER's 3-tier voice system.

    Args:
        text:       Raw text, may contain performance markup tags
        voice_id:   Override ElevenLabs voice ID (optional)
        force_tier: Force a specific tier: "elevenlabs" | "openai" | "text"
        db:         MongoDB database instance

    Returns dict with:
        tier:         "elevenlabs" | "openai" | "text"
        audio:        bytes | None
        clean_text:   Text with markup stripped (for display + fallback TTS)
        display_text: Text with markup as readable stage directions
        voice_settings: The ElevenLabs settings that were (or would be) used
        budget_remaining: Remaining ElevenLabs chars this month
    """
    clean_text, voice_settings = parse_performance_markup(text)
    display_text               = preserve_performance_markup(text)
    vid                        = voice_id or CIPHER_VOICE_ID

    budget_remaining = await get_remaining_chars(db) if db else EL_MONTHLY_CAP

    # Cache check (only for ElevenLabs tier)
    cache_key = _el_cache_key(clean_text, vid, voice_settings)
    if db and force_tier != "text":
        cached = await get_cached_audio(db, cache_key)
        if cached:
            logger.info("cipher_speak: cache hit — %d bytes", len(cached))
            return {
                "tier":             "elevenlabs_cached",
                "audio":            cached,
                "clean_text":       clean_text,
                "display_text":     display_text,
                "voice_settings":   voice_settings,
                "budget_remaining": budget_remaining,
            }

    # ── Tier 1: ElevenLabs ────────────────────────────────────────────────────
    if force_tier in ("", "elevenlabs") and ELEVENLABS_API_KEY and vid:
        audio = await elevenlabs_tts(clean_text, vid, voice_settings, db)
        if audio:
            if db:
                await cache_audio(db, cache_key, audio)
            return {
                "tier":             "elevenlabs",
                "audio":            audio,
                "clean_text":       clean_text,
                "display_text":     display_text,
                "voice_settings":   voice_settings,
                "budget_remaining": budget_remaining - len(clean_text),
            }

    # ── Tier 2: OpenAI TTS (backup voice — already in system) ─────────────────
    if force_tier in ("", "openai"):
        logger.info("cipher_speak: falling to T2 OpenAI TTS")
        return {
            "tier":             "openai",
            "audio":            None,  # Caller routes to /ai/sage/tts endpoint
            "clean_text":       clean_text,
            "display_text":     display_text,
            "voice_settings":   voice_settings,
            "budget_remaining": budget_remaining,
            "fallback_voice":   CIPHER_BACKUP_VOICE,
            "fallback_endpoint": "/api/ai/sage/tts",
        }

    # ── Tier 3: Text Performance Mode ─────────────────────────────────────────
    logger.info("cipher_speak: T3 text performance mode")
    return {
        "tier":             "text",
        "audio":            None,
        "clean_text":       clean_text,
        "display_text":     display_text,
        "voice_settings":   voice_settings,
        "budget_remaining": budget_remaining,
    }
