import inspect
import traceback

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSO")
print("IDEMPOTENCY RUNTIME PATH DIAGNOSTIC")
print("READ-ONLY")
print("=" * 58)

print()
print("1. IMPORTING TASK CONTROL")

try:
    import backend.tasks.task_control as tc_module
    from backend.tasks.task_control import task_control
    print("TASK CONTROL IMPORT: PASS")
except Exception as exc:
    print("TASK CONTROL IMPORT: FAIL")
    print(repr(exc))
    traceback.print_exc()
    raise

print()
print("2. IMPORTING REDIS CLIENT")

try:
    import backend.infrastructure.redis.client as redis_module
    from backend.infrastructure.redis.client import redis_client
    print("REDIS MODULE IMPORT: PASS")
except Exception as exc:
    print("REDIS IMPORT: FAIL")
    print(repr(exc))
    traceback.print_exc()
    raise

print()
print("3. REDIS OBJECT IDENTITY")

print("TEST redis_client ID :", id(redis_client))

task_module_redis = getattr(tc_module, "redis_client", None)

print("TASK MODULE REDIS ID  :", id(task_module_redis))
print("SAME OBJECT           :", task_module_redis is redis_client)

print()
print("4. REDIS OBJECT TYPES")

print("TEST REDIS TYPE:")
print(type(redis_client))

print("TASK MODULE REDIS TYPE:")
print(type(task_module_redis))

print()
print("5. REDIS STORE IDENTITY")

print("TEST STORE ID:", id(redis_client._store))

if task_module_redis is not None:
    print("TASK STORE ID:", id(task_module_redis._store))
    print(
        "SAME STORE:",
        task_module_redis._store is redis_client._store
    )

print("TEST STORE:", redis_client._store)

if task_module_redis is not None:
    print("TASK STORE:", task_module_redis._store)

print()
print("6. REDIS SET SIGNATURE")

print(inspect.signature(redis_client.set))

print()
print("7. REDIS GET SIGNATURE")

print(inspect.signature(redis_client.get))

print()
print("8. TASK CONTROL SUBMIT_TASK SOURCE")

source = inspect.getsource(task_control.submit_task)

lines = source.splitlines()

for number, line in enumerate(lines, 1):
    if (
        "31K-DSI" in line
        or "request_id" in line
        or "redis_client" in line
        or "idempotency_key" in line
        or "ttl=" in line
        or "except Exception" in line
    ):
        print(f"{number:04d}: {line}")

print()
print("9. FULL IDEMPOTENCY BLOCK")

start = None

for number, line in enumerate(lines):
    if "31K-DSI IDEMPOTENCY" in line:
        start = number
        break

if start is not None:
    for number, line in enumerate(
        lines[start:start + 115],
        start + 1
    ):
        print(f"{number:04d}: {line}")
else:
    print("IDEMPOTENCY BLOCK NOT FOUND")

print()
print("10. DIRECT REDIS TEST")

test_key = "eros:diagnostic:31K-DSO"

try:
    result = redis_client.set(
        test_key,
        "DSO_TEST",
        ttl=86400,
    )

    print("SET RESULT:", result)
    print("GET RESULT:", redis_client.get(test_key))
    print("STORE AFTER SET:", redis_client._store)

except Exception as exc:
    print("DIRECT REDIS SET FAILED")
    print("ERROR:", repr(exc))
    traceback.print_exc()

print()
print("11. TASK CONTROL REDIS TEST")

if task_module_redis is not None:

    test_key_2 = "eros:diagnostic:31K-DSO-TASK"

    try:
        result2 = task_module_redis.set(
            test_key_2,
            "TASK_TEST",
            ttl=86400,
        )

        print("TASK REDIS SET RESULT:", result2)
        print(
            "TASK REDIS GET RESULT:",
            task_module_redis.get(test_key_2)
        )
        print(
            "TASK REDIS STORE:",
            task_module_redis._store
        )

    except Exception as exc:
        print("TASK REDIS SET FAILED")
        print("ERROR:", repr(exc))
        traceback.print_exc()

print()
print("12. CURRENT SOURCE FILE CHECK")

file_path = "backend/tasks/task_control.py"

with open(file_path, "r", encoding="utf-8-sig") as f:
    file_content = f.read()

print(
    "REDIS IMPORT PRESENT:",
    "from backend.infrastructure.redis.client import redis_client"
    in file_content
)

print(
    "INVALID ACCESSOR PRESENT:",
    "self._get_redis_client()"
    in file_content
)

print(
    "TTL=86400 PRESENT:",
    "ttl=86400"
    in file_content
)

print(
    "EX=86400 PRESENT:",
    "ex=86400"
    in file_content
)

print()
print("=" * 58)
print("BLOCK 31K-DSO DIAGNOSTIC COMPLETE")
print("READ-ONLY: NO SOURCE FILES MODIFIED")
print("=" * 58)
