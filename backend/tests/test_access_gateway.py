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


def _run_middleware(gw, path, method="GET", auth=None):
    audit_calls = []
    gw.bind(None, lambda *a, **k: audit_calls.append((a, k)), _make_current_user("student"))

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
    status, body, audit_calls = _run_middleware(_gw(), "/api/exec/control/state", "GET", "token:student")
    assert status == 403
    assert b"ACCESS_DENIED" in body
    assert any(call[1] == "access_denied" for call in audit_calls), "denial must be audit-logged"


def test_middleware_allows_executive():
    status, body, audit_calls = _run_middleware(_gw(), "/api/exec/control/state", "GET", "token:admin")
    assert status == 200 and body == b"inner-ok"
    assert not audit_calls, "no denial should be logged for authorized access"


def test_middleware_rejects_unauthenticated_with_401_and_audit():
    status, body, audit_calls = _run_middleware(_gw(), "/api/admin/users", "GET")
    assert status == 401
    assert any(call[1] == "access_denied" for call in audit_calls)


def test_middleware_passes_through_non_control_paths():
    status, body, _ = _run_middleware(_gw(), "/api/health", "GET")
    assert status == 200 and body == b"inner-ok"
    status, body, _ = _run_middleware(_gw(), "/api/prices/public", "GET")
    assert status == 200
    status, body, _ = _run_middleware(_gw(), "/api/exec/audio/asset-1", "GET")
    assert status == 200
    status, _, _ = _run_middleware(_gw(), "/api/exec/control/state", "OPTIONS")
    assert status == 200  # preflight passes through


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
