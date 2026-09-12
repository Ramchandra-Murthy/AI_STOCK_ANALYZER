from __future__ import annotations

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "EROS 3.0 Institutional Research Platform"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/eros_prod"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-production-key")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env.production"
        extra = "ignore"


settings = Settings()
