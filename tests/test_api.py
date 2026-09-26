from api.main import dashboard, health


def test_health():
    assert health() == {"status": "ok", "service": "eros-api"}


def test_dashboard_path():
    response = dashboard()
    assert response.path.endswith("api/static/index.html")


def test_intraday_health_without_scan(monkeypatch):
    monkeypatch.setattr("api.main.recent_scans", lambda limit: [])
    from api.main import intraday_health

    result = intraday_health()
    assert result["status"] == "NO_SCAN"
    assert result["candidates"] == 0
