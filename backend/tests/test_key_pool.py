import asyncio

from ai.key_pool import KeyPool, parse_key_list


def test_parse_key_list_deduplicates_and_preserves_order():
    assert parse_key_list(" a,b ", "b\nc", "") == ["a", "b", "c"]


def test_round_robin_rotation():
    async def run():
        pool = KeyPool(["a", "b"])
        assert (await pool.acquire()).key == "a"
        assert (await pool.acquire()).key == "b"
        assert (await pool.acquire()).key == "a"

    asyncio.run(run())


def test_rate_limited_key_is_skipped_without_hammering_it():
    async def run():
        pool = KeyPool(["a", "b"], cooldown_seconds=60)
        first = await pool.acquire()
        await pool.mark_rate_limited(first)
        second = await pool.acquire()
        assert second.key == "b"
        await pool.mark_rate_limited(second)
        assert (await pool.acquire()) is None

    asyncio.run(run())


def test_evict_removes_a_key_from_rotation_forever():
    """T1-1: a revoked/invalid key must not come back after the cooldown expires.

    mark_failed only cools a key down; evict removes it from the pool entirely,
    which is what an auth failure (401/403) needs — a bad credential is not a
    transient transport error.
    """
    async def run():
        pool = KeyPool(["a", "b", "c"])
        first = await pool.acquire()
        assert first.key == "a"
        removed = await pool.evict(lambda i: i == first.index)
        assert removed == 1
        assert pool.size == 2
        # The evicted key is gone for the life of the pool, even though its
        # cooldown would have expired long ago.
        keys = []
        for _ in range(4):
            lease = await pool.acquire()
            if lease:
                keys.append(lease.key)
        assert "a" not in keys
        assert set(keys) <= {"b", "c"}

    asyncio.run(run())


def test_evict_predicate_can_target_multiple_keys():
    async def run():
        pool = KeyPool(["a", "b", "c"])
        removed = await pool.evict(lambda i: i in (0, 2))
        assert removed == 2
        assert pool.size == 1
        assert (await pool.acquire()).key == "b"
        # One surviving key, not cooling down — it rotates to itself forever,
        # which is correct: a pool of one is not "all keys throttled".
        assert (await pool.acquire()).key == "b"

    asyncio.run(run())
