from typing import Protocol, Awaitable

from src.app.shared_kernel.types.base_types import ID_T
from src.app.infra.constants.enums import AggregateName
from src.app.shared_kernel.types.event_types import BaseEvent


class DomainEvent(BaseEvent):
    aggregate_id: ID_T
    aggregate_name: AggregateName


class DomainEventHandler(Protocol):
    def __call__(self, event: DomainEvent) -> None | Awaitable[None]: ...
