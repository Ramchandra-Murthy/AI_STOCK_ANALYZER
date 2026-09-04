from pathlib import Path
import py_compile
import sys

print("=" * 58)
print("EROS 3.0 - BLOCK 31K-CK")
print("FINAL SECURITY VALIDATION - PYTHON AUDIT")
print("=" * 58)

root = Path(".")

router_files = [
    Path("backend/main.py"),
    Path("backend/api/routers/task_router.py"),
    Path("backend/api/routers/valuation_router.py"),
    Path("backend/api/routers/admin_task_router.py"),
    Path("backend/api/routers/auth_router.py"),
    Path("backend/security/dependencies.py"),
    Path("backend/security/jwt.py"),
    Path("backend/services/user_service.py"),
]

print("\n1. PYTHON COMPILE")
print("-" * 58)

compile_pass = True

for path in router_files:
    try:
        py_compile.compile(str(path), doraise=True)
        print("COMPILE PASS:", path)
    except Exception as exc:
        compile_pass = False
        print("COMPILE FAIL:", path)
        print(type(exc).__name__ + ":", str(exc))

print("\n2. FASTAPI APPLICATION IMPORT")
print("-" * 58)

import_pass = False
app = None

try:
    import backend.main as main_module

    app = main_module.app

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)
    print("TITLE:", app.title)
    print("VERSION:", app.version)

    import_pass = True

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", str(exc))

openapi_pass = False
auth_pass = False
infra_pass = False
mock_pass = False

