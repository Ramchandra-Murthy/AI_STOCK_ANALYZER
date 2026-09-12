from __future__ import annotations

from copy import deepcopy

from services.quantitative.block99_execution_intent_authorization_gate import (
    EROSBlock99ExecutionIntentAuthorizationGate,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def base_governance():
    return {
        "status": "CERTIFIED",
        "governance_status": "APPROVED",
        "governance_id": "EROS98-STRESS-GOVERNANCE-TEST",
        "block_id": "98",
        "engine_version": "EROS-3.0-BLOCK-98",
        "created_at": "2026-08-19T00:00:00+00:00",
        "source_block": "97",
        "source_readiness_id": "EROS97-STRESS-READINESS-TEST",
        "source_decision_id": "EROS96-STRESS-DECISION-TEST",
        "source_gate_id": "EROS95-STRESS-GATE-TEST",
        "source_certificate_id": "EROS94-STRESS-CERTIFICATE-TEST",
        "readiness_status": "READY",
        "decision": "ADMITTED",
        "scenario_count": 2,
        "scenario_ids": [
            "SCENARIO-A",
            "SCENARIO-B",
        ],
        "governance": "APPROVED",
        "execution_action": "EXECUTE",
        "governance_reason": "Approved",
        "portfolio_mutation": False,
        "valuation_mutation": False,
        "performance_mutation": False,
        "risk_mutation": False,
        "optimization": False,
        "order_creation": False,
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
        "execution_blocked": True,
    }


def main():
    print("")
    print("=" * 62)
    print("EROS 3.0 - BLOCK 99 SELF TEST")
    print("EXECUTION INTENT AUTHORIZATION GATE")
    print("=" * 62)

    engine = EROSBlock99ExecutionIntentAuthorizationGate()

    tests = 0

    # 1 valid certification
    governance = base_governance()
    result = engine.certify(governance=governance)
    tests += 1
    check(
        result["status"] == "CERTIFIED",
        "valid governance must certify",
    )

    # 2 intent status
    tests += 1
    check(
        result["intent_status"] == "AUTHORIZED",
        "APPROVED governance must become AUTHORIZED",
    )

    # 3 action
    tests += 1
    check(
        result["intent_action"] == "PREPARE",
        "APPROVED governance must become PREPARE",
    )

    # 4 source block
    tests += 1
    check(
        result["source_block"] == "98",
        "source block must be 98",
    )

    # 5 lineage
    tests += 1
    check(
        result["source_governance_id"] == governance["governance_id"],
        "governance lineage must be preserved",
    )

    # 6 readiness lineage
    tests += 1
    check(
        result["source_readiness_id"] == governance["source_readiness_id"],
        "readiness lineage must be preserved",
    )

    # 7 decision lineage
    tests += 1
    check(
        result["source_decision_id"] == governance["source_decision_id"],
        "decision lineage must be preserved",
    )

    # 8 gate lineage
    tests += 1
    check(
        result["source_gate_id"] == governance["source_gate_id"],
        "gate lineage must be preserved",
    )

    # 9 certificate lineage
    tests += 1
    check(
        result["source_certificate_id"] == governance["source_certificate_id"],
        "certificate lineage must be preserved",
    )

    # 10 scenario count
    tests += 1
    check(
        result["scenario_count"] == 2,
        "scenario count must be preserved",
    )

    # 11 scenario IDs
    tests += 1
    check(
        result["scenario_ids"] == governance["scenario_ids"],
        "scenario IDs must be preserved",
    )

    # 12 REVIEW mapping
    review = base_governance()
    review["governance_status"] = "REVIEW"
    review["governance"] = "REVIEW"
    review["execution_action"] = "HOLD"

    review_result = engine.certify(governance=review)

    tests += 1
    check(
        review_result["intent_status"] == "REVIEW",
        "REVIEW governance must become REVIEW",
    )

    # 13 HOLD mapping
    tests += 1
    check(
        review_result["intent_action"] == "HOLD",
        "REVIEW governance must become HOLD",
    )

    # 14 BLOCKED mapping
    blocked = base_governance()
    blocked["governance_status"] = "BLOCKED"
    blocked["governance"] = "BLOCKED"
    blocked["execution_action"] = "BLOCK"
    blocked["readiness_status"] = "BLOCKED"

    blocked_result = engine.certify(governance=blocked)

    tests += 1
    check(
        blocked_result["intent_status"] == "BLOCKED",
        "BLOCKED governance must become BLOCKED",
    )

    # 15 BLOCK action
    tests += 1
    check(
        blocked_result["intent_action"] == "BLOCK",
        "BLOCKED governance must become BLOCK",
    )

    # 16 malformed input
    malformed = engine.certify(governance=None)

    tests += 1
    check(
        malformed["status"] == "BLOCKED",
        "malformed governance must block",
    )

    # 17 wrong block
    wrong_block = base_governance()
    wrong_block["block_id"] = "97"

    wrong_result = engine.certify(governance=wrong_block)

    tests += 1
    check(
        wrong_result["status"] == "BLOCKED",
        "wrong source block must block",
    )

    # 18 missing governance ID
    missing = base_governance()
    del missing["governance_id"]

    missing_result = engine.certify(governance=missing)

    tests += 1
    check(
        missing_result["status"] == "BLOCKED",
        "missing governance ID must block",
    )

    # 19 scenario mismatch
    mismatch = base_governance()
    mismatch["scenario_count"] = 3

    mismatch_result = engine.certify(governance=mismatch)

    tests += 1
    check(
        mismatch_result["status"] == "BLOCKED",
        "scenario mismatch must block",
    )

    # 20 non-mutation invariant
    unsafe = base_governance()
    unsafe["non_mutation_invariant"] = False

    unsafe_result = engine.certify(governance=unsafe)

    tests += 1
    check(
        unsafe_result["status"] == "BLOCKED",
        "failed non-mutation invariant must block",
    )

    # 21 portfolio mutation
    unsafe = base_governance()
    unsafe["portfolio_mutation"] = True

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "portfolio mutation must block",
    )

    # 22 optimization
    unsafe = base_governance()
    unsafe["optimization"] = True

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "optimization must block",
    )

    # 23 order creation
    unsafe = base_governance()
    unsafe["order_creation"] = True

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "order creation must block",
    )

    # 24 broker
    unsafe = base_governance()
    unsafe["broker_submission"] = True

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "broker submission must block",
    )

    # 25 live execution
    unsafe = base_governance()
    unsafe["live_order_submission"] = True

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "live submission must block",
    )

    # 26 execution blocked
    unsafe = base_governance()
    unsafe["execution_blocked"] = False

    tests += 1
    check(
        engine.certify(governance=unsafe)["status"] == "BLOCKED",
        "execution blocking invariant must hold",
    )

    # 27 duplicate detection
    duplicate = engine.certify(governance=base_governance())

    tests += 1
    check(
        duplicate["status"] == "DUPLICATE",
        "same governance must be duplicate",
    )

    # 28 snapshot
    snapshot = engine.snapshot()

    tests += 1
    check(
        len(snapshot["intents"]) >= 3,
        "snapshot must preserve intent records",
    )

    # 29 input non-mutation
    original = base_governance()
    original_copy = deepcopy(original)

    fresh_engine = EROSBlock99ExecutionIntentAuthorizationGate()

    fresh_engine.certify(governance=original)

    tests += 1
    check(
        original == original_copy,
        "input governance must not be mutated",
    )

    # 30 safety invariants of successful result
    tests += 1
    check(
        result["portfolio_mutation"] is False
        and result["valuation_mutation"] is False
        and result["performance_mutation"] is False
        and result["risk_mutation"] is False
        and result["optimization"] is False
        and result["order_creation"] is False
        and result["non_mutation_invariant"] is True
        and result["broker_submission"] is False
        and result["live_order_submission"] is False
        and result["execution_blocked"] is True,
        "all safety invariants must hold",
    )

    print("=" * 62)
    print("STATUS            : PASS")
    print("BLOCK             : 99")
    print("CHECKS            :", tests)
    print("INTENT ID         :", result["intent_id"])
    print("INTENT STATUS     :", result["intent_status"])
    print("INTENT ACTION     :", result["intent_action"])
    print("SOURCE BLOCK      :", result["source_block"])
    print("NON-MUTATION      :", result["non_mutation_invariant"])
    print("ORDER CREATION    :", result["order_creation"])
    print("BROKER            :", result["broker_submission"])
    print("LIVE EXEC         :", result["live_order_submission"])
    print("EXECUTION BLOCKED :", result["execution_blocked"])
    print("")
    print("EROS 3.0 Block 99 self-test passed")
    print("=" * 62)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
