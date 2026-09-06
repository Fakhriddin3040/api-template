from typing import List

from src.app.application.blob.commands.blob_commands import (
    BlobDeleteCommand,
    BlobUploadCommand,
)
from src.app.application.blob.dto.blob_dto import (
    BlobCreateDTO,
    BlobDetailedDTO,
    BlobListDTO,
)
from src.app.application.blob.ports.blob_repository import BlobRepositoryProto
from src.app.application.blob.ports.storage import BlobStorageProto
from src.app.application.blob.queries.blob_queries import BlobByIdQuery, BlobListQuery
from src.app.application.blob.validators.blob_validators import (
    BlobDeleteValidator,
    BlobUploadValidator,
)
from src.app.shared_kernel.errors.app_exception import AppExceptionDetail
from src.app.shared_kernel.errors.constants import (
    AppExceptionMessage,
    AppExceptionStatusCodes,
)
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.result import Result, ResultDetailed
from src.app.shared_kernel.pydantic.types import ListQueryResponse


class BlobUploadCommandHandler:
    def __init__(
        self,
        validator: BlobUploadValidator,
        storage: BlobStorageProto,
        blob_repo: BlobRepositoryProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._validator = validator
        self._storage = storage
        self._blob_repo = blob_repo
        self._uow = uow

    async def __call__(self, message: BlobUploadCommand) -> ResultDetailed[BlobListDTO]:
        validation_res = await self._validator(cmd=message)

        if validation_res.is_err():
            return Result.err(validation_res.unwrap_err())

        stored = await self._storage.store(
            content=message.content, name=message.name, kind=message.kind
        )

        async with self._uow:
            try:
                data = await self._blob_repo.create(
                    dto=BlobCreateDTO(
                        name=message.name,
                        kind=message.kind,
                        content_type=None,
                        size=len(message.content),
                        path=stored.path,
                        medium_path=stored.medium_path,
                        thumbnail_path=stored.thumbnail_path,
                    )
                )
            except Exception:
                # The bytes are already on disk; without this the failed upload
                # would leave an orphan file no row will ever point at.
                await self._storage.delete(
                    [
                        p
                        for p in (
                            stored.path,
                            stored.medium_path,
                            stored.thumbnail_path,
                        )
                        if p
                    ]
                )
                raise

            return Result.ok(data)


class BlobDeleteCommandHandler:
    def __init__(
        self,
        validator: BlobDeleteValidator,
        storage: BlobStorageProto,
        blob_repo: BlobRepositoryProto,
        uow: UnitOfWorkProto,
    ) -> None:
        self._validator = validator
        self._storage = storage
        self._blob_repo = blob_repo
        self._uow = uow

    async def __call__(self, message: BlobDeleteCommand) -> ResultDetailed[None]:
        validation_res = await self._validator(cmd=message)

        if validation_res.is_err():
            return Result.err(validation_res.unwrap_err())

        async with self._uow:
            # Read the paths before the row goes away — afterwards there is
            # nothing left to tell us which files belonged to it.
            paths = await self._blob_repo.get_paths(message.id)
            await self._blob_repo.delete(message.id)

        await self._storage.delete(paths)

        return Result.OK


class BlobListQueryHandler:
    def __init__(self, blob_repo: BlobRepositoryProto) -> None:
        self._blob_repo = blob_repo

    async def __call__(self, message: BlobListQuery) -> ListQueryResponse[BlobListDTO]:
        return await self._blob_repo.get_list(message.limit, message.offset)


class BlobDetailedByIdQueryHandler:
    def __init__(self, blob_repo: BlobRepositoryProto) -> None:
        self._blob_repo = blob_repo

    async def __call__(
        self, message: BlobByIdQuery
    ) -> Result[BlobDetailedDTO, List[AppExceptionDetail]]:
        found = await self._blob_repo.get_detailed(id_=message.id)

        if not found:
            return Result.err(
                [
                    AppExceptionDetail(
                        message=AppExceptionMessage.NOT_FOUND.add_prefix("Blob"),
                        status=AppExceptionStatusCodes.OBJECT_NOT_FOUND,
                    )
                ]
            )

        return Result.ok(found)
