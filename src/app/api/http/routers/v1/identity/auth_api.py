import logging

from litestar import Controller, post
from litestar.params import Body
from starlette import status

from src.app.application.identity.commands.auth_commands import (
    ConfirmEmailCommand,
    LoginCommand,
    RefreshTokenCommand,
    RegisterCommand,
    ResendEmailConfirmationCommand,
)
from src.app.application.identity.dto.forgot_dto import MessageResponseDTO
from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.types.execution_context import ExecutionContext
from src.app.shared_kernel.types.jwt_schemas import JwtTokenDTO

logger = logging.getLogger(__name__)


class AuthController(Controller):
    """Everything a client can do without a token."""

    security = ()

    @post("/register", status_code=status.HTTP_201_CREATED)
    async def register(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: RegisterCommand = Body(),
    ) -> None:
        """Create an inactive account and mail a confirmation code."""
        logger.info("%s: register called for %s", ex_ctx.trace_id, data.email)

        result: ResultDetailed[None] = await mediator.send(data)

        if result.is_err():
            err = result.as_app_exception()
            logger.warning("%s: register failed", ex_ctx.trace_id, exc_info=err)
            raise err

        return result.unwrap()

    @post("/confirm-email", status_code=status.HTTP_204_NO_CONTENT)
    async def confirm_email(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: ConfirmEmailCommand = Body(),
    ) -> None:
        """Spend the mailed code and activate the account."""
        logger.info("%s: confirm-email called", ex_ctx.trace_id)

        result: ResultDetailed[None] = await mediator.send(data)

        if result.is_err():
            err = result.as_app_exception()
            logger.warning("%s: confirm-email failed", ex_ctx.trace_id, exc_info=err)
            raise err

        return result.unwrap()

    @post("/confirm-email/resend", status_code=status.HTTP_200_OK)
    async def resend_confirmation(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: ResendEmailConfirmationCommand = Body(),
    ) -> MessageResponseDTO:
        logger.info("%s: confirm-email resend called", ex_ctx.trace_id)

        result: ResultDetailed[MessageResponseDTO] = await mediator.send(data)

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @post("/login", status_code=status.HTTP_200_OK)
    async def login(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: LoginCommand = Body(),
    ) -> JwtTokenDTO:
        logger.info("%s: login attempt for %s", ex_ctx.trace_id, data.email)

        result: ResultDetailed[JwtTokenDTO] = await mediator.send(data)

        if result.is_err():
            err = result.as_app_exception()
            logger.warning("%s: login failed", ex_ctx.trace_id, exc_info=err)
            raise err

        return result.unwrap()

    @post("/refresh", status_code=status.HTTP_200_OK)
    async def refresh(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: RefreshTokenCommand = Body(),
    ) -> JwtTokenDTO:
        result: ResultDetailed[JwtTokenDTO] = await mediator.send(data)

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()
