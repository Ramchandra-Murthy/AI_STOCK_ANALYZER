from __future__ import annotations

import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Force passlib to use the standard bcrypt backend without inspecting missing attributes
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__default_backend="bcrypt")

class PasswordSecurity:
    @staticmethod
    def hash_password(password: str) -> str:
        # Truncate to 72 bytes to adhere to bcrypt strict length limit
        encoded_pwd = password.encode("utf-8")[:72]
        return pwd_context.hash(encoded_pwd)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        encoded_pwd = plain_password.encode("utf-8")[:72]
        return pwd_context.verify(encoded_pwd, hashed_password)