import os
import sys
import time
import uuid
import subprocess
import redis
from threading import Thread
from queue import Queue, Empty

BROKER_URL = "redis://127.0.0.1:6380/0"

def _enqueue_output(out, queue):
    for line in iter(out.readline, ''):
        queue.put(line)
    out.close()

def test_block30o_separate_process_worker_execution():
    redis_client = redis.Redis.from_url(
        BROKER_URL,
        socket_connect_timeout=3,
        socket_timeout=3,
        decode_responses=True,
    )
    assert redis_client.ping() is True

    token = f"SEPARATE-TOKEN-{uuid.uuid4()}"

    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "backend.tasks.eros_separate_process_worker:celery_app",
        "worker",
        "--pool=solo",
        "--loglevel=WARNING",
    ]

    worker_proc = subprocess.Popen(
        worker_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    q = Queue()
    t = Thread(target=_enqueue_output, args=(worker_proc.stdout, q))
    t.daemon = True
    t.start()

    worker_logs = []
    try:
        # Give the worker time to initialize.
        time.sleep(3.0)
        assert worker_proc.poll() is None, (
            f"Dedicated worker exited prematurely: {worker_proc.returncode}"
        )

        from backend.tasks.eros_separate_process_worker import (
            separate_process_echo,
        )
        result = separate_process_echo.apply_async(args=[token])
        assert result is not None
        assert result.id is not None

        deadline = time.time() + 15.0
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

        assert result.ready(), (
            f"Separate-process worker task remained PENDING. Worker logs: {worker_logs[-20:]}"
        )
        assert result.state == "SUCCESS"

        payload = result.get(timeout=3.0)
        assert isinstance(payload, dict)
        assert payload.get("status") == "EXECUTED"
        assert payload.get("token") == token

    finally:
        if worker_proc.poll() is None:
            worker_proc.terminate()
        try:
            worker_proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            worker_proc.kill()
            worker_proc.wait(timeout=5.0)
