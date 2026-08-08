from __future__ import annotations

import pytest
from backend.research.services.research_case_service import ResearchCaseService
from backend.research.evidence.services.evidence_service import EvidenceService
from backend.research.evidence.reasoning.evidence_reasoning import (
    EvidenceReasoningEngine,
    EvidenceRelationship,
)

def test_evidence_contradiction_detection() -> None:
    case = ResearchCaseService.create_case(symbol="TCS.NS", objective="Test contradictions")
    ev1 = EvidenceService.create_evidence(
        case, category="FUNDAMENTAL", statement="Margins expanding", polarity="POSITIVE", source="EngineA"
    )
    ev2 = EvidenceService.create_evidence(
        case, category="FUNDAMENTAL", statement="Margins compressing", polarity="NEGATIVE", source="EngineB"
    )
    rels = EvidenceReasoningEngine.analyze_relationships([ev1, ev2])
    contradictions = [r for r in rels if r.relation_type == "CONTRADICTS"]
    assert len(contradictions) == 1
    assert contradictions[0].source_evidence_id == ev1.evidence_id

def test_evidence_corroboration_detection() -> None:
    case = ResearchCaseService.create_case(symbol="INFY.NS", objective="Test corroborations")
    ev1 = EvidenceService.create_evidence(
        case, category="VALUATION", statement="Attractive entry point", polarity="POSITIVE", source="ModelA"
    )
    ev2 = EvidenceService.create_evidence(
        case, category="VALUATION", statement="Strong margin of safety", polarity="POSITIVE", source="ModelB"
    )
    rels = EvidenceReasoningEngine.analyze_relationships([ev1, ev2])
    corroborations = [r for r in rels if r.relation_type == "CORROBORATES"]
    assert len(corroborations) == 1

def test_net_stance_evaluation() -> None:
    case = ResearchCaseService.create_case(symbol="RELIANCE.NS", objective="Test net stance")
    ev1 = EvidenceService.create_evidence(case, category="QUALITY", statement="High ROCE", polarity="POSITIVE")
    ev2 = EvidenceService.create_evidence(case, category="GROWTH", statement="Strong CAGR", polarity="POSITIVE")
    ev3 = EvidenceService.create_evidence(case, category="RISK", statement="High leverage", polarity="NEGATIVE")
    
    rels = EvidenceReasoningEngine.analyze_relationships([ev1, ev2, ev3])
    stance = EvidenceReasoningEngine.evaluate_net_stance([ev1, ev2, ev3], rels)
    assert stance["total_evidence"] == 3
    assert stance["posture"] in {"CONSTRUCTIVE", "BALANCED", "CAUTIOUS"}