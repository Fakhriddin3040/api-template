import os
from enum import StrEnum, auto
from functools import lru_cache

from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.types.base_types import Environment


class DeploymentEnvironment(StrEnum):
    PRODUCTION = auto()
    DEVELOPMENT = auto()
    TEST = auto()

    @classmethod
    @lru_cache
    @inject
    def get_environment(
        cls, app_config: AppConfig = Provide["config.app"]
    ) -> Environment:
        return (
            app_config.environment
            if isinstance(app_config, AppConfig)
            else os.environ.get("ENVIRONMENT", "development")
        )

    @classmethod
    @lru_cache
    def is_prod(cls) -> bool:
        return cls.get_environment() == cls.PRODUCTION.value

    @classmethod
    @lru_cache
    def is_dev(cls) -> bool:
        return cls.get_environment() == cls.DEVELOPMENT.value

    @classmethod
    @lru_cache
    def is_test(cls) -> bool:
        return cls.get_environment() == cls.TEST.value

    @classmethod
    @lru_cache
    def is_local(cls) -> bool:
        return bool(os.environ.get("ENV_LOCAL", False))

    @classmethod
    @lru_cache
    def should_debug(cls) -> bool:
        return cls.get_environment() in (cls.DEVELOPMENT, cls.TEST)

    @classmethod
    @lru_cache
    def cors_allowed_origins(cls) -> tuple[str, ...]:
        """Origins allowed to call the API.

        A wildcard is fine while developing but is refused by browsers together
        with credentials, so production must list its origins explicitly via
        CORS_ALLOWED_ORIGINS (comma separated).
        """
        raw = os.environ.get("CORS_ALLOWED_ORIGINS", "").strip()

        if raw:
            return tuple(o.strip() for o in raw.split(",") if o.strip())

        return ("*",) if cls.should_debug() else ()
