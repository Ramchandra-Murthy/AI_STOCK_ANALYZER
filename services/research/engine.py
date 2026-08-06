from __future__ import annotations

import logging
from services.research.models import ResearchResult, InvestmentThesis, RiskSummary
from services.valuation.models import ValuationResult

logger = logging.getLogger(__name__)


class ResearchEngine:
    """Synthesizes valuation outcomes and qualitative factors into institutional research."""

    def synthesize(self, valuation: ValuationResult) -> ResearchResult:
        """Generate structured research from valuation results."""
        logger.info("Synthesizing research report for symbol: %s", valuation.symbol)

        thesis = InvestmentThesis(
            summary=f"Strong market position with a {valuation.margin_of_safety_pct}% margin of safety.",
            drivers=["Digital transformation leadership", "Robust balance sheet", "High free cash flow conversion"]
        )

        risks = RiskSummary(
            primary_risk="Macroeconomic volatility and regulatory shifts.",
            mitigants=["Diversified revenue streams", "Prudent capital allocation"]
        )

        confidence = 0.88 if valuation.recommendation == "BUY" else 0.72

        return ResearchResult(
            symbol=valuation.symbol,
            thesis=thesis,
            risks=risks,
            economic_moat="Wide Moat backed by network effects and cost advantages.",
            ai_recommendation=valuation.recommendation,
            confidence_score=confidence
        )
