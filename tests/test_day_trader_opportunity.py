import pandas as pd

from scanner.day_trader_opportunity import (
    _candle_settings,
    _ticker,
    scan_has_provider_data,
    score_opportunity_rows,
    select_day_trader_universe,
    summarize_day_trading_setup,
)


def test_score_ranks_volume_momentum_breakout():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "A",
                "5-min change %": 2.0,
                "Volume surge x": 3.0,
                "Session range %": 4.0,
                "Breakout": "YES",
                "Low-price flag": "YES",
            },
            {
                "Symbol": "B",
                "5-min change %": 0.5,
                "Volume surge x": 1.2,
                "Session range %": 1.0,
                "Breakout": "—",
                "Low-price flag": "—",
            },
        ]
    )

    result = score_opportunity_rows(rows)

    assert result.iloc[0]["Symbol"] == "A"
    assert result.iloc[0]["Opportunity score"] == 100.0
    assert result.iloc[0]["Setup"] == "Low-price bullish volume watch"


def test_score_handles_empty_input():
    result = score_opportunity_rows(pd.DataFrame())

    assert result.empty


def test_safety_filter_removes_known_flags_only():
    from scanner.surveillance import apply_safety_filter

    candidates = pd.DataFrame(
        [
            {"Symbol": "SAFE", "Exchange": "NSE"},
            {"Symbol": "FLAGGED", "Exchange": "NSE"},
            {"Symbol": "BSE1", "Exchange": "BSE"},
        ]
    )
    safety = pd.DataFrame(
        [
            {
                "Symbol": "SAFE",
                "Safety flags": "",
                "Safety status": "NSE check clear",
            },
            {
                "Symbol": "FLAGGED",
                "Safety flags": "ASM: 11",
                "Safety status": "Flagged - review before trading",
            },
        ]
    )

    result = apply_safety_filter(candidates, safety, exclude_flagged=True)

    assert result["Symbol"].tolist() == ["SAFE", "BSE1"]
    assert result.loc[result["Symbol"].eq("BSE1"), "Safety status"].iloc[0] == (
        "Manual check required"
    )


def test_liquidity_warning():
    from scanner.surveillance import liquidity_warning

    assert liquidity_warning(4.0, 200_000) == "Low recent traded value"
    assert liquidity_warning(10.0, 100_000) == "Low recent traded value"
    assert liquidity_warning(20.0, 100_000) == "OK"


def test_universe_filters_exchange_and_cap_basket():
    large_nse = select_day_trader_universe("Large cap", "NSE")
    assert large_nse
    assert all(exchange == "NSE" for _, exchange in large_nse)
    assert "RELIANCE" in {symbol for symbol, _ in large_nse}
    assert "IRFC" not in {symbol for symbol, _ in large_nse}

    mid_both = select_day_trader_universe("Mid cap", "Both")
    assert mid_both
    assert {exchange for _, exchange in mid_both} == {"NSE", "BSE"}
    assert "IRFC" in {symbol for symbol, exchange in mid_both if exchange == "NSE"}


def test_universe_rejects_unknown_filters():
    assert select_day_trader_universe("Unknown cap", "Both") == []


def test_candle_settings_use_five_minute_for_default_scan():
    assert _candle_settings(5) == ("5m", 1)


def test_candle_settings_keep_fine_windows_on_one_minute_data():
    assert _candle_settings(2) == ("1m", 2)
    assert _candle_settings(3) == ("1m", 3)


def test_all_caps_uses_complete_dynamic_exchange_universe(monkeypatch):
    import scanner.day_trader_opportunity as scanner

    monkeypatch.setattr(scanner, "merge_nse_universe", lambda: ["RELIANCE", "MIDCAP1", "SMALLCAP1"])
    monkeypatch.setattr(scanner, "merge_bse_universe", lambda: ["500325", "540000", "590000"])

    universe = select_day_trader_universe("All caps", "Both")

    assert len(universe) == 6
    assert ("RELIANCE", "NSE") in universe
    assert ("MIDCAP1", "NSE") in universe
    assert ("SMALLCAP1", "NSE") in universe
    assert ("540000", "BSE") in universe
    assert ("590000", "BSE") in universe
    assert select_day_trader_universe("All caps", "NSE") == [
        ("MIDCAP1", "NSE"),
        ("RELIANCE", "NSE"),
        ("SMALLCAP1", "NSE"),
    ]


