from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CO PYTHON AUDIT")
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

    import_ok = True
except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))
    raise SystemExit(1)

# --------------------------------------------------
# 2. TASK ROUTER OBJECT
# --------------------------------------------------
print()
print("2. TASK ROUTER OBJECT")
print("-" * 50)

try:
    from backend.api.routers.task_router import router as task_router

    print("TASK ROUTER: PASS")
    print("PREFIX:", task_router.prefix)
    print("TAGS:", task_router.tags)

    task_router_routes = []

    for r in task_router.routes:
        if isinstance(r, APIRoute):
            methods = sorted(r.methods or [])
            task_router_routes.append((r.path, methods, r.name))
            print(
                "ROUTER |",
                r.path,
                "|",
                methods,
                "| NAME=",
                r.name
            )

    print("TASK ROUTES:", len(task_router_routes))

except Exception as exc:
    print("TASK ROUTER: FAIL")
    print(type(exc).__name__ + ":", str(exc))
    raise SystemExit(1)

# --------------------------------------------------
# 3. FASTAPI APPLICATION ROUTES
# --------------------------------------------------
print()
print("3. FASTAPI APPLICATION ROUTES")
print("-" * 50)

app_task_routes = []

for r in app.routes:

    # IMPORTANT:
    # FastAPI may contain _IncludedRouter objects.
    # Only inspect actual APIRoute objects.
    if not isinstance(r, APIRoute):
        continue

    if r.path.startswith("/api/v1/tasks"):
        methods = sorted(r.methods or [])
        app_task_routes.append((r.path, methods, r.name))

        secured = bool(r.dependencies)

        print(
            "TASK |",
            r.path,
            "|",
            methods,
            "| DEP_COUNT=",
            len(r.dependencies),
            "| SECURITY=",
            secured,
            "| NAME=",
            r.name
        )

print()
print("APPLICATION TASK ROUTES:", len(app_task_routes))

# --------------------------------------------------
# 4. EXACT ROUTE RECONCILIATION
# --------------------------------------------------
print()
print("4. EXACT ROUTE RECONCILIATION")
print("-" * 50)

expected_routes = {
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
    ("/api/v1/tasks/queues/status", "GET"),
    ("/api/v1/tasks/{task_id}/status", "GET"),
    ("/api/v1/tasks/{task_id}/result", "GET"),
    ("/api/v1/tasks/observability/metrics", "GET"),
    ("/api/v1/tasks/observability/details", "GET"),
    ("/api/v1/tasks/observability", "GET"),
}

actual_routes = set()

for path, methods, name in app_task_routes:
    for method in methods:
        actual_routes.add((path, method))

missing = sorted(expected_routes - actual_routes)
unexpected = sorted(actual_routes - expected_routes)

if not missing:
    print("EXPECTED ROUTES: ALL PRESENT")
else:
    print("MISSING ROUTES:")
    for item in missing:
        print(" ", item)

if unexpected:
    print("UNEXPECTED TASK ROUTES:")
    for item in unexpected:
        print(" ", item)
else:
    print("UNEXPECTED ROUTES: NONE")

route_reconciliation = not missing

# --------------------------------------------------
# 5. OPENAPI TASK ROUTES
# --------------------------------------------------
print()
print("5. OPENAPI TASK ROUTES")
print("-" * 50)

client = TestClient(app)

openapi_response = client.get("/openapi.json")

print("OPENAPI STATUS:", openapi_response.status_code)

openapi = openapi_response.json()

openapi_routes = set()

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
            "head"
        }:
            continue

        method_upper = method.upper()
        openapi_routes.add((path, method_upper))

        print(
            "OPENAPI |",
            path,
            "|",
            method_upper,
            "| SECURITY=",
            bool(operation.get("security"))
        )

print()
print("OPENAPI TASK ROUTES:", len(openapi_routes))

openapi_missing = sorted(expected_routes - openapi_routes)

if openapi_missing:
    print("OPENAPI MISSING:")
    for item in openapi_missing:
        print(" ", item)
else:
    print("OPENAPI ROUTES: ALL PRESENT")

# --------------------------------------------------
# 6. OPENAPI SECURITY FOR TASK ROUTES
# --------------------------------------------------
print()
print("6. OPENAPI TASK SECURITY")
print("-" * 50)

security_failures = []

