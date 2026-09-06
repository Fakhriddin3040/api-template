from typing import Optional, Protocol, runtime_checkable

from src.app.application.identity.dto.user_dto import OtpCreateDTO, OTPDetailedDTO
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.types.base_types import ID_T


@runtime_checkable
class OtpRepositoryProto(Protocol):
    def create(self, data: OtpCreateDTO) -> None: ...

    async def find_active_by_otp(
        self,
        otp: str,
        kind: OtpKindEnum,
        content_type: ContentTypeEnum,
    ) -> Optional[OTPDetailedDTO]: ...

    async def find_active_for_content(
        self,
        otp: str,
        content_id: ID_T,
        kind: OtpKindEnum,
        content_type: ContentTypeEnum,
    ) -> Optional[OTPDetailedDTO]:
        """Same as ``find_active_by_otp`` but scoped to one owner.

        Short numeric codes are not globally unique, so any flow that mails one
        must resolve it together with the address that received it.
        """
        ...

    async def consume_by_id(self, id_: ID_T, now_epoch: int) -> bool:
        """Atomically claim an unused OTP. True only for the caller that won."""
        ...

    async def has_recent_issue(
        self,
        content_id: ID_T,
        content_type: ContentTypeEnum,
        kind: OtpKindEnum,
        cooldown_minutes: int,
    ) -> bool: ...

    async def invalidate_pending(
        self,
        content_id: ID_T,
        content_type: ContentTypeEnum,
        kind: OtpKindEnum,
        now_epoch: int,
    ) -> None: ...
