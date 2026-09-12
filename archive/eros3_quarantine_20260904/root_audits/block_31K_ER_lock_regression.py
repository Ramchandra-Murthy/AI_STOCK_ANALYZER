import threading
from backend.infrastructure.redis.client import RedisClientStub

r = RedisClientStub()
results = []
barrier = threading.Barrier(20)
lock_key = "31K-ER-R-LOCK"


def worker():
    barrier.wait()
    results.append(r.acquire_lock(lock_key))


threads = [threading.Thread(target=worker) for _ in range(20)]

for t in threads:
    t.start()

for t in threads:
    t.join()

successful = sum(results)

print("SUCCESSFUL:", successful)
print("EXPECTED:", 1)

assert successful == 1

print("STORE BEFORE RELEASE:", r._store)

assert r.release_lock(lock_key) is True

print("STORE AFTER RELEASE:", r._store)

assert not any(k.startswith("lock:") for k in r._store)

print("LOCK: PASS")
