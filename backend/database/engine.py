from __future__ import annotations

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

DATABASE_URL = "sqlite:///./eros_production.db"

engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db() -> None:
    logger.info("Initializing production database tables via SQLAlchemy Base metadata")
    Base.metadata.create_all(bind=engine)
