import logging
import time
from typing import Dict
from uuid import UUID

from src.app.infra.inheritance.mixins import ExecutionContextMixin
from src.app.shared_kernel.ports.event import (
    EventPublisherMiddlewareProto,
    EventHandlerMiddlewareProto,
    EventHandlerProto,
)
from src.app.shared_kernel.types.event_types import BaseEvent

logger = logging.getLogger(__name__)


class LoggingEventPublisherMiddleware(
    EventPublisherMiddlewareProto, ExecutionContextMixin
):

    async def before_publish(self, event: BaseEvent) -> BaseEvent:
        logger.info(
            f"{self._get_trace_id()} - Event published", extra=event.model_dump()
        )
        return event

    async def after_publish(self, event: BaseEvent) -> None: ...


class ObservabilityEventHandlerMiddleware(
    EventHandlerMiddlewareProto, ExecutionContextMixin
):
    def __init__(self) -> None:
        # Keyed per (event, handler): one event fans out to several concurrent
        # handlers, so the event_id alone is not unique here.
        self._registry: Dict[tuple[UUID, int], float] = {}

    async def before_handler(
        self, event: BaseEvent, handler: EventHandlerProto
    ) -> None:
        self._registry[(event.event_id, id(handler))] = time.perf_counter()
        logger.info(
            f"{self._get_trace_id()} - Before handling event: {event.__class__.__name__}",
            extra=event.model_dump(),
        )

    async def after_handler(
        self,
        event: BaseEvent,
        handler: EventHandlerProto,
        exc: Exception | None = None,
    ) -> None:
        started = self._registry.pop((event.event_id, id(handler)), None)
        elapsed = time.perf_counter() - started if started is not None else None

        logger.info(
            f"{self._get_trace_id()} - After handling event: {event.__class__.__name__}. "
            f"Completed in: {elapsed}",
            extra={"event_id": event.event_id},
        )
