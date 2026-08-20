"""tests/test_access_gateway.py — Unified Access Control Gateway tests.

Covers (stdlib-only — no FastAPI/DB required):
  - Canonical 7-role RBAC hierarchy (must match backend/roles.py exactly)
  - Compliance-tier derivation from real role ranks (no invented tiers)
  - Control-registry integrity (valid tiers, real min_roles, sane route patterns)
  - Control-surface matcher (user-facing/public paths must NOT be gated)
  - Enforcement decisions (deny/allowed at exact role ranks)
  - ASGI middleware: 401/403 blocking + audit logging + passthrough

Run:  cd backend && python3 tests/test_access_gateway.py   (or pytest)
"""

import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from roles import ROLE_RANK  # noqa: E402

from security.access_control.tiers import (  # noqa: E402
    ACCESS_TIERS,
    CONTROL_REGISTRY,
    ROLE_HIERARCHY,
    STORED_ROLES,
    TIER_ORDER,
    find_control,
    rbac_hierarchy,
    registry_snapshot,
    tier_key_for_role,
    tier_level_for_role,
)
from security.access_control.gateway import AccessGateway  # noqa: E402


# ── 1. Canonical 7-role RBAC ──────────────────────────────────────────────────
def test_rbac_has_exactly_seven_stored_roles():
    assert STORED_ROLES == [
        "student", "trial_pass", "instructor",
        "support_staff", "oversight", "admin", "executive_admin",
    ]
    assert len(STORED_ROLES) == 7
    # Ranks must be contiguous 0..7 with public as the unauthenticated baseline.
    assert [r for _, r in ROLE_HIERARCHY] == list(range(8))
    assert ROLE_RANK["executive_admin"] == 7
    assert ROLE_RANK["student"] == 1


def test_rbac_hierarchy_matches_roles_py():
    for role, rank in ROLE_HIERARCHY:
        assert ROLE_RANK[role] == rank
    snapshot = rbac_hierarchy()
    assert len(snapshot) == 8
    assert snapshot[-1] == {"role": "executive_admin", "rank": 7, "stored": True}
    assert snapshot[0]["stored"] is False  # public is the baseline, not a stored role


# ── 2. Compliance tiers are DERIVED from real roles, never invented ───────────
def test_tier_min_roles_are_real_rbac_roles():
    assert ACCESS_TIERS["public"]["min_role"] == "public"
    assert ACCESS_TIERS["public"]["min_rank"] == 0
    assert ACCESS_TIERS["user"]["min_role"] == "student"
    assert ACCESS_TIERS["user"]["min_rank"] == ROLE_RANK["student"] == 1
    assert ACCESS_TIERS["auditor"]["min_role"] == "support_staff"
    assert ACCESS_TIERS["auditor"]["min_rank"] == ROLE_RANK["support_staff"] == 4
    assert ACCESS_TIERS["executive"]["min_role"] == "admin"
    assert ACCESS_TIERS["executive"]["min_rank"] == ROLE_RANK["admin"] == 6


def test_role_to_tier_mapping_uses_real_ranks():
    assert tier_key_for_role("student") == "user"
    assert tier_key_for_role("trial_pass") == "user"
    assert tier_key_for_role("instructor") == "user"
    assert tier_key_for_role("support_staff") == "auditor"
    assert tier_key_for_role("oversight") == "auditor"
    assert tier_key_for_role("admin") == "executive"
    assert tier_key_for_role("executive_admin") == "executive"
    # Empty / "public" = unauthenticated baseline → Public tier (rank 0).
    assert tier_key_for_role("") == "public"
    assert tier_key_for_role("public") == "public"
    # Unknown strings fall through to roles.role_rank() least-privilege fallback ('student').
    assert tier_key_for_role("hacker") == "user"
    # Levels are monotonic across the tier order.
    levels = [tier_level_for_role(r) for r, _ in ROLE_HIERARCHY]
    assert levels == sorted(levels)
    assert levels[0] == 0 and levels[-1] == 3


