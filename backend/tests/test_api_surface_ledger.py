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

# Measured 2026-09-29 against commit d2f521a; re-measured 2026-10-11 after
# F5-F9 merged; re-measured again 2026-10-11 after the Soup work merged (the
# partner API's five routes are wrapped by _IncludedRouter and only become
# visible to this walk through the mount that serves them, so the countable
# delta is the JSON 404 catch-all registered for unknown /api/* paths).
# Re-measured 2026-10-15 after PRs #505-#512 (+3 paths from merged feature
# work) and after removing the dead /api/ai/ai/chat and /api/ai/ai/helper
# shadow routes that the double-prefixed routers/ai.py include used to mount
# (-2 paths, -2 methods).
# Re-measured 2026-10-15 after the Tier 1 batch (#515-#519): +5 paths, +4
# methods — all five are read/admin routes added in this session, none of them
# shadowing an existing path:
#   /api/nam/status (GET)                    routers/nam.py
#   /api/competition/context/{context_id}    routers/competition.py
#   /api/academy/enrollments (GET)            routers/academy.py
#   /api/academy/students/{student_id}/courses (GET)  routers/academy.py
#   /api/admin/users/{uid}/restore (POST)    routers/users.py
# Bump deliberately, with a ledger update in the same commit, when the surface
# changes on purpose.
EXPECTED_API_PATHS = 361
EXPECTED_API_METHODS = 415
EXPECTED_TOTAL_PATHS = 899
EXPECTED_TOTAL_METHODS = 1033

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


def test_no_duplicate_path_method_pairs():
    """No path+method pair may be registered twice.

    Two registrations of the same pair mean the first match wins and edits to
    the second silently do nothing. This repo shipped exactly that: the
    double-prefixed routers/ai.py include (prefix="/api/ai" + "/ai/chat")
    mounted a shadow copy of /api/ai/chat at /api/ai/ai/chat. Both copies now
    live at one path each and this guard keeps it that way.
    """
    by_path = _surface()
    seen: dict = defaultdict(int)
    for r in _walk(server.app.routes):
        path = getattr(r, "path", None)
        if not isinstance(path, str) or not path:
            continue
        for m in (getattr(r, "methods", None) or set()):
            if m in ("HEAD", "OPTIONS"):
                continue
            seen[(path, m)] += 1
    dupes = sorted(k for k, n in seen.items() if n > 1)
    assert not dupes, (
        f"duplicate path+method registrations: {dupes[:10]} — the first match "
        f"wins, so the second registration is dead code that silently ignores edits"
    )


def test_no_doubled_router_prefixes():
    """No route may carry a doubled namespace like /api/ai/ai/... .

    A doubled prefix is the signature of a router included with a prefix that
    repeats a segment already present in its own decorators.
    """
    by_path = _surface()
    doubled = sorted(p for p in by_path if "/ai/ai/" in p)
    assert not doubled, (
        f"double-prefixed AI routes mounted: {doubled} — these are shadow "
        f"copies of the real /api/ai/* handlers"
    )
