import os
import pytest
from backend.tasks.task_control import task_control
from backend.tasks.celery_app import celery_instance

def test_block30d_live_redis_broker_roundtrip():
    """
    Validates live Redis broker connectivity and message roundtrip
    if an active Redis server is running on localhost:6379.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        client = redis.Redis.from_url(redis_url, socket_timeout=1.5)
        client.ping()
    except Exception as exc:
        pytest.skip(f"Live Redis daemon is not running at {redis_url}: {exc}")

    # If Redis is active, test live key-value set/get as a broker health check
    test_key = "eros:health:ping"
    client.set(test_key, "OK", ex=10)
    assert client.get(test_key).decode("utf-8") == "OK"

def test_block30d_live_celery_task_dispatch():
    """
    Validates live task dispatch when Redis broker is online and reachable.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        client = redis.Redis.from_url(redis_url, socket_timeout=1.5)
        client.ping()
    except Exception as exc:
        pytest.skip(f"Live Redis daemon is not running at {redis_url}: {exc}")

    # Temporarily enable real celery mode for live dispatch test
    os.environ["USE_REAL_CELERY"] = "true"
    try:
        submission = task_control.submit_task(
            task_name="valuation.execute",
            user="live_production_auditor",
            payload={"symbol": "INFY.NS", "live_broker_test": True}
        )
        assert submission is not None
        assert "task_id" in submission
    finally:
        os.environ["USE_REAL_CELERY"] = "false"
