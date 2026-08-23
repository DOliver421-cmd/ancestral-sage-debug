# PHASE 16 — FREE GATEWAY AUDIT

**Date:** August 23, 2026
**Status:** CORRECTED — source code exists; provider connectivity BLOCKED (no keys in sandbox)

> **Correction:** an earlier version of this file claimed the repository had no source
> code. That was false (broken glob). The gateway is `backend/ai/llm_gateway.py` (~767
> lines) with 11 configured providers, a BYOK layer (`backend/byok.py`), per-hour token
> cap (`HOURLY_TOKEN_CAP`), per-user daily budget (`user_budget.py`), and shared
> support-staff pool fallback. Provider **connectivity** remains untestable in this
> sandbox (no API keys; health endpoint reports `key_present: false` for all) — depends
> on Railway env. See AI_GATEWAY_FUNCTIONAL_REALITY_AUDIT.md.

---

## PROVIDER INVENTORY (from documentation)

| # | Provider | Env Var | Cost | Tool Calling | Docs Status |
|---|----------|---------|------|-------------|-------------|
| 1a | Groq | `GROQ_API_KEY` | Free | Yes | "Previously active" |
| 1b | Cerebras | `CEREBRAS_API_KEY` | Free | Yes | "Previously active" |
| 1c | SambaNova | `SAMBANOVA_API_KEY` | Free | Yes | "Previously active" |
| 2 | Gemini | `GEMINI_API_KEY` | Free | No | "Previously active" |
| 3 | Grok/xAI | `XAI_API_KEY` | Free credits | Yes | "Previously active" |
| 4 | Cohere | `COHERE_API_KEY` | Free tier | Yes | "Previously failing" |
| 5 | Mistral | `MISTRAL_API_KEY` | Free 1M/mo | Yes | "Previously failing" |
| 6 | Together | `TOGETHER_API_KEY` | Free $25 | No | Unknown |
| 7 | OpenRouter | `OPENROUTER_API_KEY` | Free | No | Unknown |
| 8 | HuggingFace | `HuggingFACE_API_KEY` | Free slow | No | Unknown |
| 9 | KB Fallback | None | Zero | No | Always available |

**Total:** 11 providers configured + KB fallback

---

## STATUS FROM AI GATEWAY AUDIT

| Category | Count | Details |
|----------|-------|---------|
| Configured | 11 | Groq through Anthropic |
| Previously active (believed) | 5 | Unknown which ones |
| Previously failing (believed) | 2 | Unknown which ones |
| Currently verified | 0 | No keys in sandbox |
| Currently blocked | 11 | All blocked on missing keys |
| KB fallback | 1 | Always available |

---

## HEALTH ENDPOINT EVIDENCE

```
/api/health → "ai_api": {"status": "unconfigured", "key_present": false}
```

No provider keys are configured in the sandbox environment.

---

## THE 2 "FAILING" PROVIDERS

**Cannot determine** which 2 providers are failing or why, because:

1. No provider keys exist in this environment
2. The gateway code (`llm_gateway.py`) does not exist in this repository
3. No provider health check code is available to inspect

---

## WHAT NEEDS TO HAPPEN

1. **Locate the source code** — the gateway implementation (`llm_gateway.py`) must be found
2. **Configure at least 1 provider** — set `GROQ_API_KEY` (free tier) in Railway
3. **Test gateway health** — hit `/api/health` in production
4. **Identify failing providers** — check gateway logs for provider connection errors
5. **Fix or disable failing providers** — update configuration or remove broken providers

---

## RECOMMENDATION

**Minimum viable AI:** Configure Groq (free, no cost, tool calling supported). This single provider powers all platform AI features at zero cost.

**Priority 2:** Configure Cerebras and SambaNova as free fallbacks.

**Priority 3:** Configure Gemini for broader model coverage.

---

*Audit based on documentation only. No source code or provider keys available.*