# ── 3. Control registry integrity ─────────────────────────────────────────────
def test_registry_integrity():
    assert CONTROL_REGISTRY, "registry must not be empty"
    seen_keys = set()
    for key, spec in CONTROL_REGISTRY.items():
        assert key not in seen_keys
        seen_keys.add(key)
        assert spec["required_tier"] in ACCESS_TIERS, f"{key}: unknown tier"
        assert spec.get("routes"), f"{key}: no routes"
        min_role = spec.get("min_role")
        if min_role:
            assert min_role in ROLE_RANK, f"{key}: min_role '{min_role}' is not a real RBAC role"
            # Tier must never be stricter than its min_role (tier is the coarse gate,
            # min_role the exact one) — and tier rank may be looser (handler enforces).
            assert ACCESS_TIERS[spec["required_tier"]]["min_rank"] <= ROLE_RANK[min_role], \
                f"{key}: tier stricter than min_role"
        for route in spec["routes"]:
            if isinstance(route, tuple):
                methods, pattern = route
                assert methods, f"{key}: empty methods"
                route_str = pattern
            else:
                route_str = route
            assert route_str.startswith("/api/"), f"{key}: route must be /api-prefixed"


def test_registry_snapshot_shape():
    snap = registry_snapshot()
    by_key = {c["key"]: c for c in snap}
    entry = by_key["admin_user_management"]
    assert entry["required_tier"] == "executive"
    assert entry["required_tier_label"] == "Executive"
    assert entry["min_role"] == "admin"
    assert "/api/admin/users" in entry["routes"]


# ── 4. Control-surface matcher: gate controls, NEVER user-facing paths ────────
def test_matcher_gates_control_routes():
    assert find_control("/api/admin/users", "GET")["key"] == "admin_user_management"
    assert find_control("/api/admin/users/u-123", "PATCH")["key"] == "admin_user_management"
    assert find_control("/api/exec/control/state", "GET")["key"] == "exec_control_layer"
    assert find_control("/api/exec/panel/toggle", "POST")["key"] == "emergency_breaker_panel"
    assert find_control("/api/exec/panel", "GET")["key"] == "emergency_breaker_panel"
    assert find_control("/api/exec/access-control", "GET")["key"] == "executive_access_control"
    assert find_control("/api/incidents/i-1/resolve", "POST")["key"] == "incident_resolution"
    assert find_control("/api/admin/sites", "GET")["key"] == "commerce_tools_instructor"
    assert find_control("/api/admin/sites", "POST")["key"] == "commerce_admin"
    assert find_control("/api/admin/audit", "GET")["key"] == "commerce_governance_audit"
    assert find_control("/api/admin/audit/export", "GET")["key"] == "admin_insights_export"
    assert find_control("/api/supervisor/dashboard", "GET")["key"] == "supervisor_control"
    assert find_control("/api/sentinel/protocols", "GET")["key"] == "sentinel_governance"
    assert find_control("/api/auditor/summary", "GET")["key"] == "auditor_ledger"
    assert find_control("/api/exec/scout/run", "POST")["key"] == "exec_operations"


def test_matcher_never_gates_public_or_user_facing_paths():
    # User-facing audio stream (ANY authenticated user) must stay open.
    assert find_control("/api/exec/audio/some-asset-id", "GET") is None
    # Public pricing endpoint.
    assert find_control("/api/prices/public", "GET") is None
    # Public supervisor integrity webhook (fires before login).
    assert find_control("/api/supervisor-integrity-alert", "POST") is None
    # Frontend gate map — user-facing by design, excluded from exec_control_layer.
    assert find_control("/api/exec/control/access/public", "GET") is None
    # User-facing notifications / attendance / incidents reporting.
    assert find_control("/api/notifications/me", "GET") is None
    assert find_control("/api/attendance/me", "GET") is None
    assert find_control("/api/incidents", "GET") is None
    assert find_control("/api/incidents", "POST") is None
    # User-level adaptive endpoint living inside routers/admin.py.
    assert find_control("/api/adaptive/me", "GET") is None
    # Health/version never gated.
    assert find_control("/api/health", "GET") is None
    assert find_control("/api/version", "GET") is None


# ── 5. Enforcement decisions at exact role ranks ──────────────────────────────
def _gw():
    return AccessGateway()


