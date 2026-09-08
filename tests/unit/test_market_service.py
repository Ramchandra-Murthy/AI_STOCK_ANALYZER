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


def test_last_change_returns_latest_and_percent(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame({"Close": [100.0, 105.0]})

    monkeypatch.setattr(market_service.yf, "Ticker", lambda _: FakeTicker())

    value, change = market_service._get_last_change("TEST")
    assert value == 105.0
    assert change == 5.0


def test_last_change_rejects_single_observation(monkeypatch):
    class FakeTicker:
        def history(self, **kwargs):
            return pd.DataFrame({"Close": [100.0]})

    monkeypatch.setattr(market_service.yf, "Ticker", lambda _: FakeTicker())

    assert market_service._get_last_change("TEST") == (None, None)


def test_indices_keep_all_expected_keys(monkeypatch):
    monkeypatch.setattr(
        market_service,
        "_get_last_change",
        lambda ticker: (100.0, 1.0),
    )

    data = market_service.get_market_indices()

    assert set(data) == set(market_service.MARKET_INDICES)
    assert all(set(item) == {"value", "change"} for item in data.values())
