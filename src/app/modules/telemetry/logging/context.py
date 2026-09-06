"""Best-effort extraction of the current request context for plain log records.

Consulted so that a bare ``logging.info(...)`` still gets tagged with the active
``trace_id`` / ``user_id`` when there is one.
"""

from __future__ import annotations

from typing import Optional, Tuple


def current_context() -> Tuple[Optional[str], Optional[str]]:
    """Return ``(trace_id, user_id)`` for the active request, if any."""
    try:
        from src.app.shared_kernel.providers.execution_context_provider import (
            ExecutionContextProvider,
        )

        ctx = ExecutionContextProvider.get_context()
        if ctx is not None:
            trace_id = str(ctx.trace_id) if ctx.trace_id else None
            user_id = str(ctx.user_id) if ctx.user_id else None
            return trace_id, user_id
    except Exception:  # noqa: BLE001 - context is optional, never break logging
        pass

    return None, None
