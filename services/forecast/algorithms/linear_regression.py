"""
Module: services.forecast.algorithms.linear_regression
Description: Institutional OLS Linear Regression forecasting calculation engine.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

from typing import Tuple
from services.forecast.algorithms.base import ForecastAlgorithmProtocol


class LinearRegressionForecastEngine:
    """Pure mathematical engine for Ordinary Least Squares (OLS) linear trend projections."""

    def calculate(
        self, historical: Tuple[float, ...], periods: int, **kwargs: float
    ) -> Tuple[float, ...]:
        """
        Fitting a linear trend line (y = mx + c) over historical time indices and projecting forward.

                Parameters:
                    historical: Tuple of historical numerical observations.
                    periods: Number of future periods to project.
                    **kwargs: Optional overrides.

                Returns:
                    Tuple of projected float values.
        """
        n = len(historical)
        if n == 0 or periods <= 0:
            return tuple()

        if n == 1:
            val = historical[0]
            return tuple(val for _ in range(periods))

        # X represents time indices: 0, 1, 2, ..., n-1
        x_vals = list(range(n))
        y_vals = list(historical)

        mean_x = sum(x_vals) / n
        mean_y = sum(y_vals) / n

        numerator = sum((x_vals[i] - mean_x) * (y_vals[i] - mean_y) for i in range(n))
        denominator = sum((x_vals[i] - mean_x) ** 2 for i in range(n))

        # Handle zero variance edge case (flat line)
        if denominator == 0.0:
            slope = 0.0
        else:
            slope = numerator / denominator

        intercept = mean_y - slope * mean_x

        # Optional trend dampening factor if provided in kwargs (e.g. mean-reversion pull)
        dampening = kwargs.get("trend_dampening", 1.0)

        projected = []
        for step in range(1, periods + 1):
            future_x = n - 1 + step
            # Apply optional slope dampening over extended projection horizons
            adjusted_slope = slope * (dampening ** (step - 1))
            val = intercept + adjusted_slope * future_x
            projected.append(float(val))

        return tuple(projected)
