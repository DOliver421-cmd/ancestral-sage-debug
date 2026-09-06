# Hybrid NAM + Arena Integration Plan

## Current State (from audit)

| Component | Status | Notes |
|-----------|--------|-------|
| `/api/nam` (Hybrid NAM) | EXISTS, mounted, working | Full AI command console with chat, memory, knowledge, operational engines |
| `/api/unifier` | EXISTS, mounted, working | 3-pass synthesis (2 competitors + Hybrid NAM judge), plans, project handoff |
| `/api/competition` | EXISTS, mounted, working | 4-persona arena, commissioner scoring, leaderboard |
| `backend/routers/arena.py` | DEAD CODE | Unmounted, in-memory cycles, imports Hybrid NAM judge |
| `backend/routers/hybrid_nam.py` | DEAD CODE | Unmounted, duplicates some `/api/nam` functionality |
| Shared context/state | DOES NOT EXIST | Each feature is completely isolated |
| "Alive Intelligence" | DOES NOT EXIST | Only a keyword string in site-guide metadata |

## Goal

Make existing Arena capabilities behave as parts of one integrated executive intelligence system with Hybrid NAM as the primary interface. Do not rebuild working features.

## Approach

### Phase 1: Shared Work Context Model

**Create a new MongoDB collection: `arena_work_context`**

```python
{
  "id": str,
  "owner_id": str,           # user who created/owns this context
  "title": str,
  "status": str,             # new | exploring | refining | awaiting_decision | approved | planned | active | blocked | paused | completed | archived
  "current_objective": str,
  "project": str,
  "description": str,
  "mission_alignment": str,
  "strategic_goals": [str],
  "ideas": [str],
  "brainstorm_results": dict,
  "decisions": [dict],
  "assumptions": [str],
  "questions": [str],
  "open_issues": [str],
  "risks": [dict],
  "opportunities": [dict],
  "priorities": [dict],
  "tasks": [dict],
  "actions": [dict],
  "milestones": [dict],
  "results": [dict],
  "recommendations": [str],
  "executive_notes": str,
  "ai_reasoning": [dict],
  "activity_history": [dict],   # meaningful state changes only
  "next_recommended_action": str,
  "source_capability": str,     # which Arena capability last modified this
  "created_at": str,
  "updated_at": str,
  "created_by": str
}
```

**Add indexes:**
- `owner_id`
- `status`
- `updated_at` (descending)

### Phase 2: Connect Hybrid NAM to Shared Context

**Add to `backend/routers/nam.py`:**

1. **`POST /api/nam/context`** — Create or update shared work context
   - Auth: `require_auth` (any authenticated user)
   - Body: partial context fields to update
   - Returns: full context document

2. **`GET /api/nam/context`** — Get current user's active work context
   - Query params: `context_id` (optional, defaults to most recent active)
   - Returns: full context document

3. **`POST /api/nam/context/action`** — Record a meaningful state change
   - Body: `{action_type, description, capability, metadata}`
   - Appends to `activity_history`
   - Updates `updated_at`, `source_capability`

4. **Enhance `/api/nam/chat`** — Inject shared context into system prompt
   - When active context exists, prepend context summary to Hybrid NAM's system prompt
   - This gives Hybrid NAM awareness of current work without the executive repeating context

### Phase 3: Connect Unifier to Shared Context

**Modify `backend/routers/unifier.py`:**

1. **On session creation (`POST /unifier/sessions`)**:
   - Accept optional `work_context_id` in body
   - If provided, link session to that context
   - If not provided, create a new `arena_work_context` and link it

2. **On plan save (`POST /unifier/sessions/{id}/plans`)**:
   - Automatically update parent `arena_work_context`:
     - `brainstorm_results` ← synthesis results
     - `decisions` ← plan decisions
     - `source_capability` ← "unifier"
     - Append activity: "Plan synthesized and saved"

3. **On project handoff (`POST /unifier/plans/{id}/to-project`)**:
   - Update context: `status` → "planned", `tasks` ← plan tasks
   - Append activity: "Handed off to member projects"

### Phase 4: Connect Competition to Shared Context

