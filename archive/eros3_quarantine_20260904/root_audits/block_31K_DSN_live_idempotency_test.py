import sys
import time
import uuid
import traceback

from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSN")
print("LIVE REDIS IDEMPOTENCY TEST")
print("=" * 58)

print()
print("1. TASK CONTROL")
print("CLASS:", type(task_control))
print("REGISTERED:", task_control.get_registered_tasks())

print()
print("2. REDIS CLIENT")
print("CLASS:", type(redis_client))
print("HOST:", redis_client.host)
print("PORT:", redis_client.port)
print("DB:", redis_client.db)

print()
print("3. REDIS INITIAL STATE")
print("KEY COUNT:", len(redis_client._store))

request_id = "DSN-" + uuid.uuid4().hex
print("REQUEST ID:", request_id)

idempotency_key = f"eros:idempotency:{request_id}"
print("IDEMPOTENCY KEY:", idempotency_key)

print()
print("4. FIRST SUBMISSION")

first = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload={
        "symbol": "TCS.NS",
        "request_id": request_id,
    },
)

print("FIRST:", first)

first_task_id = first["task_id"]
print("FIRST TASK ID:", first_task_id)

print()
print("5. REDIS AFTER FIRST SUBMISSION")

redis_value_1 = redis_client.get(idempotency_key)

print("REDIS VALUE:", redis_value_1)
print("MATCHES FIRST TASK:", redis_value_1 == first_task_id)

if redis_value_1 != first_task_id:
    raise AssertionError(
        "Redis idempotency mapping does not match first task ID"
    )

print()
print("6. SECOND IDENTICAL SUBMISSION")

second = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload={
        "symbol": "TCS.NS",
        "request_id": request_id,
    },
)

print("SECOND:", second)

second_task_id = second["task_id"]
print("SECOND TASK ID:", second_task_id)

print()
print("7. IDEMPOTENCY DECISION")

print("FIRST ID :", first_task_id)
print("SECOND ID:", second_task_id)

same_task = first_task_id == second_task_id
replay_flag = second.get("idempotent_replay", False)

print("SAME TASK ID:", same_task)
print("IDEMPOTENT REPLAY:", replay_flag)

if not same_task:
    raise AssertionError(
        "IDEMPOTENCY FAILURE: second submission created a different task ID"
    )

if not replay_flag:
    raise AssertionError(
        "IDEMPOTENCY FAILURE: second submission did not report idempotent_replay"
    )

print()
print("8. REDIS AFTER SECOND SUBMISSION")

redis_value_2 = redis_client.get(idempotency_key)

print("REDIS VALUE:", redis_value_2)
print("MATCHES TASK ID:", redis_value_2 == first_task_id)

if redis_value_2 != first_task_id:
    raise AssertionError(
        "Redis mapping changed after duplicate submission"
    )

print()
print("9. WAITING FOR ORIGINAL CELERY TASK")

final_status = None

for check in range(1, 16):
    final_status = task_control.get_task_status(first_task_id)

    print(
        "CHECK",
        check,
        "STATUS:",
        final_status
    )

    if final_status.get("ready"):
        break

    time.sleep(1)

print()
print("FINAL STATUS:", final_status)

if final_status.get("status") != "SUCCESS":
    raise AssertionError(
        f"Original task did not complete successfully: {final_status}"
    )

print()
print("10. RESULT RECOVERY")

result = task_control.get_task_result(first_task_id)

print("RESULT:", result)

if result.get("status") != "SUCCESS":
    raise AssertionError(
        f"Result recovery failed: {result}"
    )

print()
print("11. DUPLICATE RESULT CHECK")

duplicate_result = task_control.get_task_result(second_task_id)

print("DUPLICATE RESULT:", duplicate_result)

if duplicate_result.get("status") != "SUCCESS":
    raise AssertionError(
        "Idempotent replay did not recover the original result"
    )

print()
print("12. FINAL REDIS STATE")

print("KEY COUNT:", len(redis_client._store))
print(
    "IDEMPOTENCY KEY PRESENT:",
    idempotency_key in redis_client._store
)

print()
print("=" * 58)
print("BLOCK 31K-DSN COMPLETE")
print("=" * 58)
print("STATUS: PASS")
print("=" * 58)
