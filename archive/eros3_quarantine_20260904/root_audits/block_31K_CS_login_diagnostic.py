import json
import os
import sys

print("=" * 70)
print("EROS 3.0 - BLOCK 31K-CS LOGIN RESPONSE DIAGNOSTIC")
print("=" * 70)

try:
    from fastapi.testclient import TestClient
    from backend.main import app

    print("APPLICATION IMPORT: PASS")
    print("APP:", type(app).__name__)

    client = TestClient(app)

    # Use a unique test identity.
    username = "eros_cs_login_test"
    email = "eros_cs_login_test@example.com"
    password = "ErosCSLogin#2026"

    print()
    print("1. REGISTER")
    print("-" * 70)

    try:
        r = client.post(
            "/api/v1/auth/register",
            json={"username": username, "email": email, "password": password},
        )

        print("STATUS:", r.status_code)
        print("BODY:", r.text[:2000])

    except Exception as exc:
        print("REGISTER ERROR:", type(exc).__name__, str(exc))

    print()
    print("2. LOGIN")
    print("-" * 70)

    try:
        r = client.post("/api/v1/auth/login", json={"username": username, "password": password})

        print("STATUS:", r.status_code)
        print("CONTENT-TYPE:", r.headers.get("content-type"))
        print("RAW BODY:", r.text[:4000])

        try:
            body = r.json()
            print("JSON TYPE:", type(body).__name__)

            if isinstance(body, dict):
                print("JSON KEYS:", sorted(body.keys()))

                for key, value in body.items():
                    if key.lower() in {
                        "access_token",
                        "token",
                        "jwt",
                        "refresh_token",
                        "token_type",
                    }:
                        if key.lower() in {"access_token", "token", "jwt", "refresh_token"}:
                            print(
                                f"{key}: PRESENT={bool(value)} "
                                f"LENGTH={len(str(value)) if value else 0}"
                            )
                        else:
                            print(f"{key}: {value}")

        except Exception as exc:
            print("JSON PARSE ERROR:", type(exc).__name__, str(exc))

    except Exception as exc:
        print("LOGIN ERROR:", type(exc).__name__, str(exc))

    print()
    print("3. AUTH ROUTER SOURCE INSPECTION")
    print("-" * 70)

    try:
        import backend.api.routers.auth_router as ar

        print("AUTH ROUTER MODULE:", ar.__file__)

        source = open(ar.__file__, "r", encoding="utf-8").read()

        for i, line in enumerate(source.splitlines(), 1):
            low = line.lower()
            if "access_token" in low or "token_type" in low or "login" in low or "return" in low:
                print(f"{i}: {line}")

    except Exception as exc:
        print("SOURCE INSPECTION ERROR:", type(exc).__name__, str(exc))

    print()
    print("4. LOGIN DIAGNOSTIC COMPLETE")
    print("=" * 70)

except Exception as exc:
    print("DIAGNOSTIC FAILURE:", type(exc).__name__, str(exc))
    sys.exit(1)
