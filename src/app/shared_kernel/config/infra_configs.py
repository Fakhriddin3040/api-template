from functools import cached_property
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig


class DatabaseConfig(BasePydanticConfig):
    user: str
    password: str
    db: str
    host: str
    port: int
    driver: str = Field(default="asyncpg")

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_",
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @cached_property
    def url(self) -> str:
        return f"postgresql+{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"

    @cached_property
    def asyncpg_dsn(self) -> str:
        """Plain libpq DSN for a direct ``asyncpg`` connection (no SQLAlchemy driver)."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class JwtConfig(BasePydanticConfig):
    secret_key: str = Field(alias="APP_SECRET_KEY")
    hash_algorithm: str = Field(alias="ALGORITHM")
    access_token_lifetime: int = Field(alias="ACCESS_TOKEN_LIFETIME")  # seconds
    refresh_token_lifetime: int = Field(alias="REFRESH_TOKEN_LIFETIME")  # days


class RedisConfig(BasePydanticConfig):
    host: str = Field(None)
    port: int = Field(None)
    password: str = Field(None)

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, context: Any, /) -> None:
        values = self.model_fields().values()
        if any(values) and not all(values):
            raise ValueError("Redis config must be fully set or not set at all.")


class SmtpConfig(BasePydanticConfig):
    host: str = Field(None)
    port: int = Field(None)
    username: str = Field(None)  # Email address
    password: str = Field(None)
    timeout: int = Field(default=5)

    model_config = SettingsConfigDict(
        env_prefix="SMTP_",
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, context: Any, /) -> None:
        values = self.model_fields.values()
        if any(values) and not all(values):
            raise ValueError("SMTP config must be fully set or not set at all.")


class TelegramConfig(BasePydanticConfig):
    """Raw telegram settings. Parsed into ``TelegramDestination``s by the writer.

    ``chat_id`` / ``system_chat_id`` accept either a plain group/channel id
    (``-100123456789``) or a topic inside a forum-mode supergroup
    (``-100123456789:12``, where ``12`` is the topic's ``message_thread_id``).
    ``service_routes`` / ``level_routes`` map an event's service or level to its
    own destination (same ``chat[:thread]`` format), e.g.
    ``TELEGRAM_SERVICE_ROUTES=api=-100123:12,beat=-100123:34,worker=-100123:56`` -
    handy for one topic per service inside a single private supergroup.
    """

    bot_token: Optional[str] = Field(default=None)
    chat_id: Optional[str] = Field(default=None)
    system_chat_id: Optional[str] = Field(default=None)
    service_routes: str = Field(default="")
    level_routes: str = Field(default="")
    global_rate: float = Field(default=25.0)
    per_chat_rate: float = Field(default=1.0)

    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_",
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def enabled(self) -> bool:
        return bool(self.bot_token and self.chat_id)


class TelemetryConfig(BasePydanticConfig):
    log_dir: str = Field(default="logs")
    service: str = Field(alias="SERVICE_NAME")
    poll_interval: float = Field(default=0.5)
    from_end: bool = Field(default=True)

    # Global gate + Telegram-only gate.
    min_level: str = Field(default="INFO")
    telegram_min_level: str = Field(default="ERROR")
    exclude_url_prefixes: str = Field(
        default="/healthcheck,/api/v2/docs,/docs,/get-schema"
    )

    # Writers.
    postgres_enabled: bool = Field(default=True)
    telegram_enabled: bool = Field(default=True)

    # Don't touch it at all
    postgres_table: str = Field(default="telemetry_log")
    postgres_batch_size: int = Field(default=200)

    model_config = SettingsConfigDict(
        env_prefix="TELEMETRY_",
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def excluded_prefixes(self) -> tuple[str, ...]:
        return tuple(
            p.strip() for p in self.exclude_url_prefixes.split(",") if p.strip()
        )
