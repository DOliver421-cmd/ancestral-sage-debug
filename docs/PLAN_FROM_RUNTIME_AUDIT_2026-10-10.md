# PLAN FROM RUNTIME AUDIT — 2026-10-10 — SUPERSEDED

> **Content integrated into `docs/WORKING_PLAN.md` (R1–R17 across Phases 0–5).** Work from the working plan;
> this file is history. Evidence: `docs/RUNTIME_AUDIT_2026-10-10.md`.


Derived strictly from `docs/RUNTIME_AUDIT_2026-10-10.md`. Every task below is ordered by **user-visible
impact proven by execution**, each with a definition-of-done that requires running the thing — not reading it.
One task per PR, branch from `origin/main`, owner reviews.

**Rules carried over (still binding):** zero schema change; additive/constants where possible; Academy stays
free for every registered member; no Anthropic anything; no writes to production; no force-push; verify against
the live target read-only; report asked-vs-delivered and what is NOT delivered.

---

## Queue 0 — Fix broken user workflows (do these first; each is small)

### R1. Make the Legal Workflow Engine's account sync real (F1)
**Problem (executed):** restore reads `r.data?.workflows` from a bare-array response; sync POSTs JSON to an
endpoint that demands query params → 422; both failures swallowed by `.catch(() => {})`.

**Change (minimal, two sides, no schema change):**
- Backend `routers/resource_hub.py:369` — annotate the body: `payload: WorkflowCreate` with
  `title: str`, `area: str`, `steps: List[WorkflowStep]` inside a pydantic model, handler uses `payload.*`.
  Keep the response shape unchanged.
- Frontend `pages/LegalWorkflows.jsx:155,174` — read the array the API actually returns
  (`const list = Array.isArray(r.data) ? r.data : (r.data?.workflows || [])`), and surface sync failure once
  (a small "not saved to your account" note) instead of a bare swallow.

**DoD (executed):** with a plus member: type in the engine → `GET` then `POST` returns **201**; reload the page
in a **fresh browser context with empty localStorage** → state restores from the account; verify a second
account's list is empty. Guard rails + `craco build` clean. PR body shows the real 201/200 outputs.

### R2. Kill the enrollment read-modify-write race (F2)
**Problem (executed):** 8/8 rounds lost 1–2 of 3 concurrent enrollments, all 200.
**Change:** `routers/academy.py:614-629` — replace read-set-write with atomic operators:
`$addToSet: {course_slugs: slug}` on enroll, `$pull: {course_slugs: slug}` on unenroll (keep the
`course_applies` 400 guard first; it stays correct).
**DoD (executed):** rerun the 8-round × 3-writer probe — **0/8 rounds with loss**, all codes 200/400 as
appropriate; then confirm unenroll still works and grade-change recompute (`update_student`) still passes the
existing Academy suite (52 tests).

### R3. Make artifact saves atomic per step (F3)
**Problem (executed):** 4/6 rounds lost artifacts; stale values resurrected.
**Change:** `routers/academy.py:1471-1496` — write each sent artifact with dot-path `$set`
(`artifacts.<step_id>`), clearing with `$unset` on empty string, keeping the existing valid-step and length guards.
**DoD (executed):** rerun the 6-round × 3-writer probe — **0/6 rounds with loss**; the #9 regression case
(sequential saves merge) still passes; off-pathway keys still dropped.

### R4. Fix the NAM knowledge seed on real databases (F4)
**Problem (executed):** `persistence.py:35` (and the collection variants) truth-test motor objects → 31/31
fail on every boot; `nam_knowledge` count = 0 in production; standalone "success" is the in-memory fallback.
**Change:** `if _db is not None` / `if col is not None` across `backend/ai/hybrid_nam/persistence.py`.
**DoD (executed):** cold boot on a fresh DB → startup logs `31 seeded, 0 skipped, 0 failed`; Mongo
`nam_knowledge.count_documents({})` = 31; restart → `0 seeded, 31 skipped` (idempotent).

