"""Provider Gateway endpoints for the executive shared AI key pool."""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from roles import ROLE_RANK

logger = logging.getLogger("lcewai.provider_gateway")

router = APIRouter(tags=["provider-gateway"])
db = None
current_user = audit = None

PROVIDERS = {
    "groq": ("Groq", "llama-3.3-70b-versatile", "https://console.groq.com"),
    "cerebras": ("Cerebras", "llama3.3-70b", "https://cloud.cerebras.ai"),
    "gemini": ("Google Gemini", "gemini-2.0-flash", "https://aistudio.google.com"),
    "mistral": ("Mistral", "mistral-small-latest", "https://console.mistral.ai"),
    "cohere": ("Cohere", "command-r-plus", "https://dashboard.cohere.com/api-keys"),
    "together": ("Together AI", "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free", "https://api.together.xyz/settings/api-keys"),
    "xai": ("xAI / Grok", "grok-3-mini", "https://console.x.ai"),
    "openai": ("OpenAI", "gpt-4o-mini", "https://platform.openai.com/api-keys"),
    "deepseek": ("DeepSeek", "deepseek-chat", "https://platform.deepseek.com/api_keys"),
    # ── Payment providers ─────────────────────────────────────────────────────
    # Stored through the same encrypted vault so the owner can link payment
    # keys from the exec Provider Gateway and have them take effect immediately.
    "stripe": ("Stripe", "checkout", "https://dashboard.stripe.com/apikeys"),
    "lemon_squeezy": ("Lemon Squeezy", "checkout", "https://app.lemonsqueezy.com/settings/api"),
    "gumroad": ("Gumroad", "checkout", "https://app.gumroad.com/settings"),
    # ── AI providers previously served by billing.py quick-setup (merged here) ──
    "sambanova": ("SambaNova", "Llama-3.3-70B", "https://sambanova.ai"),
    "openrouter": ("OpenRouter", "free models", "https://openrouter.ai"),
    "huggingface": ("HuggingFace", "inference", "https://huggingface.co"),
    # ── Zero-cost failover expansion (owner decision 2026-10-12) ─────────────
    # All five were verified from this workspace with NO credentials: NVIDIA
    # NIM, DeepInfra and Novita answer /models with a real OpenAI-format
    # catalogue (80 / 177 / 94 models); Hyperbolic and Perplexity answer on
    # their endpoints and are validated for real at key-save time. Each is
    # email sign-up, no card, $0 to the platform, usable from Tampa FL.
    "nvidia": ("NVIDIA NIM", "deepseek-v4.1-flash", "https://build.nvidia.com"),
    "deepinfra": ("DeepInfra", "Llama-3.3-70B-Instruct-Turbo", "https://deepinfra.com"),
    "novita": ("Novita AI", "llama-3.3-70b-instruct", "https://novita.ai"),
    "hyperbolic": ("Hyperbolic", "Llama-3.3-70B-Instruct", "https://hyperbolic.xyz"),
    "perplexity": ("Perplexity", "sonar", "https://perplexity.ai"),
    # ── Specialty media keys (owner decision 2026-10-12) ─────────────────────
    # Zero-cost media providers: stored in the same encrypted vault and shown
    # in the exec console with real status. The image/sound/video generation
    # endpoints land in the specialty-tools release (G5); storing the key now
    # is what makes that a paste-free step later. Every entry below is a real,
    # reachable provider (checked 2026-10-12); anything unverified was NOT
    # added — see docs/SESSION_HANDOFF.md.
    "pollinations": ("Pollinations.ai", "flux image (no key needed)", "https://pollinations.ai"),
    "elevenlabs": ("ElevenLabs", "tts (10k chars/mo free)", "https://elevenlabs.io"),
    "deepgram": ("Deepgram", "stt + tts aura", "https://deepgram.com"),
    "luma": ("Luma AI", "dream machine video", "https://lumalabs.ai"),
    "replicate": ("Replicate", "video + multimodal", "https://replicate.com"),
    "fal": ("Fal.ai", "ltx-video / cogvideox", "https://fal.ai"),
}

class QuickSetupRequest(BaseModel):
    provider_type: str
    api_key: str
    # Optional second credential for dual-key payment providers:
    #   stripe         → publication key
    #   lemon_squeezy  → store id
    secondary_key: Optional[str] = ""
    # Optional third credential — stripe webhook secret (whsec_…).
    # Without it the checkout works but the webhook 404s and buyers never
    # get their order recorded, so the exec panel requires it for Stripe.
    third_key: Optional[str] = ""
    # Opt-in live verification: when true the saved key is exercised with a
    # minimal one-token provider call before the save reports success.
    # Default false so existing callers keep the current save path.
    test_key: bool = False

