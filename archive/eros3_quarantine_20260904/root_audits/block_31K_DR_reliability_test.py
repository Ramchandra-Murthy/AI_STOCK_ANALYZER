import time
import uuid

from fastapi.testclient import TestClient
from backend.main import app


print("=" * 60)
print("EROS 3.0 - BLOCK 31K-DR")
print("PRODUCTION TASK RELIABILITY + OBSERVABILITY")
print("=" * 60)

client = TestClient(app)

suffix = uuid.uuid4().hex[:12]
username = f"dr_task_{suffix}"
email = f"dr_task_{suffix}@example.com"
password = "Password123!"


print("")
print("1. APPLICATION")

print("APP:", type(app))

if app is None:
    raise RuntimeError("APPLICATION IMPORT FAILED")

print("APPLICATION: PASS")


print("")
print("2. REGISTER TEST USER")

register = client.post(
    "/api/v1/auth/register",
    json={
        "username": username,
        "email": email,
        "password": password,
        "role": "ANALYST",
    },
)

print("REGISTER:", register.status_code)

if register.status_code != 201:
    print(register.text)
    raise RuntimeError("REGISTER FAILED")

print("REGISTER: PASS")


print("")
print("3. LOGIN")

login = client.post(
    "/api/v1/auth/login",
    json={
        "username": username,
        "password": password,
    },
)

print("LOGIN:", login.status_code)

if login.status_code != 200:
    print(login.text)
    raise RuntimeError("LOGIN FAILED")

login_data = login.json()
token = login_data.get("access_token")

print("TOKEN PRESENT:", bool(token))
print("ROLE:", login_data.get("user", {}).get("role"))

if not token:
    raise RuntimeError("TOKEN MISSING")

headers = {
    "Authorization": "Bearer " + token
}

print("LOGIN: PASS")


print("")
print("4. REAL CELERY CONFIGURATION")

from backend.tasks.celery_app import celery_app

print("CELERY TYPE:", type(celery_app))

if not hasattr(celery_app, "_app"):
    raise RuntimeError("REAL CELERY FACADE NOT ACTIVE")

real_app = celery_app._app

print("UNDERLYING CELERY:", type(real_app))
print("BROKER:", real_app.conf.broker_url)
print("BACKEND:", real_app.conf.result_backend)

print("REAL CELERY: PASS")


print("")
print("5. REDIS CONNECTIVITY")

import redis

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)

if not redis_client.ping():
    raise RuntimeError("REDIS PING FAILED")

print("PING: True")
print("REDIS VERSION:", redis_client.info().get("redis_version"))
print("REDIS: PASS")


print("")
print("6. TASK TYPE INVENTORY")

task_names = [
    "valuation.execute",
    "forecast.execute",
    "forecast.run",
    "report.generate",
]

for task_name in task_names:
    print(task_name, "REGISTERED:", task_name in celery_app.tasks)

print("REGISTERED TASK COUNT:", len(celery_app.tasks))


print("")
print("7. MULTI-TASK SUBMISSION")

tasks = []

for task_name in task_names:

    payload = {
        "task_name": task_name,
        "symbol": "TCS.NS",
    }

    response = client.post(
        "/api/v1/tasks/submit",
        json=payload,
        headers=headers,
    )

    print("")
    print("TASK:", task_name)
    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    if response.status_code not in (200, 202):
        raise RuntimeError(
            f"TASK SUBMISSION FAILED: {task_name}"
        )

    data = response.json()

    task_id = (
        data.get("task_id")
        or data.get("id")
        or data.get("taskId")
    )

    if not task_id:
        raise RuntimeError(
            f"TASK ID MISSING: {task_name}"
        )

    print("TASK ID:", task_id)

    tasks.append(
        {
            "name": task_name,
            "id": task_id,
        }
    )

print("")
print("TOTAL SUBMITTED:", len(tasks))

if len(tasks) != len(task_names):
    raise RuntimeError("NOT ALL TASKS SUBMITTED")

print("MULTI-TASK SUBMISSION: PASS")


print("")
print("8. UNIQUE TASK IDS")

ids = [x["id"] for x in tasks]

