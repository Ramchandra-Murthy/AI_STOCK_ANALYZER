from pathlib import Path
import py_compile
import importlib
import json

ROOT = Path(".")
FILES = [
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

print("=" * 70)
print("EROS 3.0 - BLOCK 31K-CV")
print("20-IN-1 FRESH SECURITY + INFRASTRUCTURE BASELINE")
print("=" * 70)

# 1
print("\n1. SOURCE FILE DISCOVERY")
print("-" * 70)
for f in FILES:
    p = ROOT / f
    print(("FOUND: " if p.exists() else "MISSING: ") + f)

# 2
print("\n2. PYTHON COMPILE")
print("-" * 70)
compile_ok = True
for f in FILES:
    p = ROOT / f
    if not p.exists():
        compile_ok = False
        continue
    try:
        py_compile.compile(str(p), doraise=True)
        print("PASS:", f)
    except Exception as e:
        compile_ok = False
        print("FAIL:", f, type(e).__name__, str(e))

# 3
print("\n3. SOURCE ARTIFACT SCAN")
print("-" * 70)
artifact_ok = True
for f in FILES:
    p = ROOT / f
    if not p.exists():
        artifact_ok = False
        continue
    b = p.read_bytes()
    bom = b.startswith(b"\xef\xbb\xbf")
    backtick_n = b"`n" in b
    null_byte = b"\x00" in b
    print(
        f"{f} | BOM={bom} | BACKTICK_N={backtick_n} | NULL_BYTE={null_byte}"
    )
    if bom or backtick_n or null_byte:
        artifact_ok = False

# 4
print("\n4. FASTAPI APPLICATION IMPORT")
print("-" * 70)
app = None
import_ok = True
try:
    from backend.main import app
    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)
except Exception as e:
    import_ok = False
    print("APPLICATION IMPORT: FAIL")
    print(type(e).__name__ + ":", str(e))

# 5
print("\n5. TASK ROUTER")
print("-" * 70)
task_ok = True
try:
    from backend.api.routers.task_router import router as task_router
    expected_task = {
        ("/api/v1/tasks/submit", "POST"),
        ("/api/v1/tasks/registered", "GET"),
        ("/api/v1/tasks/queues/status", "GET"),
        ("/api/v1/tasks/{task_id}/status", "GET"),
        ("/api/v1/tasks/{task_id}/result", "GET"),
        ("/api/v1/tasks/observability/metrics", "GET"),
        ("/api/v1/tasks/observability/details", "GET"),
        ("/api/v1/tasks/observability", "GET"),
    }
    actual_task = set()
    for r in task_router.routes:
        methods = getattr(r, "methods", set()) or set()
        path = getattr(r, "path", None)
        for m in methods:
            actual_task.add((path, m))
            if path.startswith("/api/v1/tasks"):
                print("TASK:", path, m)
    task_ok = expected_task.issubset(actual_task)
    print("TASK ROUTES:", len([x for x in actual_task if x[0].startswith("/api/v1/tasks")]))
    print("TASK ROUTER:", "PASS" if task_ok else "FAIL")
except Exception as e:
    task_ok = False
    print("TASK ROUTER: FAIL", type(e).__name__, str(e))

# 6
print("\n6. MAIN.PY ROUTER REGISTRATION")
print("-" * 70)
main_text = (ROOT / "backend/main.py").read_text(encoding="utf-8")
registration_ok = (
    "from backend.api.routers.task_router import router as task_router" in main_text
    and "app.include_router(task_router)" in main_text
)
print("TASK ROUTER IMPORT:", "FOUND" if "task_router" in main_text else "MISSING")
print("TASK ROUTER INCLUDE:", "FOUND" if "app.include_router(task_router)" in main_text else "MISSING")
print("REGISTRATION:", "PASS" if registration_ok else "FAIL")

