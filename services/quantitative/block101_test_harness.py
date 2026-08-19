from __future__ import annotations

from copy import deepcopy

from services.quantitative.block100_paper_execution_fill_gate import (
    EROSBlock100PaperExecutionFillGate,
)

from services.quantitative.block101_execution_evidence_reconciliation import (
    EROSBlock101ExecutionEvidenceReconciliationGate,
)


def main() -> int:

    print("")
    print("=" * 62)
    print("EROS 3.0 - BLOCK 101 SELF TEST")
    print("=" * 62)

    b100 = EROSBlock100PaperExecutionFillGate()
    b101 = EROSBlock101ExecutionEvidenceReconciliationGate()

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
            "intent_id": "EROS99-B101-TEST-001",
            "block_id": "99",
            "source_block": "98",
            "source_readiness_id": "EROS97-B101-READINESS-001",
            "source_governance_id": "EROS98-B101-GOVERNANCE-001",
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

    # ==========================================================
    # 1. BLOCK 100 -> FILLED
    # ==========================================================

    execution = b100.certify(
        intent=base_intent()
    )

    check(
        execution["status"] == "CERTIFIED",
        "Block 100 must certify valid intent",
    )

    check(
        execution["execution_status"] == "SIMULATED",
        "Block 100 must produce SIMULATED execution",
    )

    check(
        execution["fill_status"] == "FILLED",
        "Block 100 must produce FILLED result",
    )

    # ==========================================================
    # 2. BLOCK 100 -> BLOCK 101
    # ==========================================================

    reconciliation = b101.certify(
        execution=execution
    )

    check(
        reconciliation["status"] == "CERTIFIED",
        "Block 101 must certify valid execution evidence",
    )

    check(
        reconciliation["block_id"] == "101",
        "Block ID must be 101",
    )

    check(
        reconciliation["source_block"] == "100",
        "Source block must be 100",
    )

    check(
        reconciliation["reconciliation_status"] == "RECONCILED",
        "Filled execution must reconcile",
    )

    check(
        reconciliation["source_execution_id"]
        == execution["execution_id"],
        "Execution lineage must survive",
    )

    check(
        reconciliation["source_intent_id"]
        == execution["source_intent_id"],
        "Intent lineage must survive",
    )

    # ==========================================================
    # 3. QUANTITY RECONCILIATION
    # ==========================================================

    check(
        reconciliation["requested_quantity"]
        == execution["requested_quantity"],
        "Requested quantity must reconcile",
    )

    check(
        reconciliation["filled_quantity"]
        == execution["filled_quantity"],
        "Filled quantity must reconcile",
    )

    check(
        reconciliation["quantity_reconciled"] is True,
        "Quantity reconciliation must pass",
    )

    # ==========================================================
    # 4. PRICE / VALUE / COST
    # ==========================================================

    check(
        reconciliation["price_reconciled"] is True,
        "Price reconciliation must pass",
    )

    check(
        reconciliation["value_reconciled"] is True,
        "Value reconciliation must pass",
    )

    check(
        reconciliation["cost_reconciled"] is True,
        "Cost reconciliation must pass",
    )

    # ==========================================================
    # 5. LINEAGE
    # ==========================================================

    check(
        reconciliation["lineage_reconciled"] is True,
        "Lineage reconciliation must pass",
    )

    # ==========================================================
    # 6. SAFETY
    # ==========================================================

    check(
        reconciliation["non_mutation_invariant"] is True,
        "Non-mutation invariant must remain true",
    )

    check(
        reconciliation["broker_submission"] is False,
        "Broker submission must remain false",
    )

    check(
        reconciliation["live_order_submission"] is False,
        "Live execution must remain false",
    )

    check(
        reconciliation["execution_blocked"] is True,
        "Execution must remain blocked",
    )

    # ==========================================================
    # 7. PARTIAL EXECUTION
    # ==========================================================

    partial_execution = b100.certify(
        intent=base_intent(),
        fill_ratio=0.5,
    )

    check(
        partial_execution["status"] == "CERTIFIED",
        "Partial Block 100 execution must certify",
    )

    check(
        partial_execution["execution_status"] == "PARTIAL",
        "Execution status must be PARTIAL",
    )

    check(
        partial_execution["fill_status"] == "PARTIAL",
        "Fill status must be PARTIAL",
    )

    partial_reconciliation = b101.certify(
        execution=partial_execution
    )

    check(
        partial_reconciliation["status"] == "CERTIFIED",
        "Partial evidence must certify",
    )

    check(
        partial_reconciliation["reconciliation_status"]
        == "RECONCILED",
        "Partial evidence must reconcile",
    )

    check(
        partial_reconciliation["quantity_reconciled"] is True,
        "Partial quantity must reconcile",
    )

    # ==========================================================
    # 8. BLOCKED EXECUTION
    # ==========================================================

    hold = base_intent()
    hold["action"] = "HOLD"
    hold["quantity"] = 0.0

    blocked_execution = b100.certify(
        intent=hold
    )

    check(
        blocked_execution["status"] == "BLOCKED",
        "HOLD execution must be blocked",
    )

    blocked_reconciliation = b101.certify(
        execution=blocked_execution
    )

    check(
        blocked_reconciliation["status"] == "BLOCKED",
        "Blocked source execution must remain BLOCKED",
    )

    check(
        blocked_reconciliation["reconciliation_status"]
        == "BLOCKED",
        "Blocked execution must reconcile as BLOCKED",
    )

    check(
        blocked_reconciliation["execution_blocked"] is True,
        "Blocked execution must remain blocked",
    )

    check(
        blocked_reconciliation["broker_submission"] is False,
        "Blocked execution must not reach broker",
    )

    check(
        blocked_reconciliation["live_order_submission"] is False,
        "Blocked execution must not reach live execution",
    )

    # ==========================================================
    # 9. MALFORMED SOURCE
    # ==========================================================

    malformed = deepcopy(execution)
    malformed["execution_id"] = ""

    malformed_result = b101.certify(
        execution=malformed
    )

    check(
        malformed_result["status"] == "BLOCKED",
        "Missing execution ID must block",
    )

    # ==========================================================
    # 10. WRONG SOURCE BLOCK
    # ==========================================================

    wrong_source = deepcopy(execution)
    wrong_source["block_id"] = "99"

    wrong_source_result = b101.certify(
        execution=wrong_source
    )

    check(
        wrong_source_result["status"] == "BLOCKED",
        "Wrong source block must block",
    )

    # ==========================================================
    # 11. QUANTITY INCONSISTENCY
    # ==========================================================

    bad_quantity = deepcopy(execution)
    bad_quantity["filled_quantity"] = (
        bad_quantity["requested_quantity"] + 1
    )

    bad_quantity_result = b101.certify(
        execution=bad_quantity
    )

    check(
        bad_quantity_result["status"] == "BLOCKED",
        "Filled quantity exceeding requested must block",
    )

    # ==========================================================
    # 12. INPUT NON-MUTATION
    # ==========================================================

    original = deepcopy(execution)
    original_copy = deepcopy(execution)

    b101.certify(
        execution=original
    )

    check(
        original == original_copy,
        "Block 101 must not mutate input",
    )

    # ==========================================================
    # 13. SNAPSHOT
    # ==========================================================

    snapshot = b101.snapshot()

    check(
        snapshot["block_id"] == "101",
        "Snapshot block ID must be 101",
    )

    check(
        len(snapshot["reconciliation"]) >= 1,
        "Snapshot must preserve reconciliation evidence",
    )

    print("")
    print("=" * 62)
    print("STATUS              : PASS")
    print("BLOCK               : 101")
    print("CHECKS              :", passed)
    print(
        "RECONCILIATION      :",
        reconciliation["reconciliation_status"],
    )
    print(
        "PARTIAL             :",
        partial_reconciliation["reconciliation_status"],
    )
    print(
        "BLOCKED             :",
        blocked_reconciliation["reconciliation_status"],
    )
    print(
        "NON-MUTATION        :",
        reconciliation["non_mutation_invariant"],
    )
    print(
        "BROKER              :",
        reconciliation["broker_submission"],
    )
    print(
        "LIVE EXEC           :",
        reconciliation["live_order_submission"],
    )
    print(
        "EXECUTION BLOCKED   :",
        reconciliation["execution_blocked"],
    )
    print("")
    print("EROS 3.0 Block 101 self-test passed")
    print("=" * 62)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


