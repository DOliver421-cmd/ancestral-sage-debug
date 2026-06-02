"""
llm_gateway.py — Centralized LLM routing for WAI-Institute
============================================================
Single entry point for all persona LLM calls.  Enforces:
  - 10-tier free-first provider fallback chain
  - Per-hour token budget guard  (HOURLY_TOKEN_CAP env var, default 200k)
  - Degraded-state tracking with 5-minute auto-recovery per provider
  - OpenAI-compatible message conversion for all providers

Provider priority (free-first by design — no paid API without D. Oliver consent):
  Tier 1a — Groq / Llama 3.3 70B        (GROQ_API_KEY)              FREE  tool-capable, fastest
  Tier 1b — Cerebras / Llama 3.3 70B    (CEREBRAS_API_KEY)          FREE  tool-capable, fast
  Tier 1c — SambaNova / Llama 3.3 70B   (SAMBANOVA_API_KEY)         FREE  tool-capable, fast
  Tier 2  — Gemini 2.0 Flash Direct     (GEMINI_API_KEY)            FREE  15 RPM, 1M ctx
  Tier 3  — Grok / xAI                  (XAI_API_KEY)               FREE credits, tool-capable
  Tier 4  — Cohere Command R+           (COHERE_API_KEY)            FREE tier, tool-capable
  Tier 5  — Mistral / Mistral-Small     (MISTRAL_API_KEY)           FREE tier (1M tokens/month)
  Tier 6  — Together AI / Llama 3.3 70B (TOGETHER_API_KEY)         FREE $25 credit
  Tier 7  — OpenRouter / Gemini Free    (OPENROUTER_API_KEY)        FREE models available
  Tier 8  — HuggingFace Inference       (HUGGINGFACE_API_KEY)       FREE slow
  Tier 9  — Keyword KB                  (always available)          ZERO no dependency

  ANTHROPIC: DISABLED by owner directive. Anthropic will not be used until
  further notice from D. Oliver. ANTHROPIC_IS_ENABLED must be explicitly set
  to "true" in Railway env vars to re-enable. Default is OFF.

Tool-calling note:
  Groq, Cerebras, SambaNova, Grok, Cohere, Mistral, and Together all support function calling.
  Gemini via OpenAI-compat layer does not receive tool defs here — text-only tier.
"""

import os
import sys
import logging
import time
from typing import Optional

logger = logging.getLogger("lcewai.llm_gateway")

# ── Environment keys (env vars take priority; DB keys fill gaps) ──────────────
# ANTHROPIC: hard-disabled by owner directive. Set ANTHROPIC_IS_ENABLED=true to re-enable.
_ANTHROPIC_IS_ENABLED = os.environ.get("ANTHROPIC_IS_ENABLED", "false").lower() == "true"
ANTHROPIC_API_KEY   = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", "")) if _ANTHROPIC_IS_ENABLED else ""

GROQ_API_KEY        = os.environ.get("GROQ_API_KEY", "")
CEREBRAS_API_KEY    = os.environ.get("CEREBRAS_API_KEY", "")
SAMBANOVA_API_KEY   = os.environ.get("SAMBANOVA_API_KEY", "")
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")
XAI_API_KEY         = os.environ.get("XAI_API_KEY", os.environ.get("GROK_API_KEY", ""))
COHERE_API_KEY      = os.environ.get("COHERE_API_KEY", "")
MISTRAL_API_KEY     = os.environ.get("MISTRAL_API_KEY", "")
TOGETHER_API_KEY    = os.environ.get("TOGETHER_API_KEY", "")
OPENROUTER_API_KEY  = os.environ.get("OPENROUTER_API_KEY", "")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY", os.environ.get("HF_API_KEY", ""))

