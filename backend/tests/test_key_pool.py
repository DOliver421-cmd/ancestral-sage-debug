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
