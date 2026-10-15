"""Bounded in-process key rotation for provider credentials.

This module intentionally does not perform concurrent fan-out. A provider key is
an account credential, so one request is assigned one key; rotation spreads
requests without multiplying provider usage. Cross-replica fairness still
requires an external shared limiter, which this pool does not claim to provide.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class KeyLease:
    key: str
    index: int


class KeyPool:
    def __init__(self, raw_keys: Iterable[str], cooldown_seconds: float = 30.0):
        self.keys = tuple(dict.fromkeys(k.strip() for k in raw_keys if k and k.strip()))
        self.cooldown_seconds = max(0.0, cooldown_seconds)
        self._next = 0
        self._cooldowns: dict[int, float] = {}
        self._lock = asyncio.Lock()

    @property
    def size(self) -> int:
        return len(self.keys)

    async def acquire(self) -> KeyLease | None:
        if not self.keys:
            return None
        now = time.monotonic()
        async with self._lock:
            for offset in range(len(self.keys)):
                index = (self._next + offset) % len(self.keys)
                if self._cooldowns.get(index, 0.0) <= now:
                    self._next = (index + 1) % len(self.keys)
                    return KeyLease(self.keys[index], index)
            # All keys are cooling down. Do not silently hammer a throttled key;
            # the caller should proceed to the next provider/fallback instead.
            return None

    async def mark_rate_limited(self, lease: KeyLease, cooldown_seconds: float | None = None) -> None:
        async with self._lock:
            if 0 <= lease.index < len(self.keys):
                self._cooldowns[lease.index] = time.monotonic() + (
                    self.cooldown_seconds if cooldown_seconds is None else max(0.0, cooldown_seconds)
                )

    async def mark_failed(self, lease: KeyLease, cooldown_seconds: float = 5.0) -> None:
        """Briefly avoid a transport/provider failure without treating it as 429."""
        await self.mark_rate_limited(lease, cooldown_seconds)

    def cooldown_snapshot(self) -> dict[int, float]:
        now = time.monotonic()
        return {index: max(0.0, until - now) for index, until in self._cooldowns.items() if until > now}

    async def evict(self, predicate) -> int:
        """Drop keys whose index satisfies `predicate(index) -> bool`.

        Rotation must not resurrect a revoked key: a revoked DB key stays out
        even after a reload re-reads the pool, and a key that failed auth is
        removed from the in-process rotation rather than cycled back to.
        Returns the number of keys removed.
        """
        removed = 0
        async with self._lock:
            keep = []
            for index, key in enumerate(self.keys):
                if predicate(index):
                    removed += 1
                    self._cooldowns.pop(index, None)
                else:
                    keep.append(key)
            self.keys = tuple(keep)
            if self._next >= len(self.keys):
                self._next = 0
        return removed


def parse_key_list(*values: str | None) -> list[str]:
    """Parse comma/newline-separated values while preserving input order."""
    result: list[str] = []
    for value in values:
        if value:
            result.extend(part.strip() for part in value.replace("\n", ",").split(","))
    return [key for key in dict.fromkeys(result) if key]