def test_enforce_denies_insufficient_tier():
    gw = _gw()
    spec = CONTROL_REGISTRY["exec_control_layer"]
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="student"), spec)
    assert not allowed and reason == "insufficient_tier"
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="admin"), spec)
    assert not allowed and reason == "insufficient_role"  # needs executive_admin


def test_enforce_allows_sufficient_clearance():
    gw = _gw()
    spec = CONTROL_REGISTRY["exec_control_layer"]
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="executive_admin"), spec)
    assert allowed and reason == ""


def test_enforce_exact_min_role():
    gw = _gw()
    spec = CONTROL_REGISTRY["commerce_tools_instructor"]  # tier user (1), min instructor (3)
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="instructor"), spec)
    assert allowed
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="student"), spec)
    assert not allowed and reason == "insufficient_role"


def test_enforce_auditor_tier():
    gw = _gw()
    spec = CONTROL_REGISTRY["commerce_governance_audit"]  # auditor tier, min support_staff
    assert gw._enforce(SimpleNamespace(role="support_staff"), spec)[0] is True
    assert gw._enforce(SimpleNamespace(role="oversight"), spec)[0] is True
    assert gw._enforce(SimpleNamespace(role="student"), spec)[0] is False


# ── 6. ASGI middleware: hard gate + audit trail + passthrough ─────────────────
class _Unauthorized(Exception):
    status_code = 401


async def _inner_app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": b"inner-ok"})


def _make_current_user(role):
    async def current_user(auth):
        if not auth:
            raise _Unauthorized("missing token")
        if auth == "token:admin":
            role_ = "executive_admin"
        else:
            role_ = role
        return SimpleNamespace(id="u-test", email="t@example.com", role=role_)
    return current_user


def _make_gw(role="student", denial_buffer=None):
    gw = AccessGateway()
    gw.bind(None, None, _make_current_user(role), denial_buffer=denial_buffer)
    return gw


def _run_middleware(gw, path, method="GET", auth=None):
    audit_calls = []

    async def audit_fn(actor_id, action, target=None, meta=None):
        audit_calls.append((actor_id, action, target, meta))

    gw._audit_fn = audit_fn

    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "headers": [(b"authorization", auth.encode())] if auth else [],
    }
    started = {}
    body = []

    async def send(msg):
        if msg["type"] == "http.response.start":
            started["status"] = msg["status"]
        elif msg["type"] == "http.response.body":
            body.append(msg.get("body", b""))

    async def receive():
        return {}

    asyncio.run(gw.middleware(_inner_app)(scope, receive, send))
    return started.get("status"), b"".join(body), audit_calls


def test_middleware_blocks_low_tier_with_403_and_audit():
    status, body, audit_calls = _run_middleware(_make_gw(), "/api/exec/control/state", "GET", "token:student")
    assert status == 403
    assert b"ACCESS_DENIED" in body
    assert any(call[1] == "access_denied" for call in audit_calls), "denial must be audit-logged"


def test_middleware_allows_executive():
    status, body, audit_calls = _run_middleware(_make_gw(), "/api/exec/control/state", "GET", "token:admin")
    assert status == 200 and body == b"inner-ok"
    assert not audit_calls, "no denial should be logged for authorized access"


def test_middleware_rejects_unauthenticated_with_401_and_audit():
    status, body, audit_calls = _run_middleware(_make_gw(), "/api/admin/users", "GET")
    assert status == 401
    assert any(call[1] == "access_denied" for call in audit_calls)


def test_middleware_passes_through_non_control_paths():
    status, body, _ = _run_middleware(_make_gw(), "/api/health", "GET")
    assert status == 200 and body == b"inner-ok"
    status, body, _ = _run_middleware(_make_gw(), "/api/prices/public", "GET")
    assert status == 200
    status, body, _ = _run_middleware(_make_gw(), "/api/exec/audio/asset-1", "GET")
    assert status == 200
    status, _, _ = _run_middleware(_make_gw(), "/api/exec/control/state", "OPTIONS")
    assert status == 200  # preflight passes through


