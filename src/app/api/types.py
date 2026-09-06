from litestar.di import Provide
from typing_extensions import Annotated, TypeAlias

from src.app.api.deps.context_deps import (
    get_current_user_from_request,
    get_execution_context,
)
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.types.execution_context import ExecutionContext

DepUser: TypeAlias = Annotated[
    UserBase, Provide(get_current_user_from_request(required=True))
]

DepMayBeUser: TypeAlias = Annotated[
    UserBase | None, Provide(get_current_user_from_request(required=False))
]

DepExContext: TypeAlias = Annotated[ExecutionContext, Provide(get_execution_context)]