if app is not None:

    from fastapi.testclient import TestClient

    client = TestClient(app)

    print("\n3. ROUTE SECURITY INVENTORY")
    print("-" * 58)

    business_routes = {
        ("/api/v1/tasks/submit", "POST"),
        ("/api/v1/valuation", "POST"),
        ("/api/v1/admin/queues", "GET"),
        ("/api/v1/admin/tasks", "GET"),
    }

    for route in app.routes:
        path = getattr(route, "path", "")
        methods = sorted(getattr(route, "methods", set()) or [])
        dependency_count = len(
            getattr(route, "dependant", None).dependencies
        ) if getattr(route, "dependant", None) else 0

        for method in methods:
            if (path, method) in business_routes:
                print(
                    "BUSINESS |",
                    path,
                    "|",
                    method,
                    "| DEP_COUNT=",
                    dependency_count
                )

    print("\n4. OPENAPI SECURITY")
    print("-" * 58)

    try:
        response = client.get("/openapi.json")

        print("OPENAPI:", response.status_code)

        spec = response.json()

        schemes = (
            spec
            .get("components", {})
            .get("securitySchemes", {})
        )

        print("SECURITY SCHEMES:", schemes)

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

        print("SECURED OPERATIONS:", len(secured))

        for path, method in secured:
            print(" ", path, "|", method)

        required_business = [
            ("/api/v1/tasks/submit", "POST"),
            ("/api/v1/valuation", "POST"),
            ("/api/v1/admin/queues", "GET"),
            ("/api/v1/admin/tasks", "GET"),
        ]

        secured_business = 0

        for path, method in required_business:

            operation = (
                spec
                .get("paths", {})
                .get(path, {})
                .get(method.lower(), {})
            )

            protected = bool(operation.get("security"))

            print(
                path,
                "|",
                method,
                "| SECURITY=",
                protected
            )

            if protected:
                secured_business += 1

        openapi_pass = (
            response.status_code == 200
            and "HTTPBearer" in schemes
            and secured_business == 4
        )

        print(
            "OPENAPI SECURITY GATE:",
            "PASS" if openapi_pass else "FAIL"
        )

    except Exception as exc:
        print("OPENAPI AUDIT: FAIL")
        print(type(exc).__name__ + ":", str(exc))

    print("\n5. SETTINGS + JWT FUNCTIONAL")
    print("-" * 58)

    try:
        from datetime import timedelta
        from backend.config.settings import settings
        from backend.security.jwt import JWTSecurity

        print("PROJECT_NAME:", settings.PROJECT_NAME)
        print("ENVIRONMENT:", settings.ENVIRONMENT)
        print("AUTH_ENABLED:", settings.AUTH_ENABLED)
        print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
        print(
            "ACCESS_TOKEN_EXPIRE_MINUTES:",
            settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        print(
            "JWT_SECRET CONFIGURED:",
            bool(settings.JWT_SECRET or settings.SECRET_KEY)
        )
        print(
            "DATABASE_URL CONFIGURED:",
            bool(settings.DATABASE_URL)
        )
        print(
            "REDIS_URL CONFIGURED:",
            bool(settings.REDIS_URL)
        )

        payload = {
            "sub": "eros_security_test",
            "username": "eros_security_test",
            "role": "ANALYST",
        }

        token = JWTSecurity.create_access_token(
            payload,
            expires_delta=timedelta(minutes=60)
        )

        decoded = JWTSecurity.decode_access_token(token)

        print("TOKEN CREATED:", bool(token))
        print("TOKEN LENGTH:", len(token))
        print("DECODE SUCCESS:", decoded is not None)

        if decoded:
            print("SUB:", decoded.get("sub"))
            print("USERNAME:", decoded.get("username"))
            print("ROLE:", decoded.get("role"))
            print("ISSUER:", decoded.get("iss"))
            print("EXP:", decoded.get("exp"))

        invalid = JWTSecurity.decode_access_token(
            "invalid.jwt.token"
        )

        print(
            "INVALID TOKEN RETURNS NONE:",
            invalid is None
        )

        jwt_pass = (
            bool(token)
            and decoded is not None
            and decoded.get("sub") == "eros_security_test"
            and decoded.get("role") == "ANALYST"
            and invalid is None
        )

        print(
            "JWT FUNCTIONAL GATE:",
            "PASS" if jwt_pass else "FAIL"
        )

    except Exception as exc:
        jwt_pass = False
        print("JWT FUNCTIONAL: FAIL")
        print(type(exc).__name__ + ":", str(exc))

    print("\n6. UNAUTHENTICATED ACCESS GATE")
    print("-" * 58)

    tests = [
        ("/api/v1/tasks/submit", "POST"),
        ("/api/v1/valuation", "POST"),
        ("/api/v1/admin/queues", "GET"),
        ("/api/v1/admin/tasks", "GET"),
    ]

    protected_count = 0

    for path, method in tests:

        try:
            if method == "POST":
                result = client.post(path, json={})
            else:
                result = client.get(path)

            enforced = result.status_code == 401

            if enforced:
                protected_count += 1

            print(
                path,
                "->",
                result.status_code,
                "|",
                (
                    "SECURITY_ENFORCED"
                    if enforced
                    else "OPEN_OR_UNAVAILABLE"
                )
            )

        except Exception as exc:
            print(
                path,
                "-> TEST ERROR |",
                type(exc).__name__,
                str(exc)
            )

    print(
        "PROTECTED:",
        protected_count,
        "/",
        len(tests)
    )

    auth_pass = protected_count == len(tests)

    print(
        "AUTH GATE:",
        "PASS" if auth_pass else "FAIL"
    )

    print("\n7. INFRASTRUCTURE")
    print("-" * 58)

    try:
        health = client.get("/health")
        ready = client.get("/ready")

        print("HEALTH:", health.status_code, health.json())
        print("READY:", ready.status_code, ready.json())

        infra_pass = (
            health.status_code == 200
            and ready.status_code == 200
        )

        print(
            "INFRASTRUCTURE:",
            "PASS" if infra_pass else "FAIL"
        )

    except Exception as exc:
        print("INFRASTRUCTURE: FAIL")
        print(type(exc).__name__ + ":", str(exc))

else:
    print("\n3-7. APPLICATION TESTS SKIPPED")
    print("REASON: APPLICATION IMPORT FAILED")

print("\n8. MOCK JWT SEARCH")
print("-" * 58)

mock_matches = []

for path in Path("backend").rglob("*.py"):
    try:
        text = path.read_text(
            encoding="utf-8",
            errors="replace"
        )

        if "mock-jwt-token-xyz" in text:
            for number, line in enumerate(
                text.splitlines(),
                start=1
            ):
                if "mock-jwt-token-xyz" in line:
                    mock_matches.append(
                        (path, number, line)
                    )

    except Exception:
        pass

if mock_matches:
    print("MOCK JWT: FAIL")

    for path, number, line in mock_matches:
        print(
            f"{path}:{number} -> {line}"
        )

else:
    print("MOCK JWT: PASS - NOT FOUND")
    mock_pass = True

print("\n9. MAIN.PY BUSINESS ROUTE AUDIT")
print("-" * 58)

main_path = Path("backend/main.py")

try:
    main_text = main_path.read_text(
        encoding="utf-8",
        errors="replace"
    )

    checks = [
        '@app.post("/api/v1/valuation"',
        '@app.get("/api/v1/admin/queues"',
        '@app.get("/api/v1/admin/tasks"',
    ]

    duplicate_issue = False

    for pattern in checks:
        count = main_text.count(pattern)

        print(
            pattern,
            "| COUNT=",
            count
        )

        if count > 1:
            duplicate_issue = True

    print(
        "MAIN ROUTE DUPLICATES:",
        "FAIL" if duplicate_issue else "PASS"
    )

except Exception as exc:
    duplicate_issue = True
    print(
        "MAIN.PY AUDIT ERROR:",
        type(exc).__name__,
        str(exc)
    )

print("\n10. FINAL SECURITY GATE")
print("-" * 58)

final_pass = (
    compile_pass
    and import_pass
    and openapi_pass
    and auth_pass
    and infra_pass
    and mock_pass
    and not duplicate_issue
)

print(
    "COMPILE:",
    "PASS" if compile_pass else "FAIL"
)

print(
    "APPLICATION IMPORT:",
    "PASS" if import_pass else "FAIL"
)

print(
    "OPENAPI SECURITY:",
    "PASS" if openapi_pass else "FAIL"
)

print(
    "JWT/AUTH:",
    "PASS" if auth_pass else "FAIL"
)

print(
    "INFRASTRUCTURE:",
    "PASS" if infra_pass else "FAIL"
)

print(
    "MOCK JWT:",
    "PASS" if mock_pass else "FAIL"
)

print(
    "MAIN ROUTE DUPLICATES:",
    "PASS" if not duplicate_issue else "FAIL"
)

print("")

if final_pass:
    print("OVERALL SECURITY GATE: PASS")
    print("PRODUCTION STATUS: READY")
else:
    print("OVERALL SECURITY GATE: FAIL")
    print("PRODUCTION STATUS: BLOCKED")

print("=" * 58)
print("BLOCK 31K-CK COMPLETE")
print("=" * 58)