# ── DB key reload — called at startup and after Provider Gateway saves a key ──
# Maps provider_type values from the Provider Gateway UI to gateway globals.
_PROVIDER_TYPE_TO_GLOBAL = {
    "groq":        "GROQ_API_KEY",
    "cerebras":    "CEREBRAS_API_KEY",
    "sambanova":   "SAMBANOVA_API_KEY",
    "gemini":      "GEMINI_API_KEY",
    "xai":         "XAI_API_KEY",
    "grok":        "XAI_API_KEY",
    "cohere":      "COHERE_API_KEY",
    "mistral":     "MISTRAL_API_KEY",
    "together":    "TOGETHER_API_KEY",
    "openrouter":  "OPENROUTER_API_KEY",
    "huggingface": "HUGGINGFACE_API_KEY",
    # anthropic intentionally omitted — disabled by owner directive
}

async def reload_provider_keys(db) -> int:
    """Read active provider keys from MongoDB and update module globals.
    Env vars always win — DB keys only fill gaps where env var is empty.
    Returns the number of keys loaded from DB."""
    import sys
    enc_secret = os.environ.get("PROVIDER_KEY_ENCRYPTION_SECRET", "")
    if not enc_secret:
        return 0
    try:
        from cryptography.fernet import Fernet
        fernet = Fernet(enc_secret.encode() if isinstance(enc_secret, str) else enc_secret)
    except Exception:
        return 0

    loaded = 0
    module = sys.modules[__name__]
    try:
        # Join provider_keys with providers to get provider_type
        keys = await db.ai_provider_keys.find({}).to_list(200)
        provider_ids = list({k.get("provider_id") for k in keys if k.get("provider_id")})
        providers = {}
        if provider_ids:
            from bson import ObjectId
            oids = []
            for pid in provider_ids:
                try: oids.append(ObjectId(pid))
                except Exception: pass
            if oids:
                async for p in db.ai_providers.find({"_id": {"$in": oids}}):
                    providers[str(p["_id"])] = p.get("provider_type", "")

        for key_doc in keys:
            provider_type = providers.get(str(key_doc.get("provider_id", "")), "")
            global_name = _PROVIDER_TYPE_TO_GLOBAL.get(provider_type.lower(), "")
            if not global_name:
                continue
            # Only fill if env var is currently empty
            if getattr(module, global_name, ""):
                continue
            encrypted = key_doc.get("encrypted_key", "")
            if not encrypted:
                continue
            try:
                plaintext = fernet.decrypt(encrypted.encode() if isinstance(encrypted, str) else encrypted).decode()
                setattr(module, global_name, plaintext)
                loaded += 1
                logger.info("llm_gateway: loaded %s from DB (provider_type=%s)", global_name, provider_type)
            except Exception as e:
                logger.warning("llm_gateway: failed to decrypt key for %s: %s", global_name, e)
    except Exception as e:
        logger.warning("llm_gateway: reload_provider_keys error: %s", e)
    return loaded

# ── Model identifiers ─────────────────────────────────────────────────────────
GROQ_MODEL        = "llama-3.3-70b-versatile"              # free, 128k ctx, tool-calling
GROQ_BASE         = "https://api.groq.com/openai/v1"
CEREBRAS_MODEL    = "llama3.3-70b"                          # free, fast inference
CEREBRAS_BASE     = "https://api.cerebras.ai/v1"
SAMBANOVA_MODEL   = "Meta-Llama-3.3-70B-Instruct"          # free, fast
SAMBANOVA_BASE    = "https://api.sambanova.ai/v1"
GEMINI_MODEL      = "gemini-2.0-flash"                      # free tier, 1M ctx
GEMINI_BASE       = "https://generativelanguage.googleapis.com/v1beta/openai"
XAI_MODEL         = "grok-3-mini"                           # free credits
XAI_BASE          = "https://api.x.ai/v1"
COHERE_MODEL      = "command-r-plus"                        # free tier, tool-calling
MISTRAL_MODEL     = "mistral-small-latest"                  # free tier 1M tokens/month
MISTRAL_BASE      = "https://api.mistral.ai/v1"
TOGETHER_MODEL    = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"  # free model
TOGETHER_BASE     = "https://api.together.xyz/v1"
OPENROUTER_MODEL  = "google/gemini-2.0-flash-lite:free"
OPENROUTER_BASE   = "https://openrouter.ai/api/v1"

