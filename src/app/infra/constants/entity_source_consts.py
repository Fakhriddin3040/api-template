"""Which ORM model backs which domain entity.

The entity-source factory reads this both ways: domain -> ORM when building a
new aggregate, and ORM -> domain when hydrating one from a loaded row.
"""

from src.app.data_access.orm.identity.models.user_orm_model import (
    OtpOrmModel,
    UserOrmModel,
)
from src.app.domain.identity.aggregates.user_aggregate import UserAggregate
from src.app.domain.identity.entities.user_entity import OtpEntity

ENTITY_ORM_MODEL_MAP = {
    UserAggregate: UserOrmModel,
    OtpEntity: OtpOrmModel,
}
