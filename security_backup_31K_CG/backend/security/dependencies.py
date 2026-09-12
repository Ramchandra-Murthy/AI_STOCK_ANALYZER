from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.security.jwt import JWTSecurity

bearer_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict[str, Any]:
    token = credentials.credentials

    try:
        payload = JWTSecurity.decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_role(*allowed_roles: str):
    def role_dependency(
        current_user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:

        role = str(current_user.get("role", "")).upper()

        if allowed_roles and role not in {str(x).upper() for x in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_dependency
