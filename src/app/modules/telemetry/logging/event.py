"""The canonical telemetry record.

One ``TelemetryEvent`` == one line in ``logs/<service>.log``. It is serialised to
JSON by :class:`TelemetryJsonFormatter` and parsed back by the reader daemon, so
producer and consumer share this single schema.
"""

from __future__ import annotations

import time
from typing import Any, Optional

import msgspec

# Well-known service names (one file per service). Free-form: any string is allowed,
# these are just the canonical ones referenced across the codebase / compose.
SERVICE_API = "api"
SERVICE_BEAT = "beat"
SERVICE_WORKER = "worker"
SERVICE_PROXY = "proxy"
SERVICE_DB = "db"
SERVICE_REDIS = "redis"

# ``kind`` generalises the table for future traces (not only http requests).
KIND_HTTP_REQUEST = "http_request"
KIND_LOG = "log"
KIND_SYSTEM = "system"


class TelemetryEvent(msgspec.Struct, omit_defaults=True, forbid_unknown_fields=False):
    service: str
    level: str = "INFO"
    kind: str = KIND_HTTP_REQUEST
    # Seconds since epoch (float). The DB writer derives the timestamptz from it.
    epoch: float = msgspec.field(default_factory=time.time)
    trace_id: Optional[str] = None
    exec_ms: Optional[float] = None
    # Stringified: ids are UUIDs, and telemetry must not depend on the id type
    # of whatever produced the event.
    user_id: Optional[str] = None
    ip: Optional[str] = None
    method: Optional[str] = None
    url: Optional[str] = None
    url_params: Optional[dict[str, Any]] = None
    data: Optional[Any] = None
    status_code: Optional[int] = None
    user_agent: Optional[str] = None
    logger: Optional[str] = None
    message: Optional[str] = None
    # Full formatted stack trace. Stored out-of-line in ``telemetry_log_traceback``
    # (keyed by the parent row id) so the main table stays lean.
    traceback: Optional[str] = None
