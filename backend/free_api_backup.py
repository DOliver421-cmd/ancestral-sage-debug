"""
free_api_backup.py — Free-tier fallback matrix for core services.

Maps each paid/external service to one or more free alternatives so the
platform can stay operational with zero budget.  Each entry has:
  - service_key    : canonical name
  - primary        : the paid/default provider
  - free_fallbacks : ordered list of {name, url/endpoint, needs_key, ok}
  - ok             : whether the fallback is configured and ready

The `resolve(service_key)` helper returns the first working fallback.
"""

import logging
import os

logger = logging.getLogger("free_api_backup")

# ── Free API backup matrix ─────────────────────────────────────────────────────
# Each entry is a dict that describes the fallback chain for a service.
# `needs_key` means the env var must be set; `ok` is evaluated at call time.
MATRIX = {
    # ── AI / LLM ───────────────────────────────────────────────────────────────
    "ai_llm": {
        "label": "AI Language Model",
        "primary": "Anthropic Claude",
        "free_fallbacks": [
            {
                "name": "OpenRouter (free tier)",
                "endpoint": "https://openrouter.ai/api/v1/chat/completions",
                "needs_key": "OPENROUTER_API_KEY",
                "ok": bool(os.environ.get("OPENROUTER_API_KEY")),
                "models": ["google/gemini-2.0-flash-lite-preview-02-05:free"],
                "note": "Gemini Flash free tier — 60 req/min, no credit card needed",
            },
            {
                "name": "Local keyword KB",
                "endpoint": None,
                "needs_key": None,
                "ok": True,
                "models": [],
                "note": "Helper.jsx KB + server-side keyword fallback — zero API calls",
            },
        ],
        "current": "anthropic",
    },
    # ── Text-to-Speech ─────────────────────────────────────────────────────────
    "tts": {
        "label": "Text-to-Speech",
        "primary": "ElevenLabs / OpenAI TTS",
        "free_fallbacks": [
            {
                "name": "Browser speechSynthesis",
                "endpoint": None,
                "needs_key": None,
                "ok": True,
                "note": "Native browser TTS — no API key, no cost, works offline",
            },
        ],
        "current": "elevenlabs",
    },
    # ── Email ──────────────────────────────────────────────────────────────────
    "email": {
        "label": "Email (transactional)",
        "primary": "Resend",
        "free_fallbacks": [
            {
                "name": "Gmail SMTP",
                "endpoint": "smtp.gmail.com:587",
                "needs_key": "GMAIL_SMTP_PASSWORD",
                "ok": bool(os.environ.get("GMAIL_SMTP_PASSWORD")),
                "note": "Gmail SMTP relay — 500 emails/day free",
            },
        ],
        "current": "resend",
    },
    # ── Database ───────────────────────────────────────────────────────────────
    "database": {
        "label": "Database",
        "primary": "MongoDB (MONGO_URL)",
        "free_fallbacks": [
            {
                "name": "MongoDB Atlas (MONGO_BACKUP_URL)",
                "endpoint": None,
                "needs_key": "MONGO_BACKUP_URL",
                "ok": bool(os.environ.get("MONGO_BACKUP_URL")),
                "note": "Atlas M0 free tier — 512MB, shared RAM",
            },
        ],
        "current": "primary",
    },
    # ── Geocoding (for user location features) ────────────────────────────────
    "geocoding": {
        "label": "Geocoding",
        "primary": "Google Maps API",
        "free_fallbacks": [
            {
                "name": "Nominatim (OpenStreetMap)",
                "endpoint": "https://nominatim.openstreetmap.org/search",
                "needs_key": None,
                "ok": True,
                "note": "Free, no key required — 1 req/sec polite usage",
            },
            {
                "name": "OpenStreetMap Static Maps",
                "endpoint": "https://staticmap.openstreetmap.de/staticmap.php",
                "needs_key": None,
                "ok": True,
                "note": "Free static map images — no API key",
            },
        ],
        "current": "nominatim",
    },
    # ── DNS / Domain ──────────────────────────────────────────────────────────
    "dns": {
        "label": "DNS / Tunnel",
        "primary": "Railway domain",
        "free_fallbacks": [
            {
                "name": "Cloudflare Tunnel (free)",
                "endpoint": None,
                "needs_key": "CF_TUNNEL_TOKEN",
                "ok": bool(os.environ.get("CF_TUNNEL_TOKEN")),
                "note": "Cloudflare Tunnel — free tier, no port forwarding needed",
            },
        ],
        "current": "railway",
    },
}


def resolve(service_key: str, primary_is_up: bool = False) -> dict:
    """
    Return the first working fallback for a service.

    Args:
        service_key: key from MATRIX
        primary_is_up: caller passes True only if they have verified the
                       primary provider is configured AND reachable.

    Returns a dict with:
      {name, endpoint, note, tier (primary | free | unavailable)}
    or None if the service_key is unknown.
    """
    entry = MATRIX.get(service_key)
    if entry is None:
        logger.warning("resolve: unknown service_key=%s", service_key)
        return None

    if primary_is_up:
        return {
            "name":     entry["primary"],
            "endpoint": None,
            "note":     None,
            "tier":     "primary",
        }

    # Primary not confirmed up — try free fallbacks in order
    for fb in entry["free_fallbacks"]:
        if fb["ok"]:
            return {
                "name":     fb["name"],
                "endpoint": fb["endpoint"],
                "note":     fb.get("note"),
                "tier":     "free",
            }

    # All fallbacks exhausted
    return {
        "name":     "No fallback available",
        "endpoint": None,
        "note":     f"All fallbacks for {service_key} are unavailable",
        "tier":     "unavailable",
    }


def status_summary() -> dict:
    """Return a snapshot of every service and its current fallback status."""
    result = {}
    for key, entry in MATRIX.items():
        fallbacks = []
        for fb in entry["free_fallbacks"]:
            fallbacks.append({
                "name": fb["name"],
                "endpoint": fb["endpoint"],
                "ok": fb["ok"],
                "note": fb.get("note"),
            })
        result[key] = {
            "label": entry["label"],
            "primary": entry["primary"],
            "current": entry.get("current"),
            "free_fallbacks": fallbacks,
        }
    return result
