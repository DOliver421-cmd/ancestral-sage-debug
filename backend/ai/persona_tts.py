"""
WAI-Institute Multi-Persona TTS System
=======================================
Generalized 3-tier voice system for ALL personas — Director, Revenue Director,
Ancestral Sage, Cipher, and any future persona.

Tier 1: ElevenLabs — performance-grade voice, per-persona voice IDs
Tier 2: OpenAI TTS — backup voice, per-persona OpenAI voice assignment
Tier 3: Text Mode — clean text, always available, zero cost

BUDGET: Each persona has its own ElevenLabs character budget tracked in MongoDB.
Total allocation across personas is shared by the same ElevenLabs account.
Upgrade ElevenLabs plan when using 3+ personas actively (Creator = $22/mo, 100K chars).

VOICE CONFIGURATION (set these in Railway Variables):
  DIRECTOR_VOICE_ID           = [ElevenLabs Voice ID — deep authority, e.g. Daniel]
  DIRECTOR_BACKUP_VOICE       = alloy           (OpenAI)
  REVENUE_DIRECTOR_VOICE_ID   = [ElevenLabs Voice ID — confident, strategic]
  REVENUE_DIRECTOR_BACKUP_VOICE = echo          (OpenAI)
  SAGE_VOICE_ID               = [ElevenLabs Voice ID — warm, ancestral, resonant]
  SAGE_BACKUP_VOICE           = shimmer         (OpenAI)
  CIPHER_VOICE_ID             = [already set]
  CIPHER_BACKUP_VOICE         = onyx            (already set)
"""

import os
import re
import hashlib
import logging
from datetime import datetime, timezone

logger = logging.getLogger("lcewai.persona_tts")

# ── Per-Persona Voice Config ──────────────────────────────────────────────────

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")

PERSONA_VOICE_CONFIG = {
    "director": {
        "elevenlabs_voice_id": os.environ.get("DIRECTOR_VOICE_ID", ""),
        "openai_voice":        os.environ.get("DIRECTOR_BACKUP_VOICE", "alloy"),
        "monthly_cap":         15_000,   # chars — Director speaks authoritatively, less frequently
        "soft_warning":        12_000,
        "budget_doc_id":       "director_tts_budget",
        "cache_collection":    "director_tts_cache",
    },
    "revenue_director": {
        "elevenlabs_voice_id": os.environ.get("REVENUE_DIRECTOR_VOICE_ID", ""),
        "openai_voice":        os.environ.get("REVENUE_DIRECTOR_BACKUP_VOICE", "echo"),
        "monthly_cap":         10_000,
        "soft_warning":        8_000,
        "budget_doc_id":       "rd_tts_budget",
        "cache_collection":    "rd_tts_cache",
    },
    "ancestral_sage": {
        "elevenlabs_voice_id": os.environ.get("SAGE_VOICE_ID", ""),
        "openai_voice":        os.environ.get("SAGE_BACKUP_VOICE", "shimmer"),
        "monthly_cap":         20_000,
        "soft_warning":        16_000,
        "budget_doc_id":       "sage_tts_budget",
        "cache_collection":    "sage_tts_cache",
    },
    "cipher": {
        # Cipher uses its own elevenlabs_client.py — this is for reference only
        "elevenlabs_voice_id": os.environ.get("CIPHER_VOICE_ID", ""),
        "openai_voice":        os.environ.get("CIPHER_BACKUP_VOICE", "onyx"),
        "monthly_cap":         29_500,
        "soft_warning":        25_000,
        "budget_doc_id":       "cipher_elevenlabs_budget",
        "cache_collection":    "cipher_tts_cache",
    },
    "sovereign": {
        # The Sovereign — NAM Oshun Revenue Engine, executive-only
        "elevenlabs_voice_id": os.environ.get("SOVEREIGN_VOICE_ID", ""),
        "openai_voice":        os.environ.get("SOVEREIGN_BACKUP_VOICE", "fable"),
        "monthly_cap":         12_000,   # Sovereign speaks counseling cadence — fewer, weightier words
        "soft_warning":        9_600,
        "budget_doc_id":       "sovereign_tts_budget",
        "cache_collection":    "sovereign_tts_cache",
    },
}

# ── Default ElevenLabs Voice Settings (per persona type) ─────────────────────

