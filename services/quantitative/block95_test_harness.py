"""
EROS 3.0 - Block 95 Self-Test Harness

Adversarial architectural contract tests.

No broker, network, database, Celery, live execution,
or external market-data dependency.
"""

from __future__ import annotations

from copy import deepcopy

from .block95_stress_evidence_gate import (
    STATUS_BLOCKED,
    STATUS_CERTIFIED,
    STATUS_DUPLICATE,
    EROSBlock95StressEvidenceGate,
)


def _stress_certificate():
    return {
        "status": "CERTIFIED",
        "certificate_status": "CERTIFIED",
        "certificate_id": "EROS94-STRESS-001",
        "block_id": "EROS-BLOCK-94",
        "engine_version": "94.1.0",
        "valuation_id": "EROS91-VAL-001",
        "performance_id": "EROS92-PERF-001",
        "risk_certificate_id": "EROS93-RISK-001",
        "scenario_count": 2,
        "scenario_results": [
            {
                "status": "PASS",
                "scenario": {
                    "scenario_id": "EROS94-SCENARIO-DOWN-001",
                },
                "stressed_drawdown_pct": 12.5,
                "scenario_contribution": {
                    "portfolio_drawdown_pct": 12.5,
                },
            },
            {
                "status": "PASS",
                "scenario": {
                    "scenario_id": "EROS94-SCENARIO-UP-001",
                },
                "stressed_drawdown_pct": 0.0,
                "scenario_contribution": {
                    "portfolio_drawdown_pct": 0.0,
                },
            },
        ],
        "broker_submission": False,
        "live_order_submission": False,
    }


