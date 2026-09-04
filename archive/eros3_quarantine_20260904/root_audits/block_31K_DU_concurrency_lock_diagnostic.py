import inspect
import threading
import concurrent.futures

from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-DU")
print("IDEMPOTENCY CONCURRENCY LOCK DIAGNOSTIC")
print("READ-ONLY")
print("=" * 60)

print()
print("1. REDIS CLIENT")
print("CLASS:", type(redis_client))
print("MODULE:", type(redis_client).__module__)
print("STORE:", dict(redis_client._store))

print()
print("2. REDIS CLIENT METHODS")

for name in [
    "set",
    "get",
    "acquire_lock",
    "release_lock",
]:
    attr = getattr(redis_client, name, None)

    print()
    print("METHOD:", name)
    print("EXISTS:", attr is not None)

    if attr is not None:
        print("SIGNATURE:", inspect.signature(attr))
        try:
            print("SOURCE:")
            print(inspect.getsource(attr))
        except Exception as exc:
            print("SOURCE ERROR:", repr(exc))

print()
print("3. TASK CONTROL REDIS REFERENCES")

source = inspect.getsource(task_control.submit_task)

for number, line in enumerate(source.splitlines(), 1):
    if (
        "redis" in line.lower()
        or "request_id" in line.lower()
        or "idempot" in line.lower()
        or "lock" in line.lower()
    ):
        print(f"{number:04d}: {line}")

print()
print("4. LOCK BEHAVIOR TEST")

lock_key = "diagnostic-31K-DU"

redis_client.release_lock(lock_key)

results = []

def acquire(index):
    result = redis_client.acquire_lock(lock_key, timeout=10)
    results.append((index, result))
    return index, result

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(acquire, i)
        for i in range(10)
    ]

    lock_results = [future.result() for future in futures]

lock_results.sort(key=lambda x: x[0])

for index, result in lock_results:
    print(f"THREAD {index}: ACQUIRE={result}")

successful = [x for x in lock_results if x[1] is True]

print()
print("SUCCESSFUL LOCK ACQUISITIONS:", len(successful))

print()
print("5. LOCK VERDICT")

if len(successful) == 1:
    print("SINGLE OWNER LOCK: PASS")
    print("LOCK CAN SERIALIZE THE CRITICAL SECTION.")
else:
    print("SINGLE OWNER LOCK: FAIL")
    print("LOCK IMPLEMENTATION IS NOT SAFE FOR CONCURRENCY.")

redis_client.release_lock(lock_key)

print()
print("6. FINAL REDIS STORE")
print(dict(redis_client._store))

print()
print("=" * 60)
print("BLOCK 31K-DU DIAGNOSTIC COMPLETE")
print("=" * 60)
