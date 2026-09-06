from src.app.application.identity.commands.auth_commands import RegisterCommand
from src.app.application.identity.commands.forgot_commands import (
    ForgotPasswordStep1Command,
)
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.shared_kernel.constants.models_fields.identity_model_fields import (
    UserField,
)
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import AppExceptionStatusCodes
from src.app.shared_kernel.ports.result import Result, ResultDetailed


class RegisterValidator:
    """The email is the login, so it is the one thing that must be unique."""

    def __init__(self, user_repo: UserRepositoryProto) -> None:
        self._user_repo = user_repo

    async def __call__(self, cmd: RegisterCommand) -> ResultDetailed[None]:
        if await self._user_repo.exists_by_email(email=cmd.email):
            return Result.err(
                [
                    AppExceptionDetail(
                        status=AppExceptionStatusCodes.UNIQUE_CONSTRAINT,
                        field=UserField.EMAIL,
                        message="This email address is already registered",
                    )
                ]
            )

        return Result.OK


class ForgotPasswordStep1Validator:
    """Only checks that a reset is *possible*.

    Whether the address exists is not reported back to the caller — the handler
    answers the same way either way — so this returns a plain flag rather than an
    error the endpoint would leak.
    """

    def __init__(self, user_repo: UserRepositoryProto) -> None:
        self._user_repo = user_repo

    async def __call__(self, cmd: ForgotPasswordStep1Command) -> ResultDetailed[None]:
        return Result.OK
