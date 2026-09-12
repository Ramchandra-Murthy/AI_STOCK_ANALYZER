from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from backend.config.settings import settings

logger = logging.getLogger(__name__)


class JWTSecurity:

    @staticmethod
    def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:

        if not settings.JWT_SECRET:
            raise RuntimeError("JWT_SECRET is not configured")

        to_encode = data.copy()

        expire = datetime.now(UTC) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        to_encode.update({"exp": expire, "iss": "eros-enterprise-platform"})

        return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def decode_access_token(token: str) -> dict[str, Any] | None:

        if not settings.JWT_SECRET:
            logger.error("JWT_SECRET is not configured")
            return None

        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

        except JWTError as exc:
            logger.warning("JWT decoding failed: %s", exc)
            return None
