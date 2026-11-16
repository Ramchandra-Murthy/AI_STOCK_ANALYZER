import pandas as pd

from services import research_service, technical_service
from services.market_service import normalize_market_symbol, scan_market_universe


def test_normalize_nse_symbol():
    assert normalize_market_symbol("RELIANCE", "NSE") == "RELIANCE.NS"


def test_normalize_bse_symbol():
    assert normalize_market_symbol("500570", "BSE") == "500570.BO"


def test_explicit_exchange_suffix_is_preserved():
    assert normalize_market_symbol("TCS.NS", "BSE") == "TCS.NS"
    assert normalize_market_symbol("500570.BO", "NSE") == "500570.BO"


def test_scanner_accepts_both_exchanges(monkeypatch):
    def fake_quote(symbol, exchange="NSE"):
        return {
            "symbol": symbol,
            "exchange": "BSE" if symbol.endswith(".BO") else "NSE",
            "price": 100.0,
            "change_pct": 2.0 if symbol.endswith(".NS") else -3.0,
            "observed_at": "2026-09-16T09:00:00",
            "source": "test",
            "frequency": "daily",
            "is_tick_live": False,
            "is_intraday": False,
        }

    monkeypatch.setattr(
        "services.market_service.get_latest_available_price",
        fake_quote,
    )

    result = scan_market_universe(
        {"NSE": ["RELIANCE"], "BSE": ["500570"]},
        top_n=2,
    )

    assert set(result["Exchange"]) == {"NSE", "BSE"}
    assert set(result["Ticker"]) == {"RELIANCE.NS", "500570.BO"}


def test_fast_quote_is_preferred_over_info(monkeypatch):
    class FakeTicker:
        info = {
            "longName": "Test Company",
            "shortName": "TEST",
            "currency": "INR",
        }
        financials = pd.DataFrame()
        balance_sheet = pd.DataFrame()
        dividends = pd.Series(dtype=float)

    monkeypatch.setattr(
        research_service.yf,
        "Ticker",
        lambda symbol: FakeTicker(),
    )
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
