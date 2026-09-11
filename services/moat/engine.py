from __future__ import annotations

import logging
from math import isfinite

from services.moat.models import EconomicMoatResult
from services.ratios.models import FinancialRatios

logger = logging.getLogger(__name__)


class EconomicMoatEngine:
    """Evaluate competitive-advantage signals from supplied financial ratios."""

    def evaluate_moat(self, ratios: FinancialRatios) -> EconomicMoatResult:
        if not isinstance(ratios, FinancialRatios):
            raise TypeError("ratios must be a FinancialRatios instance")
        symbol = ratios.symbol.strip().upper()
        if not symbol:
            raise ValueError("ratios.symbol must be non-empty")

        profitability = ratios.profitability
        roe = float(profitability.get("roe", 0.0))
        roic = float(profitability.get("roic", 0.0))
        net_margin = float(profitability.get("net_margin", 0.0))
        for value in (roe, roic, net_margin):
            if not isfinite(value):
                raise ValueError("moat inputs must be finite")

        # Scores are intentionally based only on supplied, validated ratio evidence.
        roic_score = 40.0 if roic > 20.0 else 25.0 if roic > 12.0 else 10.0 if roic >= 0.0 else 0.0
        margin_score = 35.0 if net_margin > 15.0 else 20.0 if net_margin > 8.0 else 5.0 if net_margin >= 0.0 else 0.0
        roe_score = 25.0 if roe > 15.0 else 10.0 if roe >= 0.0 else 0.0
        score = min(max(roic_score + margin_score + roe_score, 0.0), 100.0)

        classification = "Wide Moat" if score >= 80.0 else "Narrow Moat" if score >= 50.0 else "No Moat"
        return EconomicMoatResult(
            symbol=symbol,
            moat_score=score,
            moat_classification=classification,
            factors={
                "roic_signal": roic_score,
                "net_margin_signal": margin_score,
                "roe_signal": roe_score,
            },
            metadata={
                "version": "6.5",
                "framework": "Quantitative return-and-margin screen",
                "input_status": "VALIDATED_FINANCIAL_RATIOS",
            },
        )
