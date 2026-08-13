from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True, slots=True)
class ResearchConfidenceResult:
    symbol: str
    overall_confidence: float
    evidence_confidence: float
    reasoning_confidence: float
    moat_confidence: float
    confidence_rating: str
    details: Dict[str, Any]

class Block17ConfidenceOrchestrator:
    """
    EROS 3.0 Block 17 Research Confidence Orchestrator.
    Computes institutional confidence composites based on evidence quality, reasoning stability, and moat strength.
    """
    def evaluate(
        self,
        symbol: str,
        evidence_confidence: float = 0.90,
        reasoning_confidence: float = 0.88,
        moat_score: float = 80.0,
        contradiction_count: int = 0,
    ) -> ResearchConfidenceResult:
        moat_confidence = moat_score / 100.0

        # Penalize confidence if contradictions exist
        contradiction_penalty = min(contradiction_count * 0.10, 0.30)

        overall = round(
            (evidence_confidence * 0.35)
            + (reasoning_confidence * 0.40)
            + (moat_confidence * 0.25)
            - contradiction_penalty,
            4
        )
        overall = min(max(overall, 0.0), 1.0)

        if overall >= 0.85:
            rating = "HIGH CONFIDENCE"
        elif overall >= 0.70:
            rating = "MODERATE CONFIDENCE"
        else:
            rating = "LOW CONFIDENCE - REVIEW REQUIRED"

        details = {
            "engine_version": "EROS-3.0-BLOCK-17D",
            "contradiction_penalty": contradiction_penalty,
        }

        return ResearchConfidenceResult(
            symbol=symbol,
            overall_confidence=overall,
            evidence_confidence=evidence_confidence,
            reasoning_confidence=reasoning_confidence,
            moat_confidence=moat_confidence,
            confidence_rating=rating,
            details=details,
        )
