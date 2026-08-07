from __future__ import annotations

import logging
from typing import Any
from services.moat.models import EconomicMoatResult
from services.ratios.models import FinancialRatios

logger = logging.getLogger(__name__)

class EconomicMoatEngine:
    """Evaluates sustainable competitive advantages (Economic Moats) based on profitability, pricing power, and capital returns."""

    def evaluate_moat(self, ratios: FinancialRatios) -> EconomicMoatResult:
        logger.info("Evaluating economic moat for %s", ratios.symbol)
        
        roe = ratios.profitability.get("roe", 0.0)
        roic = ratios.profitability.get("roic", 0.0)
        net_margin = ratios.profitability.get("net_margin", 0.0)
        
        # Quantitative moat scoring based on return on invested capital and consistent margins
        score = 0.0
        if roic > 20.0:
            score += 40.0
        elif roic > 12.0:
            score += 25.0
        else:
            score += 10.0

        if net_margin > 15.0:
            score += 35.0
        elif net_margin > 8.0:
            score += 20.0
        else:
            score += 5.0

        if roe > 15.0:
            score += 25.0
        else:
            score += 10.0

        score = min(max(score, 0.0), 100.0)

        classification = "Wide Moat" if score >= 80.0 else ("Narrow Moat" if score >= 50.0 else "No Moat")

        factors = {
            "pricing_power": net_margin * 2.0,
            "capital_returns": roic * 2.5,
            "brand_strength": roe * 1.5
        }

        return EconomicMoatResult(
            symbol=ratios.symbol,
            moat_score=score,
            moat_classification=classification,
            factors=factors,
            metadata={"version": "6.4", "framework": "Buffett-Greenwald Moat Criteria"}
        )
