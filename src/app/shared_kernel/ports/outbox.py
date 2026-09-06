from typing import runtime_checkable, Protocol

from src.app.shared_kernel.types.event_types import BaseEvent


@runtime_checkable
class OutBox(Protocol):
    async def add(self, event: BaseEvent) -> None: ...
    async def flush(self) -> None: ...
