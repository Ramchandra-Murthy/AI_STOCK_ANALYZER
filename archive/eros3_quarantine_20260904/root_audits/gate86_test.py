import requests
import time
from backend.database.engine import SessionLocal
from backend.database.models.company import ValuationRecordModel

base = "http://localhost:8000/api/v1"
login = requests.post(
    f"{base}/auth/login",
    json={"username": "gate48_admin", "password": "securepassword123"},
    timeout=10,
)
print("LOGIN_STATUS=", login.status_code)
if not login.ok:
    raise SystemExit("Authentication failed")

token = login.json()["access_token"]
headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}

symbol = "G86_REAL_FAILURE"
payload = {
    "task_name": "valuation.execute",
    "payload": {
        "symbol": symbol,
        "current_price": -10.0,
        "segments": [{"name": "Core", "valuation": -1000}],
        "net_debt": 0,
        "non_operating_assets": 0,
        "shares_outstanding": 0,
    },
}

print("SUBMITTING_DELIBERATELY_INVALID_TASK")
sub = requests.post(f"{base}/tasks/submit", json=payload, headers=headers, timeout=10)
print("SUBMIT_HTTP=", sub.status_code)
print("SUBMIT_RESPONSE=", sub.text)
if sub.status_code not in (200, 201, 202):
    raise SystemExit("Task submission failed")

task_id = sub.json().get("task_id")
if not task_id:
    raise SystemExit("No task_id returned")
print("TASK_ID=", task_id)

terminal = None
for i in range(20):
    r = requests.get(
        f"{base}/tasks/{task_id}/status", headers={"Authorization": "Bearer " + token}, timeout=10
    )
    print(f"POLL {i + 1} HTTP={r.status_code} RESPONSE={r.text}")
    if r.status_code != 200:
        time.sleep(1)
        continue
    d = r.json()
    status = d.get("status")
    if status in ("FAILURE", "FAILED", "SUCCESS"):
        terminal = status
        break
    time.sleep(1)

print("TERMINAL_STATUS=", terminal)
if terminal not in ("FAILURE", "FAILED"):
    print("ASYNC_FAILURE_PROPAGATION=FAIL")
    print("REASON=Expected FAILURE/FAILED but received:", terminal)
    raise SystemExit(1)

print("FAILURE_STATE_CONFIRMED=PASS")

db = SessionLocal()
try:
    record = db.query(ValuationRecordModel).filter_by(symbol=symbol).first()
    print("PERSISTED_RECORD=", record)
    if record is not None:
        print("NO_INVALID_RECORD_PERSISTED=FAIL")
        raise SystemExit("Invalid async task created a valuation record")
finally:
    db.close()

print("NO_INVALID_RECORD_PERSISTED=PASS")
print("ASYNC_FAILURE_PROPAGATION=PASS")
print("GATE_86=PASS")
