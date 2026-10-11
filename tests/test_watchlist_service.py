"""Tests for persistent user-isolated watchlists."""

import pytest

from services import watchlist_service as watchlists


@pytest.fixture
def database_path(tmp_path, monkeypatch):
    path = tmp_path / "watchlists.sqlite3"
    monkeypatch.setenv("WATCHLIST_DATABASE_PATH", str(path))
    return path


def test_watchlists_persist_and_are_isolated(database_path):
    first_id = watchlists.create_watchlist("user-a", "Long-term")
    watchlists.add_symbol("user-a", first_id, "reliance.ns")

    assert watchlists.list_symbols("user-a", first_id) == ["RELIANCE.NS"]
    assert watchlists.list_watchlists("user-a")[0]["name"] == "Long-term"
    assert watchlists.list_watchlists("user-b") == []
    with pytest.raises(watchlists.WatchlistError, match="not found"):
        watchlists.list_symbols("user-b", first_id)


def test_create_rename_delete_and_duplicate_symbols(database_path):
    watchlist_id = watchlists.create_watchlist("user-a", "Watchlist 01")
    watchlists.rename_watchlist("user-a", watchlist_id, "Swing")
    assert watchlists.list_watchlists("user-a")[0]["name"] == "Swing"

    assert watchlists.add_symbol("user-a", watchlist_id, "TCS")
    assert not watchlists.add_symbol("user-a", watchlist_id, "tcs")
    assert watchlists.list_symbols("user-a", watchlist_id) == ["TCS"]
    assert watchlists.remove_symbol("user-a", watchlist_id, "TCS")
    assert not watchlists.remove_symbol("user-a", watchlist_id, "TCS")

    watchlists.delete_watchlist("user-a", watchlist_id)
    assert watchlists.list_watchlists("user-a") == []


def test_users_cannot_rename_or_delete_other_users_watchlists(database_path):
    watchlist_id = watchlists.create_watchlist("user-a", "Private")
    with pytest.raises(watchlists.WatchlistError, match="not found"):
        watchlists.rename_watchlist("user-b", watchlist_id, "Hijacked")
    with pytest.raises(watchlists.WatchlistError, match="not found"):
        watchlists.delete_watchlist("user-b", watchlist_id)
    assert watchlists.list_watchlists("user-a")[0]["name"] == "Private"


def test_invalid_identity_name_and_symbol_are_rejected(database_path):
    with pytest.raises(watchlists.WatchlistError, match="authenticated user ID"):
        watchlists.create_watchlist("", "Watchlist")
    with pytest.raises(watchlists.WatchlistError, match="Watchlist name"):
        watchlists.create_watchlist("user-a", " ")
    watchlist_id = watchlists.create_watchlist("user-a", "Valid")
    with pytest.raises(watchlists.WatchlistError, match="valid stock symbol"):
        watchlists.add_symbol("user-a", watchlist_id, "BAD SYMBOL")
