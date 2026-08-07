from __future__ import annotations

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from backend.database.models.user import UserModel, UserRole

logger = logging.getLogger(__name__)

class UserRepository:
    @staticmethod
    def create_user(
        session: Session,
        user_id: str,
        username: str,
        email: str,
        hashed_password: str,
        role: UserRole = UserRole.VIEWER
    ) -> UserModel:
        logger.info("Persisting new user entity for username: %s", username)
        user = UserModel(
            id=user_id,
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    @staticmethod
    def get_user_by_id(session: Session, user_id: str) -> Optional[UserModel]:
        return session.query(UserModel).filter(UserModel.id == user_id).first()

    @staticmethod
    def get_user_by_username(session: Session, username: str) -> Optional[UserModel]:
        return session.query(UserModel).filter(UserModel.username == username).first()

    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[UserModel]:
        return session.query(UserModel).filter(UserModel.email == email).first()

    @staticmethod
    def list_users(session: Session) -> List[UserModel]:
        return session.query(UserModel).all()