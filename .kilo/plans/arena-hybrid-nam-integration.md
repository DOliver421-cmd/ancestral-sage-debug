# Corrected Implementation Plan — Hybrid NAM + Arena Integration

## Status
This is the corrected, implementable plan derived from the audit and the post-completion brief. It preserves existing working features and adds the minimum shared layer needed for integration.

## What Exists (Reality Check)
| Component | Status |
|-----------|--------|
| `/api/nam` (Hybrid NAM) | Mounted, working, persistent AI command console |
| `/api/unifier` | Mounted, working, 3-pass synthesis, plans, project handoff |
| `/api/competition` | Mounted, working, 4-persona arena, scoring, leaderboard |
| `/video-studio` | Mounted, working, Pro-tier short-form video creation |
| Ghost Studio (`/studio`) | Mounted, working, in-browser music creation |
| `member_projects` | Mounted, working, owner-scoped project tracking |
| `backend/routers/arena.py` | Dead code, unmounted |
| `backend/routers/hybrid_nam.py` | Dead code, unmounted |
| Shared context between features | Does not exist |
| "Alive Intelligence" as code entity | Does not exist |

## What NOT to Do
- Do NOT rebuild Video Studio, Ghost Studio, Unifier, Competition, or Hybrid NAM
- Do NOT create a "super dashboard" of tool links
- Do NOT rename disconnected features and call it integration
- Do NOT force rigid workflow sequences
- Do NOT make Hybrid NAM autonomous — it recommends, does not auto-execute
- Do NOT expose internal features publicly

## Implementation Plan

### Phase 1 — Shared Context Model
Create `arena_work_context` MongoDB collection with indexes. This is the single source of truth for all Arena work.

### Phase 2 — Connect Hybrid NAM to Context
Add CRUD endpoints to `/api/nam` for work context. Enhance chat to inject active context into Hybrid NAM's system prompt.

### Phase 3 — Connect Unifier to Context
Link unifier sessions/plans to work context. Auto-update context when plans are saved or handed off to projects.

### Phase 4 — Connect Competition to Context
Link competition tasks/rounds to work context. Update context with results.

### Phase 5 — Connect Production Tools
Expose Video Studio and Ghost Studio status/results through the project context. Do NOT rebuild them.

### Phase 6 — Orchestration Endpoint
Add `/api/nam/orchestrate` so Hybrid NAM can recommend the appropriate capability based on executive intent.

### Phase 7 — Frontend Unified Experience
Add active work panel to HybridNam.jsx. Show context, history, and capability handoffs.

## Acceptance Criteria
1. Executive creates initiative via Hybrid NAM → context created in `arena_work_context`
2. Hybrid NAM recommends Unifier for brainstorming → context pre-loaded
3. Unifier produces synthesis → context updated with results
4. Hybrid NAM recommends Competition for evaluation → context linked
5. Executive returns later, asks "Where are we?" → Hybrid NAM reports actual context history
6. Work can move backward (rethink) without losing history
7. Public users cannot access any of this

## Files to Modify
- `backend/server.py` — add `arena_work_context` indexes
- `backend/routers/nam.py` — context CRUD, orchestration, chat enhancement
- `backend/routers/unifier.py` — link sessions/plans to context
- `backend/routers/competition.py` — link tasks/rounds to context
- `backend/routers/member_projects.py` — link projects to context
- `backend/routers/studio.py` — expose production status via context
- `frontend/src/pages/HybridNam.jsx` — active work panel, context creation, handoffs
