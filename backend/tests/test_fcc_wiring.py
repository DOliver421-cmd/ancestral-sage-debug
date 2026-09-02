"""tests/test_fcc_wiring.py — Feature Control Center end-to-end wiring.

Proves the Critical-Directive contract for /admin/features:

  1. update_feature() is a REAL database write — it raises 503 instead of
     returning a false-positive "ok" when the control store is unavailable,
     writes an audit trail, and returns the stored record (normalized) so the
     UI can never display a client-side guess as a server confirmation.
  2. The enforcement middleware (security/fcc_middleware.py) is registered on
     the app and turns FCC records / platform flags / per-user overrides into
     403/503 verdicts on live request paths.
  3. §7A funding: check_user_feature_access enforces customer_access_allowed,
     and the gateway never spends platform tokens for non-staff callers.

Run:  cd backend && python3 tests/test_fcc_wiring.py
"""

import asyncio
import os
import sys
import types
from datetime import datetime, timezone

# Same env convention as scripts/tools/verify_endpoints.py — the test harness
# never touches a real deployment database.
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "testdb_fcc_wiring")
os.environ.setdefault("JWT_SECRET", "testsecret")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import jwt as _jwt  # noqa: E402

PASS = FAIL = 0


def ok(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}")


# ── In-memory async Mongo fake (mirrors scripts/tools/verify_new_engines.py) ─
class Coll:
    def __init__(self):
        self.docs = []
        self.indexes = []

    async def create_index(self, keys, unique=False, **kw):
        self.indexes.append((keys, unique))
        return "idx"

    async def find_one(self, filt, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in (filt or {}).items()):
                if projection is None:
                    return dict(d)
                if all(not v for v in projection.values()):
                    # Exclusion-only projection ({'x': 0}): keep everything
                    # except the excluded fields (real Mongo semantics).
                    return {k: v for k, v in d.items() if k not in projection}
                return {k: v for k, v in d.items() if k in projection}
        return None

    def find(self, filt=None, projection=None):
        filt = filt or {}
        return _Cursor([dict(d) for d in self.docs if all(d.get(k) == v for k, v in filt.items())])

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return types.SimpleNamespace(inserted_id=len(self.docs))

    async def update_one(self, filt, update, upsert=False):
        target = next((d for d in self.docs if all(d.get(k) == v for k, v in filt.items())), None)
        inserted = False
        if target is None:
            if not upsert:
                return types.SimpleNamespace(acknowledged=True, modified_count=0)
            target = dict(filt)
            self.docs.append(target)
            inserted = True
        if update.get("$setOnInsert") and inserted:
            target.update(update["$setOnInsert"])
        if update.get("$set"):
            target.update(update["$set"])
        if update.get("$inc"):
            for k, v in update["$inc"].items():
                target[k] = target.get(k, 0) + v
        return types.SimpleNamespace(
            acknowledged=True, modified_count=0 if inserted else 1,
            upserted_id=len(self.docs) if inserted else None,
        )


class _Cursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def sort(self, key, direction=1):
        self._docs.sort(key=lambda d: d.get(key), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length=None):
        return self._docs if length is None else self._docs[:length]


class DB:
    def __init__(self):
        self.c = {}

    def __getitem__(self, name):
        return self.c.setdefault(name, Coll())

    def __getattr__(self, name):
        return self.__getitem__(name)


class FakeUser(types.SimpleNamespace):
    """Mirrors server.User fields used by feature_control."""
    def __init__(self, **kw):
        defaults = {"id": "u1", "role": "student", "feature_tier": "free",
                    "is_active": True, "email": "u1@example.com"}
        defaults.update(kw)
        super().__init__(**defaults)


