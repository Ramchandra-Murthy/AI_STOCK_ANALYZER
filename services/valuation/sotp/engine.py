from __future__ import annotations

import logging
from typing import Any
from services.valuation.sotp.models import SOTPResult, SegmentValuation
from services.fundamentals.models import FinancialStatements

logger = logging.getLogger(__name__)


class SOTPEngine:
    """Sum-of-the-Parts (SOTP) valuation engine for multi-segment conglomerates like Reliance."""

    def calculate(
        self,
        financials: FinancialStatements,
        holding_discount: float = 0.15,
        shares_outstanding: float = 6760.0,
    ) -> SOTPResult:
        symbol = financials.ticker
        logger.info("Running Sum-of-the-Parts (SOTP) valuation for conglomerate: %s", symbol)

        # Segment breakdown for a conglomerate (e.g., Reliance: O2C, Jio, Retail, New Energy)
        raw_segments = [
            {"name": "O2C (Oil-to-Chemicals)", "revenue": 600000.0, "ebitda": 75000.0, "multiple": 7.0},
            {"name": "Jio Platforms (Telecom/Digital)", "revenue": 120000.0, "ebitda": 50000.0, "multiple": 18.0},
            {"name": "Reliance Retail", "revenue": 300000.0, "ebitda": 22000.0, "multiple": 22.0},
            {"name": "New Energy & Others", "revenue": 30000.0, "ebitda": 5000.0, "multiple": 15.0},
        ]

        segment_results = []
        total_ev = 0.0

        for seg in raw_segments:
            ev = seg["ebitda"] * seg["multiple"]
            total_ev += ev
            segment_results.append(
                SegmentValuation(
                    segment_name=seg["name"],
                    revenue=seg["revenue"],
                    ebitda=seg["ebitda"],
                    multiple=seg["multiple"],
                    enterprise_value=round(ev, 2),
                )
            )

        # Balance sheet net debt extraction or fallback
        bs = financials.balance_sheet
        debt_val = ((getattr(bs, "short_term_debt", 0.0) or 0.0) + (getattr(bs, "long_term_debt", getattr(bs, "debt", 0.0)) or 0.0)) if bs else 0.0
        cash_val = ((getattr(bs, "cash", 0.0) or 0.0) + (getattr(bs, "cash_equivalents", 0.0) or 0.0)) if bs else 0.0
        net_debt = (debt_val - cash_val) if bs else 250000.0

        raw_equity_value = total_ev - net_debt
        discounted_equity_value = raw_equity_value * (1.0 - holding_discount)
        fair_value_per_share = max(0.0, discounted_equity_value / shares_outstanding) if shares_outstanding > 0 else 0.0

        return SOTPResult(
            symbol=symbol,
            segments=segment_results,
            sum_of_segments_ev=round(total_ev, 2),
            net_debt=round(net_debt, 2),
            holding_company_discount_pct=holding_discount,
            conglomerate_equity_value=round(discounted_equity_value, 2),
            fair_value_per_share=round(fair_value_per_share, 2),
            assumptions={
                "holding_discount": holding_discount,
                "shares_outstanding": shares_outstanding,
            },
        )
