from uuid import uuid4

from src.app.application.identity.commands.auth_commands import RegisterCommand
from src.app.application.identity.ports.services.registration_service_ports import (
    ForgotPasswordServiceProto,
    UserRegistrationServiceProto,
)
from src.app.application.identity.ports.services.user_confirmation_service import (
    UserConfirmationServiceProto,
)
from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.events import ForgotPasswordStep1Event
from src.app.domain.identity.params.user_params import UserCreateParams
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.factories.entity_source_factory import (
    EntitySourceFactoryProto,
)
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.ports.services import ClockProto
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class UserRegistrationService(UserRegistrationServiceProto):
    """Builds the user for a self-service signup and issues its email code.

    The caller owns the transaction; this only flushes, because the OTP and the
    registration event both need the freshly assigned id.
    """

    def __init__(
        self,
        user_repo: UserRepositoryProto,
        confirmation_service: UserConfirmationServiceProto,
        password_service: PasswordServiceProto,
        source_factory: EntitySourceFactoryProto,
        clock: ClockProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._user_repo = user_repo
        self._confirmation_service = confirmation_service
        self._password_service = password_service
        self._source_factory = source_factory
        self._clock = clock
        self._uow = uow

    async def register(self, cmd: RegisterCommand) -> ResultDetailed[UserAggregate]:
        user = UserAggregate.register(
            param=UserCreateParams(
                email=cmd.email,
                first_name=cmd.first_name,
                last_name=cmd.last_name,
                phone=cmd.phone,
                address=cmd.address,
            ),
            source_factory=self._source_factory,
            clock=self._clock,
        )
        user.set_password(cmd.password, self._password_service)

        self._user_repo.create(obj=user)

        # The OTP row references the user id, so the insert has to have happened.
        await self._uow.flush()

        otp_res = await self._confirmation_service.issue(
            content_id=user.id,
            kind=OtpKindEnum.EMAIL_CONFIRMATION,
            target_value=user.email,
        )

        if otp_res.is_err():
            return Result.err(otp_res.unwrap_err())

        user.mark_registered(otp_res.unwrap())

        return Result.ok(user)


class ForgotPasswordService(ForgotPasswordServiceProto):
    def __init__(
        self,
        confirmation_service: UserConfirmationServiceProto,
    ) -> None:
        self._confirmation_service = confirmation_service

    async def issue_reset_code(self, user_aggr: UserAggregate) -> ResultDetailed[None]:
        otp_res = await self._confirmation_service.issue(
            content_id=user_aggr.id,
            kind=OtpKindEnum.FORGOT_PASSWORD,
            target_value=user_aggr.email,
        )

        if otp_res.is_err():
            return Result.err(otp_res.unwrap_err())

        user_aggr.add_domain_event(
            ForgotPasswordStep1Event(
                event_id=uuid4(),
                aggregate_id=user_aggr.id,
                recipient=user_aggr.email,
                otp_code=otp_res.unwrap(),
            )
        )

        return Result.OK

    def announce_password_changed(
        self, user_aggr: UserAggregate, new_password: str
    ) -> None:
        from src.app.domain.identity.events import ForgotPasswordStep2Event

        user_aggr.add_domain_event(
            ForgotPasswordStep2Event(
                event_id=uuid4(),
                aggregate_id=user_aggr.id,
                recipient=user_aggr.email,
                new_password=new_password,
                full_name=user_aggr.full_name,
            )
        )


ensure_isimplementation(UserRegistrationService, UserRegistrationServiceProto)
ensure_isimplementation(ForgotPasswordService, ForgotPasswordServiceProto)
