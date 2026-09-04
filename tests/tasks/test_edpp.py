from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.tasks.celery_app import celery_app
from backend.tasks.task_context import TaskContext
from backend.tasks.task_executor import BackgroundWorkers

client = TestClient(app)

def test_celery_task_registration_and_dispatch() -> None:
    assert "valuation.execute" in celery_app.tasks
    assert "forecast.execute" in celery_app.tasks
    
    task_id = celery_app.send_task("forecast.execute")
    assert task_id
    assert isinstance(task_id, str)

def test_background_valuation_worker() -> None:
    ctx = TaskContext(task_id="TASK-9999", task_name="valuation.execute", user="admin", payload={"symbol": "RELIANCE.NS"})
    result = BackgroundWorkers.execute_valuation_task(ctx)
    assert result["status"] == "SUCCESS"
    assert result["result"]["symbol"] == "RELIANCE.NS"

def test_task_submission_api_endpoint(auth_headers) -> None:
    payload = {
        "task_name": "forecast.execute",
        "user": "analyst1",
        "payload": {"symbol": "INFY.NS"}
    }
    response = client.post("/api/v1/tasks/submit", json=payload, headers=auth_headers("ANALYST"))
    assert response.status_code == 202
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "QUEUED"
    assert data["execution_result"]["status"] == "SUCCESS"


