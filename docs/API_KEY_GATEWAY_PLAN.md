# API KEY GATEWAY — BUILD & FIX PLAN — SUPERSEDED

> **Content integrated into `docs/WORKING_PLAN.md` (Phase 2, G0–G7, plus D1–D21 in §3).** Work from the
> working plan; this file is history.

**Supersedes the first draft.** This version is grounded in a second, deeper verification pass over the
gateway internals (`ai/llm_gateway.py`, `ai/key_pool.py`, `ai/team_monitor.py`, `routers/provider_gateway.py`,
`routers/revenue_exec.py`, the 7 `ai_usage_log` writers, the specialty integrations) and in the owner's written
expectations for the surface. Everything marked VERIFIED was executed or quoted from source on 2026-10-10.

**The build (owner's words, restated as the acceptance target):** one surface for every AI credential and the
gateway that routes them. Platform-owned global provider pool; configured credentials fund the platform's AI
capability and absorb usage when member traffic spikes. Every provider shown with the same routing class,
credential state, and verification requirements; live transport and model availability come from the provider's
actual endpoint and credential. `POST /v1/chat/completions` with `model: "auto"` selects only verified providers
in the no-current-platform-cost classes. Monetization and BYOK providers remain visible and testable but are
excluded unless their policy explicitly authorizes routing. Failover is model-verified and provider-aware.
Gemini 15 RPM and Mistral 1M tokens/month remain enforced. Credentials are encrypted at rest and never leave
the server. Human controls are live-wired; zero mock; no cosmetic fixes.

---

## 1. Verified baseline (what execution proved, with exact numbers)

**Real and working today:**

| Fact | Evidence |
|---|---|
| Route `/admin/providers` → `ProviderGateway.jsx`, gated frontend (`ROLE_RANK` 7) and backend (`_exec` → 403) | `App.js:510`; executed 200 as locally-promoted exec |
| `GET /api/providers/quick-setup/status` returns **15** providers (9 AI + stripe/lemon_squeezy/gumroad + sambanova/openrouter/huggingface), masked `••••7890`, source | executed |
| `POST /api/providers/quick-setup` encrypts with the keyvault Fernet, upserts, reloads the gateway | executed `{configured:true, key_masked:"••••7890"}` |
| `GET /api/admin/gateway/status` + `PATCH /budget` + `POST /reset-budget` take effect live | executed; cap 200 000 rolling hour |
| `GET/PATCH /api/admin/gateway/ranking` persists a 12-provider order | executed, `source: "default"` |
| Failover chain runs in-process with per-key cooldown + KB fallback | `llm_gateway.py:743-857`; `ai/key_pool.py` |
| `GET /api/ai/provider-test` live-pings **8** providers (omits cohere, huggingface, openai, deepseek) | executed; returns `{ok, reason}` per provider |
| Keyvault: env → Mongo-persisted → ephemeral Fernet; masking display-only; no raw key in any response/log | `keyvault.py`; `provider_gateway.py:69` |
| BYOK (7 routes) real; member BYOK keys resolved first in `call_llm` and never counted against platform budgets | `byok.py`; `llm_gateway.py:566-606` |

**Broken or missing (each verified, each fixed in §4):**

| # | Defect | Executed evidence |
|---|---|---|
| D1 | **Revocation is not real.** Disable *and* delete leave the key live in the process. `reload_provider_keys` only fills empty globals (`llm_gateway.py:101-103`) and never clears one | executed: after `DELETE /providers/keys/by-provider/groq`, `GET /admin/gateway/status` still `available: true`; a live exec toggle in `MoreHelpCenter.jsx:534/543` therefore changes nothing until restart |
| D2 | **Multi-replica amplification of D1.** Keys are import-time module globals per process; a Railway deployment with >1 replica never evicts anywhere | source: globals + `KeyPool` are per-process; reload only runs at startup and after a write *in that replica* |
| D3 | **`model:"auto"` does not exist.** `call_llm(model=...)` ignores the parameter; every tier passes its own hardcoded model constant | source; 0 of ~80 call sites pass `model=` |
| D4 | **`POST /v1/chat/completions` does not exist** | executed 404 |
| D5 | **Ranking is a stored preference with zero routing effect** — the router reads the hardcoded tuple `("groq","cerebras","sambanova","gemini")` (`llm_gateway.py:743`); `db.provider_rankings` is written and never read by the router | source + executed (ranking PATCH then routing unchanged) |
| D6 | **Usage log records almost nothing and displays fields that don't exist.** 7 writers in `routers/ai.py` (tool routes only) store `user_id/endpoint/skill/model/provider/cost_usd/created_at`; the UI renders `log.provider_id` / `log.result` — **no writer emits either**. No `result`, no tokens, no `request_id`, no fallback chain. The main chat path logs nothing: `ai_usage_log` count = 0 in the audited DB after executed AI calls. No index on `created_at` | executed + source |
| D7 | **Key save accepts any non-empty string** and reports Active — a typo'd key is stored as configured | source (`provider_gateway.py:139-140`); BYOK has a real test (`byok.py:246`) that this path lacks |
| D8 | **Model/tier strings are static and disagree across four files**: Groq is `openai/gpt-oss-120b` (`llm_gateway.py:127`), `llama-3.3-70b-versatile` (`provider_gateway.py:17`), `llama-3.3-70b-versatile` (`byok.py:60`), "Llama 3.3 70B" (UI preset); Gemini is `gemini-3.6-flash` vs `gemini-2.0-flash` vs docstring "2.0" | source |
| D9 | **Coverage gap: 9 UI cards of 15 statuses** — sambanova/openrouter/huggingface statuses are returned and silently dropped; the owner's pool lists **27** providers | source |
| D10 | **Gemini 15 RPM and Mistral 1M tokens/month are labels nothing reads** — no counter exists; the only Gemini mechanism is a cooldown after a real 429 | source (grep: zero readers) |
| D11 | **Token accounting is provider-reported only** — HuggingFace returns 0/0 by construction; no local counter exists for any limit | source (`llm_gateway.py:287-288`, `:854-855`) |
| D12 | **Specialty keys are env-only**: Exa, NASA, Pexels, Gumroad, Stripe, Resend, Gmail, Cloudflare Workers AI, HF Inference (images/music), ElevenLabs, Groq Audio — no vault storage, no CRUD, no masking, no test surface, owner cannot update them from the platform | source: `nasa_observatory.py:43`, `studio.py:612`, `server.py:769-890`, `ai/persona_tts.py:36`, `jamil.py:255` |
| D13 | **Three specialty integrations do not exist at all**: Exa (grep: zero backend code), Cloudflare Workers AI (zero), HF image/music inference (zero). The reference UI shows them ACTIVE — the keys cannot be doing anything | source |
| D14 | **Payment/Credit Keys do not exist**: no grant label, monthly grant tokens, notes, or used-this-month field anywhere | source |
| D15 | **Nav defect**: sidebar link sits in the `minRole:"admin"` section (`AppShell.jsx:214`) while the route requires `executive_admin` — an admin clicks and is bounced | source |
| D16 | **`db.api_keys` schema collision**: provider credentials (`provider_id`/`encrypted_key`) share the collection with customer API-as-a-service keys (`key_hash`/`tier`); `reload_provider_keys` scans both shapes | source |
| D17 | **Legacy write-only collections**: the older `/api/providers/keys*` path writes `ai_providers`/`ai_provider_keys`; the gateway only reads `api_providers`/`api_keys` | source |
| D18 | **No indexes** on `api_keys`, `api_providers`, `ai_usage_log`, `provider_rankings` | source (`ensure_indexes` list) |
| D19 | **Anthropic references remain** against platform policy: `ai/ai_cost_tracker.py:13-18` prices claude models; `wai_institute/pipelines/conversational_engine.py:177-187` holds a dead `client.messages.create(model="claude-haiku-4-5")` | source |
| D20 | **`run_monitor_loop()` never starts** — real per-provider health probe + auto-revoke on 401/403 (`ai/team_monitor.py:254`) is dead code | source (whole-word search: definition only) |
| D21 | The page's Refresh button refreshes only the status call, never the open tab | source (`ProviderGateway.jsx:441-443`) |

---

## 2. Owner's expectations → verified reality → required change

| Expectation (from the spec) | Reality (verified) | Required change |
|---|---|---|
| ~27-provider pool with rank, sign-up link, live model line ("live: qwen/qwen3.8-27b (+5 more)") | 15 in the vault dict, 9 in the UI, models hardcoded | Registry with all 27 + live `/models` fetch per provider (FIX-7) |
| Routing class + cost class per provider (Tier 1 Fastest … Tier 26 Media; aggregator; credit) | Two disagreeing internal tables (`gateway_status()` tiers 1a–9; UI presets) | One registry field set: display rank, routing class, cost class, limit spec, verification requirement |
| Credential masked (`***PV76`), saved state, `Credential active` On/Off toggle | Masking real; **toggle exists but has no effect** (D1) | Toggle with immediate eviction (FIX-1) |
| Connection column: `Online · 278ms` + timestamp, `Not tested`, `Not configured` | No connection state anywhere | Per-provider last-test state: result, latency, timestamp (B3) |
| Actions per row: `Test`, `Configure`, `+ Add / replace key` | Configure/save real but unvalidated; Test absent | Validate-on-save (FIX-4) + row Test (B1) |
| `Test all providers` | Endpoint exists (8 providers), **no UI caller** | Button wiring + extend to all registry providers |
| `Refresh live models` | **Does not exist** | Real `GET /models` per provider → verified model lists (FIX-7) |
| `Encrypt stored keys` | Encryption unconditional on save; no legacy-scan action | Backfill action: find plaintext/legacy rows → encrypt → report counts (B1) |
| `API Keys Vault` (specialty keys: Exa, NASA, Pexels, Gumroad, Stripe, Resend, Gmail, Cloudflare, HF Inference, ElevenLabs, Groq Audio) with masked key, saved date, replace input, Get-a-key, Test, Save | **None of it exists**; three integrations have no code at all (D12, D13) | Vault CRUD + real tests + build the three missing integrations (FIX-8) |
| Payment/Credit Keys: Together/OpenAI/DeepSeek with `Used this month: N tokens`, grant label, monthly grant tokens, notes, Save | **Does not exist** (D14) | Grant model with real usage counters + ceiling enforcement (FIX-9) |
| Specialty Tools (staff tier 8+): Pexels search + Run, etc. | Absent from this page (Pexels search exists in VideoStudio) | Tools panel executing through vault keys (B8) |
| Usage Log: requests/succeeded/success-rate/tokens today/tokens window + per-request fallback chains | Endpoint reads `ai_usage_log`; UI shows blank provider/status; no counters, no chains, no tokens (D6) | Choke-point writer + aggregates + fixed UI (FIX-5) |
| `model:"auto"` → verified no-cost providers only | Missing (D3, D4) | Routing engine + `/v1/chat/completions` (FIX-2, FIX-3) |
| Monetization/BYOK visible + testable, excluded unless policy authorizes | BYOK visible/testable (real); no policy switch exists | Policy flags, default excluded, owner-flippable, audited (B4) |
| Gemini 15 RPM, Mistral 1M tokens/month enforced | Labels only (D10, D11) | DB-backed rolling-window counters, enforced pre-dispatch, human-editable (FIX-6) |

---

## 3. Design decisions (from the findings — these are what make the fixes real)

**D-A · The database is the only source of truth for credentials; the process is a cache.**
Import-time globals (`GROQ_API_KEY` etc.) are why revocation is impossible and why multi-replica deploys drift.
Credentials resolve at **call time** from a short-TTL snapshot of the vault collections (env fills gaps only for
providers with no vault row). A write invalidates the snapshot in its own replica immediately and everywhere
within the TTL. This is the root fix behind FIX-1 and it also removes the D2 multi-replica hole. The existing
`KeyPool` gains an `evict(key)` so rotation state cannot resurrect a revoked key.

**D-B · One registry, DB-backed, human-editable.** Collection `api_provider_registry`, one doc per provider:
`provider_id, display_name, signup_url, display_rank, routing_class, cost_class, base_url, default_model,
models_verified: [], models_verified_at, verification: {mode, last_result, last_latency_ms, last_checked_at},
credential_state: {configured, active, masked, saved_at, verified_at}, limits: {rpm, monthly_tokens, grant_tokens},
policy: {auto_routable, requires_policy_authorization}`. Seeded from code constants, then owned by the owner
through the UI. `llm_gateway`'s tier table, `provider_gateway.PROVIDERS`, and the UI presets all render from it —
this is what kills D8/D9 drift permanently.

**D-C · Routing classes** (the owner's "same routing class" requirement):
`no_cost_free` (Groq, Cerebras, SambaNova, Gemini, Grok, Cohere, Mistral, Together-free, OpenRouter-free,
HuggingFace) — auto-eligible when configured + active + verified + within limits;
`credit_grant` (Together, OpenAI, DeepSeek credit pools) — visible + testable, excluded from auto unless policy
authorizes; `aggregator` (OpenRouter — operator-selected model) — auto-eligible only for its verified free
model, policy-controlled; `monetization` / `byok` — always excluded from platform auto-routing unless the policy
flag explicitly authorizes; `media_specialty` (Cloudflare, HF-inference, Pollinations, ElevenLabs, Groq audio) —
not chat-routable; `kb_fallback` — always last.

**D-D · "Verified" is a state machine, not a label.** `configured → tested (live 1-token call) → verified
(models fetched from the provider's own endpoint and the intended model present)`. Only `verified` providers
enter auto-routing. A failed test or a model-list fetch failure demotes to `unverified` with the reason shown.
This is the "model-verified, provider-aware" failover the spec demands.

**D-E · One writer, one choke point.** Every chat path funnels through `call_llm`; the usage record is written
once there: `request_id, user_id, endpoint, model_requested, provider, model_served, result, reason,
prompt_tokens, completion_tokens, latency_ms, cost_class, fallback_chain[], created_at`. The 7 ad-hoc writers
become thin wrappers that pass their endpoint label (no second schema). Counters are computed from the log, so
the Usage Log numbers cannot disagree with the rows.

**D-F · Limits live in Mongo, enforced pre-dispatch.** Rolling-minute request counters (Gemini 15 RPM) and
rolling-month token counters (Mistral 1M; credit grants) in `api_provider_limits` — not process memory, because
counters in memory are wrong on multi-replica and reset on deploy. Token counts come from provider `usage`
where reported, from a local tokenizer estimate where not (HuggingFace), so the limits are real rather than
zero-forever (D11).

---

## 4. FIXES — root cause, not workaround (each with an executed DoD)

**FIX-1 · Real revocation (D1, D2).** Call-time credential resolution from the TTL vault snapshot (D-A) +
`KeyPool.evict`. DoD: save key → status available; DELETE → the **next call in the same process** fails over
(proved by which provider serves a test message) and `gateway/status` shows not-available without restart;
second replica (second server process on another port, same DB) shows the same within the TTL; a disabled key
never reappears after a replica restart.

**FIX-2 · `model:"auto"` + `POST /v1/chat/completions` (D3, D4).** OpenAI-compatible route; `auto` selects the
highest-ranked provider that is `verified`, `no_cost_free` (or policy-authorized), and within limits; explicit
models route to their provider or 404 with the available list. DoD: executed request returns a real reply and
the response + usage row record the serving provider and chain; `model:"nope"` → 404 + model list.

**FIX-3 · Ranking that routes (D5).** Router reads `api_provider_registry` order (TTL cache, DB authoritative);
validation refuses a ranking whose top entries have no usable credential; every change audits and takes effect
on the next call. DoD: reorder via the API → the next auto call comes from the new order (proved with two
configured keys).

**FIX-4 · Validate on save (D7).** Live 1-token test before persisting; failure returns the provider's reason
and stores nothing; success records `verified_at` and the usable models. DoD: invalid key → 4xx, `api_keys`
unchanged, status unconfigured; valid key → stored, masked, verified.

**FIX-5 · Real usage log (D6).** Choke-point writer (D-E), `created_at` index, UI reads the fields that exist.
DoD: 10 calls with the primary disabled mid-run → 10 rows with chains; counters equal a direct Mongo count;
tokens non-zero for a non-HF provider.

**FIX-6 · Enforced limits (D10, D11).** Mongo rolling-window counters + local token estimate where the provider
reports none; values owner-editable; exhaustion excludes the provider from auto-routing and is shown in its row.
DoD: 16 Gemini requests in a minute → the 16th is served elsewhere and the row shows `limit_reached`; Mistral
monthly counter crossing the cap → same.

**FIX-7 · One registry + live models (D8, D9).** Registry seeded from the current constants, extended to the
owner's 27; Refresh live models does real `GET /models`; unconfigured/unverifiable providers render as
`Not configured` / `Not tested`; the four disagreeing model strings collapse to the registry's
`models_verified` list. DoD: with two keys configured, Refresh shows real provider model IDs; auto-pool equals
exactly the verified set.

**FIX-8 · Specialty vault (D12, D13).** All 11 specialty credentials vaulted (same Fernet path), masked,
replaceable, testable, toggleable with FIX-1 eviction; integrations read vault-then-env; the three missing
integrations (Exa search, Cloudflare Workers AI image/audio, HF image/music inference) are built against their
real APIs. DoD: save a Pexels key via the UI → Specialty Tools Pexels search returns real photos; Gmail test
send delivers; Exa search returns real results; disable → tool reports not-configured without restart.

**FIX-9 · Payment/Credit Keys with real accounting (D14).** Grant label, monthly grant tokens, notes per
Together/OpenAI/DeepSeek; `used_this_month` computed from actual charged calls; grant ceiling enforced like
FIX-6. DoD: 1 000-token grant → after traffic exceeds it the row shows overage and the provider leaves the
auto-pool until reset.

**FIX-10 · Structural cleanup (D15–D20).** Split `api_keys` (provider credentials vs customer API keys) with
indexes; add the missing indexes; migrate or delete the write-only legacy path; **remove the Anthropic
references** (policy, absolute); start `run_monitor_loop()` with its state visible in the UI; move the sidebar
link to the executive section; make Refresh refresh the open tab.

---

## 5. BUILD — the surface, element by element (zero decorative elements)

Every element below is bound to the registry or the vault; every control writes through the API and takes
effect on the next request; nothing renders a static string where state belongs.

**B1 · Header actions.** `Test all providers` (real pings across the whole registry, per-provider result +
latency + timestamp), `Refresh live models` (real `GET /models` per configured provider), `Encrypt stored keys`
(scan for legacy plaintext rows → encrypt → report counts; refuse new plaintext — refusal path exists).
Subtitle states the policy truth: platform-owned pool, credentials encrypted at rest, masked below.

**B2 · Filter** — free-text over provider name/model/tier/status.

**B3 · Provider table** — one row per registry provider: rank (#), provider + sign-up link, live model line
(`live: <model> (+N more)` from `models_verified`), routing class badge (Tier 1 Fastest … Tier 26 Media,
Aggregator, Credit), Status (`CONFIGURED`/`NOT CONFIGURED`/`ACTIVE`/`LIMIT REACHED`), Credential (`***` last-4
+ saved date), Credential-active toggle (FIX-1), Connection (last test: `Online · <ms>` or reason +
timestamp; `Not tested`/`Not configured`), limit badge where one applies (`Limit: 15 req/min`,
`Limit: 1,000,000 tokens/month`), Actions: `Test` · `Configure` (validates) · `+ Add / replace key`.

**B4 · Routing policy panel (human controls, all with effect).** The editable ranking that actually routes
(FIX-3); per-provider limit values editable and enforced (FIX-6/FIX-9); the hourly budget (already live);
policy switches for whether credit/aggregator/monetization/BYOK classes may serve auto-routing — **default:
excluded, exactly as specified** — owner-flippable, audited, and visibly reported as the reason a provider is
skipped.

**B5 · `POST /v1/chat/completions`** — OpenAI-compatible request/response; `model:"auto"` per the class policy;
every response and usage row records the serving provider and the full fallback chain.

**B6 · Payment / Credit Keys** — Together AI, OpenAI, DeepSeek rows: `Used this month: N tokens` (from real
accounting), grant label, monthly grant tokens, notes, dirty-state indicator, Save.

**B7 · Specialty Keys vault** — the 11 specialty credentials: description, masked key + saved date, replace
input, `Get a key` link, `Test` (real integration), `Save`, active toggle.

**B8 · Specialty Tools** — the integrations these keys power, executing through the vault: Pexels search + Run,
Gmail test send, NASA APoD fetch, Gumroad/Stripe status, Exa search, Cloudflare image gen, HF music/image gen.

**B9 · Usage Log** — Requests (in window), Succeeded, Success rate, Tokens today, Tokens (window), and the
per-request grouped fallback chains — all computed from the log written at the choke point.

---

## 6. Sequencing (one PR each; owner reviewable)

| PR | Content | Depends on |
|---|---|---|
| G0 | FIX-10 structural: Anthropic removal, nav fix, indexes, collection split, Refresh-button fix | — |
| G1 | FIX-1 revocation (call-time resolution + eviction + snapshot TTL) | — |
| G2 | FIX-4 validate-on-save + FIX-7 registry + live models + full 27-provider coverage | G1 |
| G3 | FIX-3 ranking that routes + FIX-2 auto + `/v1/chat/completions` | G2 |
| G4 | FIX-5 usage log + FIX-6 limits + FIX-9 credit accounting | G2 |
| G5 | FIX-8 specialty vault + the three missing integrations + B8 tools | G1 |
| G6 | B3/B4/B6/B7/B9 UI completion on the registry | G2–G5 |
| G7 | Monitor loop live + legacy path migration decision (owner) | G1 |

## 7. End-to-end acceptance path (the owner's walkthrough — every step executed)

1. Open `/admin/providers` as executive_admin: all 27 providers render with real states; a free-tier admin
   never reaches the page.
2. `Test all providers` → every configured provider returns a real result with latency; unconfigured report
   `no_key`. `Refresh live models` → real model lists appear on the configured rows.
3. Configure a Groq key with a deliberate typo → rejected with the provider's reason, nothing stored. Configure
   the real key → stored encrypted, masked, verified, row shows `Online · <ms>`.
4. `POST /v1/chat/completions {model:"auto"}` → real reply from the verified no-cost provider; response and
   Usage Log both name the provider and show the chain.
5. Reorder the ranking in the policy panel → the next auto call follows the new order.
6. Turn the Groq credential off → the next call fails over immediately; the row shows inactive; a second
   server process sees the same within the TTL; restart does not resurrect it.
7. Drive 16 Gemini requests in a minute → the 16th is served by another provider and Gemini's row shows
   `Limit: 15 req/min — limit reached`.
8. Usage Log: requests/succeeded/success-rate/tokens-today/tokens-window match direct Mongo counts; chains are
   grouped per request.
9. Specialty: save a Pexels key → Pexels search in Specialty Tools returns real photos; save Gmail app
   password → test send delivers; Exa search returns real results.
10. Credit keys: set a 1 000-token monthly grant → exceed it → row shows overage and the provider leaves the
    auto-pool until reset.
11. Inspect Mongo: every credential ciphertext, no plaintext rows after `Encrypt stored keys`; no key material
    in any response, log line, or error.

## 8. Verification standard

- Each fix's DoD is a **run**, pasted into the PR body with real output (recipe:
  `docs/RUNTIME_AUDIT_2026-10-10.md` §5; exec account promoted in the local test DB only).
- Production: read-only probes only — new endpoints verified to require the intended role; no accounts, no
  writes.
- Guard rails: `frontend/scripts/{academy-open-access,route-integrity,nav-integrity}.js`, Academy suite
  (52 tests), `craco build`.
- Report format: asked vs delivered, executed evidence, what is NOT verified, own bugs as findings. A control
  that cannot be exercised through the interface does not count as delivered.
