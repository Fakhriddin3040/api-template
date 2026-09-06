import base64
from datetime import tzinfo
from functools import cached_property
from pathlib import Path
from typing import Tuple

from pydantic import Field, field_validator
from pydantic_settings import SettingsConfigDict

from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig
from src.app.shared_kernel.constants.datetime_const import resolve_timezone
from src.app.shared_kernel.types.base_types import Environment

_DEBUG_ENVIRONMENTS = ("development", "testing")


class AppConfig(BasePydanticConfig):
    """Everything under ``APP_*``."""

    model_config = SettingsConfigDict(env_prefix="APP_")

    environment: Environment = Field(default="development")

    secret_key: str

    # Bare public host, no scheme and no trailing slash: "api.example.com" or
    # "localhost:8000". The scheme is derived from the environment, so there is
    # no second variable to keep in sync.
    domain: str = Field(default="localhost:8000")

    # IANA name, e.g. "Europe/Berlin". UTC by default — see datetime_const.
    timezone: str = Field(default="UTC")

    # AES secret, given base64-encoded and decoded to raw bytes at parse time.
    aes_key: bytes

    # Comma separated. Empty means "every origin" in a debug environment and
    # "none" otherwise — see `cors_origins`.
    cors_allowed_origins: str = Field(default="")

    # Static.
    #
    # ``media`` is the storage *root*; the paths stored on a blob row are
    # relative to it. Keeping the root out of the stored value is what lets
    # readers build a URL with ``make_media_full_url``
    # (-> ``https://host/media/<stored>``) and lets the root move without
    # rewriting every row.
    #
    # Not settings: they are structural, and a deployment that moves them would
    # orphan every stored path.
    app_root: Path = Field(
        default=Path(__file__).parent.parent.parent.parent.parent, frozen=True
    )
    media: Path = Field(default=Path("media"), init=False, frozen=True)
    file_path: Path = Field(default=Path("files"), init=False, frozen=True)
    image_path: Path = Field(default=Path("images"), init=False, frozen=True)

    @field_validator("aes_key", mode="before")
    def secret_key_validator(cls, v) -> bytes:
        if isinstance(v, bytes):
            return v

        return base64.b64decode(v.encode("utf-8"))

    @property
    def debug(self) -> bool:
        return self.environment in _DEBUG_ENVIRONMENTS

    @property
    def scheme(self) -> str:
        """http locally, https everywhere else.

        Hardcoding https would emit links that simply do not resolve against a
        local server, and hardcoding http would downgrade production.
        """
        return "http" if self.debug else "https"

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.domain}"

    @property
    def cors_origins(self) -> Tuple[str, ...]:
        """Origins allowed to call the API.

        A wildcard is convenient while developing but browsers refuse it
        together with credentials, so a non-debug environment has to list its
        origins explicitly rather than silently falling back to ``*``.
        """
        raw = self.cors_allowed_origins.strip()

        if raw:
            return tuple(o.strip() for o in raw.split(",") if o.strip())

        return ("*",) if self.debug else ()

    @property
    def media_root(self) -> Path:
        """Absolute on-disk directory the stored relative paths resolve against."""
        return self.app_root / self.media

    @cached_property
    def tzinfo(self) -> tzinfo:
        return resolve_timezone(self.timezone)
