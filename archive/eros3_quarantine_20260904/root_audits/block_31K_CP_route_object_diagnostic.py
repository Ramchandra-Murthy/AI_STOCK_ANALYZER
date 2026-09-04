from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CP ROUTE DIAGNOSTIC")
print("=" * 50)

# --------------------------------------------------
# 1. APPLICATION IMPORT
# --------------------------------------------------
print()
print("1. APPLICATION IMPORT")
print("-" * 50)

try:
    import backend.main as m

    app = m.app

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))
    raise SystemExit(1)

# --------------------------------------------------
# 2. RAW APP.ROUTES OBJECT TYPES
# --------------------------------------------------
print()
print("2. RAW APP.ROUTES OBJECT TYPES")
print("-" * 50)

for index, r in enumerate(app.routes):

    print(
        "INDEX=",
        index,
        "| TYPE=",
        type(r).__name__,
        "| MODULE=",
        type(r).__module__,
        "| PATH=",
        getattr(r, "path", "<NO PATH>"),
        "| NAME=",
        getattr(r, "name", "<NO NAME>")
    )

# --------------------------------------------------
# 3. TASK-RELATED RAW OBJECTS
# --------------------------------------------------
print()
print("3. TASK-RELATED RAW OBJECTS")
print("-" * 50)

task_objects = []

for index, r in enumerate(app.routes):

    path = getattr(r, "path", None)

    if path and path.startswith("/api/v1/tasks"):
        task_objects.append(r)

        print(
            "TASK OBJECT | INDEX=",
            index,
            "| TYPE=",
            type(r).__name__,
            "| PATH=",
            path,
            "| METHODS=",
            getattr(r, "methods", "<NO METHODS>"),
            "| NAME=",
            getattr(r, "name", "<NO NAME>")
        )

print()
print("TASK OBJECT COUNT:", len(task_objects))

# --------------------------------------------------
# 4. APIRoute OBJECT COUNT
# --------------------------------------------------
print()
print("4. APIRoute OBJECT CHECK")
print("-" * 50)

api_routes = []

for r in app.routes:

    if isinstance(r, APIRoute):
        api_routes.append(r)

print("TOTAL APIRoute OBJECTS:", len(api_routes))

for r in api_routes:

    if getattr(r, "path", "").startswith("/api/v1/tasks"):

        print(
            "APIRoute TASK |",
            r.path,
            "|",
            sorted(r.methods or []),
            "|",
            r.name
        )

# --------------------------------------------------
# 5. TASK ROUTER DIRECT COMPARISON
# --------------------------------------------------
print()
print("5. TASK ROUTER DIRECT COMPARISON")
print("-" * 50)

from backend.api.routers.task_router import router as task_router

print("ROUTER PREFIX:", task_router.prefix)
print("ROUTER TAGS:", task_router.tags)

router_routes = []

for r in task_router.routes:

    if isinstance(r, APIRoute):

        router_routes.append(r)

        print(
            "ROUTER |",
            r.path,
            "|",
            sorted(r.methods or []),
            "|",
            r.name,
            "| DEP_COUNT=",
            len(r.dependencies)
        )

print("ROUTER ROUTE COUNT:", len(router_routes))

# --------------------------------------------------
# 6. OPENAPI COMPARISON
# --------------------------------------------------
print()
print("6. OPENAPI TASK ROUTES")
print("-" * 50)

client = TestClient(app)

response = client.get("/openapi.json")

print("OPENAPI STATUS:", response.status_code)

openapi = response.json()

openapi_task_routes = []

for path, item in openapi.get("paths", {}).items():

    if not path.startswith("/api/v1/tasks"):
        continue

    for method, operation in item.items():

        if method.lower() not in {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "options",
            "head",
        }:
            continue

        secured = bool(operation.get("security"))

        openapi_task_routes.append(
            (path, method.upper(), secured)
        )

        print(
            "OPENAPI |",
            path,
            "|",
            method.upper(),
            "| SECURITY=",
            secured
        )

print()
print("OPENAPI TASK ROUTE COUNT:", len(openapi_task_routes))

# --------------------------------------------------
# 7. LIVE SECURITY CONFIRMATION
# --------------------------------------------------
print()
print("7. LIVE SECURITY CONFIRMATION")
print("-" * 50)

tests = [
    ("POST", "/api/v1/tasks/submit"),
    ("GET", "/api/v1/tasks/registered"),
    ("GET", "/api/v1/tasks/queues/status"),
]

security_pass = True

for method, path in tests:

    if method == "POST":
        r = client.post(path, json={})
    else:
        r = client.get(path)

    print(
        method,
        path,
        "->",
        r.status_code,
        "|",
        r.text[:150]
    )

    if r.status_code != 401:
        security_pass = False

print(
    "LIVE AUTH GATE:",
    "PASS" if security_pass else "FAIL"
)

# --------------------------------------------------
# 8. MAIN.PY REGISTRATION
# --------------------------------------------------
print()
print("8. MAIN.PY REGISTRATION")
print("-" * 50)

from pathlib import Path

main_text = Path("backend/main.py").read_text(
    encoding="utf-8"
)

print(
    "TASK ROUTER IMPORT:",
    "FOUND"
    if "from backend.api.routers.task_router import router as task_router"
       in main_text
    else "MISSING"
)

print(
    "TASK ROUTER INCLUDE:",
    "FOUND"
    if "app.include_router(task_router)" in main_text
    else "MISSING"
)

# --------------------------------------------------
# 9. CONCLUSION
# --------------------------------------------------
print()
print("=" * 50)
print("DIAGNOSTIC CONCLUSION")
print("=" * 50)

print("TASK ROUTER DIRECT ROUTES:", len(router_routes))
print("APP TASK OBJECTS:", len(task_objects))
print("OPENAPI TASK ROUTES:", len(openapi_task_routes))
print(
    "LIVE SECURITY:",
    "PASS" if security_pass else "FAIL"
)

if (
    len(router_routes) == 8
    and len(openapi_task_routes) == 8
    and security_pass
):
    print()
    print("APPLICATION TASK ROUTES: FUNCTIONALLY PRESENT")
    print("OPENAPI TASK ROUTES: PRESENT")
    print("TASK AUTHENTICATION: ENFORCED")
    print()
    print("NO APPLICATION SOURCE CHANGE REQUIRED")
else:
    print()
    print("TASK ROUTE DIAGNOSTIC: REQUIRES FURTHER INVESTIGATION")

print("=" * 50)
print("BLOCK 31K-CP COMPLETE")
print("=" * 50)
