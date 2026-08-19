from copy import deepcopy

from services.quantitative.block97_stress_readiness_gate import (
    EROSBlock97StressReadinessGate,
)


def base_decision():
    return {
        "status": "CERTIFIED",
        "decision_status": "CERTIFIED",
        "decision": "ADMITTED",
        "decision_id": "EROS96-STRESS-DECISION-001",
        "block_id": "96",
        "engine_version": "96.1.0",
        "source_block": "95",
        "source_gate_id": "EROS95-STRESS-GATE-001",
        "source_certificate_id": "EROS94-STRESS-001",
        "scenario_count": 2,
        "scenario_ids": [
            "EROS94-DOWN-001",
            "EROS94-UP-001",
        ],
        "decision_reason": "STRESS_EVIDENCE_ADMITTED",
        "policy": {
            "min_scenarios": 1,
        },
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
    }


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def main():

    print("=" * 58)
    print("EROS 3.0 - BLOCK 97 SELF TEST")
    print("=" * 58)

    engine = EROSBlock97StressReadinessGate()
    tests = 0

    # 1
    result = engine.certify(
        decision=base_decision()
    )

    first = result
    tests += 1
    check(
        result["status"] == "CERTIFIED",
        "valid decision must certify",
    )

    # 2
    tests += 1
    check(
        result["readiness_status"] == "READY",
        "ADMITTED must become READY",
    )

    # 3
    tests += 1
    check(
        result["block_id"] == "97",
        "block id must be 97",
    )

    # 4
    tests += 1
    check(
        result["source_block"] == "96",
        "source block must be 96",
    )

    # 5
    tests += 1
    check(
        result["source_decision_id"]
        == "EROS96-STRESS-DECISION-001",
        "decision lineage lost",
    )

    # 6
    tests += 1
    check(
        result["source_gate_id"]
        == "EROS95-STRESS-GATE-001",
        "gate lineage lost",
    )

    # 7
    tests += 1
    check(
        result["source_certificate_id"]
        == "EROS94-STRESS-001",
        "certificate lineage lost",
    )

    # 8
    tests += 1
    check(
        result["scenario_count"] == 2,
        "scenario count lost",
    )

    # 9
    tests += 1
    check(
        len(result["scenario_ids"]) == 2,
        "scenario ids lost",
    )

    # 10
    tests += 1
    check(
        result["decision"] == "ADMITTED",
        "decision lost",
    )

    # 11
    tests += 1
    check(
        result["readiness_reason"]
        == "STRESS_DECISION_ADMITTED",
        "readiness reason invalid",
    )

    # 12
    tests += 1
    check(
        result["non_mutation_invariant"] is True,
        "non mutation invariant failed",
    )

    # 13
    tests += 1
    check(
        result["broker_submission"] is False,
        "broker submission must remain false",
    )

    # 14
    tests += 1
    check(
        result["live_order_submission"] is False,
        "live order submission must remain false",
    )

    # 15
    rejected = base_decision()
    rejected["decision"] = "REJECTED"
    rejected["decision_reason"] = "STRESS_POLICY_REJECTED"

    review = engine.certify(
        decision=rejected
    )

    tests += 1
    check(
        review["readiness_status"] == "REVIEW",
        "REJECTED must become REVIEW",
    )

    # 16
    tests += 1
    check(
        review["decision"] == "REJECTED",
        "rejected decision lost",
    )

    # 17
    invalid = base_decision()
    invalid["block_id"] = "95"

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "invalid source block must block",
    )

    # 18
    invalid = base_decision()
    invalid["decision_id"] = ""

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "missing decision id must block",
    )

    # 19
    invalid = base_decision()
    invalid["scenario_count"] = 3

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "scenario mismatch must block",
    )

    # 20
    invalid = base_decision()
    invalid["non_mutation_invariant"] = False

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "mutation invariant failure must block",
    )

    # 21
    invalid = base_decision()
    invalid["broker_submission"] = True

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "broker submission must block",
    )

    # 22
    invalid = base_decision()
    invalid["live_order_submission"] = True

    blocked = engine.certify(
        decision=invalid
    )

    tests += 1
    check(
        blocked["status"] == "BLOCKED",
        "live execution must block",
    )

    # 23
    original = base_decision()
    before = deepcopy(original)

    engine.certify(
        decision=original
    )

    tests += 1
    check(
        original == before,
        "input was mutated",
    )

    # 24
    duplicate_source = base_decision()

    duplicate_first = engine.certify(
        decision=duplicate_source
    )

    duplicate_second = engine.certify(
        decision=duplicate_source
    )

    tests += 1
    check(
        duplicate_first["status"] == "DUPLICATE",
        "existing readiness must be detected",
    )

    # 25
    snapshot = engine.snapshot()

    tests += 1
    check(
        len(snapshot["readiness"]) >= 2,
        "snapshot must preserve readiness records",
    )

    print("=" * 58)
    print("STATUS : PASS")
    print("BLOCK  : 97")
    print("CHECKS :", tests)
    print(
        "READINESS ID:",
        first["readiness_id"],
    )
    print(
        "READINESS   :",
        first["readiness_status"],
    )
    print(
        "REVIEW TEST :",
        review["readiness_status"],
    )
    print(
        "NON-MUTATION:",
        first["non_mutation_invariant"],
    )
    print(
        "EXECUTION BLOCKED:",
        (
            first["broker_submission"] is False
            and first["live_order_submission"] is False
        ),
    )
    print(
        "EROS 3.0 Block 97 self-test passed"
    )
    print("=" * 58)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())




