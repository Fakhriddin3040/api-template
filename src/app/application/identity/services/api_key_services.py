import base64
from typing import Optional

from src.app.application.identity.dto.api_key_dto import ApiKeyCreateDTO, ApiKeyListDTO
from src.app.application.identity.ports.repositories.api_key_repository import (
    ApiKeyRepositoryProto,
)
from src.app.application.identity.ports.services.api_key_services_ports import (
    ApiKeyServiceProto,
)
from src.app.domain.identity.constants.api_key_const import API_KEY_BYTE_LENGTH
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.ports.services.encryption import SignatureServiceProto
from src.app.shared_kernel.ports.services.secrets import SecretServiceProto
from src.app.shared_kernel.types.entities import UserBase, ApiKeyBase
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)


class ApiKeyService(ApiKeyServiceProto):
    def __init__(
        self,
        api_key_repo: ApiKeyRepositoryProto,
        secret_service: SecretServiceProto,
        signature_service: SignatureServiceProto,
    ) -> None:
        self._api_key_repo = api_key_repo
        self._secret_service = secret_service
        self._signature_service = signature_service

    async def create(self, user: UserBase) -> ResultDetailed[ApiKeyListDTO]:
        secret_bytes = self._secret_service.generate(API_KEY_BYTE_LENGTH)
        signed_bytes = self._signature_service.sign(secret_bytes)

        api_key_dto = ApiKeyCreateDTO(
            key=signed_bytes, owner_id=user.id
        )

        api_key = await self._api_key_repo.create(api_key_dto)

        client_b64 = base64.b64encode(secret_bytes).decode("utf-8")
        api_key.key = client_b64

        return Result.ok(api_key)

    async def get_with_owner(self, api_key: bytes) -> Optional[ApiKeyBase]:
        """Retrieve the api key detailed object for a given user

        Args:
            api_key (bytes): Api key in binary format

        Returns:
            Optional[ApiKeyBase]: The owner of the api_key if exists
        """
        apik = await self._api_key_repo.get_with_owner(self._sign_key(api_key))
        return apik

    def _sign_key(self, api_key: bytes) -> bytes:
        return self._signature_service.sign(api_key)


ensure_isimplementation(ApiKeyService, ApiKeyServiceProto)
