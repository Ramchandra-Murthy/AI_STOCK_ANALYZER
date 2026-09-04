import uuid
import concurrent.futures
import threading

from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-DT")
print("CONCURRENT IDEMPOTENCY RACE TEST")
print("READ-ONLY TEST")
print("=" * 60)

request_id = "DT-" + uuid.uuid4().hex
key = f"eros:idempotency:{request_id}"

print()
print("1. TASK CONTROL")
print("CLASS:", type(task_control))
print("REGISTERED:", task_control.get_registered_tasks())

print()
print("2. REDIS")
print("CLASS:", type(redis_client))
print("INITIAL STORE:", dict(redis_client._store))

print()
print("3. SHARED REQUEST")
print("REQUEST ID:", request_id)
print("KEY:", key)

barrier = threading.Barrier(10)

def submit_one(index):
    barrier.wait()

    payload = {
        "symbol": "TCS.NS",
        "request_id": request_id,
    }

    result = task_control.submit_task(
        task_name="valuation.execute",
        user="system",
        payload=payload,
    )

    return index, result

print()
print("4. STARTING 10 SIMULTANEOUS SUBMISSIONS")

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(submit_one, i)
        for i in range(10)
    ]

    results = [future.result() for future in futures]

results.sort(key=lambda x: x[0])

print()
print("5. SUBMISSION RESULTS")

task_ids = []

for index, result in results:
    task_id = result.get("task_id")
    task_ids.append(task_id)

    print(
        f"REQUEST {index}: "
        f"task_id={task_id} "
        f"status={result.get('status')} "
        f"idempotent_replay={result.get('idempotent_replay', False)}"
    )

unique_ids = sorted(set(task_ids))

print()
print("6. TASK ID ANALYSIS")
print("TOTAL SUBMISSIONS:", len(task_ids))
print("UNIQUE TASK IDS:", len(unique_ids))

for task_id in unique_ids:
    print("TASK ID:", task_id)

print()
print("7. REDIS MAPPING")
stored = redis_client.get(key)

print("REDIS VALUE:", stored)
print("REDIS MATCHES A TASK:", stored in unique_ids)

print()
print("8. CONCURRENCY VERDICT")

if len(unique_ids) == 1:
    print("RACE DUPLICATION: NOT DETECTED")
    print("CONCURRENT IDEMPOTENCY: PASS")
else:
    print("RACE DUPLICATION: DETECTED")
    print("CONCURRENT IDEMPOTENCY: FAIL")
    print("IMPORTANT: Multiple Celery task IDs were created for one request_id.")

print()
print("=" * 60)
print("BLOCK 31K-DT COMPLETE")
print("=" * 60)
