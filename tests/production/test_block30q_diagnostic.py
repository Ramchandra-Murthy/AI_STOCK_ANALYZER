from __future__ import annotations

import os
import sys
import time
import uuid
import subprocess

import pytest
import redis


BROKER_URL = os.getenv(
    "CELERY_BROKER_URL",
    "redis://127.0.0.1:6379/0",
)


def test_block30q_worker_stream_diagnostic() -> None:
    """
    Launch the dedicated Celery diagnostic worker, verify that it starts,
    dispatch a diagnostic task through the live Redis broker, and verify
    successful execution.
    """
    redis_client = redis.Redis.from_url(
        BROKER_URL,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )

    try:
        assert redis_client.ping() is True
    except Exception as exc:
        pytest.fail(
            f"Redis broker is unavailable at {BROKER_URL}: {exc}"
        )

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

    try:
        # Give the worker time to initialize.
        time.sleep(3.0)

        if worker.poll() is not None:
            output = worker.stdout.read() if worker.stdout else ""
            pytest.fail(
                "Diagnostic Celery worker exited during startup.\n"
                f"Worker output:\n{output[-3000:]}"
            )

        from backend.tasks.eros_diagnostic_worker import worker_echo

        result = worker_echo.apply_async(args=[token])

        assert result.id is not None

        deadline = time.time() + 10.0

        while time.time() < deadline:
            if result.ready():
                break

            if worker.poll() is not None:
                output = worker.stdout.read() if worker.stdout else ""
                pytest.fail(
                    "Diagnostic worker exited before task completion.\n"
                    f"Worker output:\n{output[-3000:]}"
                )

            time.sleep(0.5)

        if not result.ready():
            pytest.fail(
                f"Task timed out as PENDING after 10 seconds.\n"
                f"Broker: {BROKER_URL}\n"
                f"Task ID: {result.id}"
            )

        assert result.state == "SUCCESS"

        payload = result.result

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

        if worker.stdout:
            worker.stdout.close()

