from __future__ import annotations

from fastapi.testclient import TestClient

from backend.core.config.settings import settings
from backend.main import app

client = TestClient(app)


def test_settings_configuration_loading() -> None:
    assert settings.PROJECT_NAME is not None
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None


def test_system_liveness_endpoint() -> None:
    response = client.get("/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ALIVE"


def test_system_readiness_endpoint() -> None:
    response = client.get("/system/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["database"] == "CONNECTED"


def test_system_metrics_endpoint() -> None:
    response = client.get("/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "eros_http_requests_total" in data
    assert "eros_active_websocket_subscribers" in data
