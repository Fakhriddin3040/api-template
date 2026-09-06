"""The composer sits on top of the writers.

For every event it first runs the global filter pipeline (drop noise), then for
each ``(writer, destination_filter)`` route it asks the destination filter whether
this event belongs there. Dispatch is non-blocking - each writer buffers in its
own queue. System events bypass the global gate (the system is speaking, not a log).
"""

from __future__ import annotations

import logging
from typing import Sequence, Tuple

from src.app.modules.telemetry.filters.base import FilterPipeline, RecordFilter
from src.app.modules.telemetry.logging.event import KIND_SYSTEM, TelemetryEvent
from src.app.modules.telemetry.writers.base import AbstractWriter

logger = logging.getLogger("telemetry.composer")

Route = Tuple[AbstractWriter, RecordFilter]


class TelemetryComposer:
    def __init__(
        self,
        global_pipeline: FilterPipeline,
        routes: Sequence[Route],
    ) -> None:
        self._global = global_pipeline
        self._routes: tuple[Route, ...] = tuple(routes)

    @property
    def writers(self) -> list[AbstractWriter]:
        return [writer for writer, _ in self._routes]

    def dispatch(self, event: TelemetryEvent) -> None:
        if event.kind != KIND_SYSTEM and not self._global.passes(event):
            return
        for writer, destination in self._routes:
            try:
                if destination(event):
                    writer.submit(event)
            except Exception:  # noqa: BLE001 - a bad filter must not stop dispatch
                logger.exception("route filter failed for writer '%s'", writer.name)

    async def start(self) -> None:
        for writer in self.writers:
            await writer.start()

    async def aclose(self) -> None:
        for writer in self.writers:
            try:
                await writer.aclose()
            except Exception:  # noqa: BLE001
                logger.exception("error closing writer '%s'", writer.name)
