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
            "analysis_download_failed": 0,
            "analyses_completed": 0,
            "final_rows": 0,
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


def test_batch_change_screen_counts_history_even_when_not_enough_closes(
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
    assert coverage["BSE"]["histories_returned"] == 1


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

    symbols = [f"{code:06d}" for code in range(500000, 500040)]
    coverage = {
        "BSE": {
            "histories_returned": 0,
            "screen_chunks_requested": 0,
            "screen_chunks_empty": 0,
            "screen_tickers_with_data": 0,
            "screen_tickers_missing_data": 0,
        }
    }

    monkeypatch.setattr(
        market_scanner, "_yahoo_ticker", lambda symbol, exchange: f"{symbol}.BO"
    )
    monkeypatch.setattr(market_scanner, "_download_chunk", download)

    movers = market_scanner._batch_change_screen({"BSE": symbols}, coverage=coverage)

    assert movers == []
    assert len(calls) == 3
    assert len(calls[0]) == 40
    assert sorted(len(chunk) for chunk in calls[1:]) == [20, 20]
    assert coverage["BSE"]["screen_chunks_empty"] == 3
    assert coverage["BSE"]["screen_tickers_missing_data"] == 40
