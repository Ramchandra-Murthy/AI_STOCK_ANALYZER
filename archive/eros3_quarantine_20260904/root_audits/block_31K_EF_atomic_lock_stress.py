import threading
from backend.infrastructure.redis.client import RedisClientStub

redis = RedisClientStub()
lock_key = "31K-EF-STRESS"
results = []
barrier = threading.Barrier(10)

def worker(index):
    barrier.wait()
    acquired = redis.acquire_lock(lock_key)
    results.append((index, acquired))

threads = [
    threading.Thread(target=worker, args=(i,))
    for i in range(10)
]

for t in threads:
    t.start()

for t in threads:
    t.join()

results.sort()

print("=" * 60)
print("EROS 3.0 - BLOCK 31K-EF")
print("ATOMIC REDIS LOCK STRESS TEST")
print("=" * 60)

for index, acquired in results:
    print(f"THREAD {index}: ACQUIRE={acquired}")

successes = sum(1 for _, acquired in results if acquired)

print()
print("TOTAL THREADS:", len(results))
print("SUCCESSFUL ACQUISITIONS:", successes)
print("EXPECTED SUCCESSFUL ACQUISITIONS: 1")

if successes != 1:
    raise AssertionError(
        f"Atomic lock FAILED: expected 1 owner, got {successes}"
    )

print()
print("LOCK STRESS VERDICT: PASS")

redis.release_lock(lock_key)

print("POST-RELEASE STORE:", redis._store)
print("=" * 60)
print("31K-EF COMPLETE")
print("=" * 60)
