from __future__ import annotations

from services.copilot_v2.copilot import InstitutionalCopilotV2
from services.copilot_v2.models import CopilotResponse


def test_copilot_response_immutability() -> None:
    resp = CopilotResponse(
        query="Why buy RELIANCE.NS?",
        answer="Strong fundamentals.",
        confidence=0.95,
        cited_engines=["ValuationEngine"],
        supporting_evidence=["Good ROIC"],
        recommended_actions=["Buy"],
        follow_up_questions=["Any risks?"],
    )
    assert resp.confidence == 0.95
    assert len(resp.cited_engines) == 1
    assert resp.timestamp is not None
    assert isinstance(resp.metadata, dict)


def test_institutional_copilot_v2() -> None:
    response = InstitutionalCopilotV2.query_copilot(
        "Explain investment thesis for RELIANCE.NS", "RELIANCE.NS"
    )
    assert response.confidence >= 0.90
    assert len(response.cited_engines) >= 3
    assert len(response.supporting_evidence) > 0
    assert len(response.recommended_actions) > 0
    assert len(response.follow_up_questions) > 0
