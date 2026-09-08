from __future__ import annotations

"""
EROS 3.0 - Block 85 test harness.

No broker, network, database, Celery or external market-data dependency.
"""

from services.quantitative.block85_execution_certification import (
    EROSBlock85ExecutionCertificationEngine,
)


def run_block85_self_test() -> dict:
    engine = EROSBlock85ExecutionCertificationEngine()

    orders = [
        {
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "quantity": 100.0,
            "limit_price": 2500.0,
            "allocation_pct": 0.10,
            "current_price": 2500.0,
            "market_data_state": "LIVE",
            "market_price_source": "yfinance-live-api",
        },
        {
            "symbol": "TCS.NS",
            "action": "BUY",
            "quantity": 50.0,
            "limit_price": 3500.0,
            "allocation_pct": 0.08,
            "current_price": 3500.0,
            "market_data_state": "LIVE",
            "market_price_source": "yfinance-live-api",
        },
    ]

    certified = engine.certify(
        orders=orders,
        risk={"status": "PASS", "risk_score": 25.0},
        governance={"status": "APPROVED"},
        validation={"status": "PASS"},
        simulation={"status": "PASS"},
        metadata={"test": True},
    )

    assert certified.status == "CERTIFIED"
    assert certified.execution_allowed is True
    assert certified.order_count == 2
    assert certified.total_notional > 0
    assert certified.total_transaction_cost >= 0
    assert certified.metadata["broker_submission"] is False

    blocked = engine.certify(
        orders=orders,
        risk={"status": "BLOCK"},
        governance={"status": "APPROVED"},
    )

    assert blocked.status == "BLOCKED"
    assert blocked.execution_allowed is False

    no_live_evidence = engine.certify(
        orders=[{
            "symbol": "INFY.NS",
            "action": "BUY",
            "quantity": 10,
            "limit_price": 1500.0,
        }],
        risk={"status": "PASS"},
        governance={"status": "APPROVED"},
        validation={"status": "PASS"},
        simulation={"status": "PASS"},
    )

    assert no_live_evidence.status == "BLOCKED"
    assert no_live_evidence.execution_allowed is False
    assert any(
        "market" in reason.lower()
        for reason in no_live_evidence.blocking_reasons
    )

    return {
        "status": "PASS",
        "certified_status": certified.status,
        "blocked_status": blocked.status,
        "order_count": certified.order_count,
        "transaction_cost": certified.total_transaction_cost,
    }


if __name__ == "__main__":
    print(run_block85_self_test())
