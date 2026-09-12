from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.financials.financial_ratios import (
    FinancialRatios,
    calculate_financial_ratios,
)
from services.financials.financial_statement import FinancialStatements


def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _score_positive(
    value: float,
    weak: float,
    strong: float,
) -> float:
    """
    Score a metric where higher values are better.
    weak   -> 0
    strong -> 100
    """
    if strong <= weak:
        raise ValueError("strong threshold must be greater than weak threshold")
    score = ((value - weak) / (strong - weak)) * 100.0
    return round(_clamp(score), 2)


def _score_negative(
    value: float,
    good: float,
    bad: float,
) -> float:
    """
    Score a metric where lower values are better.
    good -> 100
    bad  -> 0
    """
    if bad <= good:
        raise ValueError("bad threshold must be greater than good threshold")
    score = ((bad - value) / (bad - good)) * 100.0
    return round(_clamp(score), 2)


def _average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 2)


@dataclass(frozen=True, slots=True)
class FundamentalScoreResult:
    """
    Data-driven fundamental scoring result.
    All pillar scores are normalized to 0-100.
    """

    symbol: str
    profitability_score: float
    quality_score: float
    financial_strength_score: float
    capital_efficiency_score: float
    cash_flow_quality_score: float
    fundamental_score: float
    pillar_details: dict[str, Any]


