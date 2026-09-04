from __future__ import annotations

from celery import Celery


REDIS_URL = "redis://127.0.0.1:6379/0"


def test_block30k_real_celery_broker_connection():
    """
    Validates that a real Celery application can establish a live TCP
    connection and handshake with the WSL Redis broker.
    """
    app = Celery(
        "eros_live_broker_test",
        broker=REDIS_URL,
        backend=REDIS_URL,
    )

    conn = app.connection_for_read()
    conn.connect()

    try:
        assert conn.connected is True
    finally:
        conn.release()


def test_block30k_celery_task_signature_and_dispatch():
    """
    Validates task creation, signature binding, and message publishing
    against the active WSL Redis broker.
    """
    app = Celery(
        "eros_live_task_test",
        broker=REDIS_URL,
        backend=REDIS_URL,
    )

    @app.task(name="eros.test.ping")
    def ping_task():
        return "PONG_FROM_WSL_REDIS"

    result = ping_task.apply_async(args=[])

    assert result is not None
    assert result.id is not None
