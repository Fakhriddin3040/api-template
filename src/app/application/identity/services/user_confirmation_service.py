from typing import Mapping, Type
from uuid import uuid4

from src.app.application.identity.dto.user_dto import OtpCreateDTO
from src.app.application.identity.ports.services.otp_generator import OTPGenerator
from src.app.application.identity.ports.services.user_confirmation_service import (
    UserConfirmationServiceProto,
)
from src.app.domain.identity.constants.consts import (
    otp_cooldown_minutes,
    otp_ttl_minutes,
)
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.events import (
    UserConfirmedEvent,
    UserEmailConfirmedEvent,
)
from src.app.domain.identity.repositories.otp_repository import OtpRepositoryProto
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.event import EventBusProto
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.services import ClockProto
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

# What each kind announces once it is confirmed. Adding a kind to this map is the
# whole cost of supporting a new confirmation.
#
# Deliberately not exhaustive over OtpKindEnum: FORGOT_PASSWORD is a three-phase
# flow whose code is verified and then spent by its own handlers, so claiming it
# here would be a lie.
_EVENT_BY_KIND: Mapping[OtpKindEnum, Type[UserConfirmedEvent]] = {
    OtpKindEnum.EMAIL_CONFIRMATION: UserEmailConfirmedEvent,
}


def _invalid_otp() -> AppExceptionDetail:
    # Deliberately identical for "no such OTP" and "wrong kind": distinguishing
    # them would let a caller probe which codes exist.
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.INVALID_OTP,
        field="otp",
        message=AppExceptionMessage.INVALID_OTP,
    )


def _already_used() -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.OTP_ALREADY_VERIFIED,
        field="otp",
        message=AppExceptionMessage.OTP_ALREADY_VERIFIED,
    )


def _expired() -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.OTP_EXPIRED,
        field="otp",
        message=AppExceptionMessage.OTP_EXPIRED,
    )


def _cooldown(minutes: int) -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.OTP_RESEND_COOLDOWN,
        message=f"A new code can be requested once every {minutes} min.",
    )


class UserConfirmationService(UserConfirmationServiceProto):
    """Owns the whole rule set for user confirmations.

    The caller owns the transaction — nothing here opens a unit of work — so a
    command handler and any future batch caller share one code path.
    """

    # This service is the user boundary; nothing else may resolve through it.
    _CONTENT_TYPE = ContentTypeEnum.USER

    def __init__(
        self,
        otp_repo: OtpRepositoryProto,
        otp_generator: OTPGenerator,
        clock: ClockProto,
        bus: EventBusProto,
    ) -> None:
        self._otp_repo = otp_repo
        self._otp_generator = otp_generator
        self._clock = clock
        self._bus = bus

    async def issue(
        self,
        *,
        content_id: ID_T,
        kind: OtpKindEnum,
        target_value: str,
    ) -> ResultDetailed[str]:
        cooldown = otp_cooldown_minutes(kind)

        # Checked *before* invalidate_pending: rejecting after would have burned
        # the caller's still-valid code as a side effect of a refused resend.
        if await self._otp_repo.has_recent_issue(
            content_id=content_id,
            content_type=self._CONTENT_TYPE,
            kind=kind,
            cooldown_minutes=cooldown,
        ):
            return Result.err([_cooldown(cooldown)])

        now = int(self._clock.get_utc_epoch())

        await self._otp_repo.invalidate_pending(
            content_id=content_id,
            content_type=self._CONTENT_TYPE,
            kind=kind,
            now_epoch=now,
        )

        code = self._otp_generator()

        self._otp_repo.create(
            OtpCreateDTO(
                otp=code,
                content_id=content_id,
                content_type=self._CONTENT_TYPE,
                kind=kind,
                expires_at=now + otp_ttl_minutes(kind) * 60,
                target_value=target_value,
                verified=False,
            )
        )

        return Result.ok(code)

    async def confirm(
        self,
        *,
        content_id: ID_T,
        otp: str,
        kind: OtpKindEnum,
    ) -> ResultDetailed[ID_T]:
        event_type = _EVENT_BY_KIND.get(kind)

        if event_type is None:
            raise RuntimeError(
                f"{kind!r} has no confirmation event; it is not served by this service."
            )

        found = await self._otp_repo.find_active_for_content(
            otp,
            content_id=content_id,
            kind=kind,
            content_type=self._CONTENT_TYPE,
        )

        if found is None:
            return Result.err([_invalid_otp()])

        if found.used_at is not None or found.verified:
            return Result.err([_already_used()])

        if found.expires_at < int(self._clock.get_utc_epoch()):
            return Result.err([_expired()])

        # The checks above are advisory; this is the one that decides. A racing
        # request that also passed them will fail here, so only one wins.
        if not await self._otp_repo.consume_by_id(
            found.id, int(self._clock.get_utc_epoch())
        ):
            return Result.err([_already_used()])

        await self._bus.publish(
            event_type(
                event_id=uuid4(),
                aggregate_id=found.content_id,
                target_value=found.target_value,
            )
        )

        return Result.ok(found.content_id)


ensure_isimplementation(UserConfirmationService, UserConfirmationServiceProto)
