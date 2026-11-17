import pandas as pd
import pytest

from scanner.market_scanner import _analyze_history, _extract_history_frame


def test_extract_history_frame_drops_rows_with_invalid_ohlcv_values() -> None:
    history = pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [100.0, float("nan"), 102.0],
            "Volume": [1000.0, 1100.0, float("inf")],
        },
        index=pd.date_range("2026-10-19", periods=3, freq="D"),
    )

    result = _extract_history_frame(history, "SAMPLE.NS")

    assert len(result) == 1
    assert result.iloc[0]["Close"] == 100.0
    assert result.iloc[0]["Volume"] == 1000.0


@pytest.mark.parametrize(
    "missing_column",
    ["Open", "High", "Low", "Close", "Volume"],
)
def test_extract_history_frame_rejects_missing_required_ohlcv_column(
    missing_column: str,
) -> None:
    history = pd.DataFrame(
        {
            "Open": [100.0],
            "High": [101.0],
            "Low": [99.0],
            "Close": [100.0],
            "Volume": [1000.0],
        }
    ).drop(columns=[missing_column])

    assert _extract_history_frame(history, "SAMPLE.NS").empty


def test_analyze_history_rejects_insufficient_history_without_producing_signal(
    monkeypatch,
) -> None:
    history = pd.DataFrame(
        {
            "Open": [100.0] * 49,
            "High": [101.0] * 49,
            "Low": [99.0] * 49,
            "Close": [100.0] * 49,
            "Volume": [1000.0] * 49,
        },
        index=pd.date_range("2026-08-01", periods=49, freq="D"),
    )
    monkeypatch.setattr(
        "scanner.market_scanner._extract_history_frame",
        lambda _history, _ticker: history,
    )
    signal_calls = []
    monkeypatch.setattr(
        "scanner.market_scanner.generate_signal",
        lambda _frame: signal_calls.append(True) or {"Status": "OK"},
    )

    assert _analyze_history("SAMPLE.NS", history) is None
    assert signal_calls == []


def test_analyze_history_rejects_invalid_ohlcv_rows_before_indicator_calculation(
    monkeypatch,
) -> None:
    history = pd.DataFrame(
        {
            "Open": [100.0] * 50,
            "High": [101.0] * 50,
            "Low": [99.0] * 50,
            "Close": [100.0] * 49 + [float("nan")],
            "Volume": [1000.0] * 50,
        },
        index=pd.date_range("2026-08-01", periods=50, freq="D"),
    )
    monkeypatch.setattr(
        "scanner.market_scanner._extract_history_frame",
        lambda _history, _ticker: _extract_history_frame(history, "SAMPLE.NS"),
    )

    indicator_calls = []
    monkeypatch.setattr(
        "scanner.market_scanner.calculate_sma",
        lambda frame, *_args: indicator_calls.append(True) or frame,
    )

    assert _analyze_history("SAMPLE.NS", history) is None
    assert indicator_calls == []


def test_market_scan_records_analysis_download_failure_per_exchange(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(market_scanner, "NSE_CANDIDATES", ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "BSE_CANDIDATES", [])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates, coverage=None: [("RELIANCE.NS", "NSE", 1.0, 1_000_000.0)],
    )
    monkeypatch.setattr(
        market_scanner,
        "_download_analysis_chunk",
        lambda _tickers: pd.DataFrame(),
    )

    result = market_scanner.market_scan("NSE")

    assert result.empty
    coverage = result.attrs["scanner_coverage"]["NSE"]
    assert coverage["analysis_download_failed"] == 1
    assert coverage["analysis_requested"] == 1
    assert coverage["final_rows"] == 0


def test_market_scan_rejects_unsupported_exchange_filter() -> None:
    from scanner import market_scanner

    with pytest.raises(ValueError, match="Unsupported exchange filter"):
        market_scanner.market_scan("NYSE")


