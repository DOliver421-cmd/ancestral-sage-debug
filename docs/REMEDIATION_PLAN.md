# REMEDIATION PLAN — everything outside the initial goal

Owner instruction (2026-10-12): *"The initial goal is the homeschool and user
profile are fully functional. All other issues are part of a remediation plan."*

The initial goal is **verified done by execution** (not inspection): a real,
newly-registered account walked the whole homeschool path and the whole profile
path on the local server, and every step is recorded in `docs/SESSION_HANDOFF.md`.

Everything below is **found, evidenced, and NOT fixed** — deliberately outside
the initial goal. Ordered by risk to the owner.

---

## A. Security (fix first)

### A1. A password change does not end existing sessions
`server.py:3049` `change_password` writes the new hash and issues a fresh token,
but never bumps `token_version` and deletes no sessions.
**Evidence:** executed — after changing the password, the previously issued
token still returned `200` from `/api/auth/me`; only the password check itself
rejected the old password.
**Why it matters:** the usual reason someone changes a password is that they
think someone else has access. That access survives today.
**Fix:** bump `token_version` (the machinery exists — `/exec/control/user/role`
already does it) and delete `db.auth_sessions` rows in the same handler.
**Risk while open:** high (session fixation after credential rotation).

### A2. The AI Coach parent switch is UI-only
`coach_enabled` is written and read (`routers/academy.py:568`), enforced only in
`AcademyLesson.jsx:44,156,441`. `POST /api/ai/chat` with `mode: academy_coach`
never checks it.
**Evidence:** executed — with the learner's coach set to `false`, a direct API
call was still accepted by `/api/academy/coach/log`, and the chat handler has no
coach check at all.
**Why it matters:** a parent's "my child does not use the AI" decision is
advisory only. Same defect class as the Soup gate that was UI-only until today.
**Fix:** read the learner's flag in the `academy_coach` branch of `ai_chat`
(server.py:4623) and return the same refusal the UI shows.
**Risk while open:** medium (parental-control bypass by direct API call).

### A3. `AUDIT_ENCRYPTION_KEY` is not set in production
The gateway logs at every startup: `denial buffer attached (encryption=OFF -
AUDIT_ENCRYPTION_KEY missing)`. The audit denial buffer therefore stores
unencrypted detail.
**Fix:** set the key in the deployment secret store. The log line is the
detector — treat it as a deploy gate.

### A4. `DEV_RETURN_RESET_TOKEN` on the local profile
`/api/auth/forgot-password` returns raw reset tokens in the response when this
flag is set. The server warns loudly at startup. It is a local convenience flag
only — confirm it is absent from the Railway environment (the live
`/api/auth/forgot-password` shape was NOT probed with a real address; verify
with an owned address during the next live pass).

## B. Data integrity

### B1. Two competing `/ai/chat` implementations
`server.py:4504` and `routers/ai.py:1766` both define the endpoint. The
`server.py` copy is the one that actually serves `/api/ai/chat`; the router copy
serves a doubled path (`/api/ai/ai/chat`) created by its include prefix.
**Evidence:** traced during the crisis-precedence fix — an edit to the router
copy changed nothing until the same change was made in the server copy; the live
endpoint is the server copy.
**Why it matters:** two sources of truth for the platform's most safety-critical
surface (consent, crisis short-circuit, entitlement). One of them is dead code
that looks live.
**Fix:** keep one, delete the other, and add a guard test asserting no duplicate
path+method pair exists.

### B2. Shadowed duplicate routes across the app
The same pattern (two handlers, one path) exists elsewhere; the API surface
ledger counts 992 handler-derived requirements. An audit pass
(`.claude/skills/apiendpointauditor`) should enumerate path+method duplicates
and retire the shadows.

### B3. `Dream` prompt hashes mismatch on this host
Startup prints `PROMPT GUARD CRITICAL: 'director' prompt hash MISMATCH … falling
back to RESTRICTED mode` on this machine (not observed against the live
deployment). Either the local prompt files were edited, or the baseline was
enrolled on a different machine. **Do not "fix" by re-enrolling silently** —
confirm which files differ and why first.

## C. Correctness debt (verified, non-blocking)

- **`/api/academy/enrollments` returns 404** — the enrollment model exists
  (`routers/academy.py:154`) but no route serves it; the UI auto-enrols at
  learner creation, so no user-visible break. Either wire the route or drop the
  model.
- **`scripts/api_frontend_match.py` reports two dead frontend calls**:
  `GET /academy/kinds` (frontend/src/pages/academy/AcademyProjects.jsx) and
  `GET /digital/purchases` (frontend/src/pages/OurLegacy.jsx). Real 404s a
  member can trigger today.
- **`helper_ask`/`public_helper_ask`/`ai/helper` are three spellings** of the
  keyword knowledge base. Consolidate to one path and redirect the others.

## D. Product decisions still open

- **D1** The daily puzzle and the Sovereign chat were split this session per
  the owner's ruling; the `docs/TIER_BASELINE.md` regenerated copy is the
  record of truth going forward.
- **D2** Two owner rulings awaited from the previous session are now settled
  (AI chat = member+/BYOK; puzzles free). The remaining ones from
  `docs/API_KEY_GATEWAY_PLAN.md` — Decision 6 (which providers may run on
  `model:"auto"`) and Decision 8 (the legacy provider write-only path) — still
  block G3 and G7.
- **D3** OCR is labelled honestly in the scanner UI (text files are read
  natively; photographs are captured and carried to the summary sheet). A true
  OCR engine needs a new dependency and therefore owner approval.
