from typing import List, Optional, Protocol, runtime_checkable

from src.app.application.blob.dto.blob_dto import (
    BlobCreateDTO,
    BlobDetailedDTO,
    BlobListDTO,
)
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T


@runtime_checkable
class BlobRepositoryProto(Protocol):
    async def create(self, dto: BlobCreateDTO) -> BlobListDTO: ...

    async def delete(self, id_: ID_T) -> None: ...

    async def exist_many(self, ids: List[ID_T]) -> bool:
        """Checks that every id exists."""

    async def exist_by_id(self, id_: ID_T) -> bool: ...

    async def get_detailed(self, id_: ID_T) -> Optional[BlobDetailedDTO]: ...

    async def get_paths(self, id_: ID_T) -> List[str]:
        """Every stored path for one object (original + variants), for deletion."""

    async def get_list(
        self, limit: int, offset: int
    ) -> ListQueryResponse[BlobListDTO]: ...
