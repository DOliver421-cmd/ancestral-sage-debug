"""gateway.py — AccessGateway: the hard server-side gatekeeper.

Two enforcement layers, both driven by the single registry in tiers.py:

1. Starlette middleware (AccessGateway.wrap) — registered via
   app.add_middleware(...) so the module-level `app` REMAINS the FastAPI
   instance (startup handlers that mount the SPA, static files and any route
   tooling keep working).  It intercepts every request whose path belongs to
   the monitored control surface BEFORE any handler runs.  A user with
   insufficient clearance gets a 403 (or 401 when unauthenticated) and the
   denial is written to the audit log.

2. FastAPI dependency (AccessGateway.guard / authorize) — the per-route gate
   used by the executive dashboard itself and available for any future route.

NEVER STRICTER THAN THE HANDLER: at wrap time the gateway reads each route's
OWN guard out of its FastAPI dependency tree (the *_require_rank / require_rank
closures capture the exact roles they enforce).  Every gated request is then
enforced at exactly that handler-derived rank — a public route is discovered
and never gated, an admin-required route is enforced at admin, never at a
hand-maintained registry guess.  Where no rank is derivable the registry's
documented tier + min_role is the fallback.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from roles import ROLE_RANK

from .audit import DenialAuditBuffer
from .tiers import (
    ACCESS_TIERS,
    CONTROL_REGISTRY,
    ROLE_HIERARCHY,
    find_control,
    tier_key_for_role,
    tier_level_for_role,
)

logger = logging.getLogger("lcewai.access_control")

# Rank -> role label (for audit detail on handler-derived gates).
_RANK_TO_ROLE: dict = {rank: role for role, rank in ROLE_HIERARCHY}

# Callables that identify a route as user-authenticated (FastAPI deps). A route
# carrying any of these must go through the gate; a route carrying NONE of them
# is intentionally public (webhooks, shared-secret endpoints, public widgets)
# and must never be gated by the middleware.
_AUTH_MARKERS = (
    "current_user", "require_user", "_dep_current_user", "_user",
    "_require_rank", "require_role", "assert_role", "require_tier",
    "_require_executive", "authorize",
)

# Rank-guard FACTORIES whose returned closures capture the roles they enforce.
# The closure cells hold the required role names (tuple) or the precomputed
# needed_rank (int) — reading them yields the handler's own requirement.
_RANK_GUARD_MARKERS = ("_require_rank", "require_rank", "require_role", "assert_role")


def _route_has_auth_dep(dependant, _seen=None) -> bool:
    """True iff the route's FastAPI dependency tree resolves the user."""
    if dependant is None:
        return False
    _seen = _seen if _seen is not None else set()
    for d in getattr(dependant, "dependencies", []) or []:
        call = getattr(d, "call", None)
        q = (getattr(call, "__qualname__", "") or "") + (getattr(call, "__name__", "") or "")
        if any(m in q for m in _AUTH_MARKERS):
            # Optional-auth dependencies (e.g. _optional_current_user) resolve a
            # user only when credentials are supplied — the route is
            # intentionally public (store catalog, public puzzle). Matching the
            # bare "current_user" marker must not gate these.
            if "optional_current_user" in q:
                continue
            return True
        sub = getattr(d, "dependencies", None)
        if sub and id(sub) not in _seen:
            _seen.add(id(sub))
            if _route_has_auth_dep(d, _seen):
                return True
    return False


def _flatten_routes(routes) -> list:
    """Flatten FastAPI/Starlette route tables (nested routers included)."""
    out = []
    for r in routes or []:
        if getattr(r, "path", None):
            out.append(r)
        elif hasattr(r, "original_router"):
            out.extend(_flatten_routes(r.original_router.routes))
        elif hasattr(r, "routes"):
            out.extend(_flatten_routes(r.routes))
    return out


def _discover_public_route_patterns(app) -> list:
    """(method, request-path-pattern) pairs of routes that resolve NO user.

    Method-aware so a public GET on a path never un-gates an authenticated POST
    on the same path.  Paths are fnmatch patterns ({param} segments become
    wildcards); both raw and /api-prefixed forms are recorded because nested
    routers keep unprefixed paths but the /api prefix is applied at request time.
    """
    patterns = set()
    for route in _flatten_routes(getattr(app, "routes", [])):
        dependant = getattr(route, "dependant", None)
        if dependant is None or _route_has_auth_dep(dependant):
            continue
        raw = getattr(route, "path", "") or ""
        if not raw:
            continue
        methods = set(getattr(route, "methods", []) or [])
        methods.discard("HEAD")
        methods.discard("OPTIONS")
        methods = methods or {"GET"}
        for p in {raw, "/api" + raw}:
            if not p.startswith("/api"):
                continue
            patterns.add((frozenset(methods), _params_to_wildcard(p)))
    return sorted(patterns, key=lambda t: (t[1], sorted(t[0])))


