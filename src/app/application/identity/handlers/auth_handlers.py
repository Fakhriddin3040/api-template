import logging

from src.app.application.identity.commands.auth_commands import (
    ConfirmEmailCommand,
    LoginCommand,
    RefreshTokenCommand,
    RegisterCommand,
    ResendEmailConfirmationCommand,
)
from src.app.application.identity.dto.forgot_dto import MessageResponseDTO
from src.app.application.identity.ports.services.auth_service_ports import (
    AuthServiceProto,
)
from src.app.application.identity.ports.services.registration_service_ports import (
    UserRegistrationServiceProto,
)
from src.app.application.identity.ports.services.user_confirmation_service import (
    UserConfirmationServiceProto,
)
from src.app.application.identity.validators.user_validators import RegisterValidator
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import AppExceptionStatusCodes
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.event import EventBusProto
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.types.jwt_schemas import JwtTokenDTO

logger = logging.getLogger(__name__)

# Returned whether or not the address is known, so the endpoint cannot be used
# to enumerate registered users.
_NEUTRAL_SENT = "If the address is registered, a code has been sent to it"


class RegisterCommandHandler:
    def __init__(
        self,
        validator: RegisterValidator,
        service: UserRegistrationServiceProto,
        uow: UnitOfWorkProto,
        bus: EventBusProto,
    ) -> None:
        self._validator = validator
        self._service = service
        self._uow = uow
        self._bus = bus

    async def __call__(self, message: RegisterCommand) -> ResultDetailed[None]:
        validation_res = await self._validator(cmd=message)

        if validation_res.is_err():
            return Result.err(validation_res.unwrap_err())

        async with self._uow:
            user_res = await self._service.register(cmd=message)

            if user_res.is_err():
                await self._uow.rollback()
                return Result.err(user_res.unwrap_err())

            user = user_res.unwrap()

            # Published inside the unit of work but after the aggregate is built:
            # the mail handler only reads the event's own payload, so it never
            # touches the session.
            await self._bus.publish_many(user.pull_events())

        return Result.OK


class ConfirmEmailCommandHandler:
    def __init__(
        self,
        user_repo: UserRepositoryProto,
        confirmation_service: UserConfirmationServiceProto,
        auth_service: AuthServiceProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._user_repo = user_repo
        self._confirmation_service = confirmation_service
        self._auth_service = auth_service
        self._uow = uow

    async def __call__(self, message: ConfirmEmailCommand) -> ResultDetailed[None]:
        async with self._uow:
            user = await self._user_repo.get_aggregate_for_update_by_email(
                email=message.email
            )

            if user is None:
                # Same detail the service returns for a bad code — an unknown
                # address must not be distinguishable from a wrong code.
                return Result.err(
                    [
                        AppExceptionDetail(
                            status=AppExceptionStatusCodes.INVALID_OTP,
                            field="otp",
                            message="Invalid confirmation code",
                        )
                    ]
                )

            confirm_res = await self._confirmation_service.confirm(
                content_id=user.id,
                otp=message.otp,
                kind=OtpKindEnum.EMAIL_CONFIRMATION,
            )

            if confirm_res.is_err():
                await self._uow.rollback()
                return Result.err(confirm_res.unwrap_err())

            user.confirm_email()

        return Result.OK


class ResendEmailConfirmationCommandHandler:
    def __init__(
        self,
        user_repo: UserRepositoryProto,
        confirmation_service: UserConfirmationServiceProto,
        uow: UnitOfWorkProto,
        bus: EventBusProto,
    ) -> None:
        self._user_repo = user_repo
        self._confirmation_service = confirmation_service
        self._uow = uow
        self._bus = bus

    async def __call__(
        self, message: ResendEmailConfirmationCommand
    ) -> ResultDetailed[MessageResponseDTO]:
        async with self._uow:
            user = await self._user_repo.get_aggregate_for_update_by_email(
                email=message.email
            )

            # Unknown address, or one that is already confirmed: answer exactly
            # as if a code had been sent.
            if user is None or user.email_confirmed:
                return Result.ok(MessageResponseDTO(_NEUTRAL_SENT))

            otp_res = await self._confirmation_service.issue(
                content_id=user.id,
                kind=OtpKindEnum.EMAIL_CONFIRMATION,
                target_value=user.email,
            )

            if otp_res.is_err():
                await self._uow.rollback()
                # The cooldown is a real answer to the caller, not a leak: they
                # already proved they can reach this address.
                return Result.err(otp_res.unwrap_err())

            user.mark_registered(otp_res.unwrap())

            await self._bus.publish_many(user.pull_events())

        return Result.ok(MessageResponseDTO(_NEUTRAL_SENT))


class LoginCommandHandler:
    def __init__(self, auth_service: AuthServiceProto, uow: UnitOfWorkProto) -> None:
        self._auth_service = auth_service
        self._uow = uow

    async def __call__(self, message: LoginCommand) -> ResultDetailed[JwtTokenDTO]:
        async with self._uow:
            return await self._auth_service.login(
                email=message.email, password=message.password
            )


class RefreshTokenCommandHandler:
    def __init__(self, auth_service: AuthServiceProto, uow: UnitOfWorkProto) -> None:
        self._auth_service = auth_service
        self._uow = uow

    async def __call__(
        self, message: RefreshTokenCommand
    ) -> ResultDetailed[JwtTokenDTO]:
        async with self._uow:
            return await self._auth_service.refresh(refresh_token=message.refresh_token)
