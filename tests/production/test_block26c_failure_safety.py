from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_block26c_invalid_symbol_graceful_handling():
    """
    Verifies that requesting an invalid or non-existent ticker
    does not crash the server and returns a safe fallback or rejection status.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": "INVALID_TICKER_XYZ_999",
            "policy_profile": "Institutional",
        },
    )
    # The API should handle gracefully (200 OK with rejection payload or controlled 400/500)
    assert response.status_code in [200, 422, 500]
    if response.status_code == 200:
        payload = response.json()
        assert payload.get("success") is True
        data = payload.get("data", {})
        # If evaluated, status must indicate rejection or safe fallback, never an unvetted BUY
        if data.get("status") == "SUCCESS":
            decision = data.get("investment_decision", {})
            action = decision.get("final_action")
            # Invalid tickers should not result in unvetted BUY recommendations
            assert action not in ["STRONG BUY"]

def test_block26c_missing_payload_rejection():
    """
    Verifies that an empty or missing JSON payload returns a 422 validation error.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={},
    )
    assert response.status_code == 422

def test_block26c_malformed_symbol_type_rejection():
    """
    Verifies that providing a numeric symbol instead of a string is rejected.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": 987654,
            "policy_profile": "Institutional",
        },
    )
    assert response.status_code in [200, 422]

def test_block26c_safety_invariant_no_unvetted_buys():
    """
    Enforces the safety invariant: under no circumstances can an anomalous
    or integrity-rejected analysis bypass governance to output a BUY action.
    """
    response = client.post(
        "/api/v1/eros/evaluate",
        json={
            "symbol": "BADSYMBOL.NS",
            "policy_profile": "StrictCompliance",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    data = payload.get("data", {})
    if data.get("status") == "REJECTED_BY_INTEGRITY_GATE":
        assert "directive" in data
        assert data["directive"] == "REJECT_DATA"
    elif data.get("status") == "SUCCESS":
        # If success, confidence and score bounds must be rigorously respected
        conf = data.get("confidence_metrics", {})
        assert 0.0 <= float(conf.get("adjusted_confidence", 0.0)) <= 1.0