# ── 7. Encrypted write-only denial buffer + indexed matcher ───────────────────
def _record(entry, tmp_dir, key=None):
    from security.access_control.audit import DenialAuditBuffer
    buf = DenialAuditBuffer(file_path=os.path.join(tmp_dir, "denials.log"))
    buf.bind(None, encryption_key=key)
    asyncio.run(buf.record(entry))
    with open(os.path.join(tmp_dir, "denials.log"), encoding="utf-8") as fh:
        return buf, json.loads(fh.read().strip())


def test_denial_buffer_plaintext_without_key():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        buf, rec = _record({"control": "x", "reason": "insufficient_tier", "actor_id": None, "path": "/p"}, d)
        assert buf.encrypted is False
        assert rec["encrypted"] is False
        assert rec["control"] == "x"
        assert "insufficient_tier" in rec["payload"]


def test_denial_buffer_encrypts_with_fernet():
    import tempfile
    try:
        from cryptography.fernet import Fernet
    except ImportError:  # pragma: no cover - stdlib-only runner without cryptography
        print("SKIP test_denial_buffer_encrypts_with_fernet (cryptography not installed)")
        return
    key = Fernet.generate_key().decode()
    with tempfile.TemporaryDirectory() as d:
        buf, rec = _record({"control": "x", "reason": "insufficient_tier", "actor_id": "u1", "path": "/api/admin/users"}, d, key=key)
        assert buf.encrypted is True
        assert rec["encrypted"] is True
        assert "insufficient_tier" not in rec["payload"], "payload must be ciphertext"
        # Read-back decrypts the payload (file fallback path).
        rows = asyncio.run(buf.recent(10))
        assert rows[0]["control"] == "x"
        assert rows[0]["reason"] == "insufficient_tier"
        assert rows[0]["path"] == "/api/admin/users"


def test_gateway_writes_denial_to_buffer():
    import tempfile
    from security.access_control.audit import DenialAuditBuffer
    with tempfile.TemporaryDirectory() as d:
        buf = DenialAuditBuffer(file_path=os.path.join(d, "denials.log"))
        buf.bind(None, encryption_key=None)
        gw = _make_gw(denial_buffer=buf)
        status, body, _ = _run_middleware(gw, "/api/exec/control/state", "GET", "token:student")
        assert status == 403
        with open(os.path.join(d, "denials.log"), encoding="utf-8") as fh:
            rec = json.loads(fh.read().strip())
        assert rec["control"] == "exec_control_layer"
        assert rec["reason"] == "insufficient_tier"


def test_matcher_index_groups_by_segment():
    from security.access_control.tiers import _CONTROL_INDEX
    assert "admin" in _CONTROL_INDEX and "exec" in _CONTROL_INDEX
    assert "sentinel" in _CONTROL_INDEX and "supervisor" in _CONTROL_INDEX
    for seg, entries in _CONTROL_INDEX.items():
        for _key, _spec, _methods, pattern in entries:
            assert pattern.split("/")[2] == seg, f"pattern {pattern} indexed under wrong segment"


# ── 8. Intentionally-public routes must NEVER be gated ────────────────────────
def test_matcher_excludes_known_public_routes_from_registry():
    # Public widget, shared-secret heartbeat, and inbound bridge webhook.
    assert find_control("/api/supervisor/public-chat", "POST") is None
    assert find_control("/api/exec/panel/heartbeat", "POST") is None
    assert find_control("/api/bridge/receive", "POST") is None
    # Sibling control routes in the same prefixes stay gated.
    assert find_control("/api/supervisor/dashboard", "GET") is not None
    assert find_control("/api/exec/panel/health", "GET") is not None
    assert find_control("/api/bridge/config", "GET") is not None


