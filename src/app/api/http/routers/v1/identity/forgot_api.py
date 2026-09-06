import logging

from litestar import Controller, post
from litestar.params import Body
from starlette import status

from src.app.application.identity.commands.forgot_commands import (
    ForgotPasswordStep1Command,
    ForgotPasswordStep2Command,
    ForgotPasswordStep3Command,
)
from src.app.application.identity.dto.forgot_dto import (
    ForgotPasswordStep1ResponseDTO,
    ForgotPasswordStep2ResponseDTO,
    ForgotPasswordStep3ResponseDTO,
)
from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.types.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class ForgotPasswordController(Controller):
    """Three steps: ask for a code, prove it, spend it.

    Splitting "prove" from "spend" is what lets the UI show whose account is
    about to change, and keeps a rejected new password from burning the code.
    """

    security = ()

    @post("/step1", status_code=status.HTTP_200_OK)
    async def step1(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: ForgotPasswordStep1Command = Body(),
    ) -> ForgotPasswordStep1ResponseDTO:
        logger.info("%s: forgot-password step1 called", ex_ctx.trace_id)

        result: ResultDetailed[ForgotPasswordStep1ResponseDTO] = await mediator.send(
            data
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @post("/step2", status_code=status.HTTP_200_OK)
    async def step2(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: ForgotPasswordStep2Command = Body(),
    ) -> ForgotPasswordStep2ResponseDTO:
        logger.info("%s: forgot-password step2 called", ex_ctx.trace_id)

        result: ResultDetailed[ForgotPasswordStep2ResponseDTO] = await mediator.send(
            data
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @post("/step3", status_code=status.HTTP_200_OK)
    async def step3(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        data: ForgotPasswordStep3Command = Body(),
    ) -> ForgotPasswordStep3ResponseDTO:
        logger.info("%s: forgot-password step3 called", ex_ctx.trace_id)

        result: ResultDetailed[ForgotPasswordStep3ResponseDTO] = await mediator.send(
            data
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()
