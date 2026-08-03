"""
==========================================================
TEST CAGR FORECAST ALGORITHM
Module  : tests.forecast.algorithms.test_cagr
Layer   : Tests / Forecast / Algorithms
==========================================================
"""

from __future__ import annotations

import pytest
from services.forecast.algorithms.cagr import CAGRCalculator
from services.forecast.exceptions import ValuationError


def test_calculate_cagr_success() -> None:
    # 100 to 121 over 2 periods (years) -> 10% CAGR
    history = (100.0, 110.0, 121.0)
    cagr = CAGRCalculator.calculate_cagr(history)
    assert pytest.approx(cagr, rel=1e-4) == 0.10


def test_calculate_cagr_insufficient_data_raises() -> None:
    with pytest.raises(ValuationError, match="At least 2 periods"):
        CAGRCalculator.calculate_cagr((100.0,))


def test_project_cagr_success() -> None:
    history = (100.0, 200.0)  # 100% CAGR over 1 period
    projections = CAGRCalculator.project(history, horizon=2)
    assert len(projections) == 2
    assert pytest.approx(projections[0], rel=1e-4) == 400.0
    assert pytest.approx(projections[1], rel=1e-4) == 800.0
