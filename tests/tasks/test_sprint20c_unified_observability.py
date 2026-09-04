from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.tasks.task_control import TaskControlService

def test_unified_observability_service():
    control = TaskControlService()
    control.submit_task(task_name="valuation.execute", user="sprint20c_analyst")

    summary = control.get_observability_summary()
    assert "metrics" in summary
    assert "tasks" in summary
    assert "queues" in summary
    assert "registered_tasks" in summary
    assert summary["status"] == "HEALTHY"

def test_unified_observability_endpoint(auth_headers):
    client = TestClient(app)
    response = client.get("/api/v1/tasks/observability", headers=auth_headers("ANALYST"))
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "summary" in data
    assert "metrics" in data["summary"]
    assert "tasks" in data["summary"]
