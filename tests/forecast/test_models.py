"""
==========================================================
FORECAST DOMAIN MODELS TEST SUITE
Module  : tests.forecast.test_models
Layer   : Tests / Forecast / Domain Models
==========================================================
"""

from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from services.forecast.models import (
    ForecastMethod,
    ConfidenceLevel,
    ForecastAssumption,
    ForecastSeries,
    RevenueForecast,
    MarginForecast,
    CapexForecast,
    DepreciationForecast,
    WorkingCapitalForecast,
    TaxForecast,
    TerminalGrowthForecast,
    ForecastConfidence,
    ForecastScenario,
)


def test_forecast_method_enum() -> None:
    """Verify all ForecastMethod enum members."""
    assert ForecastMethod.CAGR == "cagr"
    assert ForecastMethod.HISTORICAL_MEAN == "historical_mean"
    assert ForecastMethod.LINEAR_REGRESSION == "linear_regression"
    assert ForecastMethod.EXPONENTIAL_SMOOTHING == "exponential_smoothing"
    assert ForecastMethod.MANAGEMENT_GUIDANCE == "management_guidance"
    assert ForecastMethod.MANUAL == "manual"


def test_confidence_level_enum() -> None:
    """Verify all ConfidenceLevel enum members."""
    assert ConfidenceLevel.HIGH == "high"
    assert ConfidenceLevel.MEDIUM == "medium"
    assert ConfidenceLevel.LOW == "low"


def test_forecast_assumption_model() -> None:
    """Verify ForecastAssumption immutability, equality, hashing, and serialization."""
    a1 = ForecastAssumption("growth", 0.08, "Rationale 1")
    a2 = ForecastAssumption("growth", 0.08, "Rationale 1")
    a3 = ForecastAssumption("growth", 0.10, "Rationale 2")

    assert a1 == a2
    assert a1 != a3
    assert hash(a1) == hash(a2)

    with pytest.raises(FrozenInstanceError):
        a1.value = 0.09  # type: ignore[misc]

    assert a1.to_dict() == {
        "parameter_name": "growth",
        "value": 0.08,
        "rationale": "Rationale 1",
    }


def test_forecast_series_model() -> None:
    """Verify ForecastSeries model behavior."""
    series = ForecastSeries(
        historical=(100.0, 110.0),
        projected=(121.0,),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
    )
    assert series.historical == (100.0, 110.0)
    assert series.projected == (121.0,)
    assert series.to_dict()["method"] == "cagr"


def test_revenue_forecast_model() -> None:
    """Verify RevenueForecast model creation and serialization."""
    rev = RevenueForecast(
        historical=(100.0, 110.0),
        projected=(121.0, 133.1),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
        growth_rates=(0.10, 0.10),
        projected_revenue=(121.0, 133.1),
        guidance_override_applied=False,
    )
    assert rev.growth_rates == (0.10, 0.10)
    assert rev.to_dict()["guidance_override_applied"] is False


def test_margin_forecast_model() -> None:
    """Verify MarginForecast model creation and serialization."""
    margin = MarginForecast(
        historical=(0.15, 0.16),
        projected=(0.17,),
        method=ForecastMethod.HISTORICAL_MEAN,
        confidence=ConfidenceLevel.MEDIUM,
        margins=(0.17,),
        metric_name="ebitda_margin",
    )
    assert margin.metric_name == "ebitda_margin"
    assert margin.to_dict()["margins"] == [0.17]


def test_capex_forecast_model() -> None:
    """Verify CapexForecast model creation and serialization."""
    capex = CapexForecast(
        historical=(10.0, 12.0),
        projected=(14.0,),
        method=ForecastMethod.LINEAR_REGRESSION,
        confidence=ConfidenceLevel.LOW,
        capex_ratio=0.05,
        capex=(14.0,),
    )
    assert capex.capex_ratio == 0.05
    assert capex.to_dict()["capex"] == [14.0]


def test_depreciation_forecast_model() -> None:
    """Verify DepreciationForecast model creation and serialization."""
    dep = DepreciationForecast(
        historical=(5.0, 6.0),
        projected=(7.0,),
        method=ForecastMethod.EXPONENTIAL_SMOOTHING,
        confidence=ConfidenceLevel.MEDIUM,
        depreciation_rate=0.04,
        depreciation=(7.0,),
    )
    assert dep.depreciation_rate == 0.04
    assert dep.to_dict()["depreciation"] == [7.0]


def test_working_capital_forecast_model() -> None:
    """Verify WorkingCapitalForecast model creation and serialization."""
    wc = WorkingCapitalForecast(
        historical=(50.0, 55.0),
        projected=(60.0,),
        method=ForecastMethod.HISTORICAL_MEAN,
        confidence=ConfidenceLevel.HIGH,
        nwc_percentage_of_revenue=0.15,
        working_capital=(60.0,),
    )
    assert wc.nwc_percentage_of_revenue == 0.15
    assert wc.to_dict()["working_capital"] == [60.0]


def test_tax_forecast_model() -> None:
    """Verify TaxForecast model creation and serialization."""
    tax = TaxForecast(
        historical=(20.0, 22.0),
        projected=(25.0,),
        method=ForecastMethod.MANUAL,
        confidence=ConfidenceLevel.HIGH,
        effective_tax_rate=0.25,
        tax_liabilities=(25.0,),
    )
    assert tax.effective_tax_rate == 0.25
    assert tax.to_dict()["tax_liabilities"] == [25.0]


def test_terminal_growth_forecast_model() -> None:
    """Verify TerminalGrowthForecast model creation and serialization."""
    tg = TerminalGrowthForecast(
        historical_gdp_growth=(0.04, 0.05),
        terminal_growth_rate=0.03,
        method=ForecastMethod.MANAGEMENT_GUIDANCE,
        confidence=ConfidenceLevel.MEDIUM,
    )
    assert tg.terminal_growth_rate == 0.03
    assert tg.to_dict()["terminal_growth_rate"] == 0.03


def test_forecast_confidence_model() -> None:
    """Verify ForecastConfidence model creation and serialization."""
    conf = ForecastConfidence(
        overall_score=0.85,
        qualitative_rating=ConfidenceLevel.HIGH,
        component_scores={"revenue": 0.9, "margin": 0.8},
    )
    assert conf.overall_score == 0.85
    assert conf.to_dict()["qualitative_rating"] == "high"


def test_forecast_scenario_model() -> None:
    """Verify ForecastScenario container composition and serialization."""
    assumption = ForecastAssumption("inflation", 0.04, "Baseline CPI")
    scenario = ForecastScenario(
        scenario_name="Base Case",
        method=ForecastMethod.CAGR,
        probability=0.75,
        assumptions=(assumption,),
        overrides={"tax_rate": 0.25},
    )

    assert scenario.scenario_name == "Base Case"
    assert scenario.probability == 0.75
    assert len(scenario.assumptions) == 1
    assert scenario.to_dict()["overrides"] == {"tax_rate": 0.25}
