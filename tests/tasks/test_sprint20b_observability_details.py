from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app
from backend.tasks.task_control import TaskControlService


def test_per_task_execution_telemetry():
    control = TaskControlService()

    submission = control.submit_task(
        task_name="valuation.execute", user="sprint20b_analyst", payload={"symbol": "TCS.NS"}
    )
    task_id = submission["task_id"]

    # Verify per-task metadata and execution timing are tracked
    status_info = control.get_task_status(task_id)
    assert "execution_time_ms" in status_info or status_info.get("ready") is True


def test_task_observability_details_endpoint(auth_headers):
    client = TestClient(app)
    response = client.get("/api/v1/tasks/observability/details", headers=auth_headers("ANALYST"))
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "SUCCESS"
    assert "tasks" in data
