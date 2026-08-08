from __future__ import annotations

import pytest
from backend.research.services.research_case_service import ResearchCaseService
from backend.research.evidence.adapters.evidence_adapters import (
    FundamentalsEvidenceAdapter,
    ValuationEvidenceAdapter,
    RiskEvidenceAdapter,
)

def test_fundamentals_evidence_adapter() -> None:
    case = ResearchCaseService.create_case(symbol="TCS.NS", objective="Test adapter")
    metrics = {"revenue_growth": 0.18, "roce": 0.24}
    items = FundamentalsEvidenceAdapter.extract(case, metrics)
    assert len(items) == 2
    assert items[0].category == "FUNDAMENTAL"
    assert items[0].polarity == "POSITIVE"
    assert items[1].category == "QUALITY"
    assert items[1].value == 0.24

def test_valuation_evidence_adapter() -> None:
    case = ResearchCaseService.create_case(symbol="INFY.NS", objective="Test valuation adapter")
    val_data = {"intrinsic_value": 3500.0, "margin_of_safety": 0.20}
    items = ValuationEvidenceAdapter.extract(case, val_data)
    assert len(items) == 2
    assert items[0].category == "VALUATION"
    assert items[1].value == 0.20

def test_risk_evidence_adapter() -> None:
    case = ResearchCaseService.create_case(symbol="RELIANCE.NS", objective="Test risk adapter")
    risk_data = {"debt_to_equity": 0.35}
    items = RiskEvidenceAdapter.extract(case, risk_data)
    assert len(items) == 1
    assert items[0].category == "RISK"
    assert items[0].polarity == "POSITIVE"