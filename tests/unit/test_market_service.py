import pandas as pd

from services import market_service


def test_clean_close_series_handles_multiindex_close():
    frame = pd.DataFrame(
        {
            ("Close", "TEST"): [100.0, 101.0],
            ("Open", "TEST"): [99.0, 100.0],
        }
    )
    close = market_service._clean_close_series(frame)
    assert close.tolist() == [100.0, 101.0]


def test_last_observation_prefers_intraday(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            assert kwargs["interval"] == "1m"
            return pd.DataFrame({"Close": [100.0, 105.0]})

    monkeypatch.setattr(market_service.yf, "Ticker", lambda _: FakeTicker())

    value, change, previous_close, observed_at, frequency, is_intraday = (
        market_service._get_last_observation("TEST")
    )
    assert value == 105.0
    assert change == 5.0
    assert frequency == "intraday_1m"
    assert is_intraday is True


def test_last_observation_falls_back_to_daily(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            if kwargs["interval"] == "1m":
                return pd.DataFrame()
            return pd.DataFrame({"Close": [100.0, 105.0]})

    monkeypatch.setattr(market_service.yf, "Ticker", lambda _: FakeTicker())

    value, change, observed_at, frequency, is_intraday = market_service._get_last_observation(
        "TEST"
    )
    assert value == 105.0
    assert change == 5.0
    assert frequency == "daily"
    assert is_intraday is False


def test_last_observation_rejects_empty_provider_data(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame()

    monkeypatch.setattr(market_service.yf, "Ticker", lambda _: FakeTicker())

    assert market_service._get_last_observation("TEST") == (
        None,
        None,
        None,
        None,
        "unavailable",
        False,
    )


def test_indices_keep_all_expected_keys(monkeypatch):
    def fake_observation(ticker):
        return (100.0, 1.0, 99.0, "2026-09-08T10:00:00", "intraday_1m", True)

    monkeypatch.setattr(market_service, "_get_last_observation", fake_observation)

    data = market_service.get_market_indices()

    assert set(data) == set(market_service.MARKET_INDICES)
    assert all(item["frequency"] == "intraday_1m" for item in data.values())
    assert all(item["is_intraday"] is True for item in data.values())
