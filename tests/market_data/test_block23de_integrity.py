from __future__ import annotations

from datetime import datetime, timedelta, timezone

from services.market_data.packet import MarketDataPacket
from services.market_data.integrity import MarketDataIntegrityGate, MarketDataValidationReport


def live_packet():
    return MarketDataPacket(
        symbol="RELIANCE.NS",
        current_price=2500.0,
        previous_close=2480.0,
        volume=2000000,
        ohlcv_history=[{"date": "2026-09-08T10:00:00+00:00", "close": 2500.0, "volume": 2000000}],
        freshness_timestamp=(datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat(),
        is_stale=False,
        details={"source": "yfinance-live-api"},
    )


def test_block23d_integrity_gate_live():
    report = MarketDataIntegrityGate.validate_packet(live_packet())
    assert isinstance(report, MarketDataValidationReport)
    assert report.data_state == "LIVE"
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_block23d_integrity_gate_invalid():
    packet = MarketDataPacket(
        symbol="BAD.NS",
        current_price=-10.0,
        previous_close=0.0,
        volume=-500,
        ohlcv_history=[],
        freshness_timestamp=datetime.now(timezone.utc).isoformat(),
        is_stale=False,
        details={"source": "test"},
    )
    report = MarketDataIntegrityGate.validate_packet(packet)
    assert report.data_state == "INVALID"
    assert report.is_valid is False
    assert len(report.errors) >= 2


def test_block23d_stale_is_not_valid_for_live_scoring():
    packet = live_packet()
    stale = MarketDataPacket(
        **{
            **packet.__dict__,
            "freshness_timestamp": (
                datetime.now(timezone.utc) - timedelta(minutes=30)
            ).isoformat(),
        }
    )
    report = MarketDataIntegrityGate.validate_packet(stale, max_age_seconds=900)
    assert report.data_state == "STALE"
    assert report.is_valid is False


def test_block23d_fallback_is_not_valid_for_live_scoring():
    packet = live_packet()
    fallback = MarketDataPacket(
        **{
            **packet.__dict__,
            "details": {"source": "fallback-parity-adapter"},
        }
    )
    report = MarketDataIntegrityGate.validate_packet(fallback)
    assert report.data_state == "FALLBACK"
    assert report.is_valid is False
