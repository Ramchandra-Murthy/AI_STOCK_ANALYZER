from fastapi.testclient import TestClient
from backend.main import app
from backend.security.jwt import create_access_token, decode_token
import uuid

print("=" * 70)
print("EROS 3.0 - BLOCK 31K-DH")
print("FINAL SECURITY REGRESSION")
print("=" * 70)

print()
print("1. APPLICATION")
print("-" * 70)
print("APP:", type(app))
print("TITLE:", app.title)
print("VERSION:", app.version)

print()
print("2. AUTH ROUTES VIA OPENAPI")
print("-" * 70)

schema = app.openapi()
paths = schema["paths"]

for path in [
    "/api/v1/auth/register",
    "/api/v1/auth/login",
]:
    print(path, "FOUND:", path in paths)

print()
print("3. AUTH ROUTER DIRECT")
print("-" * 70)

from backend.api.routers.auth_router import router as auth_router

print("PREFIX:", auth_router.prefix)
print("ROUTE COUNT:", len(auth_router.routes))

for r in auth_router.routes:
    print(
        r.path,
        sorted(r.methods),
        r.endpoint.__module__,
        r.endpoint.__name__
    )

print()
print("4. ROUTER IDENTITY")
print("-" * 70)

from backend import main as main_module

print("SAME OBJECT:", main_module.auth_router is auth_router)

print()
print("5. SOURCE DUPLICATE CHECK")
print("-" * 70)

from pathlib import Path

main_text = Path("backend/main.py").read_text(encoding="utf-8")

print(
    "INLINE REGISTER:",
    main_text.count('@app.post("/api/v1/auth/register"')
)

print(
    "INLINE LOGIN:",
    main_text.count('@app.post("/api/v1/auth/login"')
)

print(
    "AUTH INCLUDE:",
    main_text.count("app.include_router(auth_router)")
)

print()
print("6. JWT CONTRACT")
print("-" * 70)

token = create_access_token({
    "sub": "dh_contract_user",
    "role": "ANALYST"
})

decoded = decode_token(token)

print("TOKEN CREATED:", bool(token))
print("TOKEN LENGTH:", len(token))
print("DECODE SUCCESS:", bool(decoded))
print("SUB:", decoded.get("sub") if decoded else None)
print("ROLE:", decoded.get("role") if decoded else None)
print("ISSUER:", decoded.get("iss") if decoded else None)

print()
print("7. LOGIN SMOKE TEST")
print("-" * 70)

client = TestClient(app)

username = "dh_" + uuid.uuid4().hex[:12]
password = "DH_Test_12345"
email = username + "@example.com"

register = client.post(
    "/api/v1/auth/register",
    json={
        "username": username,
        "email": email,
        "password": password,
        "role": "VIEWER"
    }
)

print("REGISTER STATUS:", register.status_code)
print("REGISTER BODY:", register.text)

login = client.post(
    "/api/v1/auth/login",
    json={
        "username": username,
        "password": password
    }
)

print("LOGIN STATUS:", login.status_code)
print("LOGIN BODY:", login.text)

login_data = login.json()

print("ACCESS TOKEN PRESENT:", bool(login_data.get("access_token")))
print("TOKEN TYPE:", login_data.get("token_type"))
print("EXPIRES IN:", login_data.get("expires_in"))
print("USER PRESENT:", bool(login_data.get("user")))

token = login_data.get("access_token")

print()
print("8. UNAUTHENTICATED SECURITY")
print("-" * 70)

unauth_tests = [
    (
        "VALUATION",
        "POST",
        "/api/v1/valuation",
        {
            "symbol": "RELIANCE.NS",
            "eps": 100,
            "growth_rate": 0.10,
            "discount_rate": 0.12,
            "current_price": 2500
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
    (
        "TASK_SUBMIT",
        "POST",
        "/api/v1/tasks/submit",
        {
            "symbol": "RELIANCE.NS"
        }
    )
]

for name, method, path, body in unauth_tests:
    response = client.request(
        method,
        path,
        json=body
    )

    print(name, "->", response.status_code)

print()
print("9. AUTHENTICATED VALUATION")
print("-" * 70)

response = client.post(
    "/api/v1/valuation",
    headers={
        "Authorization": "Bearer " + token
    },
    json={
        "symbol": "RELIANCE.NS",
        "eps": 100,
        "growth_rate": 0.10,
        "discount_rate": 0.12,
        "current_price": 2500
    }
)

print("STATUS:", response.status_code)
print("BODY:", response.text)

print()
print("10. FINAL ROUTE COUNTS")
print("-" * 70)

print("APP TOP LEVEL ROUTES:", len(app.routes))

business = [
    "/api/v1/valuation",
    "/api/v1/admin/queues",
    "/api/v1/admin/tasks",
]

for path in business:
    matches = [
        r for r in app.routes
        if getattr(r, "path", None) == path
    ]
    print(path, "TOP LEVEL MATCHES:", len(matches))

print()
print("=" * 70)
print("BLOCK 31K-DH COMPLETE")
print("=" * 70)