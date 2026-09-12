from __future__ import annotations

from api.app import EROSAPIApp


def test_enterprise_api_service_platform() -> None:
    # Test Health Endpoint
    health = EROSAPIApp.health_check()
    assert health["success"] is True
    assert health["version"] == "1.0.0"
    assert health["data"]["database"] == "OK"

    # Test Workflow API Endpoint
    wf_res = EROSAPIApp.trigger_workflow("RELIANCE.NS")
    assert wf_res["success"] is True
    assert wf_res["run_id"].startswith("RUN-")
    assert len(wf_res["completed_steps"]) == 12
    assert len(wf_res["reports_generated"]) == 1