def test_bse_scrip_code_is_resolved_to_yahoo_company_ticker(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(
        market_scanner,
        "yahoo_symbol_for_bse_code",
        lambda code: "RELIANCE" if code == "500325" else None,
    )

    assert market_scanner._ticker("500325", "BSE") == "RELIANCE.BO"
    assert market_scanner._ticker("590109", "BSE") is None


def test_market_scan_exchange_filter_limits_candidate_universe(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(market_scanner, "NSE_CANDIDATES", ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "BSE_CANDIDATES", ["500325"])
    observed = {}

    def fake_screen(candidates, coverage=None, interval="1d"):
        observed.update(candidates)
        observed["interval"] = interval
        return []

    monkeypatch.setattr(market_scanner, "_batch_change_screen", fake_screen)

    result = market_scanner.market_scan("NSE")

    assert result.empty
    assert observed == {"NSE": ["RELIANCE"]}
    assert "scanner_timings" in result.attrs
    assert result.attrs["scanner_coverage"]["NSE"]["candidates"] == 1


def test_full_market_scan_uses_official_exchange_lists(monkeypatch) -> None:
    from scanner import market_scanner

    source_status = {
        "NSE": {
            "origin": "official",
            "source": "official live exchange source",
            "official_source_status": "available",
            "source_symbols": 2,
            "reason": "",
        },
        "BSE": {
            "origin": "official",
            "source": "official live exchange source",
            "official_source_status": "available",
            "source_symbols": 2,
            "reason": "",
        },
    }
    monkeypatch.setattr(market_scanner, "dynamic_nse_symbols", lambda: ["RELIANCE", "INFY"])
    monkeypatch.setattr(market_scanner, "dynamic_bse_symbols", lambda: ["500325", "500209"])
    monkeypatch.setattr(market_scanner, "universe_source_status", lambda: source_status)
    observed = {}

    def fake_screen(candidates, coverage=None):
        observed.update(candidates)
        for exchange, symbols in candidates.items():
            coverage[exchange]["tickers_requested"] = len(symbols)
        return []

    monkeypatch.setattr(market_scanner, "_batch_change_screen", fake_screen)

    result = market_scanner.market_scan("NSE + BSE", universe_mode="full")

    assert result.empty
    assert observed == {
        "NSE": ["RELIANCE", "INFY"],
        "BSE": ["500325", "500209"],
        "interval": "5m",
    }
    assert result.attrs["scanner_universe_mode"] == "full"
    assert result.attrs["scanner_coverage"]["NSE"]["candidates"] == 2
    assert result.attrs["scanner_coverage"]["BSE"]["candidates"] == 2


def test_full_market_scan_does_not_claim_curated_fallback_as_full_universe(monkeypatch) -> None:
    from scanner import market_scanner

    source_status = {
        "NSE": {
            "origin": "curated",
            "source": "curated fallback",
            "official_source_status": "source unavailable",
            "source_symbols": 0,
            "reason": "connection timeout",
        },
    }
    monkeypatch.setattr(market_scanner, "dynamic_nse_symbols", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "universe_source_status", lambda: source_status)
    observed = {}

    def fake_screen(candidates, coverage=None):
        observed.update(candidates)
        return []

    monkeypatch.setattr(market_scanner, "_batch_change_screen", fake_screen)

    result = market_scanner.market_scan("NSE", universe_mode="full")

    assert result.empty
    assert observed == {"NSE": []}
    assert result.attrs["scanner_coverage"]["NSE"]["candidates"] == 0
    assert result.attrs["scanner_coverage"]["NSE"]["source_reason"] == "connection timeout"



def test_five_minute_screen_rejects_stale_intraday_history(monkeypatch) -> None:
    from scanner import market_scanner

    now = pd.Timestamp.now(tz="Asia/Kolkata")
    stale_bar = now - pd.Timedelta(hours=1)
    history = pd.DataFrame(
        {
            "Open": [100.0, 101.0],
            "High": [101.0, 102.0],
            "Low": [99.0, 100.0],
            "Close": [100.0, 101.0],
            "Volume": [1000.0, 1100.0],
        },
        index=[stale_bar - pd.Timedelta(minutes=5), stale_bar],
    )
    monkeypatch.setattr(
        market_scanner,
        "_download_chunk",
        lambda _chunk, interval="1d": history,
    )
    coverage = {"NSE": {}}

    movers = market_scanner._batch_change_screen(
        {"NSE": ["RELIANCE"]},
        coverage,
        interval="5m",
    )

    assert movers == []
    assert coverage["NSE"]["stale_histories"] == 1
    assert "latest_bar_at" not in coverage["NSE"]
