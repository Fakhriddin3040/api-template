"""Telemetry daemon entrypoint.

A single standalone process: tails ``logs/*.log``, runs each event through the
global filter pipeline and the composer, and fans out to the Postgres/Telegram
writers. Run it separately from the api/web/worker processes:

    python -m src.app.modules.telemetry.runner
"""

from __future__ import annotations

import asyncio
import logging
import signal

from src.app.modules.telemetry.composer import Route, TelemetryComposer
from src.app.modules.telemetry.filters.base import FilterPipeline
from src.app.modules.telemetry.filters.common import (
    ExcludeUrls,
    MinLevel,
    StatusAtLeast,
)
from src.app.modules.telemetry.logging.event import KIND_SYSTEM, TelemetryEvent
from src.app.modules.telemetry.reader.filesystem import FileSystemLogReader
from src.app.modules.telemetry.writers.postgres import PostgresWriter
from src.app.modules.telemetry.writers.telegram import (
    TelegramWriter,
    parse_destination,
    parse_destination_map,
)
from src.app.shared_kernel.config.infra_configs import (
    DatabaseConfig,
    TelegramConfig,
    TelemetryConfig,
)

logger = logging.getLogger("telemetry.runner")


def _telegram_route(min_level: str):
    """Errors / 5xx / system only - keeps Telegram from being spammed."""
    at_level = MinLevel(min_level)
    server_error = StatusAtLeast(500, pass_when_missing=False)

    def _route(event: TelemetryEvent) -> bool:
        return event.kind == KIND_SYSTEM or at_level(event) or server_error(event)

    return _route


def build_composer(
    tel_cfg: TelemetryConfig,
    tg_cfg: TelegramConfig,
    db_cfg: DatabaseConfig,
) -> TelemetryComposer:
    global_pipeline = FilterPipeline(
        [
            MinLevel(tel_cfg.min_level),
            ExcludeUrls(tel_cfg.excluded_prefixes),
        ]
    )

    routes: list[Route] = []

    if tel_cfg.postgres_enabled:
        routes.append(
            (
                PostgresWriter(
                    db_cfg.asyncpg_dsn,
                    table=tel_cfg.postgres_table,
                    batch_size=tel_cfg.postgres_batch_size,
                ),
                FilterPipeline(),  # store everything that passed the global gate
            )
        )
        logger.info("telemetry: Postgres writer enabled")

    if tel_cfg.telegram_enabled and tg_cfg.enabled:
        assert tg_cfg.bot_token and tg_cfg.chat_id  # guaranteed by .enabled
        default_dest = parse_destination(tg_cfg.chat_id)
        system_dest = (
            parse_destination(tg_cfg.system_chat_id) if tg_cfg.system_chat_id else None
        )
        routes.append(
            (
                TelegramWriter(
                    bot_token=tg_cfg.bot_token,
                    default=default_dest,
                    system=system_dest,
                    service_routes=parse_destination_map(tg_cfg.service_routes),
                    level_routes=parse_destination_map(tg_cfg.level_routes),
                    global_rate=tg_cfg.global_rate,
                    per_chat_rate=tg_cfg.per_chat_rate,
                ),
                _telegram_route(tel_cfg.telegram_min_level),
            )
        )
        logger.info("telemetry: Telegram writer enabled")

    if not routes:
        logger.warning(
            "telemetry: no writers enabled - events will be read and dropped"
        )

    return TelemetryComposer(global_pipeline, routes)


async def run() -> None:
    tel_cfg = TelemetryConfig()
    tg_cfg = TelegramConfig()
    db_cfg = DatabaseConfig()  # type: ignore[call-arg]  # pydantic-settings loads from env

    reader = FileSystemLogReader(
        tel_cfg.log_dir,
        poll_interval=tel_cfg.poll_interval,
        from_end=tel_cfg.from_end,
    )
    composer = build_composer(tel_cfg, tg_cfg, db_cfg)

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover - windows
            pass

    await composer.start()
    logger.info("telemetry daemon started (log_dir=%s)", tel_cfg.log_dir)

    consume = asyncio.create_task(_consume(reader, composer))
    await stop.wait()

    logger.info("telemetry daemon shutting down")
    await reader.aclose()
    consume.cancel()
    await composer.aclose()


async def _consume(reader: FileSystemLogReader, composer: TelemetryComposer) -> None:
    try:
        async for event in reader:
            composer.dispatch(event)
    except asyncio.CancelledError:  # pragma: no cover
        pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    asyncio.run(run())


if __name__ == "__main__":
    main()
