"""UUIDv7 generation.

``uuid.uuid7`` is stdlib only from Python 3.14. Until the project's floor moves
there, this module provides the same value shape: a 128-bit UUID whose first 48
bits are the Unix timestamp in milliseconds, which makes generated ids
monotonically ordered — so they behave like a sequence for B-tree locality while
remaining unguessable.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Callable

_stdlib_uuid7: Callable[[], uuid.UUID] | None = getattr(uuid, "uuid7", None)


def _uuid7_fallback() -> uuid.UUID:
    unix_ms = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")

    # rand_a (12 bits) | rand_b (62 bits); version/variant bits are stamped below.
    rand_a = (rand >> 62) & 0x0FFF
    rand_b = rand & 0x3FFF_FFFF_FFFF_FFFF

    value = (unix_ms & 0xFFFF_FFFF_FFFF) << 80
    value |= 0x7 << 76  # version 7
    value |= rand_a << 64
    value |= 0b10 << 62  # RFC 4122 variant
    value |= rand_b

    return uuid.UUID(int=value)


def uuid7() -> uuid.UUID:
    """A time-ordered UUIDv7. Defers to the stdlib implementation on 3.14+."""
    return _stdlib_uuid7() if _stdlib_uuid7 is not None else _uuid7_fallback()
