"""Telegram writer: fully async, rate-limited, with its own buffering queue.

Rate limiting is enforced by two token buckets (global + per-destination). When a
limit is hit the consumer simply awaits a token, so pending events pile up in the
writer's own queue rather than being sent - i.e. "if the limit is reached, keep
them in its own queue". Also supports out-of-band *system* notifications.

Destinations support both a plain chat/group/channel and a topic (thread) inside
a forum-mode supergroup, via :class:`TelegramDestination`. A destination string
is ``chat_id`` for a plain chat, or ``chat_id:thread_id`` for a topic - the same
format used to configure routes in ``TelegramConfig``.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Mapping, Optional

import httpx

from src.app.modules.telemetry.logging.event import (
    KIND_SYSTEM,
    SERVICE_API,
    TelemetryEvent,
)
from src.app.modules.telemetry.writers.base import AbstractWriter
from src.app.modules.telemetry.writers.rate_limit import TokenBucket

logger = logging.getLogger("telemetry.writer.telegram")

_LEVEL_EMOJI = {
    "DEBUG": "🔧",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "🛑",
    "CRITICAL": "🔥",
}
_MAX_TEXT = 3800  # Telegram hard limit is 4096; leave headroom for the header.


@dataclass(frozen=True)
class TelegramDestination:
    """A plain chat/group/channel, or a topic (thread) inside a forum supergroup."""

    chat_id: str
    thread_id: Optional[int] = None

    def key(self) -> str:
        """Stable identity for per-destination rate limiting."""
        return (
            self.chat_id
            if self.thread_id is None
            else f"{self.chat_id}#{self.thread_id}"
        )


def parse_destination(raw: str) -> TelegramDestination:
    """Parse ``chat_id`` or ``chat_id:thread_id`` (supergroup topic) into a destination."""
    raw = raw.strip()
    if ":" in raw:
        chat_id, _, thread = raw.rpartition(":")
        if chat_id and thread.strip().lstrip("-").isdigit():
            return TelegramDestination(chat_id=chat_id, thread_id=int(thread))
    return TelegramDestination(chat_id=raw)


def parse_destination_map(raw: str) -> dict[str, TelegramDestination]:
    """Parse ``key=dest,key2=dest2`` (e.g. per-service or per-level routes)."""
    routes: dict[str, TelegramDestination] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or "=" not in pair:
            continue
        key, _, value = pair.partition("=")
        if key.strip() and value.strip():
            routes[key.strip()] = parse_destination(value)
    return routes


class TelegramWriter(AbstractWriter):
    name = "telegram"

    def __init__(
        self,
        bot_token: str,
        default: TelegramDestination,
        *,
        system: Optional[TelegramDestination] = None,
        service_routes: Optional[Mapping[str, TelegramDestination]] = None,
        level_routes: Optional[Mapping[str, TelegramDestination]] = None,
        global_rate: float = 25.0,
        per_chat_rate: float = 1.0,
        maxsize: int = 10_000,
    ) -> None:
        super().__init__(maxsize=maxsize, batch_size=1, flush_interval=0.5)
        self._bot_token = bot_token
        self._default = default
        self._system = system or default
        self._service_routes = dict(service_routes or {})
        self._level_routes = dict(level_routes or {})
        self._client: Optional[httpx.AsyncClient] = None
        self._global_bucket = TokenBucket(rate=global_rate)
        self._per_chat_rate = per_chat_rate
        self._dest_buckets: dict[str, TokenBucket] = {}

    # --- public API -----------------------------------------------------------

    def notify_system(self, message: str) -> None:
        """Queue a system notification (the system speaking, not a log line)."""
        self.submit(
            TelemetryEvent(
                service=SERVICE_API,
                level="INFO",
                kind=KIND_SYSTEM,
                message=message,
            )
        )

    # --- writer hooks ---------------------------------------------------------

    async def _on_start(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=f"https://api.telegram.org/bot{self._bot_token}",
            timeout=httpx.Timeout(15.0),
        )

    async def _on_close(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _handle_batch(self, batch: list[TelemetryEvent]) -> None:
        for event in batch:
            await self._send(self._route(event), self._format(event))

    # --- internals ------------------------------------------------------------

    def _route(self, event: TelemetryEvent) -> TelegramDestination:
        """Per-service routes win (dedicated topic/chat), then per-level, then default."""
        if event.kind == KIND_SYSTEM:
            return self._system
        dest = self._service_routes.get(event.service)
        if dest is not None:
            return dest
        dest = self._level_routes.get(event.level)
        if dest is not None:
            return dest
        return self._default

    def _bucket(self, dest: TelegramDestination) -> TokenBucket:
        key = dest.key()
        bucket = self._dest_buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(rate=self._per_chat_rate)
            self._dest_buckets[key] = bucket
        return bucket

    async def _send(
        self, dest: TelegramDestination, text: str, *, _retries: int = 2
    ) -> None:
        if self._client is None:
            return
        await self._global_bucket.acquire()
        await self._bucket(dest).acquire()

        payload: dict = {
            "chat_id": dest.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if dest.thread_id is not None:
            payload["message_thread_id"] = dest.thread_id

        try:
            resp = await self._client.post("/sendMessage", json=payload)
        except httpx.HTTPError as exc:
            logger.warning("telegram send failed: %s", exc)
            return

        if resp.status_code == 429 and _retries > 0:
            retry_after = 1.0
            try:
                retry_after = float(resp.json()["parameters"]["retry_after"])
            except (ValueError, KeyError, TypeError):
                pass
            await asyncio.sleep(retry_after)
            await self._send(dest, text, _retries=_retries - 1)
        elif resp.status_code >= 400:
            logger.warning("telegram API %s: %s", resp.status_code, resp.text[:200])

    @staticmethod
    def _format(event: TelemetryEvent) -> str:
        emoji = _LEVEL_EMOJI.get(event.level, "•")
        if event.kind == KIND_SYSTEM:
            return f"{emoji} <b>SYSTEM</b>\n{_escape(event.message or '')}"[:_MAX_TEXT]

        lines = [f"{emoji} <b>{event.level}</b> · <code>{event.service}</code>"]
        if event.method or event.url:
            status = f" → {event.status_code}" if event.status_code else ""
            lines.append(
                f"{event.method or ''} {_escape(event.url or '')}{status}".strip()
            )
        meta = []

        if event.exec_ms is not None:
            meta.append(f"{event.exec_ms:.0f}ms")
        if event.user_id is not None:
            meta.append(f"user={event.user_id}")
        if event.ip:
            meta.append(f"ip={event.ip}")
        if meta:
            lines.append(" · ".join(meta))
        if event.trace_id:
            lines.append(f"trace_id=<code>{event.trace_id}</code>")
        if event.message:
            lines.append(_escape(event.message))
        return "\n".join(lines)[:_MAX_TEXT]


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
