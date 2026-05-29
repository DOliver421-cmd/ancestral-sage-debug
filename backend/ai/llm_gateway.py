"""
llm_gateway.py — Centralized LLM routing for WAI-Institute
============================================================
Single entry point for all persona LLM calls.  Enforces:
  - 6-tier free-first provider fallback chain
  - Per-hour token budget guard  (HOURLY_TOKEN_CAP env var, default 200k)
  - Anthropic degraded-state tracking with 5-minute auto-recovery
  - OpenAI-compatible message conversion for non-Anthropic providers

Provider priority (free tiers used wherever available):
  Tier 1 — Anthropic Claude          (ANTHROPIC_API_KEY)         paid primary
  Tier 2 — Groq / Llama 3.3 70B      (GROQ_API_KEY)              free, tool-capable, fastest
  Tier 3 — Gemini 2.0 Flash Direct   (GEMINI_API_KEY)            free, 15 RPM, 1M ctx
  Tier 4 — Grok / xAI                (XAI_API_KEY)               free credits, tool-capable
  Tier 5 — Cohere Command R+         (COHERE_API_KEY)            free tier, tool-capable
  Tier 6 — Keyword KB                (always available)          zero cost, zero dependency

Tool-calling note:
  Anthropic, Groq (Llama 3.3), Grok, and Cohere Command R+ all support function
  calling.  Gemini Direct does not receive tool definitions via this gateway
  (the Google AI SDK has a different tool format — Tier 3 is text-only fallback).
  If tools are required and Anthropic is down, Groq is the primary tool-capable
  fallback.
"""

import os
import sys
import logging
import time
from typing import Optional

logger = logging.getLogger("lcewai.llm_gateway")

# ── Environment keys ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
XAI_API_KEY        = os.environ.get("XAI_API_KEY", os.environ.get("GROK_API_KEY", ""))
COHERE_API_KEY     = os.environ.get("COHERE_API_KEY", "")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")   # kept as bonus Gemini path

