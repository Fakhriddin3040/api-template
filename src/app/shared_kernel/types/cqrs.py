from typing import Union, Any, Awaitable, Protocol, runtime_checkable
from src.app.shared_kernel.pydantic.types import Command, Query


@runtime_checkable
class CQHandler[CQ: Union[Command, Query], R: Any](Protocol):
    """Обобщённый обработчик Command/Query"""

    def __call__(self, message: CQ) -> Union[R, Awaitable[R]]: ...


@runtime_checkable
class CQHandlerFactory[CQ: Union[Command, Query], R: Any](Protocol):
    def __call__(self) -> CQHandler[CQ, R]: ...