# Hourly token cap — configurable in Railway.
# Default 200k/hour ≈ $1/hour max at Sonnet pricing.
# Lower to 50000 during pre-revenue period if desired.
HOURLY_TOKEN_CAP  = int(os.environ.get("HOURLY_TOKEN_CAP", "200000"))

# ── In-process state ──────────────────────────────────────────────────────────
_hour_window_start:  float = time.time()
_hour_tokens_used:   int   = 0
_anthropic_degraded: bool  = False
_anthropic_fail_count: int = 0
_degraded_since:     float = 0.0
_DEGRADED_RESET_SEC:  int  = 300      # re-try Anthropic after 5 minutes


# ── Budget helpers ────────────────────────────────────────────────────────────
def _reset_hour_if_needed() -> None:
    global _hour_window_start, _hour_tokens_used
    if time.time() - _hour_window_start >= 3600:
        _hour_window_start = time.time()
        _hour_tokens_used  = 0


def _record_tokens(n: int) -> None:
    global _hour_tokens_used
    _reset_hour_if_needed()
    _hour_tokens_used += n


def _over_budget() -> bool:
    _reset_hour_if_needed()
    return _hour_tokens_used >= HOURLY_TOKEN_CAP


# ── Anthropic health helpers ──────────────────────────────────────────────────
def _mark_anthropic_fail() -> None:
    global _anthropic_fail_count, _anthropic_degraded, _degraded_since
    _anthropic_fail_count += 1
    if _anthropic_fail_count >= 3:
        _anthropic_degraded = True
        _degraded_since     = time.time()
        logger.warning("LLM Gateway: Anthropic marked DEGRADED after 3 consecutive failures")


def _mark_anthropic_ok() -> None:
    global _anthropic_fail_count, _anthropic_degraded
    _anthropic_fail_count = 0
    _anthropic_degraded   = False


def _anthropic_available() -> bool:
    global _anthropic_degraded, _degraded_since
    if not ANTHROPIC_API_KEY:
        return False
    if _anthropic_degraded:
        if time.time() - _degraded_since > _DEGRADED_RESET_SEC:
            _anthropic_degraded = False
            logger.info("LLM Gateway: Anthropic degraded flag cleared — retrying")
            return True
        return False
    return True


# ── Message format converter (Anthropic → OpenAI-compatible) ─────────────────
def _to_oai_messages(system: str, messages: list[dict]) -> list[dict]:
    """Convert Anthropic-style system + messages list to OpenAI chat format."""
    out = [{"role": "system", "content": system}]
    for m in messages:
        content = m.get("content", "")
        if isinstance(content, list):
            # Extract text from content blocks (tool_result, text blocks)
            content = " ".join(
                b.get("text", "") if isinstance(b, dict) else str(b)
                for b in content
            )
        out.append({"role": m["role"], "content": content})
    return out


# ── OpenAI-compatible HTTP call (used by Groq, Gemini, Grok, OpenRouter) ─────
async def _oai_compat_call(
    base_url: str,
    api_key:  str,
    model:    str,
    system:   str,
    messages: list[dict],
    max_tokens: int,
    tools:    Optional[list],
    extra_headers: Optional[dict] = None,
) -> dict:
    """
    Generic OpenAI-compatible POST /chat/completions call.
    Returns {"text": str, "in_tok": int, "out_tok": int} or raises.
    """
    import httpx

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type":  "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)

    payload: dict = {
        "model":      model,
        "messages":   _to_oai_messages(system, messages),
        "max_tokens": max_tokens,
    }
    # Tool calling in OpenAI format — only pass if provided
    if tools:
        # Convert Anthropic tool schema to OpenAI function-calling format
        payload["tools"] = [
            {
                "type": "function",
                "function": {
                    "name":        t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters":  t.get("input_schema", {}),
                },
            }
            for t in tools
        ]
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    text    = data["choices"][0]["message"].get("content") or ""
    in_tok  = data.get("usage", {}).get("prompt_tokens",     0)
    out_tok = data.get("usage", {}).get("completion_tokens", 0)
    return {"text": text, "in_tok": in_tok, "out_tok": out_tok}


