"""
Module: services.forecast.algorithms.cagr
Description: Institutional CAGR forecasting calculation engine.
Author: Engineering Team
Python Version: 3.13+
"""

from __future__ import annotations

from typing import Tuple
from services.forecast.algorithms.base import ForecastAlgorithmProtocol


class CAGRForecastEngine:
    """Pure mathematical engine for Compound Annual Growth Rate projections."""

    def calculate(
        self, historical: Tuple[float, ...], periods: int, **kwargs: float
    ) -> Tuple[float, ...]:
        """
        Projects future values using CAGR derived from the first and last historical observations.

        Parameters:
            historical: Tuple of historical numerical values (must contain at least 2 points).
            periods: Number of future periods to project.
            **kwargs: Optional overrides (e.g., 'growth_rate_override').

        Returns:
            Tuple of projected float values.
        """
        if not historical or periods <= 0:
            return tuple()

        if len(historical) == 1:
            # Fallback if only one historical point is available
            val = historical[0]
            return tuple(val for _ in range(periods))

        start_val = historical[0]
        end_val = historical[-1]
        n_years = len(historical) - 1

        # Handle edge case of zero or negative starting values safely
        if start_val <= 0 or end_val <= 0:
            cagr = 0.0
        else:
            cagr = (end_val / start_val) ** (1.0 / n_years) - 1.0

        # Apply optional override if provided in kwargs
        growth_rate = kwargs.get("growth_rate_override", cagr)

        projected = []
        last_val = end_val
        for _ in range(periods):
            last_val *= 1.0 + growth_rate
            projected.append(float(last_val))

        return tuple(projected)
