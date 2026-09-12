import threading
import uuid

from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-DW")
print("CONCURRENT IDEMPOTENCY VERIFICATION")
print("READ-ONLY TEST")
print("=" * 60)

print("\n1. TASK CONTROL")
print("CLASS:", type(task_control))
print("REGISTERED:", task_control.get_registered_tasks())

print("\n2. REDIS")
print("CLASS:", type(redis_client))
print("INITIAL STORE:", dict(redis_client._store))

request_id = "DW-" + uuid.uuid4().hex
key = f"eros:idempotency:{request_id}"

print("\n3. SHARED REQUEST")
print("REQUEST ID:", request_id)
print("KEY:", key)

# Remove only this test's possible keys.
redis_client._store.pop(key, None)
redis_client._store.pop(f"lock:eros:idempotency-lock:{request_id}", None)

results = []
errors = []
barrier = threading.Barrier(10)
results_lock = threading.Lock()


def submit(index):
    try:
        barrier.wait()

        result = task_control.submit_task(
            task_name="valuation.execute",
            user="system",
            payload={
                "symbol": "TCS.NS",
                "request_id": request_id,
            },
        )

        with results_lock:
            results.append((index, result))

    except Exception as exc:
        with results_lock:
            errors.append((index, repr(exc)))


print("\n4. STARTING 10 SIMULTANEOUS SUBMISSIONS")

threads = [threading.Thread(target=submit, args=(i,)) for i in range(10)]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

print("\n5. SUBMISSION RESULTS")

for index, result in sorted(results):
    print(
        f"REQUEST {index}: "
        f"task_id={result.get('task_id')} "
        f"status={result.get('status')} "
        f"idempotent_replay={result.get('idempotent_replay', False)}"
    )

if errors:
    print("\nERRORS:")
    for index, error in errors:
        print(f"REQUEST {index}: {error}")

task_ids = [result.get("task_id") for _, result in results]

unique_task_ids = set(task_ids)

replays = sum(1 for _, result in results if result.get("idempotent_replay") is True)

print("\n6. TASK ID ANALYSIS")
print("TOTAL SUBMISSIONS:", len(results))
print("UNIQUE TASK IDS:", len(unique_task_ids))

for task_id in sorted(unique_task_ids):
    print("TASK ID:", task_id)

print("\n7. REDIS MAPPING")
stored_value = redis_client.get(key)

print("REDIS VALUE:", stored_value)
print("REDIS MATCHES A TASK:", stored_value in unique_task_ids)

print("\n8. IDEMPOTENCY ANALYSIS")
print("IDEMPOTENT REPLAYS:", replays)
print("EXPECTED UNIQUE TASK IDS: 1")
print("EXPECTED REPLAYS: 9")

print("\n9. CONCURRENCY VERDICT")

if (
    len(results) == 10
    and len(unique_task_ids) == 1
    and replays == 9
    and stored_value in unique_task_ids
    and not errors
):
    print("RACE DUPLICATION: NOT DETECTED")
    print("CONCURRENT IDEMPOTENCY: PASS")
    print("SINGLE TASK IDENTITY: PASS")
else:
    print("RACE DUPLICATION: DETECTED")
    print("CONCURRENT IDEMPOTENCY: FAIL")

print("\n10. FINAL REDIS STORE")
print(dict(redis_client._store))

print("\n" + "=" * 60)
print("BLOCK 31K-DW COMPLETE")
print("=" * 60)
