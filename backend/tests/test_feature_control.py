"""tests/test_feature_control.py — enforcement for the exec panel's controls.

The exec panel writes platform_flags / page_access but nothing used to read
them back.  feature_control.py is the read side.  These tests pin the
SAFE-DEFAULT contract: absent config == allow; only an explicit
``enabled: false`` blocks requests.

Run:  cd backend && python3 tests/test_feature_control.py   (or pytest)
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from types import SimpleNamespace

from security.feature_control import (  # noqa: E402
    FEATURE_API_PATHS,
    FEATURE_MIN_TIER,
    PAGE_API_PATHS,
    TIER_RANK,
    check_request_config,
    check_user_feature_access,
    feature_for_path,
    load_feature_tier_requirements,
    page_access_enabled,
    platform_flag_enabled,
)


# ── Helpers: safe defaults ─────────────────────────────────────────────────────
def test_platform_flag_defaults_to_enabled():
    assert platform_flag_enabled(None, "ai_chat") is True
    assert platform_flag_enabled({}, "ai_chat") is True
    assert platform_flag_enabled({"flags": {}}, "ai_chat") is True
    assert platform_flag_enabled({"flags": {"ai_chat": {}}}, "ai_chat") is True
    assert platform_flag_enabled({"flags": {"ai_chat": {"enabled": True}}}, "ai_chat") is True
    # Only an explicit disable blocks.
    assert platform_flag_enabled({"flags": {"ai_chat": {"enabled": False}}}, "ai_chat") is False


def test_page_access_defaults_to_enabled():
    assert page_access_enabled(None) is True
    assert page_access_enabled({}) is True
    assert page_access_enabled({"enabled": True}) is True
    assert page_access_enabled({"enabled": False}) is False


# ── check_request_config with a fake db ────────────────────────────────────────
class _FakeDB:
    """Minimal async db stub: only db.page_access.find_one is used."""

    def __init__(self, page_docs=None):
        self._pages = page_docs or {}
        self.page_access = self  # db.page_access.find_one(...) resolves here

    async def find_one(self, query, projection=None):
        if "page" in query:
            return self._pages.get(query["page"])
        return None


def _run(path, flags_doc=None, db=None):
    # A supplied flags document is the policy-store fixture for these tests;
    # use a DB stub as well so the independent page-access check can remain
    # available without turning every platform-flag assertion into a 503.
    if db is None and flags_doc is not None:
        db = _FakeDB()
    return asyncio.run(check_request_config(db, path, flags_doc))


def test_absent_config_preserves_defaults_but_missing_policy_store_fails_closed():
    # Missing documents preserve the existing available behavior. A missing
    # policy store is different: the server cannot prove authorization.
    assert _run("/api/ai/chat", db=_FakeDB()) is None
    assert _run("/api/more/posts", db=_FakeDB()) is None
    assert _run("/api/modules", db=_FakeDB()) is None
    assert _run("/api/ai/chat") == (503, "Feature authorization unavailable — request rejected.")


def test_disabled_platform_flag_blocks_mapped_paths_only():
    flags = {"flags": {"ai_chat": {"enabled": False}}}
    result = _run("/api/ai/chat", flags)
    assert result is not None and result[0] == 403
    assert "ai_chat" in result[1]
    # Sibling feature untouched.
    assert _run("/api/more/posts", flags) is None
    # Unmapped / exempt paths untouched even with a flag disabled.
    assert _run("/api/health", flags) is None
    assert _run("/api/auth/login", flags) is None


def test_each_mapped_flag_only_blocks_its_own_paths():
    # The catalog LISTING is its own free-tier feature (curriculum) so the
    # /modules page stays a working central directory; the `courses` flag
    # governs content surfaces (module detail, progress, labs, credentials).
    cases = {
        "ai_chat": ["/api/ai/chat", "/api/ai/history"],
        "posts": ["/api/more/post", "/api/more/posts", "/api/more/need"],
        "curriculum": ["/api/modules"],
        "courses": ["/api/modules/electrical-safety", "/api/progress", "/api/labs", "/api/credentials"],
    }
    for flag, paths in cases.items():
        flags = {"flags": {flag: {"enabled": False}}}
        for p in paths:
            result = _run(p, flags)
            assert result is not None and result[0] == 403, f"{flag} should block {p}"
        for other, other_paths in cases.items():
            if other == flag:
                continue
            for p in other_paths[:1]:
                assert _run(p, flags) is None, f"{flag} must NOT block {other} path {p}"


def test_disabled_page_access_blocks_mapped_api():
    db = _FakeDB(page_docs={"ai": {"enabled": False}})
    result = _run("/api/ai/chat", db=db)
    assert result is not None and result[0] == 403
    # A page that is enabled / absent stays open.
    assert _run("/api/ai/chat", db=_FakeDB(page_docs={"ai": {"enabled": True}})) is None
    assert _run("/api/ai/chat", db=_FakeDB()) is None


def test_db_error_fails_closed():
    class _BrokenDB:
        async def find_one(self, query, projection=None):
            raise RuntimeError("mongo down")

    result = _run("/api/ai/chat", db=_BrokenDB())
    assert result is not None and result[0] == 503


# ── Per-user enforcement (user_feature_overrides + feature_tier) ──────────────
class _UserDB:
    """Fake db with user_feature_overrides + tier_definitions + authz_matrix."""

    def __init__(self, overrides=None, custom_tiers=None, authz=None):
        self._overrides = overrides  # dict: user_id -> doc, or None
        self._tiers = custom_tiers or []
        self._authz = authz  # dict or None (absent = code defaults)
        self.user_feature_overrides = self
        self.tier_definitions = self
        self.authz_matrix = self

    async def find_one(self, query, projection=None):
        if "user_id" in query:
            if self._overrides is None:
                return None
            return self._overrides.get(query["user_id"])
        if query.get("_id") == "matrix":
            return {"requirements": self._authz} if self._authz is not None else None
        return None

    def find(self, query, projection=None):
        return self  # .to_list(n) resolves on the db itself

    async def to_list(self, n):
        return self._tiers


def _u(role="student", feature_tier="free", uid="u1"):
    return SimpleNamespace(id=uid, role=role, feature_tier=feature_tier)


def _check(db, user, path):
    return asyncio.run(check_user_feature_access(db, user, path))


def test_feature_for_path_maps_exact_prefixes():
    assert feature_for_path("/api/ai/chat") == "ai_chat"
    assert feature_for_path("/api/more/posts") == "posts"
    assert feature_for_path("/api/modules/abc") == "courses"
    assert feature_for_path("/api/health") is None
    assert feature_for_path("/api/auth/login") is None


def test_per_user_absent_override_is_pass():
    # No override doc at all -> no verdict -> platform checks decide.
    assert _check(_UserDB(), _u(), "/api/ai/chat") == ("pass", None)
    # A missing policy store is unavailable; a missing user is left for the
    # route's own authentication dependency to reject.
    assert _check(None, _u(), "/api/ai/chat")[0] == "unavailable"
    assert _check(_UserDB(), None, "/api/ai/chat") == ("pass", None)


def test_per_user_flag_revoke_blocks_only_that_user_and_feature():
    ovr = {"u1": {"flags": {"ai_chat": False}}}
    db = _UserDB(overrides=ovr)
    # u1 is revoked from AI.
    action, detail = _check(db, _u(uid="u1"), "/api/ai/chat")
    assert action == "block" and "revoked" in detail
    # A different user is untouched.
    assert _check(db, _u(uid="u2"), "/api/ai/chat") == ("pass", None)
    # The revoke only covers ai_chat, not posts (member tier so the tier gate
    # does not interfere with this assertion).
    assert _check(db, _u(uid="u1", feature_tier="member"), "/api/more/posts") == ("pass", None)


def test_per_user_flag_grant_wins_over_platform_disable():
    # Exec disabled ai_chat platform-wide but explicitly granted it to u1.
    ovr = {"u1": {"flags": {"ai_chat": True}}}
    db = _UserDB(overrides=ovr)
    assert _check(db, _u(uid="u1"), "/api/ai/chat") == ("allow", None)
    # A user with no grant still gets the platform verdict from the caller.
    assert _check(db, _u(uid="u2"), "/api/ai/chat") == ("pass", None)


def test_ai_access_override_all_false_blocks_ai():
    ovr = {"u1": {"ai_access_override": {"all": False}}}
    db = _UserDB(overrides=ovr)
    action, detail = _check(db, _u(uid="u1"), "/api/ai/chat")
    assert action == "block" and "AI suite" in detail
    # Not blocked on non-AI surfaces (member tier so posts passes its gate).
    assert _check(db, _u(uid="u1", feature_tier="member"), "/api/more/posts") == ("pass", None)
    # Enabled override is a no-op (no explicit grant needed).
    db2 = _UserDB(overrides={"u1": {"ai_access_override": {"all": True}}})
    assert _check(db2, _u(uid="u1"), "/api/ai/chat") == ("pass", None)


def test_tier_requirements_match_frontend_contract():
    # posts requires member; free user blocked.
    action, detail = _check(_UserDB(), _u(feature_tier="free"), "/api/more/posts")
    assert action == "block" and "Member plan" in detail
    # member user passes posts.
    assert _check(_UserDB(), _u(feature_tier="member"), "/api/more/posts") == ("pass", None)
    # courses requires plus; member blocked, plus passes.
    assert _check(_UserDB(), _u(feature_tier="member"), "/api/modules/x")[0] == "block"
    assert _check(_UserDB(), _u(feature_tier="plus"), "/api/modules/x") == ("pass", None)
    # ai_chat requires free -> never a tier block.
    assert _check(_UserDB(), _u(feature_tier="free"), "/api/ai/chat") == ("pass", None)


def test_tier_instructor_and_admin_bypasses():
    # Instructors bypass course tier gates (they teach).
    assert _check(_UserDB(), _u(role="instructor", feature_tier="free"), "/api/modules/x") == ("pass", None)
    # ...but NOT the member gate on posts.
    assert _check(_UserDB(), _u(role="instructor", feature_tier="free"), "/api/more/posts")[0] == "block"
    # Admins / execs bypass every tier gate.
    assert _check(_UserDB(), _u(role="admin", feature_tier="free"), "/api/more/posts") == ("pass", None)
    assert _check(_UserDB(), _u(role="executive_admin", feature_tier="free"), "/api/modules/x") == ("pass", None)


def test_custom_tier_rank_is_respected():
    custom = [{"tier_id": "scholar", "rank": 4}]
    db = _UserDB(custom_tiers=custom)
    # scholar (rank 4) >= member (1) -> passes posts.
    assert _check(db, _u(feature_tier="scholar"), "/api/more/posts") == ("pass", None)
    # Unknown tier with no definition -> rank 0 -> blocked.
    assert _check(_UserDB(), _u(feature_tier="ghost_tier"), "/api/more/posts")[0] == "block"


def test_per_user_db_error_fails_closed():
    class _BrokenDB:
        async def find_one(self, query, projection=None):
            raise RuntimeError("mongo down")

    assert _check(_BrokenDB(), _u(), "/api/ai/chat")[0] == "unavailable"


# ── Editable authorization matrix (db.authz_matrix) ───────────────────────────
def test_authz_matrix_absent_defaults_to_code():
    # No matrix doc -> exactly the code defaults, for every enforced feature.
    req = asyncio.run(load_feature_tier_requirements(_UserDB()))
    assert req == FEATURE_MIN_TIER
    assert req["ai_chat"] == "free" and req["posts"] == "member" and req["courses"] == "plus"


def test_authz_matrix_stored_overrides_defaults():
    db = _UserDB(authz={"posts": "pro", "courses": "free"})
    req = asyncio.run(load_feature_tier_requirements(db))
    assert req["posts"] == "pro"
    assert req["courses"] == "free"  # can also relax a gate
    assert req["ai_chat"] == "free"  # untouched key keeps default


def test_authz_matrix_ignores_unknown_keys_and_tiers():
    # A bad write can never create a gate for an unmapped feature or an
    # unknown tier — unknown entries are dropped, known keys keep defaults.
    db = _UserDB(authz={"posts": "pro", "ghost_feature": "plus", "courses": "platinum"})
    req = asyncio.run(load_feature_tier_requirements(db))
    assert req["posts"] == "pro"
    assert req["courses"] == "plus"      # platinum dropped -> default
    assert "ghost_feature" not in req


def test_authz_matrix_db_error_fails_open():
    class _BrokenDB:
        async def find_one(self, query, projection=None):
            raise RuntimeError("mongo down")

    assert asyncio.run(load_feature_tier_requirements(_BrokenDB())) == FEATURE_MIN_TIER


def test_authz_matrix_changes_enforcement_live():
    # Raise the posts gate to pro: a member is now blocked server-side.
    db = _UserDB(authz={"posts": "pro"})
    action, detail = _check(db, _u(feature_tier="member"), "/api/more/posts")
    assert action == "block" and "Pro plan" in detail
    # Pro passes.
    assert _check(db, _u(feature_tier="pro"), "/api/more/posts") == ("pass", None)
    # Relax courses to free: a free user now passes (default was plus).
    db2 = _UserDB(authz={"courses": "free"})
    assert _check(db2, _u(feature_tier="free"), "/api/modules/x") == ("pass", None)


def test_tier_map_mirrors_frontend_contract():
    # The enforced map must only contain features with a mapped API surface,
    # and every requirement must be a real tier name.
    for feature, required in FEATURE_MIN_TIER.items():
        assert feature in FEATURE_API_PATHS, f"{feature}: no API surface mapped"
        assert required in TIER_RANK, f"{required}: not a real tier"


def test_maps_are_sane():
    # Every mapped prefix is /api-prefixed and every flag/page key is real.
    for flag, prefixes in FEATURE_API_PATHS.items():
        assert flag and prefixes, f"{flag}: empty map"
        for p in prefixes:
            assert p.startswith("/api"), f"{flag}: prefix {p} must be /api"
    for page_key, prefixes in PAGE_API_PATHS.items():
        assert page_key and prefixes, f"{page_key}: empty map"
        for p in prefixes:
            assert p.startswith("/api"), f"{page_key}: prefix {p} must be /api"
    # page keys must exist in the live PAGE_ACCESS_REGISTRY (needs fastapi -
    # skipped in the stdlib-only runner).
    try:
        from routers.exec_control import PAGE_ACCESS_REGISTRY
    except ImportError:
        print("SKIP test_maps_are_sane registry check (fastapi not installed)")
        return
    registry_keys = {r["key"] for r in PAGE_ACCESS_REGISTRY}
    for page_key in PAGE_API_PATHS:
        assert page_key in registry_keys, f"{page_key} not in PAGE_ACCESS_REGISTRY"


# ── Runner (works without pytest installed) ───────────────────────────────────
if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL  {name}: {exc}")
    total = sum(1 for n in globals() if n.startswith("test_") and callable(globals()[n]))
    print(f"\n{total - failures}/{total} passed")
    sys.exit(1 if failures else 0)
