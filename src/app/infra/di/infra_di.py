from dependency_injector import containers, providers

from src.app.application.cqrs.mediator import Mediator
from src.app.application.ports.http_client_port import HttpClientProto
from src.app.application.ports.notification_ports import EmailServiceProto
from src.app.infra.adapters.http_client import HttpClient
from src.app.infra.event_sourcing.event_bus import InProcessEventBus
from src.app.infra.event_sourcing.event_bus_middlewares import (
    LoggingEventPublisherMiddleware,
    ObservabilityEventHandlerMiddleware,
)
from src.app.infra.event_sourcing.identity.handlers.user_event_handlers import (
    ForgotPasswordStep1EventHandler,
    ForgotPasswordStep2EventHandler,
    UserRegisteredEventHandler,
)
from src.app.infra.providers.jwt_provider import JwtProvider
from src.app.infra.services.email_service import EmailService
from src.app.infra.services.password_service import PasswordService
from src.app.infra.services.security_services import (
    AESGCMEncryptionService,
    HmacSha256SignatureService,
    SecretService,
)
from src.app.modules.cache.ports import CacheClientProto
from src.app.modules.cache.redis_client import RedisClient
from src.app.shared_kernel.di.configuration_di import ConfigurationDIContainer
from src.app.shared_kernel.ports.event import EventBusProto
from src.app.shared_kernel.ports.mediator import MediatorProto
from src.app.shared_kernel.ports.security.password_proto import PasswordServiceProto
from src.app.shared_kernel.ports.services.encryption import (
    EncryptionServiceProto,
    SignatureServiceProto,
)
from src.app.shared_kernel.ports.services.secrets import SecretServiceProto


class InfraServicesDIContainer(containers.DeclarativeContainer):
    # Dependencies
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )

    # Providers
    email_service: providers.Provider[EmailServiceProto] = providers.Singleton(
        EmailService, smtp_config=config.smtp
    )

    password_service: providers.Provider[PasswordServiceProto] = providers.Singleton(
        PasswordService
    )

    # Security
    encryption_service: providers.Provider[EncryptionServiceProto] = (
        providers.Singleton(AESGCMEncryptionService, config=config.app)
    )
    signature_service: providers.Provider[SignatureServiceProto] = providers.Singleton(
        HmacSha256SignatureService, config=config.app
    )
    secret_service: providers.Provider[SecretServiceProto] = providers.Singleton(
        SecretService
    )

    # Cache
    cache_client: providers.Provider[CacheClientProto] = providers.Singleton(
        RedisClient, config=config.redis
    )

    # Network
    http_client: providers.Provider[HttpClientProto] = providers.Factory(HttpClient)


class InfraEventHandlersDIContainer(containers.DeclarativeContainer):
    # Dependencies
    services: providers.Container[InfraServicesDIContainer] = (
        providers.DependenciesContainer()
    )

    # Handlers. `.provider` is what the bus stores: it builds a fresh handler per
    # event instead of pinning one instance for the process lifetime.
    user_registered_event_handler = providers.Factory(
        UserRegisteredEventHandler, email_service=services.email_service
    ).provider

    forgot_password_step1_event_handler = providers.Factory(
        ForgotPasswordStep1EventHandler, email_service=services.email_service
    ).provider

    forgot_password_step2_event_handler = providers.Factory(
        ForgotPasswordStep2EventHandler, email_service=services.email_service
    ).provider


class InfraDIContainer(containers.DeclarativeContainer):
    # Dependencies
    config: providers.Container[ConfigurationDIContainer] = (
        providers.DependenciesContainer()
    )

    # Providers
    mediator: providers.Provider[MediatorProto] = providers.Singleton(Mediator)
    jwt_provider: providers.Provider[JwtProvider] = providers.Singleton(
        JwtProvider, config=config.jwt
    )
    services: providers.Container[InfraServicesDIContainer] = providers.Container(
        InfraServicesDIContainer, config=config
    )

    event_bus: providers.Singleton[EventBusProto] = providers.Singleton(
        InProcessEventBus,
        publisher_middlewares=[LoggingEventPublisherMiddleware()],
        handler_middlewares=[ObservabilityEventHandlerMiddleware()],
    )

    event_handlers: providers.Container[InfraEventHandlersDIContainer] = (
        providers.Container(
            InfraEventHandlersDIContainer,
            services=services,
        )
    )
