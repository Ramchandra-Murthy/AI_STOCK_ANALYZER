from __future__ import annotations

import traceback
from datetime import timedelta

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CH")
print("10-IN-1 SECURITY VALIDATION")
print("=" * 50)

app = None
import_ok = False

# --------------------------------------------------
# 1. APPLICATION IMPORT
# --------------------------------------------------

print("\n1. APPLICATION IMPORT")
print("-" * 50)

try:
    import backend.main as m

    app = m.app
    import_ok = True

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))
    traceback.print_exc()

# --------------------------------------------------
# 2. ROUTE INVENTORY
# --------------------------------------------------

print("\n2. ROUTE INVENTORY")
print("-" * 50)

if app:

    for route in app.routes:

        if not hasattr(route, "path"):
            continue

        dep = getattr(route, "dependant", None)
        deps = getattr(dep, "dependencies", []) if dep else []

        print(
            ("SECURED" if deps else "OPEN"),
            "|",
            route.path,
            "|",
            ",".join(sorted(route.methods or [])),
            "| DEP_COUNT=",
            len(deps),
        )

# --------------------------------------------------
# 3. MAIN DUPLICATE ROUTE AUDIT
# --------------------------------------------------

print("\n3. MAIN.PY DUPLICATE ROUTE AUDIT")
print("-" * 50)

from pathlib import Path

main_text = Path("backend/main.py").read_text(
    encoding="utf-8"
)

for route in [
    '@app.post("/api/v1/valuation"',
    '@app.get("/api/v1/admin/queues"',
    '@app.get("/api/v1/admin/tasks"',
]:

    count = main_text.count(route)

    print(route, "| COUNT=", count)

# --------------------------------------------------
# 4. MOCK TOKEN AUDIT
# --------------------------------------------------

print("\n4. MOCK JWT AUDIT")
print("-" * 50)

mock_found = "mock-jwt-token-xyz" in main_text

print(
    "MOCK JWT TOKEN:",
    "FOUND" if mock_found else "NOT FOUND"
)

# --------------------------------------------------
# 5. OPENAPI
# --------------------------------------------------

print("\n5. OPENAPI SECURITY")
print("-" * 50)

openapi = None

if app:

    from fastapi.testclient import TestClient

    client = TestClient(app)

    openapi = client.get("/openapi.json")

    print("OPENAPI:", openapi.status_code)

    if openapi.status_code == 200:

        spec = openapi.json()

        print(
            "SECURITY SCHEMES:",
            spec.get("components", {}).get(
                "securitySchemes", {}
            )
        )

        secured = []

        for path, item in spec.get("paths", {}).items():

            for method, operation in item.items():

                if (
                    isinstance(operation, dict)
                    and operation.get("security")
                ):
                    secured.append(
                        (path, method.upper())
                    )

        print(
            "SECURED OPERATIONS:",
            len(secured)
        )

        for path, method in secured:
            print(" ", path, "|", method)

# --------------------------------------------------
# 6. SETTINGS
# --------------------------------------------------

print("\n6. SECURITY SETTINGS")
print("-" * 50)

from backend.config.settings import settings

print("ENVIRONMENT:", settings.ENVIRONMENT)
print("AUTH_ENABLED:", settings.AUTH_ENABLED)
print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
print(
    "ACCESS_TOKEN_EXPIRE_MINUTES:",
    settings.ACCESS_TOKEN_EXPIRE_MINUTES
)

secret = (
    getattr(settings, "JWT_SECRET", None)
    or getattr(settings, "SECRET_KEY", None)
)

print(
    "JWT_SECRET CONFIGURED:",
    bool(secret)
)

# --------------------------------------------------
# 7. JWT FUNCTIONAL
# --------------------------------------------------

print("\n7. JWT FUNCTIONAL TEST")
print("-" * 50)

jwt_ok = False

