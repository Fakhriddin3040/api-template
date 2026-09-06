from typing import Optional, Protocol, runtime_checkable

from src.app.application.identity.dto.forgot_dto import ForgotPasswordStep2ResponseDTO
from src.app.application.identity.dto.user_dto import (
    UserAuthDTO,
    UserCredentialsDTO,
    UserDetailedDTO,
    UserListDTO,
)
from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.modules.filtering.types import FilterContainerCollection
from src.app.shared_kernel.params.ordering import OrderingContainer
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.context_dtos import UserOnContextDTO
from src.app.shared_kernel.types.entities import UserBase


@runtime_checkable
class UserRepositoryProto(Protocol):
    def create(self, obj: UserAggregate) -> None: ...
    async def get_by_id(self, id_: ID_T) -> Optional[UserBase]: ...
    async def get_for_context(self, id_: ID_T) -> Optional[UserOnContextDTO]: ...
    async def get_aggregate_for_update(self, id_: ID_T) -> Optional[UserAggregate]: ...
    async def get_aggregate_for_update_by_email(
        self, email: str
    ) -> Optional[UserAggregate]: ...

    async def exists_by_email(
        self, email: str, is_active: Optional[bool] = None
    ) -> bool: ...

    async def get_credentials_by_email(self, email: str) -> Optional[UserAuthDTO]:
        """The hash plus the flags the login path checks."""
        ...

    async def get_for_password_reset(self, email: str) -> Optional[UserAggregate]: ...

    async def get_by_email_for_password_recovery(
        self, email: str
    ) -> Optional[ForgotPasswordStep2ResponseDTO]:
        """Who a reset code belongs to. One row: the email is unique."""
        ...


@runtime_checkable
class UserAccountRepositoryProto(Protocol):
    async def exists(self, id_: ID_T) -> bool: ...
    async def toggle_status(self, id_: ID_T) -> bool: ...
    async def activate(self, user_id: ID_T) -> Optional[UserCredentialsDTO]: ...
    async def get_credentials_for_resend(
        self, user_id: ID_T
    ) -> Optional[UserCredentialsDTO]: ...


@runtime_checkable
class UserQueryRepositoryProto(Protocol):
    async def get_list(
        self,
        limit: int,
        offset: int,
        filters: FilterContainerCollection,
        ordering: Optional[OrderingContainer] = None,
    ) -> ListQueryResponse[UserListDTO]: ...

    async def get_detailed(self, id_: ID_T) -> Optional[UserDetailedDTO]: ...
