import logging

from litestar import Controller, get, patch, post
from litestar.params import Body
from starlette import status

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
from src.app.modules.filtering.litestar_integration import path_bound_query
from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.types.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class UserController(Controller):
    """Authenticated user surface.

    Every route here requires a token. There is no role check: authorization is
    deliberately left to the concrete project — see the RBAC note in the README.
    """

    @get("/me", status_code=status.HTTP_200_OK)
    async def me(
        self,
        mediator: MediatorProto,
        user: UserBase,
    ) -> UserDetailedDTO:
        # The id comes from the verified token, never from the request.
        result: ResultDetailed[UserDetailedDTO] = await mediator.ask(
            MeQuery(id=user.id)
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @patch("/me", status_code=status.HTTP_204_NO_CONTENT)
    async def update_me(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002 - presence enforces authentication
        data: UserUpdateMeCommand = Body(),
    ) -> None:
        logger.info("%s: update-me called", ex_ctx.trace_id)

        result: ResultDetailed[None] = await mediator.send(data)

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
    async def change_password(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        data: ChangePasswordCommand = Body(),
    ) -> None:
        logger.info("%s: change-password called", ex_ctx.trace_id)

        result: ResultDetailed[None] = await mediator.send(data)

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @get(
        "/",
        status_code=status.HTTP_200_OK,
        # `list_query`, not the reserved `query`: the latter binds from the query
        # string alone and would reject any field sourced from the path or body.
        dependencies=path_bound_query(UserListQuery),
    )
    async def list_(
        self,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        list_query: UserListQuery,
    ) -> ListQueryResponse[UserListDTO]:
        return await mediator.ask(list_query)

    @get("/{id:uuid}", status_code=status.HTTP_200_OK)
    async def detailed(
        self,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        id: ID_T,  # noqa: A002 - matches the path parameter name
    ) -> UserDetailedDTO:
        result: ResultDetailed[UserDetailedDTO] = await mediator.ask(
            UserDetailedQuery(id=id)
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @post("/{id:uuid}/toggle-status", status_code=status.HTTP_204_NO_CONTENT)
    async def toggle_status(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        id: ID_T,  # noqa: A002
    ) -> None:
        logger.info("%s: toggle-status called for %s", ex_ctx.trace_id, id)

        result: ResultDetailed[None] = await mediator.send(
            UserToggleStatusCommand(id=id)
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()
