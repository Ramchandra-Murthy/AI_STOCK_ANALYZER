from pathlib import Path
import re

path = Path("backend/tasks/task_control.py")
text = path.read_text(encoding="utf-8")

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSJ")
print("REDIS ACCESS + IDEMPOTENCY IMPLEMENTATION DIAGNOSTIC")
print("READ-ONLY")
print("=" * 58)

print()
print("1. REDIS-RELATED REFERENCES")
for i, line in enumerate(text.splitlines(), 1):
    if any(x in line.lower() for x in [
        "redis",
        "get_redis",
        "idempotency",
        "request_id"
    ]):
        print(f"{i}: {line}")

print()
print("2. CLASS METHODS")
match = re.search(
    r"class TaskControlService.*?(?=\nclass |\Z)",
    text,
    re.S
)

if match:
    class_text = match.group(0)

    methods = re.findall(
        r"^\s+(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        class_text,
        re.M
    )

    for method in methods:
        print(method)

    print()
    print("HAS _get_redis_client:",
          "_get_redis_client" in methods)

print()
print("3. IMPORTS")
for i, line in enumerate(text.splitlines(), 1):
    if i <= 45:
        print(f"{i}: {line}")

print()
print("4. IDEMPOTENCY SECTION")
lines = text.splitlines()

for i, line in enumerate(lines):
    if "31K-DSI" in line or "idempotency_key" in line:
        start = max(0, i - 12)
        end = min(len(lines), i + 45)

        print("-" * 58)
        for n in range(start, end):
            print(f"{n+1}: {lines[n]}")

print()
print("=" * 58)
print("BLOCK 31K-DSJ DIAGNOSTIC COMPLETE")
print("READ-ONLY: NO SOURCE FILES MODIFIED")
print("=" * 58)
