---
name: apiendpointauditor
description: "Audit this repo's 631-path FastAPI surface: which routes actually registered, which are shadowed duplicates, which router silently failed to import, and which gate really runs."
---

# apiendpointauditor

Read `.claude/skills/_shared/REPO-REALITY.md` first.

Verify every endpoint does what its route, docs, and UI promise. In this repo the
first question is not "what does the handler do" — it is **"does this route exist
in the running app at all, and is it the handler that runs?"**

## Measured baseline (re-measure, don't trust)

- 50 router modules in `backend/routers/`, registered from `backend/server.py`.
- **631 OpenAPI paths / 720 operations / 738 `(method,path)` registrations.**
- Only 5 route decorators live directly in `server.py`.
- `len(app.routes)` returns **7** — lazy `_IncludedRouter` wrappers. Any audit
  quoting that number is broken.

## Steps

1. **Enumerate the real surface** from the running app, not from grep:
   ```bash
   cd backend && JWT_SECRET=testsecret python3 -c "
   import logging; logging.disable(logging.CRITICAL)
   import server
   for p in sorted(server.app.openapi()['paths']): print(p)"
   ```

2. **Diff source-declared vs registered.** `grep -rn '@router\.\(get\|post\|put\|patch\|delete\)' backend/routers`
   gives what the source declares. Anything declared but missing from step 1 is a
   **phantom endpoint**. Confirmed live example: the CRM router fails at import
   (`non-default argument follows default argument (routes.py, line 158)`),
   swallowed to a `logger.warning`, so no `/api/crm` paths exist.

3. **Find shadowed duplicates** (Recipe C). Seven are live now:
   `DELETE /admin/users/{uid}`, `DELETE /admin/users/{uid}/sessions`,
   `GET /admin/users/{uid}/audit`, `GET /admin/users/{uid}/sessions`,
   `GET /exec/control/route-access`, `GET /personas`, and
   `GET /providers/usage-log` (**3x**). For each, determine by execution which
   handler wins. Commit `5623019` was exactly this bug class
   (`/providers/quick-setup` returning 400).
   The OpenAPI generator also emits `Duplicate Operation ID` warnings
   (e.g. `admin_delete_user` in `backend/routers/users.py`) — treat each as a lead.

4. **Identify the actual authorization mechanism per route.** There are three,
   and they do not agree:
   - router-local `_require_rank` / `_dep_current_user` copies — the majority,
     acknowledged in `backend/deps.py:1-17`;
   - canonical `deps.require_rank` / `deps.require_tier` / `deps.dep_current_user`;
   - the outer `AccessGatewayMiddleware` (`backend/server.py:2783`).
   Auditing `deps.py` alone covers a minority of the surface.

5. **Check the gateway snapshot boundary.** `access_gateway.wrap(app)`
   (`backend/server.py:2783`) snapshots public patterns and handler-derived
   requirements at call time (`backend/security/access_control/gateway.py:628-650`;
   observed 133 public / 541 with requirements). The `nam`, `saga`,
   `executive_pipeline`, and `exec_tools` routers are included **after**
   (`:2789, :2798, :2809, :2818`) and were in neither snapshot. Establish
   empirically what the gate does with an unknown route.

6. **Exercise each target route** with `TestClient` across identities:
   unauthenticated, `student`, `instructor`, `admin`, `executive_admin`, and a
   wrong-owner identity. Record status + body. A 503
   `"Service starting up"` means `deps.bind()` had not run
   (`backend/deps.py:56-64`) — a startup-race symptom, not a route defect.

7. **Cross-check against real frontend call sites.** Grep `frontend/src` for the
   path. An endpoint no page calls is dead weight; a page calling a path absent
   from step 1 is a broken feature.

8. Report: phantom routes, shadowed routes, auth-mechanism inconsistencies,
   shape mismatches against consumers, and unexpected 4xx/5xx.

## Constraints

- `source-confirmed` is not sufficient to claim an endpoint exists here. The
  minimum bar is `route-registered`.
- HTTP 200 is not success. `/api/version` returns 200 with a dead DB;
  `/api/health` reports `status: "critical"` yet `railway.toml` health-checks
  `/api/version`, so the production healthcheck cannot fail.
- DB-backed responses cannot be validated in this container (no `mongod`) —
  mark `ENVIRONMENT BLOCKED`.
- API docs are disabled unless `ENABLE_API_DOCS=1` (`backend/server.py:203`);
  generate the spec in-process instead of hitting `/api/openapi.json`.
- Cite `file:line` and paste captured status + body for every finding.
