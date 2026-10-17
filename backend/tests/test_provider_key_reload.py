"""tests/test_provider_key_reload.py — the DB key reload actually reaches the
rotating pools.

Root cause this pins: `reload_provider_keys` decrypted DB keys into the module
globals (GROQ_API_KEY, CEREBRAS_API_KEY, ...) but never rebuilt the rotating
pools, which are constructed once at import time from `os.environ`. Every
rotating tier in call_llm() reads the pool (`pool.acquire()`,
`_PROVIDER_KEY_POOLS[p].size`) and never the global — so a key saved in the
exec Provider Gateway for groq/cerebras/sambanova/gemini/nvidia/deepinfra/
novita/hyperbolic/perplexity was decrypted, stored in a global nobody read, and
the tier stayed silently skipped. That is "AI_PROVIDER_UNAVAILABLE" appearing
while keys are already saved.

The fix: rebuild each pool from env-var keys + DB keys on every reload.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import llm_gateway as gw  # noqa: E402


class FakeDB:
    """Minimal async Mongo-like fake backing the two collections reload reads.

    Access is by attribute (`db.api_keys`) and by key (`db["api_keys"]`) —
    both route to the same collection object, matching how motor exposes them.
    """

    def __init__(self, api_keys, api_providers):
        self.api_keys = _Coll(api_keys)
        self.api_providers = _Coll(api_providers)

    def __getitem__(self, name):
        return getattr(self, name)


class _Coll:
    def __init__(self, docs):
        self._docs = docs

    def find(self, query, *args, **kwargs):
        return _Cursor([d for d in self._docs if _match(query, d)])

    async def find_one(self, query, projection=None):
        for d in self._docs:
            if _match(query, d):
                return d
        return None


class _Cursor:
    def __init__(self, docs):
        self._docs = docs

    async def to_list(self, n):
        return list(self._docs[:n])

    def __aiter__(self):
        self._i = 0
        return self

    async def __anext__(self):
        if self._i >= len(self._docs):
            raise StopAsyncIteration
        d = self._docs[self._i]
        self._i += 1
        return d


def _match(query, doc):
    """Minimal Mongo query matcher — equality plus `$in`, enough for reload."""
    if not query:
        return True
    for k, v in query.items():
        if isinstance(v, dict) and "$in" in v:
            if doc.get(k) not in v["$in"]:
                return False
        elif doc.get(k) != v:
            return False
    return True


def _clear_pools():
    for pool in gw._PROVIDER_KEY_POOLS.values():
        pool.keys = ()
        pool._next = 0
        pool._cooldowns = {}


def test_reload_populates_rotating_pools_from_db_keys():
    """A DB key for a rotating provider must make that tier usable after reload.

    Before the fix this returned 0 and left every rotating pool empty, because
    the globals were written but the pools were never rebuilt.
    """
    import asyncio

    _clear_pools()
    gw.GROQ_API_KEY = ""  # no env var, so the DB key is the only source
    db = FakeDB(
        api_keys=[{
            "provider_id": "prov-groq",
            "encrypted_key": "plain-groq-key-1",
            "status": "active",
        }],
        api_providers=[{"id": "prov-groq", "provider_type": "groq"}],
    )

    async def run():
        loaded = await gw.reload_provider_keys(db)
        assert loaded == 1, f"expected 1 key loaded, got {loaded}"
        # The pool is the thing the chain actually reads.
        assert gw._PROVIDER_KEY_POOLS["groq"].size == 1
        lease = await gw._PROVIDER_KEY_POOLS["groq"].acquire()
        assert lease is not None
        assert lease.key == "plain-groq-key-1"

    asyncio.run(run())


def test_reload_skips_revoked_keys():
    """A revoked DB key must not reappear after reload — the query filters
    status: 'active', so it is simply absent from the result."""
    import asyncio

    _clear_pools()
    gw.GROQ_API_KEY = ""
    db = FakeDB(
        api_keys=[{
            "provider_id": "prov-groq",
            "encrypted_key": "plain-groq-key-1",
            "status": "revoked",  # not active — must not load
        }],
        api_providers=[{"id": "prov-groq", "provider_type": "groq"}],
    )

    async def run():
        loaded = await gw.reload_provider_keys(db)
        assert loaded == 0
        assert gw._PROVIDER_KEY_POOLS["groq"].size == 0

    asyncio.run(run())


def test_env_var_wins_over_db_key():
    """An env var already set is never overwritten, and the DB key is skipped.

    The pool is not rebuilt by reload when the env var is set (no DB key for
    that type is collected), so the pool retains whatever it held at startup —
    which, for a rotating provider, is the env key. This test pins the
    reload-side behaviour: a set env var blocks the DB key entirely, and the
    global is left untouched.
    """
    import asyncio

    _clear_pools()
    gw._PROVIDER_KEY_POOLS["groq"] = gw.KeyPool(["env-groq-key"])
    gw.GROQ_API_KEY = "env-groq-key"
    db = FakeDB(
        api_keys=[{
            "provider_id": "prov-groq",
            "encrypted_key": "plain-groq-key-1",
            "status": "active",
        }],
        api_providers=[{"id": "prov-groq", "provider_type": "groq"}],
    )

    async def run():
        loaded = await gw.reload_provider_keys(db)
        assert loaded == 0  # env var already set, DB key skipped
        assert gw.GROQ_API_KEY == "env-groq-key"
        # The pool is untouched — reload does not rebuild it when no DB key was
        # collected for this type, so the env key the pool was built with stays.
        assert gw._PROVIDER_KEY_POOLS["groq"].size == 1
        lease = await gw._PROVIDER_KEY_POOLS["groq"].acquire()
        assert lease.key == "env-groq-key"

    asyncio.run(run())


def test_reload_supports_all_rotating_providers():
    """Every provider with a rotating pool must be loadable from the DB."""
    import asyncio

    rotating = ("groq", "cerebras", "sambanova", "gemini",
                "nvidia", "deepinfra", "novita", "hyperbolic", "perplexity")
    for name in rotating:
        _clear_pools()
        for n in rotating:
            setattr(gw, f"{n.upper()}_API_KEY", "")
        db = FakeDB(
            api_keys=[{
                "provider_id": f"prov-{name}",
                "encrypted_key": f"plain-{name}-key",
                "status": "active",
            }],
            api_providers=[{"id": f"prov-{name}", "provider_type": name}],
        )

        async def run(name=name, db=db):
            loaded = await gw.reload_provider_keys(db)
            assert loaded == 1, f"{name}: expected 1 key, got {loaded}"
            assert gw._PROVIDER_KEY_POOLS[name].size == 1, (
                f"{name}: pool not rebuilt by reload"
            )

        asyncio.run(run())