def _params_to_wildcard(path: str) -> str:
    """/api/x/{uid}/y -> /api/x/*/y (fnmatch-compatible)."""
    out = []
    for seg in path.split("/"):
        out.append("*" if seg.startswith("{") and seg.endswith("}") else seg)
    return "/".join(out)


def _closure_required_rank(call) -> Optional[int]:
    """Extract the minimum rank a rank-guard closure enforces, else None.

    Both guard styles used in this codebase build closures that capture the
    required role names (a tuple, e.g. exec_control.py's _require_rank) or the
    precomputed needed_rank (an int, e.g. exec.py's _require_rank and
    server.py's require_role).  Reading those cells gives the handler's OWN
    requirement — the single source of truth for the gate.
    """
    qname = (getattr(call, "__qualname__", "") or "") + (getattr(call, "__name__", "") or "")
    # dashboard._require_executive is a plain function (not a factory) that
    # delegates to authorize("executive_access_control") — executive_admin.
    if "_require_executive" in qname:
        return ROLE_RANK["executive_admin"]
    if not any(m in qname for m in _RANK_GUARD_MARKERS):
        return None
    for cell in (getattr(call, "__closure__", None) or ()):
        value = cell.cell_contents
        if isinstance(value, (tuple, list, set, frozenset)):
            roles = [r for r in value if isinstance(r, str)]
            if roles and len(roles) == len(value) and all(r in ROLE_RANK for r in roles):
                return min(ROLE_RANK[r] for r in roles)
        elif isinstance(value, int) and 0 < value <= ROLE_RANK["executive_admin"]:
            return value
    return None


def _derive_route_min_rank(dependant) -> Optional[int]:
    """Strictest rank the route's dependency tree enforces, else None.

    None means either the route resolves no user at all (intentionally
    public — never gated) or a user is resolved but no rank is derivable
    (the caller falls back to the registry).  Same traversal semantics as
    _route_has_auth_dep so the two views of the route table can't disagree.
    """
    if dependant is None:
        return None
    best = None
    found_auth = False
    stack = [dependant]
    seen = set()
    while stack:
        node = stack.pop()
        for d in getattr(node, "dependencies", []) or []:
            call = getattr(d, "call", None)
            if call is not None:
                q = (getattr(call, "__qualname__", "") or "") + (getattr(call, "__name__", "") or "")
                if any(m in q for m in _AUTH_MARKERS):
                    found_auth = True
                rank = _closure_required_rank(call)
                if rank is not None:
                    best = rank if best is None else max(best, rank)
            sub = getattr(d, "dependencies", None)
            if sub and id(sub) not in seen:
                seen.add(id(sub))
                stack.append(d)
    # A plain authenticated route has a real minimum even when it has no
    # separate role dependency: the established lowest stored role is student.
    # This makes it governable from the route matrix without inventing a role
    # or making the gateway stricter than the handler.
    if found_auth:
        return best if best is not None else ROLE_RANK["student"]
    return None


def _derive_handler_requirements(app) -> dict:
    """(method, /api-wildcard-pattern) -> the handler's own minimum rank.

    Built once at wrap time from the app's real route table, method-aware
    (a public GET on a path never supplies a rank for an authed POST).
    """
    reqs: dict = {}
    for route in _flatten_routes(getattr(app, "routes", [])):
        rank = _derive_route_min_rank(getattr(route, "dependant", None))
        if rank is None:
            continue
        raw = getattr(route, "path", "") or ""
        if not raw:
            continue
        methods = set(getattr(route, "methods", []) or [])
        methods.discard("HEAD")
        methods.discard("OPTIONS")
        methods = methods or {"GET"}
        for p in {raw, "/api" + raw}:
            if not p.startswith("/api"):
                continue
            pat = _params_to_wildcard(p)
            for m in methods:
                key = (m, pat)
                reqs[key] = max(rank, reqs.get(key, 0))
    return reqs


