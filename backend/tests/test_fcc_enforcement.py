"""tests/test_fcc_enforcement.py — Feature Control Center enforcement tests.

Covers the Phase 16 authoritative-access work (stdlib-only, no MongoDB):
  - FCC feature_id -> API path mapping (verified prefixes)
  - load_fcc_config: registry default + DB override merge, tier normalization
  - check_user_feature_access FCC block:
      * internal_only (Jamil = admin+, Arena = executive_admin) at the
        exact decision function the HTTP middleware calls
      * enabled=false override
      * allowed_roles / allowed_tiers overrides (rank-based)
      * legacy tier label normalization (creator -> member, ...)
  - ec_access_public gate-map merge (FCC overrides reach the frontend nav map)

Run:  cd backend && python3 tests/test_fcc_enforcement.py   (or pytest)
"""

import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security.feature_control import (  # noqa: E402
    check_user_feature_access,
    fcc_feature_for_path,
    load_fcc_config,
)

# ── Minimal async fake for the motor collections the middleware touches ──────
class FakeCollection:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, query, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in query.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    def find(self, query=None, projection=None):
        return self

    async def to_list(self, limit):
        return list(self.docs)


class FakeDB:
    def __init__(self, **collections):
        for name, docs in collections.items():
            setattr(self, name, FakeCollection(docs))


def _user(role, tier="free", uid="u-1"):
    return SimpleNamespace(id=uid, role=role, feature_tier=tier)


def _db(**overrides):
    return FakeDB(
        user_feature_overrides=[],
        authz_matrix=[],
        tier_definitions=[],
        feature_configs=overrides.get("feature_configs", []),
    )


async def _verdict(db, user, path):
    return await check_user_feature_access(db, user, path)


def _run(coro):
    return asyncio.run(coro)


# ── 1. Path mapping (must match the live route table) ────────────────────────
def test_fcc_path_mapping():
    assert fcc_feature_for_path("/api/jamil/chat") == "nam.jamil"
    assert fcc_feature_for_path("/api/jamil/knowledge") == "nam.jamil"
    assert fcc_feature_for_path("/api/competition/task") == "games.arena"
    assert fcc_feature_for_path("/api/competition/leaderboard") == "games.arena"
    assert fcc_feature_for_path("/api/ai/orchestrator") == "nam.orchestrator"
    assert fcc_feature_for_path("/api/ai/helper") == "nam.helper"
    assert fcc_feature_for_path("/api/ai/sage/integrity") == "nam.council"
    assert fcc_feature_for_path("/api/ai/chat") == "nam.chat"
    assert fcc_feature_for_path("/api/nam/memory") == "nam.hybrid"  # Hybrid NAM owns memory (registry: identity, memory, intentions)
    assert fcc_feature_for_path("/api/site-guide") == "nam.site_guide"
    # Unmapped surfaces stay outside the FCC enforcement.
    assert fcc_feature_for_path("/api/auth/me") is None
    assert fcc_feature_for_path("/api/health") is None
    assert fcc_feature_for_path("/api/more/posts") is None


# ── 2. Registry default merge + tier normalization ───────────────────────────
def test_load_fcc_config_registry_default():
    cfg = _run(load_fcc_config(_db(), "nam.jamil"))
    assert cfg is not None
    assert cfg["internal_only"] is True
    assert cfg["enabled"] is True
    assert cfg["allowed_roles"] == ["admin", "executive_admin"]  # registry default
    assert cfg["_override_roles"] is False
    assert cfg["_override_tiers"] is False


def test_load_fcc_config_override_merges():
    db = _db(
        feature_configs=[
            {"feature_id": "nam.jamil", "enabled": False},
            {"feature_id": "nam.helper", "allowed_tiers": ["creator", "pro"]},
        ]
    )
    jamil = _run(load_fcc_config(db, "nam.jamil"))
    assert jamil["enabled"] is False
    assert jamil["internal_only"] is True  # classification survives the override
    helper = _run(load_fcc_config(db, "nam.helper"))
    assert helper["allowed_tiers"] == ["member", "pro"]  # legacy label normalized
    assert helper["_override_tiers"] is True


def test_load_fcc_config_unknown_feature():
    assert _run(load_fcc_config(_db(), "does.not.exist")) is None


