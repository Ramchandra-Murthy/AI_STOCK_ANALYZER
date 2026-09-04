from __future__ import annotations

import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./eros_production.db",
)

if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )

logger.info(
    "Database engine configured: %s",
    DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def init_db() -> None:
    logger.info("Initializing database tables via SQLAlchemy Base metadata")
    Base.metadata.create_all(bind=engine)