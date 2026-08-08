from __future__ import annotations

import pytest
from backend.research.models.research_case import ResearchCase
from backend.research.services.research_case_service import (
    ResearchCaseService,
)

def test_research_case_creation() -> None:
    case = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Evaluate long-term compounder potential",
    )
    assert isinstance(case, ResearchCase)
    assert case.symbol == "TCS.NS"
    assert case.status == "OPEN"
    assert case.research_type == "Long-Term Equity"
    assert case.analyst == "EROS"
    assert case.case_id.startswith("RESEARCH-TCS.NS")

def test_research_case_evidence_management() -> None:
    case = ResearchCaseService.create_case(
        symbol="RELIANCE.NS",
        objective="Evaluate investment attractiveness",
    )
    ResearchCaseService.add_evidence(
        case,
        "Revenue growth remains strong",
    )
    ResearchCaseService.add_evidence(
        case,
        "Revenue growth remains strong",
    )
    assert len(case.evidence) == 1
    assert "Revenue growth remains strong" in case.evidence

def test_research_case_thesis_update() -> None:
    case = ResearchCaseService.create_case(
        symbol="INFY.NS",
        objective="Evaluate quality and valuation",
    )
    ResearchCaseService.update_thesis(
        case,
        "High-quality business with attractive long-term economics.",
    )
    assert "High-quality business" in case.investment_thesis

def test_research_case_closure() -> None:
    case = ResearchCaseService.create_case(
        symbol="HDFC_BANK.NS",
        objective="Evaluate long-term banking opportunity",
    )
    ResearchCaseService.close_case(
        case,
        "Suitable for further institutional research.",
    )
    assert case.status == "CLOSED"
    assert case.conclusion != ""