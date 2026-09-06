from dependency_injector import containers, providers

from src.app.infra.di.blob_di import BlobDIContainer
from src.app.infra.di.db_di import DatabaseDIContainer
from src.app.infra.di.identity_di import IdentityDIContainer
from src.app.infra.di.infra_di import InfraDIContainer
from src.app.infra.services.clock import Clock
from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer
from src.app.shared_kernel.di.core_di import CoreDIContainer, CoreServicesDIContainer


class RootDIContainer(containers.DeclarativeContainer):
    config: providers.Container[ConfigurationDIContainer] = providers.Container(
        ConfigurationDIContainer
    )

    # Layers
    core: providers.Container[CoreDIContainer] = providers.Container(
        CoreDIContainer,
        config=config,
        services=providers.Container(
            CoreServicesDIContainer,
            clock=providers.Singleton(Clock, tz_=config.app.provided.tzinfo),
        ),
    )

    db: providers.Container[DatabaseDIContainer] = providers.Container(
        DatabaseDIContainer,
        core=core,
    )

    infra: providers.Container[InfraDIContainer] = providers.Container(
        InfraDIContainer,
        config=config,
    )

    # Bounded contexts
    identity: providers.Container[IdentityDIContainer] = providers.Container(
        IdentityDIContainer,
        core=core,
        db=db,
        infra=infra,
    )

    blob: providers.Container[BlobDIContainer] = providers.Container(
        BlobDIContainer,
        db=db,
        config=config,
    )
