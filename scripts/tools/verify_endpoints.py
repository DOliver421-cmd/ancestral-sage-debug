"""
verify_endpoints.py — live endpoint verification for the new Sovereign / puzzle /
partnership routes, run against the REAL FastAPI app via TestClient.

No real services: Claude is mocked (zero API spend), MongoDB is an in-memory fake,
auth is exercised both ways (real 401, role-gated 403, and authorized 200).

Run:  cd backend && python verify_endpoints.py
"""
import os
import sys
import types
from pathlib import Path

BACKEND = str(Path(__file__).resolve().parent)
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "testdb")
os.environ.setdefault("JWT_SECRET", "testsecret")
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test")
ROOT = str(Path(BACKEND).parent)          # repo root — matches PYTHONPATH ".../app"
sys.path.insert(0, ROOT)
sys.path.insert(0, BACKEND)               # backend takes precedence (".../app/backend")

# ── Mock Claude BEFORE importing server (endpoints lazy-import `anthropic`) ──
import anthropic  # noqa: E402


class _Msg:
    def __init__(self, text):
        self.content = [types.SimpleNamespace(text=text)]


class _FakeMessages:
    async def create(self, **kwargs):
        return _Msg("[Sovereign mock reply — Claude not actually called]")


class _FakeAnthropic:
    def __init__(self, *a, **k):
        self.messages = _FakeMessages()


anthropic.AsyncAnthropic = _FakeAnthropic

from verify_new_engines import DB           # in-memory async Mongo fake  # noqa: E402
from puzzles import engine as E             # noqa: E402
import jwt as _jwt                          # noqa: E402
import server                               # noqa: E402
from fastapi.testclient import TestClient   # noqa: E402

server.db = DB()  # swap the global db for the in-memory fake

_exec = lambda: types.SimpleNamespace(id="exec1", role="executive_admin")      # noqa: E731
_student = lambda: types.SimpleNamespace(id="stu1", role="student")            # noqa: E731

client = TestClient(server.app)
API = "/api"
results = []


def check(name, cond):
    results.append(bool(cond))
    print(("PASS " if cond else "FAIL ") + name)


# 1. Puzzle (anonymous view)
r = client.get(f"{API}/puzzles/next")
j = r.json()
check("GET /puzzles/next anon -> 200", r.status_code == 200)
check("puzzle returned, answer NOT leaked", bool(j.get("puzzle")) and "answers" not in j.get("puzzle", {}))
check("anon flagged requires_login_to_earn", j.get("requires_login_to_earn") is True)
pid = j["puzzle"]["id"]

# 2. Puzzle answer — logged-in (real token decoded by _optional_user_id) earns points
tok = _jwt.encode({"sub": "u1", "role": "student"}, server.JWT_SECRET, algorithm=server.JWT_ALGO)
ans = E._by_id(pid)["answers"][0]
r = client.post(f"{API}/puzzles/answer", json={"puzzle_id": pid, "answer": ans},
                headers={"Authorization": f"Bearer {tok}"})
jr = r.json()
check("POST /puzzles/answer logged-in -> 200", r.status_code == 200)
check("correct answer awards points", jr.get("correct") and jr.get("points_awarded", 0) > 0)

# 3. Puzzle answer — anonymous correct earns nothing
r = client.post(f"{API}/puzzles/answer", json={"puzzle_id": "p2", "answer": "piano"})
jr = r.json()
check("anon correct earns 0 points", jr.get("correct") and jr.get("points_awarded") == 0)

# 4. Sovereign chat — no auth -> 401
r = client.post(f"{API}/sovereign/chat", json={"message": "hi"})
check("POST /sovereign/chat no-auth -> 401", r.status_code == 401)

# 5. Sovereign chat — non-exec (student) -> 403
server.app.dependency_overrides[server.current_user] = _student
r = client.post(f"{API}/sovereign/chat", json={"message": "hi"})
check("sovereign chat student -> 403 (exec-only)", r.status_code == 403)

# 6. Sovereign chat — exec -> 200 with mocked reply
server.app.dependency_overrides[server.current_user] = _exec
r = client.post(f"{API}/sovereign/chat", json={"message": "Find me an HBCU residency."})
check("sovereign chat exec -> 200", r.status_code == 200)
check("sovereign returns a reply", "reply" in r.json())

# 7. Sovereign memory add / list / clear (exec)
r = client.post(f"{API}/sovereign/memory", json={"content": "Prefers HBCU bookings.", "kind": "preference"})
check("memory add saved", r.status_code == 200 and r.json().get("saved") is True)
r = client.get(f"{API}/sovereign/memory")
check("memory list reflects it", "HBCU" in (r.json().get("memory") or ""))
r = client.delete(f"{API}/sovereign/memory")
check("memory clear -> 200", r.status_code == 200)

# 8. Partnership status (exec via current_user)
r = client.get(f"{API}/partnership/status")
check("GET /partnership/status -> 200 + tier", r.status_code == 200 and "tier" in r.json())

server.app.dependency_overrides.clear()

ok = all(results)
print(f"\nENDPOINT VERIFICATION: {sum(results)}/{len(results)} checks  ->  " +
      ("ALL PASS" if ok else "FAILURES PRESENT"))
sys.exit(0 if ok else 1)
