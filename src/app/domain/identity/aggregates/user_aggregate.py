from typing import Self
from uuid import uuid4

from src.app.domain.identity.events import UserRegisteredEvent
from src.app.domain.identity.params.user_params import (
    UserCreateParams,
    UserUpdateParams,
)
from src.app.domain.identity.entities.user_entity import UserEntity
from src.app.shared_kernel.constants.common_enums import StatusEnum
from src.app.shared_kernel.constants.models_fields.identity_model_fields import (
    UserField,
)
from src.app.shared_kernel.ports.domain.aggregate_root import AggregateRoot
from src.app.shared_kernel.ports.domain.entity_source_proto import EntitySourceProto
from src.app.shared_kernel.ports.factories.entity_source_factory import (
    EntitySourceFactoryProto,
)
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.ports.services import ClockProto


class UserAggregate(UserEntity, AggregateRoot):
    """The identity aggregate root — one user, profile fields included.

    Two ways in: ``register`` (self-service, starts inactive until the mailed
    code is confirmed) and ``create`` (already-trusted, e.g. a seeded admin).
    """

    __slots__ = UserEntity.__slots__ + ("_events",)

    def __init__(self, source: EntitySourceProto) -> None:
        self._events = []
        UserEntity.__init__(self, source=source)
        AggregateRoot.__init__(self)

    @classmethod
    def register(
        cls,
        param: UserCreateParams,
        source_factory: EntitySourceFactoryProto,
        clock: ClockProto,
    ) -> ResultDetailed[Self]:
        """Self-service signup. The account exists but cannot be used until the
        emailed code is confirmed — `is_active`/`status` are seeded inactive
        together so the two never disagree."""
        validation_res = param.validate()

        if validation_res.is_err():
            return validation_res

        now = clock.get_now()

        kwargs = {
            UserField.EMAIL: param.email,
            UserField.FIRST_NAME: param.first_name,
            UserField.LAST_NAME: param.last_name,
            UserField.PHONE: param.phone,
            UserField.ADDRESS: param.address,
            UserField.DESCRIPTION: param.description,
            UserField.INFORMATION: param.information,
            UserField.AVATAR_ID: param.avatar_id,
            UserField.EMAIL_CONFIRMED: False,
            UserField.IS_ACTIVE: False,
            UserField.IS_SUPERUSER: False,
            UserField.STATUS: StatusEnum.INACTIVE,
            UserField.DATE_JOINED: now,
            UserField.LAST_LOGIN_TIME: None,
        }

        self = cls(source=source_factory.empty(cls, **kwargs))
        return Result.ok(self)

    @classmethod
    def create(
        cls,
        param: UserCreateParams,
        source_factory: EntitySourceFactoryProto,
        clock: ClockProto,
        is_superuser: bool = False,
    ) -> ResultDetailed[Self]:
        """An already-trusted user (CLI seed, fixture): active, email confirmed."""
        validation_res = param.validate()

        if validation_res.is_err():
            return validation_res

        now = clock.get_now()

        kwargs = {
            UserField.EMAIL: param.email,
            UserField.FIRST_NAME: param.first_name,
            UserField.LAST_NAME: param.last_name,
            UserField.PHONE: param.phone,
            UserField.ADDRESS: param.address,
            UserField.DESCRIPTION: param.description,
            UserField.INFORMATION: param.information,
            UserField.AVATAR_ID: param.avatar_id,
            UserField.EMAIL_CONFIRMED: True,
            UserField.IS_ACTIVE: True,
            UserField.IS_SUPERUSER: is_superuser,
            UserField.STATUS: StatusEnum.ACTIVE,
            UserField.DATE_JOINED: now,
            UserField.LAST_LOGIN_TIME: now,
        }

        self = cls(source=source_factory.empty(cls, **kwargs))
        return Result.ok(self)

    def update(self, param: UserUpdateParams) -> ResultDetailed[None]:
        validation_res = param.validate()

        if validation_res.is_err():
            return validation_res

        self.first_name = param.first_name
        self.last_name = param.last_name
        self.phone = param.phone
        self.address = param.address
        self.description = param.description
        self.information = param.information
        self.avatar_id = param.avatar_id

        return Result.OK

    def change_email(self, email: str) -> None:
        """Changing the email un-confirms it — the new address is unproven until
        its own confirmation code comes back."""
        if email == self.email:
            return

        self.email = email
        self.email_confirmed = False

    def set_password(
        self, raw_password: str, password_service: PasswordServiceProto
    ) -> None:
        self.password = password_service.hash_password(raw_password).decode("utf-8")

    def confirm_email(self) -> None:
        """Mark the address proven and let the account in. Idempotent: a second
        confirmation of an already-active user changes nothing."""
        self.email_confirmed = True
        self.is_active = True

    def touch_login(self, clock: ClockProto) -> None:
        self.last_login_time = clock.get_now()

    def mark_registered(self, otp_code: str) -> None:
        """Emit the signup event carrying the code to mail.

        Must be called after the aggregate is flushed, so `id` is assigned.
        """
        if not self.email:
            raise RuntimeError("Email for user is not set")

        self.add_domain_event(
            event=UserRegisteredEvent(
                event_id=uuid4(),
                aggregate_id=self.id,
                recipient=self.email,
                otp_code=otp_code,
                full_name=self.full_name,
            )
        )
