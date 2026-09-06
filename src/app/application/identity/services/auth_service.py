from src.app.application.identity.ports.services.auth_service_ports import (
    AuthServiceProto,
)
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.infra.constants.enums.jwt_enums import JwtType
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.security.jwt_proto import JwtProviderProto
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.types.jwt_schemas import JwtTokenDTO
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


def _invalid_credentials() -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.INVALID_LOGIN_CREDENTIALS,
        message=AppExceptionMessage.INVALID_LOGIN_CREDENTIALS,
    )


class AuthService(AuthServiceProto):
    """Password login and refresh-token rotation.

    Every rejection returns the same detail. Distinguishing "unknown address"
    from "wrong password" would turn the endpoint into a registered-user oracle.
    """

    def __init__(
        self,
        user_repo: UserRepositoryProto,
        password_service: PasswordServiceProto,
        jwt_provider: JwtProviderProto,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._jwt_provider = jwt_provider

    async def login(self, *, email: str, password: str) -> ResultDetailed[JwtTokenDTO]:
        found = await self._user_repo.get_credentials_by_email(email=email)

        if found is None:
            # Still hash something: returning early on an unknown address makes
            # the response measurably faster and leaks which addresses exist.
            self._password_service.verify_password(password, "")
            return Result.err([_invalid_credentials()])

        if not self._password_service.verify_password(password, found.password):
            return Result.err([_invalid_credentials()])

        if not found.is_active or not found.email_confirmed:
            return Result.err([_invalid_credentials()])

        token = self._jwt_provider.for_user(found)

        return Result.ok(
            JwtTokenDTO(
                access_token=token.access_token, refresh_token=token.refresh_token
            )
        )

    async def refresh(self, *, refresh_token: str) -> ResultDetailed[JwtTokenDTO]:
        payload = self._jwt_provider.decode_payload(token=refresh_token)

        if payload is None:
            return Result.err(
                [
                    AppExceptionDetail(
                        status=AppExceptionStatusCodes.INVALID_REFRESH_TOKEN,
                        message=AppExceptionMessage.INVALID_TOKEN_PROVIDED,
                    )
                ]
            )

        # An access token presented here would otherwise mint a new pair and
        # defeat the shorter access lifetime entirely.
        if payload.token_type != JwtType.REFRESH_TOKEN:
            return Result.err(
                [
                    AppExceptionDetail(
                        status=AppExceptionStatusCodes.INVALID_TOKEN_TYPE,
                        message=AppExceptionMessage.INVALID_TOKEN_TYPE,
                    )
                ]
            )

        user = await self._user_repo.get_for_context(id_=payload.user_id)

        if user is None or not user.is_active:
            return Result.err([_invalid_credentials()])

        token = self._jwt_provider.for_user(user)

        return Result.ok(
            JwtTokenDTO(
                access_token=token.access_token, refresh_token=token.refresh_token
            )
        )


ensure_isimplementation(AuthService, AuthServiceProto)
