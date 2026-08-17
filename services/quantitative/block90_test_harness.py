from __future__ import annotations

from services.quantitative.block90_portfolio_state_engine import (
    EROSBlock90PortfolioStateEngine,
)


def _settled_buy(
    settlement_id: str = "EROS89-TEST-BUY-001",
):
    return {
        "settlement": {
            "settlement_id": settlement_id,
            "audit_id": "EROS88-TEST-AUDIT-001",
            "decision_id": "EROS86-TEST-001",
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "settlement_status": "SETTLED",
            "settlement_allowed": True,
            "settled_quantity": 4000.0,
            "average_fill_price": 2500.0,
            "gross_value": 10000000.0,
            "transaction_cost": 10000.0,
            "cash_delta": -10010000.0,
            "position_delta": 4000.0,
            "realized_pnl": 0.0,
            "paper_settlement": True,
            "broker_submission": False,
            "live_order_submission": False,
        },
        "certificate": {
            "status": "CERTIFIED",
            "settlement_status": "SETTLED",
            "settlement_id": settlement_id,
            "audit_id": "EROS88-TEST-AUDIT-001",
            "decision_id": "EROS86-TEST-001",
            "settlement_allowed": True,
        },
    }


def _blocked_settlement():
    return {
        "settlement": {
            "settlement_id": "EROS89-TEST-BLOCKED-001",
            "audit_id": "EROS88-TEST-BLOCKED",
            "decision_id": "EROS86-TEST-BLOCKED",
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "settlement_status": "BLOCKED",
            "settlement_allowed": False,
            "position_delta": 0.0,
            "cash_delta": 0.0,
        },
        "certificate": {
            "status": "BLOCKED",
            "settlement_status": "BLOCKED",
            "settlement_id": "EROS89-TEST-BLOCKED-001",
            "audit_id": "EROS88-TEST-BLOCKED",
            "decision_id": "EROS86-TEST-BLOCKED",
            "settlement_allowed": False,
        },
    }


def run_block90_self_test():

    engine = EROSBlock90PortfolioStateEngine(
        portfolio_id="EROS90-TEST-PORTFOLIO",
        initial_cash=20000000.0,
    )

    # ------------------------------------------------------
    # TEST 1 - SETTLED BUY -> PORTFOLIO STATE APPLIED
    # ------------------------------------------------------

    settled = _settled_buy()

    result = engine.apply_settlement(settled)

    assert result["status"] == "PASS", result

    assert (
        result["certificate"]["status"]
        == "CERTIFIED"
    )

    assert (
        result["state"]["state_status"]
        == "APPLIED"
    )

    assert (
        result["state"]["position_quantity_after"]
        == 4000.0
    )

    assert (
        result["state"]["average_cost_after"]
        == 2500.0
    )

    assert (
        result["portfolio"]["position_count"]
        == 1
    )

    assert (
        result["portfolio"]["cash_balance"]
        == 9990000.0
    )

    # ------------------------------------------------------
    # TEST 2 - DUPLICATE SETTLEMENT
    # ------------------------------------------------------

    duplicate = engine.apply_settlement(
        settled
    )

    assert duplicate["status"] == "DUPLICATE", duplicate

    assert (
        duplicate["certificate"]["status"]
        == "DUPLICATE"
    )

    assert (
        duplicate["portfolio"]["cash_balance"]
        == 9990000.0
    )

    assert (
        duplicate["portfolio"]["position_count"]
        == 1
    )

    # ------------------------------------------------------
    # TEST 3 - BLOCKED SETTLEMENT CANNOT MUTATE STATE
    # ------------------------------------------------------

    before = engine.snapshot()

    blocked = engine.apply_settlement(
        _blocked_settlement()
    )

    after = engine.snapshot()

    assert blocked["status"] == "BLOCKED", blocked

    assert (
        blocked["certificate"]["status"]
        == "BLOCKED"
    )

    assert before == after

    # ------------------------------------------------------
    # TEST 4 - NON-BYPASS INVARIANT
    # ------------------------------------------------------

    assert (
        engine.snapshot()["processed_settlement_count"]
        == 1
    )

    assert (
        engine.snapshot()["state_history_count"]
        == 1
    )

    print(
        {
            "status": "PASS",
            "applied_status": result["status"],
            "portfolio_state": result["state"]["state_status"],
            "cash_after": result["portfolio"]["cash_balance"],
            "position_quantity": result["state"][
                "position_quantity_after"
            ],
            "average_cost": result["state"][
                "average_cost_after"
            ],
            "duplicate_status": duplicate["status"],
            "blocked_status": blocked["status"],
            "non_bypass_invariant": True,
        }
    )


if __name__ == "__main__":
    run_block90_self_test()
