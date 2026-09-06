import pytest

from src.app.data_access.entity_source.factories import SqlAlchemyEntitySourceFactory
from src.app.infra.constants.entity_source_consts import ENTITY_ORM_MODEL_MAP
from src.app.infra.services.clock import Clock
from src.app.infra.services.password_service import PasswordService
from src.app.shared_kernel.constants.datetime_const import DEFAULT_TIMEZONE


@pytest.fixture
def clock() -> Clock:
    return Clock(tz_=DEFAULT_TIMEZONE)


@pytest.fixture
def password_service() -> PasswordService:
    return PasswordService()


@pytest.fixture
def source_factory() -> SqlAlchemyEntitySourceFactory:
    """Builds real (unattached) ORM instances — no session, no database.

    That is enough to exercise an aggregate end to end, because the entity proxy
    only ever reads and writes attributes on the row.
    """
    return SqlAlchemyEntitySourceFactory(
        domain_model_to_orm_model_map=ENTITY_ORM_MODEL_MAP
    )
