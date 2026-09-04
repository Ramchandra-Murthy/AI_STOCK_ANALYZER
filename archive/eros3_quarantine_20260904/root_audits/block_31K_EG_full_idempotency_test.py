import threading
import uuid

from backend.tasks.task_control import TaskControlService
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-EG")
print("FULL CONCURRENT IDEMPOTENCY TEST")
print("=" * 60)

redis_client._store.clear()

task_control = TaskControlService()

request_id = "EG-RACE-" + uuid.uuid4().hex
key = f"eros:idempotency:{request_id}"

print()
print("REQUEST_ID:", request_id)
print("KEY:", key)

results = []
errors = []
barrier = threading.Barrier(10)

def worker(index):
    try:
        barrier.wait()
        result = task_control.submit_task(
            "valuation.execute",
            payload={
                "symbol": "TCS.NS",
                "request_id": request_id,
            },
        )
        results.append((index, result))
    except Exception as exc:
        errors.append((index, repr(exc)))

threads = [
    threading.Thread(target=worker, args=(i,))
    for i in range(10)
]

print()
print("STARTING 10 SIMULTANEOUS SUBMISSIONS")

for t in threads:
    t.start()

for t in threads:
    t.join()

results.sort(key=lambda x: x[0])

print()
print("RESULTS")
for index, result in results:
    print(
        index,
        result
    )

print()
print("ERRORS:", errors)

task_ids = [
    result["task_id"]
    for _, result in results
    if "task_id" in result
]

unique_task_ids = set(task_ids)

replays = sum(
    1
    for _, result in results
    if result.get("idempotent_replay") is True
)

redis_value = redis_client.get(key)

print()
print("TOTAL SUBMISSIONS:", len(results))
print("UNIQUE TASK IDS:", len(unique_task_ids))
print("IDEMPOTENT REPLAYS:", replays)
print("REDIS VALUE:", redis_value)
print("FINAL STORE:", redis_client._store)

print()
print("=" * 60)
print("31K-EG VERDICT")
print("=" * 60)

if errors:
    raise AssertionError(f"Unexpected errors: {errors}")

if len(results) != 10:
    raise AssertionError(
        f"Expected 10 results, got {len(results)}"
    )

if len(unique_task_ids) != 1:
    raise AssertionError(
        f"IDEMPOTENCY FAILED: expected 1 unique task ID, "
        f"got {len(unique_task_ids)}"
    )

if replays != 9:
    raise AssertionError(
        f"Expected 9 idempotent replays, got {replays}"
    )

if redis_value not in unique_task_ids:
    raise AssertionError(
        "Redis mapping does not point to the unique task ID"
    )

print("UNIQUE TASK IDS: PASS")
print("EXPECTED UNIQUE TASK IDS: 1")
print("IDEMPOTENT REPLAYS: PASS")
print("EXPECTED REPLAYS: 9")
print("REDIS MAPPING: PASS")
print("CONCURRENT IDEMPOTENCY: PASS")
print("=" * 60)
print("31K-EG COMPLETE")
print("=" * 60)
