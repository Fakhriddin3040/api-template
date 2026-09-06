from sqlalchemy import ForeignKey, Integer, LargeBinary, SmallInteger
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.data_access.orm.base.base_orm_models import (
    ChronoModelMixin,
    SqlAlchemyBaseModel,
)
from src.app.data_access.orm.constants.db_constants import DatabaseTable
from src.app.domain.identity.constants.enums import ApiKeyStatusEnum
from src.app.shared_kernel.types.base_types import ID_T


class ApiKeyOrmModel(SqlAlchemyBaseModel, ChronoModelMixin):
    __tablename__ = DatabaseTable.API_KEY

    # Hmac signature stores here
    key: Mapped[bytes] = mapped_column(LargeBinary(32), nullable=False, index=True)
    status: Mapped[ApiKeyStatusEnum] = mapped_column(
        SmallInteger, nullable=False, default=ApiKeyStatusEnum.ACTIVE
    )
    last_used_at: Mapped[int] = mapped_column(Integer, nullable=True, default=None)

    owner_id: Mapped[ID_T] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(DatabaseTable.USER.as_foreign_key, ondelete="CASCADE"),
        nullable=False,
    )
    owner: Mapped["UserOrmModel"] = relationship(  # noqa
        "UserOrmModel", foreign_keys=owner_id
    )
