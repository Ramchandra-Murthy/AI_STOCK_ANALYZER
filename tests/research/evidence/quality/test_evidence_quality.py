from __future__ import annotations

import pytest

from backend.research.evidence.quality.evidence_quality import (
    EvidenceQualityAssessment,
    EvidenceQualityService,
)
from backend.research.evidence.services.evidence_service import EvidenceService
from backend.research.services.research_case_service import ResearchCaseService


def test_evidence_quality_assessment_primary_source() -> None:
    case = ResearchCaseService.create_case(
        symbol="TCS.NS",
        objective="Evaluate primary source quality",
    )
    evidence = EvidenceService.create_evidence(
        case,
        category="fundamental",
        statement="Audited net profit grew by 15%",
        value=15000.0,
        source="Audited Annual Report",
        source_type="PRIMARY",
        confidence=0.99,
        recency=0.95,
    )
    assessment = EvidenceQualityService.assess_evidence(evidence)
    assert isinstance(assessment, EvidenceQualityAssessment)
    assert assessment.quality_score >= 0.90
    assert assessment.quality_grade == "A+"


def test_evidence_quality_assessment_anonymous_source() -> None:
    case = ResearchCaseService.create_case(
        symbol="INFY.NS",
        objective="Evaluate rumors",
    )
    evidence = EvidenceService.create_evidence(
        case,
        category="market",
        statement="Unverified rumor regarding contract termination",
        source="Anonymous Blog",
        source_type="ANONYMOUS",
        confidence=0.40,
        recency=0.60,
    )
    assessment = EvidenceQualityService.assess_evidence(evidence)
    assert assessment.quality_score < 0.70
    assert assessment.quality_grade in {"B", "C"}


def test_evidence_quality_invalid_weights_rejected() -> None:
    with pytest.raises(ValueError):
        EvidenceQualityAssessment(
            evidence_id="E-INVALID",
            source_reliability=1.5,
        )
