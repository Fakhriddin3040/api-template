import logging
from typing import Optional

import redis.asyncio
from redis.backoff import ExponentialBackoff
from redis.retry import Retry

from src.app.modules.cache.ports import CacheClientProto
from src.app.shared_kernel.config.infra_configs import RedisConfig
from src.app.shared_kernel.utils.static_analys.assertion_funcs import (
    ensure_isimplementation,
)

logger = logging.getLogger(__name__)


class RedisClient(CacheClientProto):
    """Redis-backed cache.

    Reads never raise: a cache outage degrades to a miss rather than taking the
    request with it. Writes are best-effort for the same reason.
    """

    def __init__(self, config: RedisConfig) -> None:
        self._config = config
        self._client = redis.asyncio.Redis(
            host=self._config.host,
            port=self._config.port,
            password=self._config.password or None,
            socket_connect_timeout=1.0,
            socket_timeout=2.0,
            socket_keepalive=True,
            health_check_interval=30,
            max_connections=50,
            db=0,
            retry_on_timeout=True,
            decode_responses=False,
            retry=Retry(ExponentialBackoff(cap=1.0, base=0.05), retries=3),
            retry_on_error=[ConnectionError, TimeoutError, ConnectionResetError],
        )

    async def set(self, key: str, value: bytes, ttl: Optional[float] = None) -> None:
        try:
            await self._client.set(key, value, ex=int(ttl) if ttl else None)
        except Exception:  # noqa: BLE001 - a cache must never fail the request
            logger.warning("cache set failed for key %s", key, exc_info=True)

    async def get(self, key: str) -> Optional[bytes]:
        try:
            return await self._client.get(key)
        except Exception:  # noqa: BLE001
            logger.warning("cache get failed for key %s", key, exc_info=True)
            return None

    async def invalidate(self, *keys: str) -> None:
        if not keys:
            return

        try:
            await self._client.delete(*keys)
        except Exception:  # noqa: BLE001
            logger.warning("cache invalidate failed", exc_info=True)

    async def close(self) -> None:
        """Gracefully close cache client connections."""
        await self._client.aclose(close_connection_pool=True)


ensure_isimplementation(RedisClient, CacheClientProto)
