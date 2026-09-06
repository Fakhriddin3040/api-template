from uuid import UUID

from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.types.execution_context import ExecutionContext


class ExecutionContextMixin:
    @staticmethod
    @inject
    def get_context(
        provider: ExecutionContextProvider = Provide["core.execution_context_provider"],
    ) -> ExecutionContext | None:
        return provider.get_context()

    def _get_user(self) -> UserBase:
        return self.get_context().user

    def _get_user_id(self) -> ID_T | None:
        return self.get_context().user_id

    def _get_trace_id(self) -> UUID | None:
        return self.get_context().trace_id
