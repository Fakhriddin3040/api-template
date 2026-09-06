from typing import List, Protocol, runtime_checkable

from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.application.blob.dto.blob_dto import StoredBlobDTO


@runtime_checkable
class BlobStorageProto(Protocol):
    """Where bytes physically live.

    The only thing the application layer knows about storage. Swapping the local
    filesystem for S3/MinIO means writing one more adapter — nothing above this
    line changes.
    """

    async def store(
        self, *, content: memoryview, name: str, kind: BlobKindEnum
    ) -> StoredBlobDTO:
        """Persist the bytes (running the image pipeline for ``IMAGE``) and
        return every path produced, relative to the storage root."""

    async def delete(self, paths: List[str]) -> None:
        """Remove stored objects. Missing paths are ignored — deletion is
        idempotent, and a half-written upload must still be cleanable."""
