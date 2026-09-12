from __future__ import annotations

import sys
import uuid
from datetime import timedelta

print("=" * 50)
print("EROS 3.0 - BLOCK 31K-CC PYTHON SECURITY AUDIT")
print("=" * 50)

# --------------------------------------------------
# 1. APPLICATION IMPORT
# --------------------------------------------------

print()
print("1. FASTAPI APPLICATION IMPORT")
print("-" * 50)

try:
    import backend.main as main

    print("APP:", type(main.app).__name__)
    print("TITLE:", main.app.title)
    print("VERSION:", main.app.version)
    print("APPLICATION IMPORT: PASS")

except Exception as exc:
    print("APPLICATION IMPORT: FAIL")
    print(type(exc).__name__ + ":", exc)
    sys.exit(1)

# --------------------------------------------------
# 2. ROUTE INVENTORY
# --------------------------------------------------

print()
print("2. APPLICATION ROUTE INVENTORY")
print("-" * 50)

for route in main.app.routes:

    if not hasattr(route, "path"):
        continue

    if "/api/v1/" not in route.path:
        continue

    methods = ",".join(sorted(route.methods or []))

    print(route.path, "|", methods)

# --------------------------------------------------
# 3. OPENAPI SECURITY
# --------------------------------------------------

print()
print("3. OPENAPI SECURITY AUDIT")
print("-" * 50)

from fastapi.testclient import TestClient

client = TestClient(main.app)

openapi_response = client.get("/openapi.json")

print("OPENAPI STATUS:", openapi_response.status_code)

openapi = openapi_response.json()

print("TITLE:", openapi.get("info", {}).get("title"))
print("VERSION:", openapi.get("info", {}).get("version"))

security_schemes = openapi.get("components", {}).get("securitySchemes", {})

print("SECURITY SCHEMES:", security_schemes)

secured = []

for path, item in openapi.get("paths", {}).items():

    for method, operation in item.items():

        if not isinstance(operation, dict):
            continue

        if operation.get("security"):
            secured.append((path, method.upper()))

print("SECURED OPERATIONS:", len(secured))

for path, method in secured:
    print(" ", path, "|", method)

# --------------------------------------------------
# 4. SETTINGS
# --------------------------------------------------

print()
print("4. SETTINGS / JWT CONFIGURATION")
print("-" * 50)

from backend.config.settings import settings

print("PROJECT_NAME:", settings.PROJECT_NAME)
print("ENVIRONMENT:", settings.ENVIRONMENT)
print("DATABASE_URL CONFIGURED:", bool(settings.DATABASE_URL))
print("REDIS_URL:", settings.REDIS_URL)
print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)
print("ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
print("AUTH_ENABLED:", settings.AUTH_ENABLED)
print("JWT_SECRET CONFIGURED:", bool(settings.JWT_SECRET))
print("SECRET_KEY CONFIGURED:", bool(settings.SECRET_KEY))

# --------------------------------------------------
# 5. JWT FUNCTIONAL TEST
# --------------------------------------------------

print()
print("5. JWT FUNCTIONAL TEST")
print("-" * 50)

from backend.security.jwt import JWTSecurity

payload = {
    "sub": "eros_security_test",
    "username": "eros_security_test",
    "role": "ANALYST",
}

token = JWTSecurity.create_access_token(
    payload,
    expires_delta=timedelta(minutes=60),
)

print("TOKEN CREATED:", bool(token))
print("TOKEN LENGTH:", len(token))

decoded = JWTSecurity.decode_access_token(token)

print("DECODE SUCCESS:", decoded is not None)

if decoded:

    print("SUB:", decoded.get("sub"))
    print("USERNAME:", decoded.get("username"))
    print("ROLE:", decoded.get("role"))
    print("ISSUER:", decoded.get("iss"))
    print("EXP:", decoded.get("exp"))

invalid = JWTSecurity.decode_access_token("invalid.jwt.token")

print("INVALID TOKEN RETURNS NONE:", invalid is None)

# --------------------------------------------------
# 6. AUTH REGISTER / LOGIN
# --------------------------------------------------

print()
print("6. AUTH REGISTER / LOGIN")
print("-" * 50)

suffix = uuid.uuid4().hex[:10]

username = "eros_security_" + suffix
email = username + "@example.com"
password = "ErosSecurity123!"

register_payload = {
    "username": username,
    "email": email,
    "password": password,
    "role": "ANALYST",
}

register_response = client.post(
    "/api/v1/auth/register",
    json=register_payload,
)

print("REGISTER STATUS:", register_response.status_code)

print("REGISTER BODY:", register_response.json())

login_response = client.post(
    "/api/v1/auth/login",
    json={
        "username": username,
        "password": password,
    },
)

print("LOGIN STATUS:", login_response.status_code)

print("LOGIN BODY:", login_response.json())

login_body = login_response.json()

token = login_body.get("access_token")

print("TOKEN PRESENT:", bool(token))

# --------------------------------------------------
# 7. UNAUTHENTICATED ACCESS
# --------------------------------------------------

print()
print("7. UNAUTHENTICATED ACCESS SECURITY GATE")
print("-" * 50)

tests = [
    (
        "TASK_SUBMIT",
        "/api/v1/tasks/submit",
        "POST",
        {
            "task_name": "forecast.execute",
            "symbol": "TCS.NS",
        },
    ),
    (
        "VALUATION",
        "/api/v1/valuation",
        "POST",
        {
            "symbol": "TCS.NS",
        },
    ),
    (
        "ADMIN_QUEUES",
        "/api/v1/admin/queues",
        "GET",
        None,
    ),
    (
        "ADMIN_TASKS",
        "/api/v1/admin/tasks",
        "GET",
        None,
    ),
]

for name, path, method, body in tests:

    if method == "POST":

        response = client.post(
            path,
            json=body,
        )

    else:

        response = client.get(path)

    classification = "SECURITY_ENFORCED" if response.status_code in (401, 403) else "OPEN"

    print(name, "->", response.status_code, "|", classification)

# --------------------------------------------------
# 8. AUTHENTICATED ACCESS
# --------------------------------------------------

print()
print("8. AUTHENTICATED ACCESS")
print("-" * 50)

if token:

    headers = {"Authorization": "Bearer " + token}

    for name, path, method, body in tests:

        if method == "POST":

            response = client.post(
                path,
                json=body,
                headers=headers,
            )

        else:

            response = client.get(
                path,
                headers=headers,
            )

        print(name, "->", response.status_code)

else:

    print("SKIPPED: LOGIN DID NOT RETURN TOKEN")

# --------------------------------------------------
# 9. HEALTH / READY
# --------------------------------------------------

print()
print("9. HEALTH / READINESS")
print("-" * 50)

health = client.get("/health")
ready = client.get("/ready")

print("HEALTH:", health.status_code, health.json())

print("READY:", ready.status_code, ready.json())

# --------------------------------------------------
# 10. FINAL REGRESSION
# --------------------------------------------------

print()
print("10. FINAL REGRESSION")
print("-" * 50)

print("OPENAPI:", openapi_response.status_code)

print("HEALTH:", health.status_code)

print("READY:", ready.status_code)

print("AUTH_ENABLED:", settings.AUTH_ENABLED)

print("JWT_ALGORITHM:", settings.JWT_ALGORITHM)

print("JWT_SECRET CONFIGURED:", bool(settings.JWT_SECRET))

print()
print("==================================================")
print("BLOCK 31K-CC PYTHON AUDIT COMPLETE")
print("==================================================")
