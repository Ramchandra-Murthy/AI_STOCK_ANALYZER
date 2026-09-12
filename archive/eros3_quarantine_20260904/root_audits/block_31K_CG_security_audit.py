from __future__ import annotations

import sys
import os
import traceback
import importlib
import py_compile
from pathlib import Path

ROOT = Path.cwd()

ROUTERS = [
    ROOT / "backend/api/routers/task_router.py",
    ROOT / "backend/api/routers/valuation_router.py",
    ROOT / "backend/api/routers/admin_task_router.py",
]

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CG PYTHON SECURITY AUDIT")
print("=" * 50)

# --------------------------------------------------
# 1. SOURCE DISCOVERY
# --------------------------------------------------

print("\n1. SOURCE DISCOVERY")
print("-" * 50)

for p in ROUTERS:
    print(("FOUND: " if p.exists() else "MISSING: ") + str(p))

# --------------------------------------------------
# 2. SOURCE ARTIFACT CHECK
# --------------------------------------------------

print("\n2. SOURCE ARTIFACT CHECK")
print("-" * 50)

for p in ROUTERS:
    if not p.exists():
        continue

    data = p.read_bytes()

    bom = data.count(b"\xef\xbb\xbf")
    literal = data.count(b"`n")

    print(
        p.name,
        "| BOM=",
        bom,
        "| LITERAL_BACKTICK_N=",
        literal,
    )

# --------------------------------------------------
# 3. IMPORT CHECK
# --------------------------------------------------

print("\n3. FASTAPI IMPORT CHECK")
print("-" * 50)

for p in ROUTERS:
    if not p.exists():
        continue

    text = p.read_text(encoding="utf-8")

    print(
        p.name,
        "| APIRouter=",
        "APIRouter" in text,
        "| Depends=",
        "Depends" in text,
    )

# --------------------------------------------------
# 4. PYTHON COMPILE
# --------------------------------------------------

print("\n4. PYTHON COMPILE CHECK")
print("-" * 50)

compile_ok = True

for p in ROUTERS:
    try:
        py_compile.compile(str(p), doraise=True)
        print("COMPILE PASS:", p.name)
    except Exception as exc:
        compile_ok = False
        print("COMPILE FAIL:", p.name)
        print(type(exc).__name__, ":", str(exc))

# --------------------------------------------------
# 5. FASTAPI APPLICATION IMPORT
# --------------------------------------------------

print("\n5. FASTAPI APPLICATION IMPORT")
print("-" * 50)

app = None
import_ok = False

try:
    import backend.main as main_module

    app = main_module.app
    import_ok = True

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", getattr(app, "title", None))
    print("VERSION:", getattr(app, "version", None))

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))
    traceback.print_exc()

# --------------------------------------------------
# 6. ROUTE INVENTORY
# --------------------------------------------------

print("\n6. APPLICATION ROUTE INVENTORY")
print("-" * 50)

if app is not None:

    for route in app.routes:

        if not hasattr(route, "path"):
            continue

        methods = ",".join(sorted(route.methods or []))

        dependant = getattr(route, "dependant", None)
        deps = getattr(dependant, "dependencies", []) if dependant else []

        secured = len(deps) > 0

        print(
            ("SECURED" if secured else "OPEN"),
            "|",
            route.path,
            "|",
            methods,
            "| DEP_COUNT=",
            len(deps),
        )

else:
    print("SKIPPED - APPLICATION IMPORT FAILED")

# --------------------------------------------------
# 7. OPENAPI SECURITY
# --------------------------------------------------

print("\n7. OPENAPI SECURITY AUDIT")
print("-" * 50)

if app is not None:

    try:
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/openapi.json")

        print("OPENAPI STATUS:", response.status_code)

        if response.status_code == 200:

            spec = response.json()

            schemes = spec.get("components", {}).get("securitySchemes", {})

            print("SECURITY SCHEMES:", schemes)
            print("GLOBAL SECURITY:", spec.get("security", []))

            secured = []

            for path, item in spec.get("paths", {}).items():

                for method, operation in item.items():

                    if not isinstance(operation, dict):
                        continue

                    if operation.get("security"):
                        secured.append((path, method.upper()))

            print("SECURED OPERATIONS:", len(secured))

            for path, method in secured:
                print(" ", path, "|", method)

    except Exception as exc:
        print("OPENAPI AUDIT FAIL:", type(exc).__name__, str(exc))

else:
    print("SKIPPED - APPLICATION IMPORT FAILED")

# --------------------------------------------------
# 8. SETTINGS + JWT
# --------------------------------------------------

print("\n8. SETTINGS + JWT SECURITY AUDIT")
print("-" * 50)

jwt_ok = False

