from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

from src.app.domain.identity.constants.enums import ApiKeyStatusEnum
from src.app.shared_kernel.types.base_types import ID_T


@runtime_checkable
class UserBase(Protocol):
    id: ID_T
    email: str
    password: str
    first_name: str
    last_name: str
    is_active: bool


@runtime_checkable
class ApiKeyBase(Protocol):
    id: ID_T
    owner: UserBase
    status: ApiKeyStatusEnum
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[int]
