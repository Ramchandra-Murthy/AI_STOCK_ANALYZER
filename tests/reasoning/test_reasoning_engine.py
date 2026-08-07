from __future__ import annotations

import pytest
from services.reasoning.models import EvidenceObject
from services.reasoning.engine import BusinessReasoningEngine

def test_business_reasoning_engine() -> None:
    evidence_items = [
        EvidenceObject(
            metric_name="revenue_growth",
            value=14.5,
            direction="ACCELERATING",
            importance="HIGH",
            confidence=0.95,
            source="Canonical Income Statement",
            period="FY2025"
        ),
        EvidenceObject(
            metric_name="operating_margin",
            value=18.2,
            direction="IMPROVING",
            importance="HIGH",
            confidence=0.92,
            source="Canonical Income Statement",
            period="FY2025"
        ),
        EvidenceObject(
            metric_name="total_debt",
            value=45000.0,
            direction="IMPROVING",
            importance="HIGH",
            confidence=0.98,
            source="Canonical Balance Sheet",
            period="FY2025"
        )
    ]

    result = BusinessReasoningEngine.synthesize("RELIANCE.NS", evidence_items)
    
    assert result.symbol == "RELIANCE.NS"
    assert len(result.hypotheses) == 3
    assert len(result.contradictions) == 0
    assert result.recommendation == "BUY"
    assert result.confidence > 0.85
    assert "Sustained Topline Expansion" in result.hypotheses[0].title
