from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_block25c_real_production_api_e2e():
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
    data = payload["data"]
    assert data["symbol"] == "INFY.NS"
    if data["status"] == "SUCCESS":
        assert "market_data" in data
        assert "confidence_metrics" in data
        assert "investment_decision" in data
        assert "audit_trace" in data
        decision = data["investment_decision"]
        assert "final_action" in decision
        assert decision["final_action"] in [
            "BUY",
            "STRONG BUY",
            "HOLD",
            "REDUCE",
            "SELL",
        ]
        assert 0.0 <= float(data["confidence_metrics"]["adjusted_confidence"]) <= 1.0
    elif data["status"] == "REJECTED_BY_INTEGRITY_GATE":
        assert "directive" in data
        assert "warning_message" in data
        assert "trace" in data
