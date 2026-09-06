from functools import cached_property
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig

# Ports are declared *inside* the network the app runs in, and they are the
# well-known defaults for their service. The host-side port a container is
# published on is a compose concern and never reaches the application.
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_REDIS_PORT = 6379
DEFAULT_SMTP_PORT = 587


class DatabaseConfig(BasePydanticConfig):
    """Everything under ``POSTGRES_*``.

    The prefix is the technology rather than the class name on purpose: the same
    four variables configure both this client and the postgres container itself,
    which reads ``POSTGRES_DB`` / ``POSTGRES_USER`` / ``POSTGRES_PASSWORD``.
    """

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    db: str
    user: str
    password: str
    host: str = Field(default="localhost")
    port: int = Field(default=DEFAULT_POSTGRES_PORT)
    driver: str = Field(default="asyncpg")

    @cached_property
    def url(self) -> str:
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @cached_property
    def asyncpg_dsn(self) -> str:
        """Plain libpq DSN for a direct ``asyncpg`` connection (no SQLAlchemy driver)."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class JwtConfig(BasePydanticConfig):
    """Everything under ``JWT_*``.

    ``secret_key`` is its own value, not the application secret: rotating the
    token-signing key should invalidate sessions without touching anything else
    that was encrypted with ``APP_SECRET_KEY``.
    """

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str
    algorithm: str = Field(default="HS256")
    access_token_lifetime: int = Field(default=3600)  # seconds
    refresh_token_lifetime: int = Field(default=30)  # days


class RedisConfig(BasePydanticConfig):
    """Everything under ``REDIS_*``."""

    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str = Field(default="localhost")
    port: int = Field(default=DEFAULT_REDIS_PORT)
    # Optional on purpose: a Redis reachable only inside the compose network
    # normally runs without auth.
    password: Optional[str] = Field(default=None)


class SmtpConfig(BasePydanticConfig):
    """Everything under ``SMTP_*``.

    All four credentials or none: a half-configured mailer starts fine and then
    fails on the first confirmation email, which is the worst moment to find out.
    """

    model_config = SettingsConfigDict(env_prefix="SMTP_")

    host: Optional[str] = Field(default=None)
    port: int = Field(default=DEFAULT_SMTP_PORT)
    username: Optional[str] = Field(default=None)  # Email address
    password: Optional[str] = Field(default=None)
    timeout: int = Field(default=5)

    def model_post_init(self, context: Any, /) -> None:
        self._require_all_or_none(("host", "username", "password"), "SMTP")

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.username and self.password)


class TelegramConfig(BasePydanticConfig):
    """Everything under ``TELEGRAM_*``.

    Raw telegram settings. Parsed into ``TelegramDestination``s by the writer.

    ``chat_id`` / ``system_chat_id`` accept either a plain group/channel id
    (``-100123456789``) or a topic inside a forum-mode supergroup
    (``-100123456789:12``, where ``12`` is the topic's ``message_thread_id``).
    ``service_routes`` / ``level_routes`` map an event's service or level to its
    own destination (same ``chat[:thread]`` format), e.g.
    ``TELEGRAM_SERVICE_ROUTES=api=-100123:12,telemetry=-100123:34`` - handy for
    one topic per service inside a single private supergroup.
    """

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    bot_token: Optional[str] = Field(default=None)
    chat_id: Optional[str] = Field(default=None)
    system_chat_id: Optional[str] = Field(default=None)
    service_routes: str = Field(default="")
    level_routes: str = Field(default="")
    global_rate: float = Field(default=25.0)
    per_chat_rate: float = Field(default=1.0)

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


class TelemetryConfig(BasePydanticConfig):
    """Everything under ``TELEMETRY_*``."""

    model_config = SettingsConfigDict(env_prefix="TELEMETRY_")

    # Which process wrote a record. One log file per service; the daemon tails
    # them all. Each container overrides it (api, telemetry, ...).
    service: str = Field(default="api")

    log_dir: str = Field(default="logs")
    poll_interval: float = Field(default=0.5)
    from_end: bool = Field(default=True)

    # Global gate + Telegram-only gate.
    min_level: str = Field(default="INFO")
    telegram_min_level: str = Field(default="ERROR")
    exclude_url_prefixes: str = Field(
        default="/healthcheck,/api/v1/docs,/api/v1/get-schema"
    )

    # Writers.
    postgres_enabled: bool = Field(default=True)
    telegram_enabled: bool = Field(default=False)

    # Don't touch it at all
    postgres_table: str = Field(default="telemetry_log")
    postgres_batch_size: int = Field(default=200)

    @property
    def excluded_prefixes(self) -> tuple[str, ...]:
        return tuple(
            p.strip() for p in self.exclude_url_prefixes.split(",") if p.strip()
        )
