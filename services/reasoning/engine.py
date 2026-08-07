from __future__ import annotations

import logging
from typing import List, Dict, Any
from services.reasoning.models import EvidenceObject, Hypothesis, Contradiction, ReasoningResult

logger = logging.getLogger(__name__)

class BusinessReasoningEngine:
    """Institutional reasoning engine that translates evidence into structured hypotheses and transparent verdicts."""

    @staticmethod
    def synthesize(symbol: str, evidence_list: List[EvidenceObject]) -> ReasoningResult:
        logger.info("Synthesizing institutional reasoning for %s based on %d evidence items", symbol, len(evidence_list))

        hypotheses: List[Hypothesis] = []
        contradictions: List[Contradiction] = []

        # Analyze evidence streams
        rev_evidence = [e for e in evidence_list if "revenue" in e.metric_name.lower()]
        margin_evidence = [e for e in evidence_list if "margin" in e.metric_name.lower()]
        debt_evidence = [e for e in evidence_list if "debt" in e.metric_name.lower()]
        fcf_evidence = [e for e in evidence_list if "fcf" in e.metric_name.lower() or "cash" in e.metric_name.lower()]

        # Generate Hypotheses
        if rev_evidence and rev_evidence[0].direction in ("IMPROVING", "ACCELERATING"):
            hypotheses.append(Hypothesis(
                title="Sustained Topline Expansion",
                statement="Revenue growth reflects durable market demand and strong operational execution.",
                supporting_evidence=[e.metric_name for e in rev_evidence],
                confidence=0.91
            ))

        if margin_evidence and margin_evidence[0].direction == "IMPROVING":
            hypotheses.append(Hypothesis(
                title="Pricing Power & Margin Expansion",
                statement="Operating margins are strengthening, indicating effective cost control or pricing power.",
                supporting_evidence=[e.metric_name for e in margin_evidence],
                confidence=0.88
            ))

        if debt_evidence and debt_evidence[0].direction == "IMPROVING": # e.g. falling debt
            hypotheses.append(Hypothesis(
                title="Prudent Capital Discipline",
                statement="Total debt reduction strengthens balance sheet resilience and reduces solvency risk.",
                supporting_evidence=[e.metric_name for e in debt_evidence],
                confidence=0.94
            ))

        # Check for Contradictions
        # Example: Revenue growing but Free Cash Flow deteriorating
        rev_growing = any(e.direction in ("IMPROVING", "ACCELERATING") for e in rev_evidence)
        fcf_declining = any(e.direction == "DETERIORATING" for e in fcf_evidence)

        if rev_growing and fcf_declining:
            contradictions.append(Contradiction(
                title="Topline Growth vs. Cash Flow Divergence",
                description="Revenue is expanding while cash generation is deteriorating, suggesting potential working capital drag or aggressive accruals.",
                conflicting_signals=["Revenue Growth", "Free Cash Flow Compression"],
                severity="HIGH"
            ))

        # Synthesize Summary Narrative
        summary = (
            f"Business quality assessment for {symbol}: "
            f"The company demonstrates solid foundational drivers supported by {len(hypotheses)} structural hypotheses. "
            f"{'Identified contradictions require cautious monitoring.' if contradictions else 'No major structural contradictions detected across audited financial streams.'}"
        )

        # Compute Confidence & Verdict
        base_confidence = sum(h.confidence for h in hypotheses) / max(len(hypotheses), 1)
        if contradictions:
            base_confidence = max(0.5, base_confidence - 0.15)
            recommendation = "HOLD"
        else:
            recommendation = "BUY" if base_confidence >= 0.8 else "HOLD"

        return ReasoningResult(
            symbol=symbol,
            department="Business Intelligence & Reasoning",
            summary=summary,
            evidence_list=evidence_list,
            hypotheses=hypotheses,
            contradictions=contradictions,
            confidence=round(base_confidence, 2),
            recommendation=recommendation
        )
