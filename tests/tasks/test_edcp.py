from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.infrastructure.redis.client import redis_client
from backend.tasks.celery_config import celery_broker

client = TestClient(app)

def test_redis_infrastructure_and_locks() -> None:
    assert redis_client.set("test_key", "institutional_value") is True
    assert redis_client.get("test_key") == "institutional_value"

    # Test distributed locks
    assert redis_client.acquire_lock("valuation_tcs") is True
    assert redis_client.acquire_lock("valuation_tcs") is False # Duplicate lock prevented
    assert redis_client.release_lock("valuation_tcs") is True
    assert redis_client.acquire_lock("valuation_tcs") is True

def test_celery_queue_routing() -> None:
    task_id = celery_broker.dispatch("valuation.execute", "valuation_queue", {"symbol": "TCS.NS"})
    assert task_id.startswith("CELERY-")
    assert task_id in celery_broker.active_tasks

def test_admin_monitoring_endpoints() -> None:
    resp = client.get("/api/v1/admin/queues")
    assert resp.status_code == 200
    data = resp.json()
    assert "valuation_queue" in data["queues"]

    tasks_resp = client.get("/api/v1/admin/tasks")
    assert tasks_resp.status_code == 200
    assert "tasks" in tasks_resp.json()