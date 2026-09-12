from __future__ import annotations

import logging

from services.investors.models import InvestorScoreResult
from services.moat.models import EconomicMoatResult
from services.ratios.models import FinancialRatios

logger = logging.getLogger(__name__)


class BuffettEngine:
    """Evaluates companies based on Warren Buffett's criteria: consistent high ROE, strong pricing power, low debt, and economic moat."""

    def evaluate(self, ratios: FinancialRatios, moat: EconomicMoatResult) -> InvestorScoreResult:
        logger.info("Running Buffett Engine analysis for %s", ratios.symbol)

        roe = ratios.profitability.get("roe", 0.0)
        roic = ratios.profitability.get("roic", 0.0)
        debt_to_equity = ratios.solvency.get("debt_to_equity", 1.0)
        interest_coverage = ratios.solvency.get("interest_coverage", 0.0)
        fcf_conversion = ratios.cash_flow.get("fcf_conversion", 0.0)

        score = 0.0
        if roe >= 15.0:
            score += 25.0
        elif roe >= 10.0:
            score += 15.0

        if roic >= 12.0:
            score += 25.0
        elif roic >= 8.0:
            score += 15.0

        if debt_to_equity <= 0.5:
            score += 20.0
        elif debt_to_equity <= 1.0:
            score += 10.0

        if interest_coverage >= 5.0:
            score += 15.0
        elif interest_coverage >= 2.0:
            score += 8.0

        if moat.moat_score >= 70.0:
            score += 15.0
        elif moat.moat_score >= 40.0:
            score += 8.0

        score = min(max(score, 0.0), 100.0)
        recommendation = "Strong Buy" if score >= 80.0 else ("Hold" if score >= 50.0 else "Avoid")

        rationale = {
            "roe": roe,
            "roic": roic,
            "debt_to_equity": debt_to_equity,
            "interest_coverage": interest_coverage,
            "moat_score": moat.moat_score,
            "summary": "Business exhibits strong compounding characteristics, superior return on capital, and manageable leverage.",
        }

        return InvestorScoreResult(
            symbol=ratios.symbol,
            investor_name="Warren Buffett",
            score=score,
            recommendation=recommendation,
            rationale=rationale,
            metadata={"version": "6.5", "philosophy": "Quality & Economic Moat"},
        )
