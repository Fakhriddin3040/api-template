from typing import Optional

from src.app.domain.identity.params.annotated import (
    ATAddress,
    ATOtp,
    ATPassword,
    ATPhone,
    ATUserEmail,
    ATUserName,
)
from src.app.shared_kernel.pydantic.types import Command


class RegisterCommand(Command):
    """Self-service signup. Creates an inactive account and mails a numeric
    code; the account becomes usable only once that code comes back."""

    email: ATUserEmail
    password: ATPassword
    first_name: ATUserName
    last_name: ATUserName
    phone: Optional[ATPhone] = None
    address: Optional[ATAddress] = None


class LoginCommand(Command):
    email: ATUserEmail
    password: str


class RefreshTokenCommand(Command):
    refresh_token: str


class ConfirmEmailCommand(Command):
    """Confirm a mailed code.

    Carries the address as well as the code: a short numeric OTP is not globally
    unique, so it only identifies a confirmation together with its recipient.
    """

    email: ATUserEmail
    otp: ATOtp


class ResendEmailConfirmationCommand(Command):
    email: ATUserEmail
