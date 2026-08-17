from __future__ import annotations

from services.quantitative.block87_execution_bridge import (
    EROSBlock87ExecutionBridge,
)
from services.quantitative.block88_audit_reconciliation import (
    EROSBlock88AuditReconciliationEngine,
)
from services.quantitative.block89_settlement_engine import (
    EROSBlock89SettlementEngine,
)


def _approved_decision():
    return {
        "decision_id": "EROS86-BLOCK89-TEST",
        "symbol": "RELIANCE.NS",
        "final_action": "BUY",
        "control_state": "APPROVED",
        "execution_allowed": True,
        "confidence": 0.95,
        "audit_evidence": {
            "decision_hash": "BLOCK89-TEST-HASH",
        },
    }


def _blocked_decision():
    return {
        "decision_id": "EROS86-BLOCK89-BLOCKED",
        "symbol": "RELIANCE.NS",
        "action": "BUY",
        "control_state": "BLOCKED",
        "execution_allowed": False,
        "confidence": 0.95,
    }


def _paper_execution_payload(execution_result):
    orders = execution_result.to_dict()["orders"]

    fills = []

    for index, order in enumerate(orders, start=1):
        quantity = float(
            order.get(
                "quantity",
                order.get(
                    "order_quantity",
                    0.0,
                ),
            )
        )

        price = float(
            order.get(
                "price",
                order.get(
                    "current_price",
                    0.0,
                ),
            )
        )

        fills.append(
            {
                "fill_id": f"EROS89-FILL-{index}",
                "order_id": order.get(
                    "order_id",
                    f"EROS89-ORDER-{index}",
                ),
                "symbol": order.get(
                    "symbol",
                    "RELIANCE.NS",
                ),
                "action": order.get(
                    "action",
                    "BUY",
                ),
                "filled_quantity": quantity,
                "fill_price": price,
                "gross_value": round(
                    quantity * price,
                    6,
                ),
                "transaction_cost": round(
                    quantity * price * 0.001,
                    6,
                ),
                "fill_status": "FILLED",
            }
        )

    execution_payload = execution_result.to_dict()

    # ------------------------------------------------------
    # BLOCK 87 -> BLOCK 88 DECISION ID CONTRACT
    #
    # Block 87 is the authoritative source of decision_id.
    # Preserve that identity explicitly inside the decision
    # envelope consumed by Block 88.
    #
    # This is especially important for BLOCKED execution,
    # where there are no orders/fills but the originating
    # governance decision must remain auditable.
    # ------------------------------------------------------

    decision_id = execution_payload.get(
        "decision_id",
        "UNKNOWN-DECISION",
    )

    decision_envelope = {
        "decision_id": decision_id,
        "symbol": execution_payload.get(
            "symbol",
            "",
        ),
        "final_action": execution_payload.get(
            "action",
            "BLOCK",
        ),
        "execution_allowed": bool(
            execution_payload.get(
                "execution_allowed",
                False,
            )
        ),
        "execution_status": (
            "EXECUTION_READY"
            if bool(
                execution_payload.get(
                    "execution_allowed",
                    False,
                )
            )
            else "BLOCKED"
        ),
    }

    return {
        **execution_payload,
        "decision": decision_envelope,
        "execution_status": decision_envelope[
            "execution_status"
        ],
        "fills": fills,
        "broker_submission": False,
        "live_order_submission": False,
    }


