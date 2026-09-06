from contextvars import ContextVar, Token
from typing import Tuple, Optional

from src.app.data_access.orm.identity.models.user_orm_model import UserOrmModel
from src.app.shared_kernel.types.execution_context import ExecutionContext


class ExecutionContextProvider:
    _registry: ContextVar[ExecutionContext] = ContextVar("execution_context")

    @classmethod
    def create(
        cls, user: Optional[UserOrmModel] = None, **payload
    ) -> Tuple[ExecutionContext, Token]:
        ctx = ExecutionContext(user=user, payload=payload)
        token = cls._registry.set(ctx)
        return ctx, token

    @classmethod
    def get_context(cls) -> ExecutionContext | None:
        return cls._registry.get()

    @classmethod
    def clear(cls, token: Token) -> None:
        cls._registry.reset(token)
