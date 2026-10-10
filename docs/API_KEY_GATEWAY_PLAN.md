# API KEY GATEWAY — BUILD & FIX PLAN (`/admin/providers`)

**Requested:** platform-owned global provider pool with full admin/exec control — one surface for every AI
credential and the gateway that routes them; `POST /v1/chat/completions` with `model: "auto"` selecting only
verified providers in no-current-platform-cost classes; monetization/BYOK providers visible and testable but
excluded unless policy authorizes routing; model-verified, provider-aware failover; Gemini 15 RPM and Mistral
1M tokens/month enforced; credentials encrypted at rest and never leaving the server.

**Rule set applied:** fixes, not workarounds. No cosmetic metadata fixes. No "make it honest" relabelling of
inert code. Every control must be alterable, verifiable, and updatable by the owner **through the interface** —
a registry the owner cannot edit, verify, or push from the UI is a hardcoded mock. Zero-mock enforcement.

**Starting point is verified, not assumed** — everything in §0 was executed on 2026-10-10 against a live local
server + Mongo with a locally-promoted executive account (local test DB only; no production writes).

---

## 0. Verified starting point (runtime evidence)

| Surface | Status | Executed evidence |
|---|---|---|
| Route `/admin/providers` → `ProviderGateway.jsx`, exec-gated frontend (`ROLE_RANK` 7) and backend (`_exec` 403) | **REAL** | `App.js:510`; page renders |
| `GET /api/providers/quick-setup/status` | **REAL** | 200, returns **15** providers (9 AI + stripe/lemon/gumroad + sambanova/openrouter/huggingface), masked key, source |
| `POST /api/providers/quick-setup` (save key) | **REAL (partial)** | 200 `{configured:true, key_masked:"••••7890"}` — Fernet-encrypted, upserts `db.api_keys`, reloads gateway. **No validation on save** — a typo'd key is accepted and reported Active |
| `PATCH/DELETE /api/providers/keys/by-provider/{type}` | **REAL write, broken effect** | after `DELETE`, `GET /api/admin/gateway/status` still shows groq `available: true` — **the deleted key keeps serving traffic until process restart**. Same for disable. Revocation is not real |
| `GET /api/admin/gateway/status` + `/budget` + `/reset-budget` | **REAL, live effect** | budget cap 200 000, `tokens_used` live; PATCH budget takes effect immediately |
| `GET/PATCH /api/admin/gateway/ranking` | **REAL persistence, ZERO routing effect** | returns the 12-provider list; `call_llm` order is the hardcoded tuple `("groq","cerebras","sambanova","gemini")` (`ai/llm_gateway.py:743`) — the persisted ranking is never read by the router. The product's own UI admits it ("Use API Keys tab to push/revoke/disable providers to enforce hard routing") |
| Failover chain in-process | **REAL** | rotation + per-key cooldown + KB fallback |
| `GET /api/ai/provider-test` | **REAL endpoint, no UI caller** | live-tests 8 providers, returns `{ok, reason}` per provider |
| `POST /v1/chat/completions` | **MISSING** | **404** executed |
| Model `"auto"` selection | **MISSING** | `call_llm(model=...)` accepts the param and ignores it; every tier passes its own hardcoded model constant |
| Usage log | **PARTIAL/broken** | endpoint reads `ai_usage_log`; the UI renders `log.provider_id` / `log.result` — fields **no writer produces** (writers store `provider`; there is no `result`). Every row renders blank provider/status. No counters, no tokens, no fallback chains, no index. `ai_usage_log` count = 0 in the audited DB despite executed AI calls |
| Specialty keys (Exa, NASA, Pexels, Gumroad, Stripe, Resend, Gmail, Cloudflare Workers AI, HF Inference, ElevenLabs, Groq Audio) | **MISSING** | env-var-only reads at request time (`nasa_observatory.py:43`, `studio.py:612`, `server.py:769-890`, `ai/persona_tts.py:36`); no vault storage, no CRUD, no masked display, no test surface |
| Payment/Credit Keys (Together/OpenAI/DeepSeek grant label, monthly grant tokens, used-this-month) | **MISSING** | no such data model anywhere |
| "Refresh live models" | **MISSING** | no endpoint fetches provider catalogs; the page's "Refresh" only re-reads DB/env status |
| "Test all providers" / per-row Test / Configure / Credential-active toggle | **MISSING in UI** | backend test endpoints exist (`/api/ai/provider-test`, `/api/providers/keys/{key_id}/test`) with zero frontend callers on this page |
| Gemini 15 RPM, Mistral 1M tokens/month | **NOT ENFORCED** | labels only — no code reads either number; the only Gemini mechanism is a cooldown after a real 429 |
| Token accounting | **PARTIAL** | provider-reported `usage` only; HuggingFace returns 0/0 by construction; no local counter |
| Provider coverage | **9 UI cards of 15 statuses** | `sambanova`, `openrouter`, `huggingface` statuses are returned and silently dropped |
| Model/tier strings in UI | **STATIC** | three different Groq model names in three files (`llm_gateway.py:127` `openai/gpt-oss-120b`, `provider_gateway.py:17` `llama-3.3-70b-versatile`, `byok.py:60` same, page preset "Llama 3.3 70B"); Gemini drift (docstring 2.0 vs constant `gemini-3.6-flash`) |
| Keyvault / Fernet at rest / masking / no raw-key leakage | **REAL, well-built** | `keyvault.py`; `"••••"+value[-4:]`; projections exclude `encrypted_key`; no log emits a key |
| Nav defect | **BROKEN** | sidebar link sits in the `minRole:"admin"` section (`AppShell.jsx:214`) while the route requires `executive_admin` — an admin clicks and is bounced to `/dashboard` |
| Anthropic references | **POLICY VIOLATION, present** | `ai/ai_cost_tracker.py:13-18` prices claude models; `wai_institute/pipelines/conversational_engine.py:177-187` has a dead `client.messages.create(model="claude-haiku-4-5")` (client never imported). AGENTS.md forbids Anthropic on this platform |
| `run_monitor_loop()` provider health auto-revoke | **REAL code, never started** | whole-word search finds only its definition |
| `db.api_keys` schema collision | **DEFECT** | provider keys (`provider_id`/`encrypted_key`) and customer API-as-a-service keys (`key_hash`/`tier`) share the collection; `reload_provider_keys` scans both |
| Legacy collections | **WRITE-ONLY** | `/api/providers/keys*` UI writes `ai_providers`/`ai_provider_keys`; the gateway only reads `api_providers`/`api_keys` — keys saved there never load |
| Indexes | **MISSING** | none for `api_keys`, `api_providers`, `ai_usage_log`, `provider_rankings` |

