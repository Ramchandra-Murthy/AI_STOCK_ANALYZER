import sqlite3
import pickle
import time
from backend.tasks.task_control import TaskControlService

print("==================================================")
print("EROS 3.0 PHASE 4A - UUID CORRELATION TEST")
print("==================================================")

control = TaskControlService()
user = "phase4a_correlation_user"
payload = {
    "symbol": "RELIANCE.NS",
    "bull_value": 6000.0,
    "base_value": 5000.0,
    "bear_value": 3000.0,
}

print("")
print("SUBMITTING TASK")
print("USER   :", user)
print("PAYLOAD:", payload)

submission = control.submit_task(
    task_name="forecast.execute",
    user=user,
    payload=payload,
)

control_id = submission["task_id"]
print("")
print("EROS CONTROL TASK ID:", control_id)
print("")
print("WAITING FOR CELERY RESULT...")

result = None
for i in range(30):
    time.sleep(1)
    status = control.get_task_status(control_id)
    print(f"[{i+1:02d}s] " f"status={status.get('status')} " f"ready={status.get('ready')}")
    if status.get("ready"):
        result = control.get_task_result(control_id)
        break

print("")
print("==================================================")
print("CONTROL-PLANE RESULT")
print("==================================================")
if result is None:
    print("NO RESULT RETURNED BY CONTROL PLANE")
else:
    print(result)

print("")
print("==================================================")
print("DIRECT SQLITE RESULT-BACKEND SEARCH")
print("==================================================")

conn = sqlite3.connect("celery_results.db")
cur = conn.cursor()
cur.execute("SELECT task_id, status, result " "FROM celery_taskmeta " "ORDER BY id DESC LIMIT 20")
rows = cur.fetchall()

matched = None
for row in rows:
    task_id = row[0]
    try:
        decoded = pickle.loads(row[2])
    except Exception:
        decoded = None

    if isinstance(decoded, dict):
        if (
            decoded.get("user") == user
            and decoded.get("symbol") == payload["symbol"]
            and decoded.get("bull_value") == payload["bull_value"]
            and decoded.get("base_value") == payload["base_value"]
            and decoded.get("bear_value") == payload["bear_value"]
        ):
            matched = {
                "backend_task_id": task_id,
                "status": row[1],
                "result": decoded,
            }
            break

if matched is None:
    print("NO MATCHING RESULT FOUND")
else:
    print("MATCH FOUND")
    print("")
    print("BACKEND TASK ID:")
    print(matched["backend_task_id"])
    print("")
    print("DECODED RESULT:")
    print(matched["result"])

conn.close()

print("")
print("==================================================")
print("UUID CORRELATION MATRIX")
print("==================================================")

if matched is None:
    print("BACKEND_RESULT_FOUND : FAIL")
    print("UUID_CORRELATION     : FAIL")
    print("RESULT_CORRELATION   : FAIL")
else:
    worker = matched["result"]
    backend_id = matched["backend_task_id"]
    worker_id = worker.get("task_id")
    expected_value = (
        payload["bull_value"] * 0.25 + payload["base_value"] * 0.50 + payload["bear_value"] * 0.25
    )

    checks = {
        "CONTROL_ID_PRESENT": bool(control_id),
        "BACKEND_ID_PRESENT": bool(backend_id),
        "WORKER_ID_PRESENT": bool(worker_id),
        "USER": worker.get("user") == user,
        "SYMBOL": worker.get("symbol") == payload["symbol"],
        "BULL": worker.get("bull_value") == payload["bull_value"],
        "BASE": worker.get("base_value") == payload["base_value"],
        "BEAR": worker.get("bear_value") == payload["bear_value"],
        "EXPECTED_VALUE": worker.get("expected_value") == expected_value,
        "BACKEND_EQUALS_WORKER": backend_id == worker_id,
    }

    for name, passed in checks.items():
        print(f"{name:<25}: " f"{'PASS' if passed else 'FAIL'}")

    print("")
    print("CONTROL ID :", control_id)
    print("BACKEND ID :", backend_id)
    print("WORKER ID  :", worker_id)
    print("")
    print("==================================================")
    if all(checks.values()):
        print("*** PHASE 4A UUID CORRELATION PASSED ***")
        print("*** RESULT BACKEND VERIFIED ***")
        print("*** USER + SYMBOL + PAYLOAD VERIFIED ***")
        print("*** WORKER UUID VERIFIED ***")
    else:
        print("*** PHASE 4A UUID CORRELATION REQUIRES REVIEW ***")
    print("==================================================")
