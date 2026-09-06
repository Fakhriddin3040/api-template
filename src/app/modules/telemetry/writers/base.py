"""Abstract async writer.

Each writer owns a bounded :class:`asyncio.Queue` and a background consumer task.
``submit`` is non-blocking and drops (counting) on overflow, so a slow or stalled
destination can never apply backpressure to the reader/composer - this is what
keeps Telegram/Postgres from ever delaying the main request path. Minimal loss is
acceptable by design.
"""

from __future__ import annotations

import abc
import asyncio
import logging
from typing import Optional

from src.app.modules.telemetry.logging.event import TelemetryEvent

logger = logging.getLogger("telemetry.writer")

_SENTINEL = object()


class AbstractWriter(abc.ABC):
    name: str = "writer"

    def __init__(
        self,
        *,
        maxsize: int = 10_000,
        batch_size: int = 1,
        flush_interval: float = 0.5,
    ) -> None:
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._batch_size = max(1, batch_size)
        self._flush_interval = flush_interval
        self._task: Optional[asyncio.Task] = None
        self._dropped = 0

    @property
    def dropped(self) -> int:
        return self._dropped

    def submit(self, event: TelemetryEvent) -> None:
        """Enqueue without blocking. Drop (and count) if the queue is full."""
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self._dropped += 1

    async def start(self) -> None:
        await self._on_start()
        self._task = asyncio.create_task(
            self._run(), name=f"telemetry-writer-{self.name}"
        )

    async def aclose(self) -> None:
        await self._queue.put(_SENTINEL)
        if self._task is not None:
            await self._task
        await self._on_close()

    async def _run(self) -> None:
        stopping = False
        while not stopping:
            try:
                first = await asyncio.wait_for(
                    self._queue.get(), timeout=self._flush_interval
                )
            except asyncio.TimeoutError:
                continue

            if first is _SENTINEL:
                break

            batch = [first]
            while len(batch) < self._batch_size:
                try:
                    item = self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                if item is _SENTINEL:
                    stopping = True
                    break
                batch.append(item)

            try:
                await self._handle_batch(batch)
            except Exception:  # noqa: BLE001 - never let one bad batch kill the writer
                logger.exception("telemetry writer '%s' failed on a batch", self.name)

    # --- hooks for subclasses -------------------------------------------------

    async def _on_start(self) -> None:
        return None

    async def _on_close(self) -> None:
        return None

    @abc.abstractmethod
    async def _handle_batch(self, batch: list[TelemetryEvent]) -> None:
        raise NotImplementedError
