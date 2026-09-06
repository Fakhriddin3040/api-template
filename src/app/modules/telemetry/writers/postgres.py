"""asyncpg-backed writer: batches events into the ``telemetry_log`` table."""

from __future__ import annotations

import logging
from typing import Any, Optional

import asyncpg
import msgspec

from src.app.modules.telemetry.logging.event import TelemetryEvent
from src.app.modules.telemetry.writers.base import AbstractWriter

logger = logging.getLogger("telemetry.writer.postgres")

_COLUMNS = (
    "trace_id",
    "kind",
    "service",
    "level",
    "ts",
    "epoch",
    "exec_ms",
    "user_id",
    "ip",
    "method",
    "url",
    "url_params",
    "data",
    "status_code",
    "user_agent",
    "message",
)


def _json_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    return msgspec.json.encode(value).decode("utf-8")


class PostgresWriter(AbstractWriter):
    name = "postgres"

    def __init__(
        self,
        dsn: str,
        *,
        table: str = "telemetry_log",
        traceback_table: str = "telemetry_log_traceback",
        pool_min_size: int = 1,
        pool_max_size: int = 4,
        batch_size: int = 200,
        flush_interval: float = 1.0,
        maxsize: int = 50_000,
    ) -> None:
        super().__init__(
            maxsize=maxsize, batch_size=batch_size, flush_interval=flush_interval
        )
        self._dsn = dsn
        self._table = table
        self._pool_min = pool_min_size
        self._pool_max = pool_max_size
        self._pool: Optional[asyncpg.Pool] = None
        self._insert_sql = (
            f"INSERT INTO {table} "
            f"(trace_id, kind, service, level, ts, epoch, exec_ms, user_id, "
            f"ip, method, url, url_params, data, status_code, user_agent, message) VALUES "
            f"($1::uuid, $2, $3, $4, to_timestamp($5), $5, $6, $7, $8, $9::inet, $10, $11, "
            f"$12::jsonb, $13::jsonb, $14, $15, $16)"
        )
        self._insert_returning_sql = self._insert_sql + " RETURNING id"
        self._traceback_insert_sql = (
            f"INSERT INTO {traceback_table} "
            f"(log_id, traceback) "
            f"VALUES ($1::bigint, $2::TEXT)"
        )

    async def _on_start(self) -> None:
        self._pool = await asyncpg.create_pool(
            dsn=self._dsn, min_size=self._pool_min, max_size=self._pool_max
        )
        logger.info("PostgresWriter connected (table=%s)", self._table)

    async def _handle_batch(self, batch: list[TelemetryEvent]) -> None:
        if self._pool is None:
            return

        plain_rows = [self._to_row(e) for e in batch if not e.traceback]
        with_traceback = [e for e in batch if e.traceback]

        async with self._pool.acquire() as conn:
            if plain_rows:
                await conn.executemany(self._insert_sql, plain_rows)
            # Events carrying a stack need the generated id to link the side row, so
            # they can't ride the batch executemany: insert the log row RETURNING id,
            # then the traceback, atomically per event.
            for event in with_traceback:
                async with conn.transaction():
                    log_id = await conn.fetchval(
                        self._insert_returning_sql, *self._to_row(event)
                    )
                    await conn.execute(
                        self._traceback_insert_sql, log_id, event.traceback
                    )

    async def _on_close(self) -> None:
        if self._pool is not None:
            await self._pool.close()

    @staticmethod
    def _to_row(event: TelemetryEvent) -> tuple:
        return (
            event.trace_id,
            event.kind,
            event.service,
            event.level,
            event.epoch,
            event.exec_ms,
            event.user_id,
            event.ip,
            event.method,
            event.url,
            _json_or_none(event.url_params),
            _json_or_none(event.data),
            event.status_code,
            event.user_agent,
            event.message,
        )