PERSONA_VOICE_SETTINGS = {
    "director": {
        # Deep, authoritative, precise — executive command voice
        "stability":         0.75,
        "similarity_boost":  0.8,
        "style":             0.2,
        "use_speaker_boost": True,
        "speed":             0.92,
    },
    "revenue_director": {
        # Confident, strategic, measured — financial intelligence voice
        "stability":         0.70,
        "similarity_boost":  0.75,
        "style":             0.25,
        "use_speaker_boost": True,
        "speed":             0.95,
    },
    "ancestral_sage": {
        # Warm, deep, unhurried — ancestral wisdom, healing presence
        "stability":         0.80,
        "similarity_boost":  0.70,
        "style":             0.15,
        "use_speaker_boost": True,
        "speed":             0.85,
    },
    "sovereign": {
        # Counseling cadence — grounded, unhurried, revenue-ethical
        "stability":         0.82,
        "similarity_boost":  0.72,
        "style":             0.18,
        "use_speaker_boost": True,
        "speed":             0.90,
    },
}


# ── Budget Management (per-persona) ──────────────────────────────────────────

async def _get_persona_budget(db, persona: str) -> dict:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config or db is None:
        return {"chars_used": 0, "chars_cap": 10_000}

    doc_id = config["budget_doc_id"]
    month  = datetime.now(timezone.utc).strftime("%Y-%m")
    try:
        doc = await db.persona_tts_budgets.find_one({"_id": doc_id})
        if not doc or doc.get("month") != month:
            new_doc = {
                "_id":        doc_id,
                "persona":    persona,
                "month":      month,
                "chars_used": 0,
                "chars_cap":  config["monthly_cap"],
                "soft_warning": config["soft_warning"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            await db.persona_tts_budgets.replace_one({"_id": doc_id}, new_doc, upsert=True)
            return new_doc
        return doc
    except Exception as e:
        logger.warning("persona_tts budget get failed [%s]: %s", persona, e)
        return {"chars_used": 0, "chars_cap": config.get("monthly_cap", 10_000)}


async def _charge_persona_budget(db, persona: str, chars: int) -> bool:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config:
        return True

    try:
        budget = await _get_persona_budget(db, persona)
        used = budget.get("chars_used", 0)
        cap  = config["monthly_cap"]

        if used + chars > cap:
            logger.info("persona_tts budget cap [%s]: %d used + %d > %d cap", persona, used, chars, cap)
            return False

        doc_id = config["budget_doc_id"]
        await db.persona_tts_budgets.update_one(
            {"_id": doc_id},
            {"$inc": {"chars_used": chars}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
            upsert=True,
        )
        new_used = used + chars
        if new_used >= config["soft_warning"]:
            logger.warning("persona_tts soft warning [%s]: %d/%d chars used", persona, new_used, cap)
        return True
    except Exception as e:
        logger.warning("persona_tts charge budget failed [%s]: %s — allowing", persona, e)
        return True  # Fail-open on DB error


async def _refund_persona_budget(db, persona: str, chars: int) -> None:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config or db is None:
        return
    try:
        await db.persona_tts_budgets.update_one(
            {"_id": config["budget_doc_id"]},
            {"$inc": {"chars_used": -chars}},
        )
    except Exception: pass


async def _get_remaining_chars(db, persona: str) -> int:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config:
        return 0
    try:
        budget = await _get_persona_budget(db, persona)
        return max(0, config["monthly_cap"] - budget.get("chars_used", 0))
    except Exception:
        return config.get("monthly_cap", 10_000)


# ── Audio Cache ───────────────────────────────────────────────────────────────

def _tts_cache_key(persona: str, text: str, voice_id: str) -> str:
    h = hashlib.sha256()
    h.update(persona.encode())
    h.update(b"|")
    h.update(text.encode())
    h.update(b"|")
    h.update(voice_id.encode())
    return f"ptts_{h.hexdigest()[:32]}"


async def _get_cached(db, persona: str, key: str) -> bytes | None:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config or db is None:
        return None
    try:
        import base64
        coll = getattr(db, config["cache_collection"])
        doc  = await coll.find_one({"key": key}, {"_id": 0, "audio_b64": 1})
        if doc and doc.get("audio_b64"):
            return base64.b64decode(doc["audio_b64"])
    except Exception as e:
        logger.warning("persona_tts cache read [%s]: %s", persona, e)
    return None


async def _cache_audio(db, persona: str, key: str, audio: bytes) -> None:
    config = PERSONA_VOICE_CONFIG.get(persona, {})
    if not config or db is None:
        return
    try:
        import base64
        coll = getattr(db, config["cache_collection"])
        await coll.update_one(
            {"key": key},
            {"$set": {
                "key":        key,
                "audio_b64":  base64.b64encode(audio).decode(),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "size_bytes": len(audio),
                "source":     "elevenlabs",
            }},
            upsert=True,
        )
    except Exception as e:
        logger.warning("persona_tts cache write [%s]: %s", persona, e)


# ── ElevenLabs API Call ───────────────────────────────────────────────────────

async def _elevenlabs_call(text: str, voice_id: str, voice_settings: dict) -> bytes | None:
    if not ELEVENLABS_API_KEY or not voice_id:
        return None
    try:
        import httpx
        payload = {
            "text":     text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability":         voice_settings.get("stability", 0.7),
                "similarity_boost":  voice_settings.get("similarity_boost", 0.75),
                "style":             voice_settings.get("style", 0.2),
                "use_speaker_boost": voice_settings.get("use_speaker_boost", True),
                "speed":             voice_settings.get("speed", 0.95),
            },
        }
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                headers={"xi-api-key": ELEVENLABS_API_KEY, "Accept": "audio/mpeg", "Content-Type": "application/json"},
                json=payload,
            )
        if r.status_code == 200:
            return r.content
        logger.warning("ElevenLabs API error: HTTP %d", r.status_code)
    except Exception as e:
        logger.warning("ElevenLabs API exception: %s", e)
    return None


# ── Main Entry Point ──────────────────────────────────────────────────────────

async def persona_speak(
    persona: str,
    text: str,
    force_tier: str = "",
    db=None,
) -> dict:
    """
    3-tier TTS for any WAI persona.

    Args:
        persona:    "director" | "revenue_director" | "ancestral_sage" | "cipher"
        text:       Text to speak (markup tags are stripped)
        force_tier: "elevenlabs" | "openai" | "text" (optional override)
        db:         MongoDB instance

    Returns dict with tier, audio, clean_text, budget_remaining, fallback_voice, fallback_endpoint
    """
    config = PERSONA_VOICE_CONFIG.get(persona)
    if not config:
        return {"tier": "text", "audio": None, "clean_text": text, "display_text": text,
                "budget_remaining": 0, "error": f"Unknown persona: {persona}"}

    # Strip any markup tags from text (simple version — Cipher has full markup engine)
    clean_text = re.sub(r"\[[^\]]*\]", "", text).strip()
    clean_text = re.sub(r" {2,}", " ", clean_text)

    vid              = config["elevenlabs_voice_id"]
    openai_voice     = config["openai_voice"]
    voice_settings   = PERSONA_VOICE_SETTINGS.get(persona, {})
    budget_remaining = await _get_remaining_chars(db, persona) if db else config["monthly_cap"]
    cache_key        = _tts_cache_key(persona, clean_text, vid)

    # ── Cache check ───────────────────────────────────────────────────────────
    if db and force_tier not in ("text", "openai"):
        cached = await _get_cached(db, persona, cache_key)
        if cached:
            logger.info("persona_tts cache hit [%s]: %d bytes", persona, len(cached))
            return {
                "tier":             "elevenlabs_cached",
                "audio":            cached,
                "clean_text":       clean_text,
                "display_text":     text,
                "budget_remaining": budget_remaining,
            }

    # ── Tier 1: ElevenLabs ────────────────────────────────────────────────────
    if force_tier in ("", "elevenlabs") and ELEVENLABS_API_KEY and vid:
        charged = await _charge_persona_budget(db, persona, len(clean_text)) if db else True
        if charged:
            audio = await _elevenlabs_call(clean_text, vid, voice_settings)
            if audio:
                if db:
                    await _cache_audio(db, persona, cache_key, audio)
                logger.info("persona_tts T1 ElevenLabs [%s]: %d bytes", persona, len(audio))
                return {
                    "tier":             "elevenlabs",
                    "audio":            audio,
                    "clean_text":       clean_text,
                    "display_text":     text,
                    "budget_remaining": budget_remaining - len(clean_text),
                }
            else:
                # API failed — refund budget
                await _refund_persona_budget(db, persona, len(clean_text))

    # ── Tier 2: OpenAI TTS ────────────────────────────────────────────────────
    if force_tier in ("", "openai"):
        logger.info("persona_tts T2 OpenAI [%s] → voice=%s", persona, openai_voice)
        return {
            "tier":              "openai",
            "audio":             None,
            "clean_text":        clean_text,
            "display_text":      text,
            "budget_remaining":  budget_remaining,
            "fallback_voice":    openai_voice,
            "fallback_endpoint": "/api/ai/sage/tts",
        }

    # ── Tier 3: Text ──────────────────────────────────────────────────────────
    logger.info("persona_tts T3 text [%s]", persona)
    return {
        "tier":             "text",
        "audio":            None,
        "clean_text":       clean_text,
        "display_text":     text,
        "budget_remaining": budget_remaining,
    }
