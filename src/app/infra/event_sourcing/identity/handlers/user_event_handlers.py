"""Side effects for identity domain events — all of them outbound email.

Handlers never raise: an SMTP outage must not roll back a completed
registration. Failures are logged by the email service itself.
"""

import logging

from src.app.application.ports.notification_ports import EmailServiceProto
from src.app.domain.identity.constants.consts import otp_ttl_minutes
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.events import (
    ForgotPasswordStep1Event,
    ForgotPasswordStep2Event,
    UserEmailConfirmedEvent,
    UserRegisteredEvent,
)
from src.app.infra.functions.mail_templates import (
    confirmation_code_email,
    password_changed_email,
    password_reset_code_email,
)

logger = logging.getLogger(__name__)

_HTML = "html"


class UserRegisteredEventHandler:
    def __init__(self, email_service: EmailServiceProto) -> None:
        self._email_service = email_service

    async def __call__(self, event: UserRegisteredEvent) -> None:
        await self._email_service.send_email(
            dest=event.recipient,
            subject="Confirm your email",
            content=confirmation_code_email(
                full_name=event.full_name,
                code=event.otp_code,
                ttl_minutes=otp_ttl_minutes(OtpKindEnum.EMAIL_CONFIRMATION),
            ),
            subtype=_HTML,
        )


class UserEmailConfirmedEventHandler:
    """Nothing to send — the account is simply usable now.

    Kept as the seam where a welcome email or an analytics signal would go.
    """

    async def __call__(self, event: UserEmailConfirmedEvent) -> None:
        logger.info("User %s confirmed %s", event.aggregate_id, event.target_value)


class ForgotPasswordStep1EventHandler:
    def __init__(self, email_service: EmailServiceProto) -> None:
        self._email_service = email_service

    async def __call__(self, event: ForgotPasswordStep1Event) -> None:
        await self._email_service.send_email(
            dest=event.recipient,
            subject="Password reset code",
            content=password_reset_code_email(
                code=event.otp_code,
                ttl_minutes=otp_ttl_minutes(OtpKindEnum.FORGOT_PASSWORD),
            ),
            subtype=_HTML,
        )


class ForgotPasswordStep2EventHandler:
    def __init__(self, email_service: EmailServiceProto) -> None:
        self._email_service = email_service

    async def __call__(self, event: ForgotPasswordStep2Event) -> None:
        # The new password is deliberately *not* echoed back by mail — the user
        # just typed it, and mailing a live credential is what leaks it.
        await self._email_service.send_email(
            dest=event.recipient,
            subject="Your password was changed",
            content=password_changed_email(full_name=event.full_name),
            subtype=_HTML,
        )