def test_route_auth_dep_detection_and_public_discovery():
    from security.access_control.gateway import (
        _discover_public_route_patterns,
        _params_to_wildcard,
        _route_has_auth_dep,
    )
    SimpleNS = SimpleNamespace

    def dep(call):
        return SimpleNS(call=call, dependencies=[])

    async def current_user():
        pass

    def require_role(role):
        async def closure():
            pass
        return closure

    def _require_rank(role):
        async def dep_closure():
            pass
        return dep_closure

    assert _route_has_auth_dep(SimpleNS(dependencies=[dep(current_user)])) is True
    assert _route_has_auth_dep(SimpleNS(dependencies=[dep(_require_rank("admin"))])) is True
    nested = SimpleNS(call=None, dependencies=[dep(require_role("admin"))])
    assert _route_has_auth_dep(SimpleNS(dependencies=[nested])) is True
    assert _route_has_auth_dep(SimpleNS(dependencies=[dep(None)])) is False
    assert _route_has_auth_dep(SimpleNS(dependencies=[])) is False

    assert _params_to_wildcard("/api/incidents/{iid}/resolve") == "/api/incidents/*/resolve"

    public = SimpleNS(path="/supervisor/public-chat", dependant=SimpleNS(dependencies=[]), methods={"POST"})
    authed = SimpleNS(path="/admin/users", dependant=SimpleNS(dependencies=[dep(current_user)]), methods={"GET"})
    patterns = _discover_public_route_patterns(SimpleNS(routes=[public, authed]))
    public_paths = [p for _m, p in patterns]
    assert "/api/supervisor/public-chat" in public_paths
    assert not any(p.startswith("/api/admin") for p in public_paths), "authed routes must not be public"

    # Method-awareness: a public GET on a path never un-gates an authed POST.
    get_only = SimpleNS(path="/band/listings", dependant=SimpleNS(dependencies=[]), methods={"GET"})
    post_only = SimpleNS(path="/band/listings", dependant=SimpleNS(dependencies=[dep(current_user)]), methods={"POST"})
    mixed = _discover_public_route_patterns(SimpleNS(routes=[get_only, post_only]))
    mixed_methods = {m for m, _p in mixed if _p == "/api/band/listings"}
    assert any("GET" in m for m in mixed_methods)
    assert not any("POST" in m for m in mixed_methods), "authed POST must not be excluded"


def test_middleware_skips_discovered_public_routes():
    gw = _make_gw()
    gw._public_route_patterns = [(frozenset({"POST"}), "/api/supervisor/public-chat")]
    # Public route inside a gated prefix passes straight through, no audit noise.
    status, body, audit_calls = _run_middleware(gw, "/api/supervisor/public-chat", "POST")
    assert status == 200 and body == b"inner-ok"
    assert not audit_calls
    # Sibling control routes in the same prefix remain hard-gated.
    status, _, _ = _run_middleware(gw, "/api/supervisor/dashboard", "GET", "token:student")
    assert status == 403


# ── 9. Handler-derived enforcement: the gate is NEVER stricter than the handler ─
def test_closure_required_rank_extraction():
    from security.access_control.gateway import _closure_required_rank
    from roles import ROLE_RANK as RR

    # exec_control.py style: closure captures the role tuple.
    def _require_rank(*roles):
        def dep():
            return roles
        return dep
    # exec.py / server.py require_role style: closure captures needed_rank int.
    def _require_rank_needed(role):
        needed_rank = RR[role]
        def dep():
            return needed_rank
        return dep
    # deps.py require_rank style: closure captures min_roles tuple.
    def require_rank(*min_roles):
        def dep():
            return min_roles
        return dep
    # Unrelated factory that happens to capture a tuple of strings.
    def unrelated(label):
        def dep():
            return (label,)
        return dep

    assert _closure_required_rank(_require_rank("admin")) == RR["admin"]
    assert _closure_required_rank(_require_rank("admin", "executive_admin")) == RR["admin"]
    assert _closure_required_rank(_require_rank_needed("executive_admin")) == 7
    assert _closure_required_rank(require_rank("support_staff")) == RR["support_staff"]
    assert _closure_required_rank(unrelated("some-label")) is None
    assert _closure_required_rank(None) is None


def test_derive_route_min_rank_tree():
    from security.access_control.gateway import _derive_route_min_rank
    SimpleNS = SimpleNamespace

    def _require_rank(*roles):
        def dep():
            return roles
        return dep

    async def current_user():
        pass

    def dep(call):
        return SimpleNS(call=call, dependencies=[])

    # current_user only → user resolved, no rank → None (registry fallback).
    assert _derive_route_min_rank(SimpleNS(dependencies=[dep(current_user)])) is None
    # Rank guard → the exact rank.
    assert _derive_route_min_rank(SimpleNS(dependencies=[dep(_require_rank("admin"))])) == 6
    # Strictest dep wins across nested trees.
    nested = SimpleNS(call=None, dependencies=[dep(_require_rank("executive_admin"))])
    assert _derive_route_min_rank(SimpleNS(dependencies=[dep(_require_rank("admin")), nested])) == 7
    # No deps at all → None.
    assert _derive_route_min_rank(SimpleNS(dependencies=[])) is None
    assert _derive_route_min_rank(None) is None


