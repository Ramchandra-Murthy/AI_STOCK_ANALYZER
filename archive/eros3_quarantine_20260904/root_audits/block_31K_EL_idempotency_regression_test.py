import concurrent.futures
import uuid

from backend.tasks.task_control import TaskControlService
from backend.infrastructure.redis.client import redis_client

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-EL")
print("IDEMPOTENCY REGRESSION SUITE")
print("READ-ONLY")
print("=" * 60)

service = TaskControlService()
redis_client._store.clear()

# ------------------------------------------------------------
# TEST 1 - SEQUENTIAL DUPLICATE
# ------------------------------------------------------------
print()
print("1. SEQUENTIAL DUPLICATE TEST")

request_id_1 = "EL-SEQ-" + uuid.uuid4().hex

first = service.submit_task(
    "valuation.execute",
    "system",
    {
        "request_id": request_id_1,
        "symbol": "TCS.NS",
    },
)

second = service.submit_task(
    "valuation.execute",
    "system",
    {
        "request_id": request_id_1,
        "symbol": "TCS.NS",
    },
)

print("FIRST TASK:", first["task_id"])
print("SECOND TASK:", second["task_id"])
print("SAME TASK ID:", first["task_id"] == second["task_id"])
print("SECOND IS REPLAY:", second.get("idempotent_replay", False))

assert first["task_id"] == second["task_id"]
assert second.get("idempotent_replay") is True

print("SEQUENTIAL DUPLICATE: PASS")

# ------------------------------------------------------------
# TEST 2 - CONCURRENT DUPLICATE
# ------------------------------------------------------------
print()
print("2. CONCURRENT DUPLICATE TEST")

request_id_2 = "EL-RACE-" + uuid.uuid4().hex
key_2 = f"eros:idempotency:{request_id_2}"

def submit_concurrent(_):
    return service.submit_task(
        "valuation.execute",
        "system",
        {
            "request_id": request_id_2,
            "symbol": "TCS.NS",
        },
    )

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    concurrent_results = list(
        executor.map(submit_concurrent, range(10))
    )

concurrent_ids = [
    r["task_id"]
    for r in concurrent_results
]

unique_concurrent_ids = set(concurrent_ids)

concurrent_replays = [
    r for r in concurrent_results
    if r.get("idempotent_replay") is True
]

print("TOTAL:", len(concurrent_results))
print("UNIQUE TASK IDS:", len(unique_concurrent_ids))
print("REPLAYS:", len(concurrent_replays))
print("REDIS VALUE:", redis_client.get(key_2))

assert len(concurrent_results) == 10
assert len(unique_concurrent_ids) == 1
assert len(concurrent_replays) == 9
assert redis_client.get(key_2) == next(iter(unique_concurrent_ids))

print("CONCURRENT DUPLICATE: PASS")

# ------------------------------------------------------------
# TEST 3 - DIFFERENT REQUEST IDS MUST REMAIN INDEPENDENT
# ------------------------------------------------------------
print()
print("3. DIFFERENT REQUEST ID INDEPENDENCE")

request_id_3a = "EL-A-" + uuid.uuid4().hex
request_id_3b = "EL-B-" + uuid.uuid4().hex

result_a = service.submit_task(
    "valuation.execute",
    "system",
    {
        "request_id": request_id_3a,
        "symbol": "TCS.NS",
    },
)

result_b = service.submit_task(
    "valuation.execute",
    "system",
    {
        "request_id": request_id_3b,
        "symbol": "TCS.NS",
    },
)

print("REQUEST A:", request_id_3a)
print("TASK A:", result_a["task_id"])
print("REQUEST B:", request_id_3b)
print("TASK B:", result_b["task_id"])
print("TASK IDS DIFFERENT:", result_a["task_id"] != result_b["task_id"])

assert result_a["task_id"] != result_b["task_id"]

print("REQUEST ID INDEPENDENCE: PASS")

# ------------------------------------------------------------
# TEST 4 - REDIS MAPPINGS
# ------------------------------------------------------------
print()
print("4. REDIS MAPPING VERIFICATION")

key_1 = f"eros:idempotency:{request_id_1}"
key_3a = f"eros:idempotency:{request_id_3a}"
key_3b = f"eros:idempotency:{request_id_3b}"

mapping_1 = redis_client.get(key_1)
mapping_2 = redis_client.get(key_2)
mapping_a = redis_client.get(key_3a)
mapping_b = redis_client.get(key_3b)

print("SEQUENTIAL MAPPING:", mapping_1)
print("CONCURRENT MAPPING:", mapping_2)
print("REQUEST A MAPPING:", mapping_a)
print("REQUEST B MAPPING:", mapping_b)

assert mapping_1 == first["task_id"]
assert mapping_2 == next(iter(unique_concurrent_ids))
assert mapping_a == result_a["task_id"]
assert mapping_b == result_b["task_id"]

print("REDIS MAPPINGS: PASS")

# ------------------------------------------------------------
# TEST 5 - LOCK CLEANUP
# ------------------------------------------------------------
print()
print("5. LOCK CLEANUP")

lock_1 = f"lock:eros:idempotency-lock:{request_id_1}"
lock_2 = f"lock:eros:idempotency-lock:{request_id_2}"
lock_3a = f"lock:eros:idempotency-lock:{request_id_3a}"
lock_3b = f"lock:eros:idempotency-lock:{request_id_3b}"

locks_remaining = [
    key for key in [lock_1, lock_2, lock_3a, lock_3b]
    if redis_client.get(key) is not None
]

print("LOCKS REMAINING:", locks_remaining)

assert not locks_remaining

print("LOCK CLEANUP: PASS")

# ------------------------------------------------------------
# TEST 6 - FINAL STORE ANALYSIS
# ------------------------------------------------------------
print()
print("6. FINAL REDIS STORE")

for key, value in redis_client._store.items():
    print(key, "=>", value)

lock_entries = [
    key for key in redis_client._store
    if key.startswith("lock:")
]

idempotency_entries = [
    key for key in redis_client._store
    if key.startswith("eros:idempotency:")
]

print()
print("LOCK ENTRIES:", len(lock_entries))
print("IDEMPOTENCY ENTRIES:", len(idempotency_entries))

assert len(lock_entries) == 0
assert len(idempotency_entries) >= 4

print("FINAL STORE: PASS")

# ------------------------------------------------------------
# FINAL VERDICT
# ------------------------------------------------------------
print()
print("=" * 60)
print("31K-EL VERDICT")
print("=" * 60)
print("SEQUENTIAL IDEMPOTENCY: PASS")
print("CONCURRENT IDEMPOTENCY: PASS")
print("9 CONCURRENT REPLAYS: PASS")
print("REQUEST ID INDEPENDENCE: PASS")
print("REDIS MAPPINGS: PASS")
print("LOCK CLEANUP: PASS")
print("FINAL STORE: PASS")
print("IDEMPOTENCY REGRESSION SUITE: PASS")
print("=" * 60)