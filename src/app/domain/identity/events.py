from pydantic import Field

from src.app.infra.constants.enums import AggregateName
from src.app.shared_kernel.ports.domain.domain_event import DomainEvent


class UserRegisteredEvent(DomainEvent):
    """A self-service signup created an inactive account; `otp_code` is the
    numeric code mailed to `recipient` to prove control of the address."""

    recipient: str
    otp_code: str
    full_name: str
    aggregate_name: str = Field(init=False, default=AggregateName.USER)


class UserConfirmedEvent(DomainEvent):
    """Base for "a user proved control of `target_value`".

    Published by ``UserConfirmationService`` once an OTP has passed every rule
    and been consumed. The concrete subclass says *what* was confirmed, so each
    kind gets its own side effect without the service knowing any of them.

    ``aggregate_id`` is the confirmed user's id; ``target_value`` is whatever
    was proven (an email address).
    """

    target_value: str
    aggregate_name: str = Field(init=False, default=AggregateName.USER)


class UserEmailConfirmedEvent(UserConfirmedEvent):
    """A user confirmed their email address. The handler is what activates the
    account on first confirmation."""


class ForgotPasswordStep1Event(DomainEvent):
    recipient: str
    otp_code: str
    aggregate_name: str = Field(init=False, default=AggregateName.USER)


class ForgotPasswordStep2Event(DomainEvent):
    recipient: str
    new_password: str
    full_name: str
    aggregate_name: str = Field(init=False, default=AggregateName.USER)
