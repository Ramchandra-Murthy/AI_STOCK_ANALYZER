import os
import uuid
import time
import threading
import pytest

def test_block30n_strict_worker_execution_proof():
    """
    Validates definitive task execution by spinning up a local Celery worker thread
    against WSL Redis (port 6380), dispatching a uniquely tokenized task,
    and asserting an absolute SUCCESS state with matching payload token echo.
    """
    broker_url = "redis://127.0.0.1:6380/0"
    
    try:
        from celery import Celery
        app = Celery(
            "eros_strict_worker_test",
            broker=broker_url,
            backend=broker_url
        )
        
        test_token = f"STRICT-TOKEN-{uuid.uuid4()}"
        
        @app.task(name="eros.diagnostic.strict_echo")
        def strict_echo_task(token: str):
            return {"status": "EXECUTED", "token": token}
            
        # Start a background Celery worker thread using the solo pool for synchronous safety
        worker_stopped = threading.Event()
        
        def run_worker():
            try:
                worker = app.Worker(loglevel="WARNING", pool="solo", concurrency=1)
                # Run worker until stopped
                worker.start()
            except Exception:
                pass

        worker_thread = threading.Thread(target=run_worker, daemon=True)
        worker_thread.start()
        
        # Give worker a brief moment to connect to Redis
        time.sleep(1.0)
        
        # Dispatch task
        result = strict_echo_task.apply_async(args=[test_token])
        assert result is not None
        assert result.id is not None
        
        # Enforce strict SUCCESS state transition (maximum 8 seconds timeout)
        start_time = time.time()
        success_achieved = False
        payload = None
        
        while time.time() - start_time < 8.0:
            if result.ready():
                if result.state == "SUCCESS":
                    payload = result.get(timeout=1.0)
                    success_achieved = True
                    break
            time.sleep(0.2)
            
        assert success_achieved is True, f"Task did not reach SUCCESS state. Current state: {result.state}"
        assert isinstance(payload, dict)
        assert payload.get("status") == "EXECUTED"
        assert payload.get("token") == test_token
        
    except Exception as exc:
        pytest.fail(f"Strict worker execution proof failed: {exc}")