def test_score_combines_opportunity_and_setup_scores():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "SETUP",
                "5-min change %": 2.0,
                "Volume surge x": 2.0,
                "Session range %": 2.0,
                "Breakout": "YES",
                "Low-price flag": "—",
                "Setup score": 80,
            }
        ]
    )

    result = score_opportunity_rows(rows)

    assert result.iloc[0]["Opportunity score"] == 75.0
    assert result.iloc[0]["Composite score"] == 77.0


def test_setup_evidence_reports_direction_and_confirmations():
    result = summarize_day_trading_setup(
        {
            "Long setup score": 80,
            "Short setup score": 35,
            "Trend": "UPTREND",
            "VWAP relation": "ABOVE",
            "EMA 9/20": "BULLISH",
            "RVOL": 2.1,
            "Breakout": "YES",
            "Breakdown": "NO",
        }
    )

    assert result["Direction"] == "LONG"
    assert result["Setup state"] == "LONG SETUP WATCH"
    assert "UPTREND" in result["Evidence"]
    assert "VWAP ABOVE" in result["Evidence"]
    assert "EMA BULLISH" in result["Evidence"]
    assert "RVOL CONFIRMED" in result["Evidence"]
    assert "BREAKOUT" in result["Evidence"]


def test_setup_evidence_marks_weak_context():
    result = summarize_day_trading_setup(
        {
            "Long setup score": 45,
            "Short setup score": 40,
            "Trend": "MIXED",
            "VWAP relation": "ABOVE",
            "EMA 9/20": "BULLISH",
            "RVOL": 0.9,
            "Breakout": "NO",
            "Breakdown": "NO",
        }
    )

    assert result["Direction"] == "LONG"
    assert result["Setup state"] == "CONTEXT ONLY"
    assert "No strong confirmation" not in result["Evidence"]


def test_day_trade_plan_long_references():
    from scanner.day_trading_strategy import calculate_day_trade_plan

    result = calculate_day_trade_plan(
        {
            "Long setup score": 80,
            "Short setup score": 30,
            "Close": 100.0,
            "ATR 14": 2.0,
            "Support": 98.0,
            "Resistance": 101.0,
        }
    )

    assert result["Plan"] == "LONG reference plan"
    assert result["Entry reference"] == 101.0
    assert result["Stop reference"] == 98.0
    assert result["Target 1"] == 104.0
    assert result["Target 2"] == 107.0
    assert result["Target 3"] == 110.0
    assert result["R:R T1"] == 1.0
    assert result["R:R T3"] == 3.0


def test_day_trade_plan_short_references():
    from scanner.day_trading_strategy import calculate_day_trade_plan

    result = calculate_day_trade_plan(
        {
            "Long setup score": 30,
            "Short setup score": 80,
            "Close": 100.0,
            "ATR 14": 2.0,
            "Support": 99.0,
            "Resistance": 102.0,
        }
    )

    assert result["Plan"] == "SHORT reference plan"
    assert result["Entry reference"] == 99.0
    assert result["Stop reference"] == 102.0
    assert result["Target 1"] == 96.0
    assert result["Target 3"] == 90.0


def test_day_trade_plan_rejects_neutral_direction():
    from scanner.day_trading_strategy import calculate_day_trade_plan

    result = calculate_day_trade_plan(
        {
            "Long setup score": 50,
            "Short setup score": 50,
            "Close": 100.0,
            "ATR 14": 2.0,
            "Support": 98.0,
            "Resistance": 102.0,
        }
    )

    assert result["Plan"] == "NO CLEAR DIRECTION"
    assert result["Entry reference"] is None


def test_day_trade_plan_state_waiting_long():
    from scanner.day_trading_strategy import classify_day_trade_plan_state

    state = classify_day_trade_plan_state(
        {"Close": 100.0},
        {
            "Plan": "LONG reference plan",
            "Entry reference": 101.0,
            "Stop reference": 98.0,
        },
    )
    assert state == "WAITING FOR REFERENCE"


def test_day_trade_plan_state_triggered_short():
    from scanner.day_trading_strategy import classify_day_trade_plan_state

    state = classify_day_trade_plan_state(
        {"Close": 98.0},
        {
            "Plan": "SHORT reference plan",
            "Entry reference": 99.0,
            "Stop reference": 102.0,
        },
    )
    assert state == "TRIGGERED / BELOW REFERENCE"


