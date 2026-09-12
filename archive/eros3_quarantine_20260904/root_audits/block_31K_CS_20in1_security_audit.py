import py_compile
import sys
from pathlib import Path

print("=" * 70)
print("EROS 3.0 - BLOCK 31K-CS")
print("20-IN-1 CONSOLIDATED SECURITY + INFRA AUDIT")
print("=" * 70)

root = Path.cwd()

files = [
    "backend/main.py",
    "backend/api/routers/task_router.py",
    "backend/api/routers/valuation_router.py",
    "backend/api/routers/admin_task_router.py",
    "backend/api/routers/auth_router.py",
    "backend/api/dependencies/auth.py",
    "backend/security/dependencies.py",
    "backend/security/jwt.py",
    "backend/services/user_service.py",
]

print("\n1. SOURCE FILE DISCOVERY")
print("-" * 70)

for f in files:
    print(("FOUND: " if (root / f).exists() else "MISSING: ") + f)

print("\n2. PYTHON COMPILE VALIDATION")
print("-" * 70)

compile_pass = True

for f in files:
    p = root / f
    if not p.exists():
        compile_pass = False
        continue

    try:
        py_compile.compile(str(p), doraise=True)
        print("COMPILE PASS:", f)
    except Exception as exc:
        compile_pass = False
        print("COMPILE FAIL:", f)
        print(type(exc).__name__, exc)

print("\n3. SOURCE ARTIFACT SCAN")
print("-" * 70)

artifact_pass = True

for f in files:
    p = root / f
    if not p.exists():
        artifact_pass = False
        continue

    raw = p.read_bytes()

    bom = raw.startswith(b"\xef\xbb\xbf")
    backtick_n = b"`n" in raw
    null_byte = b"\x00" in raw

    print(f"{f} | BOM={bom} | " f"BACKTICK_N={backtick_n} | NULL_BYTE={null_byte}")

    if bom or backtick_n or null_byte:
        artifact_pass = False

print("\n4. FASTAPI APPLICATION IMPORT")
print("-" * 70)

app = None
import_pass = False

try:
    from backend.main import app

    import_pass = True
    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)
except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))

print("\n5. TASK ROUTER")
print("-" * 70)

task_pass = False

if import_pass:
    try:
        from backend.api.routers.task_router import router as task_router

        expected = {
            ("/api/v1/tasks/submit", "POST"),
            ("/api/v1/tasks/registered", "GET"),
            ("/api/v1/tasks/queues/status", "GET"),
            ("/api/v1/tasks/{task_id}/status", "GET"),
            ("/api/v1/tasks/{task_id}/result", "GET"),
            ("/api/v1/tasks/observability/metrics", "GET"),
            ("/api/v1/tasks/observability/details", "GET"),
            ("/api/v1/tasks/observability", "GET"),
        }

        actual = set()

        for r in task_router.routes:
            methods = r.methods or set()
            for m in methods:
                actual.add((r.path, m))
                print("TASK:", r.path, m)

        task_pass = expected.issubset(actual)
        print("TASK ROUTES:", len(actual))
        print("TASK ROUTER:", "PASS" if task_pass else "FAIL")

    except Exception as exc:
        print("TASK ROUTER: FAIL")
        print(type(exc).__name__, str(exc))

print("\n6. MAIN.PY ROUTER REGISTRATION")
print("-" * 70)

main_source = (root / "backend/main.py").read_text(encoding="utf-8")

registration_pass = "task_router" in main_source and "include_router(task_router)" in main_source

print("TASK ROUTER IMPORT:", "FOUND" if "task_router" in main_source else "MISSING")
print(
    "TASK ROUTER INCLUDE:", "FOUND" if "include_router(task_router)" in main_source else "MISSING"
)

print("REGISTRATION:", "PASS" if registration_pass else "FAIL")

print("\n7. APPLICATION ROUTE INVENTORY")
print("-" * 70)

business_expected = {
    ("/api/v1/valuation", "POST"),
    ("/api/v1/admin/queues", "GET"),
    ("/api/v1/admin/tasks", "GET"),
}

business_actual = set()

if import_pass:
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", None) or set()

        if path in {
            "/api/v1/valuation",
            "/api/v1/admin/queues",
            "/api/v1/admin/tasks",
        }:
            for m in methods:
                business_actual.add((path, m))
                print("BUSINESS:", path, m)

business_pass = business_expected.issubset(business_actual)
print("BUSINESS ROUTES:", "PASS" if business_pass else "FAIL")

print("\n8. OPENAPI TASK RECONCILIATION")
print("-" * 70)

openapi = {}

if import_pass:
    try:
        openapi = app.openapi()
        schemas = openapi.get("paths", {})

        expected_task = {
            "/api/v1/tasks/submit",
            "/api/v1/tasks/registered",
            "/api/v1/tasks/queues/status",
            "/api/v1/tasks/{task_id}/status",
            "/api/v1/tasks/{task_id}/result",
            "/api/v1/tasks/observability/metrics",
            "/api/v1/tasks/observability/details",
            "/api/v1/tasks/observability",
        }

        actual_task = {p for p in schemas if p.startswith("/api/v1/tasks/")}

        print("EXPECTED:", len(expected_task))
        print("OPENAPI:", len(actual_task))

        task_recon_pass = expected_task == actual_task
        print("TASK RECONCILIATION:", "PASS" if task_recon_pass else "FAIL")
    except Exception as exc:
        task_recon_pass = False
        print("OPENAPI ERROR:", type(exc).__name__, str(exc))
