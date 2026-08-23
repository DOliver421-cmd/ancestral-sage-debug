# PHASE 16 — COST-BEARING FEATURE AUDIT

**Date:** August 23, 2026
**Status:** CORRECTED — classifications exist in the Feature Registry; enforcement verified at decision level

> **Correction:** an earlier version claimed no source code existed (false — broken
> glob). The canonical cost/classification fields (`internal_only`,
> `customer_access_allowed`, `cost_bearing`, `platform_ai`, `byok_allowed`) live in
> `backend/routers/features.py` FEATURE_REGISTRY for every feature, are editable via the
> Feature Control Center, and are now **enforced** by `security/feature_control.py`
> (internal_only + enabled + role/tier overrides; verified by
> `backend/tests/test_fcc_enforcement.py`, 15/15). Platform-funded AI spend is capped
> globally by the gateway (`HOURLY_TOKEN_CAP`, per-user daily budget); per-feature AI
> quotas are CONFIGURATION REQUIRED (none exist). See PHASE_16_VERIFICATION.md.

---

## COST-BEARING CRITERIA

A feature is cost-bearing if it consumes:

- AI/API inference tokens
- Image generation credits
- External provider costs
- Significant compute
- Paid service usage

---

## FEATURES CLAIMED AS COST-BEARING (from Phase 15 docs)

| Feature | Claimed Cost | Evidence | Verifiable? |
|---------|-------------|----------|-------------|
| AI Tutor | AI tokens | Phase 15 doc | ❌ No code |
| Personal Helper | AI tokens | Phase 15 doc | ❌ No code |
| Site Guide | AI tokens | Phase 15 doc | ❌ No code |
| Council (Sage) | AI tokens | Phase 15 doc | ❌ No code |
| Creator Studio | AI tokens | Phase 15 doc | ❌ No code |
| Ghost Producer | AI tokens | Phase 15 doc | ❌ No code |
| Social Blast | AI tokens | Phase 15 doc | ❌ No code |
| Learning Path | AI tokens | Phase 15 doc | ❌ No code |
| Sanctuary | AI tokens | Phase 15 doc | ❌ No code |
| Arena | AI tokens (4 personas) | Phase 15 doc | ❌ No code |
| Jamil | AI tokens | Phase 15 doc | ❌ No code |
| Orchestrator | AI tokens | Phase 15 doc | ❌ No code |
| Admin Assistant | AI tokens | Phase 15 doc | ❌ No code |

---

## GATEWAY ARCHITECTURE (from AI Gateway Audit)

The gateway (`llm_gateway.py`, 767 lines per docs) routes through:

| Provider | Cost | Key Required | Status |
|----------|------|--------------|--------|
| Groq | Free | `GROQ_API_KEY` | NOT TESTED |
| Cerebras | Free | `CEREBRAS_API_KEY` | NOT TESTED |
| SambaNova | Free | `SAMBANOVA_API_KEY` | NOT TESTED |
| Gemini | Free | `GEMINI_API_KEY` | NOT TESTED |
| Grok | Free credits | `XAI_API_KEY` | NOT TESTED |
| Cohere | Free tier | `COHERE_API_KEY` | NOT TESTED |
| Mistral | Free 1M/mo | `MISTRAL_API_KEY` | NOT TESTED |
| Together | Free $25 | `TOGETHER_API_KEY` | NOT TESTED |
| OpenRouter | Free | `OPENROUTER_API_KEY` | NOT TESTED |
| HuggingFace | Free slow | `HUGGINGFACE_API_KEY` | NOT TESTED |
| Anthropic | Paid (disabled) | `ANTHROPIC_API_KEY` | DISABLED |
| KB Fallback | Zero | None | AVAILABLE |

---

## FUNDING POLICY REQUIREMENTS

Per Phase 16 Rule 8, every cost-bearing feature needs an explicit funding policy:

| Funding Policy | Meaning |
|---------------|---------|
| `platform-funded` | Platform pays for AI usage |
| `byok-only` | User must provide own key |
| `tier-funded` | Higher tiers get platform-funded access |
| `role-funded` | Specific roles get funded |
| `mixed` | Combination of above |
| `disabled` | No AI access for this feature |

**STATUS: CONFIGURATION REQUIRED** — No funding policies are defined in any code or configuration file in this repository.

---

## VERIFICATION

**STATUS: NOT VERIFIED**

Cannot verify:

- Which features actually consume AI tokens
- Whether budget guards exist in code
- Whether rate limits are enforced
- Whether cost classification matches actual behavior
- Whether funding policies are implemented

---

*Audit based on documentation only. No source code exists to verify.*
