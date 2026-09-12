from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ResearchConfidenceResult:
    symbol: str
    overall_confidence: float
    evidence_confidence: float
    reasoning_confidence: float
    moat_confidence: float
    confidence_rating: str
    details: dict[str, Any]


class Block17ConfidenceOrchestrator:
    """Compute confidence from supplied evidence, reasoning, moat and contradictions."""

    def evaluate(
        self,
        symbol: str,
        evidence_confidence: float,
        reasoning_confidence: float,
        moat_score: float,
        contradiction_count: int = 0,
    ) -> ResearchConfidenceResult:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be non-empty")
        for name, value in {
            "evidence_confidence": evidence_confidence,
            "reasoning_confidence": reasoning_confidence,
        }.items():
            if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1")
        if not isinstance(moat_score, (int, float)) or not 0.0 <= float(moat_score) <= 100.0:
            raise ValueError("moat_score must be between 0 and 100")
        if not isinstance(contradiction_count, int) or contradiction_count < 0:
            raise ValueError("contradiction_count must be a non-negative integer")

        moat_confidence = float(moat_score) / 100.0
        contradiction_penalty = min(contradiction_count * 0.10, 0.30)
        overall = round(
            (float(evidence_confidence) * 0.35)
            + (float(reasoning_confidence) * 0.40)
            + (moat_confidence * 0.25)
            - contradiction_penalty,
            4,
        )
        overall = min(max(overall, 0.0), 1.0)

        rating = (
            "HIGH CONFIDENCE"
            if overall >= 0.85
            else "MODERATE CONFIDENCE" if overall >= 0.70 else "LOW CONFIDENCE - REVIEW REQUIRED"
        )
        return ResearchConfidenceResult(
            symbol=normalized_symbol,
            overall_confidence=overall,
            evidence_confidence=float(evidence_confidence),
            reasoning_confidence=float(reasoning_confidence),
            moat_confidence=moat_confidence,
            confidence_rating=rating,
            details={
                "engine_version": "EROS-3.0-BLOCK-17D",
                "contradiction_penalty": contradiction_penalty,
            },
        )
