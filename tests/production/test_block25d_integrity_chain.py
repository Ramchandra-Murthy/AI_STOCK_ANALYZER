from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_block25d_production_integrity_chain():
    """
    Validates that a production API request through EROS 3.0
    preserves the entire integrity, confidence, scoring, and decision chain.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": "RELIANCE.NS",
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload

    data = payload["data"]
    assert data["symbol"] == "RELIANCE.NS"
    assert data["status"] in ["SUCCESS", "REJECTED_BY_INTEGRITY_GATE"]

    if data["status"] == "SUCCESS":
        # 1. Market Data & State Verification
        assert "market_data" in data
        market_data = data["market_data"]
        assert "current_price" in market_data
        assert float(market_data["current_price"]) > 0.0
        assert "state" in market_data

        # 2. Confidence Metrics & Attenuation Verification
        assert "confidence_metrics" in data
        conf = data["confidence_metrics"]
        assert "base_confidence" in conf
        assert "confidence_penalty" in conf
        assert "adjusted_confidence" in conf
        assert 0.0 <= float(conf["adjusted_confidence"]) <= float(conf["base_confidence"])

        # 3. Investment Decision & Orchestration Verification
        assert "investment_decision" in data
        decision = data["investment_decision"]
        assert "final_action" in decision
        assert decision["final_action"] in ["BUY", "STRONG BUY", "HOLD", "REDUCE", "SELL"]
        assert "composite_score" in decision
        assert float(decision["composite_score"]) >= 0.0
        assert "target_allocation" in decision

        # 4. Immutable Audit Trace Verification
        assert "audit_trace" in data
        trace = data["audit_trace"]
        assert "timestamp" in trace
        assert "engine_version" in trace
    else:
        # If rejected by integrity gate, ensure safe fallback trace is preserved
        assert "directive" in data
        assert "warning_message" in data
        assert "trace" in data
        assert data["directive"] == "REJECT_DATA"
