from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.api.dependencies.database import get_session
from backend.api.schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse
from backend.services.user_service import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Identity"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, session: Session = Depends(get_session)) -> dict:
    user = UserService.register_user(
        session=session,
        username=payload.username,
        email=payload.email,
        password=payload.password,
        role=payload.role
    )
    return {
        "status": "SUCCESS",
        "message": f"User '{user.username}' created successfully.",
        "user_id": user.id
    }

@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    result = UserService.authenticate_user(
        session=session,
        username=payload.username,
        password=payload.password
    )
    return TokenResponse(**result)