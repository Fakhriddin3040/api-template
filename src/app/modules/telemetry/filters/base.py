"""Filter primitives used both as the global gate and as per-destination gates."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from src.app.modules.telemetry.logging.event import TelemetryEvent


@runtime_checkable
class RecordFilter(Protocol):
    def __call__(self, event: TelemetryEvent) -> bool:
        """Return ``True`` if the event may pass this filter."""
        ...


class FilterPipeline:
    """AND-composition of filters with short-circuit evaluation.

    An empty pipeline passes everything.
    """

    def __init__(self, filters: Sequence[RecordFilter] = ()) -> None:
        self._filters: tuple[RecordFilter, ...] = tuple(filters)

    def passes(self, event: TelemetryEvent) -> bool:
        for flt in self._filters:
            if not flt(event):
                return False
        return True

    def __call__(self, event: TelemetryEvent) -> bool:
        return self.passes(event)
