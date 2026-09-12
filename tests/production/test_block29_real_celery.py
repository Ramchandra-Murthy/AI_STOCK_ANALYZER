import os

from backend.tasks.celery_config import celery_broker
from backend.tasks.task_control import task_control


def test_block29a_redis_broker_configuration():
    """Validates Redis broker and result backend URL configuration parameters."""
    broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend_url = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    assert broker_url.startswith("redis://") or broker_url.startswith("amqp://")
    assert backend_url.startswith("redis://") or backend_url.startswith("amqp://")


def test_block29b_celery_config_queues():
    """Validates enterprise queue definitions and task routing maps."""
    queues = celery_broker.config.TASK_QUEUES
    queue_names = [queue.name for queue in queues]

    assert "valuation_queue" in queue_names
    assert "forecast_queue" in queue_names
    assert "report_queue" in queue_names
    assert "portfolio_queue" in queue_names

    routes = celery_broker.config.TASK_ROUTES
    assert "valuation.*" in routes
    assert "forecast.*" in routes


def test_block29c_task_control_broker_integration():
    """Validates that task control service correctly reports broker status."""
    status = task_control.get_queue_status()
    assert "queues" in status
    assert "real_celery" in status
    assert status["status"] == "HEALTHY"


def test_block29d_production_broker_dispatch():
    """Validates production celery broker task dispatch simulation."""
    task_id = celery_broker.dispatch(
        task_name="valuation.execute", queue="valuation_queue", payload={"symbol": "RELIANCE.NS"}
    )
    assert task_id is not None
    assert task_id.startswith("CELERY-")
    assert task_id in celery_broker.active_tasks
    assert celery_broker.active_tasks[task_id]["status"] == "QUEUED"
