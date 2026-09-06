import time
from dataclasses import dataclass, asdict
from typing import TYPE_CHECKING, Optional, Tuple, Type
from uuid import UUID, uuid4

from pydantic import Field

from src.app.shared_kernel.data_structures.mappings import NamedDict
from src.app.shared_kernel.pydantic.types import BasePydanticModel

if TYPE_CHECKING:
    from src.app.shared_kernel.ports.event import EventHandlerFactoryProto


class EventMeta(NamedDict):
    """
    BaseEvent metadata model.
    For storing dynamic data for event.
    """


class BaseEvent(BasePydanticModel):
    """
    BaseEvent representation model
    """

    event_id: UUID = Field(default_factory=uuid4)
    occurred_on: float = Field(init=False, default_factory=time.time)
    order: int = 0
    meta: Optional[EventMeta] = None


@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_seconds: float = 5
    retry_exceptions: Optional[Tuple[Exception, ...]] = None

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class EventHandlerSpec:
    event_type: Type[BaseEvent]
    handler_factory: "EventHandlerFactoryProto"
    order: int = 0
