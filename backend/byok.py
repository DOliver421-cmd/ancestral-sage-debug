"""byok.py — $3 Bring Your Own Key (BYOK) for WAI-Institute.

Every user profile can activate a $3 BYOK entitlement and attach their own API
key from one of three FREE providers. When the LLM gateway routes that user's
AI requests, it uses the user's key FIRST — so the platform pays nothing for
that user's generation.

The three providers are deliberately the ones with a genuine free tier that
require NO credit card / billing method to sign up:

  - Groq      (https://console.groq.com)     — fast free tier
  - Cerebras  (https://cloud.cerebras.ai)    — free tier, fast inference
  - Gemini    (https://aistudio.google.com)  — free tier, 15 RPM, 1M context

All three expose an OpenAI-compatible /chat/completions endpoint, so a single
HTTP call path serves every provider.

Key storage: `db.user_byok_keys` — encrypted at rest with the same Fernet secret
the Provider Gateway uses (`PROVIDER_KEY_ENCRYPTION_SECRET`). Keys are NEVER
returned to the frontend after save; only a masked suffix is shown.

Entitlement: stored on the user document as `byok_enabled` + `byok_activated_at`.
The `POST /api/byok/activate` endpoint flips the flag and is the integration
point for the payment processor (see docs/ADMIN-MANUAL.md §7).
"""

import base64
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.byok")

# Configurable; defaults to the owner's $3 price point.
BYOK_PRICE_USD = int(os.environ.get("BYOK_PRICE_USD", "3"))

# BYOK is a $3 one-time fee for users BELOW instructor tier. Instructors and
# above (instructor, admin, executive_admin, creative_partner) get BYOK free.
_ROLE_RANK = {"student": 1, "instructor": 2, "admin": 3, "executive_admin": 4, "creative_partner": 2}


def byok_price_for(role: Optional[str]) -> int:
    """$3 for users below instructor tier; free (0) at instructor tier and above."""
    if role and _ROLE_RANK.get(role, 0) >= 2:
        return 0
    return BYOK_PRICE_USD

# ── Approved providers (free tier, no credit card required) ──────────────────

BYOK_PROVIDERS = {
    "groq": {
        "label": "Groq",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "signup_url": "https://console.groq.com",
        "free_tier": "Fast free tier — no credit card required",
    },
    "cerebras": {
        "label": "Cerebras",
        "base_url": "https://api.cerebras.ai/v1",
        "model": "llama3.3-70b",
        "signup_url": "https://cloud.cerebras.ai",
        "free_tier": "Free tier — no credit card required",
    },
    "gemini": {
        "label": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.0-flash",
        "signup_url": "https://aistudio.google.com",
        "free_tier": "Free tier (15 RPM, 1M context) — no credit card required",
    },
}

# Priority order when a user has more than one key configured.
_PROVIDER_PRIORITY = ("groq", "cerebras", "gemini")


# ── Encryption (same secret + scheme as the Provider Gateway) ────────────────

_ENCRYPT_SECRET = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
_FERNET = None


def _get_fernet():
    """Return a cached Fernet instance, or False when encryption is unavailable."""
    global _FERNET
    if _FERNET is not None:
        return _FERNET
    _FERNET = False
    if _ENCRYPT_SECRET:
        try:
            from cryptography.fernet import Fernet
            # Prefer a valid Fernet key; derive one from an arbitrary string otherwise.
            try:
                _FERNET = Fernet(_ENCRYPT_SECRET.encode())
            except Exception:
                _kb = (_ENCRYPT_SECRET.encode() * 3)[:32]
                _FERNET = Fernet(base64.urlsafe_b64encode(_kb))
        except Exception as _e:
            logger.warning("byok: Fernet init failed — keys will be stored plaintext: %s", _e)
            _FERNET = False
    return _FERNET


def encrypt_key(plaintext: str) -> str:
    fernet = _get_fernet()
    if fernet:
        return fernet.encrypt(plaintext.encode()).decode()
    return plaintext  # no secret configured — stored plaintext (warned at save)


def decrypt_key(ciphertext: str) -> str:
    fernet = _get_fernet()
    if fernet:
        try:
            return fernet.decrypt(ciphertext.encode()).decode()
        except Exception:
            return ciphertext  # already plaintext or decryption failed
    return ciphertext


def mask_key(key: str) -> str:
    if not key:
        return ""
    return f"••••{key[-4:]}" if len(key) >= 4 else "••••"


def provider_route(provider: str):
    """Return (base_url, model) for a provider, or None if unknown."""
    spec = BYOK_PROVIDERS.get(provider)
    if not spec:
        return None
    return spec["base_url"], spec["model"]


# ── Entitlement + key store helpers ──────────────────────────────────────────

