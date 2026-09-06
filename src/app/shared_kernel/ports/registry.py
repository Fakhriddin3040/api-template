from typing import runtime_checkable, Protocol


@runtime_checkable
class IdempotencyRegistry(Protocol):
    def generate(self) -> str: ...
    async def is_seen(self, idempotency_key: str) -> bool: ...
    async def remember(
        self, idempotency_key: str, handler: str, ttl_seconds: int
    ) -> None: ...
