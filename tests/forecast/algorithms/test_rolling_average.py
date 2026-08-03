"""
==========================================================
TEST ROLLING AVERAGE FORECAST ALGORITHM
Module  : tests.forecast.algorithms.test_rolling_average
Layer   : Tests / Forecast / Algorithms
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.algorithms.rolling_average import RollingAverageCalculator
from services.forecast.exceptions import ValuationError


def test_calculate_period_growth_rates() -> None:
    history = (100.0, 110.0, 121.0)
    rates = RollingAverageCalculator.calculate_period_growth_rates(history)
    assert len(rates) == 2
    assert pytest.approx(rates[0], rel=1e-4) == 0.10
    assert pytest.approx(rates[1], rel=1e-4) == 0.10


def test_calculate_rolling_mean_rate() -> None:
    history = (100.0, 110.0, 120.0, 132.0)
    # YoY growth rates: 10%, 9.09%, 10%
    mean_rate = RollingAverageCalculator.calculate_rolling_mean_rate(history, window=3)
    assert pytest.approx(mean_rate, rel=1e-3) == 0.0969


def test_project_rolling_average() -> None:
    history = (100.0, 110.0, 120.0)
    projections = RollingAverageCalculator.project(history, horizon=2, window=2)
    assert len(projections) == 2
    # Last growth rates: 10%, 9.09% -> mean = 9.545%
    assert projections[0] > 120.0
    assert projections[1] > projections[0]


def test_rolling_average_insufficient_data_raises() -> None:
    with pytest.raises(ValuationError, match="At least 2 periods"):
        RollingAverageCalculator.project((100.0,), horizon=3)
