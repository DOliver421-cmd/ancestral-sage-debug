---
name: hybridnamsoulauditor
description: "Hybrid NAM (Assistant Director of MoreHelp Center) reality audit for this repo: verify the 12 functional pillars in docs/HYBRID_NAM_SPEC.md against the actually-registered /api/nam surface in backend/routers/nam.py, the feature_control gate, and the HybridNam.jsx frontend tabs."
---

# hybridnamsoulauditor — Hybrid NAM persona/pillar audit

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Verify Hybrid NAM behaves per its own spec, in code, not on the strength of the
spec's claims. The spec of record is `docs/HYBRID_NAM_SPEC.md`: its §2 declares
**The 12 Functional Pillars** — Mission, Strategy, Memory, Governance, Challenge,
Ecosystem, Power, Economics, Risk, Accountability, Crisis, Succession — each
mapped to a `GET`/`POST` endpoint pair (mostly under `/api/nam/operational/*`,
Memory under `/api/nam/memory`) and a frontend tab.

## Repo anchors (verify, then use)

- Spec of record: `docs/HYBRID_NAM_SPEC.md`. It is prior-audit output, not
  evidence — it claims "18 protected endpoints"; count the registered surface
  before repeating any number (anchor §8).
- Router: `backend/routers/nam.py` — `APIRouter(prefix="/api/nam", ...)` at
  `:70`; knowledge, memory, identity, constitution, intentions, dreams, and
  reflection routes also live there. **Registration matters, not the decorators**
  (anchor P3): nam routes were included after `access_gateway.wrap(app)` and were
  in neither gateway snapshot (anchor P4).
- Engines: `backend/ai/hybrid_nam/*.py` (`soul_kernel.py`,
  `operational_engine.py`, `memory_engine.py`, `knowledge_*.py`,
  `reflection_engine.py`, `dream_engine.py`, ...).
- Gate: `backend/security/feature_control.py` — `platform_flags.nam.hybrid` /
  `page_access.nam` decide whether the surface is enabled at all.
- UI: `frontend/src/pages/HybridNam.jsx` — one tab per pillar, wired through
  `accessGates.js` / `isPageEnabled`, calling through the single client
  `frontend/src/lib/api.js` (Bearer `lce_token`).

## Steps

1. **Enumerate the registered `/api/nam` surface from the running app** (Recipe B
   in the anchor), never from grep — source decorators exist even for routes the
   app never registered. Diff against the spec's pillar table.
2. **Map each of the 12 pillars** to its registered `GET` (view) and `POST`
   (act) endpoints and to the engine functions that back them (`file:line` both
   sides).
3. **Execute each endpoint** with the relevant identities via `TestClient`
   (pair with `cea`): unauthenticated → expect 401/403, authed member, staff.
   A pillar that 500s, returns a shape `HybridNam.jsx` cannot render, or is gated
   off is not working — an HTTP 200 alone proves nothing.
4. **Probe the loyalty/oversight claims** (mission protection, evidence
   classification, challenge path, succession): send an out-of-scope or
   challenge-style prompt and confirm the response structure and classification
   semantics appear in the body — not just a status code.
5. **Cross-check the frontend link**: every pillar tab in `HybridNam.jsx` calls a
   registered route and renders real response fields (the `fra` six-link chain).
   A tab that renders an empty array styled as success is a defect.
6. Persistence-backed pillars (memory, knowledge, dreams, reflections) cannot be
   read-after-write verified here — no `mongod` in this container. Mark those
   links `ENVIRONMENT BLOCKED`; never PASS them from source.

## Constraints

- The spec is a claim, not proof. Every pillar verdict needs an executed request
  with captured status + body, cited `file:line`.
- Report per pillar: `PASS` / `FAIL` / `ENVIRONMENT BLOCKED` using the anchor's
  §9 vocabulary; name the failing link in the chain.
- Never print secrets or provider key material from captured responses.
- Do not carry a verdict from one deployment to another (anchor §0) — the
  `/api/nam` surface, gate state, and data are per-deployment.