# ── 3. JAMIL — proprietary, admin+ only ──────────────────────────────────────
def test_jamil_blocks_non_staff():
    for role in ("student", "trial_pass", "instructor", "support_staff", "oversight"):
        action, detail = _run(_verdict(_db(), _user(role), "/api/jamil/chat"))
        assert action == "block", f"{role} must be blocked"
        assert detail and "restricted" in detail.lower()
    # Anonymous: pass-through — the route's own auth produces the 401.
    action, _ = _run(_verdict(_db(), None, "/api/jamil/chat"))
    assert action == "pass"


def test_jamil_allows_admin_and_exec():
    for role in ("admin", "executive_admin"):
        action, _ = _run(_verdict(_db(), _user(role), "/api/jamil/chat"))
        assert action == "pass", f"{role} must pass"


# ── 4. ARENA — strictly executive_admin ──────────────────────────────────────
def test_arena_exec_only():
    for role in ("student", "trial_pass", "instructor", "support_staff", "oversight", "admin"):
        action, _ = _run(_verdict(_db(), _user(role), "/api/competition/task"))
        assert action == "block", f"{role} must be blocked from Arena"
    action, _ = _run(_verdict(_db(), _user("executive_admin"), "/api/competition/task"))
    assert action == "pass"


# ── 5. ORCHESTRATOR — internal, admin+ ───────────────────────────────────────
def test_orchestrator_admin_only():
    action, _ = _run(_verdict(_db(), _user("student"), "/api/ai/orchestrator"))
    assert action == "block"
    action, _ = _run(_verdict(_db(), _user("admin"), "/api/ai/orchestrator"))
    assert action == "pass"


# ── 6. Non-internal features are NOT gated by registry defaults ──────────────
def test_helper_open_to_regular_users_by_default():
    for role in ("student", "instructor", "admin", "executive_admin"):
        action, _ = _run(_verdict(_db(), _user(role), "/api/ai/helper"))
        assert action == "pass", f"{role} must pass helper (no override)"


# ── 7. Admin overrides bind (the FCC is authoritative) ───────────────────────
def test_enabled_false_blocks_everyone():
    db = _db(feature_configs=[{"feature_id": "nam.helper", "enabled": False}])
    for role in ("student", "admin", "executive_admin"):
        action, detail = _run(_verdict(db, _user(role), "/api/ai/helper"))
        assert action == "block", f"{role} must be blocked when feature disabled"
        assert "disabled" in detail.lower()


def test_allowed_roles_override_binds_rank_based():
    db = _db(feature_configs=[{"feature_id": "nam.helper", "allowed_roles": ["admin"]}])
    action, _ = _run(_verdict(db, _user("student"), "/api/ai/helper"))
    assert action == "block"
    action, _ = _run(_verdict(db, _user("support_staff"), "/api/ai/helper"))
    assert action == "block"
    # Rank-based: "admin" also admits executive_admin.
    action, _ = _run(_verdict(db, _user("admin"), "/api/ai/helper"))
    assert action == "pass"
    action, _ = _run(_verdict(db, _user("executive_admin"), "/api/ai/helper"))
    assert action == "pass"


def test_allowed_tiers_override_binds():
    db = _db(feature_configs=[{"feature_id": "nam.helper", "allowed_tiers": ["pro"]}])
    action, _ = _run(_verdict(db, _user("student", tier="free"), "/api/ai/helper"))
    assert action == "block"
    action, _ = _run(_verdict(db, _user("student", tier="member"), "/api/ai/helper"))
    assert action == "block"
    action, _ = _run(_verdict(db, _user("student", tier="pro"), "/api/ai/helper"))
    assert action == "pass"
    action, _ = _run(_verdict(db, _user("student", tier="patron"), "/api/ai/helper"))
    assert action == "pass"


def test_legacy_tier_labels_normalize_in_enforcement():
    # An admin who checked "creator" in an old UI must still admit member users.
    db = _db(feature_configs=[{"feature_id": "nam.helper", "allowed_tiers": ["creator"]}])
    action, _ = _run(_verdict(db, _user("student", tier="free"), "/api/ai/helper"))
    assert action == "block"
    action, _ = _run(_verdict(db, _user("student", tier="member"), "/api/ai/helper"))
    assert action == "pass"