async def _user(authorization: Optional[str] = Header(None)):
    return await current_user(authorization)

def _exec(user):
    if ROLE_RANK.get(user.role, 0) < ROLE_RANK["executive_admin"]:
        raise HTTPException(403, "Executive access required.")
    return user

def bind(_db, _current_user, _audit):
    global db, current_user, audit
    db, current_user, audit = _db, _current_user, _audit

def _fernet():
    try:
        import keyvault
        return keyvault.get_fernet()
    except Exception:
        return None

def _mask(value):
    return "••••" + value[-4:] if len(value) >= 4 else "••••"

async def _provider_id(provider_type):
    doc = await db.api_providers.find_one({"provider_type": provider_type})
    if doc:
        return doc.get("id")
    provider_id = str(uuid.uuid4())
    await db.api_providers.insert_one({
        "id": provider_id, "provider_type": provider_type,
        "name": PROVIDERS[provider_type][0], "active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return provider_id

@router.get("/providers/quick-setup/status")
async def quick_setup_status(user=Depends(_user)):
    _exec(user)
    configured_env = {
        "groq": bool(os.environ.get("GROQ_API_KEY", "").strip()),
        "cerebras": bool(os.environ.get("CEREBRAS_API_KEY", "").strip()),
        "gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
        "mistral": bool(os.environ.get("MISTRAL_API_KEY", "").strip()),
        "cohere": bool(os.environ.get("COHERE_API_KEY", "").strip()),
        "together": bool(os.environ.get("TOGETHER_API_KEY", "").strip()),
        "xai": bool(os.environ.get("XAI_API_KEY", os.environ.get("GROK_API_KEY", "")).strip()),
        "openai": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
        "deepseek": bool(os.environ.get("AI_PROVIDER_DEEPSEEK_KEY", "").strip()),
        "stripe": bool(os.environ.get("STRIPE_SECRET_KEY", "").strip() and os.environ.get("STRIPE_PUBLISHABLE_KEY", "").strip()),
        "lemon_squeezy": bool(os.environ.get("LEMON_SQUEEZY_API_KEY", "").strip() and os.environ.get("LEMON_SQUEEZY_STORE_ID", "").strip() and os.environ.get("LEMON_SQUEEZY_WEBHOOK_SECRET", "").strip()),
        "gumroad": bool(os.environ.get("GUMROAD_API_KEY", "").strip()),
    }
    if db is None:
        return {
            provider_type: {
                "configured": configured_env.get(provider_type, False),
                "key_masked": None,
                "source": "env" if configured_env.get(provider_type, False) else None,
            }
            for provider_type in PROVIDERS
        }

    providers = {}
    async for p in db.api_providers.find({"provider_type": {"$in": list(PROVIDERS)}}):
        providers[p.get("provider_type")] = p.get("id")
    keys = {}
    if providers:
        async for k in db.api_keys.find({"provider_id": {"$in": list(providers.values())}, "status": "active"}):
            for provider_type, provider_id in providers.items():
                if k.get("provider_id") == provider_id:
                    keys[provider_type] = k
    return {
        provider_type: {
            "configured": provider_type in keys or configured_env.get(provider_type, False),
            "key_masked": (keys[provider_type].get("key_masked") if provider_type in keys else None),
            "source": "gateway" if provider_type in keys else ("env" if configured_env.get(provider_type, False) else None),
        }
        for provider_type in PROVIDERS
    }

@router.post("/providers/quick-setup")
async def quick_setup(body: QuickSetupRequest, user=Depends(_user)):
    _exec(user)
    if db is None:
        raise HTTPException(503, "Provider storage is unavailable. The key was not saved.")
    provider_type = body.provider_type.strip().lower()
    api_key = body.api_key.strip()
    secondary = (body.secondary_key or "").strip()
    if provider_type not in PROVIDERS:
        raise HTTPException(400, "Unsupported provider.")
    if not api_key:
        raise HTTPException(400, "API key cannot be empty.")
    # Dual-key providers require both credentials.
    if provider_type == "stripe" and not secondary:
        raise HTTPException(400, "Stripe needs BOTH the secret key and the publishable key.")
    if provider_type == "stripe" and not (body.third_key or "").strip():
        raise HTTPException(400, "Stripe also needs the webhook secret (whsec_…) so paid orders can be recorded.")
    if provider_type == "lemon_squeezy" and not secondary:
        raise HTTPException(400, "Lemon Squeezy needs BOTH the API key and the store id.")
    if provider_type == "lemon_squeezy" and not (body.third_key or "").strip():
        raise HTTPException(400, "Lemon Squeezy also needs the webhook secret (from Settings → Webhooks) so paid orders can be fulfilled.")
    fernet = _fernet()
    if fernet is None:
        raise HTTPException(503, "Provider key encryption is not configured on the server.")
    provider_id = await _provider_id(provider_type)
    now = datetime.now(timezone.utc).isoformat()
    encrypted = fernet.encrypt(api_key.encode()).decode()
    upd: dict = {
        "provider_id": provider_id,
        "encrypted_key": encrypted,
        "key_masked": _mask(api_key),
        "status": "active",
        "updated_at": now,
    }
    if secondary:
        upd["second_encrypted_key"] = fernet.encrypt(secondary.encode()).decode()
        upd["second_masked"] = _mask(secondary)
    third = (body.third_key or "").strip()
    if third:
        upd["third_encrypted_key"] = fernet.encrypt(third.encode()).decode()
        upd["third_masked"] = _mask(third)
    await db.api_keys.update_one(
        {"provider_id": provider_id},
        {"$set": upd, "$setOnInsert": {"id": str(uuid.uuid4()), "created_at": now}},
        upsert=True,
    )
    # The key is now durably stored. The in-memory reload below is a
    # convenience (the key also loads at startup): a reload failure must never
    # report "not saved" for a key that IS saved, so it is logged and the
    # save still reports success.
    try:
        if provider_type in (
            "groq", "cerebras", "gemini", "mistral", "cohere", "together", "xai",
            "openai", "deepseek", "sambanova", "openrouter", "huggingface",
            # Zero-cost expansion (2026-10-12) + specialty media keys: reload the
            # gateway globals so the pasted key serves the next request. Types the
            # gateway does not map are skipped inside reload_provider_keys.
            "nvidia", "deepinfra", "novita", "hyperbolic", "perplexity",
            "pollinations", "elevenlabs", "deepgram", "luma", "replicate", "fal",
        ):
            from ai.llm_gateway import reload_provider_keys
            await reload_provider_keys(db)
        else:
            # Payment provider — reload so the newly pasted key takes effect now.
            from routers.payments import reload_payment_keys
            await reload_payment_keys(db)
    except Exception:
        logger.exception("provider key saved but the in-memory reload failed for %s", provider_type)
    await audit(user.id, "provider_gateway.key_saved", meta={"provider": provider_type})
    result: dict = {"provider_type": provider_type, "configured": True, "key_masked": _mask(api_key)}
    if body.test_key:
        result["test"] = await _live_key_test(provider_type, api_key)
    return result


async def _live_key_test(provider_type: str, api_key: str) -> dict:
    """Exercise a provider key with a minimal one-token call.

    A key that authenticates is worth more than a key that merely encrypts:
    quick-setup used to persist any non-empty string and report "configured",
    which is how dead keys reached the live gateway. The test never blocks a
    save — the result rides along in the response so the exec can see whether
    the pasted key actually works.
    """
    import time as _time

    try:
        import httpx as _httpx

        base = _provider_base(provider_type)
        if not base:
            return {"ok": None, "skipped": "no OpenAI-compatible test endpoint for this provider"}
        start = _time.monotonic()
        async with _httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "content-type": "application/json"},
                json={"model": _probe_model(provider_type), "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]},
            )
        latency_ms = round((_time.monotonic() - start) * 1000)
        # 401/403 is the whole point of the test: the key authenticated or it
        # did not. "Reachable" is not "working" for a credential probe.
        ok = 200 <= r.status_code < 500 and r.status_code not in (401, 403, 429)
        return {"ok": ok, "status_code": r.status_code, "latency_ms": latency_ms}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _provider_base(provider_type: str) -> str:
    """OpenAI-compatible base URL per provider; empty when none applies."""
    bases = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "xai": "https://api.x.ai/v1",
        "mistral": "https://api.mistral.ai/v1",
        "nvidia": "https://integrate.api.nvidia.com/v1",
        "hyperbolic": "https://api.hyperbolic.xyz/v1",
        "novita": "https://api.novita.ai/v3/openai",
        "deepinfra": "https://api.deepinfra.com/v1/openai",
        "sambanova": "https://api.sambanova.ai/v1",
        "cerebras": "https://api.cerebras.ai/v1",
        "huggingface": "https://api-inference.huggingface.co/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    }
    return bases.get(provider_type, "")


def _probe_model(provider_type: str) -> str:
    """Cheapest model per provider — the probe only needs one token back."""
    models = {
        "openai": "gpt-4o-mini",
        "groq": "llama-3.1-8b-instant",
        "deepseek": "deepseek-chat",
        "together": "meta-llama/Llama-3.2-3B-Instruct-Turbo",
        "openrouter": "meta-llama/llama-3.2-3b-instruct",
        "xai": "grok-2-latest",
        "mistral": "mistral-small-latest",
        "nvidia": "meta/llama-3.1-8b-instruct",
        "hyperbolic": "meta-llama/Llama-3.2-3B-Instruct",
        "novita": "meta-llama/llama-3.1-8b-instruct",
        "deepinfra": "meta-llama/Llama-3.2-3B-Instruct",
        "sambanova": "Meta-Llama-3.1-8B-Instruct",
        "cerebras": "llama3.1-8b",
        "huggingface": "meta-llama/Llama-3.2-3B-Instruct",
        "gemini": "gemini-2.0-flash",
    }
    return models.get(provider_type, "gpt-4o-mini")

@router.patch("/providers/keys/by-provider/{provider_type}/status")
async def provider_key_status(provider_type: str, body: dict, user=Depends(_user)):
    """Enable or disable the encrypted quick-setup key for one provider."""
    _exec(user)
    provider_type = provider_type.strip().lower()
    if provider_type not in PROVIDERS:
        raise HTTPException(404, "Unsupported provider.")
    status = body.get("status")
    if status not in ("active", "inactive"):
        raise HTTPException(400, "status must be active or inactive")
    provider = await db.api_providers.find_one({"provider_type": provider_type}, {"id": 1})
    if not provider:
        raise HTTPException(404, "Provider key not found")
    result = await db.api_keys.update_one(
        {"provider_id": provider.get("id")},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(404, "Provider key not found")
    if provider_type in ("groq", "cerebras", "gemini", "mistral", "cohere", "together", "xai", "openai", "deepseek", "sambanova", "openrouter", "huggingface"):
        from ai.llm_gateway import reload_provider_keys
        await reload_provider_keys(db)
    await audit(user.id, "provider_gateway.key_status_changed", meta={"provider": provider_type, "status": status})
    return {"provider_type": provider_type, "status": status}


@router.delete("/providers/keys/by-provider/{provider_type}")
async def provider_key_revoke(provider_type: str, user=Depends(_user)):
    """Permanently remove the encrypted quick-setup key for one provider."""
    _exec(user)
    provider_type = provider_type.strip().lower()
    if provider_type not in PROVIDERS:
        raise HTTPException(404, "Unsupported provider.")
    provider = await db.api_providers.find_one({"provider_type": provider_type}, {"id": 1})
    if not provider:
        raise HTTPException(404, "Provider key not found")
    result = await db.api_keys.delete_one({"provider_id": provider.get("id")})
    if result.deleted_count == 0:
        raise HTTPException(404, "Provider key not found")
    if provider_type in ("groq", "cerebras", "gemini", "mistral", "cohere", "together", "xai", "openai", "deepseek", "sambanova", "openrouter", "huggingface"):
        from ai.llm_gateway import reload_provider_keys
        await reload_provider_keys(db)
    await audit(user.id, "provider_gateway.key_revoked", meta={"provider": provider_type})
    return {"provider_type": provider_type, "revoked": True}


@router.get("/providers/usage-log")
async def usage_log(limit: int = 50, user=Depends(_user)):
    """Provider usage log for the exec Provider Gateway "Usage" tab.

    Reads db.ai_usage_log — the collection that is actually written, in seven
    places in routers/ai.py. This handler previously read db.provider_usage,
    which NO code in this repository ever writes to, so it could only ever
    return an empty list.

    That defect was masked: this path was registered three times
    (routers/billing.py twice, plus here) and FastAPI serves the
    first-registered handler, which was routers/billing.py's copy reading
    ai_usage_log. The duplicates have been removed and this is now the single
    owner, so the collection had to be corrected here or the tab would have gone
    permanently blank. Verify by execution after changing this.

    `limit` is honored (the removed billing.py handler ignored it and always
    returned up to 500 records, so the frontend's ?limit=50 had no effect).
    """
    _exec(user)
    if db is None:
        raise HTTPException(503, "Provider usage storage is unavailable.")
    capped = min(max(limit, 1), 200)
    docs = await db.ai_usage_log.find({}, {"_id": 0}).sort("created_at", -1).to_list(length=capped)
    # created_at may be a datetime or an ISO string depending on the writer.
    for d in docs:
        if hasattr(d.get("created_at"), "isoformat"):
            d["created_at"] = d["created_at"].isoformat()
    return docs
