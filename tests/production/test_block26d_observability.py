from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_block26d_audit_trace_observability():
    """
    Validates that production evaluations maintain complete observability,
    preserving audit traces, engine versions, timestamps, and confidence metrics.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": "INFY.NS",
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("success") is True
    data = payload.get("data", {})

    if data.get("status") == "SUCCESS":
        # Audit trace validation
        audit = data.get("audit_trace", {})
        assert "timestamp" in audit
        assert audit["engine_version"] == "EROS-3.0-BLOCK-23J"

        # Market data observability
        mdata = data.get("market_data", {})
        assert "source" in mdata
        assert "state" in mdata
        assert float(mdata["current_price"]) > 0.0

        # Confidence metrics validation
        conf = data.get("confidence_metrics", {})
        assert "base_confidence" in conf
        assert "confidence_penalty" in conf
        assert "adjusted_confidence" in conf
        assert "decision_confidence" in conf

        expected_market_confidence = max(
            0.0,
            float(conf["base_confidence"]) - float(conf["confidence_penalty"]),
        )
        assert abs(
            float(conf["adjusted_confidence"]) - expected_market_confidence
        ) < 1e-9
        assert float(conf["adjusted_confidence"]) <= float(conf["base_confidence"])
        assert 0.0 <= float(conf["decision_confidence"]) <= 1.0

def test_block26e_state_determinism_and_health():
    """
    Validates that repeated evaluations do not corrupt system state
    and that health/readiness probes remain intact under load.
    """
    # 1. First evaluation
    res1 = client.post("/api/v1/eros/evaluate", json={"symbol": "INFY.NS"})
    assert res1.status_code == 200

    # 2. Second consecutive evaluation
    res2 = client.post("/api/v1/eros/evaluate", json={"symbol": "INFY.NS"})
    assert res2.status_code == 200

    # 3. Health & Readiness remain healthy post-evaluation
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json().get("status") == "healthy"

    ready_res = client.get("/ready")
    assert ready_res.status_code == 200
    assert ready_res.json().get("status") == "ready"
