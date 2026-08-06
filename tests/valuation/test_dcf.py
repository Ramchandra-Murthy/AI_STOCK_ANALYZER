from __future__ import annotations

import pytest
from services.forecast.models import ForecastResult
from services.valuation.dcf.engine import ProductionDCFEngine


def test_production_dcf_calculation() -> None:
    forecast = ForecastResult(
        symbol="RELIANCE.NS",
        model_type="CAGR",
        free_cash_flow_forecast=[100000.0, 115000.0, 132000.0, 151000.0, 173000.0],
    )

    engine = ProductionDCFEngine()
    result = engine.calculate(forecast, wacc=0.10, terminal_growth_rate=0.04)

    assert result.symbol == "RELIANCE.NS"
    assert result.enterprise_value > 0.0
    assert result.equity_value > 0.0
    assert result.fair_value_per_share > 0.0
    assert len(result.pv_cash_flows) == 5