---

## 1. FIXES (each is a root-cause fix with an executed DoD — no workarounds)

### FIX-1 · Revocation must be real (highest severity)
**Defect (executed):** disable **and** delete leave the key live in the process; status flips back only after
restart. On a compromised key, the admin panel lies while traffic keeps flowing.
**Fix:** `ai/llm_gateway.reload_provider_keys` currently only fills empty globals
(`llm_gateway.py:101-103`). Add a real eviction path: reconcile the process globals against the DB on every
reload — set from DB when present, **clear the global when the row is absent or `status != "active"`** — and
make `PATCH/DELETE` call that reconciliation. The next AI call after a delete must fail over to the next
provider.
**DoD (executed):** save key → `gateway/status` shows available; DELETE → status shows **not available**
*without restart* and the next `POST /api/ai/chat` fails over (reply comes from the next provider or KB, not
the deleted key); same for disable; restart-safe (DB is the source of truth).

### FIX-2 · `model: "auto"` must actually route
**Defect (executed):** `POST /v1/chat/completions` 404; `call_llm` ignores its `model` argument.
**Fix:** implement selection in the gateway: `model="auto"` → the highest-ranked **verified** provider whose
**cost class is no-current-platform-cost** and whose live model list contains a usable model; explicit model
names route to the provider that serves them; unknown model → structured 404 error, not a silent substitute.
**DoD (executed):** `POST /v1/chat/completions {model:"auto"}` returns a real reply and the response records
which provider served it; `model:"nonexistent-model"` → 404 with the list of available models.

### FIX-3 · Ranking must be a real control, not a stored preference
**Defect:** `/admin/gateway/ranking` persists; the router never reads it. This is the "glorified hardcoded
mock" the owner named — a panel that looks like control and changes nothing.
**Fix:** the router reads the persisted ranking (from `db.provider_rankings`, cached with a short TTL, DB is
authoritative) instead of the hardcoded tuple; validation prevents saving a ranking containing providers with
no usable credential; every change audits (who/when/what) and takes effect on the next call.
**DoD (executed):** reorder two providers via the API/UI → the very next auto-routed call uses the new order
(prove by testing with two configured keys and checking the recorded provider).

### FIX-4 · Key save must validate before accepting
**Defect:** `POST /providers/quick-setup` accepts any non-empty string and reports Active.
**Fix:** run the existing real test (`byok.py:246` pattern / `provider-test` caller) against the key before
persisting; on failure return the provider's error and do **not** store; on success store and mark
`verified_at` + the models the key can actually use.
**DoD (executed):** save a deliberately invalid key → 4xx with the provider's reason, `api_keys` unchanged,
status still unconfigured; save a valid key → stored, masked, verified timestamp shown in the UI.

