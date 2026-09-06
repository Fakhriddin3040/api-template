from typing import Protocol, runtime_checkable


@runtime_checkable
class TransportQueueSender(Protocol):
    """Data transport. Sender. For sending data to some storage."""

    async def send(self, data: bytes) -> None: ...


@runtime_checkable
class TransportQueueReceiver(Protocol):
    """Data transport. Receiver. For receiving data to some storage."""

    async def receive(self) -> bytes: ...
