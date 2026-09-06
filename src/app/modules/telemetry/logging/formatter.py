"""Turns a ``logging.LogRecord`` into a single masked JSON line."""

from __future__ import annotations

import logging

import msgspec

from src.app.modules.telemetry.logging.context import current_context
from src.app.modules.telemetry.logging.event import KIND_LOG, TelemetryEvent
from src.app.modules.telemetry.logging.masking import mask, mask_text

_ENCODER = msgspec.json.Encoder()


class TelemetryJsonFormatter(logging.Formatter):
    """Formats records emitted anywhere in the process.

    Two shapes are supported on the same handler:

    * structured events - middleware attaches a ready ``TelemetryEvent`` via
      ``extra={"telemetry_event": event}``; it is serialised as-is (already masked);
    * plain records - any ``logging.*`` call is wrapped into a ``TelemetryEvent``
      of ``kind="log"`` with secrets stripped from the rendered message.
    """

    def __init__(self, service: str) -> None:
        super().__init__()
        self._service = service

    def format(self, record: logging.LogRecord) -> str:
        event = getattr(record, "telemetry_event", None)

        if isinstance(event, TelemetryEvent):
            return _ENCODER.encode(event).decode("utf-8")

        trace_id, user_id = current_context()
        event = TelemetryEvent(
            service=self._service,
            level=record.levelname,
            kind=KIND_LOG,
            epoch=record.created,
            trace_id=trace_id,
            user_id=user_id,
            logger=record.name,
            message=mask_text(record.getMessage()),
        )

        if record.exc_info:
            # Keep the stack out of ``message`` - it is stored in its own column /
            # side table. Masked, same as everything else that hits disk.
            event.traceback = mask_text(self.formatException(record.exc_info))

        # Structured extras (record.__dict__ minus stdlib fields) get masked too.
        extras = _extract_extras(record)
        if extras:
            event.data = mask(extras)

        return _ENCODER.encode(event).decode("utf-8")


_RESERVED = frozenset(logging.makeLogRecord({}).__dict__.keys()) | {
    "message",
    "asctime",
    "telemetry_event",
    "taskName",
}


def _extract_extras(record: logging.LogRecord) -> dict:
    return {
        key: value for key, value in record.__dict__.items() if key not in _RESERVED
    }
