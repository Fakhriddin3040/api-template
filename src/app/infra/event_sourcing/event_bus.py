from collections import defaultdict
from typing import List, Dict, Type, Optional, Iterable


from src.app.shared_kernel.ports.event import (
    EventHandlerProto,
    EventPublisherMiddlewareProto,
    EventHandlerMiddlewareProto,
    EventBusProto,
    EventHandlerFactoryProto,
)
from src.app.shared_kernel.types.event_types import BaseEvent
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class InProcessEventBus(EventBusProto):
    """InMemoryEventBus for sync event sourcing"""

    def __init__(
        self,
        publisher_middlewares: Optional[List[EventPublisherMiddlewareProto]] = None,
        handler_middlewares: Optional[List[EventHandlerMiddlewareProto]] = None,
    ) -> None:
        self._handlers: Dict[Type[BaseEvent], List[EventHandlerProto]] = defaultdict(
            list
        )
        self._publisher_middlewares: List[EventPublisherMiddlewareProto] = (
            publisher_middlewares or []
        )
        self._handler_middlewares: List[EventHandlerMiddlewareProto] = (
            handler_middlewares or []
        )

    async def publish(self, event: BaseEvent) -> None:
        for middleware in self._publisher_middlewares:
            await middleware.before_publish(event)

        for handler in self._handlers[event.__class__]:
            await handler(event=event)

        for middleware in self._publisher_middlewares:
            await middleware.after_publish(event)

    async def publish_many(self, events: Iterable[BaseEvent]) -> None:
        if not events:
            return

        for event in sorted(events, key=lambda e: e.order):
            await self.publish(event)

    def subscribe(
        self, event_t: Type[BaseEvent], handler_f: EventHandlerFactoryProto
    ) -> None:
        handler = self._wrap_handler_factory(handler_f=handler_f)
        self._handlers[event_t].append(handler)

    def _wrap_handler_factory(
        self, handler_f: EventHandlerFactoryProto
    ) -> EventHandlerProto:
        async def wrapper(event: BaseEvent) -> None:
            handler = handler_f()
            for middleware in self._handler_middlewares:
                await middleware.before_handler(event=event, handler=handler)

            await handler(event=event)

            for middleware in self._handler_middlewares:
                await middleware.after_handler(event=event, handler=handler)

        return wrapper


ensure_isimplementation(InProcessEventBus, EventBusProto)
