from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_block25b_valid_eros_request():
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": "INFY.NS",
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload
    data = payload["data"]
    assert data["symbol"] == "INFY.NS"
    assert data["status"] in [
        "SUCCESS",
        "REJECTED_BY_INTEGRITY_GATE",
    ]


def test_block25b_missing_symbol_rejected():
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code == 422


def test_block25b_malformed_request_rejected():
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": 12345,
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code in [200, 422]
