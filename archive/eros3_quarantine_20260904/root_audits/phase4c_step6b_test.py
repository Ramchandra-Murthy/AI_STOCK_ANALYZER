import time
from backend.tasks.task_control import TaskControlService

print("==================================================")
print("EROS 3.0 PHASE 4C - STEP 6B")
print("REAL END-TO-END WORKFLOW PROPAGATION TEST")
print("==================================================")

control = TaskControlService()

workflow_id = "WF-E2E-PHASE4C-001"
payload = {
    "symbol": "TCS.NS",
    "bull_value": 5000.0,
    "base_value": 4000.0,
    "bear_value": 3000.0,
    "workflow_id": workflow_id,
}

print("")
print("Submitting workflow-aware task via TaskControlService...")
submission = control.submit_task(
    task_name="forecast.execute",
    user="e2e_phase4c_user",
    payload=payload,
)

task_id = submission.get("task_id")
print("Control Task ID  :", task_id)
print("Submitted User   :", submission.get("user"))
print("Initial Status   :", submission.get("status"))

print("")
print("Waiting for Celery worker execution and result backend update...")
max_attempts = 15
result_data = None

for attempt in range(1, max_attempts + 1):
    status_info = control.get_task_status(task_id)
    celery_status = status_info.get("status")
    print(f"Attempt {attempt:2d}: Task Celery Status -> {celery_status}")
    if status_info.get("ready") or celery_status in ("SUCCESS", "FAILURE"):
        break
    time.sleep(1.0)

print("")
print("Fetching final task result from SQLite backend...")
task_res = control.get_task_result(task_id)
print("Result Envelope  :")
import pprint

pprint.pprint(task_res)

inner_result = task_res.get("result", {})
if isinstance(inner_result, dict):
    res_task_id = inner_result.get("task_id")
    res_user = inner_result.get("user")
    res_workflow_id = inner_result.get("workflow_id")
    res_symbol = inner_result.get("symbol")
else:
    res_task_id = res_user = res_workflow_id = res_symbol = None

print("")
print("--------------------------------------------------")
print("END-TO-END CORRELATION VERIFICATION:")
print("--------------------------------------------------")
print(f"Task ID Match    : {res_task_id == task_id} ({res_task_id})")
print(f"User Match       : {res_user == 'e2e_phase4c_user'} ({res_user})")
print(f"Workflow ID Match: {res_workflow_id == workflow_id} ({res_workflow_id})")
print(f"Symbol Match     : {res_symbol == 'TCS.NS'} ({res_symbol})")

checks = {
    "TASK_ID_PROPAGATION": res_task_id == task_id,
    "USER_PROPAGATION": res_user == "e2e_phase4c_user",
    "WORKFLOW_PROPAGATION": res_workflow_id == workflow_id,
    "SYMBOL_PROPAGATION": res_symbol == "TCS.NS",
}

print("")
print("==================================================")
print("PHASE 4C STEP 6B MATRIX")
print("==================================================")
for name, passed in checks.items():
    print(f"{name:<24}: {'PASS' if passed else 'FAIL'}")

print("")
print("==================================================")
if all(checks.values()):
    print("*** PHASE 4C STEP 6B PASSED CLEANLY ***")
    print("*** FULL CONTROL -> BROKER -> WORKER -> BACKEND SUCCESS ***")
else:
    print("*** PHASE 4C STEP 6B REQUIRES REVIEW ***")
print("==================================================")
