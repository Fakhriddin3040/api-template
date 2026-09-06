import base64
from datetime import tzinfo
from functools import cached_property
from pathlib import Path

from pydantic import Field, field_validator

from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig
from src.app.shared_kernel.constants.datetime_const import resolve_timezone
from src.app.shared_kernel.types.base_types import Environment


class AppConfig(BasePydanticConfig):
    environment: Environment
    app_root: Path = Field(default=Path(__file__).parent.parent.parent.parent.parent)
    secret_key: str = Field(alias="APP_SECRET_KEY")
    domain: str = Field(alias="APP_DOMAIN")

    # IANA name, e.g. "Europe/Berlin". UTC by default — see datetime_const.
    timezone_name: str = Field(default="UTC", alias="APP_TIMEZONE")

    # Static.
    #
    # ``media`` is the storage *root*; the paths stored on a blob row are
    # relative to it. Keeping the root out of the stored value is what lets
    # readers build a URL with ``make_media_full_url``
    # (-> ``https://host/media/<stored>``) and lets the root move without
    # rewriting every row.
    media: Path = Field(default=Path("media"), init=False, frozen=True)
    file_path: Path = Field(default=Path("files"), init=False, frozen=True)
    image_path: Path = Field(default=Path("images"), init=False, frozen=True)

    @property
    def media_root(self) -> Path:
        """Absolute on-disk directory the stored relative paths resolve against."""
        return self.app_root / self.media

    @cached_property
    def timezone(self) -> tzinfo:
        return resolve_timezone(self.timezone_name)

    # AES secret must be given in base64 encoding and in parse time must be decoded into raw bytes
    aes_key: bytes = Field(alias="AES_SECRET_KEY")

    @field_validator("aes_key", mode="before")
    def secret_key_validator(cls, v) -> bytes:
        if isinstance(v, bytes):
            return v

        return base64.b64decode(v.encode("utf-8"))
