from typing import Optional

import msgspec

from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.shared_kernel.pydantic.types import BasePydanticModel
from src.app.shared_kernel.types.base_types import ID_T


class StoredBlobDTO(BasePydanticModel):
    """What the storage adapter produced — every path is media-root relative."""

    path: str
    medium_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


class BlobCreateDTO(BasePydanticModel):
    name: str
    kind: BlobKindEnum
    content_type: Optional[str]
    size: int
    path: str
    medium_path: Optional[str] = None
    thumbnail_path: Optional[str] = None


class BlobListDTO(msgspec.Struct):
    id: ID_T
    name: str
    kind: int
    url: str


class BlobDetailedDTO(msgspec.Struct):
    id: ID_T
    name: str
    kind: int
    url: str
    size: Optional[int]
    content_type: Optional[str]
    extension: str
    medium_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
