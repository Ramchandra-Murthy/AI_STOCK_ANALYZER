from __future__ import annotations
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./eros_production.db")
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

    class Config:
        env_file = ".env"

settings = Settings()
