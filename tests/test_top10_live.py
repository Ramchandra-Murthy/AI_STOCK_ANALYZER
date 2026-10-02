from zoneinfo import ZoneInfo

from components.top10_live import (
    TOP10_CACHE_SECONDS,
    TOP10_CHUNK_SIZE,
    TOP10_MARKET_CLOSE_HOUR,
    TOP10_MARKET_CLOSE_MINUTE,
    TOP10_MARKET_OPEN_HOUR,
    TOP10_MARKET_OPEN_MINUTE,
    TOP10_MAX_CANDIDATES_PER_EXCHANGE,
    TOP10_MAX_CONSECUTIVE_FAILURES,
    TOP10_REFRESH_SECONDS,
    TOP10_SCAN_WARNING_SECONDS,
    TOP10_SESSION_STATUS_KEY,
    TOP10_TIMEZONE,
    _scan_live_top10,
    _start_background_scan,
    show_live_top10_scanner,
)


def test_top10_live_scanner_refreshes_every_minute() -> None:
    assert TOP10_REFRESH_SECONDS == 60
    assert TOP10_CACHE_SECONDS < TOP10_REFRESH_SECONDS
    assert TOP10_CHUNK_SIZE == 10
    assert TOP10_MAX_CANDIDATES_PER_EXCHANGE == 20
    assert TOP10_MAX_CONSECUTIVE_FAILURES == 2
    assert 0 < TOP10_SCAN_WARNING_SECONDS < TOP10_REFRESH_SECONDS
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
