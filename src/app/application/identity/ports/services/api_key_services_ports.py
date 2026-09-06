from typing import Protocol, runtime_checkable, Optional

from src.app.application.identity.dto.api_key_dto import ApiKeyListDTO
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.types.entities import UserBase, ApiKeyBase


@runtime_checkable
class ApiKeyServiceProto(Protocol):
    async def create(self, user: UserBase) -> ResultDetailed[ApiKeyListDTO]:
        """Create a new ApiKey object for a given user"""

    async def get_with_owner(self, api_key: bytes) -> Optional[ApiKeyBase]:
        """Retrieve the api key detailed object for a given user

        Args:
            api_key (bytes): Api key in binary format

        Returns:
            Optional[ApiKeyBase]: The owner of the api_key if exists
        """
