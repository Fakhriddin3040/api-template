from datetime import datetime
from typing import Optional

import msgspec

from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.pydantic.types import BasePydanticModel
from src.app.shared_kernel.types.base_types import ID_T


class OtpCreateDTO(BasePydanticModel):
    otp: str
    content_id: ID_T
    content_type: ContentTypeEnum
    kind: OtpKindEnum
    # Unix epoch seconds. int, not float — the column is BIGINT, and pydantic
    # rejects a fractional float for an int field, so callers must coerce the
    # clock's float epoch explicitly rather than truncate by accident.
    expires_at: int
    target_value: str
    verified: Optional[bool] = False


class OTPDetailedDTO(BasePydanticModel):
    id: ID_T
    otp: str
    content_id: ID_T
    expires_at: int
    target_value: str
    verified: bool
    used_at: Optional[int] = None


class UserCredentialsDTO(msgspec.Struct):
    """Minimal identity returned by activation / resend flows, so a handler can
    mail the user without reloading the aggregate."""

    id: ID_T
    email: str
    full_name: str


class UserAuthDTO(msgspec.Struct):
    """Everything the login path needs: the hash to verify against and the flags
    that decide whether the account may be used at all."""

    id: ID_T
    email: str
    password: str
    is_active: bool
    email_confirmed: bool
    last_login_time: Optional[datetime] = None


class UserListDTO(msgspec.Struct):
    id: ID_T
    email: str
    full_name: str
    status: int
    created_at: datetime
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserDetailedDTO(msgspec.Struct):
    id: ID_T
    email: str
    full_name: str
    status: int
    created_at: datetime
    updated_at: datetime
    email_confirmed: bool
    is_active: bool
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    information: Optional[str] = None
    avatar_url: Optional[str] = None
    last_login_time: Optional[datetime] = None
