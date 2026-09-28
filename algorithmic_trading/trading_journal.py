"""Trading journal and order-reconciliation tools for research.

The design follows Chapter 10 of Laurent Bernut's *Algorithmic Short Selling
with Python, Second Edition*: record trades and thoughts, reconcile intended
orders against executions, and preserve an audit trail for later analysis.
This implementation is broker-neutral and stores records in memory so the
existing application remains dependency-free.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReconciliationStatus(StrEnum):
    """Outcome of comparing an intended order with an execution."""

    MATCHED = "matched"
    MISSED = "missed"
    OVERRIDE = "override"


@dataclass(frozen=True)
class TradeOrder:
    """An intended order."""

    order_id: str
    symbol: str
    quantity: int
    price: float | None = None


@dataclass(frozen=True)
class TradeExecution:
    """An execution reported by a venue or broker."""

    execution_id: str
    symbol: str
    quantity: int
    price: float


@dataclass(frozen=True)
class ReconciliationRecord:
    """Auditable classification of an order/execution pair."""

    status: ReconciliationStatus
    symbol: str
    ordered_quantity: int
    executed_quantity: int
    order_id: str | None
    execution_id: str | None


@dataclass(frozen=True)
class JournalEntry:
    """A dated trading thought or review note."""

    date: str
    phase: str
    text: str


def reconcile_orders(
    orders: list[TradeOrder],
    executions: list[TradeExecution],
) -> list[ReconciliationRecord]:
    """Classify orders and executions as matched, missed or override.

    Matching is by symbol and signed quantity. An execution with no
    corresponding order is an override; an order with no execution is missed.
    """
    execution_by_key = {
        (item.symbol, item.quantity): item for item in executions
    }
    matched_execution_ids: set[str] = set()
    records: list[ReconciliationRecord] = []

    for order in orders:
        execution = execution_by_key.get((order.symbol, order.quantity))
        if execution is None:
            records.append(
                ReconciliationRecord(
                    ReconciliationStatus.MISSED,
                    order.symbol,
                    order.quantity,
                    0,
                    order.order_id,
                    None,
                )
            )
            continue

        matched_execution_ids.add(execution.execution_id)
        records.append(
            ReconciliationRecord(
                ReconciliationStatus.MATCHED,
                order.symbol,
                order.quantity,
                execution.quantity,
                order.order_id,
                execution.execution_id,
            )
        )

    for execution in executions:
        if execution.execution_id in matched_execution_ids:
            continue
        records.append(
            ReconciliationRecord(
                ReconciliationStatus.OVERRIDE,
                execution.symbol,
                0,
                execution.quantity,
                None,
                execution.execution_id,
            )
        )

    return records


def reconciliation_summary(
    records: list[ReconciliationRecord],
) -> dict[str, int]:
    """Count each reconciliation outcome."""
    summary = {status.value: 0 for status in ReconciliationStatus}
    for record in records:
        summary[record.status.value] += 1
    return summary


def add_journal_entry(
    entries: list[JournalEntry],
    date: str,
    phase: str,
    text: str,
) -> JournalEntry:
    """Append a validated morning/evening or review entry."""
    if not date.strip():
        raise ValueError("date must not be empty")
    if not phase.strip():
        raise ValueError("phase must not be empty")
    if not text.strip():
        raise ValueError("text must not be empty")

    entry = JournalEntry(date=date, phase=phase, text=text)
    entries.append(entry)
    return entry
