from api.main import dashboard, health


def test_health():
    assert health() == {"status": "ok", "service": "eros-api"}


def test_dashboard_path():
    response = dashboard()
    assert response.path.endswith("api/static/index.html")
