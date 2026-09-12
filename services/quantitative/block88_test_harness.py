from __future__ import annotations

from services.quantitative.block86_control_plane import (
    EROSBlock86ControlPlane,
)
from services.quantitative.block87_execution_bridge import (
    EROSBlock87ExecutionBridge,
)
from services.quantitative.block88_audit_reconciliation import (
    EROSBlock88AuditReconciliationEngine,
)
from services.quantitative.paper_execution import (
    EROSPaperExecutionEngine,
)


def run_block88_self_test():
    # ==========================================================
    # BLOCK 86 - AUTHORIZATION
    # ==========================================================

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

    decision_payload = decision.to_dict() if hasattr(decision, "to_dict") else dict(decision)

    assert decision_payload["decision_id"]
    assert decision_payload["execution_allowed"] is True
    assert decision_payload["control_state"] == "APPROVED"

    # ==========================================================
    # BLOCK 87 - CONTROLLED EXECUTION BRIDGE
    # ==========================================================

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

    execution_payload = execution.to_dict() if hasattr(execution, "to_dict") else dict(execution)

    assert execution_payload["status"] == "EXECUTION_READY"
    assert execution_payload["execution_allowed"] is True
    assert execution_payload["order_count"] == 1
    execution_audit = execution_payload.get("audit_evidence", {})

    assert execution_audit.get("broker_submission") is False
    assert execution_audit.get("live_order_submission") is False

    orders = list(execution_payload.get("orders", []))

    assert len(orders) == 1

    # ==========================================================
    # BLOCK 84 - PAPER EXECUTION
    #
    # Block 88 must reconcile against actual paper fills,
    # not merely against the requested Block 87 orders.
    # ==========================================================

    paper = EROSPaperExecutionEngine()

    intents = []

    for order in orders:
        intents.append(
            {
                "symbol": order["symbol"],
                "action": order["action"],
                "quantity": order["quantity"],
                "reference_price": order["limit_price"],
                "execution_allowed": True,
                "fill_ratio": 1.0,
            }
        )

    paper_execution = paper.execute_intents(intents)

    assert paper_execution["status"] == "SUCCESS"
    assert paper_execution["broker_submission"] is False
    assert paper_execution["execution_mode"] == "PAPER"
    assert paper_execution["filled_count"] == 1

    fills = list(paper_execution.get("fills", []))

    assert len(fills) == 1
    assert fills[0]["fill_status"] == "FILLED"

    paper_tca = paper.generate_tca(paper_execution)

    assert isinstance(paper_tca, dict)

    # ==========================================================
    # BLOCK 88 - AUDIT / RECONCILIATION PAYLOAD
    #
    # Explicitly expose:
    #   Block 86 decision
    #   Block 87 orders
    #   Block 84 fills
    #   Block 84 TCA
    #
    # This is the canonical execution evidence chain.
    # ==========================================================

    audit_payload = dict(execution_payload)

    audit_payload["decision"] = decision_payload
    audit_payload["orders"] = orders
    audit_payload["fills"] = fills
    audit_payload["tca"] = paper_tca

    audit_payload["paper_execution"] = paper_execution
    audit_payload["paper_execution_tca"] = paper_tca

    audit_payload["decision_id"] = decision_payload["decision_id"]
    audit_payload["symbol"] = decision_payload["symbol"]
    audit_payload["action"] = decision_payload["final_action"]
    audit_payload["execution_allowed"] = True

    # ==========================================================
    # BLOCK 88 - RECONCILIATION
    # ==========================================================

    engine = EROSBlock88AuditReconciliationEngine()

    result = engine.audit_and_certify(
        audit_payload,
        expected_orders=orders,
        expected_fills=fills,
        expected_tca=paper_tca,
    )

    assert result["status"] == "PASS", result

    certificate = result["certificate"]

    assert certificate["status"] == "CERTIFIED", certificate
    assert certificate["reconciliation_status"] == "RECONCILED", certificate
    assert certificate["execution_allowed"] is True
    assert certificate["broker_submission"] is False
    assert certificate["live_order_submission"] is False
    assert certificate["exception_count"] == 0

    # ==========================================================
    # BLOCK 88 - BLOCKED PATH
    #
    # A blocked Block 86 decision must never become a
    # reconciled/executable Block 88 result.
    # ==========================================================

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

    blocked_payload = (
        blocked_decision.to_dict()
        if hasattr(blocked_decision, "to_dict")
        else dict(blocked_decision)
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

    blocked_execution_payload = (
        blocked_execution.to_dict()
        if hasattr(blocked_execution, "to_dict")
        else dict(blocked_execution)
    )

    assert blocked_execution_payload["execution_allowed"] is False
    assert blocked_execution_payload["status"] == "BLOCKED"
    assert blocked_execution_payload["order_count"] == 0

    blocked_audit_payload = dict(blocked_execution_payload)

    blocked_audit_payload["decision"] = blocked_payload
    blocked_audit_payload["orders"] = []
    blocked_audit_payload["fills"] = []
    blocked_audit_payload["tca"] = {}
    blocked_audit_payload["decision_id"] = blocked_payload["decision_id"]
    blocked_audit_payload["symbol"] = blocked_payload["symbol"]
    blocked_audit_payload["action"] = blocked_payload["final_action"]
    blocked_audit_payload["execution_allowed"] = False

    blocked_result = engine.audit_and_certify(
        blocked_audit_payload,
        expected_orders=[],
        expected_tca={},
    )

    assert blocked_result["status"] == "BLOCKED"

    blocked_certificate = blocked_result["certificate"]

    assert blocked_certificate["status"] == "BLOCKED"
    assert blocked_certificate["execution_allowed"] is False
    assert blocked_certificate["broker_submission"] is False
    assert blocked_certificate["live_order_submission"] is False

    # ==========================================================
    # NON-BYPASS INVARIANT
    # ==========================================================

    assert not (
        blocked_certificate["execution_allowed"] and blocked_certificate["status"] == "CERTIFIED"
    )

    return {
        "status": "PASS",
        "approved_status": result["status"],
        "approved_certificate": certificate["status"],
        "approved_reconciliation": certificate["reconciliation_status"],
        "approved_order_count": len(orders),
        "approved_fill_count": len(fills),
        "approved_transaction_cost": paper_execution["total_transaction_cost"],
        "blocked_status": blocked_result["status"],
        "blocked_certificate": blocked_certificate["status"],
        "non_bypass_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }


if __name__ == "__main__":
    print(run_block88_self_test())
