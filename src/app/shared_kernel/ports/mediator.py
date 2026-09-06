from typing import Protocol, runtime_checkable, TypeVar, Type, Any

from src.app.shared_kernel.pydantic.types import Command, Query
from src.app.shared_kernel.types.cqrs import CQHandlerFactory

C = TypeVar("C")
Q = TypeVar("Q")
R = TypeVar("R")


@runtime_checkable
class MediatorProto(Protocol):
    async def send(self, cmd: C) -> R: ...
    async def ask(self, query: Q) -> R: ...
    def register_command(
        self, command: Type[Command], handler_factory: CQHandlerFactory[Command, Any]
    ) -> None: ...
    def register_query(
        self, query: Type[Query], handler_factory: CQHandlerFactory[Query, Any]
    ) -> None: ...
