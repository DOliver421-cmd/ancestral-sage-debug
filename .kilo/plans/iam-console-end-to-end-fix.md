# IAM Console End-to-End Fix Plan

## Current State

The IAM console frontend exists at `frontend/src/pages/IAMConsole.jsx` with 8 tabs:
- Users (admin user management)
- Identities
- Who Can Do What
- Delegations
- My Consent
- Action History
- Who Has Access to Me
- Personas (exec only)
- Privilege Matrix (exec only)

Backend routes exist in `backend/routers/iam.py` for:
- GET/POST `/iam/identities`
- GET/PATCH `/iam/identities/{id}`
- POST `/iam/identities/{id}/rotate-token`
- GET/POST/DELETE `/iam/resources`
- GET/POST `/iam/delegations`
- POST `/iam/delegations/{id}/revoke`
- GET `/iam/consent`
- GET/POST `/iam/actions`
- POST `/iam/actions/check`

Backend routes exist for:
- GET/PATCH `/admin/rbac/matrix`
- GET `/ai/personas/exec`
- POST `/ai/personas/{slug}/toggle`
- GET `/iam/who-has-access-to-me`

## What's Actually Broken

1. **No end-to-end verification was done.** Backend 200/403 responses were treated as "working." The UI components were never traced through a real browser session.

2. **The IdentitiesTab calls `GET /iam/identities/{id}` but the backend may return `_id`** in the identity document. The frontend accesses `selected.identity.name`, `selected.identity.kind`, etc. If `_id` is present and not stripped, FastAPI's jsonable_encoder will fail with `ObjectId is not iterable`.

3. **The DelegationsTab creates delegations but the backend `create_delegation` requires `body.owner_id` for admin override.** The frontend doesn't send `owner_id`, so non-admin users are restricted to delegating only their own resources. This may be intentional but needs verification.

4. **The PersonasTab calls `/ai/personas/exec` and `/ai/personas/{slug}/toggle`.** These routes exist but were not verified to work after the RBAC changes.

5. **The WhoHasAccessTab calls `/iam/who-has-access-to-me`.** This endpoint exists but was not verified.

## Plan

### Task 1: Audit backend route registration
Check that all routes called by the IAM console are actually registered in the FastAPI router and return expected shapes.

### Task 2: Fix `_ensure_human_identity` ObjectId leak
The `_ensure_human_identity` function in `backend/routers/iam.py` returns MongoDB documents that may contain `_id`. FastAPI's jsonable_encoder fails on ObjectId. Strip `_id` before returning.

### Task 3: Verify identity detail response shape
The `GET /iam/identities/{id}` endpoint returns `{"identity": ident, "delegations": [...], "chain": [...]}`. Verify the frontend's `selected.identity.*` accesses match this shape.

### Task 4: Verify delegation creation flow
Trace the full path: DelegationsTab create form → POST `/iam/delegations` → backend validation → DB write → response → UI update. Fix any mismatches.

### Task 5: Verify consent tab data shape
The ConsentTab expects `r.data?.consent` and `r.data?.identity`. Verify the backend `/iam/consent` returns this exact shape.

### Task 6: Verify WhoHasAccessTab
Check that `/iam/who-has-access-to-me` returns `{user_id, total, access: [...]}` and that the frontend renders it correctly.

### Task 7: Verify PersonasTab
Check that `/ai/personas/exec` returns `{personas: [...]}` with the fields the frontend expects (`slug`, `name`, `enabled`, `level`, `department`, `source_status`, `capabilities`, `domain`).

### Task 8: Verify Privilege Matrix
Check that `/admin/rbac/matrix` GET returns `{matrix: {...}}` and PATCH accepts `{matrix: {...}}`.

### Task 9: Add integration tests
For each tab, add a test that:
1. Logs in as executive
2. Calls the API endpoint
3. Verifies the response shape matches what the frontend expects
4. For mutation endpoints, verifies the DB state changes

### Task 10: Fix all mismatches
Any mismatches between frontend expectations and backend responses get fixed in the backend router (backend is the source of truth for API contracts).

## Out of Scope
- Frontend UI redesign
- New IAM features
- Performance optimization

## Validation
- All IAM console tabs load without console errors
- Create/update/delete operations persist through the full UI → API → DB → response → render chain
- Tests pass: `test_rbac_matrix.py`, `test_critical_paths.py`, plus new IAM integration tests
