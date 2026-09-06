"""A tiny async token-bucket rate limiter for the Telegram writer."""

from __future__ import annotations

import asyncio


class TokenBucket:
    def __init__(self, rate: float, capacity: float | None = None) -> None:
        self._rate = float(rate)
        self._capacity = float(capacity if capacity is not None else rate)
        self._tokens = self._capacity
        self._updated = asyncio.get_event_loop().time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: float = 1.0) -> None:
        """Block until ``tokens`` are available, then consume them."""
        async with self._lock:
            while True:
                now = asyncio.get_running_loop().time()
                self._tokens = min(
                    self._capacity, self._tokens + (now - self._updated) * self._rate
                )
                self._updated = now
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                deficit = tokens - self._tokens
                await asyncio.sleep(deficit / self._rate)
