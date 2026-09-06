from dependency_injector import providers, containers

from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer
from src.app.shared_kernel.ports.services import ClockProto
from src.app.shared_kernel.providers.execution_context_provider import (
    ExecutionContextProvider,
)


class CoreServicesDIContainer(containers.DeclarativeContainer):
    clock: providers.Provider[ClockProto] = providers.Dependency(ClockProto)


class CoreDIContainer(containers.DeclarativeContainer):
    # Dependency containers.
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )
    services: providers.Container[CoreServicesDIContainer] = (
        providers.DependenciesContainer()
    )

    execution_context_provider: providers.Singleton[ExecutionContextProvider] = (
        providers.Singleton(lambda: ExecutionContextProvider)
    )
