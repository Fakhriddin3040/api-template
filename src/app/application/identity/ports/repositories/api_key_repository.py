from typing import Protocol, runtime_checkable, Optional

from src.app.application.identity.dto.api_key_dto import ApiKeyCreateDTO, ApiKeyListDTO

from src.app.shared_kernel.types.entities import ApiKeyBase


@runtime_checkable
class ApiKeyRepositoryProto(Protocol):
    """Repository must store key itself in encrypted type"""

    async def create(self, data: ApiKeyCreateDTO) -> ApiKeyListDTO:
        """Create new api key and returns it.

        Args:
            data (ApiKeyCreateDTO): Api key to create. `data.key` must be encrypted
        """

    async def get_with_owner(self, api_key: bytes) -> Optional[ApiKeyBase]:
        """Retrieve api key detailed object with its owner

        Args:
            api_key (bytes): Crypto-signed api key

        Returns:
            ApiKeyBase: Api key detailed object
        """
