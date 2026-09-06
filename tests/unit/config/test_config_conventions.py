"""The `.env` contract, enforced.

Every setting must be reachable as `<ENV_PREFIX>_<FIELD>`. These tests fail the
moment someone reintroduces an unprefixed name or a per-field alias — which is
how the previous layout ended up with `ACCESS_TOKEN_LIFETIME` next to
`TELEMETRY_MIN_LEVEL`.
"""

import pytest

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.config.base_pydantic_config import BasePydanticConfig
from src.app.shared_kernel.config.infra_configs import (
    DatabaseConfig,
    JwtConfig,
    RedisConfig,
    SmtpConfig,
    TelegramConfig,
    TelemetryConfig,
)

pytestmark = [pytest.mark.unit, pytest.mark.shared_kernel]

CONFIGS = [
    (AppConfig, "APP_"),
    (JwtConfig, "JWT_"),
    (DatabaseConfig, "POSTGRES_"),
    (RedisConfig, "REDIS_"),
    (SmtpConfig, "SMTP_"),
    (TelemetryConfig, "TELEMETRY_"),
    (TelegramConfig, "TELEGRAM_"),
]


@pytest.mark.parametrize("config_cls,prefix", CONFIGS, ids=lambda v: getattr(v, "__name__", v))
class TestConfigConventions:
    def test_declares_the_expected_prefix(self, config_cls, prefix):
        assert config_cls.model_config.get("env_prefix") == prefix

    def test_no_field_uses_an_alias(self, config_cls, prefix):
        """An alias silently opts a field out of the prefix scheme."""
        aliased = [
            name
            for name, info in config_cls.model_fields.items()
            if info.alias is not None or info.validation_alias is not None
        ]
        assert aliased == []

    def test_inherits_the_shared_settings_behaviour(self, config_cls, prefix):
        # Subclasses declare only `env_prefix`; everything else is merged in from
        # BasePydanticConfig across the MRO.
        assert issubclass(config_cls, BasePydanticConfig)
        assert config_cls.model_config["env_file"] == ".env"
        assert config_cls.model_config["env_ignore_empty"] is True
        assert config_cls.model_config["extra"] == "ignore"


class TestAppConfigDerivations:
    """The single-source-of-truth properties other code builds URLs from."""

    def _config(self, **overrides) -> AppConfig:
        defaults = dict(
            environment="development",
            secret_key="x",
            aes_key=b"0" * 32,
            domain="localhost:8000",
        )
        defaults.update(overrides)
        return AppConfig(**defaults)

    def test_scheme_follows_the_environment(self):
        assert self._config(environment="development").scheme == "http"
        assert self._config(environment="production").scheme == "https"

    def test_base_url_composes_scheme_and_domain(self):
        config = self._config(environment="production", domain="api.example.com")
        assert config.base_url == "https://api.example.com"

    def test_cors_falls_back_to_wildcard_only_in_debug(self):
        assert self._config(environment="development").cors_origins == ("*",)
        # Production must list origins explicitly — a wildcard is refused by
        # browsers alongside credentials.
        assert self._config(environment="production").cors_origins == ()

    def test_explicit_cors_origins_are_split(self):
        config = self._config(
            cors_allowed_origins="https://a.example.com, https://b.example.com"
        )
        assert config.cors_origins == (
            "https://a.example.com",
            "https://b.example.com",
        )


class TestPartialConfigIsRejected:
    def test_smtp_host_without_credentials_fails(self, monkeypatch):
        monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
        monkeypatch.delenv("SMTP_USERNAME", raising=False)
        monkeypatch.delenv("SMTP_PASSWORD", raising=False)

        with pytest.raises(ValueError, match="SMTP"):
            SmtpConfig()

    def test_no_smtp_settings_at_all_is_fine(self, monkeypatch):
        for name in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD"):
            monkeypatch.delenv(name, raising=False)

        assert SmtpConfig().enabled is False
