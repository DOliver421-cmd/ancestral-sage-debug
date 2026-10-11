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

_BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001").rstrip("/")
_API = f"{_BASE}/api"


def login_token(email: str, password: str, attempts: int = 8) -> str:
    """Return a bearer token for `email`, cached for the whole session.

    A 429 (rate limit) is retried after one window, so a suite that
    authenticates each account once stays inside the 20-per-minute-per-IP
    budget. A 423 is not retried: an account lockout lasts 30 minutes and in a
    local/test database means the credentials in the suite do not match the
    seeded account — a real signal, not a timing artefact.
    """
    key = (email, password)
    if key in _TOKEN_CACHE:
        return _TOKEN_CACHE[key]
    last = None
    for _ in range(attempts):
        r = requests.post(
            f"{_API}/auth/login", json={"email": email, "password": password}, timeout=20
        )
        if r.status_code == 200:
            token = r.json()["access_token"]
            _TOKEN_CACHE[key] = token
            return token
        last = f"{r.status_code} {r.text[:200]}"
        if r.status_code == 429:
            time.sleep(62)   # one full rate-limit window
            continue
        break
    raise AssertionError(f"login failed for {email}: {last}")