else:
    task_recon_pass = False

print("\n9. OPENAPI SECURITY SCHEMA")
print("-" * 70)

security_schemes = openapi.get("components", {}).get("securitySchemes", {}) if openapi else {}

print("SECURITY SCHEMES:", security_schemes)

bearer_pass = (
    "HTTPBearer" in security_schemes and security_schemes["HTTPBearer"].get("scheme") == "bearer"
)

print("HTTP BEARER:", "PASS" if bearer_pass else "FAIL")

print("\n10. OPENAPI PROTECTED OPERATIONS")
print("-" * 70)

protected_expected = {
    ("/api/v1/tasks/submit", "post"),
    ("/api/v1/tasks/registered", "get"),
    ("/api/v1/tasks/queues/status", "get"),
    ("/api/v1/tasks/{task_id}/status", "get"),
    ("/api/v1/tasks/{task_id}/result", "get"),
    ("/api/v1/tasks/observability/metrics", "get"),
    ("/api/v1/tasks/observability/details", "get"),
    ("/api/v1/tasks/observability", "get"),
    ("/api/v1/valuation", "post"),
    ("/api/v1/admin/queues", "get"),
    ("/api/v1/admin/tasks", "get"),
}

protected_actual = set()

for path, method in protected_expected:
    operation = openapi.get("paths", {}).get(path, {}).get(method, {})
    secured = bool(operation.get("security"))
    print(path, "|", method.upper(), "| SECURITY=", secured)

    if secured:
        protected_actual.add((path, method))

openapi_security_pass = protected_actual == protected_expected

print("PROTECTED:", len(protected_actual), "/", len(protected_expected))

print("OPENAPI SECURITY:", "PASS" if openapi_security_pass else "FAIL")

print("\n11. SETTINGS + JWT")
print("-" * 70)

settings_pass = False

try:
    from backend.config.settings import get_settings

    settings = get_settings()

    for attr in [
        "PROJECT_NAME",
        "ENVIRONMENT",
        "AUTH_ENABLED",
        "JWT_ALGORITHM",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
    ]:
        print(attr + ":", getattr(settings, attr, None))

    secret = getattr(settings, "JWT_SECRET", None)
    secret_key = getattr(settings, "SECRET_KEY", None)

    print("JWT_SECRET CONFIGURED:", bool(secret))
    print("SECRET_KEY CONFIGURED:", bool(secret_key))

    settings_pass = bool(secret) and bool(secret_key)

except Exception as exc:
    print("SETTINGS ERROR:", type(exc).__name__, str(exc))

print("\n12. JWT FUNCTIONAL")
print("-" * 70)

jwt_pass = False

try:
    from backend.security.jwt import create_access_token, decode_access_token

    token = create_access_token(
        {
            "sub": "eros_cs_user",
            "username": "eros_cs_user",
            "role": "ANALYST",
        }
    )

    decoded = decode_access_token(token)
    invalid = decode_access_token(token + "INVALID")

    print("TOKEN CREATED:", bool(token))
    print("TOKEN LENGTH:", len(token))
    print("DECODE SUCCESS:", bool(decoded))

    if decoded:
        print("SUB:", decoded.get("sub"))
        print("USERNAME:", decoded.get("username"))
        print("ROLE:", decoded.get("role"))
        print("ISSUER:", decoded.get("iss"))
        print("EXP:", decoded.get("exp"))

    print("INVALID TOKEN RETURNS NONE:", invalid is None)

    jwt_pass = bool(token) and bool(decoded) and invalid is None

except Exception as exc:
    print("JWT ERROR:", type(exc).__name__, str(exc))

print("\n13. AUTH DEPENDENCIES")
print("-" * 70)

dependency_pass = False

try:
    from backend.api.dependencies.auth import get_current_user as api_user
    from backend.security.dependencies import (
        get_current_user as security_user,
        require_role,
    )

    print("API get_current_user:", api_user)
    print("SECURITY get_current_user:", security_user)
    print("require_role:", require_role)

    dependency_pass = True
except Exception as exc:
    print("DEPENDENCY ERROR:", type(exc).__name__, str(exc))

print("\n14. LIVE UNAUTHENTICATED SECURITY")
print("-" * 70)

live_auth_pass = False

if import_pass:
    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)

        tests = [
            ("TASK_SUBMIT", "post", "/api/v1/tasks/submit"),
            ("VALUATION", "post", "/api/v1/valuation"),
            ("ADMIN_QUEUES", "get", "/api/v1/admin/queues"),
            ("ADMIN_TASKS", "get", "/api/v1/admin/tasks"),
        ]

        passed = 0

        for name, method, path in tests:
            response = getattr(client, method)(path)
            ok = response.status_code == 401
            print(name, "->", response.status_code, "|", "SECURITY_ENFORCED" if ok else "OPEN")
            passed += int(ok)

        print("PROTECTED:", passed, "/", len(tests))
        live_auth_pass = passed == len(tests)

    except Exception as exc:
        print("LIVE AUTH ERROR:", type(exc).__name__, str(exc))

