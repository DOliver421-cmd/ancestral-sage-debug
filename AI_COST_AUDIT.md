# AI COST AUDIT (Phase 20)

**Method:** source inspection of `ai/llm_gateway.py`, `routers/ai.py`, `routers/byok.py`, `byok.py` this session. Provider connectivity **BLOCKED** (no keys in sandbox).

## Provider table (SRC, `llm_gateway.py` health block)

| Provider | Tier | Cost class | Tool calling | Available = key set |
|---|---|---|---|---|
| groq | 1a primary | free | yes | `GROQ_API_KEY` |
| cerebras | 1b primary | free | yes | `CEREBRAS_API_KEY` |
| sambanova | 1c primary | free | yes | `SAMBANOVA_API_KEY` |
| gemini | 2 | free | no | `GEMINI_API_KEY` |
| grok (xAI) | 3 | free_credits | yes | `XAI_API_KEY` |
| cohere | 4 | free | yes | `COHERE_API_KEY` |
| mistral | 5 | free_1M/month | yes | `MISTRAL_API_KEY` |
| together | 6 | free_credit | no | `TOGETHER_API_KEY` |
| openrouter | 7 | free | no | `OPENROUTER_API_KEY` |
| huggingface | 8 | free_slow | no | `HUGGINGFACE_API_KEY` |
| anthropic | OFF (owner directive) | PAID_DISABLED | yes | `ANTHROPIC_API_KEY` (re-enable via flag) |
| kb_fallback | 9 | zero | no | always |
| byok_shared | shared | free_shared | yes | staff pool loaded |

Run `GET /api/admin/health` in production for the real `key_set`/`available` table (SRC).

## Budget controls (SRC)

- `HOURLY_TOKEN_CAP` (default 200k) — global hourly guard, checked before spend.
- Per-user daily cap (`USER_DAILY_TOKEN_CAP`) with `budget_key` fallback identity for anonymous (`ip:...`).
- Budget-exhausted responses are explicit notices (not silent failures).
- Startup log this session confirmed: prompt-guard baselines enrolled, failover watchdog + GDPR purge + memory consolidation crons launched.

## Funding-mode classification

| Mode | When | Verified |
|---|---|---|
| User BYOK | user has stored key for the provider | resolves FIRST (SRC) |
| Platform-funded free providers | no BYOK key; free-tier chain | primary chain (SRC) |
| Staff shared pool | all free providers fail | before KB fallback (SRC) |
| KB fallback | everything fails / budget exhausted | zero cost (SRC) |

## Gaps (documented, unchanged)

1. **`byok_allowed` is not consulted** by the gateway: BYOK keys are used whenever present, even for features configured `byok_allowed=false`. Saves platform money; contradicts declared funding policy (P1/P2, executive decision).
2. **No per-feature AI quotas** — global caps only. Marked CONFIGURATION REQUIRED; not invented.
3. **Shared pool attribution/audit:** no per-member attribution of shared-pool use and no explicit "shared pool used" audit event (SRC — pool is decrypted in-memory only; provider-priority used). Encrypt-secret-missing behavior: plaintext risk if `PROVIDER_KEY_ENCRYPTION_SECRET` is absent (SRC flag).
4. **Platform-funded AI to anonymous:** only the two bounded helper endpoints (KB-first, IP-limited/budgeted) — the only anonymous LLM path found (SRC).

## Not claimed

- No provider call was executed; no real AI cost was incurred; connectivity is unverified.
