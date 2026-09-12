from __future__ import annotations

from services.quantitative.block91_portfolio_valuation_engine import (
    EROSBlock91PortfolioValuationEngine,
)


def _portfolio_state():
    return {
        "state": {
            "portfolio_id": "EROS90-BLOCK91-TEST",
            "settlement_id": "EROS89-BLOCK91-001",
            "audit_id": "EROS88-BLOCK91-001",
            "decision_id": "EROS86-BLOCK91-001",
            "state_status": "APPLIED",
            "cash_after": 9_990_000.0,
            "positions": [
                {
                    "symbol": "RELIANCE.NS",
                    "quantity": 4000.0,
                    "average_cost": 2500.0,
                    "current_price": 2600.0,
                    "realized_pnl": 0.0,
                }
            ],
        },
        "portfolio": {
            "portfolio_id": "EROS90-BLOCK91-TEST",
            "cash_balance": 9_990_000.0,
        },
        "certificate": {
            "status": "CERTIFIED",
            "settlement_status": "SETTLED",
            "settlement_id": "EROS89-BLOCK91-001",
            "audit_id": "EROS88-BLOCK91-001",
            "decision_id": "EROS86-BLOCK91-001",
            "settlement_allowed": True,
        },
    }


def _blocked_state():
    payload = _portfolio_state()

    payload["state"] = {
        **payload["state"],
        "state_status": "BLOCKED",
    }

    payload["certificate"] = {
        **payload["certificate"],
        "status": "BLOCKED",
        "settlement_allowed": False,
    }

    return payload


def run_block91_self_test():
    engine = EROSBlock91PortfolioValuationEngine()

    source = _portfolio_state()

    # ------------------------------------------------------
    # TEST 1 - CERTIFIED BLOCK 90 STATE -> VALUATION
    # ------------------------------------------------------

    result = engine.value_portfolio(
        source,
        {
            "RELIANCE.NS": 2600.0,
        },
    )

    assert result["status"] == "PASS", result
    assert result["certificate"]["status"] == "CERTIFIED"

    assert result["valuation"]["portfolio_equity"] == 20_390_000.0

    assert result["valuation"]["market_value"] == 10_400_000.0

    assert result["valuation"]["unrealized_pnl"] == 400_000.0

    assert result["valuation"]["total_pnl"] == 400_000.0

    assert result["valuation"]["position_count"] == 1

    # ------------------------------------------------------
    # TEST 2 - SOURCE STATE MUST NOT MUTATE
    # ------------------------------------------------------

    before = repr(source)

    engine.value_portfolio(
        source,
        {
            "RELIANCE.NS": 2600.0,
        },
    )

    after = repr(source)

    assert before == after

    # ------------------------------------------------------
    # TEST 3 - DUPLICATE VALUATION
    # ------------------------------------------------------

    duplicate = engine.value_portfolio(
        source,
        {
            "RELIANCE.NS": 2600.0,
        },
    )

    assert duplicate["status"] == "DUPLICATE", duplicate
    assert duplicate["certificate"]["status"] == "DUPLICATE"

    # ------------------------------------------------------
    # TEST 4 - BLOCKED STATE
    # ------------------------------------------------------

    blocked = engine.value_portfolio(
        _blocked_state(),
        {
            "RELIANCE.NS": 2600.0,
        },
    )

    assert blocked["status"] == "BLOCKED", blocked
    assert blocked["certificate"]["status"] == "BLOCKED"

    # ------------------------------------------------------
    # TEST 5 - MISSING LINEAGE
    # ------------------------------------------------------

    malformed = _portfolio_state()

    malformed["state"] = {
        **malformed["state"],
        "settlement_id": "",
    }

    malformed_result = engine.value_portfolio(
        malformed,
        {
            "RELIANCE.NS": 2600.0,
        },
    )

    assert malformed_result["status"] == "BLOCKED"

    # ------------------------------------------------------
    # TEST 6 - INVALID MARKET PRICE
    # ------------------------------------------------------

    invalid_price = engine.value_portfolio(
        {
            **_portfolio_state(),
            "state": {
                **_portfolio_state()["state"],
                "settlement_id": "EROS89-BLOCK91-INVALID-PRICE",
            },
        },
        {
            "RELIANCE.NS": 0.0,
        },
    )

    assert invalid_price["status"] == "BLOCKED"

    # ------------------------------------------------------
    # TEST 7 - NON-BYPASS INVARIANTS
    # ------------------------------------------------------

    snapshot = engine.snapshot()

    assert snapshot["valuation_count"] == 1

    assert snapshot["valuation_history_count"] == 1

    assert result["broker_submission"] is False

    assert result["live_order_submission"] is False

    assert result["mutation_allowed"] is False

    print(
        {
            "status": "PASS",
            "valuation_status": result["status"],
            "portfolio_equity": result["valuation"]["portfolio_equity"],
            "market_value": result["valuation"]["market_value"],
            "unrealized_pnl": result["valuation"]["unrealized_pnl"],
            "duplicate_status": duplicate["status"],
            "blocked_status": blocked["status"],
            "malformed_status": malformed_result["status"],
            "invalid_price_status": invalid_price["status"],
            "non_bypass_invariant": True,
            "broker_submission": result["broker_submission"],
            "live_order_submission": result["live_order_submission"],
        }
    )


if __name__ == "__main__":
    run_block91_self_test()