# ── Cohere call (separate SDK, not OpenAI-compatible) ────────────────────────
async def _cohere_call(
    system:     str,
    messages:   list[dict],
    max_tokens: int,
    tools:      Optional[list],
) -> dict:
    """Cohere Command R+ via their Python SDK."""
    import cohere  # type: ignore

    co = cohere.AsyncClientV2(api_key=COHERE_API_KEY)

    cohere_messages = [{"role": "system", "content": system}] + [
        {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else ""}
        for m in messages
    ]

    kwargs: dict = dict(model=COHERE_MODEL, messages=cohere_messages, max_tokens=max_tokens)

    if tools:
        kwargs["tools"] = [
            {
                "type": "function",
                "function": {
                    "name":        t.get("name", ""),
                    "description": t.get("description", ""),
                    "parameters":  t.get("input_schema", {}),
                },
            }
            for t in tools
        ]

    resp = await co.chat(**kwargs)
    text    = resp.message.content[0].text if resp.message.content else ""
    in_tok  = getattr(resp.usage.billed_units, "input_tokens",  0) if resp.usage else 0
    out_tok = getattr(resp.usage.billed_units, "output_tokens", 0) if resp.usage else 0
    return {"text": text, "in_tok": in_tok, "out_tok": out_tok}


# ── KB fallback ───────────────────────────────────────────────────────────────
_KB_FALLBACK = (
    "I'm operating in restricted mode — the AI service is temporarily unavailable. "
    "Your request has been logged. Platform features (modules, labs, certificates, "
    "community) are fully operational. For urgent matters contact WAI-Institute directly."
)

_KB_RESULT = {
    "text":          _KB_FALLBACK,
    "provider":      "kb_fallback",
    "model":         "none",
    "input_tokens":  0,
    "output_tokens": 0,
    "degraded":      True,
}


