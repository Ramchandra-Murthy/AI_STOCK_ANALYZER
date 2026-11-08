"""Deterministic sequence-aware replay and snapshot recovery for Level-2 updates.

This module consumes normalized :class:`LevelUpdate` events. It does not
connect to an exchange, infer missing events, or manufacture book state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ai_trading.order_book import LevelUpdate, OrderBookSnapshot

ReplayStatus = Literal[
    "applied",
    "duplicate",
    "gap",
    "recovered",
    "invalid",
    "buffer_overflow",
]


@dataclass(frozen=True, slots=True)
class ReplayResult:
    """Outcome of one event or snapshot operation."""

    status: ReplayStatus
    snapshot: OrderBookSnapshot
    synchronized: bool
    expected_sequence: int
    received_sequence: int | None
    applied_count: int
    buffered_sequences: tuple[int, ...]
    message: str | None = None


class Level2EventReplay:
    """Apply contiguous sequenced events and recover only from authoritative snapshots.

    Events received beyond a sequence gap are buffered up to a fixed limit.
    When the missing event arrives, buffered events are replayed in sequence.
    If the gap cannot be filled, callers must supply a fresh authoritative
    snapshot through :meth:`replace_snapshot`. No missing event is inferred.
    """

    def __init__(
        self, snapshot: OrderBookSnapshot, *, max_buffered_events: int = 10_000
    ) -> None:
        if not isinstance(snapshot, OrderBookSnapshot):
            raise ValueError("snapshot must be an OrderBookSnapshot")
        if snapshot.sequence is None:
            raise ValueError("snapshot must include a sequence number")
        if (
            isinstance(max_buffered_events, bool)
            or not isinstance(max_buffered_events, int)
            or max_buffered_events < 1
        ):
            raise ValueError("max_buffered_events must be a positive integer")
        self._snapshot = snapshot
        self._max_buffered_events = max_buffered_events
        self._buffer: dict[int, LevelUpdate] = {}
        self._synchronized = True
        self._last_error: str | None = None

    @property
    def snapshot(self) -> OrderBookSnapshot:
        """Most recent successfully applied immutable book snapshot."""
        return self._snapshot

    @property
    def synchronized(self) -> bool:
        """Whether every sequence after the current snapshot has been applied."""
        return self._synchronized

    @property
    def expected_sequence(self) -> int:
        """Next sequence number required for contiguous replay."""
        assert self._snapshot.sequence is not None
        return self._snapshot.sequence + 1

    @property
    def buffered_sequences(self) -> tuple[int, ...]:
        """Buffered event sequence numbers in ascending order."""
        return tuple(sorted(self._buffer))

    def ingest(self, update: LevelUpdate) -> ReplayResult:
        """Buffer or apply one event, reporting gaps without inventing state."""
        if not isinstance(update, LevelUpdate):
            raise ValueError("update must be a LevelUpdate")
        if update.sequence is None:
            raise ValueError("replay requires every update to have a sequence number")

        sequence = update.sequence
        assert self._snapshot.sequence is not None
        if sequence <= self._snapshot.sequence:
            return self._result("duplicate", sequence, 0, "event is at or behind the current snapshot")

        buffered = self._buffer.get(sequence)
        if buffered is not None:
            if buffered != update:
                return self._result(
                    "invalid", sequence, 0, "conflicting events use the same sequence number"
                )
            return self._result("duplicate", sequence, 0, "event is already buffered")

        if sequence != self.expected_sequence or not self._synchronized:
            if not self._store(update):
                self._synchronized = False
                return self._result(
                    "buffer_overflow",
                    sequence,
                    0,
                    "event buffer limit exceeded; an authoritative snapshot is required",
                )
            self._synchronized = False
            return self._drain(sequence, was_synchronized=False)

        try:
            self._snapshot = self._snapshot.apply_update(update)
        except ValueError as exc:
            self._store(update)
            self._synchronized = False
            self._last_error = str(exc)
            return self._result("invalid", sequence, 0, self._last_error)

        return self._result("applied", sequence, 1)

    def replace_snapshot(self, snapshot: OrderBookSnapshot) -> ReplayResult:
        """Install an authoritative snapshot and replay any now-contiguous buffer."""
        if not isinstance(snapshot, OrderBookSnapshot):
            raise ValueError("snapshot must be an OrderBookSnapshot")
        if snapshot.symbol != self._snapshot.symbol:
            raise ValueError("replacement snapshot symbol must match the replay symbol")
        if snapshot.sequence is None:
            raise ValueError("replacement snapshot must include a sequence number")
        assert self._snapshot.sequence is not None
        if snapshot.sequence < self._snapshot.sequence:
            raise ValueError("replacement snapshot cannot move sequence backwards")

        self._snapshot = snapshot
        self._buffer = {
            sequence: update
            for sequence, update in self._buffer.items()
            if sequence > snapshot.sequence
        }
        self._last_error = None
        self._synchronized = not self._buffer
        return self._drain(None, was_synchronized=False)

    def _store(self, update: LevelUpdate) -> bool:
        assert update.sequence is not None
        if len(self._buffer) >= self._max_buffered_events:
            self._buffer.clear()
            self._last_error = "event buffer limit exceeded"
            return False
        self._buffer[update.sequence] = update
        return True

    def _drain(self, received_sequence: int | None, *, was_synchronized: bool) -> ReplayResult:
        applied_count = 0
        while self.expected_sequence in self._buffer:
            sequence = self.expected_sequence
            update = self._buffer[sequence]
            try:
                next_snapshot = self._snapshot.apply_update(update)
            except ValueError as exc:
                self._synchronized = False
                self._last_error = str(exc)
                return self._result("invalid", received_sequence, applied_count, self._last_error)
            self._snapshot = next_snapshot
            del self._buffer[sequence]
            applied_count += 1

        self._synchronized = not self._buffer
        if self._synchronized:
            self._last_error = None
            status: ReplayStatus = "recovered" if not was_synchronized else "applied"
        else:
            status = "gap"
        return self._result(status, received_sequence, applied_count, self._last_error)

    def _result(
        self,
        status: ReplayStatus,
        received_sequence: int | None,
        applied_count: int,
        message: str | None = None,
    ) -> ReplayResult:
        return ReplayResult(
            status=status,
            snapshot=self._snapshot,
            synchronized=self._synchronized,
            expected_sequence=self.expected_sequence,
            received_sequence=received_sequence,
            applied_count=applied_count,
            buffered_sequences=self.buffered_sequences,
            message=message,
        )