def _check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_block95_self_test() -> dict:
    checks = 0

    engine = EROSBlock95StressEvidenceGate()

    evidence = _stress_certificate()
    original = deepcopy(evidence)

    # --------------------------------------------------------
    # 1. Valid certified evidence
    # --------------------------------------------------------

    certificate = engine.certify(
        stress_certificate=evidence,
    )

    _check(
        certificate["status"] == STATUS_CERTIFIED,
        "valid stress evidence should be certified",
    )
    checks += 1

    _check(
        certificate["gate_status"] == STATUS_CERTIFIED,
        "gate status should be CERTIFIED",
    )
    checks += 1

    # --------------------------------------------------------
    # 2. Block 94 lineage
    # --------------------------------------------------------

    _check(
        certificate["source_block"] == "94",
        "source block lineage incorrect",
    )
    checks += 1

    _check(
        certificate["source_certificate_id"] == "EROS94-STRESS-001",
        "stress certificate lineage incorrect",
    )
    checks += 1

    # --------------------------------------------------------
    # 3. Block 95 identity
    # --------------------------------------------------------

    _check(
        certificate["block_id"] == "95",
        "Block 95 identity incorrect",
    )
    checks += 1

    _check(
        certificate["gate_id"].startswith("EROS95-STRESS-GATE-"),
        "Block 95 gate ID prefix incorrect",
    )
    checks += 1

    # --------------------------------------------------------
    # 4. Execution safety invariants
    # --------------------------------------------------------

    _check(
        certificate["broker_submission"] is False,
        "broker submission invariant failed",
    )
    checks += 1

    _check(
        certificate["live_order_submission"] is False,
        "live execution invariant failed",
    )
    checks += 1

    _check(
        certificate["non_mutation_invariant"] is True,
        "non-mutation invariant failed",
    )
    checks += 1

    # --------------------------------------------------------
    # 5. Input immutability
    # --------------------------------------------------------

    _check(
        evidence == original,
        "input stress evidence was mutated",
    )
    checks += 1

    # --------------------------------------------------------
    # 6. Duplicate gate
    # --------------------------------------------------------

    duplicate = engine.certify(
        stress_certificate=evidence,
    )

    _check(
        duplicate["status"] == STATUS_DUPLICATE,
        "identical certification must be duplicate",
    )
    checks += 1

    # --------------------------------------------------------
    # 7. Non-certified evidence blocked
    # --------------------------------------------------------

    blocked_evidence = deepcopy(evidence)
    blocked_evidence["status"] = "BLOCKED"

    blocked = engine.certify(
        stress_certificate=blocked_evidence,
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "blocked upstream evidence must be rejected",
    )
    checks += 1

    # --------------------------------------------------------
    # 8. Missing lineage blocked
    # --------------------------------------------------------

    missing_lineage = deepcopy(evidence)
    missing_lineage["certificate_id"] = ""

    result = engine.certify(
        stress_certificate=missing_lineage,
    )

    _check(
        result["status"] == STATUS_BLOCKED,
        "missing stress certificate lineage must be rejected",
    )
    checks += 1

    # --------------------------------------------------------
    # 9. Invalid scenario blocked
    # --------------------------------------------------------

    invalid_scenario = deepcopy(evidence)
    invalid_scenario["scenario_results"][0]["status"] = "BLOCKED"

    result = engine.certify(
        stress_certificate=invalid_scenario,
    )

    _check(
        result["status"] == STATUS_BLOCKED,
        "invalid scenario evidence must be rejected",
    )
    checks += 1

    # --------------------------------------------------------
    # 10. Duplicate scenario IDs blocked
    # --------------------------------------------------------

    duplicate_scenarios = deepcopy(evidence)
    duplicate_scenarios["scenario_results"][1]["scenario"][
        "scenario_id"
    ] = "EROS94-SCENARIO-DOWN-001"

    result = engine.certify(
        stress_certificate=duplicate_scenarios,
    )

    _check(
        result["status"] == STATUS_BLOCKED,
        "duplicate scenario IDs must be rejected",
    )
    checks += 1

    # --------------------------------------------------------
    # 11. Policy gate
    # --------------------------------------------------------

    policy_engine = EROSBlock95StressEvidenceGate()

    result = policy_engine.certify(
        stress_certificate=evidence,
        policy={
            "min_scenarios": 2,
            "max_stressed_drawdown_pct": 20.0,
        },
    )

    _check(
        result["status"] == STATUS_CERTIFIED,
        "valid policy-constrained evidence should pass",
    )
    checks += 1

    # --------------------------------------------------------
    # 12. Policy breach
    # --------------------------------------------------------

    policy_engine2 = EROSBlock95StressEvidenceGate()

    result = policy_engine2.certify(
        stress_certificate=evidence,
        policy={
            "min_scenarios": 2,
            "max_stressed_drawdown_pct": 10.0,
        },
    )

    _check(
        result["status"] == STATUS_BLOCKED,
        "drawdown policy breach must be blocked",
    )
    checks += 1

    # --------------------------------------------------------
    # 13. Forbidden execution content
    # --------------------------------------------------------

    execution_content = deepcopy(evidence)
    execution_content["metadata"] = {
        "submit_order": True,
    }

    result = engine.certify(
        stress_certificate=execution_content,
    )

    _check(
        result["status"] == STATUS_BLOCKED,
        "execution content must be rejected",
    )
    checks += 1

    # --------------------------------------------------------
    # 14. Deterministic certificate ID
    # --------------------------------------------------------

    engine2 = EROSBlock95StressEvidenceGate()

    certificate2 = engine2.certify(
        stress_certificate=evidence,
    )

    _check(
        certificate2["gate_id"] == certificate["gate_id"],
        "Block 95 gate ID is not deterministic",
    )
    checks += 1

    # --------------------------------------------------------
    # 15. Snapshot isolation
    # --------------------------------------------------------

    snapshot = engine.snapshot()

    snapshot["certificates"][certificate["gate_id"]]["source_certificate_id"] = "MUTATED"

    fresh_snapshot = engine.snapshot()

    _check(
        fresh_snapshot["certificates"][certificate["gate_id"]]["source_certificate_id"]
        == "EROS94-STRESS-001",
        "certificate snapshot is not isolated",
    )
    checks += 1

    return {
        "status": "PASS",
        "block": 95,
        "checks": checks,
        "message": "EROS 3.0 Block 95 self-test passed",
        "gate_id": certificate["gate_id"],
    }


if __name__ == "__main__":
    result = run_block95_self_test()

    print("==================================================")
    print("EROS 3.0 - BLOCK 95 SELF TEST")
    print("==================================================")
    print(f"STATUS : {result['status']}")
    print(f"BLOCK  : {result['block']}")
    print(f"CHECKS : {result['checks']}")
    print(f"GATE ID: {result['gate_id']}")
    print(result["message"])
    print("==================================================")
