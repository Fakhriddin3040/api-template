import inspect
from typing import Dict, Any, Type, Awaitable, List

from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.types.base_types import Pipeline
from src.app.shared_kernel.pydantic.types import Command, Query
from src.app.shared_kernel.types.cqrs import CQHandler, CQHandlerFactory


class Mediator(MediatorProto):
    """
    Minimal implementation of a meditor for CQRS pattern realisation
    with pipelines.
    """

    def __init__(self):
        self._pipelines: List[Pipeline] = []
        self._cmd_handlers_factories: Dict[
            type[Command], CQHandlerFactory[Command, Any]
        ] = dict()
        self._qr_handlers_factories: Dict[type[Query], CQHandlerFactory[Query, Any]] = (
            dict()
        )

    def register_command(
        self, command: Type[Command], handler_factory: CQHandlerFactory[Command, Any]
    ) -> None:
        self._cmd_handlers_factories[command] = handler_factory

    def register_query(
        self, query: Type[Query], handler_factory: CQHandlerFactory[Query, Any]
    ) -> None:
        self._qr_handlers_factories[query] = handler_factory

    async def send(self, cmd: Command) -> Any:
        """
        Send a command to the handler.

        Args:
            cmd (Command): The command to send.

        Returns:
            Any: The result of the handler.

        Raises:
            KeyError: If the handler doesn't exist.
        """
        factory = self._cmd_handlers_factories[type(cmd)]

        runner = factory()

        return await self._invoke(runner, cmd)

    async def ask(self, query: Query) -> Any:
        """
        Ask the handler for the given query.

        Args:
            query (Query): The query to ask.

        Returns:
            Any: The result of the handler.

        Raises:
            KeyError: If the handler doesn't exist.
        """
        factory = self._qr_handlers_factories[type(query)]

        runner = factory()

        return await self._invoke(runner, query)

    def _wrap(
        self, handler: CQHandler[Command | Query, Any]
    ) -> CQHandler[Command | Query, Awaitable[Any]]:
        if inspect.iscoroutinefunction(handler):
            fn = handler
        else:

            async def wrapper(*args, **kwargs) -> Awaitable[Any]:
                return handler(*args, **kwargs)

            fn = wrapper

        for p in reversed(self._pipelines):
            fn = p(fn)

        return fn

    async def _invoke(
        self, runner: CQHandler[Command | Query, Any], msg: Command | Query
    ) -> Any:
        return await runner(msg)
