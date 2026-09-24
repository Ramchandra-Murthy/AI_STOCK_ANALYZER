from api.main import health


def test_health():
    assert health() == {"status": "ok", "service": "eros-api"}
