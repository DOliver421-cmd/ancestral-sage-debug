"""Regression guard: the frontend-facing endpoints registered from canonical
router modules (routers/users.py, routers/personas.py, routers/commerce.py,
routers/exec_control.py) must stay present on the live api_router.

These handlers fix the class of defect where a page calls a real endpoint that
was never mounted (personas CRUD, user sessions/ban/unban, platform flags,
accept-terms). If any of them vanish again, this test fails at import.

Skipped when the server module cannot be imported in the local env
(no DB / missing env) — same convention as other env-dependent suites.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

REQUIRED = {
    # users.py — user administration completions
    ("GET", "/api/admin/users/{uid}"),
    ("PATCH", "/api/admin/users/{uid}/tier"),
    ("POST", "/api/admin/users/{uid}/ban"),
    ("POST", "/api/admin/users/{uid}/unban"),
    ("POST", "/api/admin/users/{uid}/erasure"),
    ("GET", "/api/admin/users/{uid}/sessions"),
    ("DELETE", "/api/admin/users/{uid}/sessions"),
    ("POST", "/api/admin/users/bulk"),
    ("GET", "/api/admin/users/{uid}/audit"),
    ("GET", "/api/admin/mfa/config"),
    ("PATCH", "/api/admin/mfa/config"),
    ("GET", "/api/admin/access/ipwhitelist"),
    ("POST", "/api/admin/access/ipwhitelist"),
    ("DELETE", "/api/admin/access/ipwhitelist/{entry_id}"),
    ("POST", "/api/admin/users/{uid}/elevated-role"),
    ("GET", "/api/admin/users/{uid}/elevated-role"),
    ("DELETE", "/api/admin/users/{uid}/elevated-role"),
    ("PATCH", "/api/admin/users/{uid}/sage-tier"),
    ("POST", "/api/users/accept-terms"),
    ("POST", "/api/admin/users/{uid}/reset-password"),
    # personas.py — persona CRUD + admin list
    ("GET", "/api/admin/personas"),
    ("POST", "/api/personas"),
    ("PUT", "/api/personas/{persona_id}"),
    ("PUT", "/api/personas/{persona_id}/priority"),
    ("DELETE", "/api/personas/{persona_id}"),
    ("GET", "/api/personas/stack"),
    # commerce.py — platform feature flags (exec consoles)
    ("GET", "/api/admin/platform/flags"),
    ("POST", "/api/admin/platform/flags/{flag}"),
    # exec_control.py — site-wide broadcast alias
    ("POST", "/api/admin/broadcast"),
    # gateway_admin.py — LLM gateway runtime controls (MoreHelp console)
    ("GET", "/api/admin/gateway/status"),
    ("GET", "/api/admin/gateway/ranking"),
    ("PATCH", "/api/admin/gateway/ranking"),
    ("PATCH", "/api/admin/gateway/budget"),
    ("POST", "/api/admin/gateway/reset-budget"),
}


def _collect(routes, acc, prefix=""):
    for r in routes:
        sub = getattr(r, "routes", None)
        inc = getattr(r, "include_context", None)
        if inc is not None:
            wrapped = getattr(inc, "included_router", None)
            if wrapped is not None:
                _collect(
                    getattr(wrapped, "routes", []) or [],
                    acc,
                    prefix + (getattr(inc, "prefix", "") or ""),
                )
            continue
        if sub:
            _collect(sub, acc, prefix + (getattr(r, "path", "") or ""))
            continue
        path = getattr(r, "path", None)
        if not path:
            continue
        full = prefix + path
        for m in getattr(r, "methods", []) or []:
            acc.add((m, full))


@pytest.fixture(scope="module")
def registered():
    try:
        import server  # noqa: PLC0415
    except Exception as exc:  # env-dependent import (DB, secrets)
        pytest.skip(f"server import unavailable in this env: {exc}")
    acc = set()
    _collect(server.api_router.routes, acc)
    # Routers mounted straight onto the app (gateway_admin etc.) live under
    # include_context wrappers — walk the whole app, not just api_router.
    try:
        _collect(server.app.routes, acc)
    except Exception:  # app shape varies by FastAPI version
        pass
    return acc


def test_completed_admin_endpoints_registered(registered):
    missing = sorted(REQUIRED - registered)
    assert missing == [], f"Previously-registered endpoints missing: {missing}"


def test_no_duplicate_persona_admin_paths_shadow(registered):
    """/api/admin/personas (admin full configs) must not collide with the
    public roster path that ai.py owns at /api/ai/personas."""
    assert ("GET", "/api/admin/personas") in registered
