import msgspec

from src.app.shared_kernel.pydantic.types import BasePydanticModel
from src.app.shared_kernel.types.base_types import ID_T


class ApiKeyCreateDTO(BasePydanticModel):
    key: bytes
    owner_id: ID_T


class ApiKeyListDTO(msgspec.Struct):
    id: ID_T
    # Api key, not a signature. In base64 format. If type is str, then its base64, raw api key otherwise
    key: bytes | str
