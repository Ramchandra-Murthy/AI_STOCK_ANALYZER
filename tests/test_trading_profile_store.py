from __future__ import annotations

import pytest

from algorithmic_trading.trading_profile import TradingProfile
from services.trading_profile_store import (
    TradingProfileStoreError,
    delete_profile,
    list_profiles,
    load_profile,
    save_profile,
)


def test_profile_store_round_trips_and_updates(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TRADING_PROFILES_DATABASE_PATH", str(tmp_path / "profiles.sqlite3"))
    profile = TradingProfile(name="Intraday", capital=10_000, risk_value=0.5)

    save_profile(profile)

    assert list_profiles() == ["Intraday"]
    assert load_profile("Intraday") == profile

    changed = TradingProfile(name="Intraday", capital=20_000, risk_value=1.0)
    save_profile(changed)
    assert list_profiles() == ["Intraday"]
    assert load_profile("Intraday") == changed


def test_profile_store_delete_and_missing_profile(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TRADING_PROFILES_DATABASE_PATH", str(tmp_path / "profiles.sqlite3"))
    save_profile(TradingProfile(name="Swing"))

    delete_profile("Swing")

    assert list_profiles() == []
    with pytest.raises(TradingProfileStoreError, match="not found"):
        load_profile("Swing")
    with pytest.raises(TradingProfileStoreError, match="not found"):
        delete_profile("Swing")


def test_profile_store_rejects_non_profile(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TRADING_PROFILES_DATABASE_PATH", str(tmp_path / "profiles.sqlite3"))

    with pytest.raises(TradingProfileStoreError, match="TradingProfile"):
        save_profile({"name": "unsafe"})  # type: ignore[arg-type]
