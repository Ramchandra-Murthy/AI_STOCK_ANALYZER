from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.database.models.user import UserModel, UserRole
from backend.database.repositories.user_repository import UserRepository
from backend.exceptions import ValidationError
from backend.security.jwt import JWTSecurity
from backend.security.passwords import PasswordSecurity

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def register_user(
        session: Session, username: str, email: str, password: str, role: UserRole = UserRole.VIEWER
    ) -> UserModel:
        if UserRepository.get_user_by_username(session, username):
            raise ValidationError(f"Username '{username}' is already registered.")
        if UserRepository.get_user_by_email(session, email):
            raise ValidationError(f"Email '{email}' is already registered.")

        user_id = f"USR-{uuid.uuid4().hex[:8].upper()}"
        hashed_pw = PasswordSecurity.hash_password(password)
        return UserRepository.create_user(session, user_id, username, email, hashed_pw, role)

    @staticmethod
    def authenticate_user(session: Session, username: str, password: str) -> dict[str, Any]:
        user = UserRepository.get_user_by_username(session, username)
        if not user or not PasswordSecurity.verify_password(password, user.hashed_password):
            raise ValidationError("Invalid username or password.")
        if not user.is_active:
            raise ValidationError("User account is inactive.")

        user.last_login = datetime.utcnow()
        session.commit()

        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        }
        access_token = JWTSecurity.create_access_token(token_data)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
            },
        }
