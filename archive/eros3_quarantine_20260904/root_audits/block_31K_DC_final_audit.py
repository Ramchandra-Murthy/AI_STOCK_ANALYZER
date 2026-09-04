from __future__ import annotations

import os
import re
import sys
import traceback
from pathlib import Path

ROOT = Path.cwd()

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

EXPECTED_TASK_ROUTES = [
    ("/api/v1/tasks/submit", "POST"),
    ("/api/v1/tasks/registered", "GET"),
    ("/api/v1/tasks/queues/status", "GET"),
    ("/api/v1/tasks/{task_id}/status", "GET"),
    ("/api/v1/tasks/{task_id}/result", "GET"),
    ("/api/v1/tasks/observability/metrics", "GET"),
    ("/api/v1/tasks/observability/details", "GET"),
    ("/api/v1/tasks/observability", "GET"),
]

PASS = 0
FAIL = 0
RESULTS = []

def section(n, title):
    print()
    print("=" * 70)
    print(f"{n}. {title}")
    print("-" * 70)

def result(name, ok):
    global PASS, FAIL
    status = "PASS" if ok else "FAIL"
    RESULTS.append((name, ok))
    if ok:
        PASS += 1
    else:
        FAIL += 1
    print(f"{name}: {status}")
    return ok

print("=" * 70)
print("EROS 3.0 - BLOCK 31K-DC")
print("20-IN-1 FINAL SECURITY + INFRASTRUCTURE REGRESSION AUDIT")
print("=" * 70)

# ----------------------------------------------------------------------
section(1, "SOURCE FILE DISCOVERY")
all_found = True
for f in FILES:
    exists = (ROOT / f).exists()
    print(f"{'FOUND' if exists else 'MISSING'}: {f}")
    all_found &= exists
result("SOURCE DISCOVERY", all_found)

# ----------------------------------------------------------------------
section(2, "PYTHON COMPILE")
compile_ok = True
for f in FILES:
    p = ROOT / f
    if not p.exists():
        compile_ok = False
        continue
    import py_compile
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"PASS: {f}")
    except Exception as exc:
        compile_ok = False
        print(f"FAIL: {f} -> {exc}")
result("PYTHON COMPILE", compile_ok)

# ----------------------------------------------------------------------
section(3, "SOURCE ARTIFACT SCAN")
artifact_ok = True
for f in FILES:
    p = ROOT / f
    if not p.exists():
        artifact_ok = False
        continue

    data = p.read_bytes()
    bom = data.startswith(b"\xef\xbb\xbf")
    backtick_n = b"`n" in data
    null_byte = b"\x00" in data

    print(
        f"{f} | BOM={bom} | "
        f"BACKTICK_N={backtick_n} | NULL_BYTE={null_byte}"
    )

    if bom or backtick_n or null_byte:
        artifact_ok = False

result("ARTIFACT SCAN", artifact_ok)

# ----------------------------------------------------------------------
section(4, "FASTAPI APPLICATION IMPORT")
app = None
app_import_ok = False

try:
    from backend.main import app
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)
    app_import_ok = True
except Exception as exc:
    print("IMPORT ERROR:", repr(exc))
    traceback.print_exc()

result("APPLICATION IMPORT", app_import_ok)

# ----------------------------------------------------------------------
section(5, "TASK ROUTER")
task_router_ok = False

try:
    from backend.api.routers.task_router import router as task_router

    actual = []
    for r in task_router.routes:
        path = getattr(r, "path", None)
        methods = getattr(r, "methods", set())
        for method in sorted(methods):
            if method in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                actual.append((path, method))
                print(f"TASK: {path} {method}")

    expected_set = set(EXPECTED_TASK_ROUTES)
    actual_set = set(actual)

    print("EXPECTED:", len(expected_set))
    print("ACTUAL:", len(actual_set))

    task_router_ok = expected_set.issubset(actual_set)

except Exception as exc:
    print("TASK ROUTER ERROR:", repr(exc))

result("TASK ROUTER", task_router_ok)

# ----------------------------------------------------------------------
section(6, "MAIN.PY ROUTER REGISTRATION")
registration_ok = False

try:
    main_text = (ROOT / "backend/main.py").read_text(encoding="utf-8")

    has_task_import = (
        "from backend.api.routers.task_router import router as task_router"
        in main_text
    )

    has_task_include = "app.include_router(task_router)" in main_text

    has_auth_import = (
        "from backend.api.routers.auth_router import router as auth_router"
        in main_text
    )

    has_auth_include = "app.include_router(auth_router)" in main_text

    print("TASK ROUTER IMPORT:", has_task_import)
    print("TASK ROUTER INCLUDE:", has_task_include)
    print("AUTH ROUTER IMPORT:", has_auth_import)
    print("AUTH ROUTER INCLUDE:", has_auth_include)

    registration_ok = (
        has_task_import
        and has_task_include
        and has_auth_import
        and has_auth_include
    )

