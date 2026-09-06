from typing import Callable

from dependency_injector.wiring import Provide, inject

from src.app.application.blob.commands.blob_commands import (
    BlobDeleteCommand,
    BlobUploadCommand,
)
from src.app.application.blob.queries.blob_queries import BlobByIdQuery, BlobListQuery
from src.app.shared_kernel.ports.mediator import MediatorProto


@inject
def _register_handlers(
    mediator: MediatorProto = Provide["infra.mediator"],
    upload: Callable = Provide["blob.command_handlers.upload_handler"],
    delete: Callable = Provide["blob.command_handlers.delete_handler"],
    detailed: Callable = Provide["blob.query_handlers.detailed_handler"],
    list_: Callable = Provide["blob.query_handlers.list_handler"],
) -> None:
    mediator.register_command(BlobUploadCommand, upload)
    mediator.register_command(BlobDeleteCommand, delete)
    mediator.register_query(BlobByIdQuery, detailed)
    mediator.register_query(BlobListQuery, list_)


def setup() -> None:
    _register_handlers()
