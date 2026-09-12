from __future__ import annotations

"""
EROS 3.0 - Block 87
Execution Bridge self-test harness.
"""

from services.quantitative.block86_control_plane import (
    EROSBlock86ControlPlane,
)
from services.quantitative.block87_execution_bridge import (
    EROSBlock87ExecutionBridge,
)


def _approved_decision() -> object:

    return EROSBlock86ControlPlane().evaluate(
        {
            "status": "CERTIFIED",
            "execution_allowed": True,
            "certification_score": 95.0,
            "risk_status": "PASS",
            "governance_status": "APPROVED",
            "validation_status": "PASS",
            "simulation_status": "PASS",
            "engine_version": "EROS-3.0-BLOCK-85",
        },
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.95,
    )


def _blocked_decision() -> object:

    return EROSBlock86ControlPlane().evaluate(
        {
            "status": "BLOCKED",
            "execution_allowed": False,
            "certification_score": 40.0,
            "risk_status": "BLOCK",
            "governance_status": "APPROVED",
            "validation_status": "PASS",
            "simulation_status": "PASS",
            "engine_version": "EROS-3.0-BLOCK-85",
        },
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.95,
    )


def run_block87_self_test() -> dict:

    bridge = EROSBlock87ExecutionBridge()

    approved = _approved_decision()

    allocations = [
        {
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "trade_weight": 0.10,
            "current_price": 2500.0,
        }
    ]

    result = bridge.execute(
        approved,
        allocations,
    )

    assert result.status == "EXECUTION_READY"
    assert result.execution_allowed is True
    assert result.order_count == 1
    assert result.decision_id == approved.decision_id
    assert result.orders[0]["symbol"] == "RELIANCE.NS"
    assert result.orders[0]["metadata"]["block86_decision_id"] == approved.decision_id
    assert result.audit_evidence["broker_submission"] is False
    assert result.audit_evidence["live_order_submission"] is False

    duplicate = bridge.execute(
        approved,
        allocations,
    )

    assert duplicate.status == "DUPLICATE"
    assert duplicate.execution_allowed is True
    assert duplicate.request_id == result.request_id

    blocked = _blocked_decision()

    blocked_result = bridge.execute(
        blocked,
        allocations,
    )

    assert blocked_result.status == "BLOCKED"
    assert blocked_result.execution_allowed is False
    assert blocked_result.order_count == 0

    malformed = bridge.execute(
        approved,
        [
            {
                "symbol": "INFY.NS",
                "action": "BUY",
                "trade_weight": 0.10,
                "current_price": 2500.0,
            }
        ],
    )

    assert malformed.status == "BLOCKED"
    assert malformed.execution_allowed is False
    assert malformed.order_count == 0

    return {
        "status": "PASS",
        "approved_status": result.status,
        "approved_order_count": result.order_count,
        "duplicate_status": duplicate.status,
        "blocked_status": blocked_result.status,
        "malformed_status": malformed.status,
        "non_bypass_invariant": (
            blocked_result.execution_allowed is False and blocked_result.order_count == 0
        ),
        "broker_submission": False,
        "live_order_submission": False,
    }


if __name__ == "__main__":
    print(run_block87_self_test())
