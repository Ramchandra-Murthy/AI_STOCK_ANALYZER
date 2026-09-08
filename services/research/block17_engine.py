from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional
from services.research.engine import ResearchEngine
from services.moat.engine import EconomicMoatEngine
from services.ratios.models import FinancialRatios
from services.research.models import ResearchResult

@dataclass(frozen=True, slots=True)
class ResearchIntelligenceResult:
    symbol: str
    research_score: float
    moat_score: float
    moat_classification: str
    ai_recommendation: str
    confidence_score: float
    thesis_summary: str
    drivers: List[str]
    primary_risk: str
    details: Dict[str, Any]

class Block17ResearchOrchestrator:
    """
    EROS 3.0 Block 17 Research Intelligence Orchestrator.
    Synthesizes qualitative research, economic moat analysis, and quantitative score alignment.
    """
    def __init__(self) -> None:
        self.research_engine = ResearchEngine()
        self.moat_engine = EconomicMoatEngine()

    def evaluate(self, symbol: str, ratios: Optional[FinancialRatios] = None, composite_score: float = 0.0, evidence: Optional[Mapping[str, Any]] = None) -> ResearchIntelligenceResult:
        # 1. Synthesize only from explicit evidence; never manufacture a thesis.
        raw_research = self.research_engine.synthesize(symbol, evidence=evidence)
        
        # 2. Evaluate Economic Moat only when real financial ratios are supplied.
        # Never substitute sample FY2025 ratios for missing fundamentals.
        if ratios is not None:
            moat_res = self.moat_engine.evaluate_moat(ratios)
            moat_score = moat_res.moat_score
            moat_classification = moat_res.moat_classification
            moat_factors = moat_res.factors
            moat_metadata = moat_res.metadata
            research_score = round((moat_score * 0.5) + (composite_score * 0.5), 2)
        else:
            moat_score = 0.0
            moat_classification = "UNASSESSED"
            moat_factors = []
            moat_metadata = {"reason": "financial_ratios_unavailable"}
            research_score = round(composite_score, 2)

        # Safely extract thesis and risks without synthetic fallbacks.
        raw_thesis = getattr(raw_research, "thesis", None)
        if hasattr(raw_thesis, "summary"):
            thesis_summary = raw_thesis.summary
            drivers = getattr(raw_thesis, "drivers", [])
        elif isinstance(raw_thesis, str):
            thesis_summary = raw_thesis
            drivers = []
        else:
            thesis_summary = "Insufficient evidence to form an investment thesis."
            drivers = []

        raw_risks = getattr(raw_research, "risks", None)
        if hasattr(raw_risks, "primary_risk"):
            primary_risk = raw_risks.primary_risk
        elif isinstance(raw_risks, str):
            primary_risk = raw_risks
        else:
            primary_risk = "Risk assessment unavailable."

        return ResearchIntelligenceResult(
            symbol=symbol,
            research_score=research_score,
            moat_score=moat_score,
            moat_classification=moat_classification,
            ai_recommendation=getattr(raw_research, "ai_recommendation", "HOLD"),
            confidence_score=getattr(raw_research, "confidence_score", 0.0),
            thesis_summary=thesis_summary,
            drivers=drivers,
            primary_risk=primary_risk,
            details={
                "engine_version": "EROS-3.0-BLOCK-17B",
                "moat_factors": moat_factors,
                "moat_metadata": moat_metadata,
                "research_evidence": dict(evidence or {}),
            }
        )