def test_enforce_with_handler_derived_rank():
    gw = _gw()
    spec = CONTROL_REGISTRY["exec_control_layer"]  # registry documents executive_admin
    # Handler-derived rank (e.g. GET /api/exec/control/tiers requires admin) wins:
    # admin passes even though the registry's min_role is stricter.
    allowed, reason, detail = gw._enforce(SimpleNamespace(role="admin"), spec, effective_rank=6)
    assert allowed and reason == ""
    # Student is still blocked under the same derived rank.
    allowed, reason, detail = gw._enforce(SimpleNamespace(role="student"), spec, effective_rank=6)
    assert not allowed and reason == "insufficient_role"
    assert detail["handler_required_rank"] == 6
    assert detail["handler_required_role"] == "admin"
    # Without a derived rank the registry fallback still applies (existing behavior).
    allowed, reason, _ = gw._enforce(SimpleNamespace(role="admin"), spec)
    assert not allowed and reason == "insufficient_role"


def test_middleware_enforces_handler_derived_rank():
    gw = _make_gw()
    # Registry says executive_admin for the whole /api/exec/control prefix;
    # the real handler for /api/exec/control/tiers requires admin — the gate
    # must match the handler, not the registry guess.
    gw._handler_requirements = {("GET", "/api/exec/control/*"): 6}
    status, body, audit_calls = _run_middleware(gw, "/api/exec/control/tiers", "GET", "token:admin")
    assert status == 200 and body == b"inner-ok"
    assert not audit_calls
    status, _, _ = _run_middleware(gw, "/api/exec/control/tiers", "GET", "token:student")
    assert status == 403


def test_real_app_handler_derived_never_stricter_than_handler():
    """Drift net against the REAL server: every route the registry gates must
    carry a handler-derived rank (so the middleware never falls back to a
    registry guess that could be stricter than the handler), and no discovered
    public route may overlap the gated control surface.
    """
    try:
        import server  # noqa: F401  (needs fastapi + backend deps)
    except Exception as exc:  # pragma: no cover - stdlib-only runner
        print(f"SKIP test_real_app_handler_derived_never_stricter_than_handler ({exc})")
        return

    gw = server.access_gateway  # already wrapped at import with derived data
    assert gw._handler_requirements, "no handler-derived requirements discovered"
    reqs = gw._handler_requirements

    # (1) Every derived rank is a real RBAC rank 1..7.
    for (m, pat), rank in reqs.items():
        assert 1 <= rank <= 7, f"derived rank {rank} for {m} {pat} out of range"

    # (2) Every control-route pattern overlaps at least one real authed route
    # with a derived rank — i.e. the middleware will ALWAYS gate at the
    # handler's own rank, never at a registry fallback that could be stricter.
    from fnmatch import fnmatchcase
    for key, spec in CONTROL_REGISTRY.items():
        for entry in spec["routes"]:
            methods, pattern = entry if isinstance(entry, tuple) else (None, entry)
            if "*" in pattern:
                wild = pattern
            elif pattern.endswith("/"):
                wild = pattern + "*"
            else:
                wild = pattern
            hits = [
                (m, pat) for (m, pat) in reqs
                if (methods is None or m in methods)
                and fnmatchcase(pat, wild)
            ]
            assert hits, f"{key}: control route {pattern} has NO handler-derived route — the gate would fall back to a registry guess"

    # (3) No discovered public route may match any control pattern: a public
    # route must never be gated.  Sample a concrete path per public pattern.
    for methods, pat in gw._public_route_patterns:
        sample = pat.replace("*", "x")
        m = next(iter(methods), "GET")
        assert find_control(sample, m) is None, f"public route {m} {pat} overlaps the gated control surface"

    # (4) No route whose guard is NOT rank-derivable may be inside the control
    # surface: if the middleware cannot read the handler's own requirement it
    # would gate on a registry guess (potentially stricter than the handler).
    from security.access_control.gateway import (
        _derive_route_min_rank,
        _flatten_routes,
        _params_to_wildcard,
        _route_has_auth_dep,
    )
    # server.app is the FastAPI instance itself (the gate is registered via
    # app.add_middleware — never rebound to a wrapper function).
    orig = getattr(server.app, "routes", None) and server.app
    assert orig is not None, "server.app is not a FastAPI instance"
    for route in _flatten_routes(getattr(orig, "routes", [])):
        dependant = getattr(route, "dependant", None)
        if dependant is None or not _route_has_auth_dep(dependant):
            continue
        if _derive_route_min_rank(dependant) is not None:
            continue  # derivable → gated at exactly the handler's rank
        raw = getattr(route, "path", "") or ""
        methods = set(getattr(route, "methods", []) or [])
        methods.discard("HEAD")
        methods.discard("OPTIONS")
        for p in {raw, "/api" + raw}:
            if not p.startswith("/api"):
                continue
            pat = _params_to_wildcard(p)
            sample = pat.replace("*", "x")
            for m in methods or {"GET"}:
                assert find_control(sample, m) is None, \
                    f"route {m} {pat} has no handler-derivable rank but lies inside the gated control surface"


