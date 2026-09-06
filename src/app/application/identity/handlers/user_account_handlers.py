import logging

from src.app.application.identity.commands.user_commands import (
    ChangePasswordCommand,
    UserToggleStatusCommand,
    UserUpdateMeCommand,
)
from src.app.application.identity.dto.user_dto import UserDetailedDTO, UserListDTO
from src.app.application.identity.queries.user_queries import (
    MeQuery,
    UserDetailedQuery,
    UserListQuery,
)
from src.app.domain.identity.params.user_params import UserUpdateParams
from src.app.domain.identity.repositories.user_repository import (
    UserAccountRepositoryProto,
    UserQueryRepositoryProto,
    UserRepositoryProto,
)
from src.app.modules.filtering.parser import parse_filters
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.pydantic.types import ListQueryResponse

logger = logging.getLogger(__name__)


def _not_found() -> AppExceptionDetail:
    return AppExceptionDetail(
        status=AppExceptionStatusCodes.OBJECT_NOT_FOUND,
        message=AppExceptionMessage.NOT_FOUND.add_prefix("User"),
    )


class UserToggleStatusCommandHandler:
    def __init__(
        self, account_repo: UserAccountRepositoryProto, uow: UnitOfWorkProto
    ) -> None:
        self._account_repo = account_repo
        self._uow = uow

    async def __call__(self, message: UserToggleStatusCommand) -> ResultDetailed[None]:
        async with self._uow:
            if not await self._account_repo.exists(id_=message.id):
                return Result.err([_not_found()])

            await self._account_repo.toggle_status(id_=message.id)

        return Result.OK


class UserUpdateMeCommandHandler:
    """Edits the caller's own record. The id comes from the execution context,
    never from the body — otherwise this would be an "edit any user" endpoint."""

    def __init__(self, user_repo: UserRepositoryProto, uow: UnitOfWorkProto) -> None:
        self._user_repo = user_repo
        self._uow = uow

    async def __call__(self, message: UserUpdateMeCommand) -> ResultDetailed[None]:
        from src.app.shared_kernel.providers.execution_context_provider import (
            ExecutionContextProvider,
        )

        user_id = ExecutionContextProvider.get_context().user_id

        async with self._uow:
            user = await self._user_repo.get_aggregate_for_update(id_=user_id)

            if user is None:
                return Result.err([_not_found()])

            update_res = user.update(
                UserUpdateParams(
                    first_name=message.first_name,
                    last_name=message.last_name,
                    phone=message.phone,
                    address=message.address,
                    description=message.description,
                    information=message.information,
                    avatar_id=message.avatar_id,
                )
            )

            if update_res.is_err():
                await self._uow.rollback()
                return Result.err(update_res.unwrap_err())

        return Result.OK


class ChangePasswordCommandHandler:
    def __init__(
        self,
        user_repo: UserRepositoryProto,
        password_service: PasswordServiceProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._user_repo = user_repo
        self._password_service = password_service
        self._uow = uow

    async def __call__(self, message: ChangePasswordCommand) -> ResultDetailed[None]:
        from src.app.shared_kernel.providers.execution_context_provider import (
            ExecutionContextProvider,
        )

        user_id = ExecutionContextProvider.get_context().user_id

        async with self._uow:
            user = await self._user_repo.get_aggregate_for_update(id_=user_id)

            if user is None:
                return Result.err([_not_found()])

            if not self._password_service.verify_password(
                message.old_password, user.password
            ):
                await self._uow.rollback()
                return Result.err(
                    [
                        AppExceptionDetail(
                            status=AppExceptionStatusCodes.INVALID_PASSWORD,
                            field="old_password",
                            message="Current password is incorrect",
                        )
                    ]
                )

            user.set_password(message.new_password, self._password_service)

        return Result.OK


class MeQueryHandler:
    def __init__(self, query_repo: UserQueryRepositoryProto) -> None:
        self._query_repo = query_repo

    async def __call__(self, message: MeQuery) -> ResultDetailed[UserDetailedDTO]:
        found = await self._query_repo.get_detailed(id_=message.id)

        if found is None:
            return Result.err([_not_found()])

        return Result.ok(found)


class UserDetailedQueryHandler:
    def __init__(self, query_repo: UserQueryRepositoryProto) -> None:
        self._query_repo = query_repo

    async def __call__(
        self, message: UserDetailedQuery
    ) -> ResultDetailed[UserDetailedDTO]:
        found = await self._query_repo.get_detailed(id_=message.id)

        if found is None:
            return Result.err([_not_found()])

        return Result.ok(found)


class UserListQueryHandler:
    def __init__(self, query_repo: UserQueryRepositoryProto) -> None:
        self._query_repo = query_repo

    async def __call__(
        self, message: UserListQuery
    ) -> ListQueryResponse[UserListDTO]:
        return await self._query_repo.get_list(
            limit=message.limit,
            offset=message.offset,
            filters=parse_filters(message),
            ordering=message.ordering,
        )
