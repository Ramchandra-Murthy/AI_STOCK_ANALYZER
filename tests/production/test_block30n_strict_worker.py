import threading
import time
import uuid

import pytest
from celery import Celery

BROKER_URL = "redis://127.0.0.1:6379/0"


def test_block30n_strict_worker_execution_proof() -> None:
    """
    Definitive worker execution proof.

    Starts a real Celery worker in a background thread, dispatches a uniquely
    tokenized task through the live Redis broker, and verifies SUCCESS plus
    the returned token.
    """

    app = Celery(
        "eros_strict_worker_test",
        broker=BROKER_URL,
        backend=BROKER_URL,
    )

    test_token = f"STRICT-TOKEN-{uuid.uuid4()}"

    @app.task(name="eros.diagnostic.strict_echo")
    def strict_echo_task(token: str) -> dict[str, str]:
        return {
            "status": "EXECUTED",
            "token": token,
        }

    worker_started = threading.Event()

    def run_worker() -> None:
        import io

        if not hasattr(sys.stdout, "write") or sys.stdout is None:
            sys.stdout = io.StringIO()
        if not hasattr(sys.stderr, "write") or sys.stderr is None:
            sys.stderr = io.StringIO()
        try:
            worker = app.Worker(
                loglevel="WARNING",
                pool="solo",
                concurrency=1,
            )

            worker_started.set()
            worker.start()

        except Exception:
            worker_started.set()

    worker_thread = threading.Thread(
        target=run_worker,
        daemon=True,
    )

    worker_thread.start()

    if not worker_started.wait(timeout=5):
        pytest.skip("Skipping threaded worker test in constrained Windows environment")

    time.sleep(1.0)

    try:
        # Dispatch task to the real Redis broker.
        result = strict_echo_task.apply_async(args=[test_token])

        assert result is not None
        assert result.id is not None

        # Wait for the worker to execute the task.
        deadline = time.time() + 8.0

        while time.time() < deadline:

            if result.ready():
                break

            time.sleep(0.2)

        # Definitive execution proof.
        assert result.ready(), (
            f"Task did not complete within 8 seconds. " f"Current state: {result.state}"
        )

        assert result.state == "SUCCESS", (
            f"Task did not reach SUCCESS state. " f"Current state: {result.state}"
        )

        # IMPORTANT:
        # Do NOT call result.get().
        #
        # Celery 5.6 can raise:
        # RuntimeError: Never call result.get() within a task!
        #
        # The task is already confirmed SUCCESS, therefore the completed
        # result can be read directly from AsyncResult.result.
        payload = result.result

        assert payload is not None
        assert isinstance(payload, dict)

        assert payload.get("status") == "EXECUTED"

        assert payload.get("token") == test_token

    except Exception as exc:

        pytest.fail(f"Strict worker execution proof failed: {exc}")
