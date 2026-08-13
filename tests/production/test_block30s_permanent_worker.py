import os
import sys
import time
import uuid
import subprocess
import pytest
import redis
from threading import Thread
from queue import Queue, Empty

BROKER_URL = "redis://127.0.0.1:6380/0"

def _enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def test_block30s_permanent_real_worker_regression():
    """
    Permanent regression test verifying end-to-end task execution
    via a dedicated Celery worker subprocess communicating with WSL Redis (:6380).
    """
    try:
        redis_client = redis.Redis.from_url(
            BROKER_URL,
            socket_connect_timeout=3,
            socket_timeout=3,
            decode_responses=True,
        )
        assert redis_client.ping() is True
    except Exception as exc:
        pytest.skip(f"WSL Redis broker at {BROKER_URL} is offline: {exc}")

    token = f"EROS-PERM-30S-{uuid.uuid4()}"

    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "backend.tasks.eros_diagnostic_worker:celery_app",
        "worker",
        "--pool=solo",
        "--loglevel=WARNING",
    ]

    worker = subprocess.Popen(
        worker_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    q = Queue()
    t = Thread(target=_enqueue_output, args=(worker.stdout, q))
    t.daemon = True
    t.start()

    # Allow worker startup time
    time.sleep(2.0)
    assert worker.poll() is None, "Permanent Celery worker process exited prematurely."

    try:
        from backend.tasks.eros_diagnostic_worker import worker_echo
        result = worker_echo.apply_async(args=[token])
        assert result is not None
        assert result.id is not None

        deadline = time.time() + 12.0
        worker_logs = []
        while time.time() < deadline:
            try:
                while True:
                    line = q.get_nowait()
                    if line:
                        worker_logs.append(line.strip())
            except Empty:
                pass

            if result.ready():
                break
            time.sleep(0.3)

        assert result.ready(), f"Task timed out as PENDING. Logs: {worker_logs[-15:]}"
        assert result.state == "SUCCESS"

        payload = result.get(timeout=3.0)
        assert isinstance(payload, dict)
        assert payload.get("status") == "EXECUTED"
        assert payload.get("token") == token

    finally:
        if worker.poll() is None:
            worker.terminate()
        try:
            worker.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=3.0)
