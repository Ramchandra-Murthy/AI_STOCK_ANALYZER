import pandas as pd

from services import research_service, technical_service


def test_fast_quote_is_preferred_over_info(monkeypatch):
    monkeypatch.setattr(
        research_service,
        "get_latest_available_price",
        lambda symbol: {
            "price": 2510.25,
            "previous_close": 2498.00,
            "source": "yfinance.fast_info",
            "observed_at": "2026-09-12T09:00:00",
            "frequency": "available",
            "is_intraday": True,
            "is_tick_live": False,
        },
    )

    result = research_service.get_stock_profile("TEST")

    assert result["price"] == 2510.25
    assert result["price_source"] == "yfinance.fast_info"
    assert result["previous_close"] == 2498.00
    assert result["market_state"] == "UNKNOWN"


def test_canonical_quote_failure_returns_unavailable_profile(monkeypatch):
    monkeypatch.setattr(
        research_service,
        "get_latest_available_price",
        lambda symbol: {"price": None, "previous_close": None, "source": "unavailable"},
    )

    result = research_service.get_stock_profile("TEST")

    assert result is not None
    assert result["price"] is None
    assert result["price_source"] == "unavailable"


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
