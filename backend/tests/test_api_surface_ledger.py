"""Regression guard: the API surface the readiness ledger claims.

The ledger (API_OPERATIONAL_LEDGER.md) was generated on 2026-09-02 and states
"571 unique paths, 647 route-method entries". Re-measuring the mounted app on
2026-09-29 gave different numbers, in both directions:

  * the app mounts 600 further route-method entries that are NOT under /api
    (the executive/admin surface: /exec, /admin, /ai, /video, /billing, ...),
    so a /api-only count materially understates what is actually mounted;
  * app.routes only holds starlette _IncludedRouter wrappers, so the obvious
    len(app.routes) count reports ~53 and looks like the app has no API at all.

This test pins the real, reproducible surface so the ledger cannot silently
drift again, and it walks the nested router tree rather than trusting the
top-level list.
"""
import os
import sys
from collections import defaultdict

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Measured 2026-09-29 against commit d2f521a. Bump deliberately, with a
# ledger update in the same commit, when the surface changes on purpose.
EXPECTED_API_PATHS = 356
EXPECTED_API_METHODS = 405
EXPECTED_TOTAL_PATHS = 882
EXPECTED_TOTAL_METHODS = 1004

# The executive/admin surface is mounted at the root, not under /api. Its
# disappearance would mean a whole router stopped mounting, so pin a sample
# across the largest namespaces.
REQUIRED_ROOT_PREFIXES = (
    "/exec",
    "/admin",
    "/ai",
    "/video",
    "/abo",
    "/academy",
    "/billing",
    "/providers",
    "/sentinel",
)


def _walk(routes, seen=None):
    if seen is None:
        seen = set()
    for r in routes or []:
        if id(r) in seen:
            continue
        seen.add(id(r))
        inner = getattr(r, "original_router", None)
        if inner is not None:
            yield from _walk(getattr(inner, "routes", []), seen)
            continue
        yield r


def _surface():
    import server

    by_path = defaultdict(set)
    for r in _walk(server.app.routes):
        path = getattr(r, "path", None)
        if not isinstance(path, str) or not path:
            continue
        methods = {
            m for m in (getattr(r, "methods", None) or set())
            if m not in ("HEAD", "OPTIONS")
        }
        if not methods:
            continue
        by_path[path].update(methods)
    return by_path


server = pytest.importorskip("server", reason="server module not importable")


def test_route_tree_is_walked_not_just_wrappers():
    """The nested-router walk must find real routes, not just wrappers."""
    by_path = _surface()
    assert len(by_path) > 800, (
        f"only {len(by_path)} routes resolved — the walk is probably not "
        f"descending into nested routers (app.routes holds _IncludedRouter "
        f"wrappers, not the real routes)"
    )


def test_api_surface_matches_ledger_baseline():
    by_path = _surface()
    api = {p: m for p, m in by_path.items() if p.startswith("/api")}
    assert len(api) == EXPECTED_API_PATHS, (
        f"/api unique paths changed: {len(api)} (expected {EXPECTED_API_PATHS}). "
        f"Update API_OPERATIONAL_LEDGER.md in the same commit if intended."
    )
    assert sum(len(m) for m in api.values()) == EXPECTED_API_METHODS


def test_total_surface_matches_ledger_baseline():
    by_path = _surface()
    assert len(by_path) == EXPECTED_TOTAL_PATHS
    assert sum(len(m) for m in by_path.values()) == EXPECTED_TOTAL_METHODS


def test_root_mounted_executive_surface_is_present():
    """Root-mounted (non-/api) namespaces must not silently unmount."""
    by_path = _surface()
    for prefix in REQUIRED_ROOT_PREFIXES:
        assert any(p.startswith(prefix + "/") or p == prefix for p in by_path), (
            f"no routes mounted under {prefix} — a root-mounted router "
            f"appears to have stopped mounting"
        )
