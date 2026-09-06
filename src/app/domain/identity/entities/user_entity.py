from datetime import datetime
from typing import Optional

from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.ports.domain.entity_proxy import EntityProxy
from src.app.shared_kernel.ports.domain.entity_source_proto import EntitySourceProto
from src.app.shared_kernel.types.base_types import ID_T


class UserEntity(EntityProxy):
    """The one identity row.

    There is no separate profile entity: ``first_name``/``last_name``/
    ``address``/``description``/``avatar_id`` are columns on the user, so a
    caller never has to know whether a user "has a profile yet".
    """

    id: ID_T
    email: str
    password: str
    phone: Optional[str]
    first_name: str
    last_name: str
    address: Optional[str]
    description: Optional[str]
    avatar_id: Optional[ID_T]
    information: Optional[str]
    email_confirmed: bool
    is_active: bool
    is_superuser: bool
    last_login_time: Optional[datetime]

    def __init__(self, source: EntitySourceProto):
        object.__setattr__(
            self,
            "_proxy_fields",
            {
                "id",
                "email",
                "password",
                "phone",
                "first_name",
                "last_name",
                "address",
                "description",
                "avatar_id",
                "information",
                "email_confirmed",
                "is_active",
                "is_superuser",
                "last_login_time",
            },
        )
        super().__init__(
            source=source,
        )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class OtpEntity(EntityProxy):
    otp: str
    content_id: ID_T
    content_type: ContentTypeEnum
    kind: OtpKindEnum
    expires_at: int
    used_at: Optional[int]
    target_value: str
    verified: bool

    def __init__(self, source: EntitySourceProto):
        object.__setattr__(
            self,
            "_proxy_fields",
            {
                "otp",
                "content_id",
                "content_type",
                "kind",
                "expires_at",
                "used_at",
                "target_value",
                "verified",
            },
        )
        super().__init__(source)
