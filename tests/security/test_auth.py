from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.database.engine import init_db
from backend.main import app
from backend.security.jwt import JWTSecurity
from backend.security.passwords import PasswordSecurity

client = TestClient(app)


def test_password_hashing_and_verification() -> None:
    raw_pwd = "SecureEnterprisePassword2026!"
    hashed = PasswordSecurity.hash_password(raw_pwd)
    assert PasswordSecurity.verify_password(raw_pwd, hashed) is True
    assert PasswordSecurity.verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding() -> None:
    payload = {"sub": "admin_user", "role": "ADMIN"}
    token = JWTSecurity.create_access_token(payload)
    assert isinstance(token, str)

    decoded = JWTSecurity.decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "admin_user"
    assert decoded["role"] == "ADMIN"


def test_user_registration_and_login_flow() -> None:
    init_db()
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"analyst_{unique_suffix}"
    email = f"analyst_{unique_suffix}@eros.org"

    reg_payload = {
        "username": username,
        "email": email,
        "password": "Password123!",
        "role": "ANALYST",
    }
    # Register user
    resp = client.post("/api/v1/auth/register", json=reg_payload)
    assert resp.status_code == 201

    # Login user
    login_payload = {"username": username, "password": "Password123!"}
    login_resp = client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    assert data["user"]["username"] == username
    assert data["user"]["role"] == "ANALYST"
