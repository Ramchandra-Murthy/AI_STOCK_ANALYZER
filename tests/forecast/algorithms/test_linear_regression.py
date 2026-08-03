"""
==========================================================
TEST LINEAR REGRESSION FORECAST ALGORITHM
Module  : tests.forecast.algorithms.test_linear_regression
Layer   : Tests / Forecast / Algorithms
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.algorithms.linear_regression import LinearRegressionCalculator
from services.forecast.exceptions import ValuationError


def test_linear_regression_perfect_trend() -> None:
    # Perfect linear trend: y = 10x + 100 -> periods: 100, 110, 120
    history = (100.0, 110.0, 120.0)
    projections = LinearRegressionCalculator.fit_and_project(history, horizon=2)
    assert len(projections) == 2
    # Next periods: 130.0, 140.0
    assert pytest.approx(projections[0], rel=1e-4) == 130.0
    assert pytest.approx(projections[1], rel=1e-4) == 140.0


def test_linear_regression_insufficient_data_raises() -> None:
    with pytest.raises(ValuationError, match="At least 2 periods"):
        LinearRegressionCalculator.fit_and_project((100.0,), horizon=2)


def test_linear_regression_invalid_horizon_raises() -> None:
    with pytest.raises(ValuationError, match="Forecast horizon must be at least 1"):
        LinearRegressionCalculator.fit_and_project((100.0, 110.0), horizon=0)
