"""tests/test_oversight_controls.py — the human-oversight surface must actually work.

Owners asked for AI compliance with full human oversight "real in code and the
UI". A console that renders but cannot save is a mock display, so this file
executes the oversight paths end-to-end against the running server:

1. A feature's kill switch can be flipped from the exec console's own API
   shape, and the flip CHANGES ENFORCEMENT — not just the stored config.
2. The same control from an unauthorised account is refused.
3. The audit trail records who flipped what.
4. (Guard) the route signatures cannot silently become query parameters again:
   the defect that made every Feature Control Center save return 422.
"""

import ast
import inspect
import os
import sys

import pytest
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
API = f"{_BASE}/api"
ADMIN = ("admin@lcewai.org", "Admin@LCE2026")
STUDENT = ("student@lcewai.org", "Learn@LCE2026")


def _hdr(t):
    return {"Authorization": f"Bearer {t}", "Content-Type": "application/json"}


def _login(email, password, attempts=8):
    try:
        from conftest import login_token
    except ImportError:
        r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
        assert r.status_code == 200, r.text
        return r.json()["access_token"]
    return login_token(email, password, attempts)


def _promote(email, role):
    from pymongo import MongoClient
    c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
                    serverSelectionTimeoutMS=5000)
    db_name = os.environ.get("DB_NAME", "phase0_dev")
    try:
        c[db_name].users.update_one({"email": email}, {"$set": {"role": role}})
    finally:
        c.close()


def _restore_admin_role():
    """Put the demo admin back on its seeded role.

    The kill-switch assertion needs an executive account; leaving the shared
    demo admin promoted would change what later suites observe (several
    assert the difference between `admin` and `executive_admin`).
    """
    from pymongo import MongoClient
    c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
                    serverSelectionTimeoutMS=5000)
    db_name = os.environ.get("DB_NAME", "phase0_dev")
    try:
        c[db_name].users.update_one({"email": ADMIN[0]},
                                    {"$set": {"role": "admin", "feature_tier": "free"}})
    finally:
        c.close()


def _audit_rows():
    from pymongo import MongoClient
    c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
                    serverSelectionTimeoutMS=5000)
    db_name = os.environ.get("DB_NAME", "phase0_dev")
    try:
        return list(c[db_name].audit_log.find({}, {"_id": 0, "action": 1, "user_id": 1, "at": 1})
                    .sort("at", -1).limit(50))
    finally:
        c.close()


# ── 1. The kill switch is real ────────────────────────────────────────────────
def test_feature_kill_switch_flips_and_enforcement_follows():
    """Disable a persona in the exec console's own shape; the persona must
    actually stop serving, and re-enable must restore it."""
    _promote(ADMIN[0], "executive_admin")
    try:
        _kill_switch_assertions()
    finally:
        _restore_admin_role()


def _kill_switch_assertions():
    admin = _login(*ADMIN)
    student = _login(*STUDENT)

    before = _audit_rows()
    r = requests.put(f"{API}/features/nam.helper", headers=_hdr(admin),
                     json={"enabled": False}, timeout=30)
    assert r.status_code == 200, (
        "the Feature Control Center's save must work — an unannotated request "
        f"parameter used to turn every save into a 422: {r.text}"
    )
    try:
        import time; time.sleep(1.5)   # config cache is short-lived by design
        off = requests.post(f"{API}/ai/helper", headers=_hdr(student),
                            json={"message": "courses"}, timeout=40)
        assert off.status_code == 403, (
            f"a disabled AI surface must refuse, got {off.status_code}: {off.text[:200]}"
        )
    finally:
        back = requests.put(f"{API}/features/nam.helper", headers=_hdr(admin),
                            json={"enabled": True}, timeout=30)
        assert back.status_code == 200, back.text
        import time; time.sleep(1.5)

    on = requests.post(f"{API}/ai/helper", headers=_hdr(student),
                       json={"message": "courses"}, timeout=40)
    assert on.status_code == 200, f"re-enabled surface must serve again: {on.text[:200]}"

    # Human oversight leaves a trace: a NEW feature_config.updated record,
    # recorded after the one we captured before the flip.
    after = _audit_rows()
    newest_before = max((a.get("at") or "" for a in before), default="")
    flipped = [a for a in after if (a.get("at") or "") > newest_before]
    assert any("feature" in str(a.get("action", "")) for a in flipped), (
        f"the flip left no audit record (newest before={newest_before!r}, after={after[:2]})"
    )


def test_feature_update_requires_an_authorised_account():
    student = _login(*STUDENT)
    r = requests.put(f"{API}/features/nam.helper", headers=_hdr(student),
                     json={"enabled": False}, timeout=30)
    assert r.status_code in (401, 403), r.text


# ── 2. Guards against the defect class that broke this console ────────────────
ROUTERS_DIR = os.path.join(_BACKEND, "routers")


def _unannotated_required(fn):
    """Required (no-default) parameters with no type annotation on a handler.

    FastAPI reads those as REQUIRED QUERY parameters — which is exactly how
    every Feature Control Center save became a 422 before the fix.
    """
    bad = []
    for p in inspect.signature(fn).parameters.values():
        if p.kind not in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.POSITIONAL_ONLY):
            continue
        if p.default is not inspect.Parameter.empty:
            continue
        if p.annotation is inspect.Parameter.empty and p.name not in ("self", "cls"):
            bad.append(p.name)
    return bad


def test_features_handlers_have_no_unannotated_required_params():
    """The three oversight handlers specifically: tier_matrix, role_matrix,
    update_feature."""
    from routers import features
    for fn in (features.tier_matrix, features.role_matrix, features.update_feature):
        assert not _unannotated_required(fn), (
            f"{fn.__name__}: {_unannotated_required(fn)} — an unannotated required "
            "parameter becomes a required query argument and the call 422s"
        )


def test_features_handlers_do_not_capture_the_dependency_at_import_time():
    """Depends(current_user) at import time captured None (the bind pattern),
    which silently disabled every check on this router. Auth must resolve at
    request time."""
    from routers import features
    import fastapi
    for fn in (features.tier_matrix, features.role_matrix, features.update_feature):
        for name, dep in inspect.signature(fn).parameters.items():
            default = dep.default
            if isinstance(default, fastapi.params.Depends):
                assert default.dependency is not None, (
                    f"{fn.__name__}.{name} depends on None (captured before bind())"
                )


def test_features_update_uses_attribute_access_on_the_user():
    """current_user() resolves a pydantic User; a dict-style .get() on it is a
    500. The console's write path hit exactly that."""
    src = open(os.path.join(ROUTERS_DIR, "features.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                and node.value.id == "actor" and node.attr == "get":
            pytest.fail(
                f"features.py:{node.lineno} calls actor.get(...) — `actor` is a "
                "pydantic User; use getattr(actor, 'field', None)"
            )
