import os
import sys
import time
import uuid
import subprocess
import pytest
import redis

import os
BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

def test_block30p_dedicated_worker_execution():
    redis_client = redis.Redis.from_url(
        BROKER_URL,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )
    assert redis_client.ping() is True

    token = f"BLOCK30P-{uuid.uuid4()}"

    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "backend.tasks.eros_diagnostic_worker:celery_app",
        "worker",
        "--pool=solo",
        "--loglevel=INFO",
    ]

    worker = subprocess.Popen(
        worker_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    try:
        # Verify that the worker process actually stays alive.
        time.sleep(3)
        assert worker.poll() is None, (
            f"Celery worker exited prematurely with code {worker.returncode}"
        )

        from backend.tasks.eros_diagnostic_worker import worker_echo
        result = worker_echo.apply_async(args=[token])
        assert result.id is not None

        deadline = time.time() + 15
        while time.time() < deadline:
            if result.ready():
                break
            time.sleep(0.5)

        assert result.ready(), (
            f"Worker did not complete task. State={result.state}"
        )
        assert result.state == "SUCCESS"

        payload = result.result
        assert isinstance(payload, dict)
        assert payload["status"] == "EXECUTED"
        assert payload["token"] == token

    finally:
        if worker.poll() is None:
            worker.terminate()
        try:
            worker.wait(timeout=5)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=5)


