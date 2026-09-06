from dependency_injector import containers, providers

from src.app.shared_kernel.config.app_config import AppConfig
from src.app.shared_kernel.config.infra_configs import (
    DatabaseConfig,
    JwtConfig,
    RedisConfig,
    SmtpConfig,
)


class ConfigurationDIContainer(containers.DeclarativeContainer):
    db: providers.Provider[DatabaseConfig] = providers.Singleton(DatabaseConfig)
    app: providers.Provider[AppConfig] = providers.Singleton(AppConfig)
    jwt: providers.Provider[JwtConfig] = providers.Singleton(JwtConfig)
    smtp: providers.Provider[SmtpConfig] = providers.Singleton(SmtpConfig)
    redis: providers.Provider[RedisConfig] = providers.Singleton(RedisConfig)
