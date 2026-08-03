"""
Module: tests.forecast.test_models
Description: Comprehensive test suite for institutional forecast domain models.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

import pytest
from dataclasses import FrozenInstanceError

from services.forecast.models import (
    ForecastMethod,
    ConfidenceLevel,
    ForecastProtocol,
    ForecastSeries,
    ForecastAssumption,
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
    """Verifies forecast method enumeration members and values."""
    assert ForecastMethod.CAGR.value == "cagr"
    assert ForecastMethod.LINEAR_REGRESSION.value == "linear_regression"
    assert ForecastMethod.ROLLING_AVERAGE.value == "rolling_average"
    assert ForecastMethod.MEAN_REVERSION.value == "mean_reversion"
    assert ForecastMethod.GUIDANCE.value == "guidance"
    assert ForecastMethod.MANUAL.value == "manual"


def test_confidence_level_enum() -> None:
    """Verifies confidence tier enumeration members and values."""
    assert ConfidenceLevel.HIGH.value == "high"
    assert ConfidenceLevel.MEDIUM.value == "medium"
    assert ConfidenceLevel.LOW.value == "low"
    assert ConfidenceLevel.SPECULATIVE.value == "speculative"


def test_forecast_assumption_model() -> None:
    """Verifies assumptions container instantiation, validation, and serialization."""
    assumption = ForecastAssumption(
        method=ForecastMethod.CAGR,
        horizon=5,
        confidence=ConfidenceLevel.HIGH,
        growth_rate=0.12,
        custom_parameters={"window": 3},
    )
    assert assumption.horizon == 5
    assert assumption.growth_rate == 0.12
    assert isinstance(assumption, ForecastProtocol) or hasattr(assumption, "to_dict")

    serialized = assumption.to_dict()
    assert serialized["method"] == "cagr"
    assert serialized["horizon"] == 5
    assert serialized["custom_parameters"]["window"] == 3

    # Test invalid horizon enforcement
    with pytest.raises(
        ValueError, match="Forecast horizon must be a positive integer."
    ):
        ForecastAssumption(
            method=ForecastMethod.CAGR,
            horizon=0,
            confidence=ConfidenceLevel.HIGH,
        )


def test_forecast_series_model() -> None:
    """Verifies base forecast series immutability, type normalization, and serialization."""
    series = ForecastSeries(
        historical=(100.0, 110.0, 120.0),
        projected=(130.0, 140.0),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.MEDIUM,
    )
    assert isinstance(series.historical, tuple)
    assert isinstance(series.projected, tuple)
    assert series.method == ForecastMethod.CAGR

    # Immutability check
    with pytest.raises(FrozenInstanceError):
        series.projected = (150.0,)  # type: ignore

    serialized = series.to_dict()
    assert serialized["historical"] == [100.0, 110.0, 120.0]
    assert serialized["projected"] == [130.0, 140.0]
    assert serialized["method"] == "cagr"
    assert serialized["confidence"] == "medium"


def test_revenue_forecast_model() -> None:
    """Verifies RevenueForecast specialization and growth rates handling."""
    rev_forecast = RevenueForecast(
        historical=(1000.0, 1100.0),
        projected=(1210.0, 1331.0),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.HIGH,
        growth_rates=(0.10, 0.10),
    )
    assert rev_forecast.growth_rates == (0.10, 0.10)
    serialized = rev_forecast.to_dict()
    assert serialized["growth_rates"] == [0.10, 0.10]


def test_margin_forecast_model() -> None:
    """Verifies MarginForecast attributes and serialization structure."""
    margin_forecast = MarginForecast(
        historical=(0.15, 0.16),
        projected=(0.17, 0.18),
        method=ForecastMethod.LINEAR_REGRESSION,
        confidence=ConfidenceLevel.MEDIUM,
        ebit_margins=(0.12, 0.13),
        ebitda_margins=(0.18, 0.19),
        gross_margins=(0.40, 0.42),
    )
    assert margin_forecast.ebit_margins == (0.12, 0.13)
    serialized = margin_forecast.to_dict()
    assert serialized["ebit_margins"] == [0.12, 0.13]
    assert serialized["ebitda_margins"] == [0.18, 0.19]
    assert serialized["gross_margins"] == [0.40, 0.42]


def test_capex_forecast_model() -> None:
    """Verifies CapExForecast default ratios, aliases, and serialization."""
    capex = CapexForecast(
        historical=(50.0, 55.0),
        projected=(60.0, 65.0),
        method=ForecastMethod.ROLLING_AVERAGE,
        confidence=ConfidenceLevel.LOW,
        capex_ratio=0.05,
    )
    assert capex.capex_ratio == 0.05
    assert capex.capex_to_revenue_ratio == 0.05
    assert capex.projected_capex == (60.0, 65.0)

    serialized = capex.to_dict()
    assert serialized["capex_ratio"] == 0.05
    assert serialized["projected_capex"] == [60.0, 65.0]


def test_depreciation_forecast_model() -> None:
    """Verifies DepreciationForecast parameters, defaults, and dictionary export."""
    dep = DepreciationForecast(
        historical=(20.0, 22.0),
        projected=(24.0, 26.0),
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.MEDIUM,
        depreciation_rate=0.04,
    )
    assert dep.depreciation_rate == 0.04
    assert dep.depreciation_ratio == 0.04
    assert dep.depreciation == (24.0, 26.0)

    serialized = dep.to_dict()
    assert serialized["depreciation_rate"] == 0.04
    assert serialized["depreciation"] == [24.0, 26.0]


def test_working_capital_forecast_model() -> None:
    """Verifies WorkingCapitalForecast adjustments and delta schedules."""
    wc = WorkingCapitalForecast(
        historical=(10.0, 12.0),
        projected=(15.0, 18.0),
        method=ForecastMethod.MEAN_REVERSION,
        confidence=ConfidenceLevel.LOW,
        working_capital_changes=(3.0, 3.0),
        delta_working_capital=(3.0, 3.0),
    )
    assert wc.delta_working_capital == (3.0, 3.0)
    serialized = wc.to_dict()
    assert serialized["delta_working_capital"] == [3.0, 3.0]


def test_tax_forecast_model() -> None:
    """Verifies TaxForecast effective tax rates mapping."""
    tax = TaxForecast(
        historical=(0.25, 0.25),
        projected=(0.25, 0.25),
        method=ForecastMethod.MANUAL,
        confidence=ConfidenceLevel.HIGH,
        effective_tax_rates=(0.25, 0.25),
    )
    assert tax.effective_tax_rates == (0.25, 0.25)
    assert tax.to_dict()["effective_tax_rates"] == [0.25, 0.25]


def test_terminal_growth_forecast_model() -> None:
    """Verifies TerminalGrowthForecast boundary validations and defaults."""
    tg = TerminalGrowthForecast(
        terminal_growth_rate=0.04,
        method=ForecastMethod.CAGR,
        confidence=ConfidenceLevel.MEDIUM,
    )
    assert tg.terminal_growth_rate == 0.04
    assert tg.to_dict()["perpetuity_growth_rate"] == 0.04

    # Boundary enforcement: < -5% or > 10%
    with pytest.raises(
        ValueError,
        match="Terminal growth rate must fall within institutional boundaries",
    ):
        TerminalGrowthForecast(
            terminal_growth_rate=0.15,
            method=ForecastMethod.CAGR,
            confidence=ConfidenceLevel.MEDIUM,
        )


def test_forecast_confidence_model() -> None:
    """Verifies ForecastConfidence score boundaries and rationale mapping."""
    conf = ForecastConfidence(
        level=ConfidenceLevel.HIGH,
        score=0.92,
        rationale="Robust historical predictability and stable margins.",
    )
    assert conf.score == 0.92
    assert conf.level == ConfidenceLevel.HIGH

    with pytest.raises(
        ValueError, match="Confidence score must be normalized between 0.0 and 1.0."
    ):
        ForecastConfidence(
            level=ConfidenceLevel.HIGH,
            score=1.1,
            rationale="Invalid score.",
        )


def test_forecast_scenario_model() -> None:
    """Verifies complete scenario assembly and deep serialization capability."""
    rev = RevenueForecast(
        (100.0,), (110.0,), ForecastMethod.CAGR, ConfidenceLevel.HIGH, (0.10,)
    )
    margin = MarginForecast(
        (0.2,),
        (0.22,),
        ForecastMethod.CAGR,
        ConfidenceLevel.HIGH,
        (0.15,),
        (0.2,),
        (0.4,),
    )
    capex = CapexForecast(
        (5.0,), (5.5,), ForecastMethod.CAGR, ConfidenceLevel.HIGH, 0.05
    )
    dep = DepreciationForecast(
        (4.0,), (4.4,), ForecastMethod.CAGR, ConfidenceLevel.HIGH, 0.04
    )
    wc = WorkingCapitalForecast(
        (2.0,), (2.2,), ForecastMethod.CAGR, ConfidenceLevel.HIGH, (0.2,), (0.2,)
    )
    tax = TaxForecast(
        (0.25,), (0.25,), ForecastMethod.CAGR, ConfidenceLevel.HIGH, (0.25,)
    )
    tg = TerminalGrowthForecast(0.04, ForecastMethod.CAGR, ConfidenceLevel.HIGH)
    conf = ForecastConfidence(ConfidenceLevel.HIGH, 0.88, "Solid baselines.")

    scenario = ForecastScenario(
        scenario_name="Base Case",
        revenue_forecast=rev,
        margin_forecast=margin,
        capex_forecast=capex,
        depreciation_forecast=dep,
        working_capital_forecast=wc,
        tax_forecast=tax,
        terminal_growth=tg,
        confidence_assessment=conf,
    )

    assert scenario.scenario_name == "Base Case"
    serialized = scenario.to_dict()
    assert serialized["scenario_name"] == "Base Case"
    assert serialized["revenue_forecast"]["projected"] == [110.0]
    assert serialized["confidence_assessment"]["score"] == 0.88
