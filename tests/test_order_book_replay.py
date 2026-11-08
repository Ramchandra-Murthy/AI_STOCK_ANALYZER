from datetime import UTC, datetime, timedelta

import pytest

from ai_trading.order_book import LevelUpdate, OrderBookSnapshot
from ai_trading.order_book_replay import Level2EventReplay

NOW = datetime(2026, 11, 9, 4, 0, tzinfo=UTC)


def _book(sequence=10):
    return OrderBookSnapshot.from_levels(
        "RELIANCE",
        NOW,
        bids=[(100.0, 10.0), (99.0, 20.0)],
        asks=[(101.0, 12.0), (102.0, 18.0)],
        sequence=sequence,
    )


def _event(sequence, side="bid", price=100.0, quantity=15.0):
    return LevelUpdate(
        NOW + timedelta(milliseconds=sequence - 10),
        side,
        price,
        quantity,
        sequence=sequence,
    )


def test_contiguous_event_is_applied_and_advances_sequence():
    replay = Level2EventReplay(_book())
    result = replay.ingest(_event(11))

    assert result.status == "applied"
    assert result.synchronized
    assert result.applied_count == 1
    assert result.snapshot.sequence == 11
    assert result.snapshot.bids[0].quantity == 15.0


def test_out_of_order_event_marks_gap_without_mutating_book():
    replay = Level2EventReplay(_book())
    result = replay.ingest(_event(12, side="ask", price=102.0, quantity=25.0))

    assert result.status == "gap"
    assert not result.synchronized
    assert result.expected_sequence == 11
    assert result.buffered_sequences == (12,)
    assert result.snapshot.sequence == 10
    assert result.snapshot.asks[1].quantity == 18.0


def test_arrival_of_missing_event_replays_buffer_in_sequence():
    replay = Level2EventReplay(_book())
    replay.ingest(_event(12, side="ask", price=102.0, quantity=25.0))

    result = replay.ingest(_event(11, side="bid", price=100.0, quantity=16.0))

    assert result.status == "recovered"
    assert result.synchronized
    assert result.applied_count == 2
    assert result.snapshot.sequence == 12
    assert result.snapshot.bids[0].quantity == 16.0
    assert result.snapshot.asks[1].quantity == 25.0
    assert result.buffered_sequences == ()


def test_authoritative_snapshot_discards_covered_events_and_recovers():
    replay = Level2EventReplay(_book())
    replay.ingest(_event(12))
    replay.ingest(_event(14))

    replacement = OrderBookSnapshot.from_levels(
        "RELIANCE",
        NOW + timedelta(milliseconds=3),
        bids=[(100.0, 22.0), (99.0, 20.0)],
        asks=[(101.0, 12.0), (102.0, 18.0)],
        sequence=13,
    )
    result = replay.replace_snapshot(replacement)

    assert result.status == "recovered"
    assert result.synchronized
    assert result.snapshot.sequence == 14
    assert result.snapshot.bids[0].quantity == 15.0
    assert result.buffered_sequences == ()


def test_snapshot_recovery_does_not_skip_a_remaining_gap():
    replay = Level2EventReplay(_book())
    replay.ingest(_event(13))

    replacement = _book(sequence=11)
    result = replay.replace_snapshot(replacement)

    assert result.status == "gap"
    assert not result.synchronized
    assert result.expected_sequence == 12
    assert result.buffered_sequences == (13,)


def test_duplicate_applied_event_is_ignored():
    replay = Level2EventReplay(_book())
    replay.ingest(_event(11))
    result = replay.ingest(_event(11))

    assert result.status == "duplicate"
    assert result.snapshot.sequence == 11
    assert result.applied_count == 0


def test_conflicting_events_with_same_buffered_sequence_are_rejected():
    replay = Level2EventReplay(_book())
    replay.ingest(_event(12))
    result = replay.ingest(_event(12, quantity=99.0))

    assert result.status == "invalid"
    assert result.buffered_sequences == (12,)


def test_buffer_overflow_requires_authoritative_snapshot():
    replay = Level2EventReplay(_book(), max_buffered_events=1)
    replay.ingest(_event(12))
    result = replay.ingest(_event(13))

    assert result.status == "buffer_overflow"
    assert not result.synchronized
    assert result.buffered_sequences == ()

    recovered = replay.replace_snapshot(_book(sequence=13))
    assert recovered.status == "recovered"
    assert recovered.synchronized
    assert recovered.snapshot.sequence == 13


def test_invalid_book_update_waits_for_authoritative_snapshot():
    replay = Level2EventReplay(_book())
    result = replay.ingest(_event(11, side="bid", price=101.0, quantity=50.0))

    assert result.status == "invalid"
    assert not result.synchronized
    assert result.snapshot.sequence == 10

    recovered = replay.replace_snapshot(_book(sequence=11))
    assert recovered.status == "recovered"
    assert recovered.synchronized
    assert recovered.snapshot.sequence == 11


@pytest.mark.parametrize(
    "snapshot, max_buffered_events",
    [
        (_book(sequence=None), 10),
        (_book(), 0),
        (_book(), True),
        (_book(), 1.5),
    ],
)
def test_constructor_rejects_invalid_configuration(snapshot, max_buffered_events):
    with pytest.raises(ValueError):
        Level2EventReplay(snapshot, max_buffered_events=max_buffered_events)


def test_replay_requires_sequence_numbers():
    replay = Level2EventReplay(_book())
    with pytest.raises(ValueError, match="sequence"):
        replay.ingest(_event(11).__class__(NOW, "bid", 100.0, 15.0))


def test_replacement_snapshot_must_match_symbol_and_not_move_backwards():
    replay = Level2EventReplay(_book())
    wrong_symbol = OrderBookSnapshot.from_levels(
        "TCS", NOW, bids=[(100, 1)], asks=[(101, 1)], sequence=10
    )
    with pytest.raises(ValueError, match="symbol"):
        replay.replace_snapshot(wrong_symbol)
    with pytest.raises(ValueError, match="backwards"):
        replay.replace_snapshot(_book(sequence=9))
