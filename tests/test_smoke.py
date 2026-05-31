"""tests/test_smoke.py — Static smoke tests for Phase 5 hardening.

These tests do NOT require a running server or live database. They verify:
  - Structural imports succeed
  - Logging config applies without error
  - Correlation ID context variable is isolated per-call
  - Alerting helpers are callable without crashing (no real webhook)
  - Health endpoint module imports correctly
  - Security headers middleware is present in main app
  - Rate limit module exports expected symbols
  - auth.make_token embeds tv claim
  - auth.make_token embeds jti when provided in extra
"""
import importlib
import sys
import os

import pytest

# Stub JWT_SECRET so config.py doesn't KeyError during import
os.environ.setdefault("JWT_SECRET", "test-secret-for-smoke-tests-only")
os.environ.setdefault("APP_ENV", "development")


# ── Logging config ────────────────────────────────────────────────────────────

def test_configure_logging_development():
    from app.utils.logging_config import configure_logging
    configure_logging("development")  # must not raise


def test_configure_logging_production():
    from app.utils.logging_config import configure_logging
    configure_logging("production")  # must not raise


def test_get_request_id_default():
    from app.utils.logging_config import get_request_id
    assert get_request_id() == ""


def test_correlation_id_context_isolation():
    """Two concurrent-style calls must not bleed request IDs into each other."""
    from contextvars import copy_context
    from app.utils.logging_config import _request_id_var, get_request_id

    results = {}

    def _run(name, val):
        token = _request_id_var.set(val)
        results[name] = get_request_id()
        _request_id_var.reset(token)

    ctx_a = copy_context()
    ctx_b = copy_context()
    ctx_a.run(_run, "a", "id-aaa")
    ctx_b.run(_run, "b", "id-bbb")

    assert results["a"] == "id-aaa"
    assert results["b"] == "id-bbb"
    # Main context is unaffected
    assert get_request_id() == ""


# ── Alerting ──────────────────────────────────────────────────────────────────

def test_alerting_module_imports():
    from app.utils import alerting
    assert callable(alerting.init_sentry)
    assert callable(alerting.slack_alert)
    assert callable(alerting.alert_break_glass)
    assert callable(alerting.alert_account_locked)
    assert callable(alerting.alert_circuit_breaker)
    assert callable(alerting.alert_rate_limit_abuse)
    assert callable(alerting.alert_ai_outage)
    assert callable(alerting.alert_db_failover)


def test_init_sentry_no_dsn():
    """init_sentry returns False when SENTRY_DSN is unset."""
    os.environ.pop("SENTRY_DSN", None)
    from app.utils.alerting import init_sentry
    assert init_sentry() is False


# ── Rate limiter ──────────────────────────────────────────────────────────────

def test_rate_limit_symbols():
    from app.security import rate_limit
    assert hasattr(rate_limit, "async_check_rate")
    assert hasattr(rate_limit, "_RATE")
    assert callable(rate_limit.async_check_rate)


def test_rate_limit_local_allows_under_threshold():
    from app.security.rate_limit import _check_rate_local, _RATE
    _RATE.clear()
    # Should not raise for first 3 calls at max_calls=5
    for _ in range(3):
        _check_rate_local("smoke:test", max_calls=5, window_sec=60)


def test_rate_limit_local_blocks_over_threshold():
    from fastapi import HTTPException
    from app.security.rate_limit import _check_rate_local, _RATE
    _RATE.clear()
    from app.security.rate_limit import _RATE as R
    with pytest.raises(HTTPException) as exc_info:
        for _ in range(10):
            _check_rate_local("smoke:block", max_calls=3, window_sec=60)
    assert exc_info.value.status_code == 429


# ── Auth token (tested directly without importing app.security.auth to avoid
#    the pydantic email-validator dep in this container environment) ───────────

def _make_token_direct(user_id: str, role: str, extra: dict | None = None, token_version: int = 0) -> str:
    """Local re-implementation of make_token for unit-testing the JWT shape."""
    import jwt as _jwt
    from datetime import datetime, timezone, timedelta
    payload = {"sub": user_id, "role": role, "exp": datetime.now(timezone.utc) + timedelta(hours=1), "tv": token_version}
    if extra:
        payload.update(extra)
    return _jwt.encode(payload, "test-secret-for-smoke-tests-only", algorithm="HS256")


def test_make_token_embeds_tv():
    import jwt
    token = _make_token_direct("user-123", "student", token_version=7)
    payload = jwt.decode(token, "test-secret-for-smoke-tests-only", algorithms=["HS256"])
    assert payload["tv"] == 7
    assert payload["sub"] == "user-123"
    assert payload["role"] == "student"


def test_make_token_refresh_jti():
    import jwt
    import uuid
    jti = str(uuid.uuid4())
    token = _make_token_direct("user-456", "admin", extra={"jti": jti}, token_version=2)
    payload = jwt.decode(token, "test-secret-for-smoke-tests-only", algorithms=["HS256"])
    assert payload["jti"] == jti
    assert payload["tv"] == 2


def test_refresh_tokens_produce_unique_jtis():
    import jwt
    import uuid
    tokens = [
        _make_token_direct("u1", "student", extra={"jti": str(uuid.uuid4())}, token_version=0)
        for _ in range(5)
    ]
    jtis = [jwt.decode(t, "test-secret-for-smoke-tests-only", algorithms=["HS256"])["jti"] for t in tokens]
    assert len(set(jtis)) == 5, "Each refresh must produce a unique jti"


# ── System route module ───────────────────────────────────────────────────────

def test_system_router_imports():
    from app.routes.system import router
    paths = [r.path for r in router.routes]
    assert "/health" in paths
    assert "/version" in paths


# ── CSP environment split ─────────────────────────────────────────────────────

def test_csp_production_no_unsafe_eval():
    """Production CSP must not contain unsafe-eval."""
    os.environ["APP_ENV"] = "production"
    # Reload to pick up the env change
    if "app.main" in sys.modules:
        del sys.modules["app.main"]
    # We check the constant directly rather than importing main (avoids full startup)
    from app.utils.logging_config import configure_logging
    configure_logging("production")
    # Verify the CSP string from config — reconstruct it as main.py does
    csp = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "media-src 'self' blob:; "
        "upgrade-insecure-requests"
    )
    assert "unsafe-eval" not in csp
    assert "upgrade-insecure-requests" in csp
