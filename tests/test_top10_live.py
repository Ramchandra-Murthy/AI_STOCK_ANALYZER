from zoneinfo import ZoneInfo

import pandas as pd

from components.top10_live import (
    TOP10_CACHE_SECONDS,
    TOP10_CHUNK_SIZE,
    TOP10_COVERAGE_KEY,
    TOP10_EXPECTED_QUOTES,
    TOP10_GOOD_COVERAGE_QUOTES,
    TOP10_MARKET_CLOSE_HOUR,
    TOP10_MARKET_CLOSE_MINUTE,
    TOP10_MARKET_OPEN_HOUR,
    TOP10_MARKET_OPEN_MINUTE,
    TOP10_MAX_CANDIDATES_PER_EXCHANGE,
    TOP10_MAX_CONSECUTIVE_FAILURES,
    TOP10_PARTIAL_FAILURES_KEY,
    TOP10_REDUCED_COVERAGE_QUOTES,
    TOP10_REFRESH_SECONDS,
    TOP10_SCAN_WARNING_SECONDS,
    TOP10_SESSION_STATUS_KEY,
    TOP10_SIGNAL_HISTORY_LIMIT,
    TOP10_SIGNAL_HISTORY_KEY,
    TOP10_STALE_DATA_SECONDS,
    TOP10_TIMEZONE,
    _add_signal_strength,
    _annotate_watchlist_changes,
    _calculate_signal_strength,
    _add_signal_history,
    _coverage_status,
    _scan_live_top10,
    _start_background_scan,
    _watchlist_change_alerts,
    show_live_top10_scanner,
)


def test_top10_live_scanner_refreshes_every_minute() -> None:
    assert TOP10_REFRESH_SECONDS == 60
    assert TOP10_CACHE_SECONDS < TOP10_REFRESH_SECONDS
    assert TOP10_CHUNK_SIZE == 10
    assert TOP10_MAX_CANDIDATES_PER_EXCHANGE == 20
    assert TOP10_MAX_CONSECUTIVE_FAILURES == 2
    assert 0 < TOP10_SCAN_WARNING_SECONDS < TOP10_STALE_DATA_SECONDS
    assert TOP10_STALE_DATA_SECONDS >= 3 * TOP10_REFRESH_SECONDS
    assert callable(show_live_top10_scanner)
    assert callable(_scan_live_top10)
    assert callable(_start_background_scan)
    assert "REFRESHING" in open("components/top10_live.py", encoding="utf-8").read()
    assert "FRESH" in open("components/top10_live.py", encoding="utf-8").read()


def test_top10_live_uses_india_timezone() -> None:
    assert TOP10_TIMEZONE == "Asia/Kolkata"
    assert ZoneInfo(TOP10_TIMEZONE).key == "Asia/Kolkata"


def test_top10_live_refresh_starts_when_interval_is_due() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert "refresh_due" in source
    assert "now >= completed_at + timedelta" in source
    assert "seconds=TOP10_REFRESH_SECONDS" in source


def test_top10_market_session_hours() -> None:
    assert (TOP10_MARKET_OPEN_HOUR, TOP10_MARKET_OPEN_MINUTE) == (9, 15)
    assert (TOP10_MARKET_CLOSE_HOUR, TOP10_MARKET_CLOSE_MINUTE) == (15, 30)


def test_top10_live_session_status_key() -> None:
    assert TOP10_SESSION_STATUS_KEY == "top10_market_status"


def test_top10_live_tracks_data_freshness() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert "data_age_seconds" in source
    assert "STALE DATA" in source
    assert "st.session_state[TOP10_SESSION_STATUS_KEY]" in source


def test_top10_live_formats_candle_times_in_ist() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert "def _format_candle_time" in source
    assert "tz_convert(_IST)" in source
    assert "Last candle" in source


def test_top10_live_exposes_partial_provider_failures() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert TOP10_PARTIAL_FAILURES_KEY == "top10_partial_failures"
    assert "partial_failures" in source
    assert "PARTIAL PROVIDER ISSUE" in source
    assert "Provider failures" in source


def test_top10_live_exposes_quote_coverage() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert TOP10_COVERAGE_KEY == "top10_quote_coverage"
    assert "valid_quotes" in source
    assert "Quotes {valid_quotes}/" in source


def test_top10_live_classifies_quote_coverage_quality() -> None:
    assert TOP10_COVERAGE_KEY == "top10_quote_coverage"
    assert TOP10_EXPECTED_QUOTES == 40
    assert TOP10_GOOD_COVERAGE_QUOTES == 36
    assert TOP10_REDUCED_COVERAGE_QUOTES == 20
    assert _coverage_status(40) == "GOOD"
    assert _coverage_status(36) == "GOOD"
    assert _coverage_status(35) == "REDUCED"
    assert _coverage_status(20) == "REDUCED"
    assert _coverage_status(19) == "CRITICAL"
    assert _coverage_status(0) == "CRITICAL"


def test_top10_live_displays_coverage_quality() -> None:
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert "Coverage {coverage_status}" in source
    assert "CRITICAL QUOTE COVERAGE" in source
    assert "REDUCED QUOTE COVERAGE" in source