# ═══════════════════════════ 1. update_feature ═══════════════════════════════
async def test_update_feature_writes_and_audits():
    import server
    from routers import features as F

    db = DB()
    actor = {"id": "admin1", "role": "admin"}
    F.db = db
    F.current_user = None

    # Redirect the update endpoint's audit dependency onto the in-memory store
    # (update_feature imports `server.audit` lazily per call, so replacing the
    # module attribute is enough).
    real_audit = server.audit

    def fake_audit(actor_id, action, target=None, meta=None):
        return db.audit_log.insert_one({
            "actor_id": actor_id, "action": action, "target": target,
            "meta": meta or {}, "at": datetime.now(timezone.utc).isoformat(),
        })

    server.audit = fake_audit
    try:
        r = await F.update_feature(
            "nam.chat",
            {"enabled": False, "allowed_tiers": ["creator", "free", "bogus"],
             "allowed_roles": ["student", "not_a_role"], "cost_bearing": True},
            request=object(),
            actor=actor,
        )
        ok("update_feature returns saved=True", r.get("saved") is True)
        doc = db.feature_configs.docs[0]
        ok("enabled persisted false", doc.get("enabled") is False)
        ok("legacy tier normalized (creator->member), bogus dropped",
           doc.get("allowed_tiers") == ["member", "free"])
        ok("unknown role dropped from stored config", doc.get("allowed_roles") == ["student"])
        ok("audit row written for feature config change",
           any(a.get("action") == "feature_config.updated" and a.get("target") == "nam.chat"
               for a in db.audit_log.docs))
        ok("stored record returned to the UI", r.get("stored", {}).get("enabled") is False)

        # Stores the effective config through the same read path the admin UI
        # uses — the UI always renders the server's truth after a save.
        eff = await F.get_feature_config_async("nam.chat")
        ok("read-back sees the persisted toggle", eff.get("enabled") is False)

        # Unknown feature -> 404.
        try:
            await F.update_feature("does.not.exist", {"enabled": False}, request=object(), actor=actor)
            ok("unknown feature -> 404", False)
        except Exception as e:
            ok("unknown feature -> 404", getattr(e, "status_code", None) == 404)

        # Non-admin actor -> 403.
        try:
            await F.update_feature("nam.chat", {"enabled": True}, request=object(),
                                   actor={"id": "stu1", "role": "student"})
            ok("student actor -> 403", False)
        except Exception as e:
            ok("student actor -> 403", getattr(e, "status_code", None) == 403)
    finally:
        server.audit = real_audit
        F.db = None
        F.current_user = None


async def test_update_feature_never_false_positives():
    from routers import features as F

    # db not bound: MUST fail loudly, never return {"ok": True}.
    F.db = None
    F.current_user = None
    try:
        await F.update_feature("nam.chat", {"enabled": False}, request=object(),
                               actor={"id": "admin1", "role": "admin"})
        ok("unbound db -> 503 (no false-positive ok)", False)
    except Exception as e:
        ok("unbound db -> 503 (no false-positive ok)", getattr(e, "status_code", None) == 503)

    # A dying store must fail loudly too.
    class DeadColl:
        async def update_one(self, *a, **k):
            raise RuntimeError("connection lost")

    class DeadDB:
        feature_configs = DeadColl()

    F.db = DeadDB()
    try:
        await F.update_feature("nam.chat", {"enabled": False}, request=object(),
                               actor={"id": "admin1", "role": "admin"})
        ok("failed store write -> 503", False)
    except Exception as e:
        ok("failed store write -> 503", getattr(e, "status_code", None) == 503)
    F.db = None


