"""Provider Gateway endpoints for the executive shared AI key pool."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from roles import ROLE_RANK

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
        "lemon_squeezy": bool(os.environ.get("LEMON_SQUEEZY_API_KEY", "").strip() and os.environ.get("LEMON_SQUEEZY_STORE_ID", "").strip()),
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
    if provider_type in ("groq", "cerebras", "gemini", "mistral", "cohere", "together", "xai", "openai", "deepseek"):
        from ai.llm_gateway import reload_provider_keys
        await reload_provider_keys(db)
    else:
        # Payment provider — reload so the newly pasted key takes effect now.
        from routers.payments import reload_payment_keys
        await reload_payment_keys(db)
    await audit(user.id, "provider_gateway.key_saved", meta={"provider": provider_type})
    return {"provider_type": provider_type, "configured": True, "key_masked": _mask(api_key)}

@router.get("/providers/usage-log")
async def usage_log(limit: int = 50, user=Depends(_user)):
    _exec(user)
    if db is None:
        raise HTTPException(503, "Provider usage storage is unavailable.")
    return await db.provider_usage.find({}).sort("created_at", -1).to_list(length=min(max(limit, 1), 200))
