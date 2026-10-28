"""uuidv7 server defaults; telemetry created_at default

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-28

Every primary key now also defaults to ``uuidv7()`` on the server (native from
Postgres 18), so inserts that bypass the ORM still get a time-ordered id. The
telemetry writer is one: it inserts through raw asyncpg without ``id`` or
``created_at``, and without these defaults every insert hit a NOT NULL
violation.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ID_TABLES = (
    "identity_user",
    "identity_otp",
    "identity_api_key",
    "blob_object",
    "telemetry_log",
)


def upgrade() -> None:
    for table in _ID_TABLES:
        op.alter_column(
            table,
            "id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=False,
            server_default=sa.text("uuidv7()"),
        )

    op.alter_column(
        "telemetry_log",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=sa.func.now(),
    )


def downgrade() -> None:
    op.alter_column(
        "telemetry_log",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
        server_default=None,
    )

    for table in _ID_TABLES:
        op.alter_column(
            table,
            "id",
            existing_type=postgresql.UUID(as_uuid=True),
            existing_nullable=False,
            server_default=None,
        )
