from dependency_injector import containers, providers

from src.app.application.identity.handlers.auth_handlers import (
    ConfirmEmailCommandHandler,
    LoginCommandHandler,
    RefreshTokenCommandHandler,
    RegisterCommandHandler,
    ResendEmailConfirmationCommandHandler,
)
from src.app.application.identity.handlers.forgot_password_handlers import (
    ForgotPasswordStep1CommandHandler,
    ForgotPasswordStep2CommandHandler,
    ForgotPasswordStep3CommandHandler,
)
from src.app.application.identity.handlers.user_account_handlers import (
    ChangePasswordCommandHandler,
    MeQueryHandler,
    UserDetailedQueryHandler,
    UserListQueryHandler,
    UserToggleStatusCommandHandler,
    UserUpdateMeCommandHandler,
)
from src.app.application.identity.ports.repositories.api_key_repository import (
    ApiKeyRepositoryProto,
)
from src.app.application.identity.ports.services.api_key_services_ports import (
    ApiKeyServiceProto,
)
from src.app.application.identity.ports.services.auth_service_ports import (
    AuthServiceProto,
)
from src.app.application.identity.ports.services.registration_service_ports import (
    ForgotPasswordServiceProto,
    UserRegistrationServiceProto,
)
from src.app.application.identity.ports.services.user_confirmation_service import (
    UserConfirmationServiceProto,
)
from src.app.application.identity.services.api_key_services import ApiKeyService
from src.app.application.identity.services.auth_service import AuthService
from src.app.application.identity.services.registration_service import (
    ForgotPasswordService,
    UserRegistrationService,
)
from src.app.application.identity.services.user_confirmation_service import (
    UserConfirmationService,
)
from src.app.application.identity.validators.user_validators import RegisterValidator
from src.app.data_access.orm.identity.repositories.api_key_orm_repository import (
    ApiKeyOrmRepository,
)
from src.app.data_access.orm.identity.repositories.otp_orm_repository import (
    OtpOrmRepository,
)
from src.app.data_access.orm.identity.repositories.user_orm_repository import (
    UserOrmRepository,
)
from src.app.domain.identity.constants.consts import OTP_CODE_LENGTH
from src.app.domain.identity.repositories.otp_repository import OtpRepositoryProto
from src.app.domain.identity.repositories.user_repository import UserRepositoryProto
from src.app.infra.di.db_di import DatabaseDIContainer
from src.app.shared_kernel.di.core_di import CoreDIContainer
from src.app.shared_kernel.utils.di_funcs import call_if_provider
from src.app.infra.di.infra_di import InfraDIContainer
from src.app.infra.event_sourcing.identity.handlers.user_event_handlers import (
    UserEmailConfirmedEventHandler,
)
from src.app.shared_kernel.utils.functions.security_funcs import generate_numeric_otp


class IdentityRepositoriesDIContainer(containers.DeclarativeContainer):
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()

    user_repo: providers.Provider[UserRepositoryProto] = providers.Factory(
        UserOrmRepository,
        db=db.session,
        source_factory=db.entity_source_factory,
    )

    otp_repo: providers.Provider[OtpRepositoryProto] = providers.Factory(
        OtpOrmRepository, db=db.session
    )

    api_key_repo: providers.Provider[ApiKeyRepositoryProto] = providers.Factory(
        ApiKeyOrmRepository, db=db.session
    )


class IdentityServicesDIContainer(containers.DeclarativeContainer):
    core: providers.Container[CoreDIContainer] = providers.DependenciesContainer()
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()
    infra: providers.Container[InfraDIContainer] = providers.DependenciesContainer()
    repositories: providers.Container[IdentityRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )

    # Numeric codes are what the template mails; the length lives with the other
    # OTP rules so both the generator and the validator read the same constant.
    otp_generator = providers.Object(
        lambda: generate_numeric_otp(OTP_CODE_LENGTH)
    )

    confirmation_service: providers.Provider[UserConfirmationServiceProto] = (
        providers.Factory(
            UserConfirmationService,
            otp_repo=repositories.otp_repo,
            otp_generator=otp_generator,
            clock=providers.Callable(call_if_provider, core.services.provided.clock),
            bus=infra.event_bus,
        )
    )

    registration_service: providers.Provider[UserRegistrationServiceProto] = (
        providers.Factory(
            UserRegistrationService,
            user_repo=repositories.user_repo,
            confirmation_service=confirmation_service,
            password_service=providers.Callable(call_if_provider, infra.services.provided.password_service),
            source_factory=db.entity_source_factory,
            clock=providers.Callable(call_if_provider, core.services.provided.clock),
            uow=db.uow,
        )
    )

    forgot_password_service: providers.Provider[ForgotPasswordServiceProto] = (
        providers.Factory(
            ForgotPasswordService,
            confirmation_service=confirmation_service,
        )
    )

    auth_service: providers.Provider[AuthServiceProto] = providers.Factory(
        AuthService,
        user_repo=repositories.user_repo,
        password_service=providers.Callable(call_if_provider, infra.services.provided.password_service),
        jwt_provider=infra.jwt_provider,
    )

    api_key_service: providers.Provider[ApiKeyServiceProto] = providers.Factory(
        ApiKeyService,
        api_key_repo=repositories.api_key_repo,
        secret_service=providers.Callable(call_if_provider, infra.services.provided.secret_service),
        signature_service=providers.Callable(call_if_provider, infra.services.provided.signature_service),
    )


