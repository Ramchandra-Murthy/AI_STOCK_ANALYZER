import concurrent.futures
import uuid

from backend.tasks.task_control import TaskControlService
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("31K-EK | CONCURRENT IDEMPOTENCY VERIFICATION")
print("=" * 60)

service = TaskControlService()
redis_client._store.clear()

request_id = "EK-RACE-" + uuid.uuid4().hex
key = f"eros:idempotency:{request_id}"

print("REQUEST_ID:", request_id)
print("KEY:", key)
print("STARTING 10 SIMULTANEOUS SUBMISSIONS")
print()


def submit(_):
    try:
        return service.submit_task(
            "valuation.execute",
            "system",
            {
                "request_id": request_id,
                "symbol": "TCS.NS",
            },
        )
    except Exception as exc:
        return {"ERROR": repr(exc)}


with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(submit, range(10)))

print("RESULTS")
for i, result in enumerate(results):
    print(i, result)

errors = [r for r in results if "ERROR" in r]

task_ids = [r.get("task_id") for r in results if isinstance(r, dict) and r.get("task_id")]

unique_ids = set(task_ids)

replays = [r for r in results if isinstance(r, dict) and r.get("idempotent_replay") is True]

redis_value = redis_client.get(key)

print()
print("ERRORS:", errors)
print("TOTAL SUBMISSIONS:", len(results))
print("TASK IDS:", task_ids)
print("UNIQUE TASK IDS:", len(unique_ids))
print("IDEMPOTENT REPLAYS:", len(replays))
print("REDIS VALUE:", redis_value)
print("FINAL STORE:", redis_client._store)

print()
print("=" * 60)
print("31K-EK VERDICT")
print("=" * 60)

if errors:
    raise AssertionError(f"Concurrency produced errors: {errors}")

if len(unique_ids) != 1:
    raise AssertionError(f"IDEMPOTENCY FAILED: expected 1 unique task ID, got {len(unique_ids)}")

if len(replays) != 9:
    raise AssertionError(f"IDEMPOTENCY FAILED: expected 9 replays, got {len(replays)}")

only_task_id = next(iter(unique_ids))

if redis_value != only_task_id:
    raise AssertionError("REDIS MAPPING FAILED: Redis value does not match unique task ID")

lock_key = f"lock:eros:idempotency-lock:{request_id}"

if redis_client.get(lock_key) is not None:
    raise AssertionError("LOCK CLEANUP FAILED: idempotency lock remains")

print("UNIQUE TASK IDS: PASS")
print("9 REPLAYS: PASS")
print("REDIS MAPPING: PASS")
print("LOCK CLEANUP: PASS")
print("CONCURRENT IDEMPOTENCY: PASS")
print("=" * 60)
