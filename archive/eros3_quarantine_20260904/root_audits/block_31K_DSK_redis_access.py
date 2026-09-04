import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSK")
print("REDIS CLIENT LOCATION + ACCESS PATTERN")
print("READ-ONLY")
print("=" * 58)

root = Path("backend")

print()
print("1. SEARCHING ENTIRE BACKEND FOR REDIS CLIENT CREATION")

patterns = [
    "redis.Redis(",
    "Redis(",
    "from redis import",
    "import redis",
    "redis.from_url(",
    "RedisBackend",
    "redis_client",
]

for path in root.rglob("*.py"):
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except Exception:
        continue

    for n, line in enumerate(lines, 1):
        if any(p in line for p in patterns):
            print(f"{path}:{n}: {line}")

print()
print("2. TASK_CONTROL IMPORTS")
path = Path("backend/tasks/task_control.py")

lines = path.read_text(encoding="utf-8-sig").splitlines()

for n, line in enumerate(lines[:100], 1):
    print(f"{n}: {line}")

print()
print("3. TASK_CONTROL REDIS / IDEMPOTENCY CODE")

for n, line in enumerate(lines, 1):
    if any(x in line.lower() for x in [
        "redis",
        "idempotency",
        "request_id",
        "_get_redis"
    ]):
        start = max(1, n - 5)
        end = min(len(lines), n + 8)

        print("-" * 58)
        for i in range(start, end + 1):
            print(f"{i}: {lines[i-1]}")

print()
print("4. POSSIBLE REDIS MODULES")

for path in root.rglob("*.py"):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        continue

    if "redis" in text.lower():
        print(path)

print()
print("=" * 58)
print("BLOCK 31K-DSK DIAGNOSTIC COMPLETE")
print("READ-ONLY: NO SOURCE FILES MODIFIED")
print("=" * 58)