def run_block89_self_test():
    bridge = EROSBlock87ExecutionBridge()
    audit_engine = EROSBlock88AuditReconciliationEngine()
    settlement_engine = EROSBlock89SettlementEngine()

    # ------------------------------------------------------
    # TEST 1 - APPROVED EXECUTION -> BLOCK 88 CERTIFIED
    # ------------------------------------------------------

    decision = _approved_decision()

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

    execution_payload = _paper_execution_payload(
        execution
    )

    orders = execution_payload["orders"]
    fills = execution_payload["fills"]

    audit_result = audit_engine.audit_and_certify(
        execution_payload,
        expected_orders=orders,
        expected_fills=fills,
    )

    assert audit_result["status"] == "PASS", (
        audit_result
    )

    assert (
        audit_result["certificate"]["status"]
        == "CERTIFIED"
    )

    assert (
        audit_result["certificate"][
            "reconciliation_status"
        ]
        == "RECONCILED"
    )

    # ------------------------------------------------------
    # TEST 2 - CERTIFIED -> SETTLED
    # ------------------------------------------------------

    settlement_payload = {
        **audit_result,
        "orders": orders,
        "fills": fills,
    }

    settlement = settlement_engine.settle(
        settlement_payload,
        orders=orders,
        fills=fills,
    )

    assert settlement["status"] == "PASS", settlement

    assert (
        settlement["settlement"]["settlement_status"]
        == "SETTLED"
    )

    assert (
        settlement["certificate"]["status"]
        == "CERTIFIED"
    )

    assert (
        settlement["settlement"][
            "paper_settlement"
        ]
        is True
    )

    assert (
        settlement["settlement"][
            "broker_submission"
        ]
        is False
    )

    assert (
        settlement["settlement"][
            "live_order_submission"
        ]
        is False
    )

    # ------------------------------------------------------
    # TEST 3 - DUPLICATE SETTLEMENT
    # ------------------------------------------------------

    duplicate = settlement_engine.settle(
        settlement_payload,
        orders=orders,
        fills=fills,
    )

    assert duplicate["status"] == "DUPLICATE", (
        duplicate
    )

    assert (
        duplicate["certificate"]["status"]
        == "DUPLICATE"
    )

    # ------------------------------------------------------
    # TEST 4 - BLOCKED EXECUTION CANNOT SETTLE
    # ------------------------------------------------------

    blocked_execution = bridge.execute(
        _blocked_decision(),
        [
            {
                "symbol": "RELIANCE.NS",
                "action": "BUY",
                "trade_weight": 0.10,
                "current_price": 2500.0,
            }
        ],
    )

    blocked_payload = _paper_execution_payload(
        blocked_execution
    )

    blocked_audit = audit_engine.audit_and_certify(
        blocked_payload,
        expected_orders=blocked_payload.get(
            "orders",
            [],
        ),
        expected_fills=blocked_payload.get(
            "fills",
            [],
        ),
    )

    assert blocked_audit["status"] == "BLOCKED", (
        blocked_audit
    )

    blocked_settlement = settlement_engine.settle(
        {
            **blocked_audit,
            "orders": blocked_payload.get(
                "orders",
                [],
            ),
            "fills": blocked_payload.get(
                "fills",
                [],
            ),
        },
        orders=blocked_payload.get(
            "orders",
            [],
        ),
        fills=blocked_payload.get(
            "fills",
            [],
        ),
    )

    assert (
        blocked_settlement["status"]
        == "BLOCKED"
    ), blocked_settlement

    assert (
        blocked_settlement["settlement"]["settlement_status"]
        == "BLOCKED"
    )

    # ------------------------------------------------------
    # TEST 5 - NON-BYPASS INVARIANT
    # ------------------------------------------------------

    assert (
        blocked_settlement["settlement"][
            "settlement_allowed"
        ]
        is False
    )

    assert (
        blocked_settlement["settlement"][
            "broker_submission"
        ]
        is False
    )

    assert (
        blocked_settlement["settlement"][
            "live_order_submission"
        ]
        is False
    )

    return {
        "status": "PASS",
        "settled_status": settlement["status"],
        "settlement_certificate": (
            settlement["certificate"]["status"]
        ),
        "duplicate_status": duplicate["status"],
        "blocked_status": blocked_settlement["status"],
        "blocked_settlement": (
            blocked_settlement["settlement"][
                "settlement_status"
            ]
        ),
        "non_bypass_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }


if __name__ == "__main__":
    print(run_block89_self_test())


