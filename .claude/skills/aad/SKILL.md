---
name: aad
description: "Agent/AI-architecture discovery & audit for this repo's persona system: llm_gateway provider routing, key resolution, autonomous exec/NAM endpoints, the APScheduler jobs, and the failover watchdog's blast radius."
---

# aad — agent/AI architecture audit

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Audit how autonomous agents and AI components are wired: entry points, decision
authority, human-in-the-loop gates, and failure blast radius.

## The actual AI surface in this repo

- `backend/ai/llm_gateway.py` — the AI authority (~46KB). All provider calls
  should funnel here. Providers pinned in `backend/requirements.txt`:
  `groq`, `openai`, `together`, `cohere`, `mistralai`, `huggingface_hub`.
- `backend/ai/persona_loader.py` — `_PERSONA_MAP` at `:1058`, plus a synthetic
  `"unified"` key added at `:1157`. `load_personas()` (`:1160`) composes every
  prompt through `_source_protocol.compose_system`. **Count the keys before
  quoting a persona count**; docs say 17 and the map is built in layers.
- `backend/ai/hybrid_nam/` + `backend/routers/nam.py` — the Hybrid NAM surface,
  registered at `/api/nam` **after** the access gateway wrap.
- Other autonomy: `backend/ai/crisis_engine.py`, `delegation_engine.py`,
  `routing.py`, `controller.py`, `mode_system.py`, `team_monitor.py`,
  `system_health_monitor.py`, `prompt_guard.py`, `sage_safety_gates.py`.
- Non-request-triggered actors: `backend/jobs.py` (APScheduler —
  `apscheduler==3.10.4`), `backend/failover_watchdog.py` (launched as
  `asyncio.create_task(run_watchdog(panel_db=db))` at
  `backend/server.py:1657`), `backend/emergency_panel.py`,
  `backend/revenue_operations_integration.py`.
- Key material: `backend/keyvault.py` (self-healing encryption secret,
  env → Mongo-persisted → ephemeral), `backend/byok.py`, `backend/api_keys.py`,
  `backend/routers/provider_gateway.py`, `backend/user_budget.py`,
  `backend/ai_cost_tracker.py`.

## Steps

1. **Inventory every entry point that can take autonomous action**, in three
   categories, because only the first is visible to route enumeration:
   - HTTP routes (`/api/nam/*`, `/api/exec/*`, `/api/executive/*`,
     `/api/exec/tools/*`, `/api/ai/*`);
   - scheduler jobs in `backend/jobs.py`;
   - background `asyncio.create_task` actors (grep for it — the watchdog at
     `server.py:1657` is one, and the startup task itself is another).

2. **Map each to its real authority scope.** Which collections can it write?
   Which provider can it spend money on? Who can trigger it, and via which of the
   three auth mechanisms (router-local `_require_rank`, `deps.require_rank`, or
   the outer gateway)?

3. **Audit key resolution by execution, not by reading.** Trace how
   `llm_gateway` resolves a provider key: env → keyvault → BYOK → user budget.
   Confirm what happens with **no** key configured. Note that
   `/api/health` reports `ai_providers_unconfigured` as an issue while still
   returning HTTP 200 — an unconfigured AI stack does not fail any healthcheck.

4. **Verify `backend/ai/prompt_guard.py` and `sage_safety_gates.py` actually run
   on the live path.** A guard module that nothing imports is decoration. Grep
   for call sites and confirm by execution.

5. **Identify human-in-the-loop gates and where they are bypassable.** Especially:
   `/api/nam/knowledge/{id}/approve` implies an approval step — establish whether
   any write path reaches published knowledge without it.

6. **Assess blast radius of the autonomous actors specifically:**
   - `backend/jobs.py` guards on `if not db_manager.db:` and `db_manager` is
     never connected (anchor §4), so these jobs are **no-ops** — a silent
     failure of billing/revenue automation, not a safe default.
   - `failover_watchdog` runs as a fire-and-forget task; establish whether an
     exception in it is logged or vanishes, and what it is empowered to change.
   - `backend/emergency_panel.py` / `/emergency` gateway — confirm its auth.

7. **Check the gateway snapshot boundary for the AI surface.** `nam`, `saga`,
   `executive_pipeline`, and `exec_tools` are registered after
   `access_gateway.wrap(app)` (`backend/server.py:2783`) and were absent from both
   `_discover_public_route_patterns` and `_derive_handler_requirements`
   snapshots. These are the highest-authority routers in the app. Establish
   empirically what the gate does with them.

8. Report: autonomy surface, privilege concentration, spend exposure, missing
   oversight, and silently-dead automation.

## Constraints

- Verify by execution where possible. A router that failed to import has no
  autonomy at all — and a module that never runs is a different finding from one
  that runs unsafely. Do not conflate them.
- **Never print, log, or commit provider keys or `JWT_SECRET` / `CROSS_SITE_SECRET`
  / `AUDIT_ENCRYPTION_KEY`.** Report absence and rotation needs by name only.
- Note when a safety control is unset rather than broken: importing the app logs
  `AUDIT_ENCRYPTION_KEY is not set — denial records are stored UNENCRYPTED` and
  `No executive admin email is configured ... the first registered user would
  become executive_admin`. Both are live pre-launch risks.
- Do not spend real provider credit during an audit without saying so first.
- Cite `file:line` for every finding; report DONE/PASS only on live behavior.
