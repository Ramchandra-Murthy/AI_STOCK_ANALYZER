from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy import Enum as SQLEnum

from backend.database.engine import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    RESEARCHER = "RESEARCHER"
    VIEWER = "VIEWER"


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
