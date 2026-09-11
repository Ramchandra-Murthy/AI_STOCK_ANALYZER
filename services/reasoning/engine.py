from __future__ import annotations

import logging

from services.reasoning.models import (
    Contradiction,
    EvidenceObject,
    Hypothesis,
    ReasoningResult,
)

logger = logging.getLogger(__name__)


class BusinessReasoningEngine:
    """Translate supplied evidence into transparent, deterministic reasoning."""

    @staticmethod
    def synthesize(symbol: str, evidence_list: list[EvidenceObject]) -> ReasoningResult:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be non-empty")

        hypotheses: list[Hypothesis] = []
        contradictions: list[Contradiction] = []

        for evidence in evidence_list:
            if not 0.0 <= evidence.confidence <= 1.0:
                raise ValueError(f"evidence confidence out of range: {evidence.metric_name}")

        rev_evidence = [e for e in evidence_list if "revenue" in e.metric_name.lower()]
        margin_evidence = [e for e in evidence_list if "margin" in e.metric_name.lower()]
        debt_evidence = [e for e in evidence_list if "debt" in e.metric_name.lower()]
        fcf_evidence = [e for e in evidence_list if "fcf" in e.metric_name.lower() or "cash" in e.metric_name.lower()]

        if any(e.direction in {"IMPROVING", "ACCELERATING"} for e in rev_evidence):
            evidence = [e.metric_name for e in rev_evidence]
            hypotheses.append(
                Hypothesis(
                    title="Sustained Topline Expansion",
                    statement="Revenue evidence indicates improving or accelerating topline performance.",
                    supporting_evidence=evidence,
                    confidence=round(sum(e.confidence for e in rev_evidence) / len(rev_evidence), 2),
                )
            )

        if any(e.direction == "IMPROVING" for e in margin_evidence):
            hypotheses.append(
                Hypothesis(
                    title="Pricing Power & Margin Expansion",
                    statement="Margin evidence indicates improving profitability dynamics.",
                    supporting_evidence=[e.metric_name for e in margin_evidence],
                    confidence=round(sum(e.confidence for e in margin_evidence) / len(margin_evidence), 2),
                )
            )

        if any(e.direction == "IMPROVING" for e in debt_evidence):
            hypotheses.append(
                Hypothesis(
                    title="Prudent Capital Discipline",
                    statement="Debt evidence indicates improving balance-sheet resilience.",
                    supporting_evidence=[e.metric_name for e in debt_evidence],
                    confidence=round(sum(e.confidence for e in debt_evidence) / len(debt_evidence), 2),
                )
            )

        rev_growing = any(e.direction in {"IMPROVING", "ACCELERATING"} for e in rev_evidence)
        fcf_declining = any(e.direction == "DETERIORATING" for e in fcf_evidence)
        if rev_growing and fcf_declining:
            contradictions.append(
                Contradiction(
                    title="Topline Growth vs. Cash Flow Divergence",
                    description="Revenue is improving while cash-flow evidence is deteriorating.",
                    conflicting_signals=["Revenue Growth", "Free Cash Flow Compression"],
                    severity="HIGH",
                )
            )

        if hypotheses:
            base_confidence = sum(h.confidence for h in hypotheses) / len(hypotheses)
        else:
            base_confidence = 0.0
        if contradictions:
            base_confidence = max(0.0, base_confidence - 0.15)

        recommendation = "HOLD"
        if base_confidence >= 0.8 and not contradictions:
            recommendation = "BUY"
        elif contradictions and base_confidence < 0.6:
            recommendation = "HOLD"

        summary = (
            f"Business quality assessment for {normalized_symbol}: "
            f"{len(hypotheses)} evidence-backed hypotheses and {len(contradictions)} contradictions detected."
        )
        return ReasoningResult(
            symbol=normalized_symbol,
            department="Business Intelligence & Reasoning",
            summary=summary,
            evidence_list=evidence_list,
            hypotheses=hypotheses,
            contradictions=contradictions,
            confidence=round(base_confidence, 2),
            recommendation=recommendation,
        )
