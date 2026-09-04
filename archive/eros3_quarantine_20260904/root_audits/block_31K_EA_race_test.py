import uuid
import concurrent.futures
from backend.tasks.task_control import task_control
from backend.infrastructure.redis.client import redis_client

redis_client._store.clear()
request_id = "EA-RACE-" + uuid.uuid4().hex

def submit_one(_):
    try:
        return task_control.submit_task(
            "valuation.execute",
            user="system",
            payload={"symbol": "TCS.NS", "request_id": request_id},
        )
    except Exception as exc:
        return {"ERROR": repr(exc)}

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(submit_one, range(10)))

print("REQUEST_ID:", request_id)
print("TOTAL:", len(results))
print("RESULTS:")
for i, result in enumerate(results):
    print(i, result)

task_ids = [
    r.get("task_id")
    for r in results
    if isinstance(r, dict) and r.get("task_id")
]

print("UNIQUE_TASK_IDS:", len(set(task_ids)))
print("REPLAYS:", sum(
    1 for r in results
    if isinstance(r, dict) and r.get("idempotent_replay")
))
print("ERRORS:", sum(
    1 for r in results
    if isinstance(r, dict) and r.get("ERROR")
))
print("REDIS_MAPPING:", redis_client.get(
    "eros:idempotency:" + request_id
))
print("FINAL_STORE:", redis_client._store)
