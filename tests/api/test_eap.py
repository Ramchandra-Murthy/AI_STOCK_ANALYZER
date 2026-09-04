from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.database.engine import init_db

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "3.0"


def test_readiness_endpoint() -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_valuation_api_endpoint() -> None:
    init_db()

    unique_suffix = uuid.uuid4().hex[:6]
    username = f"api_analyst_{unique_suffix}"
    email = f"api_analyst_{unique_suffix}@eros.org"
    password = "Password123!"

    reg_payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": "ANALYST",
    }

    register_response = client.post(
        "/api/v1/auth/register",
        json=reg_payload,
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    payload = {
        "symbol": "RELIANCE.NS",
        "current_price": 2500.0,
        "eps": 110.0,
        "growth_rate": 0.08,
        "discount_rate": 0.12,
    }

    response = client.post(
        "/api/v1/valuation",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["symbol"] == "RELIANCE.NS"
    assert data["intrinsic_value"] > 0
    assert "margin_of_safety" in data
    assert "recommendation" in data