for path, method in sorted(expected_routes):

    operation = openapi.get("paths", {}).get(path, {}).get(method.lower())

    if operation is None:
        print(
            path,
            "|",
            method,
            "| NOT FOUND"
        )
        security_failures.append((path, method, "MISSING"))
        continue

    secured = bool(operation.get("security"))

    print(
        path,
        "|",
        method,
        "| SECURITY=",
        secured
    )

    if not secured:
        security_failures.append((path, method, "OPEN"))

if security_failures:
    print()
    print("TASK SECURITY FAILURES:")
    for item in security_failures:
        print(" ", item)
else:
    print("TASK SECURITY: ALL EXPECTED ROUTES PROTECTED")

# --------------------------------------------------
# 7. LIVE UNAUTHENTICATED TASK TESTS
# --------------------------------------------------
print()
print("7. LIVE UNAUTHENTICATED TASK TESTS")
print("-" * 50)

live_tests = [
    ("POST", "/api/v1/tasks/submit"),
    ("GET", "/api/v1/tasks/registered"),
    ("GET", "/api/v1/tasks/queues/status"),
]

live_failures = []

for method, path in live_tests:

    if method == "POST":
        response = client.post(path, json={})
    else:
        response = client.get(path)

    print(
        method,
        path,
        "->",
        response.status_code,
        "|",
        response.text[:200]
    )

    if response.status_code != 401:
        live_failures.append(
            (method, path, response.status_code)
        )

if live_failures:
    print("AUTH GATE: FAIL")
else:
    print("AUTH GATE: PASS")

# --------------------------------------------------
# 8. MAIN.PY ROUTER REGISTRATION
# --------------------------------------------------
print()
print("8. MAIN.PY TASK ROUTER REGISTRATION")
print("-" * 50)

from pathlib import Path

main_path = Path("backend/main.py")
main_text = main_path.read_text(encoding="utf-8")

registration_found = (
    "app.include_router(task_router)" in main_text
)

import_found = (
    "from backend.api.routers.task_router import router as task_router"
    in main_text
)

print(
    "TASK ROUTER IMPORT:",
    "FOUND" if import_found else "MISSING"
)

print(
    "TASK ROUTER REGISTRATION:",
    "FOUND" if registration_found else "MISSING"
)

# --------------------------------------------------
# 9. DUPLICATE INLINE TASK ROUTES
# --------------------------------------------------
print()
print("9. INLINE TASK ROUTE AUDIT")
print("-" * 50)

inline_task_patterns = [
    '@app.post("/api/v1/tasks/',
    '@app.get("/api/v1/tasks/',
    '@app.put("/api/v1/tasks/',
    '@app.patch("/api/v1/tasks/',
    '@app.delete("/api/v1/tasks/',
]

inline_count = 0

for pattern in inline_task_patterns:
    count = main_text.count(pattern)
    if count:
        print(
            pattern,
            "| COUNT=",
            count
        )
        inline_count += count

if inline_count == 0:
    print("INLINE TASK ROUTES: NONE")
else:
    print("INLINE TASK ROUTES: FOUND")

# --------------------------------------------------
# 10. FINAL GATE
# --------------------------------------------------
print()
print("=" * 50)
print("FINAL TASK ROUTE SECURITY GATE")
print("=" * 50)

print(
    "APPLICATION IMPORT:",
    "PASS" if import_ok else "FAIL"
)

print(
    "TASK ROUTER:",
    "PASS" if task_router_routes else "FAIL"
)

print(
    "ROUTE RECONCILIATION:",
    "PASS" if route_reconciliation else "FAIL"
)

print(
    "OPENAPI ROUTES:",
    "PASS" if not openapi_missing else "FAIL"
)

print(
    "OPENAPI SECURITY:",
    "PASS" if not security_failures else "FAIL"
)

print(
    "UNAUTHENTICATED GATE:",
    "PASS" if not live_failures else "FAIL"
)

print(
    "MAIN ROUTER IMPORT:",
    "PASS" if import_found else "FAIL"
)

print(
    "MAIN ROUTER REGISTRATION:",
    "PASS" if registration_found else "FAIL"
)

print(
    "INLINE TASK ROUTES:",
    "PASS" if inline_count == 0 else "FAIL"
)

overall = all([
    import_ok,
    bool(task_router_routes),
    route_reconciliation,
    not openapi_missing,
    not security_failures,
    not live_failures,
    import_found,
    registration_found,
    inline_count == 0,
])

print()
print(
    "OVERALL TASK ROUTE GATE:",
    "PASS" if overall else "FAIL"
)

print(
    "PRODUCTION STATUS:",
    "READY" if overall else "BLOCKED"
)

print("=" * 50)
print("BLOCK 31K-CO COMPLETE")
print("=" * 50)
