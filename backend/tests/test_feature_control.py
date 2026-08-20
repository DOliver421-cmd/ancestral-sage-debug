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

from security.feature_control import (  # noqa: E402
    FEATURE_API_PATHS,
    PAGE_API_PATHS,
    check_request_config,
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
    return asyncio.run(check_request_config(db, path, flags_doc))


def test_absent_config_allows_everything():
    # No flags doc, no page docs, no db at all -> never block.
    assert _run("/api/ai/chat") is None
    assert _run("/api/more/posts") is None
    assert _run("/api/modules", db=_FakeDB()) is None
    assert _run("/api/ai/chat", db=None) is None


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
    cases = {
        "ai_chat": ["/api/ai/chat", "/api/ai/history"],
        "posts": ["/api/more/post", "/api/more/posts", "/api/more/need"],
        "courses": ["/api/modules", "/api/progress", "/api/labs", "/api/credentials"],
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


def test_db_error_fails_open():
    class _BrokenDB:
        async def find_one(self, query, projection=None):
            raise RuntimeError("mongo down")

    assert _run("/api/ai/chat", db=_BrokenDB()) is None


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