except Exception as exc:
    print("REGISTRATION ERROR:", repr(exc))

result("ROUTER REGISTRATION", registration_ok)

# ----------------------------------------------------------------------
section(7, "APPLICATION ROUTES")
application_routes_ok = False

try:
    paths = {
        (getattr(r, "path", None), method)
        for r in app.routes
        for method in getattr(r, "methods", set())
    }

    required = {
        ("/api/v1/valuation", "POST"),
        ("/api/v1/admin/queues", "GET"),
        ("/api/v1/admin/tasks", "GET"),
        ("/api/v1/auth/register", "POST"),
        ("/api/v1/auth/login", "POST"),
    }

    for path, method in sorted(required):
        found = (path, method) in paths
        print(f"{path} {method} | {'FOUND' if found else 'MISSING'}")
        application_routes_ok &= found

except Exception as exc:
    print("ROUTE ERROR:", repr(exc))

result("APPLICATION ROUTES", application_routes_ok)

# ----------------------------------------------------------------------
section(8, "TASK ROUTE RECONCILIATION")
reconciliation_ok = False

try:
    openapi = app.openapi()
    task_paths = set()

    for path, item in openapi.get("paths", {}).items():
        for method in item.keys():
            if method.upper() in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                if path.startswith("/api/v1/tasks/"):
                    task_paths.add((path, method.upper()))

    expected = set(EXPECTED_TASK_ROUTES)

    print("EXPECTED:", len(expected))
    print("OPENAPI:", len(task_paths))
    reconciliation_ok = expected == task_paths

except Exception as exc:
    print("OPENAPI ERROR:", repr(exc))

result("TASK RECONCILIATION", reconciliation_ok)

# ----------------------------------------------------------------------
section(9, "OPENAPI SECURITY SCHEMA")
openapi_security_ok = False

try:
    schemas = app.openapi().get("components", {}).get("securitySchemes", {})
    print("SECURITY SCHEMES:", schemas)

    openapi_security_ok = any(
        v.get("type") == "http" and v.get("scheme") == "bearer"
        for v in schemas.values()
    )

except Exception as exc:
    print("SECURITY SCHEMA ERROR:", repr(exc))

result("OPENAPI SCHEMA", openapi_security_ok)

# ----------------------------------------------------------------------
section(10, "OPENAPI PROTECTED OPERATIONS")
protected_ok = False

try:
    openapi = app.openapi()
    paths = openapi.get("paths", {})

    expected_protected = [
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
    ]

    protected_count = 0

    for path, method in expected_protected:
        op = paths.get(path, {}).get(method, {})
        secure = bool(op.get("security"))
        print(f"{path} | {method.upper()} | SECURITY={secure}")
        if secure:
            protected_count += 1

    print("PROTECTED:", protected_count, "/", len(expected_protected))
    protected_ok = protected_count == len(expected_protected)

except Exception as exc:
    print("PROTECTION ERROR:", repr(exc))

result("OPENAPI PROTECTION", protected_ok)

# ----------------------------------------------------------------------
section(11, "SETTINGS CONTRACT")
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

    settings_ok = (
        bool(s.PROJECT_NAME)
        and bool(s.ENVIRONMENT)
        and bool(s.AUTH_ENABLED)
        and bool(s.JWT_ALGORITHM)
        and bool(s.JWT_SECRET)
        and bool(s.DATABASE_URL)
        and bool(s.REDIS_URL)
    )

except Exception as exc:
    print("SETTINGS ERROR:", repr(exc))

result("SETTINGS", settings_ok)

# ----------------------------------------------------------------------
section(12, "JWT FUNCTIONAL")
jwt_ok = False

try:
    from backend.security.jwt import (
        create_access_token,
        decode_token,
    )

    token = create_access_token({
        "sub": "eros_dc_user",
        "username": "eros_dc_user",
        "role": "ANALYST",
    })

    print("TOKEN CREATED:", bool(token))
    print("TOKEN LENGTH:", len(token))

    decoded = decode_token(token)

    print("DECODE SUCCESS:", bool(decoded))

    if decoded:
        print("SUB:", decoded.get("sub"))
        print("ROLE:", decoded.get("role"))
        print("ISSUER:", decoded.get("iss"))

    invalid = decode_token("invalid.jwt.token")
    print("INVALID TOKEN RETURNS NONE:", invalid is None)

    jwt_ok = (
        bool(token)
        and bool(decoded)
        and decoded.get("sub") == "eros_dc_user"
        and decoded.get("role") == "ANALYST"
        and decoded.get("iss") == "eros-enterprise-platform"
        and invalid is None
    )

