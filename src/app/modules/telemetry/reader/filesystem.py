"""Filesystem tail reader: ``async for event in FileSystemLogReader(...)``.

Tails every ``logs/*.log`` file, tracking a per-file ``(inode, offset)`` cursor.
Rotation is detected structurally - when a file's inode changes or its size
shrinks below the cursor, reading restarts from the top - so the
``RotatingFileHandler`` producers are followed across rotations without needing a
trailer marker. Blocking reads are pushed to a thread executor to stay async.
"""

from __future__ import annotations

import asyncio
import os
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import msgspec

from src.app.modules.telemetry.logging.event import KIND_LOG, TelemetryEvent
from src.app.modules.telemetry.reader.base import AbstractLogReader

_DECODER = msgspec.json.Decoder(TelemetryEvent)


@dataclass
class _FileCursor:
    inode: int
    offset: int = 0
    buffer: bytes = b""


@dataclass
class _Poller:
    directory: Path
    pattern: str
    from_end: bool
    cursors: dict[str, _FileCursor] = field(default_factory=dict)

    def collect(self) -> list[TelemetryEvent]:
        """Blocking scan of all matching files; returns newly-parsed events."""
        events: list[TelemetryEvent] = []
        # Recursive: works for a flat logs/*.log layout and for the docker layout
        # where each service mounts its own logs/<service>/<service>.log subdir.
        for path in sorted(self.directory.rglob(self.pattern)):
            try:
                stat = path.stat()
            except OSError:
                continue

            key = str(path)
            cursor = self.cursors.get(key)
            if cursor is None or cursor.inode != stat.st_ino:
                # New or rotated file. Skip existing history on first sight when
                # from_end is set, otherwise read from the beginning.
                start = stat.st_size if (cursor is None and self.from_end) else 0
                cursor = _FileCursor(inode=stat.st_ino, offset=start)
                self.cursors[key] = cursor
            elif stat.st_size < cursor.offset:
                # Truncated in place -> restart from the top.
                cursor.offset = 0
                cursor.buffer = b""

            if stat.st_size <= cursor.offset:
                continue

            service = path.stem
            with open(path, "rb") as fh:
                fh.seek(cursor.offset)
                chunk = fh.read()
                cursor.offset = fh.tell()

            data = cursor.buffer + chunk
            *lines, cursor.buffer = data.split(b"\n")
            for line in lines:
                event = _parse_line(line, service)
                if event is not None:
                    events.append(event)
        return events


def _parse_line(line: bytes, service: str) -> Optional[TelemetryEvent]:
    line = line.strip()
    if not line:
        return None
    try:
        return _DECODER.decode(line)
    except msgspec.DecodeError:
        # Not one of our JSON lines (e.g. nginx/redis/postgres native output):
        # wrap it so downstream still sees a uniform record.
        return TelemetryEvent(
            service=service,
            level="INFO",
            kind=KIND_LOG,
            message=line.decode("utf-8", errors="replace"),
        )


class FileSystemLogReader(AbstractLogReader):
    def __init__(
        self,
        directory: str | os.PathLike,
        *,
        pattern: str = "*.log.json",
        poll_interval: float = 0.5,
        from_end: bool = True,
    ) -> None:
        self._poller = _Poller(
            directory=Path(directory),
            pattern=pattern,
            from_end=from_end,
        )
        self._poll_interval = poll_interval
        self._queue: deque[TelemetryEvent] = deque()
        self._closed = False

    async def __anext__(self) -> TelemetryEvent:
        while not self._closed:
            if self._queue:
                return self._queue.popleft()

            events = await asyncio.get_running_loop().run_in_executor(
                None, self._poller.collect
            )
            if events:
                self._queue.extend(events)
                continue

            await asyncio.sleep(self._poll_interval)

        raise StopAsyncIteration

    async def aclose(self) -> None:
        self._closed = True
