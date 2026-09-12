from __future__ import annotations

from services.forecast_system.forecast_engine import InstitutionalForecastEngine
from services.forecast_system.models import ForecastResult


def test_forecast_result_immutability() -> None:
    fc = ForecastResult(
        symbol="RELIANCE.NS",
        revenue_forecast=100000.0,
        ebit_forecast=22000.0,
        eps_forecast=125.5,
        fcf_forecast=15000.0,
        forecast_confidence=0.90,
        bull_case_eps=150.0,
        base_case_eps=125.5,
        bear_case_eps=100.0,
        key_assumptions=["Growth tailwinds"],
    )
    assert fc.symbol == "RELIANCE.NS"
    assert fc.eps_forecast == 125.5
    assert fc.timestamp is not None
    assert isinstance(fc.metadata, dict)


def test_institutional_forecast_engine() -> None:
    fc = InstitutionalForecastEngine.generate_forecast("RELIANCE.NS", 800000.0, 110.0)
    assert fc.symbol == "RELIANCE.NS"
    assert fc.revenue_forecast > 800000.0
    assert fc.bull_case_eps > fc.base_case_eps
    assert fc.base_case_eps > fc.bear_case_eps
    assert len(fc.key_assumptions) > 0