# ── 8. Unmapped paths pass (safe-default preserved) ──────────────────────────
def test_unmapped_paths_pass():
    action, _ = _run(_verdict(_db(), _user("student"), "/api/auth/me"))
    assert action == "pass"


# ── 9. Gate-map merge: FCC overrides reach the frontend nav map ──────────────
def test_ec_access_public_merges_fcc_overrides():
    from routers import exec_control as ec

    ec.db = FakeDB(
        page_access=[
            {"page": "arena", "enabled": True, "allowed_roles": None},
        ],
        feature_configs=[
            {"feature_id": "games.arena", "enabled": False},
            {"feature_id": "nam.helper", "allowed_roles": ["admin"]},
        ],
    )
    result = asyncio.run(ec.ec_access_public())
    pages = result["pages"]
    # FCC disabled Arena -> the arena nav/page gate turns off.
    assert pages["arena"]["enabled"] is False
    # FCC role override for helper reaches the gate map.
    assert pages["helper"]["allowed_roles"] == ["admin"]
    # Registry/DB pages untouched by the FCC keep their own values.
    assert "ai" in pages  # PAGE_ACCESS_REGISTRY entry still present
    # INTERNAL-only registry defaults gate customer nav: Jamil (admin+),
    # Arena (exec) are hidden from students by the existing isPageEnabled
    # allowed_roles check — no DB override needed.
    assert pages["jamil"]["allowed_roles"] == ["admin", "executive_admin"]
    assert pages["arena"]["allowed_roles"] == ["executive_admin"]
    # Non-internal features are NOT gated by registry defaults (no lockout).
    assert pages.get("helper", {}).get("allowed_roles") == ["admin"]  # from DB override only
    assert "council" not in pages or pages["council"].get("enabled", True) is not False


def test_ec_access_public_tier_and_public_metadata():
    """Tier-first navigation metadata (allowed_tiers + public_access +
    navigation_visible) reaches the gate map from registry defaults and from
    FCC overrides — the frontend nav derives visibility from this payload."""
    from routers import exec_control as ec

    ec.db = FakeDB(
        page_access=[],
        feature_configs=[
            # FCC overrides: tier lift + public marking + nav hiding.
            {"feature_id": "create.studio", "allowed_tiers": ["free", "member"]},
            {"feature_id": "nam.helper", "public_access": True},
            {"feature_id": "nam.chat", "navigation_visible": False},
        ],
    )
    pages = asyncio.run(ec.ec_access_public())["pages"]

    # Registry defaults are pushed additively (never a surprise lockout):
    # adaptive plus+, sanctuary plus+, free-tier features carry the full ladder.
    assert pages["adaptive"]["allowed_tiers"] == ["plus", "pro", "patron"]
    assert pages["sanctuary"]["allowed_tiers"] == ["plus", "pro", "patron"]
    assert "free" in pages["ai"]["allowed_tiers"]
    # Internal-only features keep empty tiers (role gate governs instead).
    assert pages["arena"]["allowed_tiers"] == []
    assert pages["jamil"]["allowed_tiers"] == []
    # Public marking: only registry-public features are flagged for anonymous.
    assert pages["store"]["public_access"] is True
    assert pages["leaderboard"]["public_access"] is True
    assert "public_access" not in pages["ai"]  # not public → anonymous hidden
    # FCC overrides win over registry defaults.
    assert pages["studio"]["allowed_tiers"] == ["free", "member"]  # FCC lifted studio down to free
    assert pages["helper"]["public_access"] is True  # FCC marked public
    assert pages["ai"]["navigation_visible"] is False  # FCC hid from nav
    # Every registered feature maps to a gate entry (nav can derive from it).
    from routers.features import FEATURE_REGISTRY

    for reg in FEATURE_REGISTRY:
        route = (reg.get("route") or "").strip("/")
        key = route.split("/")[0] if route else None
        if key:
            assert key in pages, f"gate map missing key for {reg['feature_id']} ({key})"


# ── Runner (works without pytest installed) ──────────────────────────────────
if __name__ == "__main__":
    failures = 0
    total = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            total += 1
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:  # noqa: BLE001
                failures += 1
                print(f"FAIL  {name}: {exc}")
    print(f"\n{total - failures}/{total} passed")
    sys.exit(1 if failures else 0)
