from backend.tasks.celery_app import celery_app
from backend.tasks.task_control import task_control


def test_block28_worker_facade_and_registry():
    """Validates that the task control facade and task registry are operational."""
    assert celery_app is not None
    tasks = task_control.get_registered_tasks()
    assert isinstance(tasks, list)
    assert len(tasks) > 0
    assert "valuation.execute" in tasks
    assert "forecast.execute" in tasks


def test_block28_task_submission_and_status():
    """Validates asynchronous task submission and status retrieval."""
    submission = task_control.submit_task(
        task_name="valuation.execute", user="institutional_tester", payload={"symbol": "INFY.NS"}
    )
    assert "task_id" in submission
    task_id = submission["task_id"]

    status_info = task_control.get_task_status(task_id)
    assert status_info["task_id"] == task_id
    assert "status" in status_info

    result_info = task_control.get_task_result(task_id)
    assert result_info["task_id"] == task_id
    assert "result" in result_info


def test_block28_queue_and_metrics_observability():
    """Validates queue telemetry and execution metrics."""
    queues = task_control.get_queue_status()
    assert "queues" in queues
    assert queues["status"] == "HEALTHY"

    metrics = task_control.get_task_metrics()
    assert "total_submitted" in metrics
    assert metrics["status"] == "HEALTHY"
