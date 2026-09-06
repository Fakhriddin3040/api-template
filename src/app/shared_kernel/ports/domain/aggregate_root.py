from typing import List, Optional, Tuple, Type, Union

from src.app.shared_kernel.ports.domain.domain_event import DomainEvent
from src.app.shared_kernel.types.event_types import BaseEvent


class AggregateRoot:
    """
    This class need '_events' initialize allways on init with empty list
    """

    def __init__(self) -> None:
        self._events = []

    _events: List[DomainEvent]

    def pull_events(
        self,
        types: Optional[Union[Type[BaseEvent], Tuple[Type[BaseEvent]]]] = None,
        except_filter: bool = False,
    ) -> Tuple[DomainEvent, ...]:
        if not types:
            return tuple(self._events)

        if except_filter:
            filter_cb = lambda x: isinstance(x, types), self._events
        else:
            filter_cb = lambda x: not isinstance(x, types), self._events

        return tuple(filter(filter_cb, self._events))

    def add_domain_event(self, event: DomainEvent) -> None:
        self._events.append(event)
