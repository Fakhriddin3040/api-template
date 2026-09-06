"""Single import surface for every ORM repository."""

from src.app.data_access.orm.blob.repositories.blob_orm_repository import (
    BlobOrmRepository,
)
from src.app.data_access.orm.identity.repositories.api_key_orm_repository import (
    ApiKeyOrmRepository,
)
from src.app.data_access.orm.identity.repositories.otp_orm_repository import (
    OtpOrmRepository,
)
from src.app.data_access.orm.identity.repositories.user_orm_repository import (
    UserOrmRepository,
)

__all__ = [
    "ApiKeyOrmRepository",
    "BlobOrmRepository",
    "OtpOrmRepository",
    "UserOrmRepository",
]
