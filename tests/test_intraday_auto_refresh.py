"""Tests for controlled intraday dashboard auto-refresh."""

from datetime import datetime

from services.intraday_auto_refresh import (
    market_is_open,
    next_refresh_seconds,
    refresh_label,
    seconds_until_first_scan,
)


def test_market_is_open_during_weekday_session():
    now = datetime.fromisoformat("2026-09-21T12:00:00+05:30")
    assert market_is_open(now) is True


def test_market_is_closed_on_weekend():
    now = datetime.fromisoformat("2026-09-20T12:00:00+05:30")
    assert market_is_open(now) is False


def test_next_refresh_counts_down_from_last_scan():
    last = datetime.fromisoformat("2026-09-21T12:00:00+05:30")
    now = datetime.fromisoformat("2026-09-21T12:03:30+05:30")
    assert next_refresh_seconds(last, 300, now) == 90


def test_refresh_label_formats_minutes_and_seconds():
    assert refresh_label(90) == "1m 30s"
    assert refresh_label(0) == "refresh due"


def test_first_automatic_scan_waits_until_0925_ist():
    at_open = datetime.fromisoformat("2026-09-21T09:15:00+05:30")
    just_before = datetime.fromisoformat("2026-09-21T09:24:30+05:30")
    at_first_scan = datetime.fromisoformat("2026-09-21T09:25:00+05:30")
    after_first_scan = datetime.fromisoformat("2026-09-21T10:00:00+05:30")

    assert seconds_until_first_scan(at_open) == 600
    assert seconds_until_first_scan(just_before) == 30
    assert seconds_until_first_scan(at_first_scan) == 0
    assert seconds_until_first_scan(after_first_scan) == 0



def test_naive_market_time_is_interpreted_as_india_local_time():
    # Deployment hosts may run in UTC; naive dashboard timestamps must not
    # be reinterpreted using the host machine's timezone.
    assert market_is_open(datetime.fromisoformat("2026-09-21T12:00:00")) is True
    assert market_is_open(datetime.fromisoformat("2026-09-20T12:00:00")) is False


def test_market_session_boundaries_are_half_open():
    assert market_is_open(datetime.fromisoformat("2026-09-21T09:14:59+05:30")) is False
    assert market_is_open(datetime.fromisoformat("2026-09-21T09:15:00+05:30")) is True
    assert market_is_open(datetime.fromisoformat("2026-09-21T15:29:59+05:30")) is True
    assert market_is_open(datetime.fromisoformat("2026-09-21T15:30:00+05:30")) is False


def test_naive_refresh_timestamps_are_interpreted_as_india_local_time():
    last = datetime.fromisoformat("2026-09-21T12:00:00")
    now = datetime.fromisoformat("2026-09-21T12:03:30")
    assert next_refresh_seconds(last, 300, now) == 90


def test_naive_first_scan_clock_uses_india_local_time():
    at_open = datetime.fromisoformat("2026-09-21T09:15:00")
    assert seconds_until_first_scan(at_open) == 600
