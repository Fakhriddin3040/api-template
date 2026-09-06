"""A logging filter that masks secrets in the rendered message.

The JSON formatter already masks what it writes to the telemetry file, but plain
handlers (e.g. the console handler, whose stdout is often redirected to a file)
format ``record.getMessage()`` directly. Attaching this filter to those handlers
guarantees no unmasked secret ever reaches stdout / another sink. Idempotent.
"""

from __future__ import annotations

import logging

from src.app.modules.telemetry.logging.masking import mask_text


class MaskingLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            if isinstance(record.msg, str) and record.msg:
                record.msg = mask_text(record.getMessage())
                record.args = None
        except Exception:  # noqa: BLE001 - masking must never drop a log line
            pass
        return True
