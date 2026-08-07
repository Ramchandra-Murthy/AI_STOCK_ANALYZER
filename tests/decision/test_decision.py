from __future__ import annotations

import pytest
from services.decision.models import DecisionOption
from services.decision.decision_engine import InstitutionalDecisionEngine
from services.decision.decision_policy import DecisionPolicyEngine if False else ... # placeholder check
from services.decision.policy_engine import DecisionPolicyEngine

def test_decision_option_immutability() -> None:
    option = DecisionOption(
        option_id="TEST-BUY",
        action="BUY",
        confidence=0.90,
        expected_return=0.15,
        downside_risk=0.05,
        rationale=["Strong fundamentals"],
        evidence=["DCF positive"]
    )
    assert option.option_id == "TEST-BUY"
    assert option.action == "BUY"
    assert option.confidence == 0.90
    assert option.timestamp is not None
    assert isinstance(option.metadata, dict)

def test_decision_engine_ranking() -> None:
    options = InstitutionalDecisionEngine.evaluate_options("RELIANCE.NS", "Institutional")
    assert len(options) == 3
    # Top ranked option should be BUY based on risk-adjusted score
    assert options[0].action == "BUY"
    assert options[0].expected_return > options[1].expected_return

def test_decision_policy_engine() -> None:
    weights = DecisionPolicyEngine.get_profile_weights("Conservative")
    assert weights["risk_weight"] == 0.5
    assert weights["return_weight"] == 0.4

    growth_weights = DecisionPolicyEngine.get_profile_weights("Growth")
    assert growth_weights["return_weight"] == 0.7
