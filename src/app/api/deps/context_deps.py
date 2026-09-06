from typing import Annotated, Awaitable, Callable, NoReturn, Optional

from dependency_injector import wiring
from litestar import Request
from litestar.di import Provide
from litestar.exceptions import HTTPException
from starlette import status

from src.app.api.schemes.jwt_bearer_scheme import jwt_token_scheme
from src.app.application.identity.ports.services.api_key_services_ports import (
    ApiKeyServiceProto,
)
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.infra.providers.jwt_provider import JwtProvider
from src.app.shared_kernel.errors.app_exception import AppException
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)
from src.app.shared_kernel.types.entities import ApiKeyBase, UserBase
from src.app.shared_kernel.types.execution_context import ExecutionContext


@wiring.inject
async def get_current_user_from_token(
    token: Annotated[str, Provide(jwt_token_scheme)],
    user_repository: Annotated[
        UserRepositoryProto,
        wiring.Provide["identity.repositories.user_repo"],
    ],
    token_provider: Annotated[JwtProvider, wiring.Provide["infra.jwt_provider"]],
) -> UserBase:
    def raise_exception(
        message: AppExceptionMessage, exception_status: AppExceptionStatusCodes
    ) -> NoReturn:
        raise AppException(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            exception_status=exception_status,
        )

    if not token:
        raise_exception(
            AppExceptionMessage.ACCESS_TOKEN_REQUIRED,
            AppExceptionStatusCodes.ACCESS_TOKEN_REQUIRED,
        )

    token_payload = token_provider.decode_payload(token=token)

    if not token_payload or token_payload.user_id is None:
        raise_exception(
            AppExceptionMessage.INVALID_TOKEN_PROVIDED,
            AppExceptionStatusCodes.INVALID_ACCESS_TOKEN,
        )

    user = await user_repository.get_for_context(id_=token_payload.user_id)

    if not user:
        raise_exception(
            AppExceptionMessage.INVALID_LOGIN_CREDENTIALS,
            AppExceptionStatusCodes.INVALID_LOGIN_CREDENTIALS,
        )

    # A token stays cryptographically valid after the account is disabled; the
    # flag is what actually revokes it.
    if not user.is_active:
        raise_exception(
            AppExceptionMessage.INVALID_LOGIN_CREDENTIALS,
            AppExceptionStatusCodes.INVALID_LOGIN_CREDENTIALS,
        )

    return user


def get_current_user_from_request(
    required: bool = True, allow_api_key_access: bool = False
) -> Callable[[Request], Awaitable[UserBase | None]]:
    async def _get(request: Request) -> UserBase | None:
        user = getattr(request.state, "user", None)
        apik_obj = request.state.get("api_key_obj", None)

        if apik_obj is not None:
            if not allow_api_key_access:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=AppExceptionMessage.ACCESS_TOKEN_REQUIRED,
                )
        else:
            if required and not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=AppExceptionMessage.ACCESS_TOKEN_REQUIRED,
                )
        return user

    return _get


@wiring.inject
async def get_api_key_object(
    api_key: bytes,
    api_key_service: ApiKeyServiceProto = wiring.Provide(
        "identity.services.api_key_service"
    ),
) -> Optional[ApiKeyBase]:
    return await api_key_service.get_with_owner(api_key)


async def get_execution_context() -> ExecutionContext:
    return ExecutionContextProvider.get_context()
