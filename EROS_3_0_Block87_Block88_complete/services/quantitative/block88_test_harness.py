from __future__ import annotations

from services.quantitative.block86_control_plane import EROSBlock86ControlPlane
from services.quantitative.block87_execution_bridge import EROSBlock87ExecutionBridge
from services.quantitative.block88_audit_reconciliation import (
    EROSBlock88AuditReconciliationEngine,
)


def run_block88_self_test():
    control = EROSBlock86ControlPlane()

    decision = control.evaluate(
        {
            "status": "CERTIFIED",
            "execution_allowed": True,
            "certification_score": 95.0,
            "risk_status": "PASS",
            "governance_status": "APPROVED",
            "validation_status": "PASS",
            "simulation_status": "PASS",
        },
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.95,
    )

    bridge = EROSBlock87ExecutionBridge()

    execution = bridge.execute(
        decision,
        [
            {
                "symbol": "RELIANCE.NS",
                "action": "BUY",
                "trade_weight": 0.10,
                "current_price": 2500.0,
            }
        ],
    )

    engine = EROSBlock88AuditReconciliationEngine()

    expected_orders = execution.to_dict().get("orders", [])
    result = engine.audit_and_certify(
        execution,
        expected_orders=expected_orders,
        expected_tca=execution.to_dict().get("tca", {}),
    )

    assert result["status"] == "PASS"
    assert result["certificate"]["status"] == "CERTIFIED"
    assert result["certificate"]["reconciliation_status"] == "RECONCILED"
    assert result["certificate"]["execution_allowed"] is True
    assert result["certificate"]["broker_submission"] is False
    assert result["certificate"]["live_order_submission"] is False

    blocked_decision = control.evaluate(
        {
            "status": "BLOCKED",
            "execution_allowed": False,
            "certification_score": 20.0,
            "risk_status": "BLOCK",
            "governance_status": "APPROVED",
            "validation_status": "PASS",
            "simulation_status": "PASS",
        },
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.95,
    )

    blocked_execution = bridge.execute(
        blocked_decision,
        [
            {
                "symbol": "RELIANCE.NS",
                "action": "BUY",
                "trade_weight": 0.10,
                "current_price": 2500.0,
            }
        ],
    )

    blocked_audit = engine.audit_and_certify(blocked_execution)

    assert blocked_audit["status"] == "BLOCKED"
    assert blocked_audit["certificate"]["status"] == "BLOCKED"
    assert blocked_audit["certificate"]["execution_allowed"] is False

    # Tamper test: add a fill that was not in the expected order plan.
    tampered = execution.to_dict()
    tampered["fills"] = [
        {
            "fill_id": "TAMPERED-FILL",
            "symbol": "RELIANCE.NS",
            "quantity": 999999,
            "fill_price": 2500.0,
        }
    ]

    tampered_audit = engine.audit_and_certify(
        tampered,
        expected_orders=expected_orders,
    )

    assert tampered_audit["status"] == "BLOCKED"
    assert tampered_audit["certificate"]["status"] == "BLOCKED"

    return {
        "status": "PASS",
        "approved_certificate": result["certificate"]["status"],
        "approved_reconciliation": result["certificate"]["reconciliation_status"],
        "blocked_certificate": blocked_audit["certificate"]["status"],
        "tamper_certificate": tampered_audit["certificate"]["status"],
        "non_bypass_invariant": (
            blocked_audit["certificate"]["status"] == "BLOCKED"
            and tampered_audit["certificate"]["status"] == "BLOCKED"
        ),
        "broker_submission": result["certificate"]["broker_submission"],
        "live_order_submission": result["certificate"]["live_order_submission"],
    }


if __name__ == "__main__":
    print(run_block88_self_test())