def test_top10_live_tracks_membership_and_rank_changes() -> None:
    previous = pd.DataFrame(
        [
            {"Rank": 1, "Symbol": "AAA", "Exchange": "NSE"},
            {"Rank": 2, "Symbol": "BBB", "Exchange": "NSE"},
        ]
    )
    current = pd.DataFrame(
        [
            {"Rank": 1, "Symbol": "BBB", "Exchange": "NSE"},
            {"Rank": 2, "Symbol": "CCC", "Exchange": "NSE"},
        ]
    )

    annotated, dropped = _annotate_watchlist_changes(current, previous)

    assert annotated[["Symbol", "Status", "Rank change"]].to_dict("records") == [
        {"Symbol": "BBB", "Status": "UP", "Rank change": 1},
        {"Symbol": "CCC", "Status": "NEW", "Rank change": None},
    ]
    assert dropped == ["NSE:AAA"]


def test_top10_live_first_scan_marks_all_symbols_new() -> None:
    current = pd.DataFrame(
        [
            {"Rank": 1, "Symbol": "AAA", "Exchange": "NSE"},
            {"Rank": 2, "Symbol": "BBB", "Exchange": "BSE"},
        ]
    )

    annotated, dropped = _annotate_watchlist_changes(current, None)

    assert annotated["Status"].tolist() == ["NEW", "NEW"]
    assert annotated["Rank change"].tolist() == [None, None]
    assert dropped == []


def test_top10_live_alerts_material_watchlist_changes() -> None:
    annotated = pd.DataFrame(
        [
            {
                "Rank": 1,
                "Symbol": "AAA",
                "Exchange": "NSE",
                "Status": "NEW",
                "Rank change": None,
                "1-min %": 1.25,
            },
            {
                "Rank": 2,
                "Symbol": "BBB",
                "Exchange": "NSE",
                "Status": "UP",
                "Rank change": 2,
                "1-min %": 0.2,
            },
            {
                "Rank": 3,
                "Symbol": "CCC",
                "Exchange": "BSE",
                "Status": "UNCHANGED",
                "Rank change": 0,
                "1-min %": 1.5,
            },
        ]
    )

    alerts = _watchlist_change_alerts(annotated)

    assert len(alerts) == 3
    assert "NEW · NSE:AAA" in alerts[0]
    assert "RANK UP · NSE:BBB · 2 places" in alerts[1]
    assert "MOVE · BSE:CCC · 1-min +1.50%" in alerts[2]


def test_top10_live_alerts_ignore_small_changes() -> None:
    annotated = pd.DataFrame(
        [
            {
                "Rank": 5,
                "Symbol": "AAA",
                "Exchange": "NSE",
                "Status": "UNCHANGED",
                "Rank change": 1,
                "1-min %": 0.4,
            }
        ]
    )

    assert _watchlist_change_alerts(annotated) == []


def test_top10_live_calculates_signal_strength() -> None:
    score, direction = _calculate_signal_strength(
        {
            "Status": "NEW",
            "Rank change": 2,
            "1-min %": 1.5,
            "5-min %": 3.0,
        }
    )

    assert score == 56
    assert direction == "UP"


def test_top10_live_signal_direction_handles_mixed_moves() -> None:
    score, direction = _calculate_signal_strength(
        {
            "Status": "UNCHANGED",
            "Rank change": 0,
            "1-min %": 1.0,
            "5-min %": -1.0,
        }
    )

    assert score == 19
    assert direction == "MIXED"


def test_top10_live_signal_history_tracks_score_and_direction_changes() -> None:
    previous = pd.DataFrame(
        [
            {
                "Symbol": "AAA",
                "Exchange": "NSE",
                "Momentum score": 40,
                "Direction": "UP",
            },
            {
                "Symbol": "BBB",
                "Exchange": "BSE",
                "Momentum score": 70,
                "Direction": "DOWN",
            },
        ]
    )
    current = pd.DataFrame(
        [
            {
                "Symbol": "AAA",
                "Exchange": "NSE",
                "Momentum score": 55,
                "Direction": "UP",
            },
            {
                "Symbol": "BBB",
                "Exchange": "BSE",
                "Momentum score": 60,
                "Direction": "UP",
            },
            {
                "Symbol": "CCC",
                "Exchange": "NSE",
                "Momentum score": 30,
                "Direction": "MIXED",
            },
        ]
    )

    enriched = _add_signal_history(current, [previous])

    assert enriched[["Symbol", "Previous score", "Score change", "Signal trend", "Direction change"]].to_dict("records") == [
        {"Symbol": "AAA", "Previous score": 40, "Score change": 15, "Signal trend": "STRENGTHENING", "Direction change": "UNCHANGED"},
        {"Symbol": "BBB", "Previous score": 70, "Score change": -10, "Signal trend": "WEAKENING", "Direction change": "DOWN→UP"},
        {"Symbol": "CCC", "Previous score": None, "Score change": None, "Signal trend": "NEW", "Direction change": "NEW"},
    ]


def test_top10_live_signal_history_is_limited_to_ten_scans() -> None:
    assert TOP10_SIGNAL_HISTORY_LIMIT == 10
    source = open("components/top10_live.py", encoding="utf-8").read()
    assert TOP10_SIGNAL_HISTORY_KEY == "top10_signal_history"
    assert "[-TOP10_SIGNAL_HISTORY_LIMIT:]" in source


def test_top10_live_adds_signal_columns() -> None:
    annotated = pd.DataFrame(
        [
            {
                "Rank": 1,
                "Symbol": "AAA",
                "Exchange": "NSE",
                "Status": "NEW",
                "Rank change": None,
                "1-min %": 1.0,
                "5-min %": 2.0,
            }
        ]
    )

    enriched = _add_signal_strength(annotated)

    assert enriched[["Momentum score", "Direction"]].to_dict("records") == [
        {"Momentum score": 35, "Direction": "UP"}
    ]