**Modify `backend/routers/competition.py`:**

1. **On task creation (`POST /competition/task`)**:
   - Accept optional `work_context_id`
   - Link competition round to context
   - Update context: `current_objective` ← task brief

2. **On scoring (`POST /competition/score`)**:
   - Update context: `results` ← round results
   - Append activity: "Competition round completed"

3. **New endpoint: `GET /competition/context/{context_id}`**:
   - Return competition history for a specific work context

### Phase 5: Hybrid NAM Orchestration

**Add to `backend/routers/nam.py`:**

1. **`POST /api/nam/orchestrate`** — Hybrid NAM determines next action
   - Body: `{message}` (executive's natural language request)
   - Logic:
     1. Load active work context
     2. Analyze message intent (new idea, continue work, review status, etc.)
     3. Determine appropriate Arena capability
     4. Return: `{capability, action, context_summary, reasoning}`
   - This does NOT execute the action — it recommends the appropriate capability and passes context

2. **`GET /api/nam/status`** — Executive status briefing
   - Returns: active contexts, recent activity, recommended next actions, open issues

### Phase 6: Frontend Unified Experience

**Modify `frontend/src/pages/HybridNam.jsx`:**

1. Add "Active Work" panel showing:
   - Current work context title/status
   - Recent activity timeline
   - Recommended next actions
   - Quick links to relevant Arena capability

2. Add context creation flow:
   - "New Initiative" button
   - Captures initial idea
   - Creates `arena_work_context`
   - Hybrid NAM suggests next step (brainstorm, refine, align, etc.)

3. Add capability integration:
   - When Hybrid NAM recommends a capability, show a card/button to launch that capability with context pre-loaded
   - Examples: "Open Unifier to brainstorm this", "Open Competition to evaluate approaches"

**Do NOT create a dashboard of unrelated tools.** The unified experience should feel like one intelligent environment.

### Phase 7: Security & Permissions

1. **`arena_work_context` access control**:
   - Owner can read/write their own contexts
   - Staff/admin can read all contexts in their organization
   - Never expose internal contexts to public users

2. **Hybrid NAM respects existing RBAC**:
   - `/api/nam/chat` already requires auth
   - New context endpoints follow same auth pattern
   - Capability handoffs verify user has access to target capability

3. **No public exposure**:
   - `arena_work_context` is never served through public endpoints
   - Alive Intelligence remains private/internal

## What NOT to Do

- Do NOT create a separate "Alive Intelligence" UI feature
- Do NOT rebuild Unifier, Competition, or Hybrid NAM
- Do NOT create a dashboard of links to separate tools
- Do NOT force rigid workflow sequences
- Do NOT require copy/paste between capabilities
- Do NOT make Hybrid NAM autonomous — it recommends, it does not execute without approval
- Do NOT rename disconnected features and call it integration

## Validation

1. Executive creates initiative via Hybrid NAM chat → context created
2. Hybrid NAM recommends Unifier for brainstorming → executive launches Unifier with context
3. Unifier produces synthesis → context updated with results
4. Hybrid NAM recommends Competition for evaluation → executive launches Competition with context
5. Competition completes → context updated with results
6. Executive returns later, asks "Where are we?" → Hybrid NAM reports full history from context
7. Executive says "Rethink this" → Hybrid NAM can return to brainstorming without losing history

## Files to Modify

| File | Changes |
|------|---------|
| `backend/routers/nam.py` | Add context endpoints, enhance chat with context injection |
| `backend/routers/unifier.py` | Link sessions/plans to work context |
| `backend/routers/competition.py` | Link tasks/rounds to work context |
| `backend/server.py` | Add `arena_work_context` indexes |
| `frontend/src/pages/HybridNam.jsx` | Add active work panel, context creation, capability handoffs |
| `backend/ai/hybrid_nam/store.py` | Add `arena_work_context` collection operations |

## Out of Scope

- Rebuilding Arena UI from scratch
- Changing existing authentication/authorization model
- Adding new AI providers or models
- Modifying existing NAM operational engines
- Creating "Unifier" as a separate feature (it stays as-is, just integrated via context)
