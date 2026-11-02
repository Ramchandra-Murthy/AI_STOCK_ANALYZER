"""Tests for intraday candle freshness classification."""

from datetime import datetime, timedelta

from services.intraday_context_freshness import intraday_context_freshness


def test_recent_timestamp_is_fresh():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    assert intraday_context_freshness(now - timedelta(minutes=4), now=now) == "FRESH"


def test_timestamp_at_age_limit_is_fresh():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    assert intraday_context_freshness(now - timedelta(minutes=5), now=now) == "FRESH"


def test_old_timestamp_is_stale():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    assert intraday_context_freshness(now - timedelta(minutes=6), now=now) == "STALE"


def test_future_timestamp_is_rejected():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    assert intraday_context_freshness(now + timedelta(seconds=1), now=now) == "FUTURE_TIMESTAMP"


def test_missing_or_invalid_timestamp_is_unavailable():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    assert intraday_context_freshness(None, now=now) == "TIMESTAMP_UNAVAILABLE"
    assert intraday_context_freshness("not-a-time", now=now) == "TIMESTAMP_UNAVAILABLE"


def test_naive_timestamp_uses_now_timezone():
    now = datetime.fromisoformat("2026-11-02T09:20:00+05:30")
    observed = datetime.fromisoformat("2026-11-02T09:18:00")
    assert intraday_context_freshness(observed, now=now) == "FRESH"
