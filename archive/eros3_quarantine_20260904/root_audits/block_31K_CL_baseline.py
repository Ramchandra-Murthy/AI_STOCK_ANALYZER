from pathlib import Path
import py_compile

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CL PYTHON BASELINE")
print("=" * 50)

files = [
    "backend/main.py",
    "backend/api/routers/task_router.py",
    "backend/api/routers/valuation_router.py",
    "backend/api/routers/admin_task_router.py",
    "backend/api/routers/auth_router.py",
    "backend/security/dependencies.py",
    "backend/security/jwt.py",
    "backend/services/user_service.py",
]

print("\n1. PYTHON COMPILE BASELINE")
print("-" * 50)

compile_ok = True

for f in files:
    path = Path(f)
    try:
        py_compile.compile(str(path), doraise=True)
        print("PASS:", f)
    except Exception as exc:
        compile_ok = False
        print("FAIL:", f)
        print(type(exc).__name__, str(exc))

print("\n2. FASTAPI APPLICATION IMPORT")
print("-" * 50)

import_ok = False

try:
    import backend.main as m

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(m.app).__name__)
    print("TITLE:", m.app.title)
    print("VERSION:", m.app.version)

    import_ok = True

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__, str(exc))

if import_ok:
    from fastapi.testclient import TestClient
    from backend.config.settings import settings

    client = TestClient(m.app)

    print("\n3. ROUTE SECURITY BASELINE")
    print("-" * 50)

    protected = {
        "/api/v1/tasks/submit": "POST",
        "/api/v1/valuation": "POST",
        "/api/v1/admin/queues": "GET",
        "/api/v1/admin/tasks": "GET",
    }

    routes = {
        (r.path, method.upper())
        for r in m.app.routes
        if hasattr(r, "methods")
        for method in (r.methods or [])
    }

    route_ok = True

    for path, method in protected.items():
        exists = (path, method) in routes
        print(
            path,
            "|",
            method,
            "|",
            "FOUND" if exists else "MISSING"
        )
        if not exists:
            route_ok = False

    print("\n4. OPENAPI SECURITY BASELINE")
    print("-" * 50)

    response = client.get("/openapi.json")
    print("OPENAPI:", response.status_code)

    openapi_ok = response.status_code == 200

    if openapi_ok:
        schema = response.json()
        schemes = schema.get("components", {}).get("securitySchemes", {})
        print("SECURITY SCHEMES:", schemes)

        secured = []

        for path, item in schema.get("paths", {}).items():
            for method, operation in item.items():
                if isinstance(operation, dict) and operation.get("security"):
                    secured.append((path, method.upper()))

        print("SECURED OPERATIONS:", len(secured))

        for path, method in secured:
            print(" ", path, "|", method)

        required_security = [
            ("/api/v1/tasks/submit", "POST"),
            ("/api/v1/valuation", "POST"),
            ("/api/v1/admin/queues", "GET"),
            ("/api/v1/admin/tasks", "GET"),
        ]

        security_ok = all(
            item in secured for item in required_security
        )
    else:
        security_ok = False

    print("\n5. JWT SETTINGS BASELINE")
    print("-" * 50)

    print("PROJECT_NAME:", settings.PROJECT_NAME)
    print("ENVIRONMENT:", settings.ENVIRONMENT)
    print("AUTH_ENABLED:", settings.AUTH_ENABLED)
    print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
    print(
        "ACCESS_TOKEN_EXPIRE_MINUTES:",
        settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    print("JWT_SECRET CONFIGURED:", bool(settings.JWT_SECRET))
    print("DATABASE_URL CONFIGURED:", bool(settings.DATABASE_URL))
    print("REDIS_URL CONFIGURED:", bool(settings.REDIS_URL))

    settings_ok = all([
        bool(settings.PROJECT_NAME),
        settings.AUTH_ENABLED is True,
        bool(settings.JWT_ALGORITHM),
        settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0,
        bool(settings.JWT_SECRET),
        bool(settings.DATABASE_URL),
        bool(settings.REDIS_URL),
    ])

    print("\n6. JWT FUNCTIONAL BASELINE")
    print("-" * 50)

    try:
        from datetime import timedelta
        from backend.security.jwt import JWTSecurity

        payload = {
            "sub": "eros_baseline_user",
            "username": "eros_baseline_user",
            "role": "ANALYST",
        }

        token = JWTSecurity.create_access_token(
            payload,
            expires_delta=timedelta(minutes=60),
        )

        decoded = JWTSecurity.decode_access_token(token)

        jwt_ok = (
            bool(token)
            and decoded is not None
            and decoded.get("sub") == "eros_baseline_user"
            and decoded.get("username") == "eros_baseline_user"
            and decoded.get("role") == "ANALYST"
        )

        print("TOKEN CREATED:", bool(token))
        print("DECODE SUCCESS:", decoded is not None)
        print("SUB:", decoded.get("sub") if decoded else None)
        print("USERNAME:", decoded.get("username") if decoded else None)
        print("ROLE:", decoded.get("role") if decoded else None)
        print("ISSUER:", decoded.get("iss") if decoded else None)
        print("JWT BASELINE:", "PASS" if jwt_ok else "FAIL")

    except Exception as exc:
        jwt_ok = False
        print("JWT BASELINE: FAIL")
        print(type(exc).__name__, str(exc))

    print("\n7. UNAUTHENTICATED ACCESS BASELINE")
    print("-" * 50)

    access_tests = [
        ("/api/v1/tasks/submit", "POST"),
        ("/api/v1/valuation", "POST"),
        ("/api/v1/admin/queues", "GET"),
        ("/api/v1/admin/tasks", "GET"),
    ]

    auth_ok = True

    for path, method in access_tests:

        if method == "GET":
            result = client.get(path)
        else:
            result = client.post(path, json={})

        protected_response = result.status_code == 401

        print(
            path,
            "->",
            result.status_code,
            "|",
            "SECURITY_ENFORCED"
            if protected_response
            else "OPEN"
        )

        if not protected_response:
            auth_ok = False

    print(
        "AUTH GATE:",
        "PASS" if auth_ok else "FAIL"
    )

    print("\n8. INFRASTRUCTURE BASELINE")
    print("-" * 50)

    health = client.get("/health")
    ready = client.get("/ready")

    print("HEALTH:", health.status_code, health.json())
    print("READY:", ready.status_code, ready.json())

    infrastructure_ok = (
        health.status_code == 200
        and ready.status_code == 200
    )

    print(
        "INFRASTRUCTURE:",
        "PASS" if infrastructure_ok else "FAIL"
    )

    print("\n9. MOCK JWT SEARCH")
    print("-" * 50)

    mock_found = False

    search_files = [
        Path("backend/main.py"),
        Path("backend/api/routers/auth_router.py"),
        Path("backend/services/user_service.py"),
    ]

    for path in search_files:
        if path.exists():
            text = path.read_text(
                encoding="utf-8",
                errors="ignore"
            )

            if "mock-jwt-token-xyz" in text:
                mock_found = True
                print("MOCK JWT FOUND:", path)

    print(
        "MOCK JWT:",
        "FAIL - FOUND" if mock_found else "PASS - NOT FOUND"
    )

    print("\n10. FINAL BASELINE GATE")
    print("-" * 50)

    final_pass = all([
        compile_ok,
        import_ok,
        route_ok,
        openapi_ok,
        security_ok,
        settings_ok,
        jwt_ok,
        auth_ok,
        infrastructure_ok,
        not mock_found,
    ])

    print("COMPILE:", "PASS" if compile_ok else "FAIL")
    print("APPLICATION IMPORT:", "PASS" if import_ok else "FAIL")
    print("ROUTE INVENTORY:", "PASS" if route_ok else "FAIL")
    print("OPENAPI SECURITY:", "PASS" if security_ok else "FAIL")
    print("SETTINGS:", "PASS" if settings_ok else "FAIL")
    print("JWT:", "PASS" if jwt_ok else "FAIL")
    print("AUTH GATE:", "PASS" if auth_ok else "FAIL")
    print("INFRASTRUCTURE:", "PASS" if infrastructure_ok else "FAIL")
    print("MOCK JWT:", "PASS" if not mock_found else "FAIL")

    print("")
    print(
        "OVERALL BASELINE:",
        "PASS" if final_pass else "FAIL"
    )

    print(
        "PRODUCTION STATUS:",
        "READY" if final_pass else "BLOCKED"
    )

else:
    print("\nAPPLICATION BASELINE SKIPPED")
    print("PRODUCTION STATUS: BLOCKED")

print("\n" + "=" * 50)
print("BLOCK 31K-CL COMPLETE")
print("=" * 50)
