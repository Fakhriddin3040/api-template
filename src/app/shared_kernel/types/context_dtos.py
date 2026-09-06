"""Detached, session-independent identity DTOs for the execution context.

These structurally satisfy the :mod:`entities` protocols (``UserBase``) so they
can be stored on the :class:`ExecutionContext` in place of ORM models. Being
plain frozen values (no SQLAlchemy state), reading their attributes never
triggers a lazy refresh - so the context survives a rolled-back / closed session
without ``DetachedInstanceError``.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.app.shared_kernel.types.base_types import ID_T


@dataclass(frozen=True, slots=True)
class UserOnContextDTO:
    id: ID_T
    email: str
    first_name: str
    last_name: str
    is_active: bool
    # Never carries the real credential - present only to satisfy ``UserBase``.
    password: str = ""

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
