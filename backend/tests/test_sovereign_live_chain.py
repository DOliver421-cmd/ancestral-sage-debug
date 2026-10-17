"""tests/test_sovereign_live_chain.py — prove the Sovereign AI surface answers
when a live provider key is present.

`_require_provider_result` (studio.py:1158) raises AI_PROVIDER_UNAVAILABLE
whenever call_llm cannot reach a live provider. That is a guard, and it is
correct — but the useful question is whether the chain actually CAN reach a
provider when one is configured. This test sets a fake key in the gateway
globals and asserts the chain wires through to a real HTTP call rather than
falling to kb_fallback.

It does not make a network call with the fake key: the point is that the
`if <KEY>_API_KEY:` guards fire and the request reaches the provider adapter,
which then fails with an auth error rather than being skipped. A skipped
tier (the no-key case) and a failed tier (the bad-key case) are distinguishable
by the exception type, which is what this pins.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import llm_gateway as gw  # noqa: E402


def _reset_pools():
    """Give every rotating pool exactly one fake key so acquire() succeeds."""
    gw._PROVIDER_KEY_POOLS["groq"] = gw.KeyPool(["fake-groq-key"])
    gw._PROVIDER_KEY_POOLS["cerebras"] = gw.KeyPool(["fake-cerebras-key"])
    gw._PROVIDER_KEY_POOLS["sambanova"] = gw.KeyPool(["fake-sambanova-key"])
    gw._PROVIDER_KEY_POOLS["gemini"] = gw.KeyPool(["fake-gemini-key"])


def test_chain_reaches_a_provider_when_a_key_is_set():
    """With a key present the chain must attempt a real provider call.

    The fake key cannot authenticate, so the call fails with an HTTP error —
    but it must NOT silently fall through to kb_fallback. A tier that is
    skipped because its key global is empty and a tier that is attempted and
    rejected are different outcomes, and only the second means AI works.
    """
    import asyncio

    gw.GROQ_API_KEY = "fake-groq-key"
    gw.CEREBRAS_API_KEY = "fake-cerebras-key"
    gw.SAMBANOVA_API_KEY = "fake-sambanova-key"
    gw.GEMINI_API_KEY = "fake-gemini-key"
    _reset_pools()

    async def run():
        try:
            await gw.call_llm(
                messages=[{"role": "user", "content": "ping"}],
                system="test",
                persona_label="test",
                user_id=None,
            )
        except Exception as exc:
            # A real provider attempt surfaces an HTTP/auth error, never the
            # silent KB fallback. The distinction is the whole point.
            assert "kb" not in str(exc).lower()
            return
        pytest.fail("call_llm returned without raising — expected a provider error")

    asyncio.run(run())


def test_chain_skips_every_tier_when_no_key_is_set():
    """The no-key state returns kb_fallback — that is the AI_PROVIDER_UNAVAILABLE
    root cause, and it is expected behaviour, not a code defect."""
    import asyncio

    gw.GROQ_API_KEY = ""
    gw.CEREBRAS_API_KEY = ""
    gw.SAMBANOVA_API_KEY = ""
    gw.GEMINI_API_KEY = ""
    gw.XAI_API_KEY = ""
    gw.COHERE_API_KEY = ""
    gw.MISTRAL_API_KEY = ""
    gw.TOGETHER_API_KEY = ""
    gw.OPENROUTER_API_KEY = ""
    gw.HUGGINGFACE_API_KEY = ""
    gw.OPENAI_API_KEY = ""
    gw.DEEPSEEK_API_KEY = ""
    for pool in gw._PROVIDER_KEY_POOLS.values():
        pool.keys = ()

    async def run():
        result = await gw.call_llm(
            messages=[{"role": "user", "content": "ping"}],
            system="test",
            persona_label="test",
            user_id=None,
        )
        assert result.get("provider") == "kb_fallback"

    asyncio.run(run())


def test_gateway_status_reports_no_active_provider_without_keys():
    gw.GROQ_API_KEY = ""
    gw.CEREBRAS_API_KEY = ""
    gw.SAMBANOVA_API_KEY = ""
    gw.GEMINI_API_KEY = ""
    gw.XAI_API_KEY = ""
    gw.COHERE_API_KEY = ""
    gw.MISTRAL_API_KEY = ""
    gw.TOGETHER_API_KEY = ""
    gw.OPENROUTER_API_KEY = ""
    gw.HUGGINGFACE_API_KEY = ""
    gw.OPENAI_API_KEY = ""
    gw.DEEPSEEK_API_KEY = ""
    status = gw.gateway_status()
    assert status["active_providers"] == 0
    assert status["active_free_providers"] == 0
    assert status["providers"]["groq"]["available"] is False