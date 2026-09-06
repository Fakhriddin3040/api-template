from src.app.application.blob.commands.blob_commands import (
    BlobDeleteCommand,
    BlobUploadCommand,
)
from src.app.application.blob.constants.constraints import (
    ALLOWED_FILE_SIGNATURES,
    ALLOWED_IMAGE_SIGNATURES,
    MAX_BLOB_SIZE_BYTES,
    MAX_IMAGE_SIZE_BYTES,
)
from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.application.blob.ports.blob_repository import BlobRepositoryProto
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.result import Result, ResultDetailed


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


class BlobUploadValidator:
    """Guards size and "the bytes are what the extension claims".

    Checking the magic bytes rather than trusting the filename is what stops a
    caller from parking an executable under a `.png` name.
    """

    async def __call__(self, cmd: BlobUploadCommand) -> ResultDetailed[None]:
        is_image = cmd.kind == BlobKindEnum.IMAGE
        max_size = MAX_IMAGE_SIZE_BYTES if is_image else MAX_BLOB_SIZE_BYTES

        if len(cmd.content) > max_size:
            return Result.err(
                [
                    AppExceptionDetail(
                        message=AppExceptionMessage.FILE_SIZE_LIMIT_EXCEEDED,
                        status=AppExceptionStatusCodes.FILE_SIZE_LIMIT_EXCEEDED,
                    )
                ]
            )

        return self._validate_signature(cmd.content, cmd.name, is_image=is_image)

    @staticmethod
    def _validate_signature(
        content: memoryview, filename: str, *, is_image: bool
    ) -> ResultDetailed[None]:
        allowed = ALLOWED_IMAGE_SIGNATURES if is_image else ALLOWED_FILE_SIGNATURES
        extension = _extension(filename)

        if extension not in allowed:
            return Result.err(
                [
                    AppExceptionDetail(
                        message=f"Extension .{extension} is not supported",
                        status=AppExceptionStatusCodes.UNSUPPORTED_FILE_FORMAT,
                    )
                ]
            )

        signatures = allowed[extension]

        # No signature registered (plain text): nothing to compare against.
        if not signatures:
            return Result.OK

        for signature in signatures:
            if bytes(content[: len(signature)]) == signature:
                return Result.OK

        return Result.err(
            [
                AppExceptionDetail(
                    message=f"File content does not match the .{extension} extension",
                    status=AppExceptionStatusCodes.UNSUPPORTED_FILE_FORMAT,
                )
            ]
        )


class BlobDeleteValidator:
    def __init__(self, blob_repo: BlobRepositoryProto) -> None:
        self._blob_repo = blob_repo

    async def __call__(self, cmd: BlobDeleteCommand) -> ResultDetailed[None]:
        if not await self._blob_repo.exist_by_id(cmd.id):
            return Result.err(
                [
                    AppExceptionDetail(
                        message=AppExceptionMessage.NOT_FOUND.add_prefix("Blob"),
                        status=AppExceptionStatusCodes.OBJECT_NOT_FOUND,
                    )
                ]
            )

        return Result.OK