### FIX-5 · Usage log must record and display real facts
**Defect (executed):** UI reads `provider_id`/`result`; writers store `provider` and no result; no tokens, no
fallback chains, no counters; no index.
**Fix:** one writer at the single choke point where the gateway completes a call, recording: `request_id`,
`user_id`, `endpoint`, `model_requested`, `provider`, `model_served`, `result` (success/fail + reason),
`prompt_tokens`, `completion_tokens`, `latency_ms`, `cost_class`, `fallback_chain` (ordered list of attempted
providers), `created_at`. Aggregates (requests in window, succeeded, success rate, tokens today, tokens in
window) computed from the log. Add the `created_at` index. Fix the UI to read the fields that exist.
**DoD (executed):** make 10 calls (some forced to fail by disabling the primary) → log shows 10 rows with
chains, counts match exactly, window counters match a direct Mongo count, UI renders provider + result.

### FIX-6 · Enforce the two named limits for real
**Defect:** Gemini 15 RPM and Mistral 1M tokens/month are labels; nothing counts.
**Fix:** per-provider counters in Mongo (requests in the rolling minute for Gemini; tokens in the rolling
month for Mistral) enforced before dispatch, human-editable values, surfaced in the UI with live usage; on
exhaustion the router skips that provider (and the UI shows why).
**DoD (executed):** with a Gemini key configured, drive 16 requests in a minute → the 16th is served by
another provider and the log/Gemini row shows `limit_reached`; Mistral: drive >1M provider-reported tokens in
the month → same.

### FIX-7 · Kill the drift: one registry, live models
**Defect:** model/tier strings hardcoded in four places; 9-of-15 provider coverage.
**Fix:** a single provider registry (id, name, models, tier/routing class, cost class, limits, signup URL,
verification requirements, credential state) as the only source; the UI renders from it; "Refresh live
models" fetches each configured provider's `GET /models` (real HTTP) and records `models_verified_at`;
a provider whose model list cannot be fetched is marked unverified and excluded from auto-routing.
**DoD (executed):** with 2 providers configured, Refresh live models → their rows show the real model IDs
returned by the providers; an unconfigured provider shows "Not configured / Not tested"; the auto-routing
pool equals exactly the verified set.

### FIX-8 · Specialty keys must live in the vault and be real controls
**Defect:** Exa, NASA, Pexels, Gumroad, Stripe, Resend, Gmail, Cloudflare Workers AI, HF Inference, ElevenLabs,
Groq Audio are env-only: no CRUD, no masking, no test, and the owner cannot update them from the platform.
**Fix:** store them encrypted at rest in the same vault (same Fernet path), masked display, replace-key flow,
Test button wired to the real integration tests that already exist (Resend/Gmail test-send at
`ops_admin.py:214-260`, Pexels search at `studio.py:612`, NASA, Gumroad, Stripe, HF, ElevenLabs, Groq audio);
integrations read the vault first, env as migration fallback; each row shows saved date and credential-active
toggle with the same eviction guarantee as AI keys.
**DoD (executed):** save a Pexels key via the UI → Specialty Tools Pexels search returns real photos; save a
Gmail app password → test send delivers; disable → the tool reports not-configured without a restart.

### FIX-9 · Payment / Credit Keys with real usage counters
**Fix:** grant label, monthly grant tokens, notes, and **used-this-month computed from actual gateway calls**
charged to that credit pool (not a manual field). Enforce the monthly grant ceiling in routing the same way
as FIX-6.
**DoD (executed):** set a 1 000-token monthly grant on Together → after traffic exceeds it, the row shows the
overage and Together is excluded from auto-routing until reset.

### FIX-10 · Structural fixes around the vault
- Split `api_keys` into `api_provider_keys` (encrypted credentials) and the customer API-as-a-service keys
  (rename/namespace), with indexes on both; `reload_provider_keys` must scan only its own collection.
- Add the missing indexes (`api_keys`, `api_providers`, `ai_usage_log.created_at`, `provider_rankings`).
- Legacy `/api/providers/keys*` writers: either migrate to the vault collection or delete the dead path — no
  silent write-only collections left behind.
- **Remove the Anthropic references** (`ai_cost_tracker.py` rate rows, `conversational_engine.py` dead client
  call) — platform policy, absolute.
- Start `run_monitor_loop()` (real per-provider health probe + auto-revoke on 401/403) with its state visible
  in the UI.
- Fix the nav defect: move the sidebar entry to the executive section so an admin never sees a link that bounces.
- Fix the page's Refresh button so it refreshes the tab being viewed.

---

