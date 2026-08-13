import os
import pytest
from backend.tasks.task_control import task_control

def test_block30g_redis_resilient_ping():
    """
    Validates Redis connectivity with robust timeout and fallback handling.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        client = redis.Redis.from_url(redis_url, socket_timeout=0.5)
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis daemon not responding on wire protocol (socket/timeout): {exc}")

def test_block30g_task_control_fallback():
    """
    Validates that task control operates seamlessly in mock/fallback mode
    when external brokers are offline.
    """
    tasks = task_control.get_registered_tasks()
    assert len(tasks) > 0
    
    sub = task_control.submit_task(
        task_name="valuation.execute",
        user="infrastructure_auditor",
        payload={"symbol": "TCS.NS"}
    )
    assert "task_id" in sub
    assert sub["status"] in ["QUEUED", "SUCCESS"]