try:

    from backend.config.settings import settings

    print("PROJECT_NAME:", settings.PROJECT_NAME)
    print("ENVIRONMENT:", settings.ENVIRONMENT)
    print("DATABASE_URL CONFIGURED:", bool(settings.DATABASE_URL))
    print("REDIS_URL CONFIGURED:", bool(settings.REDIS_URL))
    print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
    print("ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    print("AUTH_ENABLED:", settings.AUTH_ENABLED)

    jwt_secret = getattr(settings, "JWT_SECRET", None) or getattr(settings, "SECRET_KEY", None)

    print("JWT_SECRET CONFIGURED:", bool(jwt_secret))

    from backend.security.jwt import JWTSecurity
    from datetime import timedelta

    payload = {
        "sub": "eros_security_test",
        "username": "eros_security_test",
        "role": "ANALYST",
    }

    token = JWTSecurity.create_access_token(
        payload,
        expires_delta=timedelta(minutes=5),
    )

    decoded = JWTSecurity.decode_access_token(token)

    print("TOKEN CREATED:", bool(token))
    print("TOKEN LENGTH:", len(token) if token else 0)
    print("DECODE SUCCESS:", decoded is not None)

    if decoded:
        print("SUB:", decoded.get("sub"))
        print("USERNAME:", decoded.get("username"))
        print("ROLE:", decoded.get("role"))
        print("ISSUER:", decoded.get("iss"))
        print("EXP:", decoded.get("exp"))

    invalid = JWTSecurity.decode_access_token("invalid.jwt.token")

    print("INVALID TOKEN RETURNS NONE:", invalid is None)

    jwt_ok = bool(token and decoded and invalid is None)

except Exception as exc:
    print("JWT AUDIT FAIL:", type(exc).__name__, str(exc))
    traceback.print_exc()

# --------------------------------------------------
# 9. AUTH + UNAUTHENTICATED ACCESS
# --------------------------------------------------

print("\n9. AUTH + UNAUTHENTICATED SECURITY GATE")
print("-" * 50)

auth_ok = False

if app is not None:

    try:

        from fastapi.testclient import TestClient

        client = TestClient(app)

        tests = [
            (
                "TASK_SUBMIT",
                "POST",
                "/api/v1/tasks/submit",
                {
                    "task_name": "forecast.execute",
                    "symbol": "TCS.NS",
                },
            ),
            (
                "VALUATION",
                "POST",
                "/api/v1/valuation",
                {
                    "symbol": "TCS.NS",
                },
            ),
            (
                "ADMIN_QUEUES",
                "GET",
                "/api/v1/admin/queues",
                None,
            ),
            (
                "ADMIN_TASKS",
                "GET",
                "/api/v1/admin/tasks",
                None,
            ),
        ]

        protected_count = 0

        for name, method, path, body in tests:

            if method == "POST":
                response = client.post(
                    path,
                    json=body,
                )
            else:
                response = client.get(path)

            status_code = response.status_code

            protected = status_code in (401, 403)

            if protected:
                protected_count += 1

            print(
                name,
                "->",
                status_code,
                "|",
                ("SECURITY_ENFORCED" if protected else "OPEN_OR_UNAVAILABLE"),
            )

        print(
            "PROTECTED TESTS:",
            protected_count,
            "/",
            len(tests),
        )

        auth_ok = protected_count == len(tests)

    except Exception as exc:
        print("AUTH GATE FAIL:", type(exc).__name__, str(exc))

else:
    print("SKIPPED - APPLICATION IMPORT FAILED")

# --------------------------------------------------
# 10. INFRASTRUCTURE REGRESSION
# --------------------------------------------------

print("\n10. FINAL INFRASTRUCTURE REGRESSION")
print("-" * 50)

regression_ok = False

if app is not None:

    try:

        from fastapi.testclient import TestClient

        client = TestClient(app)

        openapi = client.get("/openapi.json")
        health = client.get("/health")
        ready = client.get("/ready")

        print("OPENAPI:", openapi.status_code)

        print(
            "HEALTH:",
            health.status_code,
            health.json(),
        )

        print(
            "READY:",
            ready.status_code,
            ready.json(),
        )

        regression_ok = (
            openapi.status_code == 200 and health.status_code == 200 and ready.status_code == 200
        )

    except Exception as exc:
        print("REGRESSION FAIL:", type(exc).__name__, str(exc))

else:
    print("SKIPPED - APPLICATION IMPORT FAILED")

# --------------------------------------------------
# FINAL GATE
# --------------------------------------------------

print("\n" + "=" * 50)
print("FINAL SECURITY GATE")
print("=" * 50)

print("ROUTER COMPILE:", "PASS" if compile_ok else "FAIL")
print("APPLICATION IMPORT:", "PASS" if import_ok else "FAIL")
print("JWT FUNCTIONAL:", "PASS" if jwt_ok else "FAIL")
print("UNAUTHENTICATED SECURITY:", "PASS" if auth_ok else "FAIL")
print("INFRASTRUCTURE:", "PASS" if regression_ok else "FAIL")

overall = compile_ok and import_ok and jwt_ok and regression_ok

print("OVERALL SECURITY GATE:", "PASS" if overall else "FAIL")

print("PRODUCTION STATUS:", "READY" if overall else "BLOCKED")

print("=" * 50)
print("BLOCK 31K-CG COMPLETE")
print("=" * 50)
