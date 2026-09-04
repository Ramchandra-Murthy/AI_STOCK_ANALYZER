import uuid
import time

from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSP")
print("LIVE IDEMPOTENCY VERIFICATION")
print("=" * 58)

print()
print("1. TASK CONTROL")
print("CLASS:", type(task_control))
print("REGISTERED:", task_control.get_registered_tasks())

print()
print("2. REDIS CLIENT")
print("CLASS:", type(redis_client))
print("STORE BEFORE:", dict(redis_client._store))

request_id = "DSP-" + uuid.uuid4().hex
key = f"eros:idempotency:{request_id}"

print()
print("3. REQUEST")
print("REQUEST ID:", request_id)
print("KEY:", key)

payload = {
    "symbol": "TCS.NS",
    "request_id": request_id,
}

print()
print("4. FIRST SUBMISSION")

first = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload=dict(payload),
)

print("FIRST:", first)
first_id = first["task_id"]

print("FIRST TASK ID:", first_id)

stored = redis_client.get(key)

print()
print("5. REDIS AFTER FIRST")
print("STORED VALUE:", stored)
print("MATCH:", stored == first_id)

if stored != first_id:
    raise AssertionError(
        f"Redis mapping mismatch: expected {first_id}, got {stored}"
    )

print()
print("6. SECOND IDENTICAL SUBMISSION")

second = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload=dict(payload),
)

print("SECOND:", second)
second_id = second["task_id"]

print("SECOND TASK ID:", second_id)

print()
print("7. IDEMPOTENCY RESULT")

print("SAME TASK ID:", second_id == first_id)
print("IDEMPOTENT REPLAY:", second.get("idempotent_replay"))
print("REQUEST ID RETURNED:", second.get("request_id"))

if second_id != first_id:
    raise AssertionError(
        f"Duplicate submission created a new task: {second_id}"
    )

if second.get("idempotent_replay") is not True:
    raise AssertionError(
        "Second submission did not report idempotent_replay=True"
    )

print()
print("8. REDIS FINAL STATE")
print("STORED VALUE:", redis_client.get(key))
print("STORE SIZE:", len(redis_client._store))

print()
print("9. FINAL VERDICT")
print("REDIS MAPPING: PASS")
print("DUPLICATE SUPPRESSION: PASS")
print("TASK IDENTITY PRESERVED: PASS")
print("IDEMPOTENCY: PASS")

print()
print("=" * 58)
print("BLOCK 31K-DSP COMPLETE")
print("STATUS: PASS")
print("=" * 58)
