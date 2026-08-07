from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app

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
    payload = {
        "symbol": "RELIANCE.NS",
        "current_price": 2500.0,
        "eps": 110.0,
        "growth_rate": 0.08,
        "discount_rate": 0.12
    }
    response = client.post("/api/v1/valuation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "RELIANCE.NS"
    assert data["intrinsic_value"] > 0
    assert "margin_of_safety" in data
    assert "recommendation" in data