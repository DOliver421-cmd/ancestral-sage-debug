"""
llm_gateway.py — Centralized LLM routing for WAI-Institute
============================================================
All persona endpoints call call_llm() instead of instantiating
AsyncAnthropic directly. This enforces:
  - Single instantiation point
  - Provider fallback chain: Anthropic → OpenRouter/Gemini → keyword KB
  - Per-hour token budget guard (configurable via HOURLY_TOKEN_CAP env var)
  - Provider health tracking (marks Anthropic as degraded on repeated failures)

Provider priority:
  Tier 1 — Anthropic Claude (ANTHROPIC_API_KEY)
  Tier 2 — OpenRouter free tier / Gemini Flash (OPENROUTER_API_KEY)
  Tier 3 — Keyword KB fallback (zero API cost, always available)
"""

import os
import logging
import asyncio
import time
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("lcewai.llm_gateway")

# ── Configuration ─────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY", os.environ.get("EMERGENT_LLM_KEY", ""))
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Hourly token cap — configurable in Railway. Default 200k tokens/hour.
# At Sonnet pricing (~$3/MTok in, ~$15/MTok out), 200k mixed = ~$1/hour max.
# Set lower (e.g. 50000) during low-revenue period.
HOURLY_TOKEN_CAP   = int(os.environ.get("HOURLY_TOKEN_CAP", "200000"))

# OpenRouter free Gemini model — no credit card, 60 req/min
OPENROUTER_MODEL   = "google/gemini-2.0-flash-lite-preview-02-05:free"
OPENROUTER_BASE    = "https://openrouter.ai/api/v1"

# ── In-process state (resets on container restart — acceptable for budget guard) ──
_hour_window_start: float = time.time()
_hour_tokens_used:  int   = 0
_anthropic_degraded: bool = False      # True after 3 consecutive Anthropic failures
_anthropic_fail_count: int = 0
_DEGRADED_RESET_SECONDS = 300          # re-try Anthropic after 5 minutes


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


def _mark_anthropic_fail() -> None:
    global _anthropic_fail_count, _anthropic_degraded, _degraded_since
    _anthropic_fail_count += 1
    if _anthropic_fail_count >= 3:
        _anthropic_degraded = True
        _degraded_since = time.time()
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
        # Auto-recover after DEGRADED_RESET_SECONDS
        if time.time() - getattr(_gateway_module, "_degraded_since", 0) > _DEGRADED_RESET_SECONDS:
            _anthropic_degraded = False
            logger.info("LLM Gateway: Anthropic degraded flag cleared — retrying")
            return True
        return False
    return True

# module-level ref for degraded_since
import sys as _sys
_gateway_module = _sys.modules[__name__]
_degraded_since: float = 0.0


# ── Keyword KB fallback response ──────────────────────────────────────────────
_KB_FALLBACK = (
    "I'm operating in restricted mode right now — the AI service is temporarily unavailable. "
    "Your request has been logged. For urgent matters, contact WAI-Institute directly. "
    "Platform features (modules, labs, certificates, community) are fully operational."
)


async def call_llm(
    system: str,
    messages: list[dict],
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2048,
    tools: Optional[list] = None,
    persona_label: str = "unknown",
) -> dict:
    """
    Unified LLM call with fallback chain.

    Returns:
        {
            "text": str,           # response text
            "provider": str,       # "anthropic" | "openrouter" | "kb_fallback"
            "model": str,
            "input_tokens": int,
            "output_tokens": int,
            "degraded": bool,      # True when not using primary provider
        }
    """
    # ── Budget guard — degrade non-critical calls when over hourly cap ────────
    if _over_budget():
        logger.warning(
            "LLM Gateway: hourly token cap %d reached (%d used). "
            "Routing %s to KB fallback.",
            HOURLY_TOKEN_CAP, _hour_tokens_used, persona_label,
        )
        return {
            "text": _KB_FALLBACK,
            "provider": "kb_fallback",
            "model": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "degraded": True,
        }

    # ── Tier 1: Anthropic ─────────────────────────────────────────────────────
    if _anthropic_available():
        try:
            import anthropic as _anth
            client = _anth.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            kwargs = dict(model=model, max_tokens=max_tokens, system=system, messages=messages)
            if tools:
                kwargs["tools"] = tools
            resp = await client.messages.create(**kwargs)
            text = "".join(b.text for b in resp.content if hasattr(b, "text"))
            in_tok  = getattr(resp.usage, "input_tokens",  0)
            out_tok = getattr(resp.usage, "output_tokens", 0)
            _record_tokens(in_tok + out_tok)
            _mark_anthropic_ok()
            return {
                "text": text,
                "provider": "anthropic",
                "model": model,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "degraded": False,
                "_raw": resp,   # callers that need tool_use blocks can access this
            }
        except Exception as e:
            logger.warning("LLM Gateway: Anthropic call failed (%s): %s", persona_label, e)
            _mark_anthropic_fail()

    # ── Tier 2: OpenRouter / Gemini Flash (free tier) ─────────────────────────
    if OPENROUTER_API_KEY:
        try:
            import httpx
            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer":  "https://wai-institute.com",
                "X-Title":       "WAI-Institute",
                "Content-Type":  "application/json",
            }
            # Convert Anthropic-style system + messages to OpenAI-compatible format
            oai_messages = [{"role": "system", "content": system}] + [
                {"role": m["role"], "content": m["content"] if isinstance(m["content"], str)
                 else (m["content"][0].get("text","") if m["content"] else "")}
                for m in messages
            ]
            payload = {
                "model":      OPENROUTER_MODEL,
                "messages":   oai_messages,
                "max_tokens": max_tokens,
            }
            async with httpx.AsyncClient(timeout=30) as http:
                r = await http.post(f"{OPENROUTER_BASE}/chat/completions", headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
            text    = data["choices"][0]["message"]["content"]
            in_tok  = data.get("usage", {}).get("prompt_tokens",     0)
            out_tok = data.get("usage", {}).get("completion_tokens", 0)
            _record_tokens(in_tok + out_tok)
            logger.info("LLM Gateway: served %s via OpenRouter/Gemini (degraded mode)", persona_label)
            return {
                "text": text,
                "provider": "openrouter",
                "model": OPENROUTER_MODEL,
                "input_tokens": in_tok,
                "output_tokens": out_tok,
                "degraded": True,
            }
        except Exception as e:
            logger.warning("LLM Gateway: OpenRouter call failed (%s): %s", persona_label, e)

    # ── Tier 3: Keyword KB — always available, zero cost ─────────────────────
    logger.error(
        "LLM Gateway: ALL providers failed for %s — returning KB fallback", persona_label
    )
    return {
        "text": _KB_FALLBACK,
        "provider": "kb_fallback",
        "model": "none",
        "input_tokens": 0,
        "output_tokens": 0,
        "degraded": True,
    }


def gateway_status() -> dict:
    """Return current gateway health for /api/admin/health."""
    _reset_hour_if_needed()
    return {
        "anthropic_available": _anthropic_available(),
        "anthropic_degraded":  _anthropic_degraded,
        "anthropic_key_set":   bool(ANTHROPIC_API_KEY),
        "openrouter_key_set":  bool(OPENROUTER_API_KEY),
        "hourly_token_cap":    HOURLY_TOKEN_CAP,
        "hourly_tokens_used":  _hour_tokens_used,
        "budget_pct":          round(_hour_tokens_used / max(HOURLY_TOKEN_CAP, 1) * 100, 1),
        "kb_fallback_always":  True,
    }
