import logging
import traceback as _tb
from typing import Any, Optional

from litestar import MediaType, Request
from litestar.exceptions import HTTPException
from litestar.response import (
    Response,
)
from pydantic import ValidationError
from starlette import status
from starlette.status import HTTP_400_BAD_REQUEST

from src.app.modules.telemetry.logging.event import KIND_LOG, TelemetryEvent
from src.app.modules.telemetry.logging.masking import mask_text
from src.app.modules.telemetry.logging.service_logger import (
    current_service,
    emit_event,
)
from src.app.shared_kernel.errors.app_exception import AppException
from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)
from src.app.shared_kernel.types.execution_context import ExecutionContext
from src.app.utils.environment.env_utils import DeploymentEnvironment

logger = logging.getLogger("app.exception_handler")

EXCEPTION_TO_STRING_MAX_LENGTH = 500


def _safe_context() -> Optional[ExecutionContext]:
    """Best-effort read of the execution context.

    The context is not guaranteed to be set (unauthenticated request, background
    call): ``get_context`` raises ``LookupError`` when the contextvar is unset, so
    we swallow it here - a missing context must never break the error handler.
    """
    try:
        return ExecutionContextProvider.get_context()
    except LookupError:
        return None


def _emit_error_event(
    request: Request, exc: Exception, *, status_code: int, level: str
) -> None:
    """Persist an error (with its stack) to telemetry so it is queryable in the DB.

    Complements the request-middleware event under the same ``trace_id``: this one
    carries the exception message + full traceback, so 4xx business errors - which
    previously left no detail in the DB - become retrievable. The stack lands in the
    ``telemetry_log_traceback`` side table via the Postgres writer. Never raises:
    telemetry must not break the error response.
    """
    try:
        ctx = _safe_context()
        emit_event(
            TelemetryEvent(
                service=current_service(),
                level=level,
                kind=KIND_LOG,
                trace_id=str(ctx.trace_id) if ctx and ctx.trace_id else None,
                user_id=str(ctx.user_id) if ctx and ctx.user_id else None,
                method=request.method,
                url=str(request.url),
                status_code=status_code,
                message=mask_text(str(exc)),
                traceback=mask_text(
                    "".join(_tb.format_exception(type(exc), exc, exc.__traceback__))
                ),
            )
        )
    except Exception:  # noqa: BLE001 - telemetry must never break the handler
        pass


def _format_validation_error(exc: ValidationError) -> dict:
    """Map pydantic errors to ``{field: message}`` (never echoes input values)."""
    return {
        ".".join(str(p) for p in err["loc"]) or "detail": err["msg"]
        for err in exc.errors(include_url=False)
    }


def _format_app_exception(e: AppException) -> dict | list:
    if e.details:
        if len(e.details) == 1:
            detail = e.details[0]
            if detail.field:
                return {
                    detail.field: detail.message,
                    "payload": {
                        "message": detail.message,
                        "status": detail.status,
                        **detail.payload,
                    },
                }
            else:
                return (
                    {"detail": detail.message}
                    if detail.message
                    else detail.model_dump()
                )
        else:
            if all(d.field and d.message for d in e.details):
                return {d.field: d.message for d in e.details}
            else:
                return [d.model_dump() for d in e.details]
    return {"detail": e.message}


def _app_exception_handler(request: Request, exc: AppException) -> Response:
    formatted = _format_app_exception(exc)
    return Response(
        media_type=MediaType.JSON,
        content=formatted,
        status_code=HTTP_400_BAD_REQUEST,
    )


def format_internal_server_error(exc: Exception, url: str | Any, method: str) -> dict:
    """Verbose 500 body for debug environments only - never exposed in production."""
    msg = str(exc)

    if len(msg) > EXCEPTION_TO_STRING_MAX_LENGTH:
        msg = f"{msg[:EXCEPTION_TO_STRING_MAX_LENGTH - 3]}..."

    ex_ctx = _safe_context()

    res = {
        "message": "Internal Server Error",
        "detail": msg,
        "trace_id": ex_ctx.trace_id if ex_ctx else None,
        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "user_id": ex_ctx.user_id if ex_ctx else None,
        "url": str(url),
        "method": method,
    }
    return {k: v for k, v in res.items() if v}


def exception_handler(request: Request, exc: Exception) -> Response:
    if isinstance(exc, AppException):
        # Expected 400 business errors: log at WARNING (below Telegram's ERROR/5xx
        # gate, so no spam) but persist the detail + stack for DB retrieval.
        _emit_error_event(
            request, exc, status_code=HTTP_400_BAD_REQUEST, level="WARNING"
        )
        return _app_exception_handler(request, exc)

    # Pydantic model validation raised in application code (not Litestar's own body
    # validation, which surfaces as HTTPException below). Persist + return 422.
    if isinstance(exc, ValidationError):
        _emit_error_event(
            request,
            exc,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            level="WARNING",
        )
        return Response(
            media_type=MediaType.JSON,
            content=_format_validation_error(exc),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    # Litestar's own HTTP errors (validation 400, auth 401, not-found 404, ...) are
    # expected client errors, not 500s: preserve their status/detail. Without this,
    # registering us as the catch-all would turn every 4xx into a 500. Still persist
    # them (message + context + stack) so 4xx have retrievable detail in the DB - 5xx
    # HTTPExceptions log at ERROR (reach Telegram), 4xx at WARNING (DB only).
    if isinstance(exc, HTTPException):
        _emit_error_event(
            request,
            exc,
            status_code=exc.status_code,
            level="ERROR" if exc.status_code >= 500 else "WARNING",
        )
        return Response(
            media_type=MediaType.JSON,
            content={
                k: v
                for k, v in {
                    "detail": exc.detail,
                    "extra": exc.extra,
                    "status_code": exc.status_code,
                }.items()
                if v
            },
            status_code=exc.status_code,
        )

    # Only unexpected (non-AppException) errors are real 500s. Log the cause with a
    # traceback: the telemetry formatter wraps this into an ERROR event stamped with
    # the same trace_id/user as the request middleware's event, so the two
    # rows correlate. AppExceptions are expected 4xx and are intentionally not logged.
    # Genuine unexpected 500: log at ERROR (reaches Telegram) with the full stack.
    _emit_error_event(
        request, exc, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, level="ERROR"
    )

    if DeploymentEnvironment.should_debug():
        content: dict | str = format_internal_server_error(
            exc, request.url, request.method
        )
    else:
        content = {"detail": "Internal Server Error"}

    return Response(
        media_type=MediaType.JSON,
        content=content,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
