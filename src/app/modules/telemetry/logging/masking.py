"""Secret masking for telemetry.

Single source of truth for redacting sensitive values before anything is written
to disk. Applied both to structured payloads (json body / query params) and to
plain ``logging`` messages.
"""

from __future__ import annotations

import re
from typing import Any

REDACTED = "***"
OMITTED = "<omitted>"

# Keys whose *values* must never be logged. Matched as a substring, case-insensitive,
# so ``refresh_token``, ``X-Authorization``, ``access_token`` etc. are all covered.
_SENSITIVE_KEY_RE = re.compile(
    r"pass|pwd|token|secret|authorization|refresh|access|api[_-]?key|cvv|card",
    re.IGNORECASE,
)

# ``key=value`` / ``key: value`` occurrences inside a free-form string.
_TEXT_SECRET_RE = re.compile(
    r"((?:password|passwd|pwd|token|secret|authorization|refresh|access|api[_-]?key)"
    r"[\"']?\s*[=:]\s*[\"']?)([^\s,;\"'&]+)",
    re.IGNORECASE,
)

# ``data:<mime>;base64,....`` inline payloads (images / files).
_DATA_URI_RE = re.compile(r"^data:[^;,]*;base64,", re.IGNORECASE)

# Strings longer than this are treated as opaque binary/base64 blobs and dropped.
_MAX_STR_LEN = 4096
_MAX_DEPTH = 32


def _is_sensitive_key(key: Any) -> bool:
    return isinstance(key, str) and bool(_SENSITIVE_KEY_RE.search(key))


def _looks_binary(value: Any) -> bool:
    if isinstance(value, (bytes, bytearray, memoryview)):
        return True
    if isinstance(value, str):
        return bool(_DATA_URI_RE.match(value)) or len(value) > _MAX_STR_LEN
    return False


def mask(obj: Any, *, _depth: int = 0) -> Any:
    """Recursively redact secrets and drop binary/base64 blobs in ``obj``."""
    if _depth > _MAX_DEPTH:
        return obj

    if isinstance(obj, dict):
        out: dict[Any, Any] = {}
        for key, value in obj.items():
            if _is_sensitive_key(key):
                out[key] = REDACTED
            elif _looks_binary(value):
                out[key] = OMITTED
            else:
                out[key] = mask(value, _depth=_depth + 1)
        return out

    if isinstance(obj, (list, tuple)):
        return [mask(item, _depth=_depth + 1) for item in obj]

    if _looks_binary(obj):
        return OMITTED

    return obj


def mask_text(text: str) -> str:
    """Redact ``key=secret`` / ``key: secret`` pairs inside a free-form string."""
    if not text:
        return text
    return _TEXT_SECRET_RE.sub(lambda m: f"{m.group(1)}{REDACTED}", text)
