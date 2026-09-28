from algorithmic_trading.trading_journal import (
    ReconciliationStatus,
    TradeExecution,
    TradeOrder,
    add_journal_entry,
    reconcile_orders,
    reconciliation_summary,
)


def test_reconcile_matched_missed_and_override() -> None:
    orders = [
        TradeOrder("O1", "RELIANCE", 100),
        TradeOrder("O2", "TCS", -50),
    ]
    executions = [
        TradeExecution("E1", "RELIANCE", 100, 1_000),
        TradeExecution("E2", "INFY", 25, 1_500),
    ]

    records = reconcile_orders(orders, executions)
    summary = reconciliation_summary(records)

    assert summary == {"matched": 1, "missed": 1, "override": 1}
    assert records[0].status == ReconciliationStatus.MATCHED
    assert records[1].status == ReconciliationStatus.MISSED
    assert records[2].status == ReconciliationStatus.OVERRIDE


def test_add_journal_entry() -> None:
    entries = []
    entry = add_journal_entry(entries, "2026-09-28", "evening", "Followed the plan.")

    assert entries == [entry]
    assert entry.phase == "evening"


def test_blank_journal_entry_is_rejected() -> None:
    entries = []

    try:
        add_journal_entry(entries, "", "morning", "note")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
