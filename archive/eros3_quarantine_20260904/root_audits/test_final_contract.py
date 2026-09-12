from backend.tasks.task_control import TaskControlService
import time
import pprint

print("==================================================")
print("   EROS 3.0 FULL TASK CONTEXT CONTRACT TEST")
print("==================================================")
control = TaskControlService()

target_user = "institutional_research_user"
payload = {
    "symbol": "TCS.NS",
    "bull_value": 4500.0,
    "base_value": 3500.0,
    "bear_value": 2500.0,
}

submission = control.submit_task(
    task_name="forecast.execute",
    user=target_user,
    payload=payload,
)

task_id = submission["task_id"]
print("Submitted Task ID :", task_id)
print("Submitted User    :", submission.get("user"))
print("")

print("WAITING FOR REAL CELERY WORKER EXECUTION...")
for i in range(15):
    time.sleep(1)
    status = control.get_task_status(task_id)
    print(f'[{i+1:02d}s] status={status.get("status")} ready={status.get("ready")}')
    if status.get("ready"):
        break

result = control.get_task_result(task_id)
print("")
print("FINAL WORKER RESULT:")
pprint.pp(result)

worker_data = result.get("result", {})
if not isinstance(worker_data, dict):
    worker_data = {}

print("")
print("==================================================")
print("EROS 3.0 CONTRACT COMPARISON MATRIX")
print("==================================================")
print(f"Control Task ID  : {task_id}")
print(f'Worker Task ID   : {worker_data.get("task_id", "MISSING")}')
print("")
print(f"Requested User   : {target_user}")
print(f'Submitted User   : {submission.get("user")}')
print(f'Worker User      : {worker_data.get("user", "MISSING")}')
print("")
print(f'Requested Symbol : {payload["symbol"]}')
print(f'Worker Symbol    : {worker_data.get("symbol", "MISSING")}')
print("==================================================")

id_match = task_id == worker_data.get("task_id")
user_match = target_user == worker_data.get("user")
symbol_match = payload["symbol"] == worker_data.get("symbol")

if id_match and user_match and symbol_match:
    print("")
    print("*** EROS CELERY TASK CONTEXT CONTRACT PASSED ***")
    print("*** UUID + USER + PAYLOAD FULLY VERIFIED ***")
else:
    print("")
    print("*** CONTRACT MISMATCH DETECTED ***")
print("==================================================")