# ═══ 2. Enforcement middleware (security/fcc_middleware.py) on the app ═══════
def test_middleware_registered_on_app():
    """The FCC gate runs on REAL requests through the live app tree."""
    import server
    from fastapi.testclient import TestClient

    names = [getattr(m.cls, "__name__", str(m.cls)) for m in server.app.user_middleware]
    ok("three http middleware layers registered (headers, logging, FCC gate)",
       sum(n == "BaseHTTPMiddleware" for n in names) >= 3)

    real_db, real_startup = server.db, server._startup_impl_done
    server.db = DB()
    server._startup_impl_done = True
    try:
        client = TestClient(server.app)
        # Open config: gate must let the request through to the handler.
        r = client.get("/api/ai/chat")
        ok("gate passes an open config through to the handler", r.status_code not in (403, 503))
        # Exec disables the ai_chat platform flag -> gate 403s before the handler.
        server.db.platform_flags.docs.append(
            {"_id": "flags", "flags": {"ai_chat": {"enabled": False}}}
        )
        r = client.get("/api/ai/chat")
        ok("gate returns 403 per request when the ai_chat flag is disabled", r.status_code == 403)
        # A real token + FCC enabled=false -> per-user 403 on the request path.
        server.db.platform_flags.docs = []
        server.db.feature_configs.docs.append({"feature_id": "nam.chat", "enabled": False})
        server.db.users.docs.append(
            {"id": "u1", "role": "student", "feature_tier": "free", "is_active": True,
             "email": "u1@example.com", "full_name": "Test Student"}
        )
        tok = _jwt.encode({"sub": "u1", "role": "student"}, server.JWT_SECRET,
                          algorithm=server.JWT_ALGO)
        r = client.get("/api/ai/chat", headers={"Authorization": f"Bearer {tok}"})
        ok("gate returns 403 per request when the FCC record is disabled (got %s)" % r.status_code,
           r.status_code == 403)
    finally:
        server.db = real_db
        server._startup_impl_done = real_startup


async def test_middleware_verdicts():
    import server
    from security.fcc_middleware import fcc_enforce_request

    db = DB()

    # Public gate map is exempt — signed-out nav must keep working.
    v = await fcc_enforce_request(db, "/api/features/gate-map", "", server.JWT_SECRET, server.JWT_ALGO, FakeUser)
    ok("gate-map exempt from enforcement", v is None)

    # Unmapped public path passes.
    v = await fcc_enforce_request(db, "/api/media/products", "", server.JWT_SECRET, server.JWT_ALGO, FakeUser)
    ok("unmapped public path passes", v is None)

    # Exec-disabled platform flag -> 403 before any per-user logic.
    db.platform_flags.docs.append({"_id": "flags", "flags": {"ai_chat": {"enabled": False}}})
    v = await fcc_enforce_request(db, "/api/ai/chat", "", server.JWT_SECRET, server.JWT_ALGO, FakeUser)
    ok("disabled ai_chat platform flag -> 403", v is not None and v[0] == 403)

    # Enabled flag + FCC record disabled -> per-user 403 with a real token.
    db.platform_flags.docs = [{"_id": "flags", "flags": {"ai_chat": {"enabled": True}}}]
    db.feature_configs.docs.append({"feature_id": "nam.chat", "enabled": False})
    db.users.docs.append({"id": "u1", "role": "student", "feature_tier": "free", "is_active": True})
    tok = _jwt.encode({"sub": "u1", "role": "student"}, server.JWT_SECRET, algorithm=server.JWT_ALGO)
    v = await fcc_enforce_request(db, "/api/ai/chat", f"Bearer {tok}", server.JWT_SECRET, server.JWT_ALGO, FakeUser)
    ok("FCC record enabled=false -> 403 for the caller", v is not None and v[0] == 403)

    # Unverifiable token is left to the handler (401 by the auth dependency).
    v = await fcc_enforce_request(db, "/api/ai/chat", "Bearer not-a-jwt", server.JWT_SECRET, server.JWT_ALGO, FakeUser)
    ok("malformed token passes middleware", v is None)

    # A valid token for an existing user whose document cannot be mapped to
    # the user model fails CLOSED (503) — never a silent pass.
    db.feature_configs.docs = []
    db.users.docs = [{"id": "u9", "is_active": True}]  # missing email/full_name
    tok9 = _jwt.encode({"sub": "u9", "role": "student"}, server.JWT_SECRET, algorithm=server.JWT_ALGO)
    # Use the strict server.User model so document-mapping genuinely fails.
    v = await fcc_enforce_request(db, "/api/ai/chat", f"Bearer {tok9}", server.JWT_SECRET, server.JWT_ALGO, server.User)
    ok("unmappable identity fails closed (503, never silent pass)", v is not None and v[0] == 503)