async def activate_byok(db, user_id: str, role: Optional[str] = None) -> dict:
    """Flip the $3 BYOK entitlement on for a user.

    Users below instructor tier pay BYOK_PRICE_USD. Instructor tier and above
    (instructor, admin, executive_admin, creative_partner) get BYOK free — the
    entitlement is granted at price 0.

    NOTE: this is the post-payment hook. Production should call it only after a
    successful Stripe/Lemon Squeezy checkout (see docs/ADMIN-MANUAL.md §7).
    """
    price = byok_price_for(role)
    now = datetime.now(timezone.utc).isoformat()
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"byok_enabled": True, "byok_activated_at": now}},
    )
    return {"enabled": True, "price_usd": price, "free_for_role": price == 0, "activated_at": now}


async def get_byok_status(db, user_id: str, role: Optional[str] = None) -> dict:
    """Entitlement + per-provider key status for the current user (no raw keys)."""
    user_doc = await db.users.find_one(
        {"id": user_id}, {"_id": 0, "byok_enabled": 1, "byok_activated_at": 1}
    )
    price = byok_price_for(role)
    key_docs = await db.user_byok_keys.find(
        {"user_id": user_id}, {"_id": 0, "encrypted_key": 0}
    ).sort("created_at", -1).to_list(length=10)
    configured = {k["provider"]: k for k in key_docs if k.get("provider") in BYOK_PROVIDERS}

    providers = []
    for p, spec in BYOK_PROVIDERS.items():
        doc = configured.get(p) or {}
        providers.append({
            "key": p,
            "label": spec["label"],
            "signup_url": spec["signup_url"],
            "free_tier": spec["free_tier"],
            "model": spec["model"],
            "configured": p in configured,
            "masked": doc.get("key_masked"),
            "active": doc.get("active", True),
            "last_used_at": doc.get("last_used_at"),
            "usage_count": doc.get("usage_count", 0),
        })

    return {
        "price_usd": price,
        "free_for_role": price == 0,
        "enabled": bool(user_doc.get("byok_enabled")) if user_doc else False,
        "activated_at": (user_doc or {}).get("byok_activated_at"),
        "providers": providers,
    }


async def save_byok_key(db, user_id: str, provider: str, plaintext_key: str) -> dict:
    """Encrypt and store a user's BYOK key for the given provider."""
    if provider not in BYOK_PROVIDERS:
        raise ValueError("unknown_byok_provider")
    plaintext_key = (plaintext_key or "").strip()
    if not plaintext_key:
        raise ValueError("empty_key")
    if not _get_fernet():
        logger.warning("byok: storing key plaintext for user %s (PROVIDER_KEY_ENCRYPTION_SECRET unset)", user_id)

    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "user_id": user_id,
        "provider": provider,
        "encrypted_key": encrypt_key(plaintext_key),
        "key_masked": mask_key(plaintext_key),
        "active": True,
        "updated_at": now,
        "last_used_at": None,
        "usage_count": 0,
    }
    await db.user_byok_keys.update_one(
        {"user_id": user_id, "provider": provider},
        {"$set": doc, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    return {"provider": provider, "masked": mask_key(plaintext_key)}


async def remove_byok_key(db, user_id: str, provider: str) -> bool:
    if provider not in BYOK_PROVIDERS:
        raise ValueError("unknown_byok_provider")
    result = await db.user_byok_keys.delete_one({"user_id": user_id, "provider": provider})
    return result.deleted_count > 0


async def test_byok_key(provider: str, plaintext_key: str) -> dict:
    """Make a minimal 1-token call to verify a key works. Never stores the key."""
    route = provider_route(provider)
    if not route:
        return {"ok": False, "error": f"Unknown provider: {provider}"}
    base_url, model = route
    import time

    import httpx

    t0 = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=15) as http:
            r = await http.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {plaintext_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Ping"}],
                    "max_tokens": 1,
                },
            )
        data = {}
        try:
            data = r.json()
        except Exception:
            pass
        if r.status_code >= 400:
            err = data.get("error")
            if isinstance(err, dict):
                err = err.get("message") or err.get("type") or str(err)
            return {"ok": False, "status_code": r.status_code, "error": str(err or r.text)[:300]}
        latency_ms = int((time.perf_counter() - t0) * 1000)
        return {"ok": True, "latency_ms": latency_ms, "model": model}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:300]}


async def resolve_byok(user_id: Optional[str]) -> Optional[dict]:
    """Resolve a user's active BYOK key for the LLM gateway.

    Returns {"provider": str, "key": str} only when the user has BOTH the $3
    entitlement enabled AND at least one active key. Returns None otherwise.
    """
    if not user_id:
        return None
    try:
        from deps import get_db

        db = get_db()
    except Exception:
        return None
    if db is None:
        return None

    try:
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0, "byok_enabled": 1})
    except Exception:
        return None
    if not user_doc or not user_doc.get("byok_enabled"):
        return None

    try:
        key_docs = await db.user_byok_keys.find(
            {"user_id": user_id, "active": True}, {"_id": 0}
        ).to_list(length=10)
    except Exception:
        return None

    by_provider = {k["provider"]: k for k in key_docs if k.get("provider") in BYOK_PROVIDERS}
    for p in _PROVIDER_PRIORITY:
        doc = by_provider.get(p)
        if not doc:
            continue
        plaintext = decrypt_key(doc.get("encrypted_key", ""))
        if plaintext:
            return {"provider": p, "key": plaintext}
    return None
