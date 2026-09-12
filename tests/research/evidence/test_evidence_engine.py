from __future__ import annotations

import pytest

from backend.research.evidence.models.research_evidence import (
    ResearchEvidence,
)
from backend.research.evidence.services.evidence_service import (
    EvidenceService,
)
from backend.research.services.research_case_service import (
    ResearchCaseService,
)


def test_structured_evidence_creation() -> None:
    case = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Evaluate long-term investment quality",
    )
    evidence = EvidenceService.create_evidence(
        case,
        category="fundamental",
        statement="Operating margin remains structurally strong",
        value=24.5,
        source="Annual Report",
        source_type="PRIMARY",
        confidence=0.95,
        materiality=0.90,
        recency=0.85,
        polarity="POSITIVE",
    )
    assert isinstance(evidence, ResearchEvidence)
    assert evidence.symbol == "TCS.NS"
    assert evidence.category == "FUNDAMENTAL"
    assert evidence.polarity == "POSITIVE"
    assert evidence.confidence == 0.95


def test_evidence_strength_calculation() -> None:
    case = ResearchCaseService.create_case(
        symbol="RELIANCE.NS",
        objective="Evaluate business quality",
    )
    evidence = EvidenceService.create_evidence(
        case,
        category="quality",
        statement="Return on capital remains healthy",
        confidence=0.90,
        materiality=0.80,
        recency=0.75,
    )
    strength = EvidenceService.calculate_evidence_strength(evidence)
    assert strength == 0.54


def test_evidence_attachment_to_case() -> None:
    case = ResearchCaseService.create_case(
        symbol="INFY.NS",
        objective="Evaluate quality and valuation",
    )
    evidence = EvidenceService.create_evidence(
        case,
        category="valuation",
        statement="Current valuation provides a margin of safety",
        confidence=0.85,
        materiality=0.95,
        recency=0.90,
        polarity="POSITIVE",
    )
    EvidenceService.attach_evidence(
        case,
        evidence,
    )
    assert len(case.evidence) == 1
    assert "margin of safety" in case.evidence[0]


def test_evidence_case_mismatch_rejected() -> None:
    case_a = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Research TCS",
    )
    case_b = ResearchCaseService.create_case(
        symbol="INFY.NS",
        objective="Research Infosys",
    )
    evidence = EvidenceService.create_evidence(
        case_a,
        category="risk",
        statement="Currency risk may affect margins",
        confidence=0.80,
        materiality=0.70,
        recency=0.90,
        polarity="NEGATIVE",
    )
    with pytest.raises(ValueError):
        EvidenceService.attach_evidence(
            case_b,
            evidence,
        )


def test_evidence_summary() -> None:
    case = ResearchCaseService.create_case(
        symbol="HDFC_BANK.NS",
        objective="Evaluate banking opportunity",
    )
    evidence_items = [
        EvidenceService.create_evidence(
            case,
            category="fundamental",
            statement="Loan growth remains strong",
            confidence=0.90,
            materiality=0.80,
            recency=0.90,
            polarity="POSITIVE",
        ),
        EvidenceService.create_evidence(
            case,
            category="risk",
            statement="Credit cost uncertainty remains",
            confidence=0.80,
            materiality=0.70,
            recency=0.80,
            polarity="NEGATIVE",
        ),
        EvidenceService.create_evidence(
            case,
            category="valuation",
            statement="Valuation requires monitoring",
            confidence=0.85,
            materiality=0.60,
            recency=0.90,
            polarity="NEUTRAL",
        ),
    ]
    summary = EvidenceService.summarize(evidence_items)
    assert summary["count"] == 3
    assert summary["positive"] == 1
    assert summary["negative"] == 1
    assert summary["neutral"] == 1
    assert summary["average_strength"] > 0


def test_invalid_confidence_rejected() -> None:
    case = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Test validation",
    )
    with pytest.raises(ValueError):
        EvidenceService.create_evidence(
            case,
            category="fundamental",
            statement="Invalid confidence",
            confidence=1.5,
        )


def test_invalid_polarity_rejected() -> None:
    case = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Test validation",
    )
    with pytest.raises(ValueError):
        EvidenceService.create_evidence(
            case,
            category="fundamental",
            statement="Invalid polarity",
            polarity="UNKNOWN",
        )
