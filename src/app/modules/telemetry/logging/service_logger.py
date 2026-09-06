"""File sink for telemetry: one rotating ``logs/<service>.log`` per service.

This is the *only* place a request/log event goes inside the api/web process -
a local file append. No network, no DB, so it can never delay a transaction. The
separate reader daemon tails these files and fans out to Telegram/Postgres.

Wiring:
* Django processes configure the handler through ``LOGGING`` (dictConfig), which
  creates a *single* shared :class:`TelemetryLogHandler` instance referenced by
  root, the django loggers and the ``telemetry.event`` logger - so there is never
  a second handler racing on the same file.
* Non-django processes call :func:`install_root_handler` to attach one to root.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from src.app.modules.telemetry.logging.event import TelemetryEvent
from src.app.modules.telemetry.logging.formatter import TelemetryJsonFormatter

_DEFAULT_LOG_DIR = "logs"
_DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # a few MB, then rotate
_DEFAULT_BACKUP_COUNT = 5

# Events are emitted through this logger; dictConfig / install_root_handler routes
# it to the telemetry file handler.
EVENT_LOGGER_NAME = "telemetry.event"


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _log_dir() -> Path:
    path = Path(os.getenv("TELEMETRY_LOG_DIR", _DEFAULT_LOG_DIR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def current_service() -> str:
    return os.getenv("TELEMETRY_SERVICE", "api")


class TelemetryLogHandler(RotatingFileHandler):
    """Rotating file handler pre-wired with the JSON formatter for one service.

    Usable both programmatically and from a Django ``LOGGING`` dict (extra keys in
    the handler config are passed here as kwargs). ``service`` defaults to the
    ``TELEMETRY_SERVICE`` env var so one config works for every process.
    """

    def __init__(
        self,
        service: Optional[str] = None,
        filename: Optional[str] = None,
        maxBytes: Optional[int] = None,
        backupCount: Optional[int] = None,
        encoding: str = "utf-8",
        delay: bool = True,
    ) -> None:
        service = service or current_service()
        target = filename or str(_log_dir() / service / f"{service}.log.json")
        parent_dir = Path(target).parent

        if not parent_dir.exists():
            parent_dir.mkdir(parents=True, exist_ok=True)
        elif not parent_dir.is_dir():
            raise RuntimeError(f"Expected a directory at {str(parent_dir)}")

        target_p = Path(target)

        if target_p.exists() and not target_p.is_file():
            raise RuntimeError(f"Expected a file at {str(target_p)}")

        super().__init__(
            target,
            maxBytes=(
                maxBytes
                if maxBytes is not None
                else _env_int("TELEMETRY_MAX_BYTES", _DEFAULT_MAX_BYTES)
            ),
            backupCount=(
                backupCount
                if backupCount is not None
                else _env_int("TELEMETRY_BACKUP_COUNT", _DEFAULT_BACKUP_COUNT)
            ),
            encoding=encoding,
            delay=delay,
        )
        self.service = service
        self.setFormatter(TelemetryJsonFormatter(service=service))


def emit_event(event: TelemetryEvent) -> None:
    """Write an already-built (masked) telemetry event to its service file."""
    logger = logging.getLogger(EVENT_LOGGER_NAME)
    level = logging.getLevelName(event.level)
    if not isinstance(level, int):
        level = logging.INFO
    logger.log(level, "", extra={"telemetry_event": event})


def install_root_handler(service: Optional[str] = None) -> None:
    """Attach the telemetry file handler to the root logger (idempotent).

    For litestar/uvicorn and any non-django process. In django processes the
    dictConfig already installed an equivalent handler, so this is a no-op there.
    """
    if service:
        os.environ.setdefault("TELEMETRY_SERVICE", service)

    from src.app.modules.telemetry.logging.filter import MaskingLogFilter

    root = logging.getLogger()
    if root.level == logging.NOTSET or root.level > logging.INFO:
        root.setLevel(logging.INFO)

    # Mask secrets on pre-existing plain handlers (e.g. basicConfig stdout).
    mask = MaskingLogFilter()
    for handler in root.handlers:
        if not isinstance(handler, TelemetryLogHandler) and not any(
            isinstance(f, MaskingLogFilter) for f in handler.filters
        ):
            handler.addFilter(mask)

    if not any(isinstance(h, TelemetryLogHandler) for h in root.handlers):
        root.addHandler(TelemetryLogHandler())

    logging.getLogger(EVENT_LOGGER_NAME).setLevel(logging.DEBUG)
