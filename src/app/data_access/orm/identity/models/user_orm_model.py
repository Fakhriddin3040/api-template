from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from src.app.data_access.orm.base.base_orm_models import (
    ChronoModelMixin,
    SqlAlchemyBaseModel,
    StatusModelMixin,
)
from src.app.data_access.orm.constants.db_constants import DatabaseTable, db_identifier
from src.app.domain.identity.constants.enums import OtpKindEnum
from src.app.domain.identity.identity_constraints import (
    USER_ADDRESS_MAX_LENGTH,
    USER_EMAIL_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PASSWORD_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
)
from src.app.shared_kernel.constants.common_enums import ContentTypeEnum
from src.app.shared_kernel.types.base_types import ID_T

if TYPE_CHECKING:
    from src.app.data_access.orm.blob.models.blob_orm_model import BlobObjectOrmModel


class OtpOrmModel(SqlAlchemyBaseModel, ChronoModelMixin):
    __tablename__ = DatabaseTable.OTP

    updated_at = None

    otp: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)

    content_id: Mapped[ID_T] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    content_type: Mapped[ContentTypeEnum] = mapped_column(String(50), nullable=False)

    kind: Mapped[OtpKindEnum] = mapped_column(SmallInteger, nullable=False)

    # Unix epoch seconds, BIGINT to match the column. Writers must pass an int:
    # `OtpCreateDTO.expires_at` is an int field and pydantic rejects a
    # fractional float, which is exactly what `clock.get_utc_epoch()` returns.
    # (asyncpg itself would tolerate the float and silently truncate.)
    used_at: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

    target_value: Mapped[str] = mapped_column(String(254), nullable=False)

    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        # Every lookup in the confirmation flows is keyed by owner + kind
        # (find_active_for_content, has_recent_issue, invalidate_pending), so
        # the table is never scanned by the code alone.
        Index(
            db_identifier(f"idx_{DatabaseTable.OTP}__content__kind"),
            "content_id",
            "content_type",
            "kind",
        ),
    )


class UserOrmModel(
    SqlAlchemyBaseModel,
    StatusModelMixin,
    ChronoModelMixin,
):
    """The single identity row.

    The former ``UserProfile`` table is merged in: first/last name, address,
    description and avatar are columns here, so there is no second row to create,
    join or keep in sync.
    """

    __tablename__ = DatabaseTable.USER

    # The login credential. Unique + NOT NULL: there is no username.
    email: Mapped[str] = mapped_column(
        String(USER_EMAIL_MAX_LENGTH), unique=True, nullable=False, index=True
    )

    password: Mapped[str] = mapped_column(
        String(USER_PASSWORD_MAX_LENGTH), nullable=True
    )

    phone: Mapped[Optional[str]] = mapped_column(
        String(USER_PHONE_MAX_LENGTH), nullable=True
    )

    first_name: Mapped[str] = mapped_column(
        String(USER_NAME_MAX_LENGTH), default="", nullable=False
    )

    last_name: Mapped[str] = mapped_column(
        String(USER_NAME_MAX_LENGTH), default="", nullable=False
    )

    address: Mapped[Optional[str]] = mapped_column(
        String(USER_ADDRESS_MAX_LENGTH), nullable=True
    )

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    information: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    avatar_id: Mapped[Optional[ID_T]] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey(DatabaseTable.BLOB_OBJECT.as_foreign_key, ondelete="SET NULL"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    email_confirmed: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    date_joined: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, server_default=func.now()
    )

    last_login_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relations
    avatar: Mapped[Optional["BlobObjectOrmModel"]] = relationship(
        "BlobObjectOrmModel", foreign_keys=[avatar_id], lazy="raise"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
