"""Shared helpers for building an http :class:`TelemetryEvent` from a request.

Used by both the litestar and django middlewares so the two entrypoints emit an
identical, already-masked record shape.
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from urllib.parse import parse_qs

import msgspec

from src.app.modules.telemetry.logging.event import KIND_HTTP_REQUEST, TelemetryEvent
from src.app.modules.telemetry.logging.masking import mask

MAX_BODY_BYTES = 16 * 1024  # cap what we buffer/log per request body

_JSON_CT = "application/json"
_SKIP_BODY_CT = ("multipart/form-data", "application/octet-stream")


def should_capture_body(content_type: Optional[str]) -> bool:
    if not content_type:
        return False
    ct = content_type.lower()
    if any(skip in ct for skip in _SKIP_BODY_CT):
        return False
    return _JSON_CT in ct


def level_for_status(status_code: Optional[int]) -> str:
    if status_code is None:
        return "INFO"
    if status_code >= 500:
        return "ERROR"
    if status_code >= 400:
        return "WARNING"
    return "INFO"


def parse_query(query_string: bytes | str | None) -> Optional[dict[str, Any]]:
    if not query_string:
        return None
    if isinstance(query_string, bytes):
        query_string = query_string.decode("latin-1")
    parsed = parse_qs(query_string, keep_blank_values=True)
    flat = {k: (v[0] if len(v) == 1 else v) for k, v in parsed.items()}
    return mask(flat) or None


def parse_json_body(
    body: Optional[bytes], content_type: Optional[str]
) -> Optional[Any]:
    if not body or not should_capture_body(content_type):
        return None
    try:
        return mask(msgspec.json.decode(body))
    except (msgspec.DecodeError, ValueError):
        return None


def build_http_event(
    *,
    service: str,
    method: Optional[str],
    url: Optional[str],
    query_string: bytes | str | None,
    body: Optional[bytes],
    content_type: Optional[str],
    status_code: Optional[int],
    exec_ms: Optional[float],
    ip: Optional[str],
    user_agent: Optional[str],
    trace_id: Optional[str],
    user_id: Optional[str],
) -> TelemetryEvent:
    return TelemetryEvent(
        service=service,
        kind=KIND_HTTP_REQUEST,
        level=level_for_status(status_code),
        trace_id=trace_id,
        exec_ms=exec_ms,
        user_id=user_id,
        ip=ip,
        method=method,
        url=url,
        url_params=parse_query(query_string),
        data=parse_json_body(body, content_type),
        status_code=status_code,
        user_agent=user_agent,
    )


logger = logging.getLogger("telemetry.http")
