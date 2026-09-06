"""Litestar/ASGI request telemetry middleware (modern ``/api/v2`` path).

Wraps ``receive``/``send`` to capture the (bounded) request body and the response
status, then emits one structured event per request to ``logs/api.log``. Replaces
the old ad-hoc ``PerfMiddleware`` logging. Must sit after ``AuthMiddleware`` so the
execution context (trace_id/user) is populated.
"""

from __future__ import annotations

import time
from typing import Optional, cast

from litestar.types import ASGIApp, Receive, Scope, Send

from src.app.modules.telemetry.integrations.http import (
    MAX_BODY_BYTES,
    build_http_event,
    should_capture_body,
)
from src.app.modules.telemetry.logging.context import current_context
from src.app.modules.telemetry.logging.event import SERVICE_API
from src.app.modules.telemetry.logging.service_logger import emit_event


class TelemetryMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        start = time.perf_counter()
        headers = _headers(scope)
        content_type = headers.get("content-type")
        capture = should_capture_body(content_type)
        body_buf = bytearray()
        status: dict[str, Optional[int]] = {"code": None}

        async def receive_wrapper():
            message = await receive()
            if message["type"] == "http.request" and len(body_buf) < MAX_BODY_BYTES:
                chunk = message.get("body", b"")
                if chunk:
                    body_buf.extend(chunk[: MAX_BODY_BYTES - len(body_buf)])
            return message

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive_wrapper if capture else receive, send_wrapper)
        finally:
            exec_ms = (time.perf_counter() - start) * 1000
            trace_id, user_id = current_context()
            url = f"{scope.get('root_path', '')}{scope.get('path', '')}"
            try:
                emit_event(
                    build_http_event(
                        service=SERVICE_API,
                        method=scope.get("method"),
                        url=url,
                        query_string=cast(bytes, scope.get("query_string", b"")),
                        body=bytes(body_buf) if capture else None,
                        content_type=content_type,
                        status_code=status["code"],
                        exec_ms=exec_ms,
                        ip=_client_ip(scope, headers),
                        user_agent=headers.get("user-agent"),
                        trace_id=trace_id,
                        user_id=user_id,
                    )
                )
            except Exception:  # noqa: BLE001 - telemetry must never break the response
                pass


def _headers(scope: Scope) -> dict[str, str]:
    return {
        key.decode("latin-1").lower(): value.decode("latin-1")
        for key, value in scope.get("headers") or []
    }


def _client_ip(scope: Scope, headers: dict[str, str]) -> Optional[str]:
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = scope.get("client")
    return client[0] if client else None
