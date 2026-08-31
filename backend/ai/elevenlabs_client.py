"""
ElevenLabs Client — DISABLED
==============================
ElevenLabs is no longer used. All personas use browser TTS (free, zero cost).

This module is kept as a stub so existing imports don't break.
All functions return None or no-op.
"""


async def speak(text, persona=None, voice_id=None, db=None):
    """No-op — ElevenLabs disabled. Returns None (caller falls back to browser TTS)."""
    return None


def get_budget_status():
    """No budget to track — ElevenLabs disabled."""
    return {"used": 0, "cap": 0, "remaining": 0, "disabled": True}


async def synthesize(text, voice_id=None, db=None):
    """No-op — returns None."""
    return None
