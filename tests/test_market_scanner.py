import pandas as pd

from scanner.market_scanner import _extract_series, _yahoo_ticker


def test_extract_series_supports_ticker_first_columns() -> None:
    columns = pd.MultiIndex.from_product([["RELIANCE.NS"], ["Close", "Volume"]])
    frame = pd.DataFrame([[100.0, 1_000_000]], columns=columns)

    assert _extract_series(frame, "RELIANCE.NS", "Close").tolist() == [100.0]


def test_extract_series_supports_field_first_columns() -> None:
    columns = pd.MultiIndex.from_product([["Close", "Volume"], ["RELIANCE.NS"]])
    frame = pd.DataFrame([[100.0, 1_000_000]], columns=columns)

    assert _extract_series(frame, "RELIANCE.NS", "Volume").tolist() == [1_000_000]


def test_market_scan_uses_only_requested_exchange(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []
    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: ["500325"])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates, coverage=None: calls.append(candidates) or [],
    )

    result = market_scanner.market_scan("BSE")

    assert result.empty
    assert calls == [{"BSE": ["500325"]}]


def test_market_scan_includes_both_exchanges_by_default(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []
    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: ["500325"])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates, coverage=None: calls.append(candidates) or [],
    )

    result = market_scanner.market_scan()

    assert result.empty
    assert calls == [{"NSE": ["RELIANCE"], "BSE": ["500325"]}]


def test_bse_candidates_follow_selected_nse_cap_basket() -> None:
    from scanner.universe import bse_candidates_for_nse_symbols

    selected = {"RELIANCE", "TCS", "NOT_IN_CURATED_UNIVERSE"}

    assert bse_candidates_for_nse_symbols(selected) == ["500325", "532540"]


def test_day_trader_cap_filter_includes_bse_candidates() -> None:
    from scanner.day_trader_opportunity import select_day_trader_universe

    selected = select_day_trader_universe("Large cap", "BSE")

    assert ("500325", "BSE") in selected
    assert ("532540", "BSE") in selected
    assert all(exchange == "BSE" for _symbol, exchange in selected)


def test_market_scan_reports_per_exchange_coverage_when_no_movers(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: ["500325"])
    monkeypatch.setattr(
        market_scanner, "_batch_change_screen", lambda candidates, coverage=None: []
    )

    result = market_scanner.market_scan("BSE")

    assert result.empty
    assert result.attrs["scanner_coverage"] == {
        "BSE": {
            "candidates": 1,
            "tickers_requested": 0,
            "mapped_tickers": 0,
            "unmapped_symbols": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
            "histories_returned": 0,
            "histories_rejected": 0,
            "history_coverage_pct": 0.0,
            "analysis_download_failed": 0,
            "stale_data_rejected": 0,
            "unknown_timestamp_rejected": 0,
            "future_timestamp_rejected": 0,
            "analyses_completed": 0,
            "final_rows": 0,
            "cached_failures_skipped": 0,
        }
    }


def test_format_last_data_date_returns_iso_date_for_datetime_index() -> None:
    from scanner.market_scanner import _format_last_data_date

    index = pd.DatetimeIndex(["2026-10-16", "2026-10-19"])

    assert _format_last_data_date(index) == "2026-10-19"


def test_format_last_data_date_does_not_invent_date_for_unknown_index() -> None:
    from scanner.market_scanner import _format_last_data_date

    assert _format_last_data_date(pd.RangeIndex(2)) == "UNKNOWN"
    assert _format_last_data_date(pd.DatetimeIndex([])) == "UNKNOWN"


def test_watchlist_observation_columns_distinguish_daily_quote_from_tick_live() -> None:
    from scanner.watchlist_scanner import _observation_columns

    columns = _observation_columns(
        {
            "price": 123.45,
            "observed_at": "2026-10-19T11:59:00+05:30",
            "frequency": "intraday_1m",
            "session_status": "INTRADAY DATA · TODAY",
            "is_tick_live": False,
        }
    )

    assert columns["Latest Observation Price"] == 123.45
    assert columns["Observed At"] == "2026-10-19T11:59:00+05:30"
    assert columns["Observation Frequency"] == "intraday_1m"
    assert columns["Observation Status"] == "INTRADAY DATA · TODAY"
    assert columns["Tick Live"] is False