except Exception as exc:
    print("JWT ERROR:", repr(exc))

result("JWT", jwt_ok)

# ----------------------------------------------------------------------
section(13, "AUTH DEPENDENCIES")
auth_dependencies_ok = False

try:
    from backend.api.dependencies.auth import get_current_user
    from backend.security.dependencies import require_role

    print("API get_current_user:", get_current_user)
    print("require_role:", require_role)

    admin_dep = require_role("ADMIN")
    analyst_dep = require_role("ANALYST")

    print("ADMIN DEPENDENCY CREATED:", callable(admin_dep))
    print("ANALYST DEPENDENCY CREATED:", callable(analyst_dep))

    auth_dependencies_ok = (
        callable(get_current_user)
        and callable(require_role)
        and callable(admin_dep)
        and callable(analyst_dep)
    )

except Exception as exc:
    print("AUTH DEPENDENCY ERROR:", repr(exc))

result("AUTH DEPENDENCIES", auth_dependencies_ok)

# ----------------------------------------------------------------------
section(14, "LIVE UNAUTHENTICATED SECURITY")
live_auth_ok = False

try:
    from fastapi.testclient import TestClient

    client = TestClient(app)

    checks = [
        ("/api/v1/tasks/submit", {"symbol": "RELIANCE.NS"}),
        ("/api/v1/valuation", {
            "symbol": "RELIANCE.NS",
            "eps": 100,
            "growth_rate": 0.10,
            "discount_rate": 0.12,
            "current_price": 2500
        }),
    ]

    statuses = []

    for path, payload in checks:
        try:
            r = client.post(path, json=payload)
            print(f"{path} -> {r.status_code}")
            statuses.append(r.status_code == 401)
        except Exception as exc:
            print(f"{path} -> TEST ERROR: {exc}")
            statuses.append(False)

    for path in ["/api/v1/admin/queues", "/api/v1/admin/tasks"]:
        try:
            r = client.get(path)
            print(f"{path} -> {r.status_code}")
            statuses.append(r.status_code == 401)
        except Exception as exc:
            print(f"{path} -> TEST ERROR: {exc}")
            statuses.append(False)

    live_auth_ok = all(statuses)

except Exception as exc:
    print("LIVE AUTH ERROR:", repr(exc))

result("LIVE AUTH GATE", live_auth_ok)

# ----------------------------------------------------------------------
section(15, "AUTH ROUTER + LOGIN CONTRACT")
login_contract_ok = False

