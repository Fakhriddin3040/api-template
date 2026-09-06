from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, DateTime, String, Boolean, false
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
    declared_attr,
)
from sqlalchemy.sql import func

from src.app.data_access.orm.constants.db_constants import DatabaseTable, db_identifier
from src.app.shared_kernel.constants.common_constraints import COMMENT_MAX_LENGTH
from src.app.shared_kernel.constants.common_enums import StatusEnum
from src.app.shared_kernel.types.base_types import ID_T
from src.app.shared_kernel.utils.functions.uuid_funcs import uuid7

if TYPE_CHECKING:
    from src.app.data_access.orm.models import UserOrmModel


class SqlAlchemyBaseModel(DeclarativeBase):
    @declared_attr
    def id(cls) -> Mapped[ID_T]:
        # Generated application-side rather than by a DB default, so the value
        # exists without asking the database for it. `default=` fires at INSERT;
        # aggregates get their id earlier still (see SqlAlchemyEntitySourceFactory).
        return mapped_column(
            PgUUID(as_uuid=True),
            primary_key=True,
            default=uuid7,
        )


class ChronoModelMixin:
    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=False,
            default=func.now(),
            onupdate=func.now(),
        )


class AuthorInfoModelMixin:

    @declared_attr
    def created_by_id(cls) -> Mapped[ID_T]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey(
                DatabaseTable.USER.as_foreign_key,
                ondelete="SET NULL",
                name=db_identifier(
                    f"fk_{cls.__tablename__}__created_by_id__{DatabaseTable.USER}__id"
                ),
            ),
            nullable=True,
        )

    @declared_attr
    def updated_by_id(cls) -> Mapped[ID_T]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey(
                DatabaseTable.USER.as_foreign_key,
                ondelete="SET NULL",
                name=db_identifier(
                    f"fk_{cls.__tablename__}__updated_by_id__{DatabaseTable.USER}__id"
                ),
            ),
            nullable=True,
        )

    @declared_attr
    def created_by(cls) -> Mapped["UserOrmModel"]:
        return relationship(
            "UserOrmModel", foreign_keys=lambda: [cls.created_by_id], lazy="raise"
        )  # noqa

    @declared_attr
    def updated_by(cls) -> Mapped["UserOrmModel"]:
        return relationship(
            "UserOrmModel", foreign_keys=lambda: [cls.updated_by_id], lazy="raise"
        )  # noqa


STATUS_ACTIVE = 1
STATUS_INACTIVE = 0


class StatusModelMixin:

    @declared_attr
    def status(cls) -> Mapped[StatusEnum]:
        return mapped_column(SmallInteger, nullable=False, default=STATUS_ACTIVE)

    @declared_attr
    def deactivated_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def activated_at(cls) -> Mapped[datetime]:
        return mapped_column(DateTime(timezone=True), nullable=True)

    @declared_attr
    def activated_by_id(cls) -> Mapped[ID_T]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey(
                DatabaseTable.USER.as_foreign_key,
                ondelete="SET NULL",
                name=db_identifier(
                    f"fk_{cls.__tablename__}__activated_by_id__{DatabaseTable.USER}__id"
                ),
            ),
            nullable=True,
        )

    @declared_attr
    def deactivated_by_id(cls) -> Mapped[ID_T]:
        return mapped_column(
            PgUUID(as_uuid=True),
            ForeignKey(
                DatabaseTable.USER.as_foreign_key,
                ondelete="SET NULL",
                name=db_identifier(
                    f"fk_{cls.__tablename__}__deactivated_by_id__{DatabaseTable.USER}__id"
                ),
            ),
            nullable=True,
        )


class CommentModelMixin:

    @declared_attr
    def comment(cls) -> Mapped[str]:
        return mapped_column(String(COMMENT_MAX_LENGTH), nullable=True)


class DirtyMixin:
    @declared_attr
    def dirty(cls) -> Mapped[bool]:
        return mapped_column(
            Boolean(), nullable=False, default=False, insert_default=false()
        )