# 7
print("\n7. APPLICATION ROUTES")
print("-" * 70)
business_expected = {
    ("/api/v1/valuation", "POST"),
    ("/api/v1/admin/queues", "GET"),
    ("/api/v1/admin/tasks", "GET"),
}
if app:
    api_routes = set()
    for r in app.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", set()) or set()
        if path:
            for m in methods:
                api_routes.add((path, m))
    for item in sorted(business_expected):
        print(item[0], item[1], "|", "FOUND" if item in api_routes else "MISSING")
    business_ok = business_expected.issubset(api_routes)
else:
    business_ok = False
print("BUSINESS ROUTES:", "PASS" if business_ok else "FAIL")

# 8
print("\n8. TASK ROUTE RECONCILIATION")
print("-" * 70)
openapi = {}
if app:
    try:
        openapi = app.openapi()
    except Exception:
        openapi = {}
paths = openapi.get("paths", {})
openapi_task = set()
for path, item in paths.items():
    if path.startswith("/api/v1/tasks"):
        for method in item.keys():
            if method.lower() in {"get", "post", "put", "patch", "delete"}:
                openapi_task.add((path, method.upper()))
print("EXPECTED:", len(expected_task))
print("OPENAPI:", len(openapi_task))
task_reconcile_ok = expected_task == openapi_task
print("TASK RECONCILIATION:", "PASS" if task_reconcile_ok else "FAIL")

# 9
print("\n9. OPENAPI SECURITY SCHEMA")
print("-" * 70)
schemes = openapi.get("components", {}).get("securitySchemes", {})
print("SECURITY SCHEMES:", schemes)
bearer_ok = any(
    isinstance(v, dict)
    and v.get("type") == "http"
    and v.get("scheme") == "bearer"
    for v in schemes.values()
)
print("HTTP BEARER:", "PASS" if bearer_ok else "FAIL")

# 10
print("\n10. OPENAPI PROTECTED OPERATIONS")
print("-" * 70)
protected_expected = {
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
    ("/api/v1/tasks/queues/status", "GET"),
    ("/api/v1/tasks/{task_id}/status", "GET"),
    ("/api/v1/tasks/{task_id}/result", "GET"),
    ("/api/v1/tasks/observability/metrics", "GET"),
    ("/api/v1/tasks/observability/details", "GET"),
    ("/api/v1/tasks/observability", "GET"),
    ("/api/v1/valuation", "POST"),
    ("/api/v1/admin/queues", "GET"),
    ("/api/v1/admin/tasks", "GET"),
}
protected_actual = set()
for path, item in paths.items():
    for method, op in item.items():
        if method.lower() not in {"get", "post", "put", "patch", "delete"}:
            continue
        if path in {x[0] for x in protected_expected}:
            if op.get("security"):
                protected_actual.add((path, method.upper()))
            print(path, "|", method.upper(), "| SECURITY=", bool(op.get("security")))
openapi_security_ok = protected_actual == protected_expected
print("PROTECTED EXPECTED:", len(protected_expected), "/", len(protected_actual))

# 11
print("\n11. SETTINGS CONTRACT")
print("-" * 70)
settings_ok = False
try:
    from backend.config.settings import settings, get_settings
    s = get_settings()
    print("PROJECT_NAME:", s.PROJECT_NAME)
    print("ENVIRONMENT:", s.ENVIRONMENT)
    print("AUTH_ENABLED:", s.AUTH_ENABLED)
    print("JWT_ALGORITHM:", s.JWT_ALGORITHM)
    print("JWT_SECRET CONFIGURED:", bool(s.JWT_SECRET))
    print("DATABASE_URL CONFIGURED:", bool(s.DATABASE_URL))
    print("REDIS_URL CONFIGURED:", bool(s.REDIS_URL))
    settings_ok = True
except Exception as e:
    print("SETTINGS ERROR:", type(e).__name__, str(e))

