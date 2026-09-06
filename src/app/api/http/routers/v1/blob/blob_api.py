import logging

from litestar import Controller, delete, get, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.params import Body
from starlette import status

from src.app.application.blob.commands.blob_commands import (
    BlobDeleteCommand,
    BlobUploadCommand,
)
from src.app.application.blob.constants.enums import BlobKindEnum
from src.app.application.blob.dto.blob_dto import BlobDetailedDTO, BlobListDTO
from src.app.application.blob.queries.blob_queries import BlobByIdQuery, BlobListQuery
from src.app.modules.filtering.litestar_integration import path_bound_query
from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.ports.result import ResultDetailed
from src.app.shared_kernel.pydantic.types import ListQueryResponse
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.types.entities import UserBase
from src.app.shared_kernel.types.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class BlobController(Controller):
    """Stored objects: raw files and images.

    Upload is multipart — base64 in a JSON body inflates the payload by a third
    and has to be held in memory twice.
    """

    @post("/", status_code=status.HTTP_201_CREATED)
    async def upload(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002 - presence enforces authentication
        data: UploadFile = Body(media_type=RequestEncodingType.MULTI_PART),
        kind: BlobKindEnum = BlobKindEnum.RAW,
    ) -> BlobListDTO:
        content = await data.read()

        logger.info(
            "%s: blob upload called (%s, %d bytes)",
            ex_ctx.trace_id,
            data.filename,
            len(content),
        )

        result: ResultDetailed[BlobListDTO] = await mediator.send(
            BlobUploadCommand(
                name=data.filename, kind=kind, content=memoryview(content)
            )
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @get(
        "/",
        status_code=status.HTTP_200_OK,
        dependencies=path_bound_query(BlobListQuery),
    )
    async def list_(
        self,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        list_query: BlobListQuery,
    ) -> ListQueryResponse[BlobListDTO]:
        return await mediator.ask(list_query)

    @get("/{id:uuid}", status_code=status.HTTP_200_OK)
    async def detailed(
        self,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        id: ID_T,  # noqa: A002
    ) -> BlobDetailedDTO:
        result: ResultDetailed[BlobDetailedDTO] = await mediator.ask(
            BlobByIdQuery(id=id)
        )

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()

    @delete("/{id:uuid}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_(
        self,
        ex_ctx: ExecutionContext,
        mediator: MediatorProto,
        user: UserBase,  # noqa: ARG002
        id: ID_T,  # noqa: A002
    ) -> None:
        logger.info("%s: blob delete called for %s", ex_ctx.trace_id, id)

        result: ResultDetailed[None] = await mediator.send(BlobDeleteCommand(id=id))

        if result.is_err():
            raise result.as_app_exception()

        return result.unwrap()
