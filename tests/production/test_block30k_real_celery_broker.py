import os
import pytest

def test_block30k_real_celery_broker_connection():
    """
    Validates that a real Celery application can establish a live TCP connection
    and handshake with the WSL Redis broker at redis://127.0.0.1:6380/0.
    """
    broker_url = "redis://127.0.0.1:6380/0"
    result_backend = "redis://127.0.0.1:6380/0"
    
    try:
        from celery import Celery
        app = Celery(
            "eros_live_broker_test",
            broker=broker_url,
            backend=result_backend
        )
        
        # Test broker connection handshake
        conn = app.connection()
        conn.connect()
        assert conn.connected is True
        conn.release()
    except Exception as exc:
        pytest.fail(f"Failed to connect real Celery broker to WSL Redis at {broker_url}: {exc}")

def test_block30k_celery_task_signature_and_dispatch():
    """
    Validates task creation, signature binding, and message publishing
    against the active WSL Redis broker.
    """
    broker_url = "redis://127.0.0.1:6380/0"
    
    try:
        from celery import Celery
        app = Celery(
            "eros_live_task_test",
            broker=broker_url,
            backend=broker_url
        )
        
        @app.task(name="eros.test.ping")
        def ping_task():
            return "PONG_FROM_WSL_REDIS"
            
        # Send task to broker
        result = ping_task.apply_async(args=[])
        assert result is not None
        assert result.id is not None
    except Exception as exc:
        pytest.fail(f"Celery task dispatch to live Redis failed: {exc}")