# ── Primary entry point ───────────────────────────────────────────────────────
async def call_llm(
    system:        str,
    messages:      list[dict],
    model:         str           = "claude-sonnet-4-6",
    max_tokens:    int           = 2048,
    tools:         Optional[list] = None,
    persona_label: str           = "unknown",
) -> dict:
    """
    Unified LLM call with 6-tier fallback chain.

    Returns:
        {
            "text":          str,   response text
            "provider":      str,   which provider served this call
            "model":         str,   model identifier used
            "input_tokens":  int,
            "output_tokens": int,
            "degraded":      bool,  True when not using Anthropic (primary)
            "_raw":          obj,   Anthropic response object (Tier 1 only)
        }
    """
    # ── Budget guard ──────────────────────────────────────────────────────────
    if _over_budget():
        logger.warning(
            "LLM Gateway: hourly cap %d reached (%d used) — routing %s to KB fallback",
            HOURLY_TOKEN_CAP, _hour_tokens_used, persona_label,
        )
        return _KB_RESULT

    # ── Tier 1a: Groq / Llama 3.3 70B (FREE — primary, fastest) ─────────────
    if GROQ_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=GROQ_BASE, api_key=GROQ_API_KEY, model=GROQ_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "groq", "model": GROQ_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": False}
        except Exception as e:
            logger.warning("LLM Gateway T1a Groq failed (%s): %s", persona_label, e)

    # ── Tier 1b: Cerebras / Llama 3.3 70B (FREE — co-primary) ───────────────
    if CEREBRAS_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=CEREBRAS_BASE, api_key=CEREBRAS_API_KEY, model=CEREBRAS_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "cerebras", "model": CEREBRAS_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": False}
        except Exception as e:
            logger.warning("LLM Gateway T1b Cerebras failed (%s): %s", persona_label, e)

    # ── Tier 1c: SambaNova / Llama 3.3 70B (FREE — co-primary) ──────────────
    if SAMBANOVA_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=SAMBANOVA_BASE, api_key=SAMBANOVA_API_KEY, model=SAMBANOVA_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "sambanova", "model": SAMBANOVA_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": False}
        except Exception as e:
            logger.warning("LLM Gateway T1c SambaNova failed (%s): %s", persona_label, e)

    # ── Tier 2: Gemini 2.0 Flash (FREE — 15 RPM, 1M ctx, text-only) ─────────
    if GEMINI_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=GEMINI_BASE, api_key=GEMINI_API_KEY, model=GEMINI_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=None,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "gemini", "model": GEMINI_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T2 Gemini failed (%s): %s", persona_label, e)

    # ── Tier 3: Grok / xAI (FREE credits — tool-capable) ─────────────────────
    if XAI_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=XAI_BASE, api_key=XAI_API_KEY, model=XAI_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "grok", "model": XAI_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T3 Grok failed (%s): %s", persona_label, e)

    # ── Tier 4: Cohere Command R+ (FREE tier — tool-capable) ─────────────────
    if COHERE_API_KEY:
        try:
            result = await _cohere_call(system=system, messages=messages, max_tokens=max_tokens, tools=tools)
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "cohere", "model": COHERE_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T4 Cohere failed (%s): %s", persona_label, e)

    # ── Tier 5: Mistral Small (FREE — 1M tokens/month) ───────────────────────
    if MISTRAL_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=MISTRAL_BASE, api_key=MISTRAL_API_KEY, model=MISTRAL_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "mistral", "model": MISTRAL_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T5 Mistral failed (%s): %s", persona_label, e)

    # ── Tier 6: Together AI / Llama free model ────────────────────────────────
    if TOGETHER_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=TOGETHER_BASE, api_key=TOGETHER_API_KEY, model=TOGETHER_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=None,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "together", "model": TOGETHER_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T6 Together failed (%s): %s", persona_label, e)

    # ── Tier 7: OpenRouter / free Gemini model ────────────────────────────────
    if OPENROUTER_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=OPENROUTER_BASE, api_key=OPENROUTER_API_KEY, model=OPENROUTER_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=None,
                extra_headers={"HTTP-Referer": "https://wai-institute.com", "X-Title": "WAI-Institute"},
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            return {"text": result["text"], "provider": "openrouter", "model": OPENROUTER_MODEL,
                    "input_tokens": result["in_tok"], "output_tokens": result["out_tok"], "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T7 OpenRouter failed (%s): %s", persona_label, e)

    # ── Tier 8: HuggingFace Inference (FREE — slow, last resort before KB) ───
    if HUGGINGFACE_API_KEY:
        try:
            import httpx
            hf_messages = _to_oai_messages(system, messages)
            prompt = "\n".join(
                f"{'[INST]' if m['role']=='user' else ''}{m['content']}{'[/INST]' if m['role']=='user' else ''}"
                for m in hf_messages
            )
            async with httpx.AsyncClient(timeout=30) as http:
                r = await http.post(
                    "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                    headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                    json={"inputs": prompt, "parameters": {"max_new_tokens": max_tokens}},
                )
                r.raise_for_status()
                data = r.json()
            text = data[0].get("generated_text", "").split("[/INST]")[-1].strip() if data else ""
            if text:
                return {"text": text, "provider": "huggingface", "model": "Mistral-7B",
                        "input_tokens": 0, "output_tokens": 0, "degraded": True}
        except Exception as e:
            logger.warning("LLM Gateway T8 HuggingFace failed (%s): %s", persona_label, e)

    # ── ANTHROPIC: DISABLED by owner directive ────────────────────────────────
    # Anthropic will not be called. Set ANTHROPIC_IS_ENABLED=true in Railway
    # env vars only if D. Oliver explicitly authorizes it.
    if _ANTHROPIC_IS_ENABLED and _anthropic_available():
        try:
            import anthropic as _anth
            client = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            kwargs: dict = dict(model=model, max_tokens=max_tokens, system=system, messages=messages)
            if tools:
                kwargs["tools"] = tools
            resp    = await client.messages.create(**kwargs)
            text    = "".join(b.text for b in resp.content if hasattr(b, "text"))
            in_tok  = getattr(resp.usage, "input_tokens",  0)
            out_tok = getattr(resp.usage, "output_tokens", 0)
            _record_tokens(in_tok + out_tok)
            _mark_anthropic_ok()
            logger.warning("LLM Gateway: %s fell through to Anthropic (PAID — owner-authorized)", persona_label)
            return {"text": text, "provider": "anthropic", "model": model,
                    "input_tokens": in_tok, "output_tokens": out_tok, "degraded": True, "_raw": resp}
        except Exception as e:
            logger.warning("LLM Gateway Anthropic failed (%s): %s", persona_label, e)
            _mark_anthropic_fail()

    # ── Tier 9: Keyword KB — always available, zero cost ─────────────────────
    logger.error("LLM Gateway: ALL providers failed for %s — KB fallback", persona_label)
    return _KB_RESULT