# ═══════════════ 3. §7A customer-access + funding enforcement ════════════════
async def test_customer_access_allowed_enforced():
    from security.feature_control import check_user_feature_access

    db = DB()
    # FCC override marks the feature staff-only (customer_access_allowed=false)
    # while the role list still includes student — the classification must win.
    db.feature_configs.docs.append({
        "feature_id": "nam.jamil",
        "customer_access_allowed": False,
        "enabled": True,
        "allowed_roles": ["student", "admin", "executive_admin"],
    })

    student = FakeUser(id="u1", role="student")
    admin = FakeUser(id="u2", role="admin")
    execu = FakeUser(id="u3", role="executive_admin")

    a, d = await check_user_feature_access(db, student, "/api/jamil/x")
    ok("student blocked from staff-only feature", a == "block" and "staff" in d)
    a, d = await check_user_feature_access(db, admin, "/api/jamil/x")
    ok("admin allowed staff-only feature", a == "pass")
    a, d = await check_user_feature_access(db, execu, "/api/jamil/x")
    ok("executive_admin allowed staff-only feature", a == "pass")

    # Unverifiable store -> unavailable (503), never an allowance.
    class BoomColl:
        async def find_one(self, *a, **k):
            raise RuntimeError("db down")

    class BoomDB:
        def __getattr__(self, name):
            return BoomColl()

    a, d = await check_user_feature_access(BoomDB(), student, "/api/ai/chat")
    ok("policy store failure -> unavailable (fail-closed)", a == "unavailable")


async def test_gateway_never_funds_non_staff():
    import deps
    from ai import llm_gateway as G

    class FakeUsers:
        def __init__(self, role):
            self.role = role

        async def find_one(self, filt, proj=None):
            if not self.role:
                return None
            return {"id": "u1", "role": self.role, "feature_tier": "free", "byok_enabled": False}

    class FakeDb:
        def __init__(self, role):
            self.users = FakeUsers(role)

    async def run(role):
        deps.set_db(FakeDb(role))
        r = await G.call_llm(
            system="test",
            messages=[{"role": "user", "content": "how do I reset my password"}],
            persona_label="test",
            user_id="u1",
        )
        return r

    # Simulate a world where platform keys EXIST so a pre-§7A gateway would
    # actually spend tokens for a student's request.
    saved_pool = G._PROVIDER_KEY_POOLS["groq"]
    saved_call = G._oai_compat_call
    G._PROVIDER_KEY_POOLS["groq"] = G.KeyPool(["sk-simulated-platform-key"])

    async def _injected(*a, **k):
        return {"text": "PLATFORM FUNDED REPLY", "in_tok": 1, "out_tok": 1}

    G._oai_compat_call = _injected
    try:
        r = await run("student")
        ok("student never receives platform-funded AI (KB served instead)",
           r.get("provider") == "kb_fallback" and "PLATFORM" not in r.get("text", ""))
        r = await run("support_staff")
        ok("support_staff never receives platform-funded AI",
           r.get("provider") == "kb_fallback")
        r = await run(None)
        ok("unverifiable staff status fails closed to KB",
           r.get("provider") == "kb_fallback")
        r = await run("admin")
        ok("admin reaches the platform chain",
           r.get("provider") != "kb_fallback" and "PLATFORM" in r.get("text", ""))
        r = await run("executive_admin")
        ok("executive_admin reaches the platform chain",
           r.get("provider") != "kb_fallback" and "PLATFORM" in r.get("text", ""))
    finally:
        G._oai_compat_call = saved_call
        G._PROVIDER_KEY_POOLS["groq"] = saved_pool


def main():
    import server  # noqa: F401  (import once: registers middleware + routers)

    asyncio.run(test_update_feature_writes_and_audits())
    asyncio.run(test_update_feature_never_false_positives())
    test_middleware_registered_on_app()
    asyncio.run(test_middleware_verdicts())
    asyncio.run(test_customer_access_allowed_enforced())
    asyncio.run(test_gateway_never_funds_non_staff())

    print(f"\nFCC WIRING: {PASS} passed, {FAIL} failed -> {'ALL PASS' if FAIL == 0 else 'FAILURES PRESENT'}")
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()