import sqlite3
import pickle
import time
from backend.tasks.task_control import TaskControlService

print("==================================================")
print("EROS 3.0 PHASE 4A - FINAL UUID CORRELATION")
print("==================================================")

control = TaskControlService()
user = "phase4a_final_user"
payload = {
    "symbol": "RELIANCE.NS",
    "bull_value": 6000.0,
    "base_value": 5000.0,
    "bear_value": 3000.0,
}

print("")
print("REQUEST")
print("User   :", user)
print("Payload:", payload)

submission = control.submit_task(
    task_name="forecast.execute",
    user=user,
    payload=payload,
)

control_id = submission["task_id"]
print("")
print("CONTROL TASK ID:", control_id)
print("")
print("WAITING FOR WORKER...")

for i in range(30):
    time.sleep(1)
    status = control.get_task_status(control_id)
    print(
        f"[{i+1:02d}s] "
        f"status={status.get('status')} "
        f"ready={status.get('ready')}"
    )
    if status.get("ready"):
        break

print("")
print("==================================================")
print("CONTROL RESULT")
print("==================================================")
control_result = control.get_task_result(control_id)
print(control_result)

print("")
print("==================================================")
print("DIRECT RESULT-BACKEND CORRELATION")
print("==================================================")

conn = sqlite3.connect("celery_results.db")
cur = conn.cursor()
cur.execute(
    "SELECT task_id, status, result "
    "FROM celery_taskmeta "
    "ORDER BY id DESC LIMIT 20"
)
rows = cur.fetchall()

match = None
for task_id, status, raw_result in rows:
    try:
        decoded = pickle.loads(raw_result)
    except Exception:
        continue

    if not isinstance(decoded, dict):
        continue

    if (
        decoded.get("user") == user
        and decoded.get("symbol") == payload["symbol"]
        and decoded.get("bull_value") == payload["bull_value"]
        and decoded.get("base_value") == payload["base_value"]
        and decoded.get("bear_value") == payload["bear_value"]
    ):
        match = {
            "backend_id": task_id,
            "backend_status": status,
            "worker_result": decoded,
        }
        break

conn.close()

if match is None:
    print("")
    print("*** NO MATCHING BACKEND RESULT ***")
    print("")
else:
    worker = match["worker_result"]
    backend_id = match["backend_id"]
    worker_id = worker.get("task_id")
    expected_value = (
        payload["bull_value"] * 0.25
        + payload["base_value"] * 0.50
        + payload["bear_value"] * 0.25
    )

    print("")
    print("MATCH FOUND")
    print("")
    print("CONTROL ID :", control_id)
    print("BACKEND ID :", backend_id)
    print("WORKER ID  :", worker_id)
    print("")
    print("==================================================")
    print("PHASE 4A CONTRACT MATRIX")
    print("==================================================")

    checks = {
        "CONTROL_ID_PRESENT": bool(control_id),
        "BACKEND_ID_PRESENT": bool(backend_id),
        "WORKER_ID_PRESENT": bool(worker_id),
        "STATUS_SUCCESS": worker.get("status") == "SUCCESS",
        "USER": worker.get("user") == user,
        "SYMBOL": worker.get("symbol") == payload["symbol"],
        "BULL": worker.get("bull_value") == payload["bull_value"],
        "BASE": worker.get("base_value") == payload["base_value"],
        "BEAR": worker.get("bear_value") == payload["bear_value"],
        "EXPECTED_VALUE": worker.get("expected_value") == expected_value,
        "BACKEND_EQUALS_WORKER": backend_id == worker_id,
    }

    for name, passed in checks.items():
        print(
            f"{name:<25}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    print("")
    print("==================================================")
    if all(checks.values()):
        print("*** PHASE 4A PASSED ***")
        print("*** REAL CELERY VERIFIED ***")
        print("*** RESULT BACKEND VERIFIED ***")
        print("*** USER VERIFIED ***")
        print("*** SYMBOL VERIFIED ***")
        print("*** FULL PAYLOAD VERIFIED ***")
        print("*** FORECAST CALCULATION VERIFIED ***")
        print("*** CELERY UUID CORRELATION VERIFIED ***")
    else:
        print("*** PHASE 4A REQUIRES REVIEW ***")
        print("")
        print("FAILED CHECKS:")
        for name, passed in checks.items():
            if not passed:
                print("   ", name)
    print("==================================================")
