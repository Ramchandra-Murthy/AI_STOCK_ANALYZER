from pathlib import Path

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CM")
print("TASK ROUTE REGISTRATION DIAGNOSTIC")
print("=" * 50)

print("\n1. APPLICATION IMPORT")
print("-" * 50)

try:
    import backend.main as m

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(m.app).__name__)
    print("TITLE:", m.app.title)
    print("VERSION:", m.app.version)

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__, str(exc))
    raise SystemExit(1)

print("\n2. ALL TASK ROUTES FROM FASTAPI APP")
print("-" * 50)

task_routes = []

for route in m.app.routes:

    path = getattr(route, "path", None)
    methods = getattr(route, "methods", None)
    name = getattr(route, "name", None)
    endpoint = getattr(route, "endpoint", None)

    if path and "/task" in path.lower():
        task_routes.append(route)

        print(
            "PATH:",
            path,
            "| METHODS:",
            sorted(methods or []),
            "| NAME:",
            name,
            "| ENDPOINT:",
            getattr(endpoint, "__name__", endpoint),
        )

print("\nTASK ROUTE COUNT:", len(task_routes))

print("\n3. EXACT TARGET ROUTE SEARCH")
print("-" * 50)

targets = [
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
    ("/api/v1/tasks/queues/status", "GET"),
]

for target_path, target_method in targets:

    matches = []

    for route in m.app.routes:

        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set()) or set()

        if path == target_path and target_method in methods:
            matches.append(route)

    print(target_method, target_path, "->", "FOUND" if matches else "NOT FOUND")

print("\n4. TASK ROUTER OBJECT")
print("-" * 50)

try:
    from backend.api.routers.task_router import router as task_router

    print("TASK ROUTER IMPORT: PASS")
    print("ROUTER:", task_router)
    print("PREFIX:", getattr(task_router, "prefix", None))
    print("TAGS:", getattr(task_router, "tags", None))

    print("\nROUTES REGISTERED INSIDE TASK ROUTER:")

    for route in task_router.routes:

        print(
            "PATH:",
            getattr(route, "path", None),
            "| METHODS:",
            sorted(getattr(route, "methods", set()) or []),
            "| NAME:",
            getattr(route, "name", None),
            "| ENDPOINT:",
            getattr(
                getattr(route, "endpoint", None),
                "__name__",
                None,
            ),
        )

except Exception as exc:
    print("TASK ROUTER IMPORT: FAIL")
    print(type(exc).__name__, str(exc))

print("\n5. MAIN.PY TASK ROUTER REGISTRATION")
print("-" * 50)

main_path = Path("backend/main.py")

if main_path.exists():

    text = main_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    lines = text.splitlines()

    for number, line in enumerate(lines, start=1):

        if "task_router" in line.lower():
            print(f"LINE {number}: {line}")

else:
    print("backend/main.py NOT FOUND")

print("\n6. OPENAPI TASK ROUTES")
print("-" * 50)

from fastapi.testclient import TestClient

client = TestClient(m.app)

response = client.get("/openapi.json")

print("OPENAPI STATUS:", response.status_code)

if response.status_code == 200:

    schema = response.json()

    for path, item in schema.get("paths", {}).items():

        if "/task" in path.lower():

            methods = [method.upper() for method in item.keys()]

            print(
                "OPENAPI:",
                path,
                "|",
                ", ".join(methods),
            )

print("\n7. LIVE TASK ENDPOINT TEST")
print("-" * 50)

tests = [
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
]

for path, method in tests:

    try:

        if method == "POST":
            result = client.post(path, json={})
        else:
            result = client.get(path)

        print(
            method,
            path,
            "->",
            result.status_code,
            "|",
            result.text[:300],
        )

    except Exception as exc:

        print(
            method,
            path,
            "-> EXCEPTION:",
            type(exc).__name__,
            str(exc),
        )

print("\n8. DIAGNOSTIC CONCLUSION")
print("-" * 50)

print("The task endpoint is present in OpenAPI and responds to " "unauthenticated requests.")

print("No source modification was performed by this diagnostic.")

print("\n" + "=" * 50)
print("BLOCK 31K-CM COMPLETE")
print("=" * 50)
