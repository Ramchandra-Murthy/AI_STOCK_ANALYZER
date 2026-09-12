from backend.api.routers.eros_production_router import router as eros_router
from backend.main import app


def test_block25a_eros_production_route_registered():
    matching = []
    for route in eros_router.routes:
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", set()) or set()
        if path == "/api/v1/eros/evaluate":
            matching.append(
                (
                    path,
                    tuple(sorted(methods)),
                )
            )
    assert matching, (
        "EROS production evaluation route is not registered "
        "in the canonical EROS production router."
    )
    path, methods = matching[0]
    assert path == "/api/v1/eros/evaluate"
    assert "POST" in methods


def test_block25a_eros_production_openapi_contract():
    schema = app.openapi()
    assert "/api/v1/eros/evaluate" in schema["paths"]
    operation = schema["paths"]["/api/v1/eros/evaluate"]["post"]
    assert operation["responses"]
    assert "requestBody" in operation


def test_block25a_eros_production_router_contract():
    assert eros_router.prefix == "/api/v1/eros"
    assert "EROS 3.0 Production Workflow" in (eros_router.tags or [])