### R5. Ship the in-product guides (continuation §4.1 — proven unstarted, F8)
**Problem (executed):** `in_product`/`steps` absent (grep = 0); the owner-rejected badge renders in the real
component with the real rows.
**Change:** exactly `docs/HANDOFF_GUIDE_STEPS.md` (verbatim — do not shorten), then the frontend half in the
same doc (badge swap, "Open the workflow", checklist persisting through the **fixed** `POST/PATCH
/api/hub/workflows` from R1 — no new endpoint).
**DoD (executed):** guides return `in_product=true` with 8 steps; render of the real panel shows
"Workflow · 8 steps" + "Open the workflow" and **no** "Read-only guide" string; check a box, re-fetch, confirm
persistence; another family's list empty.

## Queue 1 — Truthfulness of gates and tiers (owner decisions needed)

### R6. Close the Creator money surface (F5) — **highest-leverage single change**
Add `/api/creator/courses`, `/api/creator/courses/{course_id}`, `/api/creator/payout-profile`,
`/api/creator/enrollments/me` to `FEATURE_API_PATHS` in `security/feature_control.py` (constants only).
**DoD (executed):** free member `POST /api/creator/courses` → **403**; plus member → 201; Academy surfaces
still free (guard rail `academy-open-access.js` passes unchanged).
**Owner decision first:** which tier — Plus (as the framework's Tier 2 says) or keep free and build the Tier-2
marquee another way. Do not guess.

### R7. Resolve the three tier drifts (F6)
`ai_chat` (frontend member / backend free), `courses` (plus / free), `resource_hub` (plus / handler member).
Pick one side as truth per feature and align it. **Owner decision:** the plan's open question #3 (Resource Hub
Plus vs Member) is still open — execution shows the handler says Member and the UI says Plus.
**DoD (executed):** for each feature, a free/member/plus account probe returns the intended code; frontend copy
matches.

### R8. Stop production from masking API errors as 200 HTML (F9)
**Owner decision (deployment behaviour — needs approval before editing):** add a JSON 404/405 for unmatched
`/api/*` in front of the SPA catch-all. **DoD (executed):** prod `GET /api/nam/chat` → 405 JSON (matching local),
anonymous route probes unchanged.

## Queue 2 — Startup hygiene and observability

### R9. PipelineManager dead import (F7): restore `backend/src/agents/pipeline_manager.py` or remove the
import + label the fallback honestly. **DoD:** boot log shows either "PipelineManager ready" or no init-failure line.

### R10. Make startup seed failures loud (F4 companion): log per-item failure reasons (the seed already
returns them — the startup line drops them), and expose seed state on `/api/health` (e.g. `nam_knowledge: 31`).
**DoD (executed):** a forced seed failure appears in the boot log with reasons and in `/api/health.issues`.

## Queue 3 — Carried from the continuation plan, now sequenced behind the above

| Order | Task | Blocked by |
|---|---|---|
| R11 | Digital-product commerce depth over `/media/products/*` (additive) | — |
| R12 | PEP / FES-UA scholarship workflows (new UI + content over `scholarship_funds`) | — |
| R13 | Project review comments + project artifacts in printed Records (additive) | — |
| R14 | K–8 cultural deepening (~35 courses, same attach mechanism as #474) | — |
| R15 | **Co-op / multi-seat — still blocked** on the owner's schema decision | owner decision |
| R16 | Creator Studio price decision + Tier-2 marquee | owner decision (plan §7.1) |
| R17 | Weekly parent report; Afro-Latin / Portuguese-Spanish strands (ledger "not yet delivered") | — |

## Sequencing and risk

1. **R1 → R5 together are one coherent PR set** (R5's checklist needs R1's fixed endpoints; land R1 first).
2. **R2, R3, R4 are independent** and safe in parallel — all three are single-file, additive-mechanism fixes
   with executed race loops as the regression gate.
3. **R6 before R7**: gate behaviour must be truthful before tier copy is aligned.
4. Nothing in Queues 1–2 changes the database schema or the Academy's free status.

## Verification standard for every PR above

- Race/gate claims: re-run the corresponding probe from `/tmp/audit_probe*.py` and paste real output.
- UI claims: render the real component (harness recipe in the audit §5) or click the live page.
- Guard rails: `frontend/scripts/*` + `craco build`; suite: the 5 Academy test files (52 tests today).
- Live check: read-only probes against `charming-analysis-morehelpcenter.up.railway.app`; GET bodies must be
  verified as JSON (F9).
- PR body format: asked vs changed, verification evidence (commands + output), **what is NOT verified**, guard-rail results.
