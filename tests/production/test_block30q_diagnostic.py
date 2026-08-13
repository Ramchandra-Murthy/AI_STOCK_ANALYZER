import os
import sys
import time
import uuid
import subprocess
import pytest
import redis

BROKER_URL = "redis://127.0.0.1:6380/0"

def test_block30q_worker_stream_diagnostic():
    """
    Launches the dedicated Celery worker while capturing stdout/stderr
    to inspect task registration and queue binding diagnostics.
    """
    redis_client = redis.Redis.from_url(
        BROKER_URL,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )
    assert redis_client.ping() is True

    token = f"BLOCK30Q-{uuid.uuid4()}"

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

    time.sleep(3.0)
    
    # Read any initialization logs captured so far
    output_lines = []
    try:
        while True:
            line = worker.stdout.readline()
            if not line:
                break
            output_lines.append(line.strip())
            if len(output_lines) > 50:
                break
    except Exception:
        pass

    try:
        from backend.tasks.eros_diagnostic_worker import worker_echo
        result = worker_echo.apply_async(args=[token])
        assert result.id is not None

        deadline = time.time() + 10
        while time.time() < deadline:
            if result.ready():
                break
            time.sleep(0.5)

        if not result.ready():
            # Grab remaining stdout for inspection
            remaining_output = worker.stdout.read()
            pytest.fail(
                f"Task timed out as PENDING. Worker logs captured:\n" +
                "\n".join(output_lines[-20:]) + "\n--- Remaining ---\n" + remaining_output[-500:]
            )

        assert result.state == "SUCCESS"
        payload = result.get(timeout=2)
        assert payload["status"] == "EXECUTED"
        assert payload["token"] == token

    finally:
        if worker.poll() is None:
            worker.terminate()
        try:
            worker.wait(timeout=3)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=3)