## 2. BUILD — the API Key Manager surface (live-wired, zero mock)

Everything below is rendered from the registry and the vault; every control writes through the API and takes
effect on the next request; nothing is a static string pretending to be state.

**B1 · Header controls** — `Test all providers` (wires the existing real `/api/ai/provider-test`, extended to
every provider in the registry), `Refresh live models` (real `GET /models` per provider), `Encrypt stored keys`
(backfill that finds legacy plaintext rows, encrypts them with the vault Fernet, reports counts; refuses
plaintext storage going forward — the refusal path already exists).
**B2 · Filter** — free-text filter over the provider table.
**B3 · Provider table** — one row per registry provider: Provider (+ sign-up link), Model (live-verified),
Tier/routing class, Status (configured / verified / limit-reached / not configured), Credential (`••••` last-4),
Credential-active toggle, Connection (last test result + latency + timestamp), Actions: Test · Configure ·
Add/replace key. Configure validates before accepting (FIX-4). Disable evicts immediately (FIX-1).
**B4 · Routing policy panel (human controls, all real):** the editable ranking that actually routes (FIX-3);
the per-provider limits (Gemini RPM, Mistral monthly tokens, Together/OpenAI/DeepSeek grant ceilings) editable
in the UI and enforced (FIX-6/FIX-9); the hourly token budget (already live); policy switches deciding whether
monetization/BYOK providers may ever serve auto-routing (default: excluded, exactly as specified) — off by
default, owner-flippable, audited.
**B5 · `POST /v1/chat/completions`** — OpenAI-compatible request/response (messages, model, stream optional);
`model:"auto"` selects only verified providers in no-current-platform-cost classes; BYOK/monetization
providers remain visible and testable but are excluded unless the policy authorizes them; every response
records the serving provider and the full fallback chain.
**B6 · Payment / Credit Keys** — Together AI, OpenAI, DeepSeek: grant label, monthly grant tokens, notes,
used-this-month from real accounting (FIX-9).
**B7 · Specialty Keys** — the 11 specialty credentials, vaulted, masked, tested, toggleable (FIX-8).
**B8 · Specialty Tools** — the real integrations these keys power (Pexels search with Run, Gmail test send,
NASA APoD fetch, Gumroad/Stripe status) executing through the vault keys.
**B9 · Usage Log** — requests in window, succeeded, success rate, tokens today, tokens in window, and the
per-request fallback chains, grouped per request so each chain is visible (FIX-5).

---

## 3. Non-negotiable enforcement rules for the build

1. **No mock, no stub, no placeholder.** If a control exists in the UI it must read/write a real endpoint with
   an observable effect. If it cannot be real yet, it does not ship.
2. **No cosmetic fixes.** Relabelling inert code, hiding it, or documenting it as "by design" is a violation,
   not a delivery.
3. **Human control is the acceptance test:** every constant above (ranking, limits, budgets, policy switches,
   credentials) must be changeable by the owner through `/admin/providers` (or an existing exec console), with
   the change effective without a restart and audited.
4. **Executed proof per element** — each row's DoD in §1 names the run that proves it.
5. **Secrets never leave the server:** masked display only, encrypted at rest, no key in any response body,
   log, or error message.

---

## 4. Sequencing (one PR each, owner reviewable)

| PR | Content | Depends on |
|---|---|---|
| G0 | FIX-10 structural: Anthropic removal, nav fix, indexes, collection split, Refresh-button fix | — |
| G1 | FIX-1 eviction + FIX-4 validate-on-save (the vault becomes truthful) | — |
| G2 | FIX-7 registry + Refresh live models + full provider coverage (26+ rows) | G1 |
| G3 | FIX-3 ranking that routes + FIX-2 `model:"auto"` + `POST /v1/chat/completions` | G2 |
| G4 | FIX-5 usage log + FIX-6/FIX-9 limits with real counters | G2 |
| G5 | FIX-8 specialty vault + B8 specialty tools | G1 |
| G6 | B3/B4/B6/B7/B9 UI completion on the registry | G2–G5 |
| G7 | monitor loop live + legacy path migration decision (owner) | G1 |

## 5. Verification standard for every PR

- Local: server + Mongo (recipe in `docs/RUNTIME_AUDIT_2026-10-10.md` §5), exec account promoted locally,
  each DoD executed with real output pasted into the PR body.
- Production: read-only probes only; `/v1/chat/completions` and every new endpoint verified to require the
  intended role; no accounts created, no data written.
- Guard rails: `frontend/scripts/{academy-open-access,route-integrity,nav-integrity}.js` + Academy suite
  (52 tests) + `craco build`.
- Report format (unchanged): asked vs delivered, executed evidence, what is NOT verified, own bugs as findings.
