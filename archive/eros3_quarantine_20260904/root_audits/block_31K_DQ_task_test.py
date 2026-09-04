import time
import uuid

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)

suffix = uuid.uuid4().hex[:12]

username = f"dq_task_{suffix}"
email = f"dq_task_{suffix}@example.com"
password = "Password123!"

print("1. REGISTER")
print("USERNAME:", username)

register = client.post(
    "/api/v1/auth/register",
    json={
        "username": username,
        "email": email,
        "password": password,
        "role": "ANALYST",
    },
)

print("REGISTER STATUS:", register.status_code)
print("REGISTER BODY:", register.text)

if register.status_code not in (201, 400):
    raise RuntimeError("REGISTER FAILED")


print("")
print("2. LOGIN")

login = client.post(
    "/api/v1/auth/login",
    json={
        "username": username,
        "password": password,
    },
)

print("LOGIN STATUS:", login.status_code)
print("LOGIN BODY:", login.text)

if login.status_code != 200:
    raise RuntimeError("LOGIN FAILED")

login_data = login.json()

token = login_data.get("access_token")

print("ACCESS TOKEN PRESENT:", bool(token))
print("TOKEN TYPE:", login_data.get("token_type"))
print("EXPIRES IN:", login_data.get("expires_in"))

if not token:
    raise RuntimeError("ACCESS TOKEN MISSING")


headers = {
    "Authorization": "Bearer " + token
}


print("")
print("3. AUTHENTICATED TASK SUBMISSION")

payload = {
    "task_name": "valuation.execute",
    "symbol": "TCS.NS",
}

submit = client.post(
    "/api/v1/tasks/submit",
    json=payload,
    headers=headers,
)

print("SUBMIT STATUS:", submit.status_code)
print("SUBMIT BODY:", submit.text)

if submit.status_code not in (200, 202):
    raise RuntimeError("TASK SUBMISSION FAILED")

submission = submit.json()

task_id = (
    submission.get("task_id")
    or submission.get("id")
    or submission.get("taskId")
)

print("TASK ID:", task_id)

if not task_id:
    raise RuntimeError("TASK ID NOT RETURNED")


print("")
print("4. WAITING FOR CELERY WORKER")

final_status = None

for attempt in range(30):

    time.sleep(1)

    status_response = client.get(
        f"/api/v1/tasks/{task_id}/status",
        headers=headers,
    )

    print(
        "STATUS CHECK",
        attempt + 1,
        ":",
        status_response.status_code,
        status_response.text,
    )

    if status_response.status_code == 200:

        try:
            status_data = status_response.json()
        except Exception:
            status_data = {}

        state = str(
            status_data.get("state")
            or status_data.get("status")
            or ""
        ).upper()

        final_status = state

        if state in ("SUCCESS", "FAILURE", "FAILED"):
            break


print("")
print("5. FINAL TASK STATUS")
print("STATE:", final_status)


print("")
print("6. TASK RESULT")

result_response = client.get(
    f"/api/v1/tasks/{task_id}/result",
    headers=headers,
)

print("RESULT STATUS:", result_response.status_code)
print("RESULT BODY:", result_response.text)


print("")
print("==================================================")
print("BLOCK 31K-DQ COMPLETE")
print("==================================================")
