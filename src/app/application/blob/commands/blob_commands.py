import base64

from pydantic import field_validator

from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.shared_kernel.pydantic.types import Command
from src.app.shared_kernel.types.base_types import ID_T


class BlobUploadCommand(Command):
    """Upload one object.

    ``content`` arrives base64-encoded so the same command works from a JSON body
    and from a multipart part without two code paths.
    """

    name: str
    kind: BlobKindEnum = BlobKindEnum.RAW
    content: memoryview

    @field_validator("content", mode="before")
    @classmethod
    def convert_content(cls, v) -> memoryview:
        if isinstance(v, memoryview):
            return v
        if isinstance(v, (bytes, bytearray)):
            return memoryview(v)
        if not v:
            raise ValueError("content is required")
        try:
            return memoryview(base64.b64decode(v))
        except Exception as exc:
            raise ValueError("Invalid data format: expected base64") from exc


class BlobDeleteCommand(Command):
    id: ID_T
