from fastapi.testclient import TestClient
from backend.main import app
from backend.core.config.settings import settings
from backend.tasks.celery_app import celery_app
from backend.tasks.task_control import task_control
from services.production.readiness_report import ProductionReadinessEngine

client = TestClient(app)

def test_block27a_configuration_contract():
    """Validates production configuration settings and environment defaults."""
    assert settings.PROJECT_NAME is not None
    assert settings.ENVIRONMENT in ["production", "development", "staging"]
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None

def test_block27b_api_operational_contract():
    """Validates health, readiness, and task control endpoints."""
    # Health probe
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json().get("status") == "healthy"

    # Readiness probe
    res_ready = client.get("/ready")
    assert res_ready.status_code == 200
    assert res_ready.json().get("status") == "ready"

    # Admin task queues
    res_queues = client.get("/api/v1/admin/queues")
    assert res_queues.status_code == 200
    assert "queues" in res_queues.json()

def test_block27c_worker_operational_contract():
    """Validates Celery worker task facade, registry, and task submission."""
    # Check Celery task facade availability
    assert celery_app is not None
    registered_tasks = task_control.get_registered_tasks()
    assert isinstance(registered_tasks, list)
    assert len(registered_tasks) > 0

    # Submit task via control service
    sub = task_control.submit_task(
        task_name="valuation.execute",
        user="institutional_auditor",
        payload={"symbol": "RELIANCE.NS"}
    )
    assert "task_id" in sub
    assert sub.get("status") in ["SUCCESS", "QUEUED"]

    # Verify readiness report engine
    report = ProductionReadinessEngine.evaluate_readiness()
    assert report.system_status is not None
    assert isinstance(report.components_checked, int)
