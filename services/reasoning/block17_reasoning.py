from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from services.reasoning.engine import BusinessReasoningEngine
from services.reasoning.models import EvidenceObject, ReasoningResult
from services.scoring.models import AIScoreResult

@dataclass(frozen=True, slots=True)
class EvidenceReasoningResult:
    symbol: str
    reasoning_confidence: float
    recommendation: str
    hypothesis_count: int
    contradiction_count: int
    high_severity_contradictions: int
    hypotheses_summaries: List[str]
    contradictions_summaries: List[str]
    details: Dict[str, Any]

class Block17ReasoningOrchestrator:
    """
    EROS 3.0 Block 17 Evidence & Business Reasoning Orchestrator.
    Transforms EROS scoring metrics into EvidenceObjects and runs BusinessReasoningEngine synthesis.
    """
    def evaluate(self, ai_score: AIScoreResult) -> EvidenceReasoningResult:
        symbol = ai_score.symbol
        
        # Construct evidence items from EROS pillar scores
        evidence_list = [
            EvidenceObject(
                metric_name="Growth Score",
                value=ai_score.growth_score,
                direction="IMPROVING" if ai_score.growth_score >= 60.0 else "DETERIORATING",
                importance="HIGH",
                confidence=0.90,
                source="EROS Block 11 Growth Engine",
                period="FY2025"
            ),
            EvidenceObject(
                metric_name="Profitability & Margins",
                value=ai_score.profitability_score,
                direction="IMPROVING" if ai_score.profitability_score >= 60.0 else "DETERIORATING",
                importance="CRITICAL",
                confidence=0.92,
                source="EROS Block 12 Fundamental Engine",
                period="FY2025"
            ),
            EvidenceObject(
                metric_name="Free Cash Flow Quality",
                value=ai_score.capital_allocation_score,
                direction="IMPROVING" if ai_score.capital_allocation_score >= 50.0 else "DETERIORATING",
                importance="HIGH",
                confidence=0.88,
                source="EROS Block 12 Capital Allocation",
                period="FY2025"
            ),
            EvidenceObject(
                metric_name="Balance Sheet Risk",
                value=ai_score.risk_score,
                direction="IMPROVING" if ai_score.risk_score >= 70.0 else "DETERIORATING",
                importance="CRITICAL",
                confidence=0.95,
                source="EROS Block 15 Risk Engine",
                period="FY2025"
            ),
        ]

        # Run Business Reasoning Engine
        reasoning_res = BusinessReasoningEngine.synthesize(symbol, evidence_list)

        high_sev = sum(1 for c in reasoning_res.contradictions if c.severity in ("HIGH", "CRITICAL"))
        hyp_summaries = [h.title for h in reasoning_res.hypotheses]
        cont_summaries = [c.title for c in reasoning_res.contradictions]

        details = {
            "engine_version": "EROS-3.0-BLOCK-17C",
            "department": reasoning_res.department,
            "raw_summary": reasoning_res.summary,
            "all_hypotheses": [{"title": h.title, "confidence": h.confidence} for h in reasoning_res.hypotheses],
            "all_contradictions": [{"title": c.title, "severity": c.severity} for c in reasoning_res.contradictions],
        }

        return EvidenceReasoningResult(
            symbol=symbol,
            reasoning_confidence=reasoning_res.confidence,
            recommendation=reasoning_res.recommendation,
            hypothesis_count=len(reasoning_res.hypotheses),
            contradiction_count=len(reasoning_res.contradictions),
            high_severity_contradictions=high_sev,
            hypotheses_summaries=hyp_summaries,
            contradictions_summaries=cont_summaries,
            details=details,
        )
