"""Ready-made filters. Compose them into a :class:`FilterPipeline`."""

from __future__ import annotations

import logging
import random
from typing import Callable, Iterable

from src.app.modules.telemetry.logging.event import TelemetryEvent


def _level_no(level: str) -> int:
    resolved = logging.getLevelName((level or "").upper())
    return resolved if isinstance(resolved, int) else logging.INFO


class MinLevel:
    """Pass events whose level is at least ``level`` (e.g. WARNING)."""

    def __init__(self, level: str) -> None:
        self._threshold = _level_no(level)

    def __call__(self, event: TelemetryEvent) -> bool:
        return _level_no(event.level) >= self._threshold


class ServiceIn:
    def __init__(self, services: Iterable[str]) -> None:
        self._services = frozenset(services)

    def __call__(self, event: TelemetryEvent) -> bool:
        return event.service in self._services


class KindIn:
    def __init__(self, kinds: Iterable[str]) -> None:
        self._kinds = frozenset(kinds)

    def __call__(self, event: TelemetryEvent) -> bool:
        return event.kind in self._kinds


class StatusAtLeast:
    """Pass http events with ``status_code >= code`` (e.g. 500).

    ``pass_when_missing`` controls non-http events (no status): ``True`` when used
    as a global gate (don't drop logs), ``False`` when used inside an OR route
    (e.g. "errors only" for Telegram), so plain INFO logs don't leak through.
    """

    def __init__(self, code: int, *, pass_when_missing: bool = True) -> None:
        self._code = code
        self._pass_when_missing = pass_when_missing

    def __call__(self, event: TelemetryEvent) -> bool:
        if event.status_code is None:
            return self._pass_when_missing
        return event.status_code >= self._code


class Sampling:
    """Randomly pass a fraction ``rate`` (0..1) of events."""

    def __init__(self, rate: float) -> None:
        self._rate = max(0.0, min(1.0, rate))

    def __call__(self, event: TelemetryEvent) -> bool:
        return random.random() < self._rate


class Not:
    def __init__(self, flt: Callable[[TelemetryEvent], bool]) -> None:
        self._flt = flt

    def __call__(self, event: TelemetryEvent) -> bool:
        return not self._flt(event)


class AnyOf:
    """OR-composition: pass if any inner filter passes."""

    def __init__(self, filters: Iterable[Callable[[TelemetryEvent], bool]]) -> None:
        self._filters = tuple(filters)

    def __call__(self, event: TelemetryEvent) -> bool:
        return any(flt(event) for flt in self._filters)


class ExcludeUrls:
    """Drop noisy paths (healthchecks, docs, ...)."""

    def __init__(self, prefixes: Iterable[str]) -> None:
        self._prefixes: tuple[str, ...] = tuple(prefixes)

    def __call__(self, event: TelemetryEvent) -> bool:
        if not event.url:
            return True
        return not any(event.url.startswith(p) for p in self._prefixes)
