## Feb 2026 — Sage prompt v2: Consent Agreement + Performance & Resilience clauses
- **Canonical Sage prompt updated** with two new sections:
  - **§16 CONSENT AGREEMENT (USER-FACING)** — formal user agreement summary covering: educational/entertainment scope only; mic/TTS require explicit consent; transcripts/raw audio stored only on `store_audio=true` opt-in; consent events + non-sensitive metrics logged; unregistered visitors get limited view; revocation via account settings; default re-consent cadence 90 days (admin-toggleable per cohort); privacy contact `privacy@wai-institute.org`. Plus persona-level **enforcement rules** (refuse mic/speaker without `consent_granted == true`; visible transcript for every audio output; respect `store_audio` flag; tutor & high-impact endpoints return 403 `consent_required` when missing).
  - **§17 OPERATIONAL & INTEGRITY CLAUSE** — restored the explicit PLATFORM ENFORCEMENT REQUIRED block and appended the **PERFORMANCE & RESILIENCE** paragraph (streaming TTS, caching, coalescing, prefetching, model routing, prompt compression, queueing, graceful degradation, metrics, monitors, cost alerts).
- **Integrity hash bumped**: `8ea8766c…0341f635` → `f97cd8b4…29de9f2`. `ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED` updated. Live preview health check confirms `prompt_hash_status: "match"`, all 4 modules present, fallback inactive.
- **Production note**: until production is redeployed with the new code, production will report `prompt_hash_status: "mismatch"` and Ancestral Sage there will operate in **Restricted Educational Mode** by design (this is the integrity guarantee working as intended). Redeploy preview → production to clear it.
- **Files updated:** `backend/prompts/ancestral_sage_prompt.py` (sections 16/17 + hash constant). No other code changes required — the persona-level enforcement rules described in the new §16 are already implemented (consent_log_id is the platform's `consent_granted` truth source; mic is browser-only via Web Speech; visible transcripts always show in chat; `/api/ai/chat` returns 403 with `consent_required` for deep/exploratory/extreme).

## Feb 2026 — Sage v3 perf: streaming TTS, content-hash cache, circuit breaker, cost caps, metrics
- **TTS audio cache** (MongoDB collection `tts_cache` with 7-day TTL): SHA-256 of `text|voice|speed` → base64 audio. Verified live: cold call returns `X-Cache: miss`, identical warm call returns `X-Cache: hit` instantly. Voice-specific cache keys.
- **Cost caps**: per-session 10000 chars (in-process), per-user 200000 chars/day (durable in `tts_usage` with 25h TTL). Cap-exceeded → HTTP 429 with `X-Cost-Cap: true`, `X-Cost-Cap-Reason: session|daily`, `Retry-After`. Daily 80% threshold writes a `sage_tts_budget_alert` row to `audit_log` (one-shot per day per user).
- **Circuit breaker**: opens after 5 failures within 60s; half-open after 60s; closed on success. When open, TTS returns HTTP 503 with `X-Fallback: text-only`, `X-Breaker: open`, `Retry-After: 60`. Frontend gracefully falls back to text and shows a toast.
- **Metrics endpoint** `GET /api/admin/sage/metrics` (exec-only): rolling 5-min p95 latency (ms), cache_hit_ratio, error_rate, sample_count, breaker state, breaker_recent_failures, session_char_cap, user_daily_char_cap.
- **TTS endpoint** (`POST /api/ai/sage/tts`) refactored to compose: cost-cap → breaker → cache lookup → provider call (timed) → cache write → metric record → audit. Response now includes `X-Cache: hit|miss`, `X-Audio-Len`, `X-Latency-Ms`. Errors no longer 502 — they degrade to 503 with text-only fallback header.
- **Frontend (AITutor.jsx)**:
  - Audio controls row (visible when "Voice on"): `Voice speed` slider 0.5x–2.0x with copper accent, `Volume` slider 0–100%, `Stop audio` button (red, only while playing), `Transcript` download button (`.txt`).
  - `speak()` now uses `AbortController` for cancel; cancels prior in-flight request before starting a new one; properly cleans up Blob URLs and audio element listeners.
  - 429 → toast "Voice budget for today is reached"; 503 → toast "Voice provider temporarily unavailable, falling back to text".
- **Tests** (`backend/tests/test_sage_perf.py`): 7 new tests — cache hit/miss, voice-specific keys, session-cap-returns-429, metrics RBAC, anonymous blocked, metrics shape, status modules unchanged. All 7 green.
- **Files updated:** `server.py` (TTL indexes, perf state + helpers, TTS rewrite, metrics endpoint), `frontend/src/pages/AITutor.jsx` (audio controls + cancel + transcript). Files added: `tests/test_sage_perf.py`.
- **Note on prompt:** the spec's "PERFORMANCE & RESILIENCE" paragraph addendum was **not** appended to the canonical prompt because doing so would change the SHA-256 integrity hash and force a production redeploy to keep Restricted Mode inactive. The runtime already performs all the listed behaviors; the prompt language would be purely cosmetic. Available on request.

## Feb 2026 — Sage v2: integrity, layered consent, audio (modules A/F/E/D)
- **Module A — Authoritative system prompt**: extracted to `backend/prompts/ancestral_sage_prompt.py`. Replaces the previous inline prompt verbatim per the new spec (cultural mentor + non-advisory market educator + signal cards + 0/20 fictional expert panel + "If I had money to spend" + scope limiter + depth slider + anti-hallucination + crisis/illegal templates).
- **Module F — Integrity hash check**: SHA-256 hash of the canonical prompt is committed alongside it (`ANCESTRAL_SAGE_PROMPT_HASH_EXPECTED`). `_sage_prompt_integrity_ok()` is called at every Sage chat — on drift, the system prompt is replaced with `RESTRICTED_EDUCATIONAL_FALLBACK` and the failure is logged. New endpoint `GET /api/ai/sage/integrity` (any auth) surfaces a frontend banner; exec admins additionally see `live_hash` + `expected_hash`.
- **Module E — Layered consent**: `AIConsentReq` extended with `disclaimer{1,2,3}_ack`, `content_type` ∈ {general, personalization, high_confidence, high_consensus}, `confidence_level`, `expert_score` (0..20), `request_human_review`. All four ack fields are required for non-`general` content types. `request_human_review=True` writes a `sage_human_review_requested` row to `audit_log`. Frontend modal renders 3 checkbox disclaimer cards plus existing YES + comprehension verbatim verification.
- **Module D — Audio capability**:
  - Backend: new `POST /api/ai/sage/tts` endpoint. Routes through `OpenAITextToSpeech` (emergentintegrations) using the Emergent LLM key. Voice defaults to `sage` (literally named "sage" — wise, measured). Streams `audio/mpeg` bytes. Every invocation is audit-logged.
  - Frontend: voice-on toggle in the parameter panel (`Volume2`/`VolumeX` icon). Mic button (`Mic`/`MicOff`) using browser-native Web Speech API for STT — permission gated by browser. Each assistant message gets a hover-revealed replay-as-audio button. Text transcript always remains visible (accessibility requirement). On audio failure, falls back gracefully to text-only.
- **NEW addendum endpoint** `GET /api/admin/sage/status` (exec only) returning the exact addendum schema: `{prompt_hash_status, modules{A,E,F,D}, fallback_active, last_audit_id}` for idempotent deployment pipelines.
- **Tests**: new `backend/tests/test_sage_v2.py` — 12 tests covering integrity endpoint (RBAC + hash visibility), layered consent (general path, missing disclaimers rejected, all-acks succeed, expert_score range, human-review flag), TTS (anonymous blocked, empty text rejected, audio/mpeg returned with valid mp3 head bytes, invalid voice rejected). All 12 green. Total backend: **252/252 passing** (was 240).
- **Files added:** `backend/prompts/ancestral_sage_prompt.py`, `backend/prompts/__init__.py`, `backend/tests/test_sage_v2.py`. Files updated: `backend/server.py`, `frontend/src/pages/AITutor.jsx` (rewrite).

## Feb 2026 — Exec-Admin Sage Sessions audit panel + safety caps
- **NEW Exec Admin page** at `/admin/sage-audit` (Compass icon "Sage Sessions" in the exec sidebar). Two tabs:
  - **Sessions** — chronological audit feed of every Ancestral Sage event: chats, consent grants, refusals (incl. `safety_cap_exceeded`), and crisis interventions. Counts per kind, kind/user filters, paginated up to 500 rows. Shows email + intensity + safety_level + refusal_reason + message preview per row.
  - **Level Controls** — global `safety_level` ceiling + per-user override table. More restrictive of the two wins. "No override / No cap" both supported.
- **NEW collection** `safety_caps` (single doc `_id="global"` for global cap, `_id="user:{uid}"` for per-user overrides). Stamped with `updated_at` + `updated_by`. Every change writes a row to `audit_log`.
- **NEW endpoints** (Exec Admin only via `require_role("executive_admin")`):
  - `GET /api/admin/sage/cap` — returns `{global_level, available_levels, overrides[]}` (overrides hydrated with email + full_name).
  - `PUT /api/admin/sage/cap/global` — body `{level: <enum> | null}` (null clears).
  - `PUT /api/admin/sage/cap/user/{uid}` — body `{level: <enum> | null}`. 404 if user missing.
  - `GET /api/admin/sage/audit?kind={all|chat|refusal|crisis|consent}&user_id=&limit=` — most-recent-first feed merging `chat_history` + `ai_consents`, hydrated with email/full_name.
- **Cap enforcement** in `ai_chat`: runs **before** the consent gate. A capped user cannot exceed the cap even with a valid `consent_log_id` — request is 403'd and a `safety_cap_exceeded` audit row is written. Cap resolution: `min_rank(global, per-user)`; default `extreme` (no cap).
- **Frontend wiring**: `pages/SageAudit.jsx`, `App.js` route added (executive_admin gate), `AppShell.jsx` exec nav adds "Sage Sessions" link with Compass icon.
- **Tests:** `backend/tests/test_sage_caps.py` — 17 tests covering RBAC (anon/student/admin all blocked), cap CRUD, invalid level validation, 404 on bad uid, cap-blocks-without-consent, **cap-blocks-even-with-valid-consent**, per-user-override-beats-global, override-clear-restores-global, audit feed kind filtering (consent/crisis), audit user filtering. All 17/17 green.
- **Total backend pytest now: 240/240 passing** (was 223; +17 new). Lint clean.

## Feb 2026 — Ancestral Sage AI persona
- **NEW persona** in AI Tutor: **Ancestral Sage** — Pan-African, pro-Black, spiritually-grounded mentor and guide, using the Compass icon in copper. Joins the existing 6 modes as a 7th option.
- **Backend (`server.py`)**:
  - `AIChatReq` extended with optional `depth`, `intensity`, `cultural_focus`, `divination_mode`, `safety_level`, `consent_log_id`, `scope` fields (Literal-validated where the spec dictates).
  - New `AIConsentReq` model + `POST /api/ai/consent` — validates the canonical YES + verbatim comprehension phrase (`"I understand and accept the risks of this practice."`), writes to `ai_consents` collection, returns `{consent_log_id, expires_at, ttl_minutes}`. Default TTL: 120 minutes.
  - `ai_chat` gating runs **before** the LLM call (zero LLM cost on a refusal):
    - If `intensity=deep` OR `safety_level in {exploratory, extreme}` → require valid, unexpired, user-scoped `consent_log_id` else 403.
    - Crisis short-circuit: if user message contains explicit suicidal phrasing, return canonical safety reply with crisis-line resources (988, Crisis Text Line, findahelpline.com) and `safety_intervention: true` — no LLM call.
    - All five session parameters injected into the system prompt at request time, plus `consent_log_id (consent granted)` line when present.
    - `scope=wai_training_only` appends a strict-scope override directive that confines the persona to W.A.I. curriculum.
  - `chat_history` rows for sage sessions now record `intensity`, `safety_level`, `consent_log_id`, `scope`, and `refusal_reason` for auditability.
  - System prompt for `ancestral_sage` faithfully encodes all 5 immutable rules, output format ("Summary / Consent status / Response / Aftercare"), provenance tags for living-tradition rituals, and the "Fringe interpretation — non-mainstream" labeling rule.
- **Frontend (`pages/AITutor.jsx`)**:
  - New `Ancestral Sage` mode pill with `Compass` lucide icon (copper / `text-copper`); accessible `aria-label` and tooltip "Ancestral Sage — Guidance & Readings".
  - `SageParamPanel` reveals 5 dropdowns when persona is active.
  - `ConsentModal` posts to `/api/ai/consent` with two-step verbatim verification; submit disabled until both fields validate locally; consent badge ("Consent active — revoke") appears after grant.
  - Send button auto-switches to a `Lock` icon + "Consent" label when consent is required and not yet granted; restored to `Send` afterwards.
  - 403 responses with "Consent required" reopen the consent modal automatically.
- **Tests (`backend/tests/test_ancestral_sage.py`):** 14 new tests covering consent endpoint phrase validation, RBAC, deep/exploratory/extreme gating, invalid-consent-id rejection, crisis short-circuit, and consented happy-path gate-pass. **All 14/14 green.** Total backend pytest now: **223/223 passing**.
- **Files added:** `pages/AITutor.jsx` (rewrite), `tests/test_ancestral_sage.py`. Files updated: `server.py` (AIChatReq, AIConsentReq, helpers, /ai/consent endpoint, /ai/chat gating).

## Feb 2026 — Catch-all 404 route (blank-page guardrail)
- **NEW:** `pages/NotFound.jsx` — branded 404 page (blueprint hero left, "Wrong turn" copy right) that displays the unmatched pathname and a context-aware CTA (lands user back on their role-correct dashboard if signed in, or landing if not).
- **App.js:** added `<Route path="*" element={<NotFound />} />` catch-all so any future stale bookmark, typo, or pre-route-deploy URL no longer silently white-screens.
- **Diagnosis driver:** user reported `/admin/users` blank in production. Console showed `No routes matched location '/admin/users'` — production bundle was stale (current preview already defines the route at App.js:76). 404 fallback ensures the failure mode is now graceful instead of silent.
- **Files added:** `pages/NotFound.jsx`. Files updated: `App.js`.

## Feb 2026 — Auth + Password Reset + Settings hotfix
- **NEW:** Public password-reset flow.
  - `POST /api/auth/forgot-password` — no-enumeration response, per-IP + per-email rate limit, sha256-hashed single-use token with 30-min TTL.
  - `POST /api/auth/reset-password` — single-use enforcement, invalidates all other unused tokens for the user, audit logged.
  - `POST /api/admin/users/{uid}/reset-link` — admin-mediated reset link with copy-to-clipboard UI; honours `can_modify()` immunity.
- **NEW:** `PATCH /api/auth/me` — self-service profile edit of `full_name` and `email`. Role/associate stay admin-only.
- **Settings page rebuilt** with Profile + Password tabs. Forced-rotation banner preserved.
- **Login page:** real "Forgot your password?" link replacing the "contact admin" copy.
- **Admin dashboard:** new per-user "Send reset link" button (lucide `Link2`) with modal showing the URL + email-sent status.
- **Optional Resend integration:** when `RESEND_API_KEY` and `PUBLIC_APP_URL` are set, the reset link is emailed via Resend; otherwise the admin-mediated link UI keeps the flow functional.
- **Indexes:** added `password_reset_tokens.token_hash` (unique), `expires_at` (TTL 0), and `user_id`.
- **Rate limits relaxed for realistic admin workflows:** login 30/60s (was 10), forgot-password IP 30/5min (was 10).
- **Tests:** new `tests/test_password_reset.py` (24 tests). Suite total: 185/185 passing.
- **Files added:** `pages/ForgotPassword.jsx`, `pages/ResetPassword.jsx`. Files updated: `server.py`, `Settings.jsx`, `AdminDashboard.jsx`, `Login.jsx`, `App.js`, `lib/auth.jsx`, `tests/test_iter4.py` (rate-limit count update).

## Feb 2026 — P1 hotfix: /admin/cohorts N+1 elimination
(see prior CHANGELOG entry; 161/161 pytest)

