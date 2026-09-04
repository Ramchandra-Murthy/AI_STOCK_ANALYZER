import os
import time
import uuid
from backend.tasks.task_control import task_control

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSJ")
print("LIVE IDEMPOTENCY VERIFICATION")
print("=" * 58)

print()
print("1. TASK CONTROL")
print("CLASS:", type(task_control))
print("REGISTERED:", task_control.get_registered_tasks())

print()
print("2. REDIS")
try:
    r = task_control._get_redis_client()
    print("PING:", r.ping())
    print("VERSION:", r.info().get("redis_version"))
    print("IDEMPOTENCY KEYS BEFORE:",
          len(r.keys("eros:idempotency:*")))
except Exception as e:
    print("REDIS ERROR:", repr(e))
    raise

print()
print("3. REQUEST ID")
request_id = "DSJ-" + uuid.uuid4().hex
print("REQUEST ID:", request_id)
idempotency_key = f"eros:idempotency:{request_id}"
print("IDEMPOTENCY KEY:", idempotency_key)

payload = {
    "symbol": "TCS.NS",
    "request_id": request_id,
}

print()
print("4. FIRST SUBMISSION")
first = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload=payload,
)
print("FIRST:", first)
first_id = first["task_id"]
print("FIRST TASK ID:", first_id)

print()
print("5. REDIS MAPPING AFTER FIRST SUBMISSION")
stored = r.get(idempotency_key)
if isinstance(stored, bytes):
    stored = stored.decode("utf-8")
print("STORED TASK ID:", stored)
print("MAPPING CORRECT:", stored == first_id)

print()
print("6. SECOND IDENTICAL SUBMISSION")
second = task_control.submit_task(
    task_name="valuation.execute",
    user="system",
    payload=payload,
)
print("SECOND:", second)
second_id = second["task_id"]
print("SECOND TASK ID:", second_id)

print()
print("7. IDEMPOTENCY ANALYSIS")
print("FIRST ID :", first_id)
print("SECOND ID:", second_id)
print("SAME TASK ID:", first_id == second_id)
print("IDEMPOTENT REPLAY FLAG:",
      second.get("idempotent_replay"))
print("DUPLICATE EXECUTION PREVENTED:",
      first_id == second_id and second.get("idempotent_replay") is True)

print()
print("8. TASK STATUS")
for label, task_id in [("FIRST", first_id), ("SECOND", second_id)]:
    for attempt in range(1, 11):
        status = task_control.get_task_status(task_id)
        print(label, "CHECK", attempt, ":", status.get("status"))
        if status.get("ready"):
            break
        time.sleep(1)

print()
print("9. FINAL RESULT")
result = task_control.get_task_result(first_id)
print("RESULT:", result)

print()
print("10. REDIS FINAL CHECK")
print("PING:", r.ping())
stored_final = r.get(idempotency_key)
if isinstance(stored_final, bytes):
    stored_final = stored_final.decode("utf-8")
print("FINAL STORED TASK ID:", stored_final)
print("KEY EXISTS:", bool(stored_final))
print("TOTAL IDEMPOTENCY KEYS:",
      len(r.keys("eros:idempotency:*")))

print()
print("=" * 58)
print("BLOCK 31K-DSJ COMPLETE")
print("=" * 58)
