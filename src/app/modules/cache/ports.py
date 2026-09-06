from typing import Any, Optional, Protocol, Union, runtime_checkable

type CacheResult = Union[str, dict[str, Any], list[Any], set[Any], None, bool]


@runtime_checkable
class CacheClientProto(Protocol):
    """Cache client abstraction.

    Works with ``bytes`` so no encoding step sits between the caller and the
    server. **A cache must not fail the client's request** — implementations
    swallow transport errors and answer as a miss rather than raising.
    """

    async def set(self, key: str, value: bytes, ttl: Optional[float] = None) -> None:
        """Store a value.

        Args:
            key: Key to set.
            value: Value to set, as bytes — the native form for most caches.
            ttl: Time to live, in seconds. ``None`` means no expiry.
        """

    async def get(self, key: str) -> Optional[bytes]:
        """Read a value, or ``None`` on a miss."""

    async def invalidate(self, *keys: str) -> None:
        """Drop one or more keys."""

    async def close(self) -> None:
        """Gracefully close cache client connections."""