# ── Status report ─────────────────────────────────────────────────────────────
def gateway_status() -> dict:
    """Return current gateway health. Exposed via /api/admin/health."""
    _reset_hour_if_needed()
    return {
        "providers": {
            "groq":         {"tier": "1a", "primary": True,  "available": bool(GROQ_API_KEY),         "key_set": bool(GROQ_API_KEY),         "cost": "free",          "tool_calling": True},
            "cerebras":     {"tier": "1b", "primary": True,  "available": bool(CEREBRAS_API_KEY),     "key_set": bool(CEREBRAS_API_KEY),     "cost": "free",          "tool_calling": True},
            "sambanova":    {"tier": "1c", "primary": True,  "available": bool(SAMBANOVA_API_KEY),    "key_set": bool(SAMBANOVA_API_KEY),    "cost": "free",          "tool_calling": True},
            "gemini":       {"tier": 2,    "primary": False, "available": bool(GEMINI_API_KEY),       "key_set": bool(GEMINI_API_KEY),       "cost": "free",          "tool_calling": False},
            "grok":         {"tier": 3,    "primary": False, "available": bool(XAI_API_KEY),          "key_set": bool(XAI_API_KEY),          "cost": "free_credits",  "tool_calling": True},
            "cohere":       {"tier": 4,    "primary": False, "available": bool(COHERE_API_KEY),       "key_set": bool(COHERE_API_KEY),       "cost": "free",          "tool_calling": True},
            "mistral":      {"tier": 5,    "primary": False, "available": bool(MISTRAL_API_KEY),      "key_set": bool(MISTRAL_API_KEY),      "cost": "free_1M/month", "tool_calling": True},
            "together":     {"tier": 6,    "primary": False, "available": bool(TOGETHER_API_KEY),     "key_set": bool(TOGETHER_API_KEY),     "cost": "free_credit",   "tool_calling": False},
            "openrouter":   {"tier": 7,    "primary": False, "available": bool(OPENROUTER_API_KEY),   "key_set": bool(OPENROUTER_API_KEY),   "cost": "free",          "tool_calling": False},
            "huggingface":  {"tier": 8,    "primary": False, "available": bool(HUGGINGFACE_API_KEY),  "key_set": bool(HUGGINGFACE_API_KEY),  "cost": "free_slow",     "tool_calling": False},
            "anthropic":    {"tier": "OFF","primary": False, "available": False,                       "key_set": bool(ANTHROPIC_API_KEY),    "cost": "PAID_DISABLED", "tool_calling": True,
                             "note": "Disabled by owner directive. Set ANTHROPIC_IS_ENABLED=true to re-enable."},
            "kb_fallback":  {"tier": 9,    "primary": False, "available": True,                       "key_set": True,                       "cost": "zero",          "tool_calling": False},
        },
        "anthropic_enabled": _ANTHROPIC_IS_ENABLED,
        "budget": {
            "hourly_cap":     HOURLY_TOKEN_CAP,
            "tokens_used":    _hour_tokens_used,
            "budget_pct":     round(_hour_tokens_used / max(HOURLY_TOKEN_CAP, 1) * 100, 1),
            "over_budget":    _over_budget(),
        },
        "active_free_providers": sum(1 for v in [
            GROQ_API_KEY, CEREBRAS_API_KEY, SAMBANOVA_API_KEY, GEMINI_API_KEY,
            XAI_API_KEY, COHERE_API_KEY, MISTRAL_API_KEY, TOGETHER_API_KEY,
            OPENROUTER_API_KEY, HUGGINGFACE_API_KEY,
        ] if v),
    }
