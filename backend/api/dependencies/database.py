from __future__ import annotations

from collections.abc import Generator

from sqlalchemy.orm import Session

from backend.database.engine import SessionLocal


def get_session() -> Generator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