def _matches_public(path: str, pattern: str) -> bool:
    from fnmatch import fnmatchcase
    return fnmatchcase(path, pattern)


class AccessGateway:
    """Centralized access-control gateway. Bound to shared deps by server.py."""

    def __init__(self) -> None:
        self._db = None
        self._audit_fn = None
        self._current_user_fn = None
        self._denial_buffer: DenialAuditBuffer | None = None
        self._public_route_patterns: list = []
        self._handler_requirements: dict = {}
        self.active = False

    # ── Wiring (called by server.py at startup) ────────────────────────────────
    def bind(self, db, audit_fn, current_user_fn, denial_buffer: DenialAuditBuffer | None = None) -> None:
        """Inject shared dependencies: db, audit(), current_user() and the
        encrypted write-only denial buffer (see security/access_control/audit.py)."""
        self._db = db
        self._audit_fn = audit_fn
        self._current_user_fn = current_user_fn
        self._denial_buffer = denial_buffer
        self.active = True
        if denial_buffer is not None:
            logger.info(
                "AccessGateway denial buffer attached (encryption=%s)",
                "ON" if denial_buffer.encrypted else "OFF - AUDIT_ENCRYPTION_KEY missing",
            )
        logger.info(
            "AccessGateway active: %d controls monitored across %d tiers",
            len(CONTROL_REGISTRY), len(ACCESS_TIERS),
        )

    # ── Core decision ──────────────────────────────────────────────────────────
    def _enforce(self, user, spec, effective_rank: Optional[int] = None) -> tuple:
        """Return (allowed: bool, reason: str, detail: dict).

        *effective_rank* is the handler's OWN minimum rank, derived from the
        route's dependency tree at wrap time — when present it is the single
        source of truth and the gate is exactly as strict as the handler (no
        more, no less).  When absent (rank not derivable), the registry's
        documented tier + min_role gate is applied as the fallback.
        """
        user_role = getattr(user, "role", "") or ""
        user_tier = tier_key_for_role(user_role)
        user_level = tier_level_for_role(user_role)

        if effective_rank is not None:
            from roles import role_rank
            if role_rank(user_role) < effective_rank:
                return (
                    False,
                    "insufficient_role",
                    {
                        "user_role": user_role,
                        "user_tier": user_tier,
                        "user_tier_level": user_level,
                        "required_tier": spec["required_tier"],
                        "handler_required_rank": effective_rank,
                        "handler_required_role": _RANK_TO_ROLE.get(effective_rank),
                    },
                )
            return True, "", {}

        req_level = ACCESS_TIERS[spec["required_tier"]]["level"]
        if user_level < req_level:
            return (
                False,
                "insufficient_tier",
                {
                    "user_role": user_role,
                    "user_tier": user_tier,
                    "user_tier_level": user_level,
                    "required_tier": spec["required_tier"],
                    "required_tier_level": req_level,
                },
            )

        min_role = spec.get("min_role")
        if min_role:
            from roles import role_rank
            if role_rank(user_role) < role_rank(min_role):
                return (
                    False,
                    "insufficient_role",
                    {
                        "user_role": user_role,
                        "user_tier": user_tier,
                        "required_role": min_role,
                        "required_tier": spec["required_tier"],
                    },
                )

        return True, "", {}

    def _lookup_handler_entry(self, method: str, path: str) -> Optional[dict]:
        """Return the registered authenticated route matched by a request."""
        for (m, pat), rank in self._handler_requirements.items():
            if method == m and _matches_public(path, pat):
                return {"method": m, "path_pattern": pat, "rank": rank}
        return None

    def _lookup_handler_rank(self, method: str, path: str) -> Optional[int]:
        """Handler-derived rank for (method, path), or None (registry fallback)."""
        entry = self._lookup_handler_entry(method, path)
        return entry["rank"] if entry else None

    def _route_spec(self, method: str, path: str, registry_spec=None) -> Optional[dict]:
        """Build a truthful synthetic registry entry for an authenticated route.

        The static registry remains the named control catalogue. Every other
        authenticated FastAPI route is still a real gateway surface, keyed by
        its method and discovered path pattern, so the executive matrix can
        govern it without pretending an unregistered route is protected.
        """
        if registry_spec is not None:
            return registry_spec
        entry = self._lookup_handler_entry(method, path)
        if entry is None:
            return None
        required_role = _RANK_TO_ROLE.get(entry["rank"], "student")
        return {
            "key": f"route:{entry['method']}:{entry['path_pattern']}",
            "label": f"{entry['method']} {entry['path_pattern']}",
            "category": "Authenticated application route",
            "source": "FastAPI route table",
            "description": "Discovered from the deployed route dependency graph.",
            "required_tier": tier_key_for_role(required_role),
            "min_role": required_role,
            "routes": [entry["path_pattern"]],
        }

    async def _load_route_policy(self, method: str, path: str, user=None) -> Optional[dict]:
        """Read the effective route policy for a request.

        A per-user override is evaluated first, then the executive role policy.
        Both are additional restrictions; neither can loosen the handler's
        own dependency-derived minimum rank.
        """
        entry = self._lookup_handler_entry(method, path)
        if entry is None or self._db is None:
            return None
        route_key = f"{entry['method']} {entry['path_pattern']}"
        if user is not None:
            user_policy = await self._db.user_route_access.find_one(
                {"user_id": user.id, "route_key": route_key}, {"_id": 0}
            )
            if user_policy:
                return user_policy
        return await self._db.route_access.find_one(
            {"route_key": route_key}, {"_id": 0}
        )

    async def route_access_snapshot(self) -> list:
        """Return every authenticated route and its live executive policy."""
        policies = {}
        if self._db is not None:
            docs = await self._db.route_access.find({}, {"_id": 0}).to_list(length=10000)
            policies = {d.get("route_key"): d for d in docs if d.get("route_key")}
        rows = []
        for (method, pattern), rank in sorted(self._handler_requirements.items()):
            route_key = f"{method} {pattern}"
            policy = policies.get(route_key) or {}
            role = _RANK_TO_ROLE.get(rank, "student")
            rows.append({
                "route_key": route_key,
                "method": method,
                "path_pattern": pattern,
                "handler_min_role": role,
                "handler_min_rank": rank,
                "handler_required_tier": tier_key_for_role(role),
                "enabled": policy.get("enabled", True),
                "allowed_roles": policy.get("allowed_roles"),
                "policy_source": "executive_override" if policy else "handler_default",
                "control": find_control(pattern, method),
            })
        return rows

    # ── Audit logging (compliance trail) ───────────────────────────────────────
    async def _log_denial(self, user, spec, path, method, reason, detail) -> None:
        actor = getattr(user, "id", None) or getattr(user, "email", None)
        control_key = spec.get("key", "unknown")
        meta = {
            "control": control_key,
            "control_label": spec.get("label"),
            "path": path,
            "method": method,
            "reason": reason,
            "user_role": getattr(user, "role", None),
            "user_tier": tier_key_for_role(getattr(user, "role", "") or ""),
            "required_tier": spec.get("required_tier"),
            **detail,
        }
        if self._audit_fn is not None:
            try:
                await self._audit_fn(actor, "access_denied", target=control_key, meta=meta)
            except Exception:  # pragma: no cover - audit must never break the gate
                logger.exception("access_denied audit write failed")
        if self._denial_buffer is not None:
            try:
                await self._denial_buffer.record({"actor_id": actor, **meta})
            except Exception:  # pragma: no cover - buffer must never break the gate
                logger.exception("access_denied buffer write failed")
        logger.warning(
            "ACCESS_DENIED control=%s path=%s method=%s actor=%s reason=%s",
            control_key, path, method, actor, reason,
        )

    async def _log_anonymous_denial(self, spec, path, method, reason) -> None:
        control_key = spec.get("key", "unknown")
        meta = {
            "control": control_key,
            "control_label": spec.get("label"),
            "path": path,
            "method": method,
            "reason": reason,
            "user_role": None,
            "user_tier": "public",
            "required_tier": spec.get("required_tier"),
        }
        if self._audit_fn is not None:
            try:
                await self._audit_fn(None, "access_denied", target=control_key, meta=meta)
            except Exception:  # pragma: no cover
                logger.exception("access_denied audit write failed")
        if self._denial_buffer is not None:
            try:
                await self._denial_buffer.record({"actor_id": None, **meta})
            except Exception:  # pragma: no cover
                logger.exception("access_denied buffer write failed")
        logger.warning(
            "ACCESS_DENIED control=%s path=%s method=%s actor=None reason=%s",
            control_key, path, method, reason,
        )

    # ── FastAPI dependency (per-route hard gate) ───────────────────────────────
    async def authorize(self, authorization: Optional[str], control_key: str):
        """Resolve the current user and enforce the control's tier.

        Raises HTTPException(401) when unauthenticated, HTTPException(403) when
        clearance is insufficient (denial is audit-logged).  Returns the user
        on success.
        """
        from fastapi import HTTPException

        spec = {**CONTROL_REGISTRY[control_key], "key": control_key}
        user = await self._current_user_fn(authorization)  # raises 401 when missing/invalid
        allowed, reason, detail = self._enforce(user, spec)
        if not allowed:
            await self._log_denial(user, spec, f"/api/.../{control_key}", "dependency", reason, detail)
            raise HTTPException(
                status_code=403,
                detail=f"Access denied — {spec['label']} requires {ACCESS_TIERS[spec['required_tier']]['label']} clearance.",
            )
        return user

    def guard(self, control_key: str):
        """Return a FastAPI dependency that hard-gates *control_key*."""
        from fastapi import Depends, Header

        async def dep(authorization: Optional[str] = Header(None)):
            return await self.authorize(authorization, control_key)

        return dep

    # ── Middleware (defense-in-depth for the whole control surface) ───────────
    async def _check(self, path: str, method: str, auth_header: Optional[str], spec) -> Optional[tuple]:
        """Core gate decision, shared by the Starlette and raw-ASGI adapters.

        Returns (status_code, detail) to reject with — after audit-logging the
        denial — or None to let the request through.
        """
        # Intentionally-public routes (no user-auth dependency on the route)
        # are excluded from gating — e.g. /api/supervisor/public-chat,
        # /api/exec/panel/heartbeat, /api/bridge/receive. Method-aware: a
        # public GET never un-gates an authenticated POST on the same path.
        if any(method in methods and _matches_public(path, p)
               for methods, p in self._public_route_patterns):
            return None

        try:
            user = await self._current_user_fn(auth_header)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 401:
                await self._log_anonymous_denial(spec, path, method, "unauthenticated")
                return (401, "Authentication required for this control.")
            if status == 403:
                await self._log_anonymous_denial(spec, path, method, "account_deactivated")
                return (403, "Account deactivated.")
            # Fail closed: if we cannot verify clearance, the control stays shut.
            logger.exception("AccessGateway could not resolve user for %s", path)
            return (503, "Access control unavailable — request rejected.")

        # Executive route policy is an additional restriction, never a way to
        # loosen the handler's own dependency. Missing policy = current behavior.
        try:
            policy = await self._load_route_policy(method, path, user)
        except Exception:
            logger.exception("Route access policy unavailable for %s %s", method, path)
            return (503, "Access control unavailable — request rejected.")
        if policy:
            allowed_roles = policy.get("allowed_roles")
            if policy.get("enabled") is False or (
                isinstance(allowed_roles, list)
                and user.role not in allowed_roles
            ):
                detail = {
                    "route_key": policy.get("route_key"),
                    "allowed_roles": allowed_roles or [],
                }
                await self._log_denial(user, spec, path, method, "route_policy_denied", detail)
                return (403, "Access denied — this route is disabled for your role.")

        # Enforce at EXACTLY the rank the route's own handler enforces
        # (derived at wrap time). Registry values apply only when no rank is
        # derivable — the gateway can never loosen the handler.
        allowed, reason, detail = self._enforce(
            user, spec, effective_rank=self._lookup_handler_rank(method, path)
        )
        if not allowed:
            await self._log_denial(user, spec, path, method, reason, detail)
            req = ACCESS_TIERS[spec["required_tier"]]
            return (403, f"Access denied — {spec['label']} requires {req['label']} clearance.")
        return None

    def middleware_class(self):
        """A Starlette middleware class for ``app.add_middleware(...)``.

        Registering the gate THIS way — instead of rebinding the module-level
        app to a wrapped ASGI function — keeps ``app`` the FastAPI instance, so
        startup handlers (SPA mount, static files) and any route tooling keep
        working.  The gate still runs before every handler.
        """
        from starlette.middleware.base import BaseHTTPMiddleware
        from fastapi.responses import JSONResponse

        gateway = self

        class AccessGatewayMiddleware(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                method = (request.method or "GET").upper()
                if method == "OPTIONS":  # CORS preflight passes through
                    return await call_next(request)
                path = request.url.path
                spec = gateway._route_spec(method, path, find_control(path, method))
                if spec is None:
                    return await call_next(request)
                result = await gateway._check(
                    path, method, request.headers.get("authorization"), spec
                )
                if result is None:
                    return await call_next(request)
                status, detail = result
                return JSONResponse(
                    status_code=status,
                    content={"detail": detail, "error": "ACCESS_DENIED"},
                    headers={"cache-control": "no-store"},
                )

        return AccessGatewayMiddleware

    def middleware(self, app):
        """Return an ASGI callable that gates the registered control surface.

        Dependency-free adapter (no Starlette import) so the stdlib-only test
        runner can exercise the gate end-to-end.  Production uses
        ``middleware_class()`` via ``app.add_middleware`` instead.
        """

        async def dispatch(scope, receive, send):
            if scope.get("type") != "http":
                return await app(scope, receive, send)

            path = scope.get("path") or ""
            method = (scope.get("method") or "GET").upper()
            if method == "OPTIONS":  # let CORS preflight through
                return await app(scope, receive, send)

            spec = self._route_spec(path=path, method=method, registry_spec=find_control(path, method))
            if spec is None:
                return await app(scope, receive, send)

            auth_header = None
            for key, value in (scope.get("headers") or []):
                if key.lower() == b"authorization":
                    auth_header = value.decode("latin-1")
                    break

            result = await self._check(path, method, auth_header, spec)
            if result is None:
                return await app(scope, receive, send)
            return await self._reject(send, *result)

        return dispatch

    def wrap(self, app):
        """Register the gate as a Starlette middleware on a FastAPI app.

        Discovers the app's intentionally-unauthenticated routes (public
        widgets, shared-secret webhooks, heartbeat endpoints) and the
        handler-derived rank of every route, then registers the gate via
        ``app.add_middleware``.  Returns the SAME app object — never a wrapper
        function — so ``server.app`` stays the FastAPI instance and startup
        handlers (SPA mount) keep working.
        """
        self._public_route_patterns = _discover_public_route_patterns(app)
        self._handler_requirements = _derive_handler_requirements(app)
        if self._public_route_patterns:
            logger.info(
                "AccessGateway: %d intentionally-public route(s) excluded from gating",
                len(self._public_route_patterns),
            )
        logger.info(
            "AccessGateway: %d route(s) carry handler-derived requirements (never stricter than the handler)",
            len(self._handler_requirements),
        )
        app.add_middleware(self.middleware_class())
        return app

    @staticmethod
    async def _reject(send, status: int, detail: str) -> None:
        body = json.dumps({"detail": detail, "error": "ACCESS_DENIED"}).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"cache-control", b"no-store"),
        ]
        await send({"type": "http.response.start", "status": status, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    # ── Dashboard data helpers ─────────────────────────────────────────────────
    async def denial_stats(self, limit: int = 500) -> dict:
        """Per-control denial counts + last-denied timestamps.

        Prefers the encrypted write-only buffer (access_control_denials),
        falls back to the legacy audit_log collection.
        """
        if self._denial_buffer is not None:
            return await self._denial_buffer.stats(limit=limit)
        stats: dict = {}
        if self._db is None:
            return stats
        try:
            cursor = self._db.audit_log.find(
                {"action": "access_denied"},
                {"_id": 0, "meta.control": 1, "at": 1, "meta.reason": 1},
            ).sort("at", -1).limit(limit)
            rows = await cursor.to_list(length=limit)
        except Exception:
            logger.exception("denial_stats query failed")
            return stats
        for row in rows:
            control = ((row.get("meta") or {}).get("control")) or "unknown"
            entry = stats.setdefault(control, {"denials": 0, "last_denied_at": None})
            entry["denials"] += 1
            if entry["last_denied_at"] is None:
                entry["last_denied_at"] = row.get("at")
        return stats

    async def recent_denials(self, limit: int = 50) -> list:
        """Most recent access-denied audit entries (executive dashboard feed).

        Prefers the encrypted write-only buffer, falls back to audit_log.
        """
        if self._denial_buffer is not None:
            return await self._denial_buffer.recent(limit=limit)
        if self._db is None:
            return []
        try:
            cursor = self._db.audit_log.find(
                {"action": "access_denied"},
                {"_id": 0, "actor_id": 1, "target": 1, "meta": 1, "at": 1},
            ).sort("at", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception:
            logger.exception("recent_denials query failed")
            return []
