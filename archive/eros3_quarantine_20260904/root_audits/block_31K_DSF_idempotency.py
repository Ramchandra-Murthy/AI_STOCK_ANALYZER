import time
import uuid

from backend.tasks.task_control import task_control

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-DSF")
print("IDEMPOTENCY + DUPLICATE SUBMISSION AUDIT")
print("=" * 58)

logical_request_id = "IDEMP-" + uuid.uuid4().hex

payload = {"symbol": "TCS.NS", "request_id": logical_request_id}

print("\n1. LOGICAL REQUEST ID")
print("REQUEST ID:", logical_request_id)

print("\n2. FIRST SUBMISSION")

first = task_control.submit_task(task_name="valuation.execute", user="system", payload=payload)

print("FIRST:", first)

first_id = first["task_id"]

print("FIRST TASK ID:", first_id)

print("\n3. SECOND IDENTICAL SUBMISSION")

second = task_control.submit_task(task_name="valuation.execute", user="system", payload=payload)

print("SECOND:", second)

second_id = second["task_id"]

print("SECOND TASK ID:", second_id)

print("\n4. DUPLICATE ANALYSIS")

print("FIRST ID :", first_id)
print("SECOND ID:", second_id)

if first_id == second_id:
    print("IDEMPOTENCY: SAME TASK ID")
else:
    print("IDEMPOTENCY: DISTINCT TASK IDS")
    print("NOTE: Current control plane may not implement deduplication.")

print("\n5. WAITING FOR TASKS")

for task_id in [first_id, second_id]:

    for i in range(30):

        status = task_control.get_task_status(task_id)

        print(task_id, "CHECK", i + 1, status.get("status"))

        if status.get("status") in ("SUCCESS", "FAILURE", "FAILED", "NOT_FOUND"):
            break

        time.sleep(2)

print("\n6. FINAL RESULTS")

first_result = task_control.get_task_result(first_id)
second_result = task_control.get_task_result(second_id)

print("FIRST RESULT:")
print(first_result)

print("\nSECOND RESULT:")
print(second_result)

print("\n7. RESULT IDENTITY")

if first_id == second_id:

    print("SINGLE TASK EXECUTION ID")
    print("IDEMPOTENCY KEY HONORED: PASS")

else:

    print("TWO TASK EXECUTION IDS CREATED")

    if first_result.get("status") == "SUCCESS" and second_result.get("status") == "SUCCESS":
        print("BOTH TASKS EXECUTED SUCCESSFULLY")
        print("DUPLICATE EXECUTION: DETECTED")

print("\n8. OBSERVABILITY")

metrics = task_control.get_task_metrics()

print(metrics)

print("\n==================================================")
print("BLOCK 31K-DSF COMPLETE")
print("==================================================")