print("TASK IDS:", ids)
print("UNIQUE IDS:", len(set(ids)))

if len(set(ids)) != len(ids):
    raise RuntimeError("DUPLICATE TASK ID DETECTED")

print("UNIQUE TASK IDS: PASS")


print("")
print("9. WAITING FOR CELERY")

results = {}

for attempt in range(40):

    all_done = True

    for item in tasks:

        task_id = item["id"]

        if task_id in results:
            continue

        response = client.get(
            f"/api/v1/tasks/{task_id}/status",
            headers=headers,
        )

        if response.status_code != 200:
            print(
                "STATUS ERROR:",
                task_id,
                response.status_code,
                response.text,
            )
            all_done = False
            continue

        data = response.json()

        state = str(
            data.get("status")
            or data.get("state")
            or ""
        ).upper()

        print(
            "CHECK",
            attempt + 1,
            item["name"],
            task_id,
            state,
        )

        if state in ("SUCCESS", "FAILURE", "FAILED"):
            results[task_id] = data
        else:
            all_done = False

    if all_done:
        break

    time.sleep(1)

print("")
print("COMPLETED TASKS:", len(results))


print("")
print("10. TASK RESULT VALIDATION")

for item in tasks:

    task_id = item["id"]
    task_name = item["name"]

    response = client.get(
        f"/api/v1/tasks/{task_id}/result",
        headers=headers,
    )

    print("")
    print("RESULT:", task_name)
    print("HTTP:", response.status_code)
    print("BODY:", response.text)

    if response.status_code != 200:
        raise RuntimeError(
            f"RESULT API FAILED: {task_name}"
        )

    data = response.json()

    returned_id = data.get("task_id")

    if returned_id != task_id:
        raise RuntimeError(
            f"TASK ID MISMATCH: {task_name}"
        )

    status = str(
        data.get("status", "")
    ).upper()

    if status != "SUCCESS":
        raise RuntimeError(
            f"TASK NOT SUCCESSFUL: {task_name}"
        )

print("")
print("RESULT VALIDATION: PASS")


print("")
print("11. OBSERVABILITY METRICS")

response = client.get(
    "/api/v1/tasks/observability/metrics",
    headers=headers,
)

print("METRICS STATUS:", response.status_code)
print("METRICS BODY:", response.text)

if response.status_code != 200:
    raise RuntimeError("OBSERVABILITY METRICS FAILED")

print("OBSERVABILITY METRICS: PASS")


print("")
print("12. OBSERVABILITY DETAILS")

response = client.get(
    "/api/v1/tasks/observability/details",
    headers=headers,
)

print("DETAILS STATUS:", response.status_code)
print("DETAILS BODY:", response.text)

if response.status_code != 200:
    raise RuntimeError("OBSERVABILITY DETAILS FAILED")

print("OBSERVABILITY DETAILS: PASS")


print("")
print("13. QUEUE STATUS")

response = client.get(
    "/api/v1/tasks/queues/status",
    headers=headers,
)

print("QUEUE STATUS:", response.status_code)
print("QUEUE BODY:", response.text)

if response.status_code != 200:
    raise RuntimeError("QUEUE STATUS FAILED")

print("QUEUE STATUS: PASS")


print("")
print("14. ADMIN PROTECTION WITHOUT ADMIN ROLE")

response = client.get(
    "/api/v1/admin/queues",
    headers=headers,
)

print("ADMIN QUEUES:", response.status_code)
print("BODY:", response.text)

if response.status_code not in (401, 403):
    raise RuntimeError(
        "ADMIN ROUTE NOT PROTECTED FROM ANALYST"
    )

print("ADMIN ROLE PROTECTION: PASS")


print("")
print("15. FINAL SUMMARY")

print("SUBMITTED:", len(tasks))
print("COMPLETED:", len(results))
print("UNIQUE IDS:", len(set(ids)))

if len(results) != len(tasks):
    raise RuntimeError(
        "NOT ALL TASKS COMPLETED"
    )

print("")
print("=" * 60)
print("BLOCK 31K-DR COMPLETE")
print("=" * 60)
print("STATUS: PASS")
print("=" * 60)