try:

    from backend.security.jwt import JWTSecurity

    payload = {
        "sub": "eros_security_test",
        "username": "eros_security_test",
        "role": "ANALYST",
    }

    token = JWTSecurity.create_access_token(
        payload,
        expires_delta=timedelta(minutes=5)
    )

    decoded = JWTSecurity.decode_access_token(token)

    invalid = JWTSecurity.decode_access_token(
        "invalid.jwt.token"
    )

    print("TOKEN CREATED:", bool(token))
    print("DECODE SUCCESS:", decoded is not None)

    if decoded:
        print("SUB:", decoded.get("sub"))
        print("ROLE:", decoded.get("role"))
        print("ISSUER:", decoded.get("iss"))

    print(
        "INVALID TOKEN RETURNS NONE:",
        invalid is None
    )

    jwt_ok = (
        bool(token)
        and decoded is not None
        and invalid is None
    )

except Exception as exc:
    print("JWT FAIL:", type(exc).__name__, str(exc))

# --------------------------------------------------
# 8. UNAUTHENTICATED SECURITY GATE
# --------------------------------------------------

print("\n8. UNAUTHENTICATED ACCESS GATE")
print("-" * 50)

auth_tests = [
    (
        "TASK_SUBMIT",
        "POST",
        "/api/v1/tasks/submit",
        {
            "task_name": "forecast.execute",
            "symbol": "TCS.NS"
        }
    ),
    (
        "VALUATION",
        "POST",
        "/api/v1/valuation",
        {
            "symbol": "TCS.NS"
        }
    ),
    (
        "ADMIN_QUEUES",
        "GET",
        "/api/v1/admin/queues",
        None
    ),
    (
        "ADMIN_TASKS",
        "GET",
        "/api/v1/admin/tasks",
        None
    ),
]

protected = 0

if app:

    for name, method, path, body in auth_tests:

        if method == "POST":
            r = client.post(path, json=body)
        else:
            r = client.get(path)

        secure = r.status_code in (401, 403)

        if secure:
            protected += 1

        print(
            name,
            "->",
            r.status_code,
            "|",
            (
                "SECURITY_ENFORCED"
                if secure
                else "OPEN"
            )
        )

auth_ok = protected == len(auth_tests)

print(
    "PROTECTED:",
    protected,
    "/",
    len(auth_tests)
)

print(
    "AUTH GATE:",
    "PASS" if auth_ok else "FAIL"
)

# --------------------------------------------------
# 9. HEALTH / READY
# --------------------------------------------------

print("\n9. INFRASTRUCTURE REGRESSION")
print("-" * 50)

infra_ok = False

if app:

    health = client.get("/health")
    ready = client.get("/ready")

    print(
        "HEALTH:",
        health.status_code,
        health.json()
    )

    print(
        "READY:",
        ready.status_code,
        ready.json()
    )

    infra_ok = (
        health.status_code == 200
        and ready.status_code == 200
    )

# --------------------------------------------------
# 10. FINAL GATE
# --------------------------------------------------

print("\n10. FINAL SECURITY GATE")
print("-" * 50)

print(
    "APPLICATION IMPORT:",
    "PASS" if import_ok else "FAIL"
)

print(
    "JWT:",
    "PASS" if jwt_ok else "FAIL"
)

print(
    "UNAUTHENTICATED SECURITY:",
    "PASS" if auth_ok else "FAIL"
)

print(
    "INFRASTRUCTURE:",
    "PASS" if infra_ok else "FAIL"
)

print(
    "MOCK JWT:",
    "FAIL" if mock_found else "PASS"
)

overall = (
    import_ok
    and jwt_ok
    and auth_ok
    and infra_ok
    and not mock_found
)

print(
    "OVERALL SECURITY GATE:",
    "PASS" if overall else "FAIL"
)

print(
    "PRODUCTION STATUS:",
    "READY" if overall else "BLOCKED"
)

print("=" * 50)
print("BLOCK 31K-CH COMPLETE")
print("=" * 50)