# ── Model identifiers ─────────────────────────────────────────────────────────
GROQ_MODEL        = "llama-3.3-70b-versatile"       # free, 128k ctx, tool-calling
GROQ_BASE         = "https://api.groq.com/openai/v1"
GEMINI_MODEL      = "gemini-2.0-flash"               # free tier, 1M ctx
GEMINI_BASE       = "https://generativelanguage.googleapis.com/v1beta/openai"
XAI_MODEL         = "grok-3-mini"                    # free tier
XAI_BASE          = "https://api.x.ai/v1"
COHERE_MODEL      = "command-r-plus"                 # free tier, tool-calling
OPENROUTER_MODEL  = "google/gemini-2.0-flash-lite-preview-02-05:free"
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

    # ── Tier 1: Anthropic Claude ──────────────────────────────────────────────
    if _anthropic_available():
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
            return {
                "text":          text,
                "provider":      "anthropic",
                "model":         model,
                "input_tokens":  in_tok,
                "output_tokens": out_tok,
                "degraded":      False,
                "_raw":          resp,
            }
        except Exception as e:
            logger.warning("LLM Gateway T1 Anthropic failed (%s): %s", persona_label, e)
            _mark_anthropic_fail()

    # ── Tier 2: Groq / Llama 3.3 70B (free, fastest, tool-capable) ───────────
    if GROQ_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=GROQ_BASE, api_key=GROQ_API_KEY, model=GROQ_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            logger.info("LLM Gateway: %s served via Groq/Llama3.3 (free)", persona_label)
            return {
                "text":          result["text"],
                "provider":      "groq",
                "model":         GROQ_MODEL,
                "input_tokens":  result["in_tok"],
                "output_tokens": result["out_tok"],
                "degraded":      True,
            }
        except Exception as e:
            logger.warning("LLM Gateway T2 Groq failed (%s): %s", persona_label, e)

    # ── Tier 3: Gemini 2.0 Flash Direct (free, 15 RPM, text-only fallback) ───
    if GEMINI_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=GEMINI_BASE, api_key=GEMINI_API_KEY, model=GEMINI_MODEL,
                system=system, messages=messages, max_tokens=max_tokens,
                tools=None,   # Gemini via OpenAI-compat layer doesn't support tool defs here
                extra_headers={},
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            logger.info("LLM Gateway: %s served via Gemini Direct (free)", persona_label)
            return {
                "text":          result["text"],
                "provider":      "gemini",
                "model":         GEMINI_MODEL,
                "input_tokens":  result["in_tok"],
                "output_tokens": result["out_tok"],
                "degraded":      True,
            }
        except Exception as e:
            logger.warning("LLM Gateway T3 Gemini failed (%s): %s", persona_label, e)

    # ── Tier 4: Grok / xAI (free credits, tool-capable) ─────────────────────
    if XAI_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=XAI_BASE, api_key=XAI_API_KEY, model=XAI_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            logger.info("LLM Gateway: %s served via Grok/xAI (free credits)", persona_label)
            return {
                "text":          result["text"],
                "provider":      "grok",
                "model":         XAI_MODEL,
                "input_tokens":  result["in_tok"],
                "output_tokens": result["out_tok"],
                "degraded":      True,
            }
        except Exception as e:
            logger.warning("LLM Gateway T4 Grok failed (%s): %s", persona_label, e)

    # ── Tier 5: Cohere Command R+ (free tier, tool-capable) ──────────────────
    if COHERE_API_KEY:
        try:
            result = await _cohere_call(
                system=system, messages=messages, max_tokens=max_tokens, tools=tools,
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            logger.info("LLM Gateway: %s served via Cohere Command R+ (free)", persona_label)
            return {
                "text":          result["text"],
                "provider":      "cohere",
                "model":         COHERE_MODEL,
                "input_tokens":  result["in_tok"],
                "output_tokens": result["out_tok"],
                "degraded":      True,
            }
        except Exception as e:
            logger.warning("LLM Gateway T5 Cohere failed (%s): %s", persona_label, e)

    # ── Bonus: OpenRouter (if key set — additional Gemini path) ──────────────
    if OPENROUTER_API_KEY:
        try:
            result = await _oai_compat_call(
                base_url=OPENROUTER_BASE, api_key=OPENROUTER_API_KEY,
                model=OPENROUTER_MODEL,
                system=system, messages=messages, max_tokens=max_tokens, tools=None,
                extra_headers={
                    "HTTP-Referer": "https://wai-institute.com",
                    "X-Title":      "WAI-Institute",
                },
            )
            _record_tokens(result["in_tok"] + result["out_tok"])
            logger.info("LLM Gateway: %s served via OpenRouter/Gemini (free)", persona_label)
            return {
                "text":          result["text"],
                "provider":      "openrouter",
                "model":         OPENROUTER_MODEL,
                "input_tokens":  result["in_tok"],
                "output_tokens": result["out_tok"],
                "degraded":      True,
            }
        except Exception as e:
            logger.warning("LLM Gateway OpenRouter failed (%s): %s", persona_label, e)

    # ── Tier 6: Keyword KB — always available, zero cost ─────────────────────
    logger.error("LLM Gateway: ALL providers failed for %s — KB fallback", persona_label)
    return _KB_RESULT


# ── Status report ─────────────────────────────────────────────────────────────
def gateway_status() -> dict:
    """Return current gateway health. Exposed via /api/admin/health."""
    _reset_hour_if_needed()
    return {
        "providers": {
            "anthropic":   {"available": _anthropic_available(), "degraded": _anthropic_degraded, "key_set": bool(ANTHROPIC_API_KEY), "cost": "paid",      "tool_calling": True},
            "groq":        {"available": bool(GROQ_API_KEY),     "degraded": False,                "key_set": bool(GROQ_API_KEY),      "cost": "free",      "tool_calling": True},
            "gemini":      {"available": bool(GEMINI_API_KEY),   "degraded": False,                "key_set": bool(GEMINI_API_KEY),    "cost": "free",      "tool_calling": False},
            "grok":        {"available": bool(XAI_API_KEY),      "degraded": False,                "key_set": bool(XAI_API_KEY),       "cost": "free_credits", "tool_calling": True},
            "cohere":      {"available": bool(COHERE_API_KEY),   "degraded": False,                "key_set": bool(COHERE_API_KEY),    "cost": "free",      "tool_calling": True},
            "openrouter":  {"available": bool(OPENROUTER_API_KEY),"degraded": False,               "key_set": bool(OPENROUTER_API_KEY),"cost": "free",      "tool_calling": False},
            "kb_fallback": {"available": True,                   "degraded": False,                "key_set": True,                   "cost": "zero",      "tool_calling": False},
        },
        "budget": {
            "hourly_cap":     HOURLY_TOKEN_CAP,
            "tokens_used":    _hour_tokens_used,
            "budget_pct":     round(_hour_tokens_used / max(HOURLY_TOKEN_CAP, 1) * 100, 1),
            "over_budget":    _over_budget(),
        },
        "active_free_providers": sum(1 for k, v in {
            "groq": GROQ_API_KEY, "gemini": GEMINI_API_KEY,
            "grok": XAI_API_KEY,  "cohere": COHERE_API_KEY,
            "openrouter": OPENROUTER_API_KEY,
        }.items() if v),
    }