# ── 10. Wrap must NOT rebind app (the production 404 regression) ─────────────
def test_wrap_keeps_app_a_fastapi_instance():
    """Regression: wrap() used to rebind the module-level app to an ASGI
    function, so startup's SPA mount crashed with
    AttributeError: 'function' object has no attribute 'mount' and / 404'd.
    The gate must register via app.add_middleware and return the same app.
    """
    try:
        from fastapi import FastAPI
        from starlette.testclient import TestClient
    except ImportError:  # pragma: no cover - stdlib-only runner
        print("SKIP test_wrap_keeps_app_a_fastapi_instance (fastapi/starlette not installed)")
        return

    gw = _make_gw()
    app = FastAPI()
    returned = gw.wrap(app)
    assert returned is app, "wrap() must return the SAME FastAPI instance"
    assert hasattr(app, "mount") and hasattr(app, "routes"), "app must stay a FastAPI app"
    # The gate is live through the standard middleware stack.

    @app.get("/api/health")
    async def health():
        return {"ok": True}

    @app.get("/api/exec/control/state")
    async def control():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/exec/control/state").status_code == 401  # gate live
    assert client.get(
        "/api/exec/control/state", headers={"Authorization": "token:admin"}
    ).status_code == 200
    assert client.get(
        "/api/exec/control/state", headers={"Authorization": "token:student"}
    ).status_code == 403


def test_middleware_class_gates_like_raw_asgi():
    """The Starlette middleware class and the raw-ASGI adapter share the same
    gate decision (_check) — behavior must be identical."""
    try:
        from fastapi import FastAPI
        from starlette.testclient import TestClient
    except ImportError:  # pragma: no cover
        print("SKIP test_middleware_class_gates_like_raw_asgi (fastapi not installed)")
        return

    gw = _make_gw()
    app = FastAPI()
    app.add_middleware(gw.middleware_class())

    @app.get("/api/exec/control/state")
    async def control():
        return {"ok": True}

    @app.get("/api/prices/public")
    async def public():
        return {"ok": True}

    client = TestClient(app)
    # Same outcomes as the raw-ASGI adapter tests: 401 unauthenticated,
    # 200 executive, 403 student, passthrough for public paths.
    assert client.get("/api/exec/control/state").status_code == 401
    assert client.get(
        "/api/exec/control/state", headers={"Authorization": "token:admin"}
    ).status_code == 200
    assert client.get(
        "/api/exec/control/state", headers={"Authorization": "token:student"}
    ).status_code == 403
    assert client.get("/api/prices/public").status_code == 200


# ── Runner (works without pytest installed) ───────────────────────────────────
if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{sum(1 for n in globals() if n.startswith('test_') and callable(globals()[n])) - failures}/{sum(1 for n in globals() if n.startswith('test_') and callable(globals()[n]))} passed")
    sys.exit(1 if failures else 0)
