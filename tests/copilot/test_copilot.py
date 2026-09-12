from __future__ import annotations

from services.copilot.intent_classifier import IntentClassifier
from services.copilot.orchestrator import InstitutionalAICopilot


def test_institutional_ai_copilot() -> None:
    # Test Intent Classification
    assert IntentClassifier.classify("Value Reliance using DCF") == "VALUATION"
    assert (
        IntentClassifier.classify("Why is the committee recommending BUY?") == "COMMITTEE_REASONING"
    )
    assert IntentClassifier.classify("Run full workflow for TCS") == "WORKFLOW"

    # Test Copilot Orchestrator Response
    response = InstitutionalAICopilot.process_query("Value Reliance", "RELIANCE.NS")
    assert response.confidence > 0.85
    assert len(response.evidence) > 0
    assert len(response.workflow_steps) > 0
    assert len(response.sources) > 0
    assert "Valuation" in response.answer
