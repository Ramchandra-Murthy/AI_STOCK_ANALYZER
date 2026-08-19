from __future__ import annotations

from copy import deepcopy

from .block96_stress_decision_gate import (
    EROSBlock96StressDecisionGate,
    STATUS_BLOCKED,
    STATUS_CERTIFIED,
    STATUS_DUPLICATE,
    DECISION_ADMITTED,
    DECISION_REJECTED,
)


def _stress_gate():
    return {
        "status": "CERTIFIED",
        "gate_status": "CERTIFIED",
        "gate_id": "EROS95-STRESS-GATE-001",
        "block_id": "95",
        "engine_version": "EROS-3.0-BLOCK-95",
        "source_block": "94",
        "source_engine_version": "94.1.0",
        "source_certificate_id": "EROS94-STRESS-001",
        "scenario_count": 2,
        "scenario_ids": [
            "EROS94-DOWN-001",
            "EROS94-UP-001",
        ],
        "evidence_status": "CERTIFIED",
        "downstream_risk_gate": "PASS",
        "non_mutation_invariant": True,
        "broker_submission": False,
        "live_order_submission": False,
        "scenario_results": [
            {
                "status": "PASS",
                "scenario": {
                    "scenario_id": "EROS94-DOWN-001",
                    "scenario_type": "MARKET",
                },
                "stressed_pnl": -1500000.0,
                "stressed_drawdown_pct": 15.0,
                "scenario_contribution": [
                    {
                        "symbol": "RELIANCE.NS",
                        "contribution_pct": 15.0,
                    }
                ],
            },
            {
                "status": "PASS",
                "scenario": {
                    "scenario_id": "EROS94-UP-001",
                    "scenario_type": "MARKET",
                },
                "stressed_pnl": 1000000.0,
                "stressed_drawdown_pct": 0.0,
                "scenario_contribution": [
                    {
                        "symbol": "RELIANCE.NS",
                        "contribution_pct": 0.0,
                    }
                ],
            },
        ],
    }


def _check(condition, message):
    if not condition:
        raise AssertionError(message)


def run_block96_self_test():

    checks = 0

    engine = EROSBlock96StressDecisionGate()
    evidence = _stress_gate()
    original = deepcopy(evidence)

    # 1. Valid certification
    result = engine.certify(
        stress_gate=evidence
    )

    _check(
        result["status"] == STATUS_CERTIFIED,
        "valid gate must certify",
    )
    checks += 1

    # 2. Decision certification
    _check(
        result["decision_status"] == STATUS_CERTIFIED,
        "decision status must certify",
    )
    checks += 1

    # 3. Admission
    _check(
        result["decision"] == DECISION_ADMITTED,
        "valid evidence must be admitted",
    )
    checks += 1

    # 4. Block identity
    _check(
        result["block_id"] == "96",
        "Block 96 identity incorrect",
    )
    checks += 1

    _check(
        result["engine_version"] == "EROS-3.0-BLOCK-96",
        "Block 96 engine version incorrect",
    )
    checks += 1

    # 5. Lineage
    _check(
        result["source_block"] == "95",
        "source block must be 95",
    )
    checks += 1

    _check(
        result["source_gate_id"] == "EROS95-STRESS-GATE-001",
        "source gate lineage incorrect",
    )
    checks += 1

    _check(
        result["source_certificate_id"] == "EROS94-STRESS-001",
        "source certificate lineage incorrect",
    )
    checks += 1

    # 6. Scenario propagation
    _check(
        result["scenario_count"] == 2,
        "scenario count incorrect",
    )
    checks += 1

    _check(
        len(result["scenario_ids"]) == 2,
        "scenario IDs incorrect",
    )
    checks += 1

    # 7. Safety invariants
    _check(
        result["non_mutation_invariant"] is True,
        "non mutation invariant failed",
    )
    checks += 1

    _check(
        result["broker_submission"] is False,
        "broker submission invariant failed",
    )
    checks += 1

    _check(
        result["live_order_submission"] is False,
        "live execution invariant failed",
    )
    checks += 1

    # 8. Input immutability
    _check(
        evidence == original,
        "input evidence mutated",
    )
    checks += 1

    # 9. Duplicate protection
    duplicate = engine.certify(
        stress_gate=evidence
    )

    _check(
        duplicate["status"] == STATUS_DUPLICATE,
        "identical decision must be duplicate",
    )
    checks += 1

    # 10. Invalid source block
    invalid = deepcopy(evidence)
    invalid["block_id"] = "94"

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "invalid source block must block",
    )
    checks += 1

    # 11. Non-certified source
    invalid = deepcopy(evidence)
    invalid["status"] = "BLOCKED"

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "non-certified source must block",
    )
    checks += 1

    # 12. Missing scenarios
    invalid = deepcopy(evidence)
    invalid["scenario_results"] = []

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "missing scenarios must block",
    )
    checks += 1

    # 13. Duplicate scenario IDs
    invalid = deepcopy(evidence)
    invalid["scenario_results"][1]["scenario"]["scenario_id"] = (
        "EROS94-DOWN-001"
    )

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "duplicate scenario IDs must block",
    )
    checks += 1

    # 14. Missing contribution
    invalid = deepcopy(evidence)
    invalid["scenario_results"][0]["scenario_contribution"] = []

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "missing contribution must block",
    )
    checks += 1

    # 15. Invalid drawdown
    invalid = deepcopy(evidence)
    invalid["scenario_results"][0]["stressed_drawdown_pct"] = "INVALID"

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "invalid drawdown must block",
    )
    checks += 1

    # 16. Downstream risk gate
    invalid = deepcopy(evidence)
    invalid["downstream_risk_gate"] = "BLOCKED"

    blocked = engine.certify(
        stress_gate=invalid
    )

    _check(
        blocked["status"] == STATUS_BLOCKED,
        "blocked risk gate must block",
    )
    checks += 1

    # 17. Policy rejection
    rejected = engine.certify(
        stress_gate=evidence,
        policy={
            "max_stressed_drawdown_pct": 10.0
        },
    )

    _check(
        rejected["status"] == STATUS_CERTIFIED,
        "policy decision should certify",
    )
    checks += 1

    _check(
        rejected["decision"] == DECISION_REJECTED,
        "drawdown policy should reject",
    )
    checks += 1

    # 18. Snapshot
    snapshot = engine.snapshot()

    _check(
        snapshot["block_id"] == "96",
        "snapshot block identity incorrect",
    )
    checks += 1

    print("=" * 50)
    print("EROS 3.0 - BLOCK 96 SELF TEST")
    print("=" * 50)
    print("STATUS : PASS")
    print("BLOCK  : 96")
    print("CHECKS :", checks)
    print("DECISION ID:", result["decision_id"])
    print("DECISION    :", result["decision"])
    print("REJECTION TEST:", rejected["decision"])
    print("NON-MUTATION :", result["non_mutation_invariant"])
    print(
        "EXECUTION BLOCKED :",
        result["broker_submission"] is False
        and result["live_order_submission"] is False,
    )
    print("EROS 3.0 Block 96 self-test passed")
    print("=" * 50)


if __name__ == "__main__":
    run_block96_self_test()