def test_day_trade_plan_state_invalidated():
    from scanner.day_trading_strategy import classify_day_trade_plan_state

    state = classify_day_trade_plan_state(
        {"Close": 97.0},
        {
            "Plan": "LONG reference plan",
            "Entry reference": 101.0,
            "Stop reference": 98.0,
        },
    )
    assert state == "INVALIDATED"


def test_ticker_resolves_bse_scrip_codes_to_yahoo_symbols(monkeypatch):
    import scanner.day_trader_opportunity as scanner

    monkeypatch.setattr(
        scanner,
        "yahoo_symbol_for_bse_code",
        lambda code: {"500325": "RELIANCE", "532540": "TCS"}.get(code),
    )

    assert _ticker("500325", "BSE") == "RELIANCE.BO"
    assert _ticker("532540", "BSE") == "TCS.BO"
    assert _ticker("999999", "BSE") is None
    assert _ticker("RELIANCE", "NSE") == "RELIANCE.NS"


def test_score_ranks_long_neutral_then_short_and_scores_downside():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "SHORT_STRONG",
                "Direction": "SHORT",
                "5-min change %": -2.0,
                "Volume surge x": 3.0,
                "Session range %": 4.0,
                "Breakout": "—",
                "Breakdown": "YES",
                "Low-price flag": "—",
                "Setup score": 90,
            },
            {
                "Symbol": "NEUTRAL",
                "Direction": "NEUTRAL",
                "5-min change %": 0.0,
                "Volume surge x": 1.0,
                "Session range %": 1.0,
                "Breakout": "—",
                "Breakdown": "—",
                "Low-price flag": "—",
                "Setup score": 20,
            },
            {
                "Symbol": "LONG_STRONG",
                "Direction": "LONG",
                "5-min change %": 2.0,
                "Volume surge x": 3.0,
                "Session range %": 4.0,
                "Breakout": "YES",
                "Breakdown": "—",
                "Low-price flag": "—",
                "Setup score": 90,
            },
        ]
    )

    result = score_opportunity_rows(rows)

    assert result["Symbol"].tolist() == ["LONG_STRONG", "NEUTRAL", "SHORT_STRONG"]
    assert result.loc[result["Symbol"].eq("SHORT_STRONG"), "Opportunity score"].iloc[0] == 100.0
    assert result.loc[result["Symbol"].eq("LONG_STRONG"), "Opportunity score"].iloc[0] == 100.0


def test_score_labels_bearish_momentum_and_breakdown():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "BEARISH_MOMENTUM",
                "Direction": "SHORT",
                "5-min change %": -1.2,
                "Volume surge x": 2.0,
                "Session range %": 2.0,
                "Breakout": "—",
                "Breakdown": "—",
                "Low-price flag": "—",
                "Setup score": 75,
            },
            {
                "Symbol": "BEARISH_BREAKDOWN",
                "Direction": "SHORT",
                "5-min change %": -0.4,
                "Volume surge x": 1.2,
                "Session range %": 2.0,
                "Breakout": "—",
                "Breakdown": "YES",
                "Low-price flag": "—",
                "Setup score": 80,
            },
        ]
    )

    result = score_opportunity_rows(rows).set_index("Symbol")

    assert result.loc["BEARISH_MOMENTUM", "Setup"] == "Bearish volume + momentum"
    assert result.loc["BEARISH_BREAKDOWN", "Setup"] == "Breakdown watch"


def test_coverage_diagnostics_distinguish_unmapped_and_unusable_symbols():
    from scanner.day_trader_opportunity import _add_coverage_diagnostics

    stats = _add_coverage_diagnostics(
        {
            "candidate_count": 100,
            "mapped_symbol_count": 80,
            "usable_data_count": 60,
        }
    )

    assert stats["no_usable_data_count"] == 20
    assert stats["data_coverage_pct"] == 60.0
    assert stats["universe_resolution_pct"] == 80.0
    assert stats["scan_completed"] is True


def test_coverage_diagnostics_handle_empty_universe():
    from scanner.day_trader_opportunity import _add_coverage_diagnostics

    stats = _add_coverage_diagnostics(
        {"candidate_count": 0, "mapped_symbol_count": 0, "usable_data_count": 0}
    )

    assert stats["data_coverage_pct"] == 0.0
    assert stats["universe_resolution_pct"] == 0.0
    assert stats["no_usable_data_count"] == 0


