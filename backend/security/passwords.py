from __future__ import annotations

import logging

import bcrypt

logger = logging.getLogger(__name__)


class PasswordSecurity:
    @staticmethod
    def hash_password(password: str) -> str:
        # Truncate to 72 bytes to adhere to bcrypt strict length limit
        encoded_pwd = password.encode("utf-8")[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(encoded_pwd, salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        encoded_pwd = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        try:
            return bcrypt.checkpw(encoded_pwd, hashed_bytes)
        except Exception as e:
            logger.error("Password verification failed: %s", str(e))
            return False