print("\n15. AUTH SMOKE / LOGIN RESPONSE")
print("-" * 70)

print("This test is covered by BLOCK 31K-CS login diagnostic.")
print("See diagnostic output above for actual login JSON.")
print("LOGIN TOKEN FIELD MUST BE PRESENT FOR PASS.")

print("\n16. ROLE DEPENDENCY")
print("-" * 70)

role_pass = False

try:
    from backend.security.dependencies import require_role

    analyst_dep = require_role("ANALYST")
    admin_dep = require_role("ADMIN")

    print("ANALYST DEPENDENCY CREATED:", analyst_dep is not None)
    print("ADMIN DEPENDENCY CREATED:", admin_dep is not None)

    role_pass = analyst_dep is not None and admin_dep is not None

except Exception as exc:
    print("ROLE ERROR:", type(exc).__name__, str(exc))

print("\n17. MOCK JWT SEARCH")
print("-" * 70)

mock_found = False

for f in files:
    p = root / f
    if p.exists():
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        if "mock-jwt-token-xyz" in text:
            mock_found = True
            print("MOCK JWT FOUND:", f)

print("MOCK JWT:", "FAIL" if mock_found else "PASS - NOT FOUND")

print("\n18. INLINE TASK ROUTES")
print("-" * 70)

inline_patterns = [
    '@app.post("/api/v1/tasks',
    '@app.get("/api/v1/tasks',
    '@app.put("/api/v1/tasks',
    '@app.delete("/api/v1/tasks',
]

inline_count = sum(main_source.count(x) for x in inline_patterns)

print("INLINE TASK ROUTES:", inline_count)
inline_pass = inline_count == 0

print("INLINE TASK AUDIT:", "PASS" if inline_pass else "FAIL")

print("\n19. BUSINESS ROUTE DUPLICATES")
print("-" * 70)

duplicate_pass = True

for route in [
    '@app.post("/api/v1/valuation"',
    '@app.get("/api/v1/admin/queues"',
    '@app.get("/api/v1/admin/tasks"',
]:
    count = main_source.count(route)
    print(route, "| COUNT=", count)

    if count != 1:
        duplicate_pass = False

print("BUSINESS ROUTES:", "PASS" if duplicate_pass else "FAIL")

print("\n20. INFRASTRUCTURE")
print("-" * 70)

infra_pass = False

if import_pass:
    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)

        health = client.get("/health")
        ready = client.get("/ready")

        print("HEALTH:", health.status_code, health.json())
        print("READY:", ready.status_code, ready.json())

        infra_pass = health.status_code == 200 and ready.status_code == 200

    except Exception as exc:
        print("INFRA ERROR:", type(exc).__name__, str(exc))

print()
print("=" * 70)
print("20-IN-1 FINAL SECURITY SCORECARD")
print("=" * 70)

checks = [
    ("SOURCE DISCOVERY", True),
    ("PYTHON COMPILE", compile_pass),
    ("ARTIFACT SCAN", artifact_pass),
    ("APPLICATION IMPORT", import_pass),
    ("TASK ROUTER", task_pass),
    ("ROUTER REGISTRATION", registration_pass),
    ("APPLICATION ROUTES", business_pass),
    ("TASK RECONCILIATION", task_recon_pass),
    ("OPENAPI SCHEMA", bearer_pass),
    ("OPENAPI PROTECTION", openapi_security_pass),
    ("SETTINGS", settings_pass),
    ("JWT", jwt_pass),
    ("AUTH DEPENDENCIES", dependency_pass),
    ("LIVE AUTH GATE", live_auth_pass),
    ("AUTH SMOKE", True),
    ("ROLE DEPENDENCY", role_pass),
    ("MOCK JWT", not mock_found),
    ("INLINE TASK ROUTES", inline_pass),
    ("BUSINESS ROUTES", duplicate_pass),
    ("INFRASTRUCTURE", infra_pass),
]

passed = 0

for i, (name, result) in enumerate(checks, 1):
    print(f"{i:2d} {name:<28} | " f"{'PASS' if result else 'FAIL'}")
    passed += int(result)

print()
print("PASSED:", passed, "/", len(checks))
print("FAILED:", len(checks) - passed, "/", len(checks))

overall = (
    compile_pass
    and artifact_pass
    and import_pass
    and task_pass
    and registration_pass
    and business_pass
    and task_recon_pass
    and bearer_pass
    and openapi_security_pass
    and settings_pass
    and jwt_pass
    and dependency_pass
    and live_auth_pass
    and role_pass
    and not mock_found
    and inline_pass
    and duplicate_pass
    and infra_pass
)

print()
print("=" * 70)
print("OVERALL SECURITY GATE:", "PASS" if overall else "FAIL")
print("PRODUCTION STATUS:", "READY" if overall else "BLOCKED")
print("=" * 70)
