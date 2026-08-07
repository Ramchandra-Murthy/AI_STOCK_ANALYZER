from __future__ import annotations

import pytest
from services.moat.engine import EconomicMoatEngine
from services.ratios.models import FinancialRatios

def test_economic_moat_engine() -> None:
    engine = EconomicMoatEngine()
    
    ratios = FinancialRatios(
        symbol="RELIANCE.NS",
        period="2025",
        profitability={"net_margin": 16.0, "roe": 18.5, "roic": 15.0, "operating_margin": 20.0, "ebit_margin": 18.0, "roce": 14.0, "croic": 13.0},
        liquidity={"current_ratio": 1.5, "cash_ratio": 0.4, "quick_ratio": 1.2},
        solvency={"debt_to_equity": 0.5, "net_debt_to_equity": 0.3, "interest_coverage": 8.5, "debt_to_capital": 0.3},
        efficiency={"asset_turnover": 0.8, "capital_turnover": 1.1},
        growth={"revenue_cagr_3y": 12.0, "net_income_cagr_3y": 15.0, "eps_cagr_3y": 14.0},
        cash_flow={"fcf_margin": 10.0, "fcf_conversion": 85.0, "capex_to_revenue": 5.0, "owner_earnings": 15000.0},
        quality_scores={"piotroski_f_score": 8.0, "altman_z_score": 3.5, "beneish_m_score": -2.2, "accrual_ratio": 0.02},
        metadata={"version": "6.3"}
    )

    result = engine.evaluate_moat(ratios)

    assert result.symbol == "RELIANCE.NS"
    assert result.moat_score > 0.0
    assert result.moat_classification in ["Wide Moat", "Narrow Moat", "No Moat"]
