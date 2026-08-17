from __future__ import annotations

from services.quantitative.block85_execution_certification import (
    EROSBlock85ExecutionCertificationEngine,
)
from services.quantitative.block86_control_plane import (
    EROSBlock86ControlPlane,
)


def run_block86_self_test() -> dict:
    block85 = EROSBlock85ExecutionCertificationEngine()

    certification = block85.certify(
        orders=[{
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "quantity": 100,
            "limit_price": 2500,
            "allocation_pct": 0.10,
        }],
        risk={"status": "PASS"},
        governance={"status": "APPROVED"},
        validation={"status": "PASS"},
        simulation={"status": "PASS"},
    )

    block86 = EROSBlock86ControlPlane()

    approved = block86.evaluate(
        certification,
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.85,
    )

    assert approved.control_state == "APPROVED"
    assert approved.final_action == "BUY"
    assert approved.execution_allowed is True
    assert approved.metadata["broker_submission"] is False
    assert approved.decision_id.startswith("EROS86-")

    blocked_certification = block85.certify(
        orders=[{
            "symbol": "RELIANCE.NS",
            "action": "BUY",
            "quantity": 100,
            "limit_price": 2500,
            "allocation_pct": 0.10,
        }],
        risk={"status": "BLOCK"},
        governance={"status": "APPROVED"},
    )

    blocked = block86.evaluate(
        blocked_certification,
        symbol="RELIANCE.NS",
        requested_action="BUY",
        confidence=0.95,
    )

    # Non-bypass invariant:
    assert blocked.control_state == "BLOCKED"
    assert blocked.final_action == "BLOCK"
    assert blocked.execution_allowed is False

    return {
        "status": "PASS",
        "approved_decision_id": approved.decision_id,
        "approved_action": approved.final_action,
        "blocked_action": blocked.final_action,
        "non_bypass_invariant": True,
    }


if __name__ == "__main__":
    print(run_block86_self_test())
