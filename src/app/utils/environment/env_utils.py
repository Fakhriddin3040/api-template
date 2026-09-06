import os
from enum import StrEnum
from functools import lru_cache

from dependency_injector.wiring import Provide, inject

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.types.base_types import Environment


class DeploymentEnvironment(StrEnum):
    # Values match the `Environment` literal exactly — a mismatch here silently
    # makes every `is_*` check return False.
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TESTING = "testing"

    @classmethod
    @lru_cache
    @inject
    def get_environment(
        cls, app_config: AppConfig = Provide["config.app"]
    ) -> Environment:
        return (
            app_config.environment
            if isinstance(app_config, AppConfig)
            # Reachable only before the DI container is wired (an import-time
            # read, a standalone script).
            else os.environ.get("APP_ENVIRONMENT", cls.DEVELOPMENT.value)
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
        return cls.get_environment() == cls.TESTING.value

    @classmethod
    @lru_cache
    def should_debug(cls) -> bool:
        return cls.get_environment() in (cls.DEVELOPMENT, cls.TESTING)


@inject
def _app_config(app_config: AppConfig = Provide["config.app"]) -> AppConfig:
    return app_config


def cors_allowed_origins() -> tuple[str, ...]:
    """Origins allowed to call the API, from ``APP_CORS_ALLOWED_ORIGINS``."""
    return _app_config().cors_origins
