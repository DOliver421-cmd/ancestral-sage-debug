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

# NOTE: do NOT add defaults for keys that individual suites set themselves at
# module import (e.g. MORE_ROLLBACK_WEBHOOK_SECRET / RAILWAY_DEPLOYMENT_ID /
# COMMIT_SHA in tests/test_system_rollback*.py).  conftest executes before the
# test module, so a conftest setdefault would shadow the suite's own value and
# break its HMAC/round-trip assertions.
