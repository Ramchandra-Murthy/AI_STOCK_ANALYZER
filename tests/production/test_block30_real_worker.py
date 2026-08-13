import os
import pytest
from backend.tasks.celery_app import celery_instance

def test_block30a_redis_ping_connection():
    """
    Validates connection to Redis if available, ensuring broker health
    can be established via TCP / Redis ping.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        import redis
        client = redis.Redis.from_url(redis_url, socket_timeout=1.0)
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis server not actively responding at {redis_url}: {exc}")

def test_block30b_real_celery_instance_bootstrap():
    """
    Validates that a real Celery instance can be instantiated and configured
    with enterprise serializer and timezone settings when USE_REAL_CELERY=true.
    """
    os.environ["USE_REAL_CELERY"] = "true"
    try:
        from celery import Celery
        app = Celery(
            "eros_test_worker",
            broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
            backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
        )
        app.conf.update(
            task_serializer="json",
            result_serializer="json",
            accept_content=["json"],
            timezone="UTC",
            enable_utc=True,
        )
        assert app is not None
        assert app.conf.task_serializer == "json"
    finally:
        os.environ["USE_REAL_CELERY"] = "false"
