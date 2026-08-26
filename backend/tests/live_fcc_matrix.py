"""Live HTTP access-matrix verification for Phase 16 FCC enforcement.

Requires the backend server running on :8000 with a reachable database
(MONGO_URL set in the environment).  Seeds clearly-marked test users,
verifies the matrix, and cleans up after itself.  Run from backend/:

    python3 tests/live_fcc_matrix.py
"""
import json
import sys
import urllib.request
import urllib.error

sys.path.insert(0, ".")

BASE = "http://localhost:8000/api"
TEST_IDS = ["fcc-test-student", "fcc-test-instructor", "fcc-test-admin", "fcc-test-exec"]

PASS = []
FAIL = []


def check(name, got, expected):
    ok = got == expected
    (PASS if ok else FAIL).append(f"{name}: got {got}, expected {expected}")
    print(("PASS " if ok else "FAIL ") + f"{name}: {got}")


def http(method, path, token=None, body=None, form=None):
    url = BASE + path
    data = None
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, resp.read().decode()[:200]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]


def main():
    import os
    import asyncio
    import urllib.parse
    import server  # noqa: F401  (binds db, JWT_SECRET from the real env)
    from motor.motor_asyncio import AsyncIOMotorClient

    async def seed():
        mongo_url = os.environ.get("MONGO_URL")
        if not mongo_url:
            print("BLOCKED: MONGO_URL not set — cannot run live matrix")
            return None
        client = AsyncIOMotorClient(mongo_url)
        db = client[server.db.name] if server.db is not None else client["wai"]
        users = [
            {"id": "fcc-test-student", "email": "fcc-test-student@example.com", "full_name": "FCC Test Student",
             "role": "student", "feature_tier": "free", "is_active": True, "token_version": 0},
            {"id": "fcc-test-instructor", "email": "fcc-test-instructor@example.com", "full_name": "FCC Test Instructor",
             "role": "instructor", "feature_tier": "free", "is_active": True, "token_version": 0},
            {"id": "fcc-test-admin", "email": "fcc-test-admin@example.com", "full_name": "FCC Test Admin",
             "role": "admin", "feature_tier": "pro", "is_active": True, "token_version": 0},
            {"id": "fcc-test-exec", "email": "fcc-test-exec@example.com", "full_name": "FCC Test Exec",
             "role": "executive_admin", "feature_tier": "executive", "is_active": True, "token_version": 0},
        ]
        for u in users:
            await db.users.replace_one({"id": u["id"]}, u, upsert=True)
        # Ensure no stale override from a previous run.
        await db.feature_configs.delete_many({"feature_id": "nam.helper"})
        return db

    async def cleanup(db):
        await db.users.delete_many({"id": {"$in": TEST_IDS}})
        await db.feature_configs.delete_many({"feature_id": "nam.helper"})
        print("\ncleanup: test users + nam.helper override removed")

    db = asyncio.run(seed())
    if db is None:
        sys.exit(2)

    student = server.make_token("fcc-test-student", "student")
    admin = server.make_token("fcc-test-admin", "admin")
    exec_tok = server.make_token("fcc-test-exec", "executive_admin")

    # ── JAMIL (internal_only, admin+) ────────────────────────────────────────
    st, _ = http("POST", "/jamil/chat", token=student, form={"message": ""})
    check("jamil: student → blocked (403)", st, 403)
    st, _ = http("POST", "/jamil/chat", token=admin, form={"message": ""})
    check("jamil: admin → passes FCC (route 400 empty msg)", st, 400)
    st, _ = http("POST", "/jamil/chat", token=exec_tok, form={"message": ""})
    check("jamil: exec → passes FCC (route 400 empty msg)", st, 400)

    # ── ARENA (internal_only, executive_admin ONLY) ─────────────────────────
    st, _ = http("POST", "/competition/task", token=student, body={})
    check("arena: student → blocked (403)", st, 403)
    st, _ = http("POST", "/competition/task", token=admin, body={})
    check("arena: admin → blocked by FCC (403)", st, 403)
    st, _ = http("POST", "/competition/task", token=exec_tok, body={})
    check("arena: exec → passes FCC (422/400 from handler)", st in (400, 422), True)

    # ── AI helper (NOT internal — open to students unless overridden) ───────
    st, _ = http("POST", "/ai/helper", token=student, body={})
    check("helper: student → passes FCC (non-403)", st != 403, True)
    st, _ = http("POST", "/ai/helper", token=admin, body={})
    check("helper: admin → passes FCC (non-403)", st != 403, True)

    # ── ORCHESTRATOR (internal, admin+) ─────────────────────────────────────
    st, _ = http("POST", "/ai/orchestrator", token=student, body={"message": ""})
    check("orchestrator: student → blocked (403)", st, 403)

    # ── FCC admin surface: only admin/exec may read it ──────────────────────
    st, _ = http("GET", "/features", token=student)
    check("features: student → 403", st, 403)
    st, _ = http("GET", "/features", token=exec_tok)
    check("features: exec → 200", st, 200)

    # ── FCC toggle binds at the API (enabled=false blocks everyone) ─────────
    st, _ = http("PUT", "/features/nam.helper", token=exec_tok,
                 body={"enabled": False})
    check("fcc disable helper: exec PUT → 200", st, 200)
    st, _ = http("POST", "/ai/helper", token=student, body={})
    check("helper disabled: student → blocked (403)", st, 403)
    st, _ = http("POST", "/ai/helper", token=admin, body={})
    check("helper disabled: admin → blocked (403)", st, 403)
    # Gate map reflects the toggle for the frontend nav.
    st, body = http("GET", "/exec/control/access/public")
    pages = json.loads(body).get("pages", {})
    check("gate map: helper page disabled", pages.get("helper", {}).get("enabled"), False)
    # Re-enable.
    st, _ = http("PUT", "/features/nam.helper", token=exec_tok,
                 body={"enabled": True})
    check("fcc re-enable helper: exec PUT → 200", st, 200)
    st, _ = http("POST", "/ai/helper", token=student, body={})
    check("helper re-enabled: student passes FCC (non-403)", st != 403, True)

    # ── FCC role override binds (allowed_roles=["admin"]) ───────────────────
    st, _ = http("PUT", "/features/nam.helper", token=exec_tok,
                 body={"allowed_roles": ["admin"]})
    check("fcc roles override: exec PUT → 200", st, 200)
    st, _ = http("POST", "/ai/helper", token=student, body={})
    check("roles override: student → blocked (403)", st, 403)
    st, _ = http("POST", "/ai/helper", token=exec_tok, body={})
    check("roles override: exec → passes (rank >= admin)", st != 403, True)

    # ── Cleanup ─────────────────────────────────────────────────────────────
    asyncio.run(cleanup(db))

    print(f"\n=== LIVE MATRIX: {len(PASS)} passed, {len(FAIL)} failed ===")
    for f in FAIL:
        print("  " + f)
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
