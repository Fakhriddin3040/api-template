"""Single import surface for every ORM model.

Alembic's autogenerate and SQLAlchemy's mapper configuration both need every
model imported before they run; doing it here means one import instead of a list
that silently goes stale.
"""

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.data_access.orm.blob.models.blob_orm_model import BlobObjectOrmModel
from src.app.data_access.orm.identity.models.api_key_orm_model import ApiKeyOrmModel
from src.app.data_access.orm.identity.models.user_orm_model import (
    OtpOrmModel,
    UserOrmModel,
)

__all__ = [
    "SqlAlchemyBaseModel",
    "ApiKeyOrmModel",
    "BlobObjectOrmModel",
    "OtpOrmModel",
    "UserOrmModel",
]
