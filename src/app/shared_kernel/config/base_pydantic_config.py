from typing import Iterable

from pydantic_settings import BaseSettings, SettingsConfigDict


class BasePydanticConfig(BaseSettings):
    """Common settings behaviour for every config in the project.

    Subclasses declare **only** their ``env_prefix`` — pydantic merges
    ``model_config`` across the MRO, so the file/encoding/casing rules are
    defined once here. That is what keeps the whole ``.env`` on one pattern:
    a variable's name is always ``<PREFIX>_<FIELD>``, never a hand-written alias.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Treat `FOO=` as "unset" so an empty line falls back to the default
        # instead of failing as an empty string.
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    def _require_all_or_none(self, fields: Iterable[str], label: str) -> None:
        """Guard a group of settings that only makes sense complete.

        Half-configured infrastructure is worse than none: the app starts, then
        fails on the first use with a connection error that says nothing about
        the real cause.
        """
        values = {name: getattr(self, name, None) for name in fields}

        if any(v is not None for v in values.values()) and not all(
            v is not None for v in values.values()
        ):
            missing = sorted(name for name, v in values.items() if v is None)
            prefix = self.model_config.get("env_prefix", "")
            raise ValueError(
                f"{label} is partially configured; missing: "
                + ", ".join(f"{prefix}{name}".upper() for name in missing)
            )
