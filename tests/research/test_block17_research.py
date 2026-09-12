from services.reasoning.block17_reasoning import Block17ReasoningOrchestrator
from services.research.block17_engine import Block17ResearchOrchestrator
from services.scoring.block17_confidence import Block17ConfidenceOrchestrator
from services.scoring.models import AIScoreResult


def test_block17b_research_intelligence():
    orchestrator = Block17ResearchOrchestrator()
    result = orchestrator.evaluate("INFY.NS", composite_score=84.5)

    assert result.symbol == "INFY.NS"
    assert 0.0 <= result.research_score <= 100.0
    assert 0.0 <= result.moat_score <= 100.0
    assert result.moat_classification in ["Wide Moat", "Narrow Moat", "No Moat"]
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-17B"


def test_block17c_evidence_reasoning():
    ai_score = AIScoreResult(
        symbol="TCS.NS",
        growth_score=85.0,
        quality_score=90.0,
        profitability_score=92.0,
        capital_allocation_score=80.0,
        valuation_score=78.0,
        momentum_score=75.0,
        risk_score=88.0,
        composite_score=84.5,
        breakdown_details={"rating": "STRONG BUY"},
    )

    orchestrator = Block17ReasoningOrchestrator()
    result = orchestrator.evaluate(ai_score)

    assert result.symbol == "TCS.NS"
    assert 0.0 <= result.reasoning_confidence <= 1.0
    assert result.hypothesis_count > 0
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-17C"


def test_block17d_confidence_orchestration():
    orchestrator = Block17ConfidenceOrchestrator()
    result = orchestrator.evaluate(
        symbol="RELIANCE.NS",
        evidence_confidence=0.92,
        reasoning_confidence=0.90,
        moat_score=85.0,
        contradiction_count=0,
    )

    assert result.symbol == "RELIANCE.NS"
    assert 0.0 <= result.overall_confidence <= 1.0
    assert result.confidence_rating in [
        "HIGH CONFIDENCE",
        "MODERATE CONFIDENCE",
        "LOW CONFIDENCE - REVIEW REQUIRED",
    ]
    assert result.details["engine_version"] == "EROS-3.0-BLOCK-17D"
