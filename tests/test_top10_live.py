from zoneinfo import ZoneInfo

from components.top10_live import (
    TOP10_CACHE_SECONDS,
    TOP10_CHUNK_SIZE,
    TOP10_REFRESH_SECONDS,
    TOP10_TIMEZONE,
    show_live_top10_scanner,
)


def test_top10_live_scanner_refreshes_every_minute() -> None:
    assert TOP10_REFRESH_SECONDS == 60
    assert TOP10_CACHE_SECONDS < TOP10_REFRESH_SECONDS
    assert TOP10_CHUNK_SIZE == 10
    assert callable(show_live_top10_scanner)


def test_top10_live_uses_india_timezone() -> None:
    assert TOP10_TIMEZONE == "Asia/Kolkata"
    assert ZoneInfo(TOP10_TIMEZONE).key == "Asia/Kolkata"
