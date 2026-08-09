from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.tasks.task_control import TaskControlService

def test_task_observability_metrics():
    control = TaskControlService()
    
    # Submit task to generate mock execution metrics
    submission = control.submit_task(
        task_name="forecast.execute",
        user="sprint20a_analyst",
        payload={"symbol": "INFY.NS"}
    )
    task_id = submission["task_id"]

    # Check metrics payload
    metrics = control.get_task_metrics()
    assert "total_submitted" in metrics
    assert metrics["total_submitted"] >= 1
    assert "success_count" in metrics
    assert metrics["success_count"] >= 1
    assert "average_execution_time_ms" in metrics

def test_task_observability_router_endpoint():
    client = TestClient(app)
    response = client.get("/api/v1/tasks/observability/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "SUCCESS"
    assert "metrics" in data
    assert "total_submitted" in data["metrics"]
