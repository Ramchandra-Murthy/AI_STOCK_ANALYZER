from fastapi.testclient import TestClient
import backend.main as m
from backend.api.routers.task_router import router as task_router
from backend.config.settings import settings

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CN PYTHON AUDIT")
print("=" * 50)

# --------------------------------------------------
# 1. APPLICATION IMPORT
# --------------------------------------------------
print("\n1. APPLICATION IMPORT")
print("-" * 50)

print("APPLICATION IMPORT: PASS")
print("APP:", type(m.app).__name__)
print("TITLE:", m.app.title)
print("VERSION:", m.app.version)

# --------------------------------------------------
# 2. TASK ROUTER SOURCE
# --------------------------------------------------
print("\n2. TASK ROUTER OBJECT")
print("-" * 50)

print("TASK ROUTER: PASS")
print("PREFIX:", task_router.prefix)
print("TAGS:", task_router.tags)

task_routes = []

for r in task_router.routes:
    methods = sorted(r.methods or [])
    full_path = r.path
    task_routes.append((full_path, methods, r.name))

    print("ROUTER |", full_path, "|", methods, "|", "NAME=", r.name)

print("TASK ROUTES:", len(task_routes))

# --------------------------------------------------
# 3. FASTAPI APP ROUTE RECONCILIATION
# --------------------------------------------------
print("\n3. FASTAPI APPLICATION ROUTES")
print("-" * 50)

app_task_routes = []

for r in m.app.routes:
    if r.path.startswith("/api/v1/tasks"):
        methods = sorted(r.methods or [])
        app_task_routes.append((r.path, methods, r.name))

        print("APP |", r.path, "|", methods, "|", "NAME=", r.name)

print("APP TASK ROUTES:", len(app_task_routes))

# --------------------------------------------------
# 4. EXACT TARGET ROUTES
# --------------------------------------------------
print("\n4. EXACT TARGET ROUTE RECONCILIATION")
print("-" * 50)

targets = [
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
    ("/api/v1/tasks/queues/status", "GET"),
    ("/api/v1/tasks/{task_id}/status", "GET"),
    ("/api/v1/tasks/{task_id}/result", "GET"),
    ("/api/v1/tasks/observability/metrics", "GET"),
    ("/api/v1/tasks/observability/details", "GET"),
    ("/api/v1/tasks/observability", "GET"),
]

route_map = {}

for r in m.app.routes:
    route_map[r.path] = set(r.methods or [])

target_pass = True

for path, method in targets:
    found = path in route_map and method in route_map[path]

    if found:
        print("FOUND |", method, path)
    else:
        print("MISSING |", method, path)
        target_pass = False

print("TARGET ROUTES:", "PASS" if target_pass else "FAIL")

# --------------------------------------------------
# 5. OPENAPI RECONCILIATION
# --------------------------------------------------
print("\n5. OPENAPI ROUTE RECONCILIATION")
print("-" * 50)

client = TestClient(m.app)

openapi_response = client.get("/openapi.json")

print("OPENAPI STATUS:", openapi_response.status_code)

openapi = openapi_response.json()
paths = openapi.get("paths", {})

openapi_pass = True

for path, method in targets:
    method_lower = method.lower()

    if path in paths and method_lower in paths[path]:
        print("OPENAPI FOUND |", method, path)
    else:
        print("OPENAPI MISSING |", method, path)
        openapi_pass = False

print("OPENAPI TARGETS:", "PASS" if openapi_pass else "FAIL")

# --------------------------------------------------
# 6. SECURITY SCHEMA
# --------------------------------------------------
print("\n6. OPENAPI SECURITY SCHEMA")
print("-" * 50)

security_schemes = openapi.get("components", {}).get("securitySchemes", {})

print("SECURITY SCHEMES:", security_schemes)

secured_operations = []

for path, item in paths.items():
    for method, operation in item.items():
        if not isinstance(operation, dict):
            continue

        if operation.get("security"):
            secured_operations.append((path, method.upper()))

print("SECURED OPERATIONS:", len(secured_operations))

for path, method in secured_operations:
    print("SECURED |", method, path)

# --------------------------------------------------
# 7. TASK SECURITY CHECK
# --------------------------------------------------
print("\n7. TASK SECURITY CHECK")
print("-" * 50)

security_pass = True

security_tests = [
    ("POST", "/api/v1/tasks/submit", {}),
    ("GET", "/api/v1/tasks/registered", {}),
    ("GET", "/api/v1/tasks/queues/status", {}),
]

for method, path, kwargs in security_tests:

    if method == "POST":
        response = client.post(path, **kwargs)
    else:
        response = client.get(path, **kwargs)

    print(method, path, "->", response.status_code, "|", response.text[:200])

    if response.status_code != 401:
        security_pass = False

print("TASK AUTH GATE:", "PASS" if security_pass else "FAIL")

# --------------------------------------------------
# 8. BUSINESS SECURITY
# --------------------------------------------------
print("\n8. BUSINESS SECURITY")
print("-" * 50)

business_tests = [
    ("POST", "/api/v1/valuation"),
    ("GET", "/api/v1/admin/queues"),
    ("GET", "/api/v1/admin/tasks"),
]

business_security_pass = True

for method, path in business_tests:

    if method == "POST":
        response = client.post(path, json={})
    else:
        response = client.get(path)

    print(method, path, "->", response.status_code)

    if response.status_code != 401:
        business_security_pass = False

print("BUSINESS AUTH GATE:", "PASS" if business_security_pass else "FAIL")

# --------------------------------------------------
# 9. SETTINGS
# --------------------------------------------------
print("\n9. SECURITY SETTINGS")
print("-" * 50)

print("ENVIRONMENT:", settings.ENVIRONMENT)
print("AUTH_ENABLED:", settings.AUTH_ENABLED)
print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
print("ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
print("JWT_SECRET CONFIGURED:", bool(settings.JWT_SECRET or settings.SECRET_KEY))

settings_pass = all(
    [
        settings.AUTH_ENABLED,
        bool(settings.JWT_SECRET or settings.SECRET_KEY),
        bool(settings.JWT_ALGORITHM),
        settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0,
    ]
)

print("SETTINGS:", "PASS" if settings_pass else "FAIL")

# --------------------------------------------------
# 10. FINAL RECONCILIATION
# --------------------------------------------------
print("\n10. FINAL ROUTE RECONCILIATION")
print("-" * 50)

print("TASK ROUTER ROUTES:", len(task_routes))
print("APP TASK ROUTES:", len(app_task_routes))
print("OPENAPI TASK ROUTES:", sum(1 for p in paths if p.startswith("/api/v1/tasks")))

final_pass = all(
    [
        target_pass,
        openapi_pass,
        security_pass,
        business_security_pass,
        settings_pass,
    ]
)

print("\n" + "=" * 50)
print("FINAL SECURITY GATE")
print("=" * 50)

print("APPLICATION IMPORT: PASS")
print("TASK ROUTE REGISTRATION:", "PASS" if target_pass else "FAIL")
print("OPENAPI ROUTES:", "PASS" if openapi_pass else "FAIL")
print("TASK AUTH:", "PASS" if security_pass else "FAIL")
print("BUSINESS AUTH:", "PASS" if business_security_pass else "FAIL")
print("SETTINGS:", "PASS" if settings_pass else "FAIL")

print("OVERALL ROUTE/SECURITY GATE:", "PASS" if final_pass else "FAIL")

print("PRODUCTION STATUS:", "READY" if final_pass else "BLOCKED")

print("=" * 50)
print("BLOCK 31K-CN COMPLETE")
print("=" * 50)
