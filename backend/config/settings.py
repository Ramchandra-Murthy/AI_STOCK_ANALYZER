from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "EROS 3.0 Institutional Research Platform"
    VERSION: str = "3.0.0"

    DATABASE_URL: str = "sqlite:///./eros_production.db"
    REDIS_URL: str = "redis://127.0.0.1:6379/0"

    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    SECRET_KEY: str = "eros_3_0_change_me"
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AUTH_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

# JWT_SECRET takes precedence when explicitly configured.
if settings.JWT_SECRET:
    settings.SECRET_KEY = settings.JWT_SECRET


# Compatibility accessor used by application security dependencies.
def get_settings() -> Settings:
    return settings
