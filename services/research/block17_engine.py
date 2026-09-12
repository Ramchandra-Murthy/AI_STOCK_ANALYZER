from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.moat.engine import EconomicMoatEngine
from services.ratios.models import FinancialRatios
from services.research.engine import ResearchEngine


@dataclass(frozen=True, slots=True)
class ResearchIntelligenceResult:
    symbol: str
    research_score: float
    moat_score: float
    moat_classification: str
    ai_recommendation: str
    confidence_score: float
    thesis_summary: str
    drivers: list[str]
    primary_risk: str
    details: dict[str, Any]


class Block17ResearchOrchestrator:
    """Synthesize supplied research and ratio evidence without fabricated defaults."""

    def __init__(self) -> None:
        self.research_engine = ResearchEngine()
        self.moat_engine = EconomicMoatEngine()

    def evaluate(
        self,
        symbol: str,
        ratios: FinancialRatios | None = None,
        composite_score: float | None = None,
    ) -> ResearchIntelligenceResult:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be non-empty")
        if composite_score is None:
            raise ValueError("composite_score is required")
        if not isinstance(composite_score, (int, float)) or not 0 <= float(composite_score) <= 100:
            raise ValueError("composite_score must be between 0 and 100")
        if ratios is None:
            raise ValueError("validated financial ratios are required for research intelligence")

        raw_research = self.research_engine.synthesize(normalized_symbol)
        moat_res = self.moat_engine.evaluate_moat(ratios)

        raw_confidence = float(getattr(raw_research, "confidence_score", 0.0))
        raw_recommendation = str(getattr(raw_research, "ai_recommendation", "UNAVAILABLE"))
        thesis = str(getattr(raw_research, "thesis", "Research evidence unavailable."))
        risks = str(getattr(raw_research, "risks", "Validated research risk evidence unavailable."))
        research_score = round((moat_res.moat_score * 0.5) + (float(composite_score) * 0.5), 2)

        return ResearchIntelligenceResult(
            symbol=normalized_symbol,
            research_score=research_score,
            moat_score=moat_res.moat_score,
            moat_classification=moat_res.moat_classification,
            ai_recommendation=raw_recommendation,
            confidence_score=raw_confidence,
            thesis_summary=thesis,
            drivers=[],
            primary_risk=risks,
            details={
                "engine_version": "EROS-3.0-BLOCK-17B",
                "moat_factors": moat_res.factors,
                "moat_metadata": moat_res.metadata,
                "research_source_status": (
                    "INSUFFICIENT_EXTERNAL_RESEARCH" if raw_confidence <= 0 else "AVAILABLE"
                ),
            },
        )
