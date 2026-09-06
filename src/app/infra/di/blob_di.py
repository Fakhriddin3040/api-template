from dependency_injector import containers, providers

from src.app.application.blob.handlers.blob_handlers import (
    BlobDeleteCommandHandler,
    BlobDetailedByIdQueryHandler,
    BlobListQueryHandler,
    BlobUploadCommandHandler,
)
from src.app.application.blob.ports.blob_repository import BlobRepositoryProto
from src.app.application.blob.ports.storage import BlobStorageProto
from src.app.application.blob.validators.blob_validators import (
    BlobDeleteValidator,
    BlobUploadValidator,
)
from src.app.data_access.orm.blob.repositories.blob_orm_repository import (
    BlobOrmRepository,
)
from src.app.infra.adapters.local_blob_storage import LocalBlobStorage
from src.app.infra.di.db_di import DatabaseDIContainer
from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer


class BlobRepositoriesDIContainer(containers.DeclarativeContainer):
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()

    blob_repo: providers.Provider[BlobRepositoryProto] = providers.Factory(
        BlobOrmRepository, db=db.session
    )


class BlobCommandHandlersDIContainer(containers.DeclarativeContainer):
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()
    repositories: providers.Container[BlobRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )
    storage: providers.Provider[BlobStorageProto] = providers.Dependency()

    upload_handler = providers.Factory(
        BlobUploadCommandHandler,
        validator=providers.Factory(BlobUploadValidator),
        storage=storage,
        blob_repo=repositories.blob_repo,
        uow=db.uow,
    ).provider

    delete_handler = providers.Factory(
        BlobDeleteCommandHandler,
        validator=providers.Factory(
            BlobDeleteValidator, blob_repo=repositories.blob_repo
        ),
        storage=storage,
        blob_repo=repositories.blob_repo,
        uow=db.uow,
    ).provider


class BlobQueryHandlersDIContainer(containers.DeclarativeContainer):
    repositories: providers.Container[BlobRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )

    detailed_handler = providers.Factory(
        BlobDetailedByIdQueryHandler, blob_repo=repositories.blob_repo
    ).provider

    list_handler = providers.Factory(
        BlobListQueryHandler, blob_repo=repositories.blob_repo
    ).provider


class BlobDIContainer(containers.DeclarativeContainer):
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )

    # Swap this provider for an S3/MinIO adapter and nothing else moves.
    storage: providers.Provider[BlobStorageProto] = providers.Singleton(
        LocalBlobStorage, app_config=config.app
    )

    repositories: providers.Container[BlobRepositoriesDIContainer] = providers.Container(
        BlobRepositoriesDIContainer, db=db
    )

    command_handlers: providers.Container[BlobCommandHandlersDIContainer] = (
        providers.Container(
            BlobCommandHandlersDIContainer,
            db=db,
            repositories=repositories,
            storage=storage,
        )
    )

    query_handlers: providers.Container[BlobQueryHandlersDIContainer] = (
        providers.Container(BlobQueryHandlersDIContainer, repositories=repositories)
    )