# 12
print("\n12. JWT FUNCTIONAL")
print("-" * 70)
jwt_ok = False
try:
    from backend.security.jwt import create_access_token, decode_token
    token = create_access_token({
        "sub": "eros_cv_user",
        "username": "eros_cv_user",
        "role": "ANALYST",
    })
    decoded = decode_token(token)
    invalid = decode_token("invalid-token")
    print("TOKEN CREATED:", bool(token))
    print("TOKEN LENGTH:", len(token))
    print("DECODE SUCCESS:", bool(decoded))
    print("SUB:", decoded.get("sub") if decoded else None)
    print("ROLE:", decoded.get("role") if decoded else None)
    print("ISSUER:", decoded.get("iss") if decoded else None)
    print("INVALID TOKEN RETURNS NONE:", invalid is None)
    jwt_ok = bool(token) and bool(decoded) and invalid is None
except Exception as e:
    print("JWT ERROR:", type(e).__name__, str(e))

# 13
print("\n13. AUTH DEPENDENCIES")
print("-" * 70)
dependency_ok = False
try:
    from backend.api.dependencies.auth import get_current_user as api_get_current_user
    from backend.security.dependencies import (
        get_current_user as security_get_current_user,
        require_role,
    )
    print("API get_current_user:", api_get_current_user)
    print("SECURITY get_current_user:", security_get_current_user)
    print("require_role:", require_role)
    dependency_ok = True
except Exception as e:
    print("DEPENDENCY ERROR:", type(e).__name__, str(e))

# 14
print("\n14. LIVE UNAUTHENTICATED SECURITY")
print("-" * 70)
live_auth_ok = False
if app:
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        tests = [
            ("/api/v1/tasks/submit", "post", {}),
            ("/api/v1/valuation", "post", {"symbol": "RELIANCE.NS"}),
            ("/api/v1/admin/queues", "get", {}),
            ("/api/v1/admin/tasks", "get", {}),
        ]
        results = []
        for path, method, kwargs in tests:
            response = getattr(client, method)(path, **kwargs)
            print(path, "->", response.status_code)
            results.append(response.status_code == 401)
        live_auth_ok = all(results)
    except Exception as e:
        print("LIVE AUTH ERROR:", type(e).__name__, str(e))

# 15
print("\n15. AUTH ROUTER / LOGIN CONTRACT")
print("-" * 70)
auth_router_ok = False
login_contract_ok = False
try:
    from backend.api.routers.auth_router import router as auth_router
    print("AUTH ROUTER IMPORT: PASS")
    for r in auth_router.routes:
        print(
            getattr(r, "path", None),
            getattr(r, "methods", None),
            getattr(r, "name", None)
        )
    auth_router_ok = True

    if app:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        payload = {
            "email": "eros_cv_user@example.com",
            "password": "ErosCVPassword123!",
            "role": "VIEWER"
        }
        register = client.post("/api/v1/auth/register", json=payload)
        print("REGISTER STATUS:", register.status_code)
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": payload["email"],
                "password": payload["password"]
            }
        )
        print("LOGIN STATUS:", login.status_code)
        print("LOGIN CONTENT-TYPE:", login.headers.get("content-type"))
        try:
            body = login.json()
            print("LOGIN JSON KEYS:", sorted(body.keys()) if isinstance(body, dict) else type(body).__name__)
            print("ACCESS TOKEN PRESENT:", bool(body.get("access_token")) if isinstance(body, dict) else False)
            login_contract_ok = (
                login.status_code == 200
                and isinstance(body, dict)
                and bool(body.get("access_token"))
            )
        except Exception as e:
            print("LOGIN JSON ERROR:", type(e).__name__, str(e))
except Exception as e:
    print("AUTH/LOGIN ERROR:", type(e).__name__, str(e))

