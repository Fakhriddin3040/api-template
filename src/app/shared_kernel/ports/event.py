from typing import (
    runtime_checkable,
    Protocol,
    Iterable,
    TypeVar,
    Type,
    TypeAlias,
    Callable,
)

from src.app.shared_kernel.types.event_types import BaseEvent

TEvent = TypeVar("TEvent", bound=BaseEvent)


@runtime_checkable
class EventHandlerProto[TEvent](Protocol):
    """BaseEvent handler protocol"""

    async def __call__(self, event: TEvent) -> None: ...


EventHandlerFactoryProto: TypeAlias = Callable[[], EventHandlerProto]


@runtime_checkable
class DLQ(Protocol):
    """
    Dead letter queue for fallen events(after retries).
    """

    async def push(self, event: BaseEvent, exc: Exception) -> None: ...


@runtime_checkable
class EventTransport(Protocol):
    async def send(self, event: BaseEvent) -> None: ...


@runtime_checkable
class EventPublisherMiddlewareProto(Protocol):
    async def before_publish(self, event: BaseEvent) -> BaseEvent: ...
    async def after_publish(self, event: BaseEvent) -> None: ...


@runtime_checkable
class EventHandlerMiddlewareProto(Protocol):
    async def before_handler(
        self, event: BaseEvent, handler: EventHandlerProto
    ) -> None: ...
    async def after_handler(
        self,
        event: BaseEvent,
        handler: EventHandlerProto,
        exc: Exception | None = None,
    ) -> None: ...


@runtime_checkable
class EventPublisherProto(Protocol):
    async def publish(self, event: BaseEvent) -> None: ...
    async def publish_many(self, events: Iterable[BaseEvent]) -> None: ...


@runtime_checkable
class EventConsumerRegistryProto(Protocol):
    def subscribe(
        self, event_t: Type[BaseEvent], handler_f: EventHandlerFactoryProto
    ) -> None: ...


@runtime_checkable
class EventBusProto(EventPublisherProto, EventConsumerRegistryProto, Protocol):
    """BaseEvent bus protocol"""
