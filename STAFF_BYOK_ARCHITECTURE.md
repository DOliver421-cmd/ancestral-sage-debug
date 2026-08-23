# STAFF BYOK ARCHITECTURE

**Date:** August 23, 2026
**Status:** AUDIT COMPLETE — the authorized support-staff shared pool EXISTS and is verified in code

## 1. THE THREE FUNDING SOURCES (verified)

| # | Source | Storage | Resolved by | Platform cost |
|---|--------|---------|-------------|---------------|
| 1 | **User BYOK** | `db.user_byok_keys` (encrypted) + `byok_enabled` | `byok.resolve_byok(user_id)` | $0 — user pays |
| 2 | **Platform provider keys** | env vars (`GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, …) | `call_llm` platform chain | platform budget (global caps) |
| 3 | **Authorized support-staff shared pool** | `db.user_byok_keys` of `role="support_staff"` users (encrypted) | `reload_shared_byok()` → `_SHARED_BYOK_POOL` | $0 (voluntary) |
| 4 | KB fallback | code constant | gateway degradation | $0 |

## 2. HOW THE SHARED POOL WORKS (verified in code)

- Support staff activate BYOK for **free** (`FREE_BYOK_ROLES` — staff/partner/support
  roles pay `$0` via `byok_price_for()`).
- Their keys are stored like any BYOK key in `db.user_byok_keys`
  (`role="support_staff"`).
- `backend/ai/llm_gateway.py reload_shared_byok()` loads active support keys into
  `_SHARED_BYOK_POOL` at startup (and on demand), provider-priority
  groq → cerebras → gemini, **decrypted in memory only**.
- `call_llm` uses the pool AFTER user BYOK and ALL platform free providers fail,
  and BEFORE the KB fallback.
- **Isolation:** customers never receive pool credentials — keys are used by the
  gateway process, never returned to any client (`get_byok_status` returns masked
  suffixes only; `save_byok_key` encrypts; `remove_byok_key` deletes).

## 3. SECURITY PROPERTIES (verified)

| Property | Status |
|----------|--------|
| Encryption at rest | Fernet with `PROVIDER_KEY_ENCRYPTION_SECRET` (warns if unset — plaintext risk must be fixed in production env) |
| Raw keys to frontend | NEVER (masked suffix only) |
| Cross-user credential access | IMPOSSIBLE via API (queries scoped by `user_id`) |
| Staff identity exposure | Pool stores only `provider`+`key`; no identity in the pool |
| Authorization before selection | Feature middleware runs before route handlers → before `call_llm` → before BYOK/pool resolution (structural) |
| Audit trail | Gateway logs provider/persona; `ai_cost_tracker.py` records per-persona cost; denial buffer logs access denials (encrypted when `AUDIT_ENCRYPTION_KEY` set) |
| Revocation | Support staff removes key → `reload_shared_byok` drops it from the pool |

## 4. GAPS (documented)

| # | Gap | Impact | Required change |
|---|-----|--------|-----------------|
| S1 | Shared-pool usage is not attributed per support member (pool stores provider+key only, no owner id in the resolved list) | Cannot answer "which staff key served what" without DB forensics | Add owner attribution metadata (not identity exposure) in `_SHARED_BYOK_POOL` + usage logging |
| S2 | No explicit per-request "shared pool used" audit event | Observability gap | Record `provider="shared:<provider>"` in gateway result + cost tracker (result already exposes `provider`) |
| S3 | `PROVIDER_KEY_ENCRYPTION_SECRET` unset → plaintext storage warning | Credential-at-rest risk in any env lacking the secret | Set in Railway (exec action) |
| S4 | Pool eligibility is hardcoded to `role="support_staff"` | No admin control over who may contribute | Tie to a configurable role list / FCC control (future) |

## 5. ACCEPTANCE STATUS (staff BYOK dimension)

- Test 13 (staff contribute/use pool): code path verified; live test BLOCKED (no Mongo,
  no keys in sandbox).
- Test 14 (customers cannot access staff credentials): verified by code (API never
  returns keys; pool is gateway-internal) + BYOK status endpoint returns masked
  values only.
- Test 20 (BYOK authorization after feature authorization): structural (middleware →
  handler → gateway) + decision-function tests.