def test_watchlist_observation_columns_fail_closed_when_observation_missing() -> None:
    from scanner.watchlist_scanner import _observation_columns

    columns = _observation_columns(None)

    assert columns["Latest Observation Price"] is None
    assert columns["Observed At"] == "UNKNOWN"
    assert columns["Observation Frequency"] == "unknown"
    assert columns["Observation Status"] == "MARKET DATA STATUS UNAVAILABLE"
    assert columns["Tick Live"] is False


def test_batch_change_screen_counts_returned_histories_not_only_movers(monkeypatch) -> None:
    from scanner import market_scanner

    columns = pd.MultiIndex.from_product([["RELIANCE.NS"], ["Close", "Volume"]])
    history = pd.DataFrame(
        [[100.0, 1000], [101.0, 1100]],
        index=pd.DatetimeIndex(["2026-10-16", "2026-10-19"]),
        columns=columns,
    )
    coverage = {
        "NSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }
    monkeypatch.setattr(market_scanner, "_download_chunk", lambda chunk: history)

    movers = market_scanner._batch_change_screen({"NSE": ["RELIANCE"]}, coverage=coverage)

    assert len(movers) == 1
    assert coverage["NSE"]["histories_returned"] == 1


def test_batch_change_screen_does_not_count_history_with_too_few_candles(
    monkeypatch,
) -> None:
    from scanner import market_scanner

    columns = pd.MultiIndex.from_product([["500325.BO"], ["Close", "Volume"]])
    history = pd.DataFrame(
        [[100.0, 1000]],
        index=pd.DatetimeIndex(["2026-10-19"]),
        columns=columns,
    )
    coverage = {
        "BSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }
    monkeypatch.setattr(market_scanner, "_yahoo_ticker", lambda symbol, exchange: f"{symbol}.BO")
    monkeypatch.setattr(market_scanner, "_download_chunk", lambda chunk: history)

    movers = market_scanner._batch_change_screen({"BSE": ["500325"]}, coverage=coverage)

    assert movers == []
    assert coverage["BSE"]["histories_returned"] == 0
    assert coverage["BSE"]["screen_tickers_missing_data"] == 1


def test_batch_change_screen_retries_empty_batches_as_smaller_chunks(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []

    def download(chunk):
        calls.append(chunk)
        if len(chunk) > 5:
            return pd.DataFrame()
        columns = pd.MultiIndex.from_product([chunk, ["Close", "Volume"]])
        values = []
        for row in range(2):
            values.append(
                [
                    value
                    for ticker in chunk
                    for value in (
                        (100.0 if ticker.endswith("0.NS") else 200.0) * (1 + 0.01 * row),
                        1000 + row * 200,
                    )
                ]
            )
        return pd.DataFrame(
            values,
            index=pd.DatetimeIndex(["2026-10-16", "2026-10-19"]),
            columns=columns,
        )

    symbols = [f"AAA{i}" for i in range(6)]
    coverage = {
        "NSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }
    monkeypatch.setattr(market_scanner, "_download_chunk", download)

    movers = market_scanner._batch_change_screen({"NSE": symbols}, coverage=coverage)

    assert len(movers) == 6
    assert len(calls[0]) == 6
    assert sorted(map(len, calls[1:])) == [3, 3]
    assert coverage["NSE"]["screen_chunks_requested"] == 3
    assert coverage["NSE"]["screen_chunks_empty"] == 1
    assert coverage["NSE"]["screen_tickers_with_data"] == 6
    assert coverage["NSE"]["screen_tickers_missing_data"] == 0


def test_yahoo_ticker_maps_current_nse_symbols() -> None:
    assert _yahoo_ticker("ZOMATO", "NSE") == "ETERNAL.NS"
    assert _yahoo_ticker("TATAMOTORS", "NSE") == "TMPV.NS"
    assert _yahoo_ticker("RELIANCE", "NSE") == "RELIANCE.NS"


def test_yahoo_ticker_maps_bse_codes(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(
        market_scanner,
        "yahoo_symbol_for_bse_code",
        lambda code: {"500325": "RELIANCE", "532540": "TCS"}.get(code),
    )

    assert _yahoo_ticker("500325", "BSE") == "RELIANCE.BO"
    assert _yahoo_ticker("532540", "BSE") == "TCS.BO"
    assert _yahoo_ticker("999999", "BSE") is None
    assert _yahoo_ticker("RELIANCE", "OTHER") is None


def test_batch_change_screen_stops_splitting_after_repeated_bse_failures(
    monkeypatch,
) -> None:
    from scanner import market_scanner

    calls = []

    def download(chunk):
        calls.append(chunk)
        return pd.DataFrame()

    symbols = [f"{code:06d}" for code in range(500000, 500100)]
    coverage = {
        "BSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }

    monkeypatch.setattr(market_scanner, "_yahoo_ticker", lambda symbol, exchange: f"{symbol}.BO")
    monkeypatch.setattr(market_scanner, "_download_chunk", download)

    movers = market_scanner._batch_change_screen({"BSE": symbols}, coverage=coverage)

    assert movers == []
    assert len(calls) == 3
    assert len(calls[0]) == 100
    assert sorted(len(chunk) for chunk in calls[1:]) == [50, 50]
    assert coverage["BSE"]["screen_chunks_empty"] == 3
    assert coverage["BSE"]["screen_tickers_missing_data"] == 100


def test_bse_ticker_mapping_falls_back_to_scrip_code_when_live_map_unavailable(monkeypatch) -> None:
    from scanner import dynamic_universe

    monkeypatch.setattr(dynamic_universe, "_bse_yahoo_symbol_map", {})

    assert dynamic_universe.yahoo_symbol_for_bse_code("500325") == "RELIANCE"


def test_bse_ticker_mapping_prefers_live_symbol_map(monkeypatch) -> None:
    from scanner import dynamic_universe

    monkeypatch.setattr(dynamic_universe, "_bse_yahoo_symbol_map", {"500325": "RELIANCE"})

    assert dynamic_universe.yahoo_symbol_for_bse_code("500325") == "RELIANCE"


def test_bse_ticker_mapping_rejects_invalid_unmapped_codes(monkeypatch) -> None:
    from scanner import dynamic_universe

    monkeypatch.setattr(dynamic_universe, "_bse_yahoo_symbol_map", {})

    assert dynamic_universe.yahoo_symbol_for_bse_code("RELIANCE") is None
    assert dynamic_universe.yahoo_symbol_for_bse_code("12345") is None


def test_batch_change_screen_counts_only_usable_two_candle_history(monkeypatch) -> None:
    from scanner import market_scanner

    ticker = "RELIANCE.NS"
    columns = pd.MultiIndex.from_product([[ticker], ["Close", "Volume"]])
    one_candle = pd.DataFrame(
        [[100.0, 1000]],
        index=pd.DatetimeIndex(["2026-10-19"]),
        columns=columns,
    )
    coverage = {
        "NSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }
    monkeypatch.setattr(market_scanner, "_download_chunk", lambda chunk: one_candle)
    monkeypatch.setattr(market_scanner, "_failed_tickers_until", {})

    assert market_scanner._batch_change_screen({"NSE": ["RELIANCE"]}, coverage=coverage) == []
    assert coverage["NSE"]["histories_returned"] == 0
    assert coverage["NSE"]["screen_tickers_with_data"] == 0
    assert coverage["NSE"]["screen_tickers_missing_data"] == 1


def test_daily_data_status_handles_fresh_stale_unknown_and_future_dates() -> None:
    from datetime import date

    from scanner.market_scanner import _daily_data_status

    assert _daily_data_status(pd.DatetimeIndex(["2026-10-23"]), date(2026, 10, 25)) == "FRESH"
    assert _daily_data_status(pd.DatetimeIndex(["2026-10-10"]), date(2026, 10, 25)) == "STALE"
    assert _daily_data_status(pd.RangeIndex(2), date(2026, 10, 25)) == "UNKNOWN"
    assert _daily_data_status(pd.DatetimeIndex(["2026-10-26"]), date(2026, 10, 25)) == "FUTURE DATE"


def test_market_scan_rejects_stale_analysis_history(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: [])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates, coverage=None: [("RELIANCE.NS", "NSE", 1.0, 1_000_000.0)],
    )
    dates = pd.date_range(end="2026-10-01", periods=60, freq="B")
    columns = pd.MultiIndex.from_product(
        [["RELIANCE.NS"], ["Open", "High", "Low", "Close", "Volume"]]
    )
    values = [[100.0, 102.0, 98.0, 101.0, 100_000.0] for _ in dates]
    history = pd.DataFrame(values, index=dates, columns=columns)
    monkeypatch.setattr(market_scanner, "_download_analysis_chunk", lambda tickers: history)

    result = market_scanner.market_scan("NSE")

    assert result.empty
    assert result.attrs["scanner_coverage"]["NSE"]["stale_data_rejected"] == 1
    assert result.attrs["scanner_coverage"]["NSE"]["analyses_completed"] == 0


def _failing_download(*_args, **_kwargs):
    raise RuntimeError("provider unavailable")


def test_download_chunk_logs_provider_failure_and_returns_empty(monkeypatch, caplog) -> None:
    import logging

    from scanner import market_scanner

    def failing_shared_download(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(market_scanner, "download_symbol_frames", failing_shared_download)

    with caplog.at_level(logging.DEBUG, logger=market_scanner.logger.name):
        result = market_scanner._download_chunk(["AAA.NS", "BBB.NS"])

    assert result.empty
    messages = [record.getMessage() for record in caplog.records]
    assert any("provider unavailable" in message for message in messages)
    assert any(record.levelno == logging.WARNING for record in caplog.records)


def test_download_analysis_chunk_logs_provider_failure_and_returns_empty(
    monkeypatch, caplog
) -> None:
    import logging

    from scanner import market_scanner

    def failing_shared_download(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(market_scanner, "download_symbol_frames", failing_shared_download)

    with caplog.at_level(logging.DEBUG, logger=market_scanner.logger.name):
        result = market_scanner._download_analysis_chunk(["AAA.NS"])

    assert result.empty
    assert any(
        record.levelno == logging.WARNING and "provider unavailable" in record.getMessage()
        for record in caplog.records
    )


def test_broad_market_screen_uses_larger_batches_and_reports_progress(monkeypatch) -> None:
    from scanner import market_scanner

    symbols = [f"AAA{i}" for i in range(205)]
    calls = []
    progress = []

    def download(chunk):
        calls.append(len(chunk))
        columns = pd.MultiIndex.from_product([chunk, ["Close", "Volume"]])
        values = [
            [value for _ticker in chunk for value in (100.0, 1000.0)],
            [value for _ticker in chunk for value in (101.0, 1200.0)],
        ]
        return pd.DataFrame(
            values,
            index=pd.DatetimeIndex(["2026-10-16", "2026-10-19"]),
            columns=columns,
        )

    monkeypatch.setattr(market_scanner, "_yahoo_ticker", lambda symbol, exchange: f"{symbol}.NS")
    monkeypatch.setattr(market_scanner, "_download_chunk", download)
    coverage = {
        "NSE": {
            "tickers_requested": 0,
            "mapped_tickers": 0,
            "unmapped_symbols": 0,
            "cached_failures_skipped": 0,
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }

    movers = market_scanner._batch_change_screen(
        {"NSE": symbols},
        coverage=coverage,
        progress_callback=lambda exchange, completed, total: progress.append(
            (exchange, completed, total)
        ),
    )

    assert sorted(calls) == [5, 100, 100]
    assert len(movers) == 205
    assert coverage["NSE"]["screen_chunks_requested"] == 3
    assert coverage["NSE"]["histories_returned"] == 205
    assert len(progress) == 3
    assert all(exchange == "NSE" and total == 3 for exchange, _done, total in progress)


def test_market_scan_records_resource_diagnostics_when_no_movers(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(market_scanner, "merge_nse_universe", lambda: ["RELIANCE"])
    monkeypatch.setattr(market_scanner, "merge_bse_universe", lambda: [])
    monkeypatch.setattr(
        market_scanner,
        "_batch_change_screen",
        lambda candidates, coverage=None: [],
    )

    result = market_scanner.market_scan("NSE")
    timings = result.attrs["scanner_timings"]

    assert timings["screen_workers"] == 2
    assert timings["download_chunk_size"] == 100
    assert timings["cpu_seconds"] >= 0
    assert timings["total_seconds"] >= 0


def test_analysis_shortlist_uses_full_limit_for_single_exchange():
    from scanner.market_scanner import _select_analysis_tickers

    movers = [(f"{index}.NS", "NSE", 5.0 - index / 100, 1000.0) for index in range(30)]

    selected = _select_analysis_tickers(movers, ["NSE"], 20)

    assert len(selected) == 20
    assert selected == [f"{index}.NS" for index in range(20)]


def test_analysis_shortlist_balances_both_exchanges():
    from scanner.market_scanner import _select_analysis_tickers

    movers = [(f"N{index}.NS", "NSE", 10.0 - index / 100, 1000.0) for index in range(20)] + [
        (f"B{index}.BO", "BSE", 9.0 - index / 100, 1000.0) for index in range(20)
    ]

    selected = _select_analysis_tickers(movers, ["NSE", "BSE"], 20)

    assert len(selected) == 20
    assert sum(ticker.endswith(".NS") for ticker in selected) == 10
    assert sum(ticker.endswith(".BO") for ticker in selected) == 10


def test_analysis_shortlist_fills_unused_exchange_quota():
    from scanner.market_scanner import _select_analysis_tickers

    movers = [(f"N{index}.NS", "NSE", 10.0 - index / 100, 1000.0) for index in range(3)] + [
        (f"B{index}.BO", "BSE", 9.0 - index / 100, 1000.0) for index in range(20)
    ]

    selected = _select_analysis_tickers(movers, ["NSE", "BSE"], 20)

    assert len(selected) == 20
    assert sum(ticker.endswith(".NS") for ticker in selected) == 3
    assert sum(ticker.endswith(".BO") for ticker in selected) == 17


def test_analysis_shortlist_rejects_invalid_limits():
    from scanner.market_scanner import _select_analysis_tickers

    assert _select_analysis_tickers([], ["NSE"], 0) == []


def test_analyze_history_frame_does_not_extract_batch_history_again(monkeypatch) -> None:
    from scanner import market_scanner

    def unexpected_extract(*args, **kwargs):
        raise AssertionError("already-extracted ticker frame must not be sliced again")

    monkeypatch.setattr(market_scanner, "_extract_history_frame", unexpected_extract)

    result = market_scanner._analyze_history_frame(
        "RELIANCE.NS",
        pd.DataFrame({"Close": [100.0], "Volume": [1000]}),
    )

    assert result is None

def test_broad_market_download_uses_shared_service_and_preserves_ticker_columns(monkeypatch) -> None:
    from scanner import market_scanner

    calls = []
    index = pd.DatetimeIndex(["2026-11-09", "2026-11-10"])
    frames = {
        "RELIANCE.NS": pd.DataFrame(
            {"Open": [100.0, 101.0], "High": [102.0, 103.0], "Low": [99.0, 100.0],
             "Close": [101.0, 102.0], "Volume": [1000, 1100]}, index=index
        ),
        "TCS.NS": pd.DataFrame(
            {"Open": [200.0, 201.0], "High": [202.0, 203.0], "Low": [199.0, 200.0],
             "Close": [201.0, 202.0], "Volume": [2000, 2100]}, index=index
        ),
    }

    def shared_download(tickers, **kwargs):
        calls.append((tickers, kwargs))
        return frames, []

    monkeypatch.setattr(market_scanner, "download_symbol_frames", shared_download)

    history = market_scanner._download_chunk(list(frames))

    assert calls[0][0] == list(frames)
    assert calls[0][1]["interval"] == "1d"
    assert calls[0][1]["recover_missing"] is True
    assert isinstance(history.columns, pd.MultiIndex)
    assert set(history.columns.get_level_values(0)) == set(frames)
    assert market_scanner._extract_series(history, "RELIANCE.NS", "Close").tolist() == [101.0, 102.0]


def test_broad_market_download_returns_empty_frame_when_all_history_missing(monkeypatch) -> None:
    from scanner import market_scanner

    monkeypatch.setattr(
        market_scanner,
        "download_symbol_frames",
        lambda tickers, **kwargs: ({}, list(tickers)),
    )

    assert market_scanner._download_analysis_chunk(["MISSING.NS"]).empty

