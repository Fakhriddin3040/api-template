from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import (
    Double,
    Index,
    SmallInteger,
    String,
    Text,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.data_access.orm.constants.db_constants import DatabaseTable, db_identifier


class LogRecordOrmModel(SqlAlchemyBaseModel):
    """Generic telemetry sink.

    Deliberately decoupled: ``user_id`` is a plain nullable column
    (no FKs) so the table stays an append-only, immutable trace that survives row
    deletions elsewhere. ``kind`` generalises it beyond http requests for future traces.
    """

    __tablename__ = DatabaseTable.TELEMETRY_LOG

    trace_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )
    kind: Mapped[str] = mapped_column(
        String(32), nullable=False, default="http_request"
    )
    service: Mapped[str] = mapped_column(String(64), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="INFO")

    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    epoch: Mapped[float] = mapped_column(Double, nullable=False)
    exec_ms: Mapped[Optional[float]] = mapped_column(Double, nullable=True)

    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True
    )

    ip: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url_params: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    data: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )

    __table_args__ = (
        Index(db_identifier(f"idx_{__tablename__}__trace_id"), "trace_id"),
        Index(db_identifier(f"idx_{__tablename__}__service__ts"), "service", "ts"),
        Index(db_identifier(f"idx_{__tablename__}__user_id__ts"), "user_id", "ts"),
        Index(db_identifier(f"idx_{__tablename__}__level"), "level"),
        Index(db_identifier(f"idx_{__tablename__}__status_code"), "status_code"),
    )


class LogRecordTracebackOrmModel(SqlAlchemyBaseModel):
    __tablename__ = DatabaseTable.TELEMETRY_LOG_TRACEBACK

    id = None

    log_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey(
            DatabaseTable.TELEMETRY_LOG.as_foreign_key,
            name=db_identifier(
                f"pk_{__tablename__}__log_id__{DatabaseTable.TELEMETRY_LOG}__id"
            ),
        ),
        nullable=False,
        primary_key=True,
    )
    traceback: Mapped[str] = mapped_column(
        Text(),
        nullable=False,
    )

    __table_args__ = (
        PrimaryKeyConstraint(
            "log_id",
            name=db_identifier(f"pk_{__tablename__}__log_id"),
        ),
    )
