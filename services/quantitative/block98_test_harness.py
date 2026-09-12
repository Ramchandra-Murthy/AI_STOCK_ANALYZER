from __future__ import annotations

from copy import deepcopy

from services.quantitative.block98_execution_governance_bridge import (
    EROSBlock98ExecutionGovernanceBridge,
)


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def base_ready() -> dict:
    return {
        "status": "CERTIFIED",
        "readiness_status": "READY",
        "readiness_id": "EROS97-TEST-READINESS-001",
        "block_id": "97",
        "source_block": "96",
        "source_decision_id": "EROS96-TEST-DECISION-001",
        "source_gate_id": "EROS95-TEST-GATE-001",
        "source_certificate_id": "EROS94-TEST-CERT-001",
        "decision": "ADMITTED",
        "scenario_count": 2,
        "scenario_ids": [
            "SCENARIO-DOWN-001",
            "SCENARIO-UP-001",
        ],
        "readiness_reason": "Stress readiness satisfies policy.",
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }


def main() -> int:
    print("=" * 58)
    print("EROS 3.0 - BLOCK 98 SELF TEST")
    print("=" * 58)

    engine = EROSBlock98ExecutionGovernanceBridge()

    tests = 0

    # 1
    result = engine.certify(decision=base_ready())
    tests += 1
    check(
        result["status"] == "CERTIFIED",
        "READY source must certify",
    )

    # 2
    tests += 1
    check(
        result["governance_status"] == "APPROVED",
        "READY must map to APPROVED",
    )

    # 3
    tests += 1
    check(
        result["execution_action"] == "EXECUTE",
        "APPROVED must map to EXECUTE",
    )

    # 4
    tests += 1
    check(
        result["block_id"] == "98",
        "block id must be 98",
    )

    # 5
    tests += 1
    check(
        result["source_block"] == "97",
        "source block must be 97",
    )

    # 6
    tests += 1
    check(
        result["source_readiness_id"] == base_ready()["readiness_id"],
        "readiness lineage must be preserved",
    )

    # 7
    tests += 1
    check(
        result["source_decision_id"] == base_ready()["source_decision_id"],
        "decision lineage must be preserved",
    )

    # 8
    tests += 1
    check(
        result["source_gate_id"] == base_ready()["source_gate_id"],
        "gate lineage must be preserved",
    )

    # 9
    tests += 1
    check(
        result["source_certificate_id"] == base_ready()["source_certificate_id"],
        "certificate lineage must be preserved",
    )

    # 10
    tests += 1
    check(
        result["scenario_count"] == 2,
        "scenario count must be preserved",
    )

    # 11
    tests += 1
    check(
        len(result["scenario_ids"]) == 2,
        "scenario ids must be preserved",
    )

    # 12
    tests += 1
    check(
        result["non_mutation_invariant"] is True,
        "non-mutation invariant must hold",
    )

    # 13
    tests += 1
    check(
        result["broker_submission"] is False,
        "broker submission must be false",
    )

    # 14
    tests += 1
    check(
        result["live_order_submission"] is False,
        "live execution must be false",
    )

    # 15
    tests += 1
    check(
        result["execution_blocked"] is True,
        "execution remains blocked",
    )

    # 16 REVIEW
    review = deepcopy(base_ready())
    review["readiness_id"] = "EROS97-TEST-READINESS-REVIEW"
    review["readiness_status"] = "REVIEW"

    review_result = engine.certify(decision=review)

    tests += 1
    check(
        review_result["governance_status"] == "REVIEW",
        "REVIEW must map to REVIEW",
    )

    # 17
    tests += 1
    check(
        review_result["execution_action"] == "HOLD",
        "REVIEW must map to HOLD",
    )

    # 18 BLOCKED
    blocked = deepcopy(base_ready())
    blocked["readiness_id"] = "EROS97-TEST-READINESS-BLOCKED"
    blocked["readiness_status"] = "BLOCKED"

    blocked_result = engine.certify(decision=blocked)

    tests += 1
    check(
        blocked_result["governance_status"] == "BLOCKED",
        "BLOCKED must map to BLOCKED",
    )

    # 19
    tests += 1
    check(
        blocked_result["execution_action"] == "BLOCK",
        "BLOCKED must map to BLOCK",
    )

    # 20 invalid source status
    invalid = deepcopy(base_ready())
    invalid["readiness_id"] = "EROS97-TEST-INVALID-STATUS"
    invalid["status"] = "BLOCKED"

    invalid_result = engine.certify(decision=invalid)

    tests += 1
    check(
        invalid_result["status"] == "BLOCKED",
        "invalid source must be blocked",
    )

    # 21 invalid source block
    invalid = deepcopy(base_ready())
    invalid["readiness_id"] = "EROS97-TEST-INVALID-BLOCK"
    invalid["block_id"] = "96"

    invalid_result = engine.certify(decision=invalid)

    tests += 1
    check(
        invalid_result["status"] == "BLOCKED",
        "invalid block lineage must be blocked",
    )

    # 22 scenario mismatch
    invalid = deepcopy(base_ready())
    invalid["readiness_id"] = "EROS97-TEST-SCENARIO-MISMATCH"
    invalid["scenario_count"] = 3

    invalid_result = engine.certify(decision=invalid)

    tests += 1
    check(
        invalid_result["status"] == "BLOCKED",
        "scenario mismatch must be blocked",
    )

    # 23 mutation violation
    invalid = deepcopy(base_ready())
    invalid["readiness_id"] = "EROS97-TEST-MUTATION"
    invalid["non_mutation_invariant"] = False

    invalid_result = engine.certify(decision=invalid)

    tests += 1
    check(
        invalid_result["status"] == "BLOCKED",
        "mutation violation must be blocked",
    )

    # 24 duplicate
    duplicate_source = deepcopy(base_ready())
    duplicate_source["readiness_id"] = "EROS97-TEST-DUPLICATE"

    duplicate_first = engine.certify(decision=duplicate_source)

    duplicate_second = engine.certify(decision=duplicate_source)

    tests += 1
    check(
        duplicate_first["status"] == "CERTIFIED",
        "first governance record must certify",
    )

    # 25
    tests += 1
    check(
        duplicate_second["status"] == "DUPLICATE",
        "duplicate governance must be detected",
    )

    # 26 snapshot
    snapshot = engine.snapshot()

    tests += 1
    check(
        len(snapshot["governance"]) >= 4,
        "snapshot must preserve governance records",
    )

    # 27 non-mutation of input
    original = base_ready()
    original_copy = deepcopy(original)

    engine.certify(decision=original)

    tests += 1
    check(
        original == original_copy,
        "input decision must not be mutated",
    )

    print("=" * 58)
    print("STATUS : PASS")
    print("BLOCK  : 98")
    print("CHECKS :", tests)
    print(
        "GOVERNANCE ID:",
        result["governance_id"],
    )
    print(
        "GOVERNANCE   :",
        result["governance_status"],
    )
    print(
        "ACTION       :",
        result["execution_action"],
    )
    print(
        "NON-MUTATION :",
        result["non_mutation_invariant"],
    )
    print(
        "BROKER       :",
        result["broker_submission"],
    )
    print(
        "LIVE EXEC    :",
        result["live_order_submission"],
    )
    print(
        "EXECUTION BLOCKED:",
        result["execution_blocked"],
    )
    print("EROS 3.0 Block 98 self-test passed")
    print("=" * 58)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
