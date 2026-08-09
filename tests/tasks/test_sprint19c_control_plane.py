from fastapi.testclient import TestClient
from backend.main import app
from backend.tasks.task_control import TaskControlService

def test_task_control_forecast_lifecycle():
    control = TaskControlService()
    submission = control.submit_task(
        task_name="forecast.execute",
        user="sprint19c_test",
        payload={"symbol": "TCS.NS"},
    )
    assert submission["task_id"]
    assert submission["status"] == "QUEUED"
    task_id = submission["task_id"]
    status = control.get_task_status(task_id)
    assert status["task_id"] == task_id
    assert status["status"] == "SUCCESS"
    assert status["ready"] is True
    result = control.get_task_result(task_id)
    assert result["task_id"] == task_id
    assert result["status"] == "SUCCESS"
    assert result["result"]["symbol"] == "TCS.NS"
    assert result["result"]["expected_value"] == 2837.5

def test_task_control_registered_tasks():
    control = TaskControlService()
    tasks = control.get_registered_tasks()
    assert "valuation.execute" in tasks
    assert "forecast.execute" in tasks
    assert "report.generate" in tasks

def test_task_control_queue_status():
    control = TaskControlService()
    queue_status = control.get_queue_status()
    assert queue_status["status"] == "HEALTHY"
    assert "forecast_queue" in queue_status["queues"]
    assert "report_queue" in queue_status["queues"]
    assert queue_status["real_celery"] is False

def test_task_control_unknown_task():
    control = TaskControlService()
    try:
        control.submit_task(
            task_name="unknown.task",
            user="sprint19c_test",
            payload={},
        )
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unknown task" in str(exc)

def test_task_router_lifecycle():
    client = TestClient(app)
    response = client.post(
        "/api/v1/tasks/submit",
        json={
            "task_name": "forecast.execute",
            "user": "sprint19c_api",
            "payload": {
                "symbol": "TCS.NS",
            },
        },
    )
    assert response.status_code == 202
    body = response.json()
    task_id = body["task_id"]
    assert body["execution_result"]["status"] == "SUCCESS"
    assert body["execution_result"]["symbol"] == "TCS.NS"
    status_response = client.get(
        f"/api/v1/tasks/{task_id}/status"
    )
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["task_id"] == task_id
    assert status_body["status"] == "SUCCESS"
    result_response = client.get(
        f"/api/v1/tasks/{task_id}/result"
    )
    assert result_response.status_code == 200
    result_body = result_response.json()
    assert result_body["task_id"] == task_id
    assert result_body["result"]["symbol"] == "TCS.NS"

def test_task_router_unknown_task():
    client = TestClient(app)
    response = client.get(
        "/api/v1/tasks/TASK-SPRINT19C-NOT-FOUND/status"
    )
    assert response.status_code == 404
    response = client.get(
        "/api/v1/tasks/TASK-SPRINT19C-NOT-FOUND/result"
    )
    assert response.status_code == 404

def test_task_router_queue_status():
    client = TestClient(app)
    response = client.get("/api/v1/tasks/queues/status")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "HEALTHY"
    assert "forecast_queue" in body["queues"]
    assert "report_queue" in body["queues"]
