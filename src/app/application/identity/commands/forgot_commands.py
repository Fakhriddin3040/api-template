from src.app.domain.identity.params.annotated import (
    ATOtp,
    ATPassword,
    ATUserEmail,
)
from src.app.shared_kernel.pydantic.types import Command


class ForgotPasswordStep1Command(Command):
    """Ask for a reset code."""

    email: ATUserEmail


class ForgotPasswordStep2Command(Command):
    """Prove the code is yours; returns who it belongs to."""

    email: ATUserEmail
    otp: ATOtp


class ForgotPasswordStep3Command(Command):
    """Spend the code and set the new password."""

    email: ATUserEmail
    otp: ATOtp
    new_password: ATPassword
