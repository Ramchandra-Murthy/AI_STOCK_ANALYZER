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
    for line in iter(out.readline, ""):
        queue.put(line)

    out.close()


def test_block31g_canonical_worker_smoke_execution():
    """
    Block 31G

    Validates end-to-end task execution using the canonical EROS
    Celery worker:

        celery -A backend.tasks.celery_app worker

    against WSL Redis exposed through:

        127.0.0.1:6380

    Verifies:

        1. Redis availability
        2. Real Celery mode
        3. Canonical Celery application
        4. Worker startup
        5. Automatic task registration
        6. valuation.execute dispatch
        7. Worker execution
        8. SUCCESS result lifecycle
    """

    # ========================================================
    # STEP 1 - Redis preflight
    # ========================================================

    try:
        redis_client = redis.Redis.from_url(
            BROKER_URL,
            socket_connect_timeout=10,
            socket_timeout=10,
            decode_responses=True,
        )

        assert redis_client.ping() is True

    except Exception as exc:
        pytest.skip(
            f"WSL Redis broker at {BROKER_URL} is offline: {exc}"
        )

    # ========================================================
    # STEP 2 - Generate unique task token
    # ========================================================

    token = f"BLOCK31G-{uuid.uuid4()}"

    # ========================================================
    # STEP 3 - Force real Celery environment
    # ========================================================

    os.environ["USE_REAL_CELERY"] = "true"

    os.environ["CELERY_BROKER_URL"] = BROKER_URL

    os.environ["CELERY_RESULT_BACKEND"] = BROKER_URL

    # ========================================================
    # STEP 4 - Canonical worker command
    # ========================================================

    worker_cmd = [
        sys.executable,
        "-m",
        "celery",
        "-A",
        "backend.tasks.celery_app",
        "worker",
        "--pool=solo",
        "--loglevel=INFO",
    ]

    print("")
    print("CANONICAL WORKER COMMAND:")
    print(" ".join(worker_cmd))
    print("")

    # ========================================================
    # STEP 5 - Start worker
    # ========================================================

    worker_proc = subprocess.Popen(
        worker_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=os.environ.copy(),
    )

    q = Queue()

    reader_thread = Thread(
        target=_enqueue_output,
        args=(worker_proc.stdout, q),
        daemon=True,
    )

    reader_thread.start()

    worker_logs = []

    try:

        # ====================================================
        # STEP 6 - Wait for worker startup
        # ====================================================

        startup_deadline = time.time() + 10.0

        while time.time() < startup_deadline:

            try:

                while True:

                    line = q.get_nowait()

                    if line:
                        text = line.strip()
                        worker_logs.append(text)
                        print("[WORKER]", text)

            except Empty:
                pass

            if worker_proc.poll() is not None:
                break

            time.sleep(0.2)

        # ====================================================
        # Worker must still be alive
        # ====================================================

        assert worker_proc.poll() is None, (
            "Canonical Celery worker exited prematurely "
            f"with code {worker_proc.returncode}. "
            f"Logs: {worker_logs[-30:]}"
        )

        print("")
        print("CANONICAL WORKER PROCESS: ALIVE")
        print("")

        # ====================================================
        # STEP 7 - Import canonical Celery application
        # ====================================================

        from backend.tasks.celery_app import (
            celery_instance,
        )

        assert celery_instance is not None

        # ====================================================
        # STEP 8 - Verify required task registration
        # ====================================================

        required_task = "valuation.execute"

        assert required_task in celery_instance.tasks, (
            f"Required task {required_task!r} "
            "is not registered in canonical Celery instance."
        )

        print(
            "REGISTERED TASK:",
            required_task,
        )

        # ====================================================
        # STEP 9 - Dispatch REAL valuation task
        # ====================================================

        result = celery_instance.send_task(
            required_task,
            args=[
                {
                    "symbol": "TCS.NS",
                    "source": "BLOCK31G",
                    "task_id": token,
                }
            ],
        )

        assert result is not None

        assert result.id is not None

        print("")
        print("TASK ID:", result.id)
        print("")

        # ====================================================
        # STEP 10 - Wait for SUCCESS
        # ====================================================

        deadline = time.time() + 20.0

        success_achieved = False

        payload = None

        while time.time() < deadline:

            try:

                while True:

                    line = q.get_nowait()

                    if line:
                        text = line.strip()
                        worker_logs.append(text)
                        print("[WORKER]", text)

            except Empty:
                pass

            # -----------------------------------------------
            # Read Celery state
            # -----------------------------------------------

            state = result.state

            print(
                "TASK STATE:",
                state,
            )

            if result.ready():

                if result.state == "SUCCESS":

                    payload = result.get(
                        timeout=5.0
                    )

                    success_achieved = True

                    break

                if result.state in {
                    "FAILURE",
                    "REVOKED",
                }:

                    break

            time.sleep(0.5)

        # ====================================================
        # STEP 11 - Verify successful lifecycle
        # ====================================================

        assert success_achieved is True, (
            "Canonical worker task did not reach SUCCESS. "
            f"Current state: {result.state}. "
            f"Worker logs: {worker_logs[-40:]}"
        )

        # ====================================================
        # STEP 12 - Validate returned payload
        # ====================================================

        assert isinstance(
            payload,
            dict,
        ), (
            "Expected task result to be a dict, "
            f"got {type(payload).__name__}"
        )

        assert payload.get("status") == "SUCCESS", (
            "Expected payload status SUCCESS, "
            f"got {payload.get('status')!r}. "
            f"Payload={payload}"
        )

        print("")
        print("TASK RESULT:")
        print(payload)

        print("")
        print("CANONICAL TASK EXECUTION: PASS")

    finally:

        # ====================================================
        # STEP 13 - Always stop worker
        # ====================================================

        if worker_proc.poll() is None:

            print("")
            print("Stopping canonical worker...")

            worker_proc.terminate()

        try:

            worker_proc.wait(
                timeout=5.0
            )

        except subprocess.TimeoutExpired:

            print(
                "Worker did not terminate normally; "
                "forcing termination..."
            )

            worker_proc.kill()

            worker_proc.wait(
                timeout=5.0
            )