def test_chunk_download_retries_empty_response_then_succeeds(monkeypatch):
    import scanner.day_trader_opportunity as scanner

    calls = []
    expected = pd.DataFrame({"Close": [100.0]})

    def fake_download(**kwargs):
        calls.append(kwargs)
        return pd.DataFrame() if len(calls) == 1 else expected

    monkeypatch.setattr(scanner.yf, "download", fake_download)
    monkeypatch.setattr(scanner.time, "sleep", lambda _delay: None)

    result, attempts = scanner._download_chunk_with_retry(["ABC.NS"], "5m")

    assert result.equals(expected)
    assert attempts == 2
    assert len(calls) == 2
    assert calls[-1]["timeout"] == 15


def test_chunk_download_stops_after_bounded_failures(monkeypatch):
    import scanner.day_trader_opportunity as scanner

    calls = []

    def fake_download(**_kwargs):
        calls.append(True)
        raise TimeoutError("provider timeout")

    monkeypatch.setattr(scanner.yf, "download", fake_download)
    monkeypatch.setattr(scanner.time, "sleep", lambda _delay: None)

    result, attempts = scanner._download_chunk_with_retry(["ABC.NS"], "5m")

    assert result.empty
    assert attempts == scanner.CHUNK_DOWNLOAD_ATTEMPTS
    assert len(calls) == scanner.CHUNK_DOWNLOAD_ATTEMPTS


def test_scan_provider_data_contract_detects_all_failed_chunks():
    assert (
        scan_has_provider_data(
            {
                "mapped_symbol_count": 1200,
                "nonempty_chunks": 0,
                "download_failed_chunks": 12,
            }
        )
        is False
    )


def test_scan_provider_data_contract_accepts_partial_provider_success():
    assert (
        scan_has_provider_data(
            {
                "mapped_symbol_count": 1200,
                "nonempty_chunks": 1,
                "download_failed_chunks": 11,
            }
        )
        is True
    )


def test_scan_provider_data_contract_accepts_empty_mapped_universe():
    assert scan_has_provider_data(
        {
            "mapped_symbol_count": 0,
            "nonempty_chunks": 0,
            "download_failed_chunks": 0,
        }
    )


def test_scan_timing_diagnostics_are_rounded_and_non_negative():
    from scanner.day_trader_opportunity import _set_scan_timing_diagnostics

    stats = {}
    _set_scan_timing_diagnostics(
        stats,
        total_seconds=12.34567,
        download_seconds=8.76543,
        analysis_seconds=2.34567,
        safety_filter_seconds=1.23456,
    )

    assert stats == {
        "download_seconds": 8.765,
        "analysis_seconds": 2.346,
        "safety_filter_seconds": 1.235,
        "scan_duration_seconds": 12.346,
    }


def test_scan_timing_diagnostics_clamp_negative_clock_deltas():
    from scanner.day_trader_opportunity import _set_scan_timing_diagnostics

    stats = {}
    _set_scan_timing_diagnostics(
        stats,
        total_seconds=-1.0,
        download_seconds=-0.5,
        analysis_seconds=0.25,
        safety_filter_seconds=-0.1,
    )

    assert stats == {
        "download_seconds": 0.0,
        "analysis_seconds": 0.25,
        "safety_filter_seconds": 0.0,
        "scan_duration_seconds": 0.0,
    }


def test_exchange_diagnostics_track_mapping_chunks_and_usable_data(monkeypatch):
    import scanner.day_trader_opportunity as scanner

    monkeypatch.setattr(scanner, "merge_nse_universe", lambda: ["NSE_A", "NSE_B"])
    monkeypatch.setattr(scanner, "merge_bse_universe", lambda: ["500001"])
    monkeypatch.setattr(scanner, "yahoo_symbol_for_bse_code", lambda _code: None)

    universe = scanner.select_day_trader_universe("All caps", "Both")
    assert len(universe) == 3
    nse_symbols = [symbol for symbol, exchange in universe if exchange == "NSE"]
    bse_symbols = [symbol for symbol, exchange in universe if exchange == "BSE"]
    assert len(nse_symbols) == 2
    assert len(bse_symbols) == 1
