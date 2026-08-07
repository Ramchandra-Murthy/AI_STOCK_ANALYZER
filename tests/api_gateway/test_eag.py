from __future__ import annotations

import pytest
from services.api_gateway.schemas import APIEndpointResponse
from services.api_gateway.rest_api import EnterpriseAPIGateway

def test_api_response_immutability() -> None:
    resp = APIEndpointResponse(
        endpoint="/valuation/RELIANCE.NS",
        status_code=200,
        data={"value": 3500.0},
        execution_time_ms=10.5
    )
    assert resp.endpoint == "/valuation/RELIANCE.NS"
    assert resp.status_code == 200
    assert resp.timestamp is not None
    assert isinstance(resp.metadata, dict)

def test_enterprise_api_gateway_routing() -> None:
    val_resp = EnterpriseAPIGateway.route_request("/valuation/RELIANCE.NS", "GET")
    assert val_resp.status_code == 200
    assert "intrinsic_value" in val_resp.data

    wf_resp = EnterpriseAPIGateway.route_request("/workflow/run", "POST", {"symbol": "TCS.NS"})
    assert wf_resp.status_code == 200
    assert wf_resp.data["success"] is True

    bad_resp = EnterpriseAPIGateway.route_request("/unknown/endpoint", "GET")
    assert bad_resp.status_code == 404
    assert "error" in bad_resp.data
