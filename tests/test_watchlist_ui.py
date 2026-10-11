"""Tests for the authenticated watchlist UI adapter."""

from services.watchlist_ui import get_or_create_default_watchlist


def test_adapter_creates_seeded_default_list_for_authenticated_user(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCHLIST_DATABASE_PATH", str(tmp_path / "watchlists.sqlite3"))
    user = {"is_logged_in": True, "iss": "https://identity.example", "sub": "user-1"}

    user_id, watchlist_id, symbols = get_or_create_default_watchlist(
        user, ["RELIANCE.NS", "TCS.NS"]
    )

    assert user_id == "oidc:https://identity.example:user-1"
    assert symbols == ["RELIANCE.NS", "TCS.NS"]
    assert watchlist_id > 0


def test_adapter_does_not_mix_users(tmp_path, monkeypatch):
    monkeypatch.setenv("WATCHLIST_DATABASE_PATH", str(tmp_path / "watchlists.sqlite3"))
    first = {"is_logged_in": True, "iss": "https://identity.example", "sub": "user-1"}
    second = {"is_logged_in": True, "iss": "https://identity.example", "sub": "user-2"}

    _, first_id, _ = get_or_create_default_watchlist(first, ["RELIANCE.NS"])
    _, second_id, second_symbols = get_or_create_default_watchlist(second, ["TCS.NS"])

    assert first_id != second_id
    assert second_symbols == ["TCS.NS"]
