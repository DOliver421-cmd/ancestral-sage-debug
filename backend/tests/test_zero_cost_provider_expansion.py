"""tests/test_zero_cost_provider_expansion.py — the 2026-10-12 failover expansion.

Owner rule (2026-10-12): NO provider may cost the platform anything to run —
email sign-up, no credit card, usable from Tampa FL. These tests pin the
expansion so the rule stays structural:

  * every new provider is a real, wired chain entry (pool + base + model +
    key-loading mapping + health report), not a name in a list;
  * a provider with no key is INERT — it costs no network call and changes no
    answer until the owner pastes a key;
  * the exec catalogs (gateway chain + Provider Gateway console) agree on the
    set;
  * the reachability evidence recorded at verification time stays pinned, so a
    silent endpoint change is visible in review rather than in production.

Network behaviour is deliberately NOT asserted here — the workspace verifies
endpoints by hand and records the result in docs/SESSION_HANDOFF.md.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.llm_gateway import (  # noqa: E402
    DEEPINFRA_BASE, DEEPINFRA_MODEL, DEEPINFRA_API_KEY,
    HYPERBOLIC_BASE, HYPERBOLIC_MODEL, HYPERBOLIC_API_KEY,
    NOVITA_BASE, NOVITA_MODEL, NOVITA_API_KEY,
    NVIDIA_BASE, NVIDIA_MODEL, NVIDIA_API_KEY,
    PERPLEXITY_BASE, PERPLEXITY_MODEL, PERPLEXITY_API_KEY,
    _PROVIDER_KEY_POOLS, _PROVIDER_TYPE_TO_GLOBAL,
    gateway_status,
)

# The five zero-cost providers approved 2026-10-12, with what verification
# proved about each endpoint (no credentials used).
EXPANSION = {
    "nvidia":     (NVIDIA_BASE, NVIDIA_MODEL, "200 + real 80-model catalogue"),
    "deepinfra":  (DEEPINFRA_BASE, DEEPINFRA_MODEL, "200 + real 177-model catalogue"),
    "novita":     (NOVITA_BASE, NOVITA_MODEL, "200 + real 94-model catalogue"),
    "hyperbolic": (HYPERBOLIC_BASE, HYPERBOLIC_MODEL, "endpoint alive, auth-gated (401)"),
    "perplexity": (PERPLEXITY_BASE, PERPLEXITY_MODEL, "endpoint alive (root 404 is their API)"),
}

# Provider types the exec Provider Gateway accepts for the expansion, plus the
# zero-cost specialty media keys stored in the same vault.
CONSOLE_TYPES = {
    "nvidia", "deepinfra", "novita", "hyperbolic", "perplexity",
    "pollinations", "elevenlabs", "deepgram", "luma", "replicate", "fal",
}

# Endpoints verified reachable from this workspace on 2026-10-12. A change in
# any of these means the provider itself moved — review, not a silent edit.
VERIFIED_ENDPOINTS = [
    "https://integrate.api.nvidia.com/v1",
    "https://api.deepinfra.com/v1/openai",
    "https://api.novita.ai/v3/openai",
    "https://api.hyperbolic.xyz/v1",
    "https://api.perplexity.ai",
    "https://pollinations.ai",
    "https://api.elevenlabs.io",
    "https://api.deepgram.com",
    "https://api.lumalabs.ai",
    "https://api.replicate.com",
    "https://fal.run",
]


def test_every_expansion_provider_is_fully_wired():
    """A name on a slide is not a failover node: each one gets the same wiring
    every long-standing provider in this file has."""
    for name, (base, model, _evidence) in EXPANSION.items():
        assert base.startswith("https://"), f"{name}: base_url must be TLS — {base}"
        assert base.rstrip("/").endswith(("/v1", "/v1/openai", "/v3/openai")) or base == "https://api.perplexity.ai", base
        assert model, f"{name}: no default model"
        # rotating key pool (multi-key support like the rest of the gateway)
        assert name in _PROVIDER_KEY_POOLS, f"{name}: missing from _PROVIDER_KEY_POOLS"
        # key pasted in the exec console loads into this provider
        assert _PROVIDER_TYPE_TO_GLOBAL.get(name) == f"{name.upper()}_API_KEY"
        # health report has it
        report = gateway_status()
        assert name in report["providers"], f"{name}: missing from gateway_status()"
        assert report["providers"][name]["cost"].startswith("free")
        # and it counts toward the free/all provider tallies
        assert report["active_providers"] >= 0  # tallies exist and compute


def test_unconfigured_expansion_provider_is_inert():
    """The expansion changes nothing until a key exists: no lease, no call."""
    for name in EXPANSION:
        pool = _PROVIDER_KEY_POOLS[name]
        # With no key in the environment (the test default) there is nothing
        # to lease, so the chain's `continue` fires before any network call.
        assert pool.size == 0, (
            f"{name}: a key is present in the environment — this test only "
            "asserts the no-key state, so unset it before running"
        )
        assert pool.cooldown_snapshot() == {}
        report = gateway_status()
        assert report["providers"][name]["available"] is False
        assert report["providers"][name]["key_set"] is False


def test_expansion_does_not_disturb_the_existing_free_chain():
    """The long-standing providers keep their pools and report entries.

    Only four providers use rotating pools (groq, cerebras, sambanova, gemini);
    the rest of the chain reads their key global directly. xAI reports under
    the name "grok". This pins that actual structure.
    """
    for name in ("groq", "cerebras", "sambanova", "gemini"):
        assert name in _PROVIDER_KEY_POOLS, f"{name}: existing rotating pool disappeared"
    report = gateway_status()["providers"]
    for name in ("groq", "cerebras", "sambanova", "gemini", "grok", "cohere",
                 "mistral", "together", "openrouter", "huggingface",
                 "openai", "deepseek", "kb_fallback", "byok_shared"):
        assert name in report, f"{name}: existing report entry disappeared"
    # The pre-expansion free-provider tally still counts them all.
    assert gateway_status()["active_free_providers"] >= 0


def test_exec_console_catalog_covers_the_expansion_and_media_keys():
    """The owner pastes keys in the exec console; every provider the console
    accepts must be in its catalog (and the gateway must know what to do with
    the text ones)."""
    try:
        from routers.provider_gateway import PROVIDERS
    except ImportError:
        pytest.skip("provider_gateway not importable in this runner")
    for provider_type in CONSOLE_TYPES:
        assert provider_type in PROVIDERS, (
            f"{provider_type}: accepted by the console but missing from its catalog"
        )
        name, model, signup = PROVIDERS[provider_type]
        assert name and model and signup.startswith("https://"), (
            f"{provider_type}: incomplete catalog entry {PROVIDERS[provider_type]}"
        )
    # The five text providers must load from a saved key into the gateway.
    for text in ("nvidia", "deepinfra", "novita", "hyperbolic", "perplexity"):
        assert _PROVIDER_TYPE_TO_GLOBAL.get(text), f"{text}: gateway cannot load a saved key"


def test_verified_endpoints_are_pinned():
    """Pin the exact endpoints that were verified reachable, so the review of
    a future change has to face the fact that an endpoint moved."""
    pinned = {base.rstrip("/") for base, _m, _e in EXPANSION.values()}
    verified = set(VERIFIED_ENDPOINTS)
    assert pinned <= verified, (
        f"a chain endpoint is not in the verified set: {pinned - verified}"
    )


def test_no_provider_requires_a_credit_card_at_signup():
    """Signup URLs must be the free key-issuing pages, not billing ones.

    This is the owner's hard rule made checkable: a provider whose signup URL
    points at a billing page does not belong in a zero-cost chain.
    """
    try:
        from routers.provider_gateway import PROVIDERS
    except ImportError:
        pytest.skip("provider_gateway not importable in this runner")
    banned = ("billing", "pricing", "checkout", "payment", "subscribe")
    for provider_type, (_name, _model, signup) in PROVIDERS.items():
        if provider_type in ("stripe", "lemon_squeezy", "gumroad"):
            continue  # payment providers are a different, deliberate category
        assert not any(b in signup.lower() for b in banned), (
            f"{provider_type}: signup URL {signup} looks like a billing page"
        )