# 16
print("\n16. ROLE DEPENDENCY")
print("-" * 70)
role_ok = False
try:
    from backend.security.dependencies import require_role
    analyst_dep = require_role("ANALYST")
    admin_dep = require_role("ADMIN")
    print("ANALYST DEPENDENCY CREATED:", callable(analyst_dep))
    print("ADMIN DEPENDENCY CREATED:", callable(admin_dep))
    role_ok = callable(analyst_dep) and callable(admin_dep)
except Exception as e:
    print("ROLE ERROR:", type(e).__name__, str(e))

# 17
print("\n17. MOCK JWT SEARCH")
print("-" * 70)
mock_found = []
for f in FILES:
    p = ROOT / f
    if p.exists():
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "mock-jwt-token" in text.lower():
            mock_found.append(f)
print("MOCK JWT:", "FOUND: " + ", ".join(mock_found) if mock_found else "PASS - NOT FOUND")
mock_ok = not mock_found

# 18
print("\n18. INLINE TASK ROUTES")
print("-" * 70)
inline_patterns = [
    '@app.post("/api/v1/tasks',
    '@app.get("/api/v1/tasks',
]
inline_count = sum(main_text.count(x) for x in inline_patterns)
print("INLINE TASK ROUTES:", inline_count)
inline_ok = inline_count == 0

# 19
print("\n19. BUSINESS ROUTE DUPLICATES")
print("-" * 70)
duplicate_ok = True
for pattern in [
    '@app.post("/api/v1/valuation"',
    '@app.get("/api/v1/admin/queues"',
    '@app.get("/api/v1/admin/tasks"',
]:
    count = main_text.count(pattern)
    print(pattern, "| COUNT=", count)
    if count != 1:
        duplicate_ok = False
print("MAIN BUSINESS ROUTES:", "PASS" if duplicate_ok else "FAIL")

# 20
print("\n20. INFRASTRUCTURE")
print("-" * 70)
infra_ok = False
if app:
    try:
        from fastapi.testclient import TestClient
        client = TestClient(app)
        health = client.get("/health")
        ready = client.get("/ready")
        print("HEALTH:", health.status_code, health.json())
        print("READY:", ready.status_code, ready.json())
        infra_ok = health.status_code == 200 and ready.status_code == 200
    except Exception as e:
        print("INFRA ERROR:", type(e).__name__, str(e))

print("\n" + "=" * 70)
print("20-IN-1 FINAL SCORECARD")
print("=" * 70)

checks = [
    compile_ok,
    artifact_ok,
    import_ok,
    task_ok,
    registration_ok,
    business_ok,
    task_reconcile_ok,
    bearer_ok,
    openapi_security_ok,
    settings_ok,
    jwt_ok,
    dependency_ok,
    live_auth_ok,
    auth_router_ok,
    login_contract_ok,
    role_ok,
    mock_ok,
    inline_ok,
    duplicate_ok,
    infra_ok,
]

names = [
    "PYTHON COMPILE",
    "ARTIFACT SCAN",
    "APPLICATION IMPORT",
    "TASK ROUTER",
    "ROUTER REGISTRATION",
    "APPLICATION ROUTES",
    "TASK RECONCILIATION",
    "OPENAPI SCHEMA",
    "OPENAPI PROTECTION",
    "SETTINGS",
    "JWT",
    "AUTH DEPENDENCIES",
    "LIVE AUTH GATE",
    "AUTH ROUTER",
    "LOGIN CONTRACT",
    "ROLE DEPENDENCY",
    "MOCK JWT",
    "INLINE TASK ROUTES",
    "BUSINESS ROUTES",
    "INFRASTRUCTURE",
]

passed = 0
for i, (name, ok) in enumerate(zip(names, checks), 1):
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    print(f"{i:2d} {name:<28} | {status}")

print()
print("PASSED:", passed, "/ 20")
print("FAILED:", 20 - passed, "/ 20")

overall = passed == 20
print()
print("OVERALL SECURITY GATE:", "PASS" if overall else "FAIL")
print("PRODUCTION STATUS:", "READY" if overall else "BLOCKED")
print("=" * 70)
