from typing import Optional, TypedDict
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from urllib3.util import Url

from src.app.modules.filtering.types import FilterSpecCollection
from src.app.shared_kernel.pydantic.types import BasePydanticModel
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.entities import UserBase


class ExecutionContextRequest(TypedDict):
    url: Url


class ExecutionContextPayload(BasePydanticModel):
    query_filters: FilterSpecCollection = tuple()
    request: ExecutionContextRequest = None


class ExecutionContext(BaseModel):
    trace_id: UUID = Field(default_factory=uuid4)
    # A detached ``UserOnContextDTO`` (plain values) - reading its attributes never
    # touches a session, so the context is safe to read after a rollback / close.
    user: Optional[UserBase | None] = Field(default=None)
    payload: ExecutionContextPayload = Field(ExecutionContextPayload)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def user_id(self) -> Optional[ID_T]:
        return self.user.id if self.user else None

    @property
    def request(self) -> ExecutionContextRequest:
        return self.payload.request
