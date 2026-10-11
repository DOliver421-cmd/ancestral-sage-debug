"""
tests/conftest.py — shared test-environment defaults.

Several suites import backend modules at collection time whose module scope
reads configuration from the environment (JWT_SECRET, MONGO_URL, DB_NAME).
When pytest is the runner (rather than the suites' standalone `python3
tests/<file>.py` runners, which set these themselves) those reads raised
KeyError before any test ran.

These are setdefault-only: a real value already present in the environment
(such as the CI/deployment environment) is never overwritten, and no secret
is fabricated — JWT_SECRET here is the same throwaway value the repo's own
test files use when running against a local/test database.

The env keys below are also used by modules under test, so they must be set
before any backend import happens — hence the import order here.
"""
import os

import pytest

os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "testdb_pytest")
# Live-server suites read the backend base URL at module import (repo
# convention: scripts/daytona-dev.sh serves the API on :8001/8080).
os.environ.setdefault("REACT_APP_BACKEND_URL", "http://localhost:8001")

# The executive-seat password the live-server suites authenticate with.  The
# suites previously defaulted TEST_EXEC_PW to "" — an empty password, which
# fails, and whose repeated failures then LOCK the executive account for 30
# minutes, failing every other suite that shares it.  This default matches the
# password `seed_users()` writes for the seat TEST_EXEC_EMAIL defaults to
# (BACKUP_EXEC_EMAIL = youpickeddoliver@gmail.com →
# BACKUP_EXEC_DEFAULT_PASSWORD = NamOshun@WAI2026, server.py:437-444).  Set
# TEST_EXEC_EMAIL/TEST_EXEC_PASSWORD to point at a different seat, or a local
# account, as the deployment requires — never the other way round.
os.environ.setdefault("TEST_EXEC_PW", "NamOshun@WAI2026")

# The live-server suites log in as the LCEWAI demo accounts (admin@lcewai.org,
# instructor@lcewai.org, student@lcewai.org). seed_users() only creates them when
# KEEP_TEST_DEMOS=1 — otherwise it DELETES them, by design, because a live
# platform must not carry demo credentials. Under pytest the suites need them, so
# the flag defaults on (setdefault: an explicit value in the environment wins).
os.environ.setdefault("KEEP_TEST_DEMOS", "1")


def ensure_lcewai_demo_accounts() -> None:
    """Make sure the demo accounts the suites log in as actually exist.

    Cross-suite pollution: a suite exercising user management can delete a
    shared demo account mid-run, and seed_users() only restores it at boot, so
    every suite that runs afterwards fails at login with 401 while nothing is
    wrong with the product. This runs the product's own seeding (which also
    heals role drift and reactivates deactivated demo accounts) against the
    configured database before the suites that need it.
    """
    import asyncio

    from motor.motor_asyncio import AsyncIOMotorClient

    url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "testdb_pytest")
    client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=5000)
    try:
        import server

        original_db, original_client = server.db, getattr(server, "client", None)
        server.db = client[db_name]
        server.client = client
        try:
            asyncio.run(server.seed_users())
        finally:
            server.db, server.client = original_db, original_client
    finally:
        client.close()


@pytest.fixture(scope="session", autouse=True)
def _seed_demo_accounts():
    ensure_lcewai_demo_accounts()


@pytest.fixture(scope="session", autouse=True)
def _pace_login_requests():
    """Keep the suite inside POST /auth/login's rate limit.

    Login is deliberately capped at 20 attempts per minute per IP — a real
    anti-brute-force control the suite must work within, never around. A suite
    that authenticates once per test from one address exceeds it and then fails
    with "Too many requests, slow down" instead of testing anything (three
    tests in test_rbac_matrix failed exactly this way), so login POSTs are paced
    here to 18 per rolling 60-second window — what any real client from one
    address can do. No limit is relaxed and nothing is mocked; the suite simply
    authenticates at a human-plausible rate.
    """
    import threading
    import time as _time

    budget, window = 18, 60.0
    stamps: list = []
    lock = threading.Lock()
    original = requests.Session.request

    def paced(self, method, url, *args, **kwargs):
        if str(method).upper() == "POST" and str(url).endswith("/auth/login"):
            with lock:
                now = _time.time()
                stamps[:] = [s for s in stamps if now - s < window]
                if len(stamps) >= budget:
                    _time.sleep(window - (now - stamps[0]) + 0.5)
                    now = _time.time()
                    stamps[:] = [s for s in stamps if now - s < window]
                stamps.append(now)
        return original(self, method, url, *args, **kwargs)

    requests.Session.request = paced
    try:
        yield
    finally:
        requests.Session.request = original

# NOTE: do NOT add defaults for keys that individual suites set themselves at
# module import (e.g. MORE_ROLLBACK_WEBHOOK_SECRET / RAILWAY_DEPLOYMENT_ID /
# COMMIT_SHA in tests/test_system_rollback*.py).  conftest executes before the
# test module, so a conftest setdefault would shadow the suite's own value and
# break its HMAC/round-trip assertions.

# ── Shared, rate-limit-aware authentication ──────────────────────────────────
# `POST /auth/login` deliberately rate-limits: 5 attempts per minute per email
# and 20 per minute per IP, and repeated failures lock the account.  A suite
# that authenticates per test from one address therefore locks itself out —
# which is how ~150 of these tests were failing with "Too many requests, slow
# down" and 423 lockouts rather than testing anything.
#
# Tokens are cached per (email, password) for the whole session, and a 429/423
# waits out the window instead of failing the test.  The rate limit is a real
# anti-brute-force control and is NOT relaxed: the suite works within it by
# authenticating once per account rather than once per test.
import time

import requests

_TOKEN_CACHE: dict = {}
_BODY_CACHE: dict = {}

_BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
_API = f"{_BASE}/api"


def login_body(email: str, password: str, attempts: int = 8) -> dict:
    """Return the full `/auth/login` response body, cached per session.

    Several suites index the body (`body["access_token"]`, `body["user"]["role"]`)
    and several expect only the token string, so both are kept: this returns the
    whole body and `login_token()` returns just the token from the same cache.

    A 429 (rate limit) is retried after one window, so a suite that
    authenticates each account once stays inside the 20-per-minute-per-IP
    budget. A 423 is not retried: an account lockout lasts 30 minutes and in a
    local/test database means the credentials in the suite do not match the
    seeded account — a real signal, not a timing artefact.
    """
    key = (email, password)
    if key in _BODY_CACHE:
        return dict(_BODY_CACHE[key])
    last = None
    for _ in range(attempts):
        r = requests.post(
            f"{_API}/auth/login", json={"email": email, "password": password}, timeout=20
        )
        if r.status_code == 200:
            body = r.json()
            _BODY_CACHE[key] = dict(body)
            _TOKEN_CACHE[key] = body["access_token"]
            return body
        last = f"{r.status_code} {r.text[:200]}"
        if r.status_code == 429:
            time.sleep(62)   # one full rate-limit window
            continue
        break
    raise AssertionError(f"login failed for {email}: {last}")


def login_token(email: str, password: str, attempts: int = 8) -> str:
    """Return only the bearer token for `email`, cached for the whole session."""
    key = (email, password)
    if key in _TOKEN_CACHE:
        return _TOKEN_CACHE[key]
    return login_body(email, password, attempts)["access_token"]
