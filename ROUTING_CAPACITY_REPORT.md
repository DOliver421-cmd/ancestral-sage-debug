# Routing Capacity Assessment

## Executive summary

The gateway now supports bounded per-provider key rotation for Groq, Cerebras,
SambaNova, and Gemini. Requests are assigned one available key in a
lock-protected round-robin order. A key that receives HTTP 429 is placed on a
short cooldown; transport and provider failures receive a shorter cooldown.
When all keys for a provider are cooling down, the request proceeds to the next
provider instead of repeatedly hammering throttled credentials.

This improves throughput when multiple approved keys belong to the same
provider without multiplying one user request into several provider calls.

## Configuration

The legacy single-key variables remain valid. Additional keys can be supplied
as comma-separated or newline-separated values:

```text
GROQ_API_KEYS=key_a,key_b,key_c
CEREBRAS_API_KEYS=key_a,key_b
SAMBANOVA_API_KEYS=key_a,key_b
GEMINI_API_KEYS=key_a,key_b
```

Numbered variables are also supported for the first few slots:

```text
GROQ_KEY_1=...
GROQ_KEY_2=...
GROQ_KEY_3=...
CEREBRAS_KEY_1=...
CEREBRAS_KEY_2=...
SAMBANOVA_KEY_1=...
SAMBANOVA_KEY_2=...
GEMINI_KEY_1=...
GEMINI_KEY_2=...
```

Optional cooldown settings:

```text
PROVIDER_KEY_COOLDOWN_SEC=30
PROVIDER_KEY_FAILURE_COOLDOWN_SEC=5
```

Values must be entered only in the deployment secret manager or platform
variable store. They must never be committed to the repository or printed in
logs.

## Request lifecycle

1. An authenticated request enters the existing budget and access checks.
2. User BYOK remains isolated and is attempted only for that same user.
3. The provider pool selects one available key atomically.
4. The gateway makes one provider request using that key.
5. A successful response returns normally and is recorded by the existing
   token/cost accounting.
6. A 429 cools down only the selected key.
7. Other failures briefly cool down only the selected key.
8. The gateway advances through the existing provider fallback chain.
9. The zero-cost knowledge-base response remains the final fallback.

## Why this is safer than unconditional fan-out

`asyncio.gather()` across every key would create multiple upstream requests for
one user action. That can exhaust free quotas, produce duplicate work, and
violate provider rate or account terms. Rotation gives higher sustained
capacity while preserving one-request/one-response semantics.

## Operational limits

The pool is process-local. With multiple Railway replicas, each worker has its
own pointer and cooldown map. This is expected and safe, but it is not a
fleet-wide rate limiter. If traffic grows beyond one worker, add a shared
provider-aware limiter or queue before increasing replica count.

The gateway still has a sequential provider fallback order. Key rotation
reduces contention within a provider, but does not remove worst-case latency
when several providers time out. A future latency-bounded hedge should be
added only with explicit request budgets and cancellation behavior.

## Keeping it active and correct

- Keep the pool variables configured in Railway Variables, never in tracked
  files.
- Keep `PROVIDER_KEY_COOLDOWN_SEC` aligned with the provider's documented
  retry-after behavior.
- Monitor provider status, 429 rates, timeout rates, fallback rates, and KB
  fallback frequency.
- Rotate or revoke compromised credentials immediately.
- Do not enable shared staff BYOK without explicit contributor consent,
  provider-terms review, and per-contributor attribution.
- Preserve backend authorization; frontend visibility is not a security gate.
- Keep executive owner access outside checkout and paid entitlements.
- Re-run the key-pool regression tests after gateway changes.

## Verification evidence

- `backend/tests/test_key_pool.py`: parsing, round-robin, cooldown isolation,
  and all-keys-cooling behavior.
- `scripts/tools/verify_endpoints.py`: 14/14 focused endpoint checks passed.
- Python compilation passed for the gateway and key-pool modules.
