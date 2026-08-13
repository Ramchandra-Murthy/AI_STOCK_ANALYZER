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

def enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def test_block30r_nonblocking_worker_diagnostic():
    redis_client = redis.Redis.from_url(
        BROKER_URL,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )
    assert redis_client.ping() is True

    token = f"BLOCK30R-{uuid.uuid4()}"

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

    q = Queue()
    t = Thread(target=enqueue_output, args=(worker.stdout, q))
    t.daemon = True
    t.start()

    # Collect startup logs for 3 seconds
    start_time = time.time()
    worker_logs = []
    while time.time() - start_time < 3.0:
        try:
            line = q.get_nowait()
            if line:
                worker_logs.append(line.strip())
        except Empty:
            time.sleep(0.1)

    try:
        from backend.tasks.eros_diagnostic_worker import worker_echo
        result = worker_echo.apply_async(args=[token])
        assert result.id is not None

        deadline = time.time() + 10
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
            time.sleep(0.5)

        if not result.ready():
            pytest.fail(
                f"Task timed out as PENDING.\nCaptured Worker Logs:\n" + "\n".join(worker_logs[-30:])
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
