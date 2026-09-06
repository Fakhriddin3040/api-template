"""Alembic environment.

The database URL and the metadata both come from the application itself, so a
migration can never run against a different database than the app, and
autogenerate always sees every model.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

# Importing the aggregator is what populates `SqlAlchemyBaseModel.metadata`;
# without it autogenerate would happily emit a migration dropping every table.
from src.app.data_access.orm import models as _models  # noqa: F401
from src.app.data_access.orm.base.base_orm_models import SqlAlchemyBaseModel
from src.app.data_access.orm.telemetry.models import (  # noqa: F401
    log_record_orm_model as _telemetry_models,
)
from src.app.shared_kernel.config.infra_configs import DatabaseConfig

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SqlAlchemyBaseModel.metadata

config.set_main_option(
    "sqlalchemy.url",
    DatabaseConfig().url.replace("%", "%%"),  # type: ignore[call-arg]
)


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
