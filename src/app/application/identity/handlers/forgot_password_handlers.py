import logging

from src.app.application.identity.commands.forgot_commands import (
    ForgotPasswordStep1Command,
    ForgotPasswordStep2Command,
    ForgotPasswordStep3Command,
)
from src.app.application.identity.dto.forgot_dto import (
    ForgotPasswordStep1ResponseDTO,
    ForgotPasswordStep2ResponseDTO,
    ForgotPasswordStep3ResponseDTO,
)
from src.app.application.identity.ports.services.registration_service_ports import (
    ForgotPasswordServiceProto,
)
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.repositories.otp_repository import OtpRepositoryProto
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.event import EventBusProto
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.ports.services import ClockProto

logger = logging.getLogger(__name__)

_NEUTRAL_SENT = "If the address is registered, a reset code has been sent to it"


def _invalid_otp() -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.INVALID_OTP,
        field="otp",
        message=AppExceptionMessage.INVALID_OTP,
    )


class ForgotPasswordStep1CommandHandler:
    """Ask for a reset code.

    Answers identically for a known and an unknown address: a password-reset
    form is the easiest place to enumerate accounts.
    """

    def __init__(
        self,
        user_repo: UserRepositoryProto,
        service: ForgotPasswordServiceProto,
        uow: UnitOfWorkProto,
        bus: EventBusProto,
    ) -> None:
        self._user_repo = user_repo
        self._service = service
        self._uow = uow
        self._bus = bus

    async def __call__(
        self, message: ForgotPasswordStep1Command
    ) -> ResultDetailed[ForgotPasswordStep1ResponseDTO]:
        async with self._uow:
            user_aggr = await self._user_repo.get_for_password_reset(
                email=message.email
            )

            if user_aggr is None:
                return Result.ok(ForgotPasswordStep1ResponseDTO(_NEUTRAL_SENT))

            issue_res = await self._service.issue_reset_code(user_aggr=user_aggr)

            if issue_res.is_err():
                await self._uow.rollback()
                return Result.err(issue_res.unwrap_err())

            await self._bus.publish_many(user_aggr.pull_events())

        return Result.ok(ForgotPasswordStep1ResponseDTO(_NEUTRAL_SENT))


class ForgotPasswordStep2CommandHandler:
    """Check the code without spending it, and say who it belongs to.

    Verification and consumption are deliberately split: the user has to see
    whose account they are resetting before they choose a new password, and a
    mistyped password on step 3 must not burn the code.
    """

    def __init__(
        self,
        user_repo: UserRepositoryProto,
        otp_repo: OtpRepositoryProto,
        clock: ClockProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._user_repo = user_repo
        self._otp_repo = otp_repo
        self._clock = clock
        self._uow = uow

    async def __call__(
        self, message: ForgotPasswordStep2Command
    ) -> ResultDetailed[ForgotPasswordStep2ResponseDTO]:
        async with self._uow:
            found = await self._user_repo.get_by_email_for_password_recovery(
                email=message.email
            )

            if not found:
                return Result.err([_invalid_otp()])

            otp = await self._otp_repo.find_active_for_content(
                message.otp,
                content_id=found.id,
                kind=OtpKindEnum.FORGOT_PASSWORD,
                content_type=ContentTypeEnum.USER,
            )

            if otp is None or otp.used_at is not None:
                return Result.err([_invalid_otp()])

            if otp.expires_at < int(self._clock.get_utc_epoch()):
                return Result.err(
                    [
                        AppExceptionDetail(
                            status=AppExceptionStatusCodes.OTP_EXPIRED,
                            field="otp",
                            message=AppExceptionMessage.OTP_EXPIRED,
                        )
                    ]
                )

            return Result.ok(found)


class ForgotPasswordStep3CommandHandler:
    """Spend the code and set the new password."""

    def __init__(
        self,
        password_service: PasswordServiceProto,
        user_repo: UserRepositoryProto,
        service: ForgotPasswordServiceProto,
        otp_repo: OtpRepositoryProto,
        clock: ClockProto,
        uow: UnitOfWorkProto,
        bus: EventBusProto,
    ) -> None:
        self._password_service = password_service
        self._user_repo = user_repo
        self._service = service
        self._otp_repo = otp_repo
        self._clock = clock
        self._uow = uow
        self._bus = bus

    async def __call__(
        self, message: ForgotPasswordStep3Command
    ) -> ResultDetailed[ForgotPasswordStep3ResponseDTO]:
        async with self._uow:
            user_aggr = await self._user_repo.get_for_password_reset(
                email=message.email
            )

            if user_aggr is None:
                return Result.err([_invalid_otp()])

            otp = await self._otp_repo.find_active_for_content(
                message.otp,
                content_id=user_aggr.id,
                kind=OtpKindEnum.FORGOT_PASSWORD,
                content_type=ContentTypeEnum.USER,
            )

            if otp is None:
                return Result.err([_invalid_otp()])

            if otp.expires_at < int(self._clock.get_utc_epoch()):
                return Result.err(
                    [
                        AppExceptionDetail(
                            status=AppExceptionStatusCodes.OTP_EXPIRED,
                            field="otp",
                            message=AppExceptionMessage.OTP_EXPIRED,
                        )
                    ]
                )

            # Consume first: this is the atomic step, and a racing request that
            # also passed the checks above must not get a second reset.
            if not await self._otp_repo.consume_by_id(
                otp.id, int(self._clock.get_utc_epoch())
            ):
                await self._uow.rollback()
                return Result.err([_invalid_otp()])

            user_aggr.set_password(message.new_password, self._password_service)
            self._service.announce_password_changed(
                user_aggr=user_aggr, new_password=message.new_password
            )

            await self._bus.publish_many(user_aggr.pull_events())

        return Result.ok(ForgotPasswordStep3ResponseDTO("Password updated"))
