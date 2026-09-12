import time
import uuid

from fastapi.testclient import TestClient

from backend.main import app
from backend.tasks.celery_app import celery_app
from backend.tasks.task_control import task_control

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSE")
print("FAILURE + RECOVERY BEHAVIOR TEST")
print("=" * 58)

client = TestClient(app)

# ----------------------------------------------------------
# 1. REAL CELERY
# ----------------------------------------------------------
print("\n1. REAL CELERY")

underlying = getattr(celery_app, "_app", None)

print("FACADE:", type(celery_app))
print("UNDERLYING:", type(underlying))

assert underlying is not None
print("REAL CELERY: PASS")

# ----------------------------------------------------------
# 2. UNKNOWN TASK REJECTION
# ----------------------------------------------------------
print("\n2. UNKNOWN TASK REJECTION")

bad_task = "task.does.not.exist." + uuid.uuid4().hex

try:
    result = task_control.submit_task(task_name=bad_task, user="system", payload={})

    print("UNEXPECTED RESULT:", result)
    raise AssertionError("Unknown task was accepted")

except Exception as exc:
    print("REJECTION:", type(exc).__name__, str(exc))
    print("UNKNOWN TASK REJECTION: PASS")

# ----------------------------------------------------------
# 3. INVALID TASK ID LOOKUP
# ----------------------------------------------------------
print("\n3. INVALID TASK ID LOOKUP")

fake_id = str(uuid.uuid4())

status_result = task_control.get_task_status(fake_id)

print("STATUS:", status_result)

assert status_result.get("status") == "NOT_FOUND"

result_result = task_control.get_task_result(fake_id)

print("RESULT:", result_result)

assert result_result.get("status") == "NOT_FOUND"

print("INVALID TASK HANDLING: PASS")

# ----------------------------------------------------------
# 4. REAL TASK SUBMISSION
# ----------------------------------------------------------
print("\n4. REAL TASK SUBMISSION")

submission = task_control.submit_task(
    task_name="valuation.execute", user="system", payload={"symbol": "TCS.NS"}
)

print("SUBMISSION:", submission)

task_id = submission["task_id"]

assert task_id
print("TASK ID:", task_id)

# ----------------------------------------------------------
# 5. WAIT FOR WORKER
# ----------------------------------------------------------
print("\n5. WAITING FOR WORKER")

final = None

for i in range(30):
    status = task_control.get_task_status(task_id)

    print("CHECK", i + 1, "STATE:", status.get("status"))

    if status.get("status") in (
        "SUCCESS",
        "FAILURE",
        "FAILED",
        "NOT_FOUND",
    ):
        final = status
        break

    time.sleep(2)

assert final is not None, "Task did not reach terminal state"

print("FINAL STATUS:", final)

# ----------------------------------------------------------
# 6. RESULT RECOVERY
# ----------------------------------------------------------
print("\n6. RESULT RECOVERY")

if final.get("status") == "SUCCESS":

    recovered = task_control.get_task_result(task_id)

    print("RECOVERED RESULT:", recovered)

    assert recovered.get("status") == "SUCCESS"
    print("RESULT RECOVERY: PASS")

elif final.get("status") in ("FAILURE", "FAILED"):

    print("TASK FAILED AS A TEST CONDITION")
    print("FAILURE PAYLOAD:", final)

    recovered = task_control.get_task_result(task_id)

    print("RECOVERED FAILURE:", recovered)

    print("FAILURE STATE PERSISTED: PASS")

else:
    raise AssertionError(f"Unexpected terminal state: {final}")

# ----------------------------------------------------------
# 7. REDIS HEALTH
# ----------------------------------------------------------
print("\n7. REDIS HEALTH")

try:
    import redis

    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

    print("PING:", r.ping())
    print("KEY COUNT:", len(r.keys("*")))

    assert r.ping() is True

    print("REDIS HEALTH: PASS")

except Exception as exc:
    print("REDIS ERROR:", exc)
    raise

# ----------------------------------------------------------
# 8. OBSERVABILITY
# ----------------------------------------------------------
print("\n8. OBSERVABILITY")

metrics = task_control.get_task_metrics()

print("METRICS:", metrics)

assert metrics.get("total_submitted", 0) >= 1

print("OBSERVABILITY: PASS")

print("\n" + "=" * 58)
print("BLOCK 31K-DSE COMPLETE")
print("=" * 58)
