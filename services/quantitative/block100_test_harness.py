from __future__ import annotations

from copy import deepcopy

from services.quantitative.block100_paper_execution_fill_gate import (
    EROSBlock100PaperExecutionFillGate,
)


def main() -> int:

    print("==========================================================")
    print("EROS 3.0 - BLOCK 100 SELF TEST")
    print("==========================================================")

    engine = EROSBlock100PaperExecutionFillGate()

    tests = 0
    passed = 0

    def check(condition, message):
        nonlocal tests, passed
        tests += 1

        if not condition:
            raise AssertionError(message)

        passed += 1

    def base_intent():
        return {
            "status": "CERTIFIED",
            "intent_status": "AUTHORIZED",
            "authorization_status": "AUTHORIZED",
            "intent_id": "EROS99-TEST-INTENT-001",
            "block_id": "99",
            "source_block": "98",
            "source_readiness_id": "EROS97-TEST-READINESS-001",
            "source_governance_id": "EROS98-TEST-GOVERNANCE-001",
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "quantity": 100.0,
            "reference_price": 2500.0,
            "execution_allowed": True,
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
            "execution_blocked": True,
        }

    # 1
    result = engine.certify(intent=base_intent())
    check(
        result["status"] == "CERTIFIED",
        "valid intent must certify",
    )

    # 2
    check(
        result["execution_status"] == "SIMULATED",
        "full fill must be simulated",
    )

    # 3
    check(
        result["block_id"] == "100",
        "block id must be 100",
    )

    # 4
    check(
        result["source_block"] == "99",
        "source block must be 99",
    )

    # 5
    check(
        result["source_intent_id"] == "EROS99-TEST-INTENT-001",
        "intent lineage must survive",
    )

    # 6
    check(
        result["filled_quantity"] == 100.0,
        "full quantity must fill",
    )

    # 7
    check(
        result["fill_status"] == "FILLED",
        "full fill status required",
    )

    # 8
    check(
        result["fill_price"] > 2500.0,
        "BUY slippage must increase fill price",
    )

    # 9
    check(
        result["slippage_bps"] == 5.0,
        "BUY slippage must be 5 bps",
    )

    # 10
    check(
        result["transaction_cost"] > 0,
        "transaction cost must be present",
    )

    # 11
    check(
        result["broker_submission"] is False,
        "broker submission must remain false",
    )

    # 12
    check(
        result["live_order_submission"] is False,
        "live submission must remain false",
    )

    # 13
    check(
        result["execution_blocked"] is True,
        "live execution must remain blocked",
    )

    # 14
    check(
        result["non_mutation_invariant"] is True,
        "non-mutation invariant required",
    )

    # 15
    partial = engine.certify(
        intent=base_intent(),
        fill_ratio=0.5,
    )

    check(
        partial["execution_status"] == "PARTIAL",
        "partial fill must be detected",
    )

    # 16
    check(
        partial["filled_quantity"] == 50.0,
        "partial quantity must be 50",
    )

    # 17
    check(
        partial["fill_status"] == "PARTIAL",
        "partial fill status required",
    )

    # 18
    hold = base_intent()
    hold["action"] = "HOLD"
    hold["quantity"] = 0.0

    hold_result = engine.certify(intent=hold)

    check(
        hold_result["status"] == "BLOCKED",
        "HOLD must be blocked",
    )

    # 19
    check(
        hold_result["fill_status"] == "BLOCKED",
        "HOLD cannot produce a fill",
    )

    # 20
    unauthorized = base_intent()
    unauthorized["authorization_status"] = "REJECTED"

    rejected = engine.certify(intent=unauthorized)

    check(
        rejected["status"] == "BLOCKED",
        "unauthorized intent must block",
    )

    # 21
    invalid_symbol = base_intent()
    invalid_symbol["symbol"] = ""

    blocked = engine.certify(intent=invalid_symbol)

    check(
        blocked["status"] == "BLOCKED",
        "missing symbol must block",
    )

    # 22
    invalid_price = base_intent()
    invalid_price["reference_price"] = 0

    blocked_price = engine.certify(intent=invalid_price)

    check(
        blocked_price["status"] == "BLOCKED",
        "invalid price must block",
    )

    # 23
    invalid_broker = base_intent()
    invalid_broker["broker_submission"] = True

    blocked_broker = engine.certify(intent=invalid_broker)

    check(
        blocked_broker["status"] == "BLOCKED",
        "broker submission must be rejected",
    )

    # 24
    original = base_intent()
    original_copy = deepcopy(original)

    engine.certify(intent=original)

    check(
        original == original_copy,
        "input must not mutate",
    )

    # 25
    snapshot = engine.snapshot()

    check(
        snapshot["execution_count"] >= 1,
        "snapshot must preserve executions",
    )

    print("==========================================================")
    print("STATUS : PASS")
    print("BLOCK  : 100")
    print(
        "CHECKS :",
        passed,
    )
    print(
        "EXECUTION STATUS:",
        result["execution_status"],
    )
    print(
        "FILL STATUS:",
        result["fill_status"],
    )
    print(
        "EXECUTION ID:",
        result["execution_id"],
    )
    print(
        "NON-MUTATION:",
        result["non_mutation_invariant"],
    )
    print(
        "BROKER:",
        result["broker_submission"],
    )
    print(
        "LIVE EXEC:",
        result["live_order_submission"],
    )
    print(
        "EXECUTION BLOCKED:",
        result["execution_blocked"],
    )
    print("EROS 3.0 Block 100 self-test passed")
    print("==========================================================")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