try:
    from backend.api.routers.auth_router import router as auth_router

    auth_paths = {
        (r.path, next(iter(r.methods)))
        for r in auth_router.routes
        if getattr(r, "path", None)
    }

    print("AUTH ROUTER PATHS:", sorted(auth_paths))

    client = TestClient(app)

    username = "dc_verify_user"
    email = "dc_verify_user@example.com"
    password = "StrongPass123!"

    register_payload = {
        "username": username,
        "email": email,
        "password": password,
        "role": "VIEWER",
    }

    rr = client.post("/api/v1/auth/register", json=register_payload)
    print("REGISTER STATUS:", rr.status_code)

    # If the user already exists, login can still validate the contract.
    lr = client.post(
        "/api/v1/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    print("LOGIN STATUS:", lr.status_code)
    print("LOGIN CONTENT-TYPE:", lr.headers.get("content-type"))

    try:
        body = lr.json()
    except Exception:
        body = {}

    print("LOGIN JSON KEYS:", sorted(body.keys()) if isinstance(body, dict) else [])
    print("ACCESS TOKEN PRESENT:", bool(body.get("access_token")) if isinstance(body, dict) else False)
    print("TOKEN TYPE:", body.get("token_type") if isinstance(body, dict) else None)
    print("EXPIRES IN:", body.get("expires_in") if isinstance(body, dict) else None)
    print("USER PRESENT:", bool(body.get("user")) if isinstance(body, dict) else False)

    login_contract_ok = (
        lr.status_code == 200
        and isinstance(body, dict)
        and bool(body.get("access_token"))
        and body.get("token_type") == "bearer"
        and isinstance(body.get("expires_in"), int)
        and isinstance(body.get("user"), dict)
    )

except Exception as exc:
    print("AUTH ROUTER ERROR:", repr(exc))

result("AUTH ROUTER / LOGIN", login_contract_ok)

# ----------------------------------------------------------------------
section(16, "ROLE DEPENDENCY")
role_ok = False

try:
    from backend.security.dependencies import require_role

    analyst = require_role("ANALYST")
    admin = require_role("ADMIN")

    print("ANALYST DEPENDENCY CREATED:", callable(analyst))
    print("ADMIN DEPENDENCY CREATED:", callable(admin))

    role_ok = callable(analyst) and callable(admin)

except Exception as exc:
    print("ROLE ERROR:", repr(exc))

result("ROLE DEPENDENCY", role_ok)

# ----------------------------------------------------------------------
section(17, "MOCK JWT SEARCH")
mock_jwt_ok = True

for f in FILES:
    p = ROOT / f
    if not p.exists():
        continue

    text = p.read_text(encoding="utf-8", errors="ignore")

    suspicious = (
        "mock.jwt" in text.lower()
        or "fake.jwt" in text.lower()
        or "eyJhbGciOiJub25l" in text
    )

    if suspicious:
        print("MOCK JWT FOUND:", f)
        mock_jwt_ok = False

print("MOCK JWT:", "PASS - NOT FOUND" if mock_jwt_ok else "FAIL")

result("MOCK JWT", mock_jwt_ok)

# ----------------------------------------------------------------------
section(18, "INLINE TASK ROUTES")
inline_task_ok = False

try:
    main_text = (ROOT / "backend/main.py").read_text(
        encoding="utf-8",
        errors="ignore"
    )

    patterns = [
        r'@app\.(get|post|put|delete|patch)\("/api/v1/tasks',
    ]

    count = sum(
        len(re.findall(pattern, main_text, flags=re.I))
        for pattern in patterns
    )

    print("INLINE TASK ROUTES:", count)
    inline_task_ok = count == 0

except Exception as exc:
    print("INLINE TASK ERROR:", repr(exc))

result("INLINE TASK ROUTES", inline_task_ok)

# ----------------------------------------------------------------------
section(19, "BUSINESS ROUTE DUPLICATES")
duplicate_ok = False

try:
    main_text = (ROOT / "backend/main.py").read_text(
        encoding="utf-8",
        errors="ignore"
    )

    targets = [
        '@app.post("/api/v1/valuation"',
        '@app.get("/api/v1/admin/queues"',
        '@app.get("/api/v1/admin/tasks"',
        '@app.post("/api/v1/auth/register"',
        '@app.post("/api/v1/auth/login"',
    ]

    duplicate_ok = True

    for target in targets:
        count = main_text.count(target)
        print(f"{target} | COUNT={count}")

        # Auth routes should now be zero in main.py.
        if "auth/" in target:
            if count != 0:
                duplicate_ok = False
        else:
            if count > 1:
                duplicate_ok = False

except Exception as exc:
    print("DUPLICATE ERROR:", repr(exc))

result("BUSINESS ROUTES", duplicate_ok)

# ----------------------------------------------------------------------
section(20, "INFRASTRUCTURE")
infra_ok = False

try:
    from fastapi.testclient import TestClient

    client = TestClient(app)

    h = client.get("/health")
    rd = client.get("/ready")

    print("HEALTH:", h.status_code, h.json())
    print("READY:", rd.status_code, rd.json())

    health_body = h.json()
    ready_body = rd.json()

    infra_ok = (
        h.status_code == 200
        and rd.status_code == 200
        and health_body.get("status") == "healthy"
        and ready_body.get("status") == "ready"
        and ready_body.get("database") == "connected"
        and ready_body.get("redis") == "connected"
    )

except Exception as exc:
    print("INFRASTRUCTURE ERROR:", repr(exc))

result("INFRASTRUCTURE", infra_ok)

# ----------------------------------------------------------------------
print()
print("=" * 70)
print("20-IN-1 FINAL SECURITY SCORECARD")
print("=" * 70)

for i, (name, ok) in enumerate(RESULTS, 1):
    print(f"{i:2d} {name:<30} | {'PASS' if ok else 'FAIL'}")

print()
print("PASSED:", PASS, "/ 20")
print("FAILED:", FAIL, "/ 20")
print()

if FAIL == 0:
    print("=" * 70)
    print("OVERALL SECURITY GATE: PASS")
    print("PRODUCTION STATUS: READY FOR NEXT VALIDATION")
    print("=" * 70)
else:
    print("=" * 70)
    print("OVERALL SECURITY GATE: FAIL")
    print("PRODUCTION STATUS: BLOCKED")
    print("=" * 70)

print()
print("BLOCK 31K-DC COMPLETE")