class IdentityValidatorsDIContainer(containers.DeclarativeContainer):
    repositories: providers.Container[IdentityRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )

    register_validator = providers.Factory(
        RegisterValidator, user_repo=repositories.user_repo
    )


class IdentityCommandHandlersDIContainer(containers.DeclarativeContainer):
    core: providers.Container[CoreDIContainer] = providers.DependenciesContainer()
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()
    infra: providers.Container[InfraDIContainer] = providers.DependenciesContainer()
    repositories: providers.Container[IdentityRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )
    services: providers.Container[IdentityServicesDIContainer] = (
        providers.DependenciesContainer()
    )
    validators: providers.Container[IdentityValidatorsDIContainer] = (
        providers.DependenciesContainer()
    )

    # `.provider` (not the factory itself): the mediator stores a *factory* and
    # calls it per message, so each command gets a handler bound to the current
    # request's session.
    register_handler = providers.Factory(
        RegisterCommandHandler,
        validator=validators.register_validator,
        service=services.registration_service,
        uow=db.uow,
        bus=infra.event_bus,
    ).provider

    confirm_email_handler = providers.Factory(
        ConfirmEmailCommandHandler,
        user_repo=repositories.user_repo,
        confirmation_service=services.confirmation_service,
        auth_service=services.auth_service,
        uow=db.uow,
    ).provider

    resend_confirmation_handler = providers.Factory(
        ResendEmailConfirmationCommandHandler,
        user_repo=repositories.user_repo,
        confirmation_service=services.confirmation_service,
        uow=db.uow,
        bus=infra.event_bus,
    ).provider

    login_handler = providers.Factory(
        LoginCommandHandler, auth_service=services.auth_service, uow=db.uow
    ).provider

    refresh_token_handler = providers.Factory(
        RefreshTokenCommandHandler, auth_service=services.auth_service, uow=db.uow
    ).provider

    forgot_step1_handler = providers.Factory(
        ForgotPasswordStep1CommandHandler,
        user_repo=repositories.user_repo,
        service=services.forgot_password_service,
        uow=db.uow,
        bus=infra.event_bus,
    ).provider

    forgot_step2_handler = providers.Factory(
        ForgotPasswordStep2CommandHandler,
        user_repo=repositories.user_repo,
        otp_repo=repositories.otp_repo,
        clock=providers.Callable(call_if_provider, core.services.provided.clock),
        uow=db.uow,
    ).provider

    forgot_step3_handler = providers.Factory(
        ForgotPasswordStep3CommandHandler,
        password_service=providers.Callable(call_if_provider, infra.services.provided.password_service),
        user_repo=repositories.user_repo,
        service=services.forgot_password_service,
        otp_repo=repositories.otp_repo,
        clock=providers.Callable(call_if_provider, core.services.provided.clock),
        uow=db.uow,
        bus=infra.event_bus,
    ).provider

    update_me_handler = providers.Factory(
        UserUpdateMeCommandHandler, user_repo=repositories.user_repo, uow=db.uow
    ).provider

    change_password_handler = providers.Factory(
        ChangePasswordCommandHandler,
        user_repo=repositories.user_repo,
        password_service=providers.Callable(call_if_provider, infra.services.provided.password_service),
        uow=db.uow,
    ).provider

    user_toggle_status_handler = providers.Factory(
        UserToggleStatusCommandHandler,
        account_repo=repositories.user_repo,
        uow=db.uow,
    ).provider


class IdentityQueryHandlersDIContainer(containers.DeclarativeContainer):
    repositories: providers.Container[IdentityRepositoriesDIContainer] = (
        providers.DependenciesContainer()
    )

    me_handler = providers.Factory(
        MeQueryHandler, query_repo=repositories.user_repo
    ).provider

    user_detailed_handler = providers.Factory(
        UserDetailedQueryHandler, query_repo=repositories.user_repo
    ).provider

    user_list_handler = providers.Factory(
        UserListQueryHandler, query_repo=repositories.user_repo
    ).provider


class IdentityEventHandlersDIContainer(containers.DeclarativeContainer):
    user_email_confirmed_handler = providers.Factory(
        UserEmailConfirmedEventHandler
    ).provider


class IdentityDIContainer(containers.DeclarativeContainer):
    core: providers.Container[CoreDIContainer] = providers.DependenciesContainer()
    db: providers.Container[DatabaseDIContainer] = providers.DependenciesContainer()
    infra: providers.Container[InfraDIContainer] = providers.DependenciesContainer()

    repositories: providers.Container[IdentityRepositoriesDIContainer] = (
        providers.Container(IdentityRepositoriesDIContainer, db=db)
    )

    services: providers.Container[IdentityServicesDIContainer] = providers.Container(
        IdentityServicesDIContainer,
        core=core,
        db=db,
        infra=infra,
        repositories=repositories,
    )

    validators: providers.Container[IdentityValidatorsDIContainer] = (
        providers.Container(IdentityValidatorsDIContainer, repositories=repositories)
    )

    command_handlers: providers.Container[IdentityCommandHandlersDIContainer] = (
        providers.Container(
            IdentityCommandHandlersDIContainer,
            core=core,
            db=db,
            infra=infra,
            repositories=repositories,
            services=services,
            validators=validators,
        )
    )

    query_handlers: providers.Container[IdentityQueryHandlersDIContainer] = (
        providers.Container(IdentityQueryHandlersDIContainer, repositories=repositories)
    )

    event_handlers: providers.Container[IdentityEventHandlersDIContainer] = (
        providers.Container(IdentityEventHandlersDIContainer)
    )
