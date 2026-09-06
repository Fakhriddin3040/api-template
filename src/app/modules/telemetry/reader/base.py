"""Abstract async log reader.

A reader is an async iterator of :class:`TelemetryEvent`. Concrete
implementations decide *where* lines come from (filesystem, socket, ...); the
composer only cares about the ``async for`` contract.
"""

from __future__ import annotations

import abc

from src.app.modules.telemetry.logging.event import TelemetryEvent


class AbstractLogReader(abc.ABC):
    def __aiter__(self) -> "AbstractLogReader":
        return self

    @abc.abstractmethod
    async def __anext__(self) -> TelemetryEvent:  # pragma: no cover - interface
        raise NotImplementedError

    async def aclose(self) -> None:
        """Release any held resources. Overridable; no-op by default."""
        return None
