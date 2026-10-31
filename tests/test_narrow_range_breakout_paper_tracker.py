"""Tests for the NR4/NR7 paper-trade journal."""

import pytest

from ai_trading.narrow_range_breakout_paper_tracker import NarrowRangePaperTracker


def _signal(tracker: NarrowRangePaperTracker, signal_id: str = "s1"):
    return tracker.add_signal(
        signal_id=signal_id,
        symbol="reliance",
        pattern="NR4",
        side="LONG",
        signal_time="2026-10-30T10:00:00+05:30",
        trigger=100.0,
        stop=95.0,
        target=110.0,
    )


def test_signal_entry_close_and_realized_metrics() -> None:
    tracker = NarrowRangePaperTracker()
    signal = _signal(tracker)
    assert signal.symbol == "RELIANCE"
    assert signal.status == "WATCHING"

    tracker.record_entry("s1", entry_price=101.0, quantity=10)
    closed = tracker.close_trade("s1", exit_price=111.0, exit_reason="target")

    assert closed.status == "CLOSED"
    assert closed.realized_pnl == pytest.approx(100.0)
    assert closed.realized_r == pytest.approx(100.0 / 60.0)


def test_short_trade_realized_pnl_is_directional() -> None:
    tracker = NarrowRangePaperTracker()
    tracker.add_signal(
        signal_id="short1",
        symbol="NIFTY",
        pattern="NR7",
        side="SHORT",
        trigger=100.0,
        stop=105.0,
        target=90.0,
    )
    tracker.record_entry("short1", entry_price=99.0, quantity=2)
    trade = tracker.close_trade("short1", exit_price=94.0, exit_reason="target")
    assert trade.realized_pnl == pytest.approx(10.0)


def test_levels_and_state_transitions_are_validated() -> None:
    tracker = NarrowRangePaperTracker()
    with pytest.raises(ValueError, match="LONG levels"):
        tracker.add_signal(
            signal_id="bad",
            symbol="ABC",
            pattern="NR4",
            side="LONG",
            trigger=100,
            stop=101,
            target=110,
        )
    _signal(tracker)
    with pytest.raises(ValueError, match="already exists"):
        _signal(tracker)
    with pytest.raises(ValueError, match="only WATCHING"):
        tracker.close_trade("s1", exit_price=110, exit_reason="target")


def test_cancel_and_csv_round_trip(tmp_path) -> None:
    tracker = NarrowRangePaperTracker()
    _signal(tracker)
    tracker.cancel_signal("s1", notes="No breakout")
    path = tmp_path / "nr_journal.csv"
    tracker.save_csv(path)

    restored = NarrowRangePaperTracker.load_csv(path)
    assert len(restored.trades) == 1
    assert restored.trades[0].status == "CANCELLED"
    assert restored.trades[0].notes == "No breakout"


def test_entry_requires_positive_quantity_and_price() -> None:
    tracker = NarrowRangePaperTracker()
    _signal(tracker)
    with pytest.raises(ValueError, match="positive"):
        tracker.record_entry("s1", entry_price=0, quantity=1)
