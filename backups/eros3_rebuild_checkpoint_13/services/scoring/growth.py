from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.financials.financial_statement import FinancialStatements


def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0,
) -> float:
    return max(minimum, min(maximum, float(value)))


def _calculate_cagr(
    begin_value: float,
    end_value: float,
    periods: int,
) -> float:
    if periods <= 0:
        return 0.0
    if begin_value <= 0 or end_value <= 0:
        return 0.0
    try:
        return (end_value / begin_value) ** (1.0 / periods) - 1.0
    except Exception:
        return 0.0


@dataclass(frozen=True, slots=True)
class GrowthScoreResult:
    revenue_cagr: float
    ebitda_cagr: float
    net_income_cagr: float
    eps_cagr: float
    fcf_cagr: float
    growth_score: float
    growth_details: dict[str, Any]


class GrowthScoringEngine:
    """
    EROS 3.0 Block 11 Historical Multi-Period Growth Engine.
    Evaluates:
        - Revenue CAGR
        - EBITDA CAGR
        - Net Income CAGR
        - EPS CAGR
        - Free Cash Flow CAGR
    Historical periods are read from the canonical
    PeriodFinancials.period field.
    """

    def evaluate(
        self,
        financials: FinancialStatements,
    ) -> GrowthScoreResult:
        periods = financials.periods
        if not periods or len(periods) < 2:
            return GrowthScoreResult(
                revenue_cagr=0.0,
                ebitda_cagr=0.0,
                net_income_cagr=0.0,
                eps_cagr=0.0,
                fcf_cagr=0.0,
                growth_score=60.0,
                growth_details={
                    "status": "INSUFFICIENT_HISTORICAL_PERIODS",
                    "periods_analyzed": len(periods),
                },
            )
        # IMPORTANT:
        # PeriodFinancials uses `period`, NOT `fiscal_year`.
        sorted_periods = sorted(
            periods,
            key=lambda p: p.period,
        )
        count = len(sorted_periods)
        oldest = sorted_periods[0]
        newest = sorted_periods[-1]

        old_income = oldest.income_statement
        new_income = newest.income_statement
        old_cashflow = oldest.cash_flow_statement
        new_cashflow = newest.cash_flow_statement

        years = count - 1
        revenue_cagr = _calculate_cagr(
            old_income.revenue,
            new_income.revenue,
            years,
        )
        ebitda_cagr = _calculate_cagr(
            old_income.ebitda,
            new_income.ebitda,
            years,
        )
        net_income_cagr = _calculate_cagr(
            old_income.net_income,
            new_income.net_income,
            years,
        )
        eps_cagr = _calculate_cagr(
            old_income.eps,
            new_income.eps,
            years,
        )

        old_fcf = old_cashflow.operating_cash_flow - old_cashflow.capital_expenditure
        new_fcf = new_cashflow.operating_cash_flow - new_cashflow.capital_expenditure
        fcf_cagr = _calculate_cagr(
            old_fcf,
            new_fcf,
            years,
        )

        def _score_cagr(cagr: float) -> float:
            score = 50.0 + (cagr / 0.15) * 50.0
            return _clamp(score)

        revenue_score = _score_cagr(revenue_cagr)
        ebitda_score = _score_cagr(ebitda_cagr)
        net_income_score = _score_cagr(net_income_cagr)
        eps_score = _score_cagr(eps_cagr)
        fcf_score = _score_cagr(fcf_cagr)

        composite_growth = round(
            revenue_score * 0.25
            + ebitda_score * 0.25
            + net_income_score * 0.20
            + eps_score * 0.20
            + fcf_score * 0.10,
            2,
        )

        details = {
            "engine_version": "EROS-3.0-BLOCK-11",
            "status": "HISTORICAL_GROWTH_CALCULATED",
            "periods_analyzed": count,
            "period_range": {
                "oldest": oldest.period,
                "newest": newest.period,
            },
            "cagrs": {
                "revenue_cagr": round(revenue_cagr * 100, 2),
                "ebitda_cagr": round(ebitda_cagr * 100, 2),
                "net_income_cagr": round(
                    net_income_cagr * 100,
                    2,
                ),
                "eps_cagr": round(eps_cagr * 100, 2),
                "fcf_cagr": round(fcf_cagr * 100, 2),
            },
            "component_scores": {
                "revenue": round(revenue_score, 2),
                "ebitda": round(ebitda_score, 2),
                "net_income": round(
                    net_income_score,
                    2,
                ),
                "eps": round(eps_score, 2),
                "fcf": round(fcf_score, 2),
            },
        }

        return GrowthScoreResult(
            revenue_cagr=round(revenue_cagr, 4),
            ebitda_cagr=round(ebitda_cagr, 4),
            net_income_cagr=round(
                net_income_cagr,
                4,
            ),
            eps_cagr=round(eps_cagr, 4),
            fcf_cagr=round(fcf_cagr, 4),
            growth_score=composite_growth,
            growth_details=details,
        )
