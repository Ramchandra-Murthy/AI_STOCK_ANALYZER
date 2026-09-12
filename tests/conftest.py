from __future__ import annotations

import pytest

from backend.security.jwt import JWTSecurity


@pytest.fixture
def sample_fixture() -> str:
    return "AIERP-TEST-READY"


@pytest.fixture
def auth_headers():
    def _auth_headers(role: str = "ANALYST") -> dict[str, str]:
        token = JWTSecurity.create_access_token(
            {
                "sub": f"test_{role.lower()}",
                "username": f"test_{role.lower()}",
                "role": role,
            }
        )
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
