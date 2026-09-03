"""Regression tests for the /modules catalog gate fix and the IAM RBAC matrix
reachability fix.

1. GET /api/modules (catalog LISTING) must map to the free-tier `curriculum`
   feature — the /modules page is a central directory and must never hide the
   catalog behind the Plus gate.  Content (`/api/modules/{slug}`) stays under
   the `courses` (plus) contract.
2. The listing handler must use the optional-auth dependency so anonymous
   visitors can browse the directory (content remains auth-gated).
3. GET/PATCH /api/admin/rbac/matrix must be registered on the real app —
   routers/users.py was never mounted, so the IAM console's matrix tab got
   SPA HTML instead of JSON.

Run: cd backend && python3 -m pytest tests/test_modules_rbac_reachability.py -v
"""
import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "local-test-secret")

from security.feature_control import (  # noqa: E402
    FEATURE_MIN_TIER,
    feature_for_path,
)


def test_catalog_listing_is_free_tier_curriculum():
    # The bare listing is a free, public directory.
    assert feature_for_path("/api/modules") == "curriculum"
    assert FEATURE_MIN_TIER["curriculum"] == "free"


def test_module_content_stays_under_courses_contract():
    # Content and progress surfaces remain tier-gated (plus) — monetized.
    assert feature_for_path("/api/modules/electrical-safety") == "courses"
    assert feature_for_path("/api/progress/me") == "courses"
    assert feature_for_path("/api/labs/foo") == "courses"
    assert feature_for_path("/api/credentials") == "courses"
    assert FEATURE_MIN_TIER["courses"] == "plus"


class _FakeUser:
    id = "u1"
    role = "student"
    feature_tier = "free"


async def _gate_verdict(fake_db):
    from security.feature_control import check_user_feature_access
    return await check_user_feature_access(fake_db, _FakeUser(), "/api/modules")


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, query, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    async def find(self, *a, **k):
        return self

    def to_list(self, n):
        return asyncio.sleep(0)  # placeholder

    async def __aiter__(self):
        return iter(self.docs)


class FakeDB:
    def __init__(self):
        self.user_feature_overrides = FakeCollection([])
        self.tier_definitions = FakeCollection([])
        self.authz_matrix = FakeCollection([{"_id": "matrix", "requirements": {"courses": "plus"}}])
        self.feature_configs = FakeCollection([])


def test_free_student_can_list_catalog_despite_courses_plus_matrix():
    # Even with a stored matrix raising `courses` to plus, the LISTING passes
    # because it maps to the separate `curriculum` feature.
    verdict = asyncio.run(_gate_verdict(FakeDB()))
    assert verdict == ("pass", None), verdict


def test_rbac_matrix_routes_registered_on_real_app():
    import server

    found = []
    for route in server.app.routes:
        orig = getattr(route, "original_router", None)
        sub = getattr(route, "routes", None)
        candidates = []
        if orig is not None:
            candidates = list(getattr(orig, "routes", []) or [])
        elif sub:
            candidates = list(sub)
        else:
            candidates = [route]
        for r in candidates:
            path = getattr(r, "path", None)
            if path and "/admin/rbac/matrix" in path:
                found.extend((m, path) for m in (getattr(r, "methods", []) or []))
    assert ("GET", "/api/admin/rbac/matrix") in found, found
    assert ("PATCH", "/api/admin/rbac/matrix") in found, found


def test_modules_listing_handler_uses_optional_auth():
    import server

    for route in server.app.routes:
        orig = getattr(route, "original_router", None)
        sub = getattr(route, "routes", None)
        candidates = []
        if orig is not None:
            candidates = list(getattr(orig, "routes", []) or [])
        elif sub:
            candidates = list(sub)
        else:
            candidates = [route]
        for r in candidates:
            if getattr(r, "path", None) == "/api/modules" and "GET" in (getattr(r, "methods", []) or []):
                dep = getattr(r, "dependant", None)
                names = [getattr(d.call, "__name__", "") for d in dep.dependencies] if dep else []
                assert "optional_current_user" in names, names
                return
    raise AssertionError("GET /api/modules not found on the app")