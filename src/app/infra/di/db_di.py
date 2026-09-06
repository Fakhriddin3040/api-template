from contextvars import Token

from dependency_injector import providers, containers
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.app.data_access.entity_source.factories import SqlAlchemyEntitySourceFactory
from src.app.data_access.orm.unit_of_work import OrmUnitOfWork
from src.app.infra.constants.entity_source_consts import ENTITY_ORM_MODEL_MAP
from src.app.shared_kernel.di.core_di import CoreDIContainer
from src.app.shared_kernel.globals_ import db_session_registry
from src.app.shared_kernel.ports.db.unit_of_work import UnitOfWorkProto
from src.app.shared_kernel.ports.factories.entity_source_factory import (
    EntitySourceFactoryProto,
)

def _get_current_session() -> AsyncSession:
    return db_session_registry.get(required=True)


def set_current_session(session_factory: async_sessionmaker[AsyncSession]) -> Token:
    return db_session_registry.set(session_factory())


async def clear_current_session(token: Token) -> None:
    session = _get_current_session()
    await session.close()
    db_session_registry.reset(token=token)


class DatabaseDIContainer(containers.DeclarativeContainer):

    # Inject outside on bootstrapping.
    core: providers.Container[CoreDIContainer] = providers.DependenciesContainer()

    engine: providers.Provider[AsyncEngine] = providers.Singleton(
        lambda db_cfg, app_cfg: create_async_engine(
            db_cfg().url,
            # Pin the session timezone so `now()` and every timestamptz render
            # in the app's zone regardless of the server's locale.
            connect_args={
                "server_settings": {"timezone": app_cfg().timezone_name}
            },
            pool_pre_ping=True,
        ),
        db_cfg=core.config.provided.db,
        app_cfg=core.config.provided.app,
    )

    session_factory: providers.Provider[async_sessionmaker[AsyncSession]] = (
        providers.Singleton(
            async_sessionmaker,
            bind=engine,
            autoflush=False,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    )
    session: providers.Provider[AsyncSession] = providers.Callable(_get_current_session)
    set_current_session: providers.Provider[None] = providers.Callable(
        set_current_session,
        session_factory=session_factory,
    )
    clear_current_session: providers.Provider[None] = providers.Callable(
        clear_current_session
    )

    # Get the session with 'session' property.
    # Init this resource need before scope is started. If not initialized, then on
    # 'getattr(session)' 'RuntimeError' will occur. See 'session' factory bellow.
    uow: providers.Provider[UnitOfWorkProto] = providers.Factory(
        OrmUnitOfWork, session=session
    )

    entity_source_factory: providers.Provider[EntitySourceFactoryProto] = (
        providers.Singleton(
            SqlAlchemyEntitySourceFactory,
            domain_model_to_orm_model_map=ENTITY_ORM_MODEL_MAP,
        )
    )
