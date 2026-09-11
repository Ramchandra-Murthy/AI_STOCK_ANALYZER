import pandas as pd

from services import research_service, technical_service


class FakeTicker:
    def __init__(self):
        self.fast_info = {
            "last_price": 2510.25,
            "previous_close": 2498.00,
            "last_volume": 123456,
            "last_trade_time": None,
        }
        self._financials = pd.DataFrame()
        self._balance_sheet = pd.DataFrame()
        self._cashflow = pd.DataFrame()

    @property
    def info(self):
        return {
            "longName": "Test Company",
            "currentPrice": 2490.00,
            "previousClose": 2480.00,
            "marketState": "REGULAR",
        }

    @property
    def financials(self):
        return self._financials

    @property
    def balance_sheet(self):
        return self._balance_sheet

    @property
    def cashflow(self):
        return self._cashflow


def test_fast_quote_is_preferred_over_info(monkeypatch):
    monkeypatch.setattr(research_service.yf, "Ticker", lambda symbol: FakeTicker())

    result = research_service.get_stock_profile("TEST")

    assert result["price"] == 2510.25
    assert result["price_source"] == "yfinance.fast_info"
    assert result["previous_close"] == 2498.00
    assert result["market_state"] == "REGULAR"


def test_fast_quote_failure_falls_back_to_info(monkeypatch):
    class NoFastTicker(FakeTicker):
        @property
        def fast_info(self):
            raise RuntimeError("quote unavailable")

    monkeypatch.setattr(research_service.yf, "Ticker", lambda symbol: NoFastTicker())

    result = research_service.get_stock_profile("TEST")

    assert result["price"] == 2490.00
    assert result["price_source"] == "yfinance.info"


def test_history_boundary_records_provenance(monkeypatch):
    index = pd.date_range("2026-09-01", periods=3, freq="D")
    frame = pd.DataFrame(
        {
            "Open": [1, 2, 3],
            "High": [2, 3, 4],
            "Low": [0, 1, 2],
            "Close": [1.5, 2.5, 3.5],
            "Volume": [100, 200, 300],
        },
        index=index,
    )

    monkeypatch.setattr(technical_service.yf, "download", lambda *args, **kwargs: frame)

    result = technical_service.get_price_history("TEST", period="1y")

    assert result is not None
    assert result.attrs["data_source"] == "yfinance.download"
    assert result.attrs["requested_period"] == "1y"
    assert result.attrs["last_bar_timestamp"] == index[-1].isoformat()


def test_history_download_failure_returns_none(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("network failure")

    monkeypatch.setattr(technical_service.yf, "download", fail)

    assert technical_service.get_price_history("TEST") is None