class FundamentalScoringEngine:
    """
    Deterministic, explainable fundamental scoring engine.
    This engine intentionally uses only validated canonical financial
    statements and calculated financial ratios.
    Growth, momentum and valuation are deliberately excluded here.
    """

    def evaluate(
        self,
        financials: FinancialStatements,
    ) -> FundamentalScoreResult:
        ratios: FinancialRatios = calculate_financial_ratios(
            income=financials.income_statement,
            balance=financials.balance_sheet,
            cashflow=financials.cash_flow_statement,
        )

        # ======================================================
        # PROFITABILITY
        # ======================================================
        profitability_components = {
            "gross_margin": _score_positive(
                ratios.gross_margin,
                weak=0.20,
                strong=0.60,
            ),
            "ebitda_margin": _score_positive(
                ratios.ebitda_margin,
                weak=0.05,
                strong=0.30,
            ),
            "ebit_margin": _score_positive(
                ratios.ebit_margin,
                weak=0.03,
                strong=0.25,
            ),
            "net_margin": _score_positive(
                ratios.net_margin,
                weak=0.02,
                strong=0.20,
            ),
            "roe": _score_positive(
                ratios.roe,
                weak=0.05,
                strong=0.25,
            ),
            "roa": _score_positive(
                ratios.roa,
                weak=0.02,
                strong=0.15,
            ),
            "roce": _score_positive(
                ratios.roce,
                weak=0.05,
                strong=0.25,
            ),
            "roic": _score_positive(
                ratios.roic,
                weak=0.04,
                strong=0.20,
            ),
        }
        profitability_score = _average(list(profitability_components.values()))

        # ======================================================
        # QUALITY
        # ======================================================
        quality_components = {
            "cash_conversion_ratio": _score_positive(
                ratios.cash_conversion_ratio,
                weak=0.70,
                strong=1.20,
            ),
            "fcf_margin": _score_positive(
                ratios.fcf_margin,
                weak=0.02,
                strong=0.20,
            ),
            "roic": _score_positive(
                ratios.roic,
                weak=0.04,
                strong=0.20,
            ),
            "roe": _score_positive(
                ratios.roe,
                weak=0.05,
                strong=0.25,
            ),
        }
        quality_score = _average(list(quality_components.values()))

        # ======================================================
        # FINANCIAL STRENGTH
        # ======================================================
        financial_strength_components = {
            "current_ratio": _score_positive(
                ratios.current_ratio,
                weak=1.00,
                strong=2.00,
            ),
            "quick_ratio": _score_positive(
                ratios.quick_ratio,
                weak=0.50,
                strong=1.50,
            ),
            "debt_to_equity": _score_negative(
                ratios.debt_to_equity,
                good=0.25,
                bad=1.50,
            ),
            "net_debt_to_ebitda": _score_negative(
                ratios.net_debt_to_ebitda,
                good=0.50,
                bad=4.00,
            ),
        }
        financial_strength_score = _average(list(financial_strength_components.values()))

        # ======================================================
        # CAPITAL EFFICIENCY
        # ======================================================
        capital_efficiency_components = {
            "roic": _score_positive(
                ratios.roic,
                weak=0.04,
                strong=0.20,
            ),
            "roce": _score_positive(
                ratios.roce,
                weak=0.05,
                strong=0.25,
            ),
            "roa": _score_positive(
                ratios.roa,
                weak=0.02,
                strong=0.15,
            ),
            "asset_turnover": _score_positive(
                ratios.asset_turnover,
                weak=0.30,
                strong=1.50,
            ),
            "inventory_turnover": _score_positive(
                ratios.inventory_turnover,
                weak=2.00,
                strong=12.00,
            ),
        }
        capital_efficiency_score = _average(list(capital_efficiency_components.values()))

        # ======================================================
        # CASH FLOW QUALITY
        # ======================================================
        cash_flow_components = {
            "fcf_margin": _score_positive(
                ratios.fcf_margin,
                weak=0.02,
                strong=0.20,
            ),
            "cash_conversion_ratio": _score_positive(
                ratios.cash_conversion_ratio,
                weak=0.70,
                strong=1.20,
            ),
        }
        cash_flow_quality_score = _average(list(cash_flow_components.values()))

        # ======================================================
        # FUNDAMENTAL COMPOSITE
        # ======================================================
        pillar_weights = {
            "profitability": 0.25,
            "quality": 0.20,
            "financial_strength": 0.20,
            "capital_efficiency": 0.20,
            "cash_flow_quality": 0.15,
        }
        fundamental_score = round(
            profitability_score * pillar_weights["profitability"]
            + quality_score * pillar_weights["quality"]
            + financial_strength_score * pillar_weights["financial_strength"]
            + capital_efficiency_score * pillar_weights["capital_efficiency"]
            + cash_flow_quality_score * pillar_weights["cash_flow_quality"],
            2,
        )

        raw_ratios = {
            "gross_margin": ratios.gross_margin,
            "ebitda_margin": ratios.ebitda_margin,
            "ebit_margin": ratios.ebit_margin,
            "net_margin": ratios.net_margin,
            "roe": ratios.roe,
            "roa": ratios.roa,
            "roce": ratios.roce,
            "roic": ratios.roic,
            "current_ratio": ratios.current_ratio,
            "quick_ratio": ratios.quick_ratio,
            "debt_to_equity": ratios.debt_to_equity,
            "net_debt_to_ebitda": ratios.net_debt_to_ebitda,
            "fcf_margin": ratios.fcf_margin,
            "cash_conversion_ratio": ratios.cash_conversion_ratio,
            "asset_turnover": ratios.asset_turnover,
            "inventory_turnover": ratios.inventory_turnover,
        }

        details = {
            # Block 10 audit identity
            "engine_version": "EROS-3.0-BLOCK-10",
            # Canonical Block 10 audit contract
            "raw_ratios": raw_ratios,
            "profitability_components": profitability_components,
            "quality_components": quality_components,
            "capital_allocation_components": capital_efficiency_components,
            # Existing detailed contract retained for compatibility
            "ratios": raw_ratios,
            "profitability": profitability_components,
            "quality": quality_components,
            "financial_strength": financial_strength_components,
            "capital_efficiency": capital_efficiency_components,
            "cash_flow_quality": cash_flow_components,
            "weights": pillar_weights,
        }

        return FundamentalScoreResult(
            symbol=financials.ticker,
            profitability_score=profitability_score,
            quality_score=quality_score,
            financial_strength_score=financial_strength_score,
            capital_efficiency_score=capital_efficiency_score,
            cash_flow_quality_score=cash_flow_quality_score,
            fundamental_score=fundamental_score,
            pillar_details=details,
        )
