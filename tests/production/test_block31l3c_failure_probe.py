import subprocess
import sys
import time

from backend.tasks.task_control import TaskControlService


def test_failure_semantics_probe():
    print("\n--- STARTING BLOCK 31L.3C FAILURE SEMANTICS PROBE ---")

    # 1. Start a background Celery worker process
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
    print("Launching background Celery worker for failure test...")
    worker_proc = subprocess.Popen(worker_cmd)
    time.sleep(4)  # Wait for worker startup

    try:
        control = TaskControlService()
        assert control.real_celery_enabled is True

        # 2. Submit a task with invalid payload designed to trigger a failure in valuation.execute
        payload = {"symbol": "", "current_price": -100.0}  # Invalid symbol / price
        submission = control.submit_task(
            task_name="valuation.execute", user="institutional_system", payload=payload
        )
        task_id = submission["task_id"]
        print(f"Submitted failing task ID: {task_id}")

        # 3. Poll status until completion
        final_status = None
        for i in range(15):
            status_info = control.get_task_status(task_id)
            print(f"Poll [{i+1}/15] STATUS INFO:", status_info)
            final_status = status_info.get("status")
            if final_status in ("SUCCESS", "FAILURE"):
                break
            time.sleep(1)

        print(f"Final task status: {final_status}")

        # 4. Inspect result retrieval behavior under failure
        result_info = control.get_task_result(task_id)
        print("RETRIEVED RESULT INFO FOR FAILING TASK:", result_info)

        res_payload = result_info.get("result", {})
        print("Result payload content:", res_payload)

    finally:
        print("Terminating background worker...")
        worker_proc.terminate()
        worker_proc.wait(timeout=5)